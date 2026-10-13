# -*- coding: utf-8 -*-
r"""p370 -- vision_only/seed42: is the archived epoch-10 R@1 (0.700) reproducible from the
epoch-10 weights, or is only that one evaluation anomalous?

p369 showed that the PROTOCOL'S OWN loader + metric on `last_checkpoint.pt` gives
R@1 = 0.675-0.682 (4 draws), while the archived `final_task_metrics.R@1` = 0.7000.
`saved per-epoch series (inside the checkpoint) = [0.643, 0.652, 0.674, 0.673, 0.680,
0.675, 0.688, 0.694, 0.682, 0.700]`.

If the per-epoch series is internally reproducible, then evaluating the *epoch-9* weights
(`best_checkpoint.pt`, val-loss minimum) should give ~0.694 and the epoch-10 entry (0.700)
is the anomaly.  If instead BOTH checkpoints re-evaluate to ~0.68, the whole late-epoch
tail of the recorded series is inconsistent with fresh draws.

    python tools/_p370_vision_only_checkpoint_identity.py --repeats 3 --apply
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
OUT = REPO / "outputs" / "analysis" / "dinov2_hetero" / "vision_only_ckpt_identity.json"
PRISTINE = str(REPO / "models" / "clip-vit-base-patch32")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    from transformers import CLIPModel
    from src.dataset import create_dataloaders
    from src.lora import apply_lora_to_model
    from src.trainer import GapAwareTrainer

    torch.set_num_threads(6)
    d = REPO / "outputs" / "strict_freeze" / "vision_only" / "seed42"
    cks = {}
    for name in ("best_checkpoint.pt", "last_checkpoint.pt"):
        cks[name] = torch.load(str(d / name), map_location="cpu", weights_only=False)

    same = None
    if set(cks["best_checkpoint.pt"]["lora_state_dict"]) == set(
            cks["last_checkpoint.pt"]["lora_state_dict"]):
        diffs = [float((cks["best_checkpoint.pt"]["lora_state_dict"][k]["A"].float()
                        - cks["last_checkpoint.pt"]["lora_state_dict"][k]["A"].float()).abs().max())
                 for k in cks["best_checkpoint.pt"]["lora_state_dict"]]
        diffs += [float((cks["best_checkpoint.pt"]["lora_state_dict"][k]["B"].float()
                         - cks["last_checkpoint.pt"]["lora_state_dict"][k]["B"].float()).abs().max())
                  for k in cks["best_checkpoint.pt"]["lora_state_dict"]]
        same = max(diffs) == 0.0

    _, va, _ = create_dataloaders(data_dir=".", dataset_name="flickr30k", batch_size=128,
                                  max_samples=5000)

    class Shim:
        pass

    rep = {"script": "tools/_p370_vision_only_checkpoint_identity.py",
           "why": "p369: protocol loader+metric on last_checkpoint.pt gives 0.675-0.682, "
                  "archived says 0.7000",
           "checkpoints": {k: {"epoch": v.get("epoch"),
                               "n_val_losses": len(v.get("val_losses", [])),
                               "task_R1_per_epoch": [round(float(t["R@1"]), 4)
                                                     for t in v.get("task_metrics", [])],
                               "val_losses": [round(float(x), 4)
                                              for x in v.get("val_losses", [])]}
                           for k, v in cks.items()},
           "best_equals_last_weights": same,
           "evaluations": {},
           "archived_R1_final": 0.7000}

    for name, ck in cks.items():
        model, lora_layers, _ = apply_lora_to_model(
            CLIPModel.from_pretrained(PRISTINE, local_files_only=True).eval(),
            rank=8, alpha=16, dropout=0.0, target_modules=["q_proj", "v_proj"],
            apply_to_vision=True, apply_to_text=False)
        for k, w in lora_layers.items():
            w.lora_A.data.copy_(ck["lora_state_dict"][k]["A"].float())
            w.lora_B.data.copy_(ck["lora_state_dict"][k]["B"].float())
        model.eval()
        shim = Shim()
        shim.model, shim.device, shim.processor = model, "cpu", None
        shim._compute_retrieval_metrics = types.MethodType(
            GapAwareTrainer._compute_retrieval_metrics, shim)
        r1s = [float(shim._compute_retrieval_metrics(va)["R@1"]) for _ in range(a.repeats)]
        rep["evaluations"][name] = {
            "epoch": ck.get("epoch"), "R1_fresh_draws": r1s,
            "mean": statistics.mean(r1s),
            "sd": statistics.stdev(r1s) if len(r1s) > 1 else None,
            "recorded_series_value_at_that_epoch": (
                [round(float(t["R@1"]), 4) for t in ck.get("task_metrics", [])] or [None])[-1],
        }
        print("  %-22s epoch=%s  fresh R@1 %s  mean %.4f   series-last %s"
              % (name, ck.get("epoch"), ["%.4f" % x for x in r1s],
                 statistics.mean(r1s),
                 rep["evaluations"][name]["recorded_series_value_at_that_epoch"]), flush=True)
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
