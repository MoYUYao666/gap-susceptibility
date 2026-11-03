#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1642_recon_gate_formats.py -- read-only recon of the gate formats task-18 must satisfy.

Records (no edits):
  * current section-count expectations in audit_check.py / audit_pdf.py (S1--S4x)
  * page-count expectations
  * provenance manifest entry schema (one example + key set)
  * tools/_p1637_p3_reproduce_all.py registry schema (one example + how MISSING/UNSOURCED is counted)
  * tools/_p1428_provenance_gate.py expectations
  * archive presence

Output: outputs/analysis/p3_pope_gate_recon.json
"""
import io
import json
import os
import re
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = ROOT / "outputs" / "analysis" / "p3_pope_gate_recon.json"

AUD_CHK = ROOT / "paper3/paper_ieee/audit_check.py"
AUD_PDF = ROOT / "paper3/paper_ieee/audit_pdf.py"
MANIFEST = ROOT / "docs/provenance_manifest.json"
REPRO = ROOT / "tools/_p1637_p3_reproduce_all.py"
GATE = ROOT / "tools/_p1428_provenance_gate.py"
MAIN = ROOT / "paper3/paper_ieee/main.tex"


def txt(p):
    return io.open(p, encoding="utf-8", errors="replace").read()


out = {}

# ---- archive presence (fresh check)
arch = ["outputs/analysis/p3_second_downstream.json",
        "outputs/analysis/p3_second_downstream_base.json",
        "outputs/analysis/p3_second_downstream_5.json",
        "outputs/analysis/p3_second_downstream_6.json"]
out["archive"] = {r: os.path.exists(os.path.join(ROOT, r)) for r in arch}
out["archive_all_present"] = all(out["archive"].values())

# ---- section/page expectations
for name, p in (("audit_check", AUD_CHK), ("audit_pdf", AUD_PDF)):
    t = txt(p)
    out[name] = {
        "S46_mentions": len(re.findall(r"S1--S46|S46", t)),
        "S43_mentions": len(re.findall(r"S1--S43|S43", t)),
        "pages_18_mentions": len(re.findall(r"18 pages|18pages", t)),
        "pages_10_mentions": len(re.findall(r"10 pages|10pages", t)),
        "supplementary_tex_pointer_lines": [
            ln for ln in t.split("\n") if "supplementary.tex" in ln][:5],
    }

# ---- manifest schema
try:
    mf = json.loads(txt(MANIFEST))
    out["manifest"] = {"type": type(mf).__name__}
    if isinstance(mf, dict):
        out["manifest"]["top_keys"] = list(mf.keys())[:20]
        # find a list of entries
        for k, v in mf.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                out["manifest"]["entry_list_key"] = k
                out["manifest"]["n_entries"] = len(v)
                out["manifest"]["entry_keys"] = sorted(v[0].keys())
                out["manifest"]["example"] = v[0]
                break
    elif isinstance(mf, list):
        out["manifest"]["n_entries"] = len(mf)
        out["manifest"]["entry_keys"] = sorted(mf[0].keys()) if mf else []
        out["manifest"]["example"] = mf[0] if mf else None
except Exception as e:
    out["manifest"] = {"error": str(e)}

# ---- reproduce_all registry schema
t = txt(REPRO)
out["reproduce_all"] = {
    "lines": t.count("\n") + 1,
    "has_MISMATCH_token": "MISMATCH" in t,
    "has_UNSOURCED_token": "UNSOURCED" in t,
    "def_lines": [ln.strip()[:120] for ln in t.split("\n")
                  if re.match(r"^\s*def ", ln)][:25],
    "top_level_consts": [ln.strip()[:120] for ln in t.split("\n")
                         if re.match(r"^[A-Z_][A-Z0-9_]*\s*=", ln)][:20],
}

# ---- provenance gate
t = txt(GATE)
out["provenance_gate"] = {
    "lines": t.count("\n") + 1,
    "mentions_manifest": "provenance_manifest" in t,
    "def_lines": [ln.strip()[:120] for ln in t.split("\n") if re.match(r"^\s*def ", ln)][:10],
}

# ---- main.tex pointer
mt = txt(MAIN)
m = re.search(r"Supplementary Sections?~([^)]*?S\d+--S\d+)", mt)
out["main_pointer"] = m.group(1) if m else None
out["main_pages"] = len(re.findall(r"\\begin\{document\}|\\end\{document\}", mt))

dst = OUT
with open(dst, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)

print("ARCHIVE ALL PRESENT:", out["archive_all_present"])
print(json.dumps(out["archive"], indent=1))
print("\nAUDIT expectations:")
print(json.dumps(out["audit_check"], indent=1)[:700])
print(json.dumps(out["audit_pdf"], indent=1)[:700])
print("\nMANIFEST:")
print(json.dumps(out["manifest"], indent=1, ensure_ascii=False)[:1600])
print("\nREPRODUCE_ALL:")
print(json.dumps(out["reproduce_all"], indent=1, ensure_ascii=False)[:1200])
print("\nGATE:")
print(json.dumps(out["provenance_gate"], indent=1))
print("\nMAIN POINTER:", out["main_pointer"])
print("\nwrote", dst)
