# -*- coding: utf-8 -*-
r"""Re-evaluate the trained COCO runs with the corrected metric, from their saved checkpoints.

evaluate() had a double-counting bug in the image-to-text branch: it accumulated a hit for every
caption row rather than a per-image flag, so R@1 could exceed 1 (it reported 2.0317 where the loop
and a plain argmax both give 0.4203). Every i2t and t2i number recorded during the scale-up is
therefore inflated and has to be recomputed.

Training is not repeated: each run saved a checkpoint, so this loads it and re-runs the corrected
evaluation. Nothing is overwritten in place; results are written to a separate file for comparison.

    python tools/_p782_reevaluate.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
OUT = REPO / "outputs" / "analysis" / "coco_scaleup_reeval.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-images", type=int, default=3000)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    from transformers import CLIPModel, CLIPProcessor
    from src.config import ExperimentConfig, TrainConfig, LoRAConfig, GapConfig
    from src.trainer import GapAwareTrainer
    from _p754_coco_scaleup import subset_loader, evaluate

    device = "cuda" if torch.cuda.is_available() else "cpu"
    proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    val_loader = subset_loader("val", a.eval_images, a.batch, False, first=False, workers=8)

    prev = json.loads((REPO / "outputs" / "analysis" / "coco_scaleup.json").read_text(
        encoding="utf-8", errors="ignore"))
    runs = prev["runs"]
    print(f"  {len(runs)} runs to re-evaluate")

    out = []
    for r in runs:
        name = r["name"]
        print()
        print("=" * 100)
        print(f"{name}   (previous R@1 {r['R@1']:.4f}, i2t {r['R@1_i2t']:.4f})")
        print("=" * 100)
        ckpt = REPO / "outputs" / "scaleup_coco" / name
        cfg = ExperimentConfig(
            name=name, peft_method="frozen" if r["arm"] == "frozen" else "lora",
            lora=(None if r["arm"] == "frozen" else
                  LoRAConfig(rank=8, alpha=8.0, dropout=0.0, apply_to_text=True,
                             apply_to_vision=(r["arm"] == "both"))),
            gap=GapConfig(compute_every_n_epochs=1, compute_per_layer=False, sample_size=200),
            train=TrainConfig(dataset="coco", batch_size=64, num_epochs=3, learning_rate=1e-5,
                              seed=r["seed"], use_amp=False, save_dir=str(ckpt)))
        tr = GapAwareTrainer(cfg)
        tr.setup_model()
        t0 = time.time()
        loaded = False
        for cand in (ckpt / "best_checkpoint.pt", ckpt / "last_checkpoint.pt",
                     ckpt / "best_model.pt"):
            if cand.exists():
                sd = torch.load(cand, map_location=device, weights_only=False)
                # the checkpoint format changed when the adapter-scope defect was fixed: the trained
                # state now lives under trainable_state_dict rather than model_state_dict
                for key in ("trainable_state_dict", "model_state_dict"):
                    if isinstance(sd, dict) and key in sd:
                        sd = sd[key]
                        break
                model_sd = tr.model.state_dict()
                loadable = {k: v for k, v in sd.items()
                            if k in model_sd and model_sd[k].shape == v.shape}
                skipped = [k for k in sd if k not in loadable]
                tr.model.load_state_dict(loadable, strict=False)
                print(f"  loaded {cand.name}: {len(loadable)} tensors matched, "
                      f"{len(skipped)} skipped")
                if skipped[:4]:
                    print(f"     e.g. skipped {skipped[:4]}")
                # confirm the loaded weights actually differ from a fresh model
                fresh = CLIPModel.from_pretrained(
                    "openai/clip-vit-base-patch32").state_dict()
                diffs = [k for k in loadable
                         if k in fresh and not torch.equal(fresh[k].cpu(), loadable[k].cpu())]
                print(f"  tensors differing from the pretrained model: {len(diffs)}")
                loaded = len(diffs) > 0
                break
        if not loaded:
            cands = sorted(p.name for p in ckpt.glob("*") if p.is_file()) if ckpt.exists() else []
            print(f"  no checkpoint found in {ckpt.name}; files: {cands}")
        met = evaluate(tr.model, val_loader, device, processor=proc)
        print(f"  corrected: R@1 {met['R@1']:.4f}  R@5 {met['R@5']:.4f}  R@10 {met['R@10']:.4f}"
              f"   (i2t {met['R@1_i2t']:.4f} / t2i {met['R@1_t2i']:.4f})   {time.time()-t0:.0f}s")
        assert 0.0 <= met["R@1"] <= 1.0, "R@1 outside [0,1]"
        row = dict(r)
        row.update({"R@1": met["R@1"], "R@5": met["R@5"], "R@10": met["R@10"],
                    "R@1_i2t": met["R@1_i2t"], "R@5_i2t": met["R@5_i2t"],
                    "R@10_i2t": met["R@10_i2t"], "R@1_t2i": met["R@1_t2i"],
                    "R@5_t2i": met["R@5_t2i"], "R@10_t2i": met["R@10_t2i"],
                    "n_unique_images": met["n_unique_images"], "n_captions": met["n_captions"],
                    "checkpoint_loaded": loaded})
        out.append(row)
        del tr
        torch.cuda.empty_cache()

    print()
    print("=" * 100)
    print("previous vs corrected")
    print("=" * 100)
    print(f"  {'run':<32} {'R@1 old':>8} {'R@1 new':>8} {'i2t old':>8} {'i2t new':>8}")
    for old, new in zip(runs, out):
        print(f"  {new['name']:<32} {old['R@1']:>8.4f} {new['R@1']:>8.4f} "
              f"{old['R@1_i2t']:>8.4f} {new['R@1_i2t']:>8.4f}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"runs": out}, ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
