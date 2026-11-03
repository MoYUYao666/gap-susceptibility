# -*- coding: utf-8 -*-
r"""Block until the `both/seed42` run archives its result, then print a compact summary.

Replaces repeated polling: the training run is the only thing that can produce the file, so this
waits on it and returns once, with the numbers the report and the Lead's decision need.

USAGE
    python tools/_p293_wait_both.py [--timeout-min 300]
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RES = (REPO / "outputs" / "analysis" / "dinov2_hetero" / "fitted" / "both" / "seed42"
       / "results.json")
LOG = REPO / "outputs" / "analysis" / "dinov2_hetero" / "logs" / "fitted_both_seed42.log"
TEXT_ONLY = (REPO / "outputs" / "analysis" / "dinov2_hetero" / "fitted" / "text_only"
             / "seed42" / "results.json")
FROZEN = REPO / "outputs" / "analysis" / "dinov2_hetero" / "fitted" / "frozen" / "results.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout-min", type=float, default=300)
    ap.add_argument("--poll-sec", type=int, default=60)
    a = ap.parse_args()

    t0 = time.time()
    while not RES.exists():
        if (time.time() - t0) / 60 > a.timeout_min:
            print("[timeout] %s not present after %.0f min" % (RES, a.timeout_min))
            return 2
        time.sleep(a.poll_sec)

    time.sleep(5)   # let the JSON flush
    r = json.loads(RES.read_text(encoding="utf-8"))
    print("=== both/seed42 archived at %s ===" % datetime.now(timezone.utc).isoformat(
        timespec="seconds"))
    for k in ("delta_CG", "delta_DG", "CG_initial", "CG_final", "DG_initial", "DG_final",
              "R@1", "R@5", "n_trainable_params", "n_trainable_vision_side",
              "n_trainable_text_side", "elapsed_sec", "final_train_loss",
              "lora_update_norm_frobenius", "lora_update_sum_of_layer_frobenius",
              "backbone_delta_note"):
        print("  %-32s %s" % (k, r.get(k)))
    print("  backbone_delta nonzero:",
          {g: v.get("nonzero_tensors") for g, v in (r.get("backbone_delta") or {}).items()})

    if TEXT_ONLY.exists() and FROZEN.exists():
        t = json.loads(TEXT_ONLY.read_text(encoding="utf-8"))
        f = json.loads(FROZEN.read_text(encoding="utf-8"))
        print("\n=== comparison (seed 42, n=1 per arm) ===")
        print("  frozen      CG %.4f  R@1 %.4f" % (f["CG"], f["R@1"]))
        print("  text_only   dCG %+.4f  R@1 %.4f" % (t["delta_CG"], t["R@1"]))
        print("  both        dCG %+.4f  R@1 %.4f" % (r["delta_CG"], r["R@1"]))
        more_neg = r["delta_CG"] < t["delta_CG"]
        print("\n  VERDICT: both is %s text_only (%.4f vs %.4f)"
              % ("MORE negative than" if more_neg else "LESS negative than",
                 r["delta_CG"], t["delta_CG"]))
        print("  -> ordering in this heterogeneous setting: %s"
              % ("both < text_only  (same direction as BioCLIP's both-first ordering)"
                 if more_neg else
                 "text_only < both  (opposite to BioCLIP's both-first ordering)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
