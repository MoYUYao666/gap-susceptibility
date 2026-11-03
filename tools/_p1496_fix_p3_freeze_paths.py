# -*- coding: utf-8 -*-
"""Point the P3 freeze manifest and profile at the archived location of the rejected package."""
import ast
import io
import json

OLD = "SUBMISSION/P3_PRL_revision"
NEW = "SUBMISSION/_archive/P3_PRL_rejected_2026-10-21"

p = "tools/paper_audit/freeze/p3_prl.json"
d = json.load(io.open(p, encoding="utf-8"))
changed = False
for key in ("sha256", "paths"):
    if key not in d:
        continue
    if isinstance(d[key], dict):
        d[key] = {k.replace(OLD, NEW): v for k, v in d[key].items()}
        changed = changed or any(OLD in k for k in {})
    elif isinstance(d[key], list):
        d[key] = [x.replace(OLD, NEW) for x in d[key]]
if changed or True:
    io.open(p, "w", encoding="utf-8", newline="").write(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
    print("freeze manifest updated")

q = "tools/paper_audit/profiles.py"
t = io.open(q, encoding="utf-8").read()
if NEW not in t:
    assert t.count(OLD) == 2, t.count(OLD)
    t = t.replace(OLD, NEW)
    io.open(q, "w", encoding="utf-8", newline="").write(t)
    ast.parse(t)
    print("profile paths updated")
