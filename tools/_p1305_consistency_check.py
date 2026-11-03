# -*- coding: utf-8 -*-
"""Cross-check that every artefact is on the latest version.

Layers checked:
  1. manuscript      live main.pdf page count vs package Manuscript.pdf, hashes of the mapped files
  2. package        expected files, source zip contains the current main.tex and figures
  3. ledgers        A1 / main / Paper A counts, and claim-ledger freshness against sources
  4. documents      stale numbers in HANDOFF, map, which-paper, READMEs (page counts, ledger counts, "three backbones")
  5. mirror prep    the staging list covers every new archive and script
  6. git            working tree state
"""
import glob
import hashlib
import io
import json
import os
import re
import subprocess
import zipfile

from pypdf import PdfReader

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(REPO, "SUBMISSION", "A1_PatternAnalysisApplications")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def pages(p):
    return len(PdfReader(p).pages)


def main() -> int:
    problems, notes = [], []
    live = os.path.join(REPO, "paper_a1", "main.pdf")
    n_live = pages(live)
    print(f"live main.pdf: {n_live} pages")

    # 1. package copies
    mapping = [("Manuscript.pdf", "paper_a1/main.pdf"), ("Title Page.pdf", "paper_a1/title_page.pdf"),
               ("Cover Letter.pdf", "paper_a1/cover_letter_paa.pdf"),
               ("Graphical Abstract.pdf", "paper_a1/figures/graphical_abstract.pdf")]
    for pkg_name, live_rel in mapping:
        pkg_p = os.path.join(PKG, pkg_name)
        live_p = os.path.join(REPO, live_rel)
        if not os.path.exists(pkg_p):
            problems.append(f"package missing {pkg_name}")
            continue
        same = sha(pkg_p) == sha(live_p)
        if not same:
            problems.append(f"package {pkg_name} differs from {live_rel}")
        else:
            notes.append(f"package {pkg_name} == {live_rel}")
    if os.path.exists(os.path.join(PKG, "Manuscript.pdf")):
        print(f"package Manuscript.pdf: {pages(os.path.join(PKG, 'Manuscript.pdf'))} pages")

    # 2. source zip
    zpath = os.path.join(PKG, "latex_source.zip")
    if os.path.exists(zpath):
        z = zipfile.ZipFile(zpath)
        names = z.namelist()
        tex = [n for n in names if n.endswith("main.tex")]
        figs = [n for n in names if n.startswith("figures/")]
        print(f"source zip: {len(names)} entries | main.tex: {len(tex)} | figures: {len(figs)}")
        if tex:
            zip_tex = z.read(tex[0]).decode("utf-8", "ignore")
            live_tex = io.open(os.path.join(REPO, "paper_a1", "main.tex"), encoding="utf-8").read()
            if zip_tex.strip() != live_tex.strip():
                problems.append("source zip main.tex differs from live main.tex")
            else:
                notes.append("source zip main.tex is current")
        else:
            problems.append("source zip has no main.tex")
    else:
        problems.append("source zip missing")

    # 3. ledgers
    for name, path in (("A1", "outputs/analysis/claim_ledger_a1.json"),
                       ("main", "outputs/analysis/claim_ledger.json"),
                       ("PaperA", "outputs/analysis/claim_ledger_paperA.json")):
        p = os.path.join(REPO, path)
        if not os.path.exists(p):
            problems.append(f"ledger missing: {path}")
            continue
        d = json.load(io.open(p, encoding="utf-8"))
        got = d.get("pass", d.get("通过", d.get("pass_count", "?")))
        total = d.get("total", d.get("总", "?"))
        notes.append(f"ledger {name}: pass={got} total={total} mtime={int(os.path.getmtime(p))}")
    ledger_fresh = int(os.path.getmtime(os.path.join(REPO, "outputs/analysis/claim_ledger_a1.json")))
    a1_mtime = max(int(os.path.getmtime(p)) for p in glob.glob(os.path.join(REPO, "paper_a1", "*.tex")))
    if ledger_fresh < a1_mtime:
        problems.append("A1 claim ledger is older than the manuscript sources (J-01)")

    # 4. stale numbers in documents
    docs = ["HANDOFF.md", "文件地图.md", "哪篇是哪篇.md", "AUTOMATION_HANDOVER.md",
            "SUBMISSION/README.md", os.path.join("SUBMISSION", "A1_PatternAnalysisApplications", "README.md")]
    patterns = {"53 页": "old page count", "55 页": "old page count", "97/97": "old ledger count",
                "three architectures": "model-count phrasing", "three backbones": "model-count phrasing"}
    print("\ndocument scan:")
    for rel in docs:
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            problems.append(f"document missing: {rel}")
            continue
        t = io.open(p, encoding="utf-8", errors="ignore").read()
        hits = [f"{k} ({v})" for k, v in patterns.items() if k in t]
        if hits:
            notes.append(f"{rel}: {', '.join(hits)}")
        else:
            notes.append(f"{rel}: clean")

    # 5. mirror prep coverage
    mp = os.path.join(REPO, "tools", "_p1284_prepare_public_mirror.py")
    if os.path.exists(mp):
        mt = io.open(mp, encoding="utf-8").read()
        need = ["a1_matched_gap_dense.json", "a1_real_checkpoint_pairs.json",
                "a1_lower_bound_constants.json", "a1_margin_mass.json",
                "_p1299_margin_mass.py", "_p1300_matched_gap_dense.py",
                "_p1301_lower_bound_constants.py", "_p1302_insert_novelty_b.py"]
        missing = [n for n in need if n not in mt]
        if missing:
            problems.append("mirror staging list misses: " + ", ".join(missing))
        else:
            notes.append("mirror staging list covers the new files")

    # 6. git
    st = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    print(f"git: {'clean' if not st else str(len(st.splitlines())) + ' uncommitted'}")
    if st:
        notes.append("uncommitted: " + "; ".join(st.splitlines()[:6]))

    print("\n=== NOTES ===")
    for n in notes:
        print("  -", n)
    print("\n=== PROBLEMS ===")
    if problems:
        for p in problems:
            print("  !!", p)
        return 1
    print("  none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
