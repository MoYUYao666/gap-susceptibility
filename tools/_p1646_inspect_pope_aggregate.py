#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1646_inspect_pope_aggregate.py -- inspect the POPE aggregate's arms block versus the
per-arm archives, to resolve the token_f1 discrepancy found by _p1644.

Read-only; prints the raw fields with their paths.
"""
import json
import os
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ANA = ROOT / "outputs/analysis"

agg = json.loads((ANA / "p3_second_downstream.json").read_text(encoding="utf-8"))
per = {t: json.loads((ANA / ("p3_second_downstream_%s.json" % t)).read_text(encoding="utf-8"))
       for t in ("base", "5", "6")}

print("aggregate top-level keys:", list(agg.keys()))
print("\n=== agg['arms'] ===")
print(json.dumps(agg["arms"], indent=1, ensure_ascii=False)[:2500])

print("\n=== per-arm metric fields vs agg['arms'] ===")
print("%-6s %-14s %14s %14s" % ("arm", "metric", "agg.arms", "per-arm file"))
for t in ("base", "5", "6"):
    for m in ("accuracy", "token_f1", "pope_f1", "yes_ratio", "relaxed_accuracy",
              "yes_no_accuracy", "n_yes_no"):
        a = agg["arms"][t].get(m, "<absent>")
        p = per[t].get(m, "<absent>")
        flag = "" if a == p else "   <-- DIFFERS"
        print("%-6s %-14s %14s %14s%s" % (t, m, a, p, flag))

print("\n=== aggregate bytes around 'token_f1' ===")
raw = (ANA / "p3_second_downstream.json").read_text(encoding="utf-8")
i = raw.find('"token_f1"')
while i >= 0 and i < len(raw):
    print("  ...", raw[max(0, i - 120):i + 160].replace("\n", " "))
    i = raw.find('"token_f1"', i + 1)

print("\n=== does the aggregate carry a metric-definitions note? ===")
print(json.dumps(agg.get("meta", {}).get("metric_definitions"), indent=1))
print("\n=== caveat_sentences ===")
print(json.dumps(agg.get("caveat_sentences"), indent=1, ensure_ascii=False))
