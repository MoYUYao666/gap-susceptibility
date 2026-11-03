# -*- coding: utf-8 -*-
r"""Build SUBMISSION/A2_JOE_next_revision from the current paper_a2 working draft.

    python tools/_p1631_a23_next_revision.py                # dry run
    python tools/_p1631_a23_next_revision.py --apply        # build + hash manifest
    python tools/_p1631_a23_next_revision.py --apply --verify-tex   # also compile the source zip standalone

Convention: the same one tools/_p1627_rebuild_next_revision.py uses for the P3 next-revision package.
tools/_p1336_build_venue_package.py assembles the package (upload names without underscores); this driver
adds the package-local extras that the generic builder does not know about:

  * DeclarationOfInterest.docx  - the IEEE declaration, copied from paper_a2/ (no underscore in the name);
  * Supplementary.pdf           - the reviewers' bundle, copied byte-identically from the submitted package;
  * LaTeXSource.zip             - the builder's zip with its main tex file renamed to root.tex, which is the
                                  only name the JOE portal accepts ("root.tex or A23_latex_source.tex");
  * README.md freeze record     - states that this is a staged next-revision package and what it carries;
  * SHA256SUMS.txt              - one line per file in the package.

Inputs are READ-ONLY. SUBMISSION/A23_JOE/** and SUBMISSION/_frozen_submitted/** are never written to: the
supplementary copy is checked against the SHA-256 that paper_a2/verify_a23_fix.py pins for the frozen
archive. The driver refuses to run if the superseded pre-narrowing transfer claim is still present in the
paper_a2 sources, and refuses to finish if it appears in a rebuilt artefact (so a stale package cannot be
frozen again).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = "SUBMISSION/A2_JOE_next_revision"
SUBMITTED = "SUBMISSION/A23_JOE"
BUILDER = "tools/_p1336_build_venue_package.py"

VENUE = "IEEE JOE (A23)"
MANUSCRIPT = "paper_a2/main_ieee.pdf"
PAGES = 74  # 2026-10-28: table captions moved above the body added one page
HIGHLIGHTS = "paper_a2/highlights.pdf"
DECLARATION = "paper_a2/declaration_of_interest.docx"
SUPPLEMENTARY = "SUBMISSION/A23_JOE/supplementary/SUPPLEMENTARY_FOR_REVIEWERS.pdf"
# Pinned by paper_a2/verify_a23_fix.py (frozen archive manifest): the copy must be byte-identical.
SUPPLEMENTARY_SHA256 = "5a9c624e106ec7d06eed8163cb4a4a48e1dbdc545c47d20d10c2c63f3d840f77"

SOURCES = ["paper_a2/main_ieee.tex", "paper_a2/ext_partII_domains.tex"]
# Pre-narrowing states of the multi-encoder transfer claim: the 5-unit/25-pair negative claim and the
# intermediate 18-unit/324-pair state. None of these may survive into a rebuilt package.
SUPERSEDED = [
    "all $25$ ordered pairs",
    "$5$ units",
    "leaves the verdict unchanged",
    "all $324$ ordered pairs",
    "$18$ units",
    "$3536$ scored",
    "$19$ keep their",
    "$124$ reach",
    "none keeps its",
]
# The zip holds only what the manuscript compiles from: root.tex + the five ext_part*.tex + figures/.
ZIP_EXCLUDE = ",".join([
    "abstract.tex", "cover_letter.tex", "highlights.tex", "main.tex", "main_zh.tex",
    "zh_ext_partI_theory.tex", "zh_ext_partII_domains.tex", "zh_ext_partIII_dynamics.tex",
    "zh_ext_partIV_degradation.tex", "zh_ext_partV_mechanisms.tex",
])

FREEZE = """
## Staged next-revision package ({when})

This is a **staged next-revision package** for IEEE JOE `26-0663`, built from the current `paper_a2/` working
draft. It is not a submitted package, and no submitted artefact was touched: `SUBMISSION/A23_JOE/` and
`SUBMISSION/_frozen_submitted/` are read-only inputs, and `paper_a2/verify_a23_fix.py` still reports all
`37` frozen SHA-256 hashes unchanged.

| item | state |
|---|---|
| `Manuscript.pdf` | rebuilt from `paper_a2/main_ieee.pdf`: {pages} pages (the submitted manuscript is 64 pages) |
| `Supplementary.pdf` | byte-identical copy of the frozen reviewers' bundle, sha256 `{supp_sha}` (not revised) |
| `Highlights.pdf` | byte-identical to `SUBMISSION/A23_JOE/current/highlights.pdf` |
| `DeclarationOfInterest.docx` | byte-identical to `SUBMISSION/A23_JOE/current/declaration_of_interest.docx` |
| `TitlePage.pdf` | not supplied: JOE review is single-blind and the author block is in the manuscript |
| `CoverLetter.pdf` | not supplied: the submission-era cover letter is stale, the revision letter is still to be written |
| `Abstract.pdf` | not supplied: not part of the P3 next-revision pattern (`paper_a2/abstract.pdf` is current, 1 page) |
| `LaTeXSource.zip` | `root.tex` + the five `ext_part*.tex` + `figures/` (7 files) |

