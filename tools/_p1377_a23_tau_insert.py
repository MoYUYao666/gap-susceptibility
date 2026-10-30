# -*- coding: utf-8 -*-
r"""A23: insert the order-preservation (tau) positive control next to the margin-mass control.

Reads outputs/analysis/a23_tau_control.json and appends one sentence to the threshold paragraph in
paper_a2/ext_partII_domains.tex. Idempotent.

    python tools/_p1377_a23_tau_insert.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

TEX = os.path.join("paper_a2", "ext_partII_domains.tex")
JSON = os.path.join("outputs", "analysis", "a23_tau_control.json")
ANCHOR = "a within-domain, order-based diagnostic rather than a portable scalar."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.load(io.open(JSON, encoding="utf-8"))
    models = d["models"]
    r_tau = {k: v["r_tau"] for k, v in models.items()}
    r_mass = {k: v["r_mass"] for k, v in models.items()}
    tr = d["threshold_transfer"]
    tau_test = [v["test_BA"] for k, v in tr.items() if k.startswith("tau|")]
    mass_test = [v["test_BA"] for k, v in tr.items() if k.startswith("mass|")]
    sentence = (f" The positive counterpart is order preservation: on the same surgery family the measured $\\tau$ "
                f"(per-image Kendall correlation of the top-5 scores against the unshifted baseline) tracks accuracy at "
                f"$r={r_tau['bioclip']:+.2f}$ (BioCLIP) and ${r_tau['oceanclip']:+.2f}$ (OceanCLIP), against "
                f"$r={r_mass['bioclip']:+.2f}$ / ${r_mass['oceanclip']:+.2f}$ for the margin mass, and a $\\tau$ threshold "
                f"fitted on one encoder transfers to the other at balanced accuracy "
                f"${min(tau_test):.2f}$--${max(tau_test):.2f}$ where the mass threshold reaches "
                f"${min(mass_test):.2f}$--${max(mass_test):.2f}$. Order is the quantity to monitor; absolute gap and "
                f"margin scales are not.")
    t = io.open(TEX, encoding="utf-8").read()
    if "The positive counterpart is order preservation" in t:
        print("  already inserted")
        return 0
    assert t.count(ANCHOR) == 1, t.count(ANCHOR)
    t = t.replace(ANCHOR, ANCHOR + sentence, 1)
    print("  sentence:", sentence.strip()[:180], "...")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(TEX, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
