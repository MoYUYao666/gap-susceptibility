# -*- coding: utf-8 -*-
r"""p369 -- do the archived CLIP strict-freeze R@1 values reproduce through the PAPER'S OWN
code path (`GapAwareTrainer._compute_retrieval_metrics` on `create_dataloaders`' loader)?

WHY
    `tools/_p360_gallery_noise.py` re-measures the archived checkpoints with its own
    embedding/loader code and reproduces the archived Delta-CG to ~0.0003, but for the
    `vision_only` arm its R@1 (0.678 +- 0.006 over 12 draws) sits ~3.5 sd BELOW the archived
    `final_task_metrics.R@1` = 0.7000.  Before any noise claim is made from that pipeline,
    the pipeline itself has to be shown equivalent to the protocol.  This script runs the
    protocol's own loader (num_workers=4, batch 128, `src/dataset.py`) and the protocol's own
    metric function on the same archived checkpoints.

    (For the vision-side arms the fresh-draw cost is one pass per repeat; text_only reuses
    the same images for both states, so 1 pass per repeat for every arm.)

    python tools/_p369_reproduce_clip_arm_r1.py --repeats 4 --apply
"""
from __future__ import annotations

import argparse
import io
import json
import os
import statistics
import sys
import types
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ["CUDA_VISIBLE_DEVICES"] = ""

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.chdir(REPO)
OUT = REPO / "outputs" / "analysis" / "dinov2_hetero" / "paper_path_r1.json"
PRISTINE = str(REPO / "models" / "clip-vit-base-patch32")
ARMS = {"text_only": dict(apply_to_vision=False, apply_to_text=True),
        "both": dict(apply_to_vision=True, apply_to_text=True),
        "vision_only": dict(apply_to_vision=True, apply_to_text=False)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=4)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    from transformers import CLIPModel
    from src.dataset import create_dataloaders
    from src.lora import apply_lora_to_model
    from src.trainer import GapAwareTrainer

    torch.set_num_threads(6)
    tr, va, te = create_dataloaders(data_dir=".", dataset_name="flickr30k",
                                    batch_size=128, max_samples=5000)
    print("[loader] val pairs = %d  (protocol loader: num_workers auto, batch 128)"
          % len(va.dataset), flush=True)

    class Shim:
        """Only what `_compute_retrieval_metrics` touches (src/trainer.py:785-838)."""
        pass

    rep = {"script": "tools/_p369_reproduce_clip_arm_r1.py",
           "question": "does the archived R@1 reproduce through the protocol's own loader "
                       "and metric function, from the archived checkpoint?",
           "loader": {"val_pairs": len(va.dataset), "batch_size": 128,
                      "source": "src.dataset.create_dataloaders(data_dir='.', "
                                "max_samples=5000) -- the protocol's own loader, i.e. with "
                                "the augmented gallery transform"},
           "metric": "src.trainer.GapAwareTrainer._compute_retrieval_metrics (unmodified)",
           "arms": {}}

    for arm, flags in ARMS.items():
        ckp = REPO / "outputs" / "strict_freeze" / arm / "seed42" / "last_checkpoint.pt"
        ck = torch.load(str(ckp), map_location="cpu", weights_only=False)
        model, lora_layers, _ = apply_lora_to_model(
            CLIPModel.from_pretrained(PRISTINE, local_files_only=True).eval(),
            rank=8, alpha=16, dropout=0.0, target_modules=["q_proj", "v_proj"], **flags)
        assert set(ck["lora_state_dict"]) == set(lora_layers)
        for k, w in lora_layers.items():
            w.lora_A.data.copy_(ck["lora_state_dict"][k]["A"].float())
            w.lora_B.data.copy_(ck["lora_state_dict"][k]["B"].float())
        model.eval()
        shim = Shim()
        shim.model, shim.device, shim.processor = model, "cpu", None
        shim._compute_retrieval_metrics = types.MethodType(
            GapAwareTrainer._compute_retrieval_metrics, shim)

        r1s = []
        for r in range(a.repeats):
            m = shim._compute_retrieval_metrics(va)          # protocol metric + loader
            r1s.append(float(m["R@1"]))
            print("  [%s] repeat %d: R@1=%.4f (i2t %.4f t2i %.4f) R@5=%.4f"
                  % (arm, r, m["R@1"], m["R@1_i2t"], m["R@1_t2i"], m["R@5"]), flush=True)
        with open(REPO / "outputs" / "strict_freeze" / arm / "seed42" / "results.json",
                  encoding="utf-8") as fh:
            arch = json.load(fh)
        rep["arms"][arm] = {
            "checkpoint": str(ckp.relative_to(REPO)), "checkpoint_epoch": ck.get("epoch"),
            "repeat_R1": r1s,
            "mean": statistics.mean(r1s),
            "sd": statistics.stdev(r1s) if len(r1s) > 1 else None,
            "min": min(r1s), "max": max(r1s),
            "archived_R1_final": arch["final_task_metrics"]["R@1"],
            "archived_source": "outputs/strict_freeze/%s/seed42/results.json :: "
                               "final_task_metrics.R@1" % arm,
            "archived_R1_series_in_checkpoint": [round(float(t["R@1"]), 4)
                                                 for t in ck.get("task_metrics", [])],
        }
        del model

    print(json.dumps(rep, indent=2, ensure_ascii=False))
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, indent=2, ensure_ascii=False))
        print("\n[ok] wrote %s" % OUT.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
