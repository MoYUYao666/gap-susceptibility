# -*- coding: utf-8 -*-
r"""Block until the random-head `text_only` arm finishes, then compare it with the fitted head.

This is the control the Lead added back: the fitted head has 656,384 parameters, MORE than either
adapter configuration (196,608 / 491,520), so "the text tower is pushed far" could in principle be
a property of the head rather than of the adaptation site.  Comparing the same arm under a fitted
head and under a random head separates the two:

  * if the random head ALSO moves ΔCG a lot (or is sensitive to the site), the effect is head-driven
    and the finding must be weakened;
  * if the random head barely moves it, the head's choice is not the driver.

No auto-continuation: this script starts nothing else.

USAGE
    python tools/_p293_wait_random.py [--timeout-min 90]
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DH = REPO / "outputs" / "analysis" / "dinov2_hetero"


def show(head, arm):
    p = DH / head / arm / "seed42" / "results.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    return {"head": head, "arm": arm, "delta_CG": d["delta_CG"], "delta_DG": d["delta_DG"],
            "CG_initial": d["CG_initial"], "CG_final": d["CG_final"],
            "R1": d["R@1"], "n": d["n_trainable_params"], "file": str(p.relative_to(REPO))}


def frozen(head):
    p = DH / head / "frozen" / "results.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    return {"CG": d["CG"], "DG": d["DG"], "R1": d["R@1"], "file": str(p.relative_to(REPO))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout-min", type=float, default=90)
    ap.add_argument("--poll-sec", type=int, default=45)
    a = ap.parse_args()

    target = DH / "random" / "text_only" / "seed42" / "results.json"
    t0 = time.time()
    while not target.exists():
        if (time.time() - t0) / 60 > a.timeout_min:
            print("[timeout] %s not present after %.0f min" % (target, a.timeout_min))
            return 2
        time.sleep(a.poll_sec)
    time.sleep(5)

    rnd = show("random", "text_only")
    fit = show("fitted", "text_only")
    fr, ff = frozen("random"), frozen("fitted")

    print("=== frozen baselines ===")
    for lbl, f in (("random head", fr), ("fitted head", ff)):
        print("  %-12s CG %.4f  DG %.4f  R@1 %.4f   (%s)"
              % (lbl, f["CG"], f["DG"], f["R1"], f["file"]))

    print("\n=== text_only arm, same protocol, two heads ===")
    print("  %-12s dCG %+.4f  dDG %+.4f  CG %.4f->%.4f  R@1 %.4f"
          % ("random", rnd["delta_CG"], rnd["delta_DG"], rnd["CG_initial"], rnd["CG_final"],
             rnd["R1"]))
    print("  %-12s dCG %+.4f  dDG %+.4f  CG %.4f->%.4f  R@1 %.4f"
          % ("fitted", fit["delta_CG"], fit["delta_DG"], fit["CG_initial"], fit["CG_final"],
             fit["R1"]))
    delta = rnd["delta_CG"] - fit["delta_CG"]
    print("\n  dCG(random) - dCG(fitted) = %+.4f" % delta)
    print("  |dCG| of the arm under a random head: %.4f ; under the fitted head: %.4f"
          % (abs(rnd["delta_CG"]), abs(fit["delta_CG"])))
    ratio = abs(rnd["delta_CG"]) / abs(fit["delta_CG"]) if fit["delta_CG"] else float("inf")
    print("  ratio |random| / |fitted| = %.2f" % ratio)
    print("\n  INTERPRETATION INPUTS (not a verdict):")
    print("   * fitted-head frozen R@1 = %.4f, random-head frozen R@1 = %.4f"
          % (ff["R1"], fr["R1"]))
    print("   * if the random-head arm barely moves the gap while the fitted-head arm moves it a "
          "lot, the adaptation effect is entangled with the head; if both move it comparably, the "
          "site effect does not depend on the head being fitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
