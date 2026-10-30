# -*- coding: utf-8 -*-
r"""p368 -- are the archived strict-freeze checkpoints the FINAL-epoch weights?

`src/trainer.py:353-356` writes `best_checkpoint.pt` whenever val loss improves, so the
file need NOT be the epoch-10 model.  The DINOv2 audit's re-measurements load
`last_checkpoint.pt`; if that is an earlier epoch, a re-measured R@1 is not comparable with
the archived `final_task_metrics`.  Reads the `epoch` field of every strict-freeze
checkpoint plus the archived per-epoch task metrics.

    python tools/_p368_checkpoint_epochs.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ["CUDA_VISIBLE_DEVICES"] = ""

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "dinov2_hetero" / "checkpoint_epochs.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    rep = {"script": "tools/_p368_checkpoint_epochs.py",
           "why": "best_checkpoint.pt is written on val-loss improvement, not at the end",
           "clip_strict_freeze": {}, "dinov2_hetero": {}}

    for arm in ("text_only", "both", "vision_only"):
        d = REPO / "outputs" / "strict_freeze" / arm / "seed42"
        rec = {}
        for name in ("best_checkpoint.pt", "last_checkpoint.pt"):
            f = d / name
            if not f.exists():
                rec[name] = None
                continue
            ck = torch.load(str(f), map_location="cpu", weights_only=False)
            rec[name] = {"epoch": ck.get("epoch"),
                         "n_train_losses": len(ck.get("train_losses", [])),
                         "n_val_losses": len(ck.get("val_losses", [])),
                         "task_R1_per_epoch": [round(float(t["R@1"]), 4)
                                               for t in ck.get("task_metrics", [])],
                         "val_losses": [round(float(v), 4) for v in ck.get("val_losses", [])],
                         "gap_CG_per_epoch": [round(float(g["centroid_gap"]), 4)
                                              for g in ck.get("gap_history", [])]}
        p = d / "results.json"
        if p.exists():
            r = json.loads(p.read_text(encoding="utf-8"))
            rec["archived"] = {"R1_final": r["final_task_metrics"]["R@1"],
                               "CG_final": r["final_gap"]["centroid_gap"],
                               "source": str(p.relative_to(REPO))}
        rep["clip_strict_freeze"][arm] = rec

    dp = REPO / "outputs" / "analysis" / "dinov2_hetero" / "fitted"
    for arm in ("text_only", "both", "vision_only"):
        d = dp / arm / "seed42"
        rec = {}
        for name in ("best_checkpoint.pt", "last_checkpoint.pt"):
            f = d / name
            if not f.exists():
                rec[name] = None
                continue
            ck = torch.load(str(f), map_location="cpu", weights_only=False)
            rec[name] = {"epoch": ck.get("epoch"),
                         "n_val_losses": len(ck.get("val_losses", [])),
                         "task_R1_per_epoch": [round(float(t["R@1"]), 4)
                                               for t in ck.get("task_metrics", [])]}
        rep["dinov2_hetero"][arm] = rec

    print(json.dumps(rep, indent=1, ensure_ascii=False))
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, indent=2, ensure_ascii=False))
        print("\n[ok] wrote %s" % OUT.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
