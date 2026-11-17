#!/usr/bin/env python3
"""Paper B v2 submission gate: data, claims, build, package."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "paper_b_v2/manuscript/main.pdf"
BIB = ROOT / "paper_b_v2/manuscript/references.bib"
PKG = ROOT / "SUBMISSION/PaperBv2_PRL_2026-11-15"
REPORT = ROOT / "paper_b_v2/results/gate_report.json"
fails = []
notes = []


def require(cond, msg):
    if not cond:
        fails.append(msg)


def count_runs(path: Path, expected: int, label: str):
    files = [p for p in path.glob("*.json") if p.name != "summary.json"] if path.exists() else []
    complete = 0
    for p in files:
        try:
            if len(json.loads(p.read_text(encoding="utf-8")).get("epochs", [])) == 3:
                complete += 1
        except Exception:
            pass
    require(complete == expected, f"{label}: {complete}/{expected} complete")
    notes.append(f"{label}: {complete}/{expected}")


# Data coverage
count_runs(ROOT / "outputs/paper_b/runs", 144, "B32 frozen")
for d in ["runs_b16", "runs_b16_r16", "runs_b16_r32", "runs_b16_r64"]:
    count_runs(ROOT / "outputs/paper_b" / d, 36, f"B16 {d}")
for d in ["runs_b32_r6_full", "runs_b32_r12_full", "runs_b32_r24_full", "runs_b32_r48_full", "runs_b32_split2_full"]:
    count_runs(ROOT / "cloud/p1_retrieved/outputs/paper_b" / d, 36, f"P1 {d}")
count_runs(ROOT / "cloud/p1_retrieved/outputs/paper_b/runs_siglip_r8_dtd", 12, "P1 SigLIP dtd")
count_runs(ROOT / "outputs/paper_b/qwen_textvqa", 16, "TextVQA sweep")
count_runs(ROOT / "outputs/paper_b/qwen_vqav2", 16, "VQAv2 sweep")
count_runs(ROOT / "outputs/paper_b/qwen_chartqa", 16, "ChartQA sweep")
count_runs(ROOT / "cloud/p1_retrieved/outputs/paper_b/runs_siglip_r8_other", 24, "P1 SigLIP other")

# Result JSONs
for rel, key in [("paper_b_v2/results/p1_full.json", "r6"), ("paper_b_v2/results/p1_siglip_valid.json", "n_runs")]:
    p = ROOT / rel
    require(p.exists(), f"missing {rel}")
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        require(key in d, f"{rel} missing {key}")

# Manuscript
require(PDF.exists(), "manuscript PDF missing")
if PDF.exists():
    text = subprocess.run(["pdftotext", str(PDF), "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(PDF)], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout).group(1))
    notes.append(f"PDF pages: {pages}")
    require(pages >= 9, f"PDF too short: {pages}")
    refs = len(re.findall(r"^\[\d+\]", text, re.M))
    notes.append(f"rendered references: {refs}")
    require(refs >= 20, f"references <20: {refs}")
    abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", (ROOT / "paper_b_v2/manuscript/main.tex").read_text(encoding="utf-8"), re.S).group(1)
    abstract = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})?", " ", abstract)
    abstract = re.sub(r"[\\{}%]", " ", abstract)
    words = len(abstract.split())
    notes.append(f"abstract words: {words}")
    require(words <= 250, f"abstract >250: {words}")

# No old/self papers in bib
bib = BIB.read_text(encoding="utf-8")
for bad in ["wan2026", "paper3", "P3"]:
    require(bad.lower() not in bib.lower(), f"old/self trace in bib: {bad}")

# Fonts
fonts = subprocess.run(["pdffonts", str(PDF)], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
require("Type 3" not in fonts, "Type 3 font present")
require("TimesNewRoman" in fonts, "Times New Roman missing")

# Package
required = ["Manuscript.pdf", "TitlePage.pdf", "CoverLetter.pdf", "Declarations.pdf", "Declarations.docx",
            "Highlights.pdf", "Highlights.docx", "GraphicalAbstract.pdf", "AuthorshipConfirmation.pdf",
            "LaTeXSource.zip", "README.md", "SHA256SUMS.txt"]
for f in required:
    require((PKG / f).exists(), f"package missing {f}")
if (PKG / "Manuscript.pdf").exists():
    pkg_pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(PKG / "Manuscript.pdf")], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout).group(1))
    notes.append(f"package manuscript pages: {pkg_pages}")
    require(pkg_pages == pages, f"package manuscript page mismatch: {pkg_pages} vs {pages}")
if (PKG / "LaTeXSource.zip").exists():
    import zipfile
    names = zipfile.ZipFile(PKG / "LaTeXSource.zip").namelist()
    require(not any("paper3" in n.lower() or "wan2026" in n.lower() for n in names), "old/self trace in source zip")
    notes.append(f"source zip entries: {len(names)}")

out = {"status": "PASS" if not fails else "FAIL", "fails": fails, "notes": notes}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
print(json.dumps(out, indent=2))
raise SystemExit(0 if not fails else 1)
