#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1650_diagnose_p1640_metric_bug.py -- locate the exact line that puts relaxed_accuracy
into arms.*.token_f1, by calling the generator's own arm_from_payload on the real archives.

Read-only.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ANA = ROOT / "outputs/analysis"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

import importlib.util


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


p1640 = load_module("p1640", str(ROOT / "tools/_p1640_p3_second_downstream.py"))
print("loaded _p1640; checking its metric path on the real per-arm archives")

per = {t: json.loads((ANA / ("p3_second_downstream_%s.json" % t)).read_text(encoding="utf-8"))
       for t in ("base", "5", "6")}

print("\n=== the imported token_f1's signature and behaviour ===")
norm, token_f1 = p1640.metric_functions()
print("  token_f1('yes','yes')  =", token_f1("yes", "yes"), "  <- strings zip CHARACTER-wise")
print("  token_f1(['yes'],['yes']) =", token_f1(["yes"], ["yes"]), "  <- list form (correct)")
print("  norm('Yes.') =", norm("Yes."))

print("\n=== arm_from_payload on the real archives ===")
for t in ("base", "5", "6"):
    arm = p1640.arm_from_payload(per[t], "aggregate")
    print("  %-5s arm_from_payload.token_f1 = %.10f | archive token_f1 = %.10f | archive relaxed = %.10f"
          % (t, arm["token_f1"], per[t]["token_f1"], per[t].get("relaxed_accuracy")))
    print("        archived_token_f1 field = %.10f" % arm["archived_token_f1"])

print("\n=== the buggy line ===")
import inspect
src = inspect.getsource(p1640.arm_from_payload)
for i, ln in enumerate(src.split("\n"), 1):
    if "token_f1" in ln or "f1 =" in ln or "relaxed" in ln:
        print("  arm_from_payload line %d: %s" % (i, ln.rstrip()))

print("\n=== how the eval path computes per-question F1 (correct form) ===")
ev = inspect.getsource(p1640)
for i, ln in enumerate(ev.split("\n"), 1):
    if "per_f1 = float(token_f1(" in ln:
        print("  line %d: %s" % (i, ln.strip()))

print("\n=== verdict rule lines ===")
for i, ln in enumerate(ev.split("\n"), 1):
    if "both_keep" in ln or "both_lose" in ln or "verdict = (" in ln:
        print("  line %d: %s" % (i, ln.rstrip()))

print("\n=== _interval percentile lines ===")
for i, ln in enumerate(ev.split("\n"), 1):
    if "percentile" in ln:
        print("  line %d: %s" % (i, ln.strip()))
