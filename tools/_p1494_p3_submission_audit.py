# -*- coding: utf-8 -*-
r"""Audit the submitted P3 package against the R1 objections and the rejection reason.

    python tools/_p1494_p3_submission_audit.py [--apply]
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re

from pypdf import PdfReader

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(REPO, "SUBMISSION", "P3_PRL_resubmission")
OUT = os.path.join(REPO, "outputs", "analysis", "p3_submission_audit.json")
FILES = ["Manuscript.pdf", "Supplementary.pdf", "CoverLetter.pdf", "TitlePage.pdf", "Highlights.pdf",
         "AuthorshipConfirmation.pdf", "LaTeXSource.zip", "EM_FIELDS.md", "README.md"]


def pdf_text(path):
    return "".join((p.extract_text() or "") for p in PdfReader(path).pages)


def main() -> int:
    report = {"package": "SUBMISSION/P3_PRL_resubmission", "files": {}, "checks": {}}
    for f in FILES:
        p = os.path.join(PKG, f)
        if not os.path.exists(p):
            report["files"][f] = {"exists": False}
            continue
        h = hashlib.sha256(io.open(p, "rb").read()).hexdigest()
        pages = len(PdfReader(p).pages) if f.endswith(".pdf") else None
        report["files"][f] = {"exists": True, "sha256": h, "bytes": os.path.getsize(p), "pages": pages,
                              "underscore": "_" in f}
    main_pdf = os.path.join(PKG, "Manuscript.pdf")
    supp_pdf = os.path.join(PKG, "Supplementary.pdf")
    m = pdf_text(main_pdf)
    s = pdf_text(supp_pdf)

    def norm(x):
        return " ".join(x.split()).lower()
    emb = io.open(os.path.join(PKG, "EM_FIELDS.md"), encoding="utf-8").read()
    c = {}
    c["title_reframed"] = "identifiability, negative results, and protocol dependence" in norm(m)
    c["doi_v22"] = "10.5281/zenodo.23523263" in m and "10.5281/zenodo.23341223" not in m
    c["abstract_five_seed_p"] = "p = 0.008" in emb and "0/300" not in emb
    c["five_seed_stats"] = "23.0" in m and "65.5" in m
    c["real_image_numbers"] = "83.0" in m and "66.5" in m and "39.5" in m
    c["protocol_shift_section"] = "protocol shift at the crossing" in norm(s)
    c["claim_status_table"] = "assumption audit and claim status" in norm(s) and "not supported" in norm(s)
    c["provenance_section"] = "data and code provenance" in norm(s)
    c["no_code_on_request"] = "upon request" not in m
    c["random_pairing_answer"] = "11.5" in m or "11.5" in s
    c["adalora_numbers"] = "1468" in m or "1468" in s
    c["matched_loss_answer"] = "5968" in m or "2842" in m
    c["transfer_scope"] = "qwen" in norm(m) and "llava" in norm(m)
    c["authorship_date"] = "October 21, 2026" in pdf_text(os.path.join(PKG, "AuthorshipConfirmation.pdf"))
    c["cover_letter_prior_id"] = "PRLETTERS-D-26-02378R1" in pdf_text(os.path.join(PKG, "CoverLetter.pdf"))
    uploaded = [f for f in FILES if f.endswith((".pdf", ".zip"))]
    c["filenames_underscore_free"] = all("_" not in f for f in uploaded)
    c["pages_ok"] = report["files"]["Manuscript.pdf"]["pages"] == 10 and report["files"]["Supplementary.pdf"]["pages"] == 8
    report["checks"] = c
    report["all_critical_pass"] = all([c["title_reframed"], c["doi_v22"], c["abstract_five_seed_p"],
                                       c["real_image_numbers"], c["protocol_shift_section"],
                                       c["claim_status_table"], c["provenance_section"],
                                       c["no_code_on_request"], c["author_id_ok"] if "author_id_ok" in c else True,
                                       c["authorship_date"], c["cover_letter_prior_id"],
                                       c["filenames_underscore_free"], c["pages_ok"]])
    for k, v in c.items():
        print(f"  {k:26s} {v}")
    print("  all critical pass:", report["all_critical_pass"])
    if "--apply" in os.sys.argv:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(report, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0 if report["all_critical_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
