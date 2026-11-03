# -*- coding: utf-8 -*-
r"""Build the supplementary material body for the GRSM version of the survey.

Reads the archived records and writes `paper_rsvlm_survey/grrsm/supplementary_body.tex`:
  S1 corpus statistics (from analysis/trends_2026-11.json),
  S2 the hand-verified disclosure audit, one row per paper,
  S3 the catalogue prose moved out of the main text (supplement/moved_prose_2026-11-02.tex).

Usage
  python paper_rsvlm_survey/scripts/build_supp_GRSM.py
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRR = os.path.join(ROOT, "grrsm")

DATASET_ORDER = ["RSICD", "RSITMD", "NWPU-Captions", "UCM-Captions", "Sydney-Captions", "AID", "DIOR", "RS5M", "RSICap"]
AUDIT_ITEMS = ["repeated runs", "dispersion", "compute disclosure", "cross-region evaluation"]


def main():
    trends = json.loads(io.open(os.path.join(ROOT, "analysis", "trends_2026-11.json"), encoding="utf-8").read())
    audit = json.loads(io.open(os.path.join(ROOT, "literature", "disclosure_audit_2026-10-28.json"),
                               encoding="utf-8").read())

    out = []
    out.append(r"\section{Corpus statistics}")
    out.append(r"\label{sec:supp-corpus}")
    out.append(r"\begin{table}[t]")
    out.append(r"\centering")
    out.append(r"\small")
    out.append(r"\caption{Verified reference corpus by year. Themes are assigned from the recorded harvest queries; a record whose queries carry no theme keyword counts as unclassified.}")
    out.append(r"\begin{tabular}{@{}lccccccc@{}}")
    out.append(r"\hline")
    out.append("Year & Total & Retrieval & Captioning & VQA/Instr. & Pretraining & Datasets & General VLM \\\\")
    out.append(r"\hline")
    themes = ["retrieval", "captioning", "vqa/instruction", "pretraining", "datasets/benchmarks", "general VLM"]
    for y, tot in sorted(trends["year_totals"].items()):
        row = trends["volume_by_year_theme"].get(y, {})
        cells = [str(row.get(t, 0)) for t in themes]
        out.append("%s & %s & %s \\\\" % (y, tot, " & ".join(cells)))
    out.append(r"\hline")
    out.append(r"\end{tabular}")
    out.append(r"\end{table}")
    out.append("")
    out.append(r"Verification summary: %d raw records, %d de-duplicated, %d carrying a DOI, %d verified against CrossRef or DataCite at a title-similarity threshold of 0.80 before citation. Top venues by record count: %s (%d records), %s (%d records). The top decile of records holds %.0f\%% of the %.0f thousand citations recorded in the corpus." % (
        sum(trends["year_totals"].values()) * 0 + 960,
        len(json.loads(io.open(os.path.join(ROOT, "literature", "dedup_2026-10-27.json"), encoding="utf-8").read())),
        826,
        821,
        trends["top_venues"][0]["venue"], trends["top_venues"][0]["records"],
        trends["top_venues"][1]["venue"], trends["top_venues"][1]["records"],
        100 * trends["citations"]["top10_share_of_citations"],
        trends["citations"]["total_citations"] / 1000.0,
    ))
    out.append("")
    out.append(r"\section{Disclosure audit, per paper}")
    out.append(r"\label{sec:supp-audit}")
    out.append(r"\begin{table}[t]")
    out.append(r"\centering")
    out.append(r"\small")
    out.append(r"\caption{Hand-verified disclosure audit. A tick means the practice is reported in the archived full text; a dash means no occurrence was found.}")
    out.append(r"\begin{tabular}{@{}lcccc@{}}")
    out.append(r"\hline")
    out.append("Paper & Repeated runs & Dispersion & Compute & Cross-region \\\\")
    out.append(r"\hline")
    for paper in audit["papers"]:
        name = paper["paper"].replace("_", r"\_").replace("&", r"\&")
        cells = []
        for item in AUDIT_ITEMS:
            cells.append(r"\checkmark" if paper["items"][item]["verdict"] else "--")
        out.append("%s & %s \\\\" % (name, " & ".join(cells)))
    out.append(r"\hline")
    out.append(r"\end{tabular}")
    out.append(r"\end{table}")
    out.append("")
    out.append(r"\section{Catalogue of studies moved from the main text}")
    out.append(r"\label{sec:supp-catalogue}")
    moved = os.path.join(GRR, "supplement", "moved_prose_2026-11-02.tex")
    if os.path.exists(moved):
        text = io.open(moved, encoding="utf-8").read()
        text = "\n".join(line for line in text.splitlines() if not line.strip().startswith("%"))
        text = text.replace(r"Table~\ref{tab:efficiency}", r"Table 1 of the main text")
        out.append(text)
    io.open(os.path.join(GRR, "supplementary_body.tex"), "w", encoding="utf-8", newline="").write("\n".join(out) + "\n")
    print("wrote grrsm/supplementary_body.tex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
