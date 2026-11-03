#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1641_recon_pope_integration.py -- read-only recon for task-18 (POPE integration).

Answers, before any edit is made:
  1. Does the POPE archive exist yet? (dev must NOT write if it is missing)
  2. Supplementary section inventory: how many \section entries, and which index is
     the VQA-RAD section (the plan calls it "S28")?  This decides whether adding a
     POPE subsection changes the total count and thus main.tex's "S1--S46" pointer.
  3. Where the audit needles and the provenance manifest live, and their formats.

Output: outputs/analysis/p3_pope_recon.json
"""
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "outputs", "analysis")
os.makedirs(OUTDIR, exist_ok=True)

SUPP = os.path.join(ROOT, "paper3", "paper_ieee", "supplementary", "supplementary.tex")
MAIN = os.path.join(ROOT, "paper3", "paper_ieee", "main.tex")
ARCH = ["outputs/analysis/p3_second_downstream.json",
        "outputs/analysis/p3_second_downstream_base.json",
        "outputs/analysis/p3_second_downstream_5.json",
        "outputs/analysis/p3_second_downstream_6.json"]

report = {"archive": {}, "supplementary": {}, "main_pointer": None, "files": {}}

# ---- 1. archive presence
for rel in ARCH:
    p = os.path.join(ROOT, rel)
    report["archive"][rel] = {
        "exists": os.path.exists(p),
        "size": os.path.getsize(p) if os.path.exists(p) else None,
        "mtime": __import__("datetime").datetime.fromtimestamp(
            os.path.getmtime(p)).isoformat(timespec="seconds") if os.path.exists(p) else None,
    }
report["archive_all_present"] = all(v["exists"] for v in report["archive"].values())

# ---- 2. supplementary section inventory
txt = io.open(SUPP, encoding="utf-8").read()
secs = []
for m in re.finditer(r"\\section\*?\{([^}]*)\}", txt):
    # line number of the match
    line = txt[:m.start()].count("\n") + 1
    secs.append({"index": len(secs) + 1, "title": m.group(1), "line": line})
report["supplementary"] = {
    "n_sections": len(secs),
    "sections": secs,
}
# locate the VQA-RAD section index
vqa = next((s for s in secs if "VQA" in s["title"]), None)
report["supplementary"]["vqa_section"] = vqa

# also: \subsection inventory after the VQA section (does the file use subsections?)
subsecs = []
for m in re.finditer(r"\\subsection\*?\{([^}]*)\}", txt):
    line = txt[:m.start()].count("\n") + 1
    subsecs.append({"title": m.group(1), "line": line})
report["supplementary"]["n_subsections"] = len(subsecs)
report["supplementary"]["subsections"] = subsecs

# tables / labels near VQA
labels = []
for m in re.finditer(r"\\label\{([^}]*)\}", txt):
    line = txt[:m.start()].count("\n") + 1
    labels.append({"label": m.group(1), "line": line})
report["supplementary"]["labels_near_vqa"] = [
    x for x in labels if vqa and abs(x["line"] - vqa["line"]) < 200]

# ---- 3. main.tex pointer
mtxt = io.open(MAIN, encoding="utf-8").read()
mptr = re.search(r"Supplementary Sections?~([^)]*S\d+--S\d+)", mtxt)
if not mptr:
    mptr = re.search(r"(S\d+--S\d+)", mtxt)
if mptr:
    line = mtxt[:mptr.start()].count("\n") + 1
    report["main_pointer"] = {"text": mptr.group(1), "line": line,
                              "context": mtxt.split("\n")[line - 1].strip()[:300]}

# ---- 4. files we will have to touch
for rel in ("paper3/paper_ieee/audit_check.py", "paper3/paper_ieee/audit_pdf.py",
            "tools/_p1637_p3_reproduce_all.py", "tools/_p1428_provenance_gate.py",
            "docs/provenance_manifest.json", "paper3/paper_ieee/main.tex"):
    p = os.path.join(ROOT, rel)
    report["files"][rel] = {"exists": os.path.exists(p),
                            "size": os.path.getsize(p) if os.path.exists(p) else None,
                            "lines": (io.open(p, encoding="utf-8", errors="replace").read().count("\n") + 1)
                            if os.path.exists(p) else None}

dst = os.path.join(OUTDIR, "p3_pope_recon.json")
with open(dst, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=1, ensure_ascii=False)

print("ARCHIVE ALL PRESENT:", report["archive_all_present"])
for k, v in report["archive"].items():
    print("  %-52s exists=%s size=%s" % (k, v["exists"], v["size"]))
print("\nSUPPLEMENTARY: %d \\section entries" % report["supplementary"]["n_sections"])
for s in report["supplementary"]["sections"]:
    mark = "  <-- VQA-RAD" if vqa and s["index"] == vqa["index"] else ""
    print("  S%-3d line %-5d %s%s" % (s["index"], s["line"], s["title"][:70], mark))
print("\nsubsections: %d" % report["supplementary"]["n_subsections"])
print("main pointer:", report["main_pointer"])
print("\nfiles to touch:")
for k, v in report["files"].items():
    print("  %-46s exists=%s lines=%s" % (k, v["exists"], v["lines"]))
print("\nwrote", dst)
