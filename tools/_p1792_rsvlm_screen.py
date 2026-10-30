# -*- coding: utf-8 -*-
r"""Screen the verified corpus into a core reference set for the survey, section by section.

Input:  paper_rsvlm_survey/literature/verified_<date>.json  (758 verified records)
Output: paper_rsvlm_survey/screening/core_<date>.json        the selected core set with reasons
        paper_rsvlm_survey/screening/screening_<date>.md      human-readable tables per section

Selection is deterministic and reproducible: each record is scored against section-specific keyword sets drawn from the
outline, tie-broken by citation count and then by recency. Quotas keep every section supplied with enough references to
make its claims, and every inclusion records why it was picked so the choice can be audited later.

Usage
  D:\Anaconda\envs\pytorch\python.exe tools\_p1792_rsvlm_screen.py [--per-section 30]
"""
import argparse
import io
import json
import os
import time

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIT = os.path.join("paper_rsvlm_survey", "literature")
OUT = os.path.join("paper_rsvlm_survey", "screening")

SECTIONS = {
    "S2 foundations": {
        "quota": 30,
        "keywords": ["clip", "siglip", "openclip", "contrastive", "vision-language pretraining",
                     "foundation model", "multimodal large language", "instruction tuning"],
    },
    "S3 datasets": {
        "quota": 30,
        "keywords": ["dataset", "benchmark", "captioning", "retrieval", "visual question", "grounding",
                     "segmentation", "change detection"],
    },
    "S4 pretraining": {
        "quota": 30,
        "keywords": ["pretraining", "synthetic caption", "sar", "multispectral", "temporal", "self-supervised",
                     "masked image", "alignment"],
    },
    "S5 adaptation": {
        "quota": 30,
        "keywords": ["parameter-efficient", "low-rank", "lora", "adapter", "prompt learning", "fine-tuning",
                     "zero-shot", "instruction tuning", "distillation"],
    },
    "S6 evaluation": {
        "quota": 30,
        "keywords": ["evaluation", "benchmark", "zero-shot", "transfer", "robustness", "leakage", "reproduc",
                     "metrics", "retrieval"],
    },
}


def score(rec, kws):
    hay = (rec.get("title", "") + " " + rec.get("venue", "") + " " + " ".join(rec.get("found_by", []))).lower()
    hits = [k for k in kws if k in hay]
    return len(hits), hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-section", type=int, default=0, help="override every section quota")
    a = ap.parse_args()
    stamp = time.strftime("%Y-%m-%d")
    os.makedirs(OUT, exist_ok=True)
    v = json.load(io.open(os.path.join(LIT, "verified_%s.json" % stamp), encoding="utf-8"))
    print("verified records:", len(v))

    core, chosen = {}, {}
    for sec, cfg in SECTIONS.items():
        quota = a.per_section or cfg["quota"]
        ranked = []
        for key, rec in v.items():
            if key in chosen:
                continue
            n, hits = score(rec, cfg["keywords"])
            if n == 0:
                continue
            ranked.append((n, rec.get("cited_by") or 0, rec.get("year") or 0, key, rec, hits))
        ranked.sort(key=lambda t: (-t[0], -t[1], -t[2]))
        picked = []
        for n, cites, year, key, rec, hits in ranked[:quota]:
            chosen[key] = sec
            picked.append({"doi": rec["doi"], "title": rec["title"], "year": year, "venue": rec.get("venue"),
                           "cited_by": cites, "matched_terms": hits, "section": sec, "key": key})
        core[sec] = picked
        print("  %-18s candidates=%3d picked=%2d" % (sec, len(ranked), len(picked)))

    io.open(os.path.join(OUT, "core_%s.json" % stamp), "w", encoding="utf-8", newline="").write(
        json.dumps(core, indent=1, ensure_ascii=False))

    lines = ["# Screening: core reference set (2026-10-27)", "",
             "Verified corpus: **%d** records. Core selection: **%d** records, at most %d per section, chosen by "
             "keyword match count against the outline, then citations, then recency. Every inclusion lists the terms "
             "that selected it, so the choice is auditable." % (len(v), sum(len(x) for x in core.values()),
                                                                a.per_section or 30),
             "",
             "Rule for drafting: a claim may only cite records from this core set, and any new reference must come back "
             "through the harvest + verification pipeline (`tools/_p1790`, `tools/_p1791`)."]
    for sec, recs in core.items():
        lines += ["", "## %s (%d)" % (sec, len(recs)), "",
                  "| year | cites | title | venue | doi | matched |", "|---|---|---|---|---|---|"]
        for r in recs:
            lines.append("| %s | %s | %s | %s | `%s` | %s |" % (
                r["year"], r["cited_by"], r["title"][:120].replace("|", "\\|"),
                (r["venue"] or "")[:44].replace("|", "\\|"), r["doi"], ", ".join(r["matched_terms"][:3])))
    io.open(os.path.join(OUT, "screening_%s.md" % stamp), "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
    print("\ncore set:", sum(len(x) for x in core.values()), "-> paper_rsvlm_survey/screening/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
