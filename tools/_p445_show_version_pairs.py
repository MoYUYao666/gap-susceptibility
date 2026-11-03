#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p445_show_version_pairs.py -- print the archived paired runs that carry a
transformers-version note, so the version sensitivity can be judged from data."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "paper3", "scripts", "outputs", "experiments")
for f in sorted(os.listdir(D)):
    if not f.endswith(".json"):
        continue
    p = os.path.join(D, f)
    try:
        with open(p, encoding="utf-8") as fh:
            o = json.load(fh)
    except Exception:
        continue
    s = json.dumps(o, ensure_ascii=False)
    if "transformers" in s.lower():
        print("=" * 70)
        print(f)
        print(json.dumps(o, ensure_ascii=False, indent=1)[:1800])
