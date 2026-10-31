# -*- coding: utf-8 -*-
"""Restore the `tab:odefit` provenance entry (dropped when the map script regenerated the manifest)."""
import io
import json

MP = "tools/_p1432_provenance_map_paperA.py"
t = io.open(MP, encoding="utf-8").read()
old = '    "tab:config_groups": (None, ["outputs/analysis/strict_control_summary.json"]),'
new = ('    "tab:config_groups": (None, ["outputs/analysis/strict_control_summary.json"]),\n'
       '    "tab:odefit": ("tools/_p1440_paperA_ode_residuals.py", ["outputs/analysis/paperA_ode_residuals.json"]),')
assert old in t and "tab:odefit" not in t
io.open(MP, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
print("mapping script: tab:odefit restored")

p = "docs/provenance_manifest.json"
man = json.load(io.open(p, encoding="utf-8"))
floats = man["manuscripts"]["paperA"]["floats"]
labels = {f.get("label") for f in floats}
if "tab:odefit" not in labels:
    floats.append({
        "label": "tab:odefit",
        "kind": "table",
        "script": "tools/_p1440_paperA_ode_residuals.py",
        "archive": "outputs/analysis/paperA_ode_residuals.json",
        "archives": ["outputs/analysis/paperA_ode_residuals.json"],
        "status": "verified",
        "note": "ODE fit-quality table (96 archived runs); entry restored 2026-10-24",
    })
    json.dump(man, io.open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("manifest: tab:odefit restored")
print("paperA floats:", len(floats))