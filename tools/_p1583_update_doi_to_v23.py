# -*- coding: utf-8 -*-
r"""Update the working-copy Data statements from the v1.0 DOI to the v2.3 version DOI.

Four manuscripts (Paper A, A1, A23, Commentary) still cite the 13 October 2026 snapshot
(DOI 10.5281/zenodo.23341223).  The repository now has the v2.3 release
(DOI 10.5281/zenodo.23609295, 24 October 2026); the local revision drafts should cite it.
The submitted/frozen packages are not touched.

    python tools/_p1583_update_doi_to_v23.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

V1 = "10.5281/zenodo.23341223"
V3 = "10.5281/zenodo.23609295"

PAIRS = [
    ("paper合/main_nc.tex",
     "under DOI \\texttt{%s} (\\url{https://doi.org/%s}). The\ndecoder-model records reported in Appendix "
     "Sections E and G were produced after that snapshot; their per-run records are openly available in the same "
     "repository, and the adapters are not redistributed" % (V1, V1),
     "under version DOI \\texttt{%s} (\\url{https://doi.org/%s}) (v2.3, 24 October 2026), which includes the "
     "decoder-model records of Appendix Sections E and G. The adapters are not redistributed" % (V3, V3)),
    ("paper合/main_springer.tex",
     "snapshot (DOI \\texttt{%s}). The decoder-model records reported in Appendix\nSections E and G were produced "
     "after that snapshot; their per-run records are openly available in the same repository, and the adapters are "
     "not redistributed" % V1,
     "snapshot (version DOI \\texttt{%s}; v2.3, 24 October 2026), which includes the decoder-model records of "
     "Appendix Sections E and G. The adapters are not redistributed" % V3),
    ("paper_a1/main.tex",
     "archived at Zenodo with DOI\n\\url{https://doi.org/%s}. That snapshot (13 October 2026) covers the per-run "
     "records and scripts that existed\nat that date; the analyses added in the present revision (prompt-template "
     "control, further-benchmark and retrieval\nreplications, monitoring evaluation) are in the public repository, "
     "and a versioned snapshot that includes them will be\narchived on acceptance." % V1,
     "archived at Zenodo with version DOI\n\\url{https://doi.org/%s} (v2.3, 24 October 2026). That snapshot covers "
     "the per-run records, scripts\nand analyses of the present revision (prompt-template control, further-benchmark "
     "and retrieval replications, monitoring\nevaluation); further updates will be archived under a new version DOI "
     "on acceptance." % V3),
    ("paper_a1/title_page.tex",
     "versioned snapshot archived at Zenodo with DOI \\url{https://doi.org/%s} (13 October 2026; the analyses added "
     "in this revision are in the public repository and will be included in the next snapshot)." % V1,
     "versioned snapshot archived at Zenodo with version DOI \\url{https://doi.org/%s} (v2.3, 24 October 2026; it "
     "includes the analyses added in this revision)." % V3),
    ("paper_review_prl/MANUSCRIPT.md",
     "available under DOI %s." % V1,
     "available under version DOI %s." % V3),
    ("paper_a2/main_ieee.tex",
     "archived in the project repository (currently private; to be made public upon publication) "
     "\\url{https://github.com/MoYUYao666/gap-susceptibility}.",
     "archived in the public project repository \\url{https://github.com/MoYUYao666/gap-susceptibility} and in a "
     "versioned Zenodo snapshot (version DOI \\texttt{%s})." % V3),
]

# plain DOI swaps in the revision cover letters
SWAPS = ["paper合/cover_letter_nc.tex", "paper合/cover_letter_nc_revision.tex",
         "paper_a1/cover_letter.tex", "paper_a1/cover_letter_paa_revision.tex"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for path, old, new in PAIRS:
        t = io.open(path, encoding="utf-8").read()
        assert old in t, "pattern not found in %s" % path
        assert new not in t
        print("%-34s %s" % (os.path.basename(path), "ok" if a.apply else "would update"))
        if a.apply:
            io.open(path, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
    for path in SWAPS:
        t = io.open(path, encoding="utf-8").read()
        n = t.count(V1)
        print("%-34s DOI occurrences: %d" % (os.path.basename(path), n))
        if a.apply and n:
            io.open(path, "w", encoding="utf-8", newline="").write(t.replace(V1, V3))
    if a.apply:
        left = []
        for path, _, _ in PAIRS:
            if V1 in io.open(path, encoding="utf-8").read():
                left.append(path)
        print("remaining v1.0 DOI references:", left or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())