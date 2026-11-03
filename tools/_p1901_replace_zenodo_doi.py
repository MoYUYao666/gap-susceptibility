# -*- coding: utf-8 -*-
"""Replace the old Zenodo snapshot DOIs with one clean version DOI across the active manuscript trees.

The old version records (v1.0-v2.8, including the duplicate v1.0 record) are being deleted by Zenodo; the
clean v3.0 snapshot is the single record the manuscripts should cite. This script rewrites every occurrence
of the old DOIs in the active trees, prints a diff, and can optionally skip rebuilding (the caller rebuilds
the packages afterwards).

Usage
  python tools/_p1901_replace_zenodo_doi.py --new-doi 10.5281/zenodo.XXXXXXXX --check
  python tools/_p1901_replace_zenodo_doi.py --new-doi 10.5281/zenodo.XXXXXXXX
"""
import argparse
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OLD_DOIS = [
    "10.5281/zenodo.23341083",
    "10.5281/zenodo.23341223",
    "10.5281/zenodo.23632347",
    "10.5281/zenodo.23800255",
    "10.5281/zenodo.23835149",
]

# active manuscript trees only; frozen SUBMISSION packages are rebuilt by the package builders afterwards
TARGETS = [
    "paper_a3/draft/08_declarations.tex",
    "paper_a3/draft/cover_letter.tex",
    "paper合/main_springer.tex",
    "paper合/main_nc.tex",
    "paper合/cover_letter_nc.tex",
    "paper合/cover_letter_nc_revision.tex",
    "paper合/reframed/main.tex",
    "paper合/reframed/new/backmatter.tex",
    "paper_a1/main.tex",
    "paper_a1/title_page.tex",
    "paper_a1/cover_letter.tex",
    "paper_a1/cover_letter_paa_revision.tex",
    "paper3/paper_ieee/main.tex",
    "paper3/paper_ieee/sections/conclusion.tex",
    "paper_rsvlm_survey/grrsm/main_ieee.tex",
    "paper_rsvlm_survey/grrsm/main.tex",
    "paper_rsvlm_survey/grrsm/cover_letter.tex",
    "paper_rsvlm_survey/grrsm/whitepaper.tex",
    "paper_rsvlm_survey/grrsm/References.bib",
    "paper_rsvlm_survey/isprsj/main.tex",
    "paper_rsvlm_survey/isprsj/cover_letter.tex",
    "paper_rsvlm_survey/isprsj/References.bib",
    "paper_rsvlm_survey/literature/survey.bib",
    "paper_rsvlm_survey/draft/survey.bib",
    "paper_review_prl/RESPONSE_TEMPLATE.md",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new-doi", required=True,
                    help="new clean version DOI, for example 10.5281/zenodo.12345678")
    ap.add_argument("--check", action="store_true", help="report changes without writing")
    args = ap.parse_args()

    if not re.fullmatch(r"10\.5281/zenodo\.\d{6,9}", args.new_doi):
        print("invalid DOI format:", args.new_doi)
        return 2

    total = 0
    for rel in TARGETS:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        text = io.open(path, encoding="utf-8").read()
        new = text
        here = 0
        for old in OLD_DOIS:
            if old in new:
                count = new.count(old)
                new = new.replace(old, args.new_doi)
                here += count
        if here:
            total += here
            print("%-70s %d replacement(s)" % (rel, here))
            if not args.check:
                io.open(path, "w", encoding="utf-8", newline="").write(new)
    print("total replacements:", total)
    if args.check:
        print("dry run only; rerun without --check to write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
