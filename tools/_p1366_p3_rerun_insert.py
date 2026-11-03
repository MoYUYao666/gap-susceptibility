# -*- coding: utf-8 -*-
r"""P3: insert the current-protocol re-run result into the conclusion.

Reads outputs/analysis/p3_rerun_protocol.json (produced by tools/_p1365_p3_rerun_protocol.py) and adds one sentence next to
the existing protocol-attribution sentence. Idempotent: refuses to insert twice.

    python tools/_p1366_p3_rerun_insert.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

TEX = os.path.join("paper3", "paper_ieee", "sections", "conclusion.tex")
JSON = os.path.join("outputs", "analysis", "p3_rerun_protocol.json")
ANCHOR = ("differ in training configuration rather than data; the crossing therefore tracks the protocol\n"
          "including its hyperparameters, which is what we claim for it.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.load(io.open(JSON, encoding="utf-8"))
    runs = d["runs"]
    ranks = sorted(int(k[1:].split("_")[0]) for k in runs)
    for k, v in runs.items():
        assert v.get("ok"), f"run {k} not ok: {v}"
    de = {int(k[1:].split("_")[0]): v["delta_E"] for k, v in runs.items()}
    e0 = runs[f"r{ranks[0]}_s42"]["E"][0]
    neg = [r for r in ranks if de[r] < 0]
    pos = [r for r in ranks if de[r] > 0]
    if neg and pos:
        boundary = f"between $r={max(neg)}$ and $r={min(pos)}$"
    elif not pos:
        boundary = f"above $r={max(ranks)}$ (no sign change up to that rank)"
    else:
        boundary = f"below $r={min(ranks)}$"
    parts = ", ".join(f"$\\Delta E={de[r]:+.0f}$ at $r={r}$" for r in ranks)
    sentence = (f" Re-running the current, reproducible script (its defaults give $E_0={e0:.1f}$, three epochs, seed 42) "
                f"yields {parts}, so the sign change lies {boundary}; the archived families were produced by earlier "
                f"script versions with $E_0=3927.0$ or $3930.5$, which is why their brackets differ by more than seed "
                f"noise.")
    t = io.open(TEX, encoding="utf-8").read()
    if "Re-running the current, reproducible script" in t:
        print("  already inserted")
        return 0
    assert t.count(ANCHOR) == 1, t.count(ANCHOR)
    t = t.replace(ANCHOR, ANCHOR + sentence, 1)
    print("  sentence:", sentence.strip()[:160], "...")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(TEX, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
