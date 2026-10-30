# -*- coding: utf-8 -*-
r"""Fetch the abstracts of the screened core references from OpenAlex and extract quotable numbers.

Why: a survey that cites only titles is shallow, but inventing numbers is worse. OpenAlex stores abstracts as inverted
indexes, so this script reconstructs the real abstract text for every core reference, keeps the source URL of each record,
and then extracts candidate numeric claims (dataset sizes, metric values, parameter counts) together with the sentence they
came from. The candidates are *evidence for later use*, never inserted into the manuscript automatically.

Outputs
  paper_rsvlm_survey/literature/abstracts_<date>.json         doi -> title, year, abstract, openalex id
  paper_rsvlm_survey/literature/number_candidates_<date>.json  sentence-level numeric claims with the DOI they come from

Usage
  D:\Anaconda\envs\pytorch\python.exe tools\_p1794_rsvlm_abstracts.py
"""
import io
import json
import os
import re
import time
import urllib.parse
import urllib.request

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIT = os.path.join("paper_rsvlm_survey", "literature")
UA = "dsh-survey-abstracts/1.0 (mailto:research@example.org)"
BATCH = 40
KEYS = ("abstract_inverted_index", "id", "doi", "title", "publication_year", "cited_by_count")
NUM_KEYS = ("dataset", "images", "image", "captions", "caption", "pairs", "samples", "patches", "classes",
            "accuracy", "recall", "mAP", "parameters", "tokens", "resolution")


def get(url, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def rebuild(inv):
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))


def candidates(abstract, doi, title):
    out = []
    for sent in re.split(r"(?<=[.!?])\s+", abstract):
        if not re.search(r"\d", sent):
            continue
        low = sent.lower()
        hits = [k for k in NUM_KEYS if k.lower() in low]
        if hits:
            out.append({"doi": doi, "title": title[:120], "sentence": sent.strip()[:400],
                        "matched_terms": sorted(set(hits))[:6]})
    return out


def main() -> int:
    stamp = time.strftime("%Y-%m-%d")
    CORE = os.path.join("paper_rsvlm_survey", "screening")
    core = json.load(io.open(os.path.join(CORE, "core_%s.json" % stamp), encoding="utf-8"))
    dois = sorted({r["doi"] for recs in core.values() for r in recs if r.get("doi")})
    seeds_path = os.path.join(LIT, "seeds_verified_%s.json" % stamp)
    if os.path.exists(seeds_path):
        seeds = json.load(io.open(seeds_path, encoding="utf-8"))
        dois += [d for d in seeds if d not in dois]
    print("abstracts requested:", len(dois))

    found, missing = {}, []
    for start in range(0, len(dois), BATCH):
        chunk = dois[start:start + BATCH]
        flt = "doi:" + "|".join(d.lower() for d in chunk)
        url = ("https://api.openalex.org/works?filter=" + urllib.parse.quote(flt, safe=":|") +
               "&per-page=50&select=" + ",".join(KEYS) + "&mailto=research@example.org")
        try:
            data = get(url)
        except Exception as e:
            print("  batch %d failed: %s" % (start, str(e)[:90]))
            time.sleep(2)
            continue
        for w in data.get("results", []):
            doi = (w.get("doi") or "").lower().replace("https://doi.org/", "")
            abstract = rebuild(w.get("abstract_inverted_index"))
            if not abstract:
                continue
            found[doi] = {"title": w.get("title"), "year": w.get("publication_year"),
                          "openalex_id": w.get("id"), "cited_by": w.get("cited_by_count"),
                          "abstract": abstract,
                          "source": "OpenAlex abstract_inverted_index"}
        for d in chunk:
            if d.lower() not in found:
                missing.append(d)
        print("  %d/%d requested, %d with abstract" % (min(start + BATCH, len(dois)), len(dois), len(found)))
        time.sleep(0.4)

    io.open(os.path.join(LIT, "abstracts_%s.json" % stamp), "w", encoding="utf-8", newline="").write(
        json.dumps(found, indent=1, ensure_ascii=False))

    cand = []
    for doi, rec in found.items():
        cand.extend(candidates(rec["abstract"], doi, rec.get("title") or ""))
    io.open(os.path.join(LIT, "number_candidates_%s.json" % stamp), "w", encoding="utf-8", newline="").write(
        json.dumps({"generated": time.strftime("%Y-%m-%d %H:%M"),
                    "source": "abstracts_%s.json (OpenAlex)" % stamp,
                    "note": "candidate numeric claims for manual checking before use in the manuscript",
                    "n_candidates": len(cand), "candidates": cand}, indent=1, ensure_ascii=False))
    print("\nabstracts: %d | without abstract: %d | numeric candidates: %d" %
          (len(found), len(missing), len(cand)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
