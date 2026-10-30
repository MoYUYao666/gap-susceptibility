# -*- coding: utf-8 -*-
r"""Literature harvest for the remote-sensing vision-language survey, with real identifiers only.

Nothing in this pipeline invents a reference. Every record comes from a live API call and carries the identifier the
source returned; a record without a DOI or arXiv id is kept in the raw dump but cannot enter the bibliography.

Sources
  OpenAlex  (https://api.openalex.org)  primary: DOI, title, authors, year, venue, citation count, retraction flag
  CrossRef  (https://api.crossref.org)  cross-check: the DOI must resolve and the titles must agree

Outputs (all English keys, provenance inside the JSON):
  paper_rsvlm_survey/literature/raw_<date>.json        every record returned by every query
  paper_rsvlm_survey/literature/dedup_<date>.json      deduplicated by DOI, with per-query provenance
  paper_rsvlm_survey/literature/summary_<date>.json    counts, per-theme yield, overlap statistics

Usage
  D:\Anaconda\envs\pytorch\python.exe tools\_p1790_rsvlm_lit_harvest.py [--per-query 50] [--min-year 2019]
"""
import argparse
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTDIR = os.path.join("paper_rsvlm_survey", "literature")
UA = "dsh-survey-harvest/1.0 (mailto:research@example.org)"

QUERIES = [
    "remote sensing image-text retrieval",
    "remote sensing image captioning",
    "remote sensing visual question answering",
    "remote sensing vision-language model",
    "CLIP remote sensing",
    "vision-language pretraining remote sensing",
    "foundation model earth observation",
    "parameter-efficient fine-tuning remote sensing",
    "Low-Rank Adaptation remote sensing",
    "prompt learning remote sensing classification",
    "multimodal large language model remote sensing",
    "remote sensing benchmark multimodal",
    "text-to-image generation remote sensing",
    "zero-shot scene classification remote sensing",
    "cross-modal retrieval satellite imagery",
    "instruction tuning remote sensing",
]

# The survey must also cite the foundations it argues from, and those are not remote-sensing papers. They are harvested
# with the same pipeline so they are verified exactly like everything else.
GENERAL_QUERIES = [
    "learning transferable visual models from natural language supervision",
    "sigmoid loss for language image pre-training",
    "reproducible scaling of contrastive language-image pretraining",
    "BLIP-2 bootstrapping language-image pre-training",
    "visual instruction tuning multimodal large language model",
    "Flamingo visual language model few-shot",
    "modality gap contrastive representation learning",
    "image-text retrieval benchmark recall",
]
QUERIES = QUERIES + GENERAL_QUERIES


def get_json(url, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def openalex(query, per_query, min_year):
    params = {
        "search": query,
        "per-page": str(per_query),
        "filter": "from_publication_date:%d-01-01,type:article|review" % min_year,
        "select": "id,doi,title,publication_year,authorships,primary_location,cited_by_count,is_retracted,"
                  "type,open_access",
        "mailto": "research@example.org",
    }
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    data = get_json(url)
    return data.get("results", [])


def norm(rec, query):
    doi = (rec.get("doi") or "").lower().replace("https://doi.org/", "")
    loc = rec.get("primary_location") or {}
    src = (loc.get("source") or {}) if isinstance(loc, dict) else {}
    authors = []
    for a in rec.get("authorships", [])[:12]:
        name = (a.get("author") or {}).get("display_name")
        if name:
            authors.append(name)
    return {
        "openalex_id": rec.get("id"),
        "doi": doi,
        "title": (rec.get("title") or "").strip(),
        "year": rec.get("publication_year"),
        "venue": (src.get("display_name") or "").strip(),
        "authors": authors,
        "n_authors": len(rec.get("authorships", [])),
        "cited_by": rec.get("cited_by_count"),
        "type": rec.get("type"),
        "retracted": bool(rec.get("is_retracted")),
        "found_by": [query],
    }


def merge(dst, rec):
    key = rec["doi"] or rec["openalex_id"]
    if key in dst:
        hit = dst[key]
        for q in rec["found_by"]:
            if q not in hit["found_by"]:
                hit["found_by"].append(q)
        return False
    dst[key] = rec
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-query", type=int, default=50)
    ap.add_argument("--min-year", type=int, default=2019)
    a = ap.parse_args()
    os.makedirs(OUTDIR, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d")

    raw, dedup, per_theme = {}, {}, {}
    for q in QUERIES:
        try:
            results = openalex(q, a.per_query, a.min_year)
        except Exception as e:
            print("  %-46s FAILED %s" % (q, str(e)[:90]))
            per_theme[q] = {"n": 0, "error": str(e)[:120]}
            continue
        kept = 0
        for rec in results:
            n = norm(rec, q)
            if not n["title"]:
                continue
            raw.setdefault(q, []).append(n)
            if merge(dedup, n):
                kept += 1
        per_theme[q] = {"n": len(results), "new": kept}
        print("  %-46s returned %3d, new %3d" % (q, len(results), kept))
        time.sleep(0.35)

    with_doi = sum(1 for r in dedup.values() if r["doi"])
    summary = {
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "source": "OpenAlex works search (filter from %d, type article|review)" % a.min_year,
        "api": "https://api.openalex.org/works",
        "per_query": a.per_query,
        "n_queries": len(QUERIES),
        "n_raw": sum(len(v) for v in raw.values()),
        "n_dedup": len(dedup),
        "n_with_doi": with_doi,
        "n_without_doi": len(dedup) - with_doi,
        "n_retracted": sum(1 for r in dedup.values() if r["retracted"]),
        "overlap_ge2_queries": sum(1 for r in dedup.values() if len(r["found_by"]) >= 2),
        "per_theme": per_theme,
        "note": "records without a DOI stay in the raw dump but are excluded from the bibliography; every entry that "
                "enters the manuscript is re-verified against CrossRef by tools/_p1791_rsvlm_verify_bib.py",
    }
    io.open(os.path.join(OUTDIR, "raw_%s.json" % stamp), "w", encoding="utf-8", newline="").write(
        json.dumps(raw, indent=1, ensure_ascii=False))
    io.open(os.path.join(OUTDIR, "dedup_%s.json" % stamp), "w", encoding="utf-8", newline="").write(
        json.dumps(dedup, indent=1, ensure_ascii=False))
    io.open(os.path.join(OUTDIR, "summary_%s.json" % stamp), "w", encoding="utf-8", newline="").write(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print("\nraw %d | dedup %d | with DOI %d | retracted %d" %
          (summary["n_raw"], summary["n_dedup"], with_doi, summary["n_retracted"]))
    print("wrote", OUTDIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