`LaTeXSource.zip` carries `root.tex` as its main file because the JOE portal rejects any other name. Standalone
check of the zip: {tex_check}

Built by `tools/_p1631_a23_next_revision.py`, which calls `tools/_p1336_build_venue_package.py` - the A23 analogue
of `tools/_p1627_rebuild_next_revision.py`. What a revision letter has to disclose is listed in
`docs/a23_next_revision_package_notes.md`. `SHA256SUMS.txt` covers every file in this package.
"""


def sha256(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def assert_sources_clean() -> None:
    for rel in SOURCES:
        text = io.open(os.path.join(REPO, rel), encoding="utf-8").read()
        for token in SUPERSEDED:
            if token in text:
                raise SystemExit("superseded string %r still present in %s" % (token, rel))
    print("sources clean of superseded transfer-claim strings: %s" % ", ".join(repr(t) for t in SUPERSEDED))


def build_package(out: str) -> None:
    cmd = [sys.executable, BUILDER, "--venue", VENUE, "--out", PKG,
           "--manuscript", MANUSCRIPT, "--highlights", HIGHLIGHTS,
           "--source", "paper_a2", "--figures", "paper_a2/figures",
           "--zip-exclude", ZIP_EXCLUDE, "--apply"]
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr[-1500:])
        raise SystemExit("builder failed with exit %d" % r.returncode)


def rename_zip_main_to_root(zpath: str) -> list[str]:
    """Rewrite LaTeXSource.zip so the main tex file is root.tex (JOE portal requirement)."""
    with zipfile.ZipFile(zpath) as z:
        entries = [(i, z.read(i.filename)) for i in z.infolist()]
    if not any(i.filename == "main_ieee.tex" for i, _ in entries):
        raise SystemExit("builder zip has no main_ieee.tex to rename")
    tmp = zpath + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for info, data in entries:
            if info.filename == "main_ieee.tex":
                # keep the original timestamp so a rebuild of an unchanged tree is byte-identical
                renamed = zipfile.ZipInfo("root.tex", date_time=info.date_time)
                renamed.compress_type = info.compress_type
                renamed.external_attr = info.external_attr
                renamed.internal_attr = info.internal_attr
                renamed.create_system = info.create_system
                z.writestr(renamed, data)
            else:
                z.writestr(info, data)
    os.replace(tmp, zpath)
    with zipfile.ZipFile(zpath) as z:
        names = sorted(z.namelist())
    print("latex source zip: %d entries, main file root.tex" % len(names))
    return names


def verify_latex_zip(zpath: str) -> dict:
    """Extract the zip into a temp dir and compile it standalone with pdflatex twice."""
    tmp = tempfile.mkdtemp(prefix="a23_next_revision_zip_")
    try:
        with zipfile.ZipFile(zpath) as z:
            z.extractall(tmp)
        for _ in range(2):
            r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "root.tex"], cwd=tmp,
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            if r.returncode != 0:
                return {"ok": False, "detail": (r.stdout or "")[-1200:]}
        log = io.open(os.path.join(tmp, "root.log"), encoding="utf-8", errors="replace").read()
        m = re.search(r"Output written on root\.pdf \((\d+) pages", log)
        pages = int(m.group(1)) if m else None
        errors = len(re.findall(r"(?m)^! ", log))
        undefined = len(re.findall(r"Reference .* undefined", log)) + len(re.findall(r"Citation .* undefined", log))
        overfull = len(re.findall(r"Overfull \\hbox", log))
        return {"ok": pages == PAGES and errors == 0 and undefined == 0, "pages": pages,
                "errors": errors, "undefined": undefined, "overfull": overfull}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def patch_readme_table(out: str) -> None:
    """The builder's summary table is generated from its own item list; fill in what this driver added."""
    from pypdf import PdfReader
    supp_pages = len(PdfReader(os.path.join(out, "Supplementary.pdf")).pages)
    readme = os.path.join(out, "README.md")
    text = io.open(readme, encoding="utf-8").read()
    row_supp = "| Supplementary | `Supplementary.pdf` | %d pages (frozen reviewers' bundle, carried unchanged) |" % supp_pages
    row_decl = "| Declaration of interest | `DeclarationOfInterest.docx` | IEEE declaration, carried unchanged |"
    for old, new in (("| Supplementary | `-` | not supplied |", row_supp),
                     ("| Authorship | `-` | not supplied |", row_decl)):
        if old not in text:
            raise SystemExit("README row not found: %r" % old)
        text = text.replace(old, new)
    io.open(readme, "w", encoding="utf-8", newline="").write(text)
    print("README table: Supplementary %d pages, declaration of interest listed" % supp_pages)


