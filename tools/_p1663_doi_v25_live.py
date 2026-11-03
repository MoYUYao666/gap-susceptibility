"""Point the five LIVE manuscripts at the v2.5 version DOI (10.5281/zenodo.23632347).

Scope decided from the artefacts, and recorded in docs/retire_exceptions_and_doi_v25_2026-10-25.md:

  * UPDATED - the manuscript Data-availability / conclusion statements, i.e. the papers' own claims:
      paper合/main_nc.tex:87, paper合/main_springer.tex:87,
      paper_a1/main.tex:1471-1472, paper_a1/title_page.tex:36,
      paper_a2/main_ieee.tex:839, paper_review_prl/main_prl.tex:218,
      paper3/paper_ieee/main.tex:133-134, paper3/paper_ieee/sections/conclusion.tex:49
    (title_page.tex is included because it repeats the same data statement as main.tex; leaving it at
    v2.3 would make one submission package contradict itself.)
  * UPDATED - the five gate needles that pin an old DOI, so no gate keeps checking a superseded value:
      paper3/paper_ieee/audit_check.py, paper3/paper_ieee/audit_pdf.py,
      tools/_p1181_verify_paperA_consistency.py, tools/_p1637_p3_reproduce_all.py (2 strings).
  * NOT updated (reported, not silently skipped):
      - cover letters and response templates (`paper_a1/cover_letter*.tex`, `paper合/cover_letter*.tex`,
        `paper3/paper_ieee/cover_letter_prl*.tex`, `paper_review_prl/RESPONSE_TEMPLATE.md`): they are
        submission correspondence tied to the versions that were actually sent, and one of them says
        "frozen Zenodo version DOI" on purpose;
      - historical fix logs (`*/FIXES_2026-*.md`) and `paper3/paper_ieee/PRL_submission/**`: records of
        what was done/sent at the time;
      - `SUBMISSION/**`: frozen packages keep the DOI they were submitted with.

Version label: where the manuscript already carries one ("v2.3, 24 October 2026") it is updated to
"v2.5, 25 October 2026"; the P3 statement carries no label and none is added (P3 main is at its
10-page limit and the instruction is to change no claims).

Idempotent: files already carrying the new DOI and no old DOI are skipped.

Usage:
    python tools/_p1663_doi_v25_live.py [--apply]
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OLD_DOIS = ("10.5281/zenodo.23609295", "10.5281/zenodo.23523263")
NEW_DOI = "10.5281/zenodo.23632347"
OLD_LABEL = "v2.3, 24 October 2026"
NEW_LABEL = "v2.5, 25 October 2026"

MANUSCRIPTS = [
    "paper合/main_nc.tex",
    "paper合/main_springer.tex",
    "paper_a1/main.tex",
    "paper_a1/title_page.tex",
    "paper_a2/main_ieee.tex",
    "paper_review_prl/main_prl.tex",
    "paper3/paper_ieee/main.tex",
    "paper3/paper_ieee/sections/conclusion.tex",
    # Cover letters for A1 and Paper A: these two submission packages are the REFRESHABLE working
    # packages (`SUBMISSION/A1_PatternAnalysisApplications`, `SUBMISSION/PaperA_Neurocomputing`), which
    # `tools/_p1576_refresh_a1_papera_packages.py` re-syncs from the live files; the frozen submitted
    # artefacts live separately under `SUBMISSION/_frozen_submitted/`. Leaving the letters at v2.3 would
    # make the refreshed package contradict its own manuscript. The P3 letters are NOT updated: their
    # package is frozen and one letter cites the frozen v1.0 DOI on purpose.
    "paper_a1/cover_letter.tex",
    "paper_a1/cover_letter_paa_revision.tex",
    "paper合/cover_letter_nc.tex",
    "paper合/cover_letter_nc_revision.tex",
]

NEEDLES = [
    ("paper3/paper_ieee/audit_check.py", '"10.5281/zenodo.23523263" in tex',
     '"10.5281/zenodo.23632347" in tex'),
    ("paper3/paper_ieee/audit_pdf.py", '("Zenodo DOI", "10.5281/zenodo.23523263")',
     '("Zenodo DOI", "10.5281/zenodo.23632347")'),
    ("tools/_p1181_verify_paperA_consistency.py", '"10.5281/zenodo.23609295"',
     '"10.5281/zenodo.23632347"'),
    ("tools/_p1637_p3_reproduce_all.py", "version DOI 10.5281/zenodo.23523263",
     "version DOI 10.5281/zenodo.23632347"),
    ("tools/_p1637_p3_reproduce_all.py", '         "10.5281/zenodo.23523263",',
     '         "10.5281/zenodo.23632347",'),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    rc = 0

    print("== manuscript statements ==")
    for rel in MANUSCRIPTS:
        p = REPO / rel
        if not p.is_file():
            print("  [FAIL] missing %s" % rel)
            rc = 2
            continue
        text = io.open(p, encoding="utf-8").read()
        n_old = sum(text.count(d) for d in OLD_DOIS)
        has_new = NEW_DOI in text
        if n_old == 0 and has_new:
            print("  [skip] %-52s already on v2.5" % rel)
            continue
        if n_old == 0:
            print("  [FAIL] %-52s no old and no new DOI -- inspect manually" % rel)
            rc = 2
            continue
        new = text
        for d in OLD_DOIS:
            new = new.replace(d, NEW_DOI)
        n_label = new.count(OLD_LABEL)
        new = new.replace(OLD_LABEL, NEW_LABEL)
        print("  [edit] %-52s %d DOI(s), %d version label(s) -> v2.5" % (rel, n_old, n_label))
        if args.apply:
            io.open(p, "w", encoding="utf-8", newline="\n").write(new)
            check = io.open(p, encoding="utf-8").read()
            assert NEW_DOI in check and not any(d in check for d in OLD_DOIS), \
                "DOI replacement incomplete in %s" % rel

    print("\n== gate needles ==")
    for rel, old, new in NEEDLES:
        p = REPO / rel
        if not p.is_file():
            print("  [FAIL] missing %s" % rel)
            rc = 2
            continue
        text = io.open(p, encoding="utf-8").read()
        if new in text and old not in text:
            print("  [skip] %-52s already updated" % rel)
            continue
        n = text.count(old)
        if n < 1:
            print("  [FAIL] %-52s needle not found: %r" % (rel, old[:40]))
            rc = 2
            continue
        print("  [edit] %-52s %d needle(s)" % (rel, n))
        if args.apply:
            io.open(p, "w", encoding="utf-8", newline="\n").write(text.replace(old, new))

    print("\n== verify no old repo DOI remains in the five LIVE trees (manuscripts only) ==")
    if args.apply:
        for rel in MANUSCRIPTS:
            t = io.open(REPO / rel, encoding="utf-8").read()
            for d in OLD_DOIS:
                assert d not in t, "%s still cites %s" % (rel, d)
        print("  ok: all eight manuscript statements cite %s only" % NEW_DOI)
    if not args.apply:
        print("\n(preview; pass --apply to write)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
