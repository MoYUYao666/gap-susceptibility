#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1643_recon_manifest_registry.py -- read-only recon (part 2): P3 manifest entries
and the reproduce_all registry layout, so the POPE additions can be made in the
established format rather than invented.

Output: outputs/analysis/p3_pope_manifest_recon.json
"""
import io
import json
import os
import re
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = ROOT / "outputs" / "analysis" / "p3_pope_manifest_recon.json"

MF = json.loads((ROOT / "docs/provenance_manifest.json").read_text(encoding="utf-8"))
REPRO = (ROOT / "tools/_p1637_p3_reproduce_all.py").read_text(encoding="utf-8")

out = {"manifest_keys": list(MF.keys()), "manuscripts": {}}
ms = MF.get("manuscripts", {})
out["manuscripts_type"] = type(ms).__name__
if isinstance(ms, dict):
    out["manuscript_ids"] = list(ms.keys())
    for k, v in ms.items():
        if isinstance(v, dict):
            out["manuscripts"][k] = {"keys": sorted(v.keys())}
            for kk, vv in v.items():
                if isinstance(vv, list):
                    out["manuscripts"][k]["n_" + kk] = len(vv)
                    if vv and isinstance(vv[0], dict):
                        out["manuscripts"][k]["example_" + kk] = vv[0]
                        out["manuscripts"][k]["example_keys_" + kk] = sorted(vv[0].keys())
elif isinstance(ms, list):
    out["n_manuscripts"] = len(ms)
    out["example"] = ms[0] if ms else None
    out["manuscript_ids"] = [m.get("id") or m.get("name") for m in ms if isinstance(m, dict)]

# ---- P3-specific: find entries mentioning p3 or POPE/VQA
flat = json.dumps(MF, ensure_ascii=False)
out["mentions_pope"] = flat.lower().count("pope")
out["mentions_vqa"] = flat.lower().count("vqa")
out["mentions_second_downstream"] = flat.lower().count("second_downstream")

# ---- reproduce_all: how are entries grouped / where does P3 live?
lines = REPRO.split("\n")
out["repro"] = {
    "n_add_calls": len(re.findall(r"\badd\(", REPRO)),
    "n_calc_calls": len(re.findall(r"\bcalc\(", REPRO)),
    "n_unsourced_calls": len(re.findall(r"\bunsourced\(", REPRO)),
    "sections_mentioned": sorted(set(re.findall(r'section="([^"]+)"', REPRO)))[:40],
    "registration_blocks": [],
    "final_report_lines": [],
}
# find lines that look like section headers / registration blocks
for i, ln in enumerate(lines, 1):
    s = ln.strip()
    if re.match(r'^#\s*[-=]{2,}', s) or (s.startswith("#") and ("register" in s.lower() or "P3" in s)):
        out["repro"]["registration_blocks"].append({"line": i, "text": s[:150]})
for i, ln in enumerate(lines, 1):
    if "MISMATCH" in ln or "UNSOURCED" in ln:
        out["repro"]["final_report_lines"].append({"line": i, "text": ln.strip()[:180]})

# how is the count of registered claims tracked?
m = re.findall(r"len\(([A-Z_]+)\)", REPRO)
out["repro"]["len_of_consts"] = sorted(set(m))[:20]
consts = {}
for mm in re.finditer(r"^([A-Z_][A-Z0-9_]*)\s*=\s*", REPRO, re.M):
    consts[mm.group(1)] = "assignment"
out["repro"]["top_consts"] = consts

dst = OUT
with open(dst, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)

print("MANIFEST keys:", out["manifest_keys"])
print("manuscripts type:", out["manuscripts_type"])
print("manuscript ids:", out.get("manuscript_ids"))
for k, v in out.get("manuscripts", {}).items():
    print("  %-24s %s" % (k, json.dumps(v, ensure_ascii=False)[:400]))
print("\nmentions: pope=%d vqa=%d second_downstream=%d"
      % (out["mentions_pope"], out["mentions_vqa"], out["mentions_second_downstream"]))
print("\nREPRO: add=%d calc=%d unsourced=%d" % (out["repro"]["n_add_calls"],
                                                out["repro"]["n_calc_calls"],
                                                out["repro"]["n_unsourced_calls"]))
print("sections:", out["repro"]["sections_mentioned"])
print("\nregistration blocks:")
for b in out["repro"]["registration_blocks"][:25]:
    print("  L%-5d %s" % (b["line"], b["text"]))
print("\nfinal report lines:")
for b in out["repro"]["final_report_lines"][:12]:
    print("  L%-5d %s" % (b["line"], b["text"]))
print("\ntop consts:", json.dumps(out["repro"]["top_consts"], indent=1)[:800])
print("\nwrote", dst)
