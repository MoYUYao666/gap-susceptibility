# -*- coding: utf-8 -*-
r"""Refresh the A1 (PAA) and Paper A (Neurocomputing) working packages so that the
package copies match the current live manuscript, the source archive matches the
current sources, and the package README states the measured facts.

    python tools/_p1576_refresh_a1_papera_packages.py --apply
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import re
import shutil
import sys
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from tools.paper_audit import checks as C  # noqa: E402
from tools.paper_audit import profiles as P  # noqa: E402

ARCHIVE = "SUBMISSION/_archive"

PACKAGES = [
    {
        "name": "A1_PAA",
        "profile": "a1_paa",
        "pkg": "SUBMISSION/A1_PatternAnalysisApplications",
        "src_root": "paper_a1",
        "copy": [["paper_a1/main.pdf", "Manuscript.pdf"],
                 ["paper_a1/title_page.pdf", "Title Page.pdf"]],
        "status_old": ("| Submission status | **Submitted 2026-10-18** to the Springer Nature portal "
                       "(Submission ID `0a4629f0-0a6d-45d8-b5b1-3681cc4adc8b`); Submission received, "
                       "technical check in progress; PAA manuscript number pending by email |"),
        "status_new": ("| Submission status | **Submitted 2026-10-18** to the Springer Nature portal "
                       "(Submission ID `0a4629f0-0a6d-45d8-b5b1-3681cc4adc8b`); technical check passed and an "
                       "editor was assigned; **With editor since 2026-10-19**. Package refreshed 2026-10-24 so "
                       "that the shipped PDF matches the current live manuscript. |"),
        "pages_re": r"(\d+)\s*pages",
        "words_re": r"(\d+)\s*words",
    },
    {
        "name": "PaperA_NEUCOM",
        "profile": "paperA_nc",
        "pkg": "SUBMISSION/PaperA_Neurocomputing",
        "src_root": "paper合",
        "copy": [["paper合/main_nc.pdf", "Manuscript.pdf"],
                 ["paper合/cover_letter_nc.pdf", "Cover Letter.pdf"],
                 ["paper合/highlights_nc.pdf", "Highlights.pdf"]],
        "status_old": "> 单作者 ｜ 模板：Elsevier elsarticle ｜ 本包最后同步：2026-10-18（投前终检）",
        "status_new": ("> 单作者 ｜ 模板：Elsevier elsarticle ｜ 本包最后同步：2026-10-24（刷新 Manuscript/Cover Letter/"
                       "Highlights 与 latex source；投出件仍在 `SUBMISSION/_frozen_submitted/PaperA_NEUCOM`）"),
        "pages_re": r"\*\*(\d+)\s*页\*\*",
        "words_re": r"\*\*(\d+)\s*词\*\*",
    },
]


def sha(path: str) -> str:
    return hashlib.sha256(io.open(path, "rb").read()).hexdigest()


def rebuild_zip_and_tree(pkg: str, src_root: str, old_zip: str) -> tuple[int, int]:
    with zipfile.ZipFile(old_zip) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
    missing = [n for n in names if not os.path.isfile(os.path.join(REPO, src_root, n))]
    assert not missing, "source files missing for %s: %s" % (pkg, missing)
    tmp = old_zip + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
        for n in names:
            zf.write(os.path.join(REPO, src_root, n), n)
    os.replace(tmp, old_zip)
    tree = os.path.join(REPO, pkg, "latex_source")
    shutil.rmtree(tree, ignore_errors=True)
    with zipfile.ZipFile(old_zip) as zf:
        zf.extractall(tree)
    n_tree = sum(1 for root, _, fs in os.walk(tree) for _ in fs)
    assert n_tree == len(names), "source tree %d != zip entries %d" % (n_tree, len(names))
    return len(names), n_tree


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for spec in PACKAGES:
        pkg = os.path.join(REPO, spec["pkg"])
        ctx = C.build_context(P.PROFILES[spec["profile"]], {})
        pages = C.parse_pages(C.pdfinfo(ctx["pdf"]))
        words = ctx["abstract_words"]
        print("== %s: live pages=%d abstract_words=%d" % (spec["name"], pages, words))
        if not a.apply:
            continue
        # 1. archive the previous working package
        dst = os.path.join(REPO, ARCHIVE, spec["name"] + "_package_2026-10-18")
        if not os.path.isdir(dst):
            shutil.copytree(pkg, dst)
            n_src = sum(1 for r, _, fs in os.walk(pkg) for _ in fs)
            n_dst = sum(1 for r, _, fs in os.walk(dst) for _ in fs)
            assert n_src == n_dst, "archive incomplete"
            print("   archived previous package ->", os.path.relpath(dst, REPO), "(%d files)" % n_dst)
        # 2. refresh the mapped live copies
        for src, name in spec["copy"]:
            shutil.copy2(os.path.join(REPO, src), os.path.join(pkg, name))
            assert sha(os.path.join(REPO, src)) == sha(os.path.join(pkg, name))
        # 3. rebuild the source archive from the same inclusion list, current contents
        n_zip, n_tree = rebuild_zip_and_tree(spec["pkg"], spec["src_root"],
                                             os.path.join(pkg, "latex_source.zip"))
        print("   source archive rebuilt: %d entries, tree %d files" % (n_zip, n_tree))
        # 4. README measured facts
        rp = os.path.join(pkg, "README.md")
        txt = io.open(rp, encoding="utf-8").read()
        if spec["pages_re"]:
            m = re.search(spec["pages_re"], txt)
            assert m, "no page claim in README"
            txt = txt[:m.start(1)] + str(pages) + txt[m.end(1):]
        if spec["words_re"]:
            m = re.search(spec["words_re"], txt)
            assert m, "no word claim in README"
            txt = txt[:m.start(1)] + str(words) + txt[m.end(1):]
        if spec["status_old"] in txt:
            txt = txt.replace(spec["status_old"], spec["status_new"], 1)
        else:
            print("   note: status line not found; README left as is")
        io.open(rp, "w", encoding="utf-8", newline="").write(txt)
        print("   README facts set: %d pages, %d words" % (pages, words))
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())