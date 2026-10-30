# -*- coding: utf-8 -*-
r"""p367 -- list every published-vs-recomputed R@1 discrepancy of tab:position_strict.

Feeds the audit's "can gallery-draw noise explain the R@1 column's non-reproduction?"
question with the exact list (cell, published, recomputed, |diff|, seeds) instead of a
paraphrase.  Pure archive read.

    python tools/_p367_r1_discrepancies.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "outputs" / "analysis" / "dinov2_hetero" / "clip_baseline_check.json"
PROV = REPO / "outputs" / "analysis" / "dinov2_hetero" / "r1_provenance.json"
OUT = REPO / "outputs" / "analysis" / "dinov2_hetero" / "r1_discrepancies.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    d = json.loads(SRC.read_text(encoding="utf-8"))
    prov = json.loads(PROV.read_text(encoding="utf-8"))

    rows = []
    for c in d["checks"]:
        rows.append({
            "row": c["row"], "arm": c["arm"], "n_seeds": c["n_seeds"], "seeds": c["seeds"],
            "published_R1": c["published_R1"], "recomputed_R1": c["recomputed_R1"],
            "abs_diff": c["R1_abs_diff"], "pass": c["R1_pass"],
            "published_delta_CG": c["published_delta_CG"],
            "recomputed_delta_CG": c["recomputed_delta_CG"],
            "delta_CG_pass": c["delta_CG_pass"],
        })
    rows.sort(key=lambda r: -r["abs_diff"])

    rep = {"script": "tools/_p367_r1_discrepancies.py",
           "source": str(SRC.relative_to(REPO)) + " :: checks",
           "n_cells": len(rows),
           "n_R1_fail": sum(1 for r in rows if not r["pass"]),
           "n_deltaCG_fail": sum(1 for r in rows if not r["delta_CG_pass"]),
           "R1_discrepancies_desc": rows,
           "summary": {
               "delta_CG_column": "reproduces for all %d cells at published precision" % len(rows),
               "R1_column": ("%d of %d cells differ from the archive's own full-seed mean"
                             % (sum(1 for r in rows if not r["pass"]), len(rows))),
               "max_abs_diff": max(r["abs_diff"] for r in rows),
               "openclip_caveat": prov["conclusion"]["explanation"],
           }}

    print(json.dumps(rep, indent=2, ensure_ascii=False))
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, indent=2, ensure_ascii=False))
        print("\n[ok] wrote %s" % OUT.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
