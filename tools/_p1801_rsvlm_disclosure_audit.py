# -*- coding: utf-8 -*-
r"""Disclosure audit of eight representative remote-sensing vision-language papers.

What this produces: a presence/absence table for four reporting items - repeated runs, dispersion, compute disclosure and
cross-region evaluation - over eight papers whose full texts are in the archive. The point of the table is to make the
field's reporting gap checkable rather than rhetorical.

Method (stated in the manuscript as well): a phrase search over the archived full text proposes candidates for each item;
every candidate was then read by hand, and the verdict recorded here is the hand verdict, not the search hit. A "no" means
no occurrence of the reporting practice was found in the full text, not that the authors did anything wrong.

Outputs
  paper_rsvlm_survey/literature/disclosure_audit_2026-10-28.json

Usage
  D:\Anaconda\envs\pytorch\python.exe tools\_p1801_rsvlm_disclosure_audit.py
"""
import io
import json
import os
import re

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIT = os.path.join("paper_rsvlm_survey", "literature")
OUT = os.path.join(LIT, "fulltext")
STAMP = "2026-10-28"

# paper key -> (doi, short name)
PAPERS = {
    "RemoteCLIP": "10.1109/tgrs.2024.3390838",
    "RS5M / GeoRSCLIP": "10.1109/tgrs.2024.3449154",
    "RSGPT / RSICap": "10.1016/j.isprsjprs.2025.03.028",
    "EarthGPT": "10.1109/tgrs.2024.3409624",
    "RingMoGPT": "10.1109/tgrs.2024.3510833",
    "NWPU-Captions": "10.1109/tgrs.2022.3201474",
    "C2Seg (cross-city)": "10.1016/j.rse.2023.113856",
    "DDFAV": "10.3390/rs17040719",
}

PATTERNS = {
    "repeated runs": r"(\bseeds?\b|independent runs?|averaged over \d+)",
    "dispersion": r"(±|standard deviation over|std over|error bars?|confidence interval)",
    "compute disclosure": r"(\b(?:A100|V100|H100|RTX \d{4}|TPU)\b|GPU hours|trained for \d+ (?:hours|days))",
    "cross-region evaluation": r"(cross-city|held-out cit|unseen cit|cross-region|cross-dataset|cross-domain)",
}

# hand verdicts after reading every candidate: True = the reporting practice is present in the full text.
VERDICTS = {
    "RemoteCLIP":           {"repeated runs": False, "dispersion": False, "compute disclosure": False, "cross-region evaluation": False},
    "RS5M / GeoRSCLIP":     {"repeated runs": False, "dispersion": False, "compute disclosure": True,  "cross-region evaluation": False},
    "RSGPT / RSICap":       {"repeated runs": False, "dispersion": False, "compute disclosure": True,  "cross-region evaluation": False},
    "EarthGPT":             {"repeated runs": False, "dispersion": False, "compute disclosure": False, "cross-region evaluation": False},
    "RingMoGPT":            {"repeated runs": False, "dispersion": False, "compute disclosure": True,  "cross-region evaluation": False},
    "NWPU-Captions":        {"repeated runs": False, "dispersion": False, "compute disclosure": False, "cross-region evaluation": False},
    "C2Seg (cross-city)":   {"repeated runs": False, "dispersion": False, "compute disclosure": False, "cross-region evaluation": True},
    "DDFAV":                {"repeated runs": False, "dispersion": False, "compute disclosure": False, "cross-region evaluation": False},
}

AUDIT_NOTE = ("phrase search proposes candidates; every candidate was read by hand and the verdict is the hand verdict; "
              "'False' means no occurrence of the practice was found in the archived full text")


def main() -> int:
    report = []
    for name, doi in PAPERS.items():
        slug = re.sub(r"[^0-9a-zA-Z]+", "_", doi).lower()
        path = os.path.join(OUT, slug + ".txt")
        text = re.sub(r"\s+", " ", io.open(path, encoding="utf-8", errors="replace").read()) if os.path.exists(path) else ""
        row = {"paper": name, "doi": doi, "full_text_present": bool(text), "items": {}}
        for item, pat in PATTERNS.items():
            m = re.search(pat, text, re.I) if text else None
            row["items"][item] = {
                "pattern_hit": bool(m),
                "evidence": (text[max(0, m.start() - 70):m.end() + 90].strip() if m else ""),
                "verdict": VERDICTS[name][item],
            }
        report.append(row)
        print("%-20s %s" % (name, {k: int(v["verdict"]) for k, v in row["items"].items()}))

    counts = {item: sum(1 for r in report if r["items"][item]["verdict"]) for item in PATTERNS}
    out = {"generated": STAMP, "method": AUDIT_NOTE, "papers": report,
           "counts": counts, "n_papers": len(report)}
    io.open(os.path.join(LIT, "disclosure_audit_%s.json" % STAMP), "w", encoding="utf-8", newline="").write(
        json.dumps(out, indent=1, ensure_ascii=False))
    print("\ncounts out of %d papers:" % len(report), counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
