# -*- coding: utf-8 -*-
r"""Reference the new subsection and proposition, and extend the A1 claim ledger with the new numbers.

    python tools/_p1303_wire_and_ledger.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")
LEDGER = os.path.join(REPO, "tools", "_claim_ledger_a1.py")

REF_OLD = "Two matched-gap pairs settle the question"
REF_NEW = "Two matched-gap pairs settle the question (a denser sweep and real checkpoints in Section~\\ref{sec:realpairs})"

LOWER_OLD = "The bound turns the empirical dissociation into a statement about the statistic class"
LOWER_NEW = "Proposition~\\ref{prop:lowerbound} turns the empirical dissociation into a statement about the statistic class"

LEDGER_ADD = '''    # ---- dense sweep, real checkpoints, lower bound (novelty round b)
    dense = load("outputs/analysis/a1_matched_gap_dense.json")["models"]
    d_spreads = {tag: v["matched_tol003"]["spread"] for tag, v in dense.items() if v.get("matched_tol003")}
    claim("dense spread CLIP B/32", 50.6, d_spreads["clip32"], "...a1_matched_gap_dense:clip32", 1)
    claim("dense spread CLIP B/16", 54.4, d_spreads["clip16"], "...:clip16", 1)
    claim("dense spread OpenCLIP", 48.0, d_spreads["openclip"], "...:openclip", 1)
    claim("dense spread SigLIP", 7.7, d_spreads["siglip"], "...:siglip", 1)
    claim("dense spread CLIP L/14", 62.0, d_spreads["vitl"], "...:vitl", 1)
    rp = load("outputs/analysis/a1_real_checkpoint_pairs.json")
    claim("real checkpoint pairs", 31, len(rp["pairs"]), "...a1_real_checkpoint_pairs:pairs", 0)
    claim("widest real pair spread", 6.6, rp["pairs"][0]["dtop1"], "...:pairs[0].dtop1", 1)
    claim("widest real pair dCG", 0.002, rp["pairs"][0]["dCG"], "...:pairs[0].dCG", 3)
    claim("DTD within-dataset spread", 2.2, rp["within_dataset"]["dtd"]["widest_pair_at_0.01"][0],
          "...:within_dataset.dtd", 1)
    claim("DTD within-dataset dCG", 0.001, rp["within_dataset"]["dtd"]["widest_pair_at_0.01"][1],
          "...:within_dataset.dtd dCG", 3)
    lb = load("outputs/analysis/a1_lower_bound_constants.json")
    claim("class-spread constant L", 1.013, lb["text_embedding_spread_L"], "...a1_lower_bound_constants:L", 3)
    mm = load("outputs/analysis/a1_margin_mass.json")
    claim("margin mass at eps=0.01", 0.681, mm["correlation_with_top1"] and
          next(r for r in mm["rows"] if r["family"] == "frozen")["mass_eps_0.01"],
          "...a1_margin_mass:frozen.mass_eps_0.01", 3)
    claim("margin mass at eps=0.02", 0.875, next(r for r in mm["rows"] if r["family"] == "frozen")["mass_eps_0.02"],
          "...:frozen.mass_eps_0.02", 3)
    claim("mass(0.01) vs top-1 correlation", -0.996, mm["correlation_with_top1"]["mass_eps_0.01"],
          "...:correlation_with_top1.mass_eps_0.01", 3)
    claim("CG vs top-1 correlation (same pool)", -0.154, mm["correlation_with_top1"]["CG"],
          "...:correlation_with_top1.CG", 3)

    # ---- epoch sweep correlation (manuscript abstract/intro/epoch subsection)'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    print(f"  ref anchor: {t.count(REF_OLD)} | lower anchor: {t.count(LOWER_OLD)}")
    assert t.count(REF_OLD) == 1 and t.count(LOWER_OLD) == 1
    t = t.replace(REF_OLD, REF_NEW, 1).replace(LOWER_OLD, LOWER_NEW, 1)
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  references wired")

    led = io.open(LEDGER, encoding="utf-8").read()
    if "dense sweep, real checkpoints, lower bound" in led:
        print("  ledger already extended")
    else:
        anchor = "    # ---- epoch sweep correlation (manuscript abstract/intro/epoch subsection)"
        assert led.count(anchor) == 1
        led = led.replace(anchor, LEDGER_ADD, 1)
        io.open(LEDGER, "w", encoding="utf-8", newline="").write(led)
        print("  ledger extended")
    if not a.apply:
        print("  (dry run)")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
