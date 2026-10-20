# -*- coding: utf-8 -*-
r"""A1: insert the both-tower LoRA monitoring result into the monitoring section.

Requires outputs/analysis/a1_monitor_bothtower_analysis.json (tools/_p1452_a1_bothtower_analysis.py).

    python tools/_p1458_a1_insert_bothtower.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(REPO, "outputs", "analysis", "a1_monitor_bothtower_analysis.json")
MAIN = os.path.join(REPO, "paper_a1", "main.tex")
ANCHOR = ("(\\texttt{outputs/\\allowbreak analysis/\\allowbreak a1\\_monitor\\_diagnosis.json}).")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(AN):
        print("  both-tower analysis not ready")
        return 0
    d = json.load(io.open(AN, encoding="utf-8"))
    s = d["summary"]
    doms = ", ".join(d["per_run"])
    sent = (" Adapting both towers rather than the text tower alone does not change the picture: over %s the\n"
            "minimum-mass rule loses $%.1f$ points of accuracy on average (worst $%.1f$), against $%.1f$ for the last\n"
            "epoch and $%.1f$ for the first epoch\n"
            "(\\texttt{outputs/\\allowbreak analysis/\\allowbreak a1\\_monitor\\_bothtower.json})."
            % (doms, s["mass_regret"]["mean"], s["mass_regret"]["max"], s["last_regret"]["mean"],
               s["first_regret"]["mean"]))
    t = io.open(MAIN, encoding="utf-8").read()
    if "Adapting both towers rather than the text tower alone" in t:
        print("  already inserted")
        return 0
    assert t.count(ANCHOR) == 1, t.count(ANCHOR)
    t = t.replace(ANCHOR, ANCHOR + sent, 1)
    print("  sentence inserted")
    if a.apply:
        io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
        print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