def superseded_hits(root: str, zpath: str) -> list[str]:
    bad = []
    for dirpath, _, names in os.walk(root):
        for n in names:
            fp = os.path.join(dirpath, n)
            if n.startswith("SHA256SUMS") or n.startswith("README"):
                continue
            if n.endswith((".tex", ".md")):
                data = io.open(fp, encoding="utf-8", errors="replace").read()
                for token in SUPERSEDED:
                    if token in data:
                        bad.append("%s: %s" % (n, token))
    with zipfile.ZipFile(zpath) as z:
        for name in z.namelist():
            if not name.endswith(".tex"):
                continue
            data = z.read(name).decode("utf-8", "replace")
            for token in SUPERSEDED:
                if token in data:
                    bad.append("%s (zip): %s" % (name, token))
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--verify-tex", action="store_true", help="compile the source zip standalone with pdflatex")
    a = ap.parse_args()

    assert_sources_clean()
    if not os.path.isfile(os.path.join(REPO, MANUSCRIPT)):
        raise SystemExit("missing manuscript %s" % MANUSCRIPT)
    print("  manuscript %s: %d pages expected, sha256 %s" %
          (MANUSCRIPT, PAGES, sha256(os.path.join(REPO, MANUSCRIPT))[:16]))
    supp_sha = sha256(os.path.join(REPO, SUPPLEMENTARY))
    if supp_sha != SUPPLEMENTARY_SHA256:
        raise SystemExit("frozen supplementary changed: %s != %s" % (supp_sha, SUPPLEMENTARY_SHA256))
    for rel in (HIGHLIGHTS, DECLARATION):
        if not os.path.isfile(os.path.join(REPO, rel)):
            raise SystemExit("missing package input %s" % rel)

    if not a.apply:
        print("would rebuild %s (existing=%s)" % (PKG, os.path.isdir(os.path.join(REPO, PKG))))
        return 0

    out = os.path.join(REPO, PKG)
    if os.path.isdir(out):
        shutil.rmtree(out)
        print("removed previous %s" % PKG)
    build_package(out)

    # package-local extras the generic builder does not handle
    shutil.copyfile(os.path.join(REPO, SUPPLEMENTARY), os.path.join(out, "Supplementary.pdf"))
    shutil.copyfile(os.path.join(REPO, DECLARATION), os.path.join(out, "DeclarationOfInterest.docx"))
    zpath = os.path.join(out, "LaTeXSource.zip")
    zip_names = rename_zip_main_to_root(zpath)

    # frozen-archive guard: the copy and its source must agree with the pinned hash
    if sha256(os.path.join(out, "Supplementary.pdf")) != SUPPLEMENTARY_SHA256:
        raise SystemExit("copied Supplementary.pdf does not match the frozen hash")

    # upload-file-name rule: no underscore in any file name in the package
    offenders = [f for f in sorted(os.listdir(out)) if "_" in f]
    if offenders:
        raise SystemExit("underscore in package file name(s): %s" % offenders)

    tex_check = "not run (pass --verify-tex)"
    if a.verify_tex:
        res = verify_latex_zip(zpath)
        if not res.get("ok"):
            print("standalone zip compile FAILED: %s" % res)
            return 1
        tex_check = ("2x pdflatex -> %d pages, 0 errors, 0 undefined refs/cites, %d overfull hboxes"
                     % (res["pages"], res["overfull"]))
        print("standalone zip check:", tex_check)

    readme = os.path.join(out, "README.md")
    patch_readme_table(out)
    text = io.open(readme, encoding="utf-8").read()
    note = FREEZE.format(when="2026-10-25", pages=PAGES, supp_sha=SUPPLEMENTARY_SHA256, tex_check=tex_check)
    io.open(readme, "w", encoding="utf-8", newline="").write(text.rstrip() + "\n" + note)

    lines = []
    for f in sorted(os.listdir(out)):
        fp = os.path.join(out, f)
        if os.path.isfile(fp) and f != "SHA256SUMS.txt":
            lines.append("%s  %s" % (sha256(fp), f))
    io.open(os.path.join(out, "SHA256SUMS.txt"), "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")

    page_count = None
    try:
        from pypdf import PdfReader
        page_count = len(PdfReader(os.path.join(out, "Manuscript.pdf")).pages)
    except Exception as exc:  # pragma: no cover - pypdf is present in this repo
        print("  (page count not measured: %s)" % exc)
    print("package rebuilt: %d files hashed; Manuscript.pdf pages=%s" % (len(lines), page_count))
    if page_count is not None and page_count != PAGES:
        print("PAGE COUNT MISMATCH: expected %d, measured %s" % (PAGES, page_count))
        return 1

    bad = superseded_hits(out, zpath)
    if bad:
        print("SUPERSEDED STRINGS FOUND AFTER REBUILD:")
        for item in bad:
            print("   ", item)
        return 1
    print("no superseded transfer-claim string in the rebuilt package")
    print("zip entries:", ", ".join(zip_names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())