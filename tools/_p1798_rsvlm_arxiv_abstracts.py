# -*- coding: utf-8 -*-
r"""Fetch the real abstracts of the foundational arXiv papers behind the curated seeds.

The seeds were admitted by resolving their DOI through DataCite; that gives title and year but often no abstract. arXiv's
API is reachable over https, so this script pulls the abstract for each seed's arXiv id, checks the returned title against
the seed title (so a wrong id cannot slip through), and archives the result for the drafting of Section 2.

Outputs
  paper_rsvlm_survey/literature/arxiv_abstracts_<date>.json     arxiv id -> title, abstract, published, title check
  paper_rsvlm_survey/literature/arxiv_numbers_<date>.json       numeric mentions with the sentence they appear in

Usage
  D:\Anaconda\envs\pytorch\python.exe tools\_p1798_rsvlm_arxiv_abstracts.py
"""
import difflib
import io
import json
import os
import re
import time
import urllib.request
import xml.etree.ElementTree as ET

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIT = os.path.join("paper_rsvlm_survey", "literature")
UA = "dsh-survey-arxiv/1.0"
NS = {"a": "http://www.w3.org/2005/Atom"}


def fetch_with_retry(arxiv_id, attempts=3):
    last = None
    for k in range(attempts):
        try:
            return fetch(arxiv_id)
        except Exception as e:
            last = e
            time.sleep(8 * (k + 1))
    raise last


def fetch(arxiv_id):
    url = "https://export.arxiv.org/api/query?id_list=%s&max_results=1" % arxiv_id
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        xml = r.read().decode("utf-8", "replace")
    root = ET.fromstring(xml)
    entry = root.find("a:entry", NS)
    if entry is None:
        return None
    return {
        "title": re.sub(r"\s+", " ", (entry.findtext("a:title", default="", namespaces=NS) or "")).strip(),
        "abstract": re.sub(r"\s+", " ", (entry.findtext("a:summary", default="", namespaces=NS) or "")).strip(),
        "published": entry.findtext("a:published", default="", namespaces=NS),
    }


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower())).strip()


def main() -> int:
    stamp = time.strftime("%Y-%m-%d")
    seeds = json.load(io.open(os.path.join(LIT, "seeds_verified_%s.json" % stamp), encoding="utf-8"))
    out, numbers, bad = {}, [], []
    for doi, rec in seeds.items():
        m = re.search(r"arXiv\.(\d{4}\.\d{4,5})", doi)
        if not m:
            continue
        aid = m.group(1)
        try:
            got = fetch_with_retry(aid)
        except Exception as e:
            bad.append((doi, str(e)[:100]))
            print("  FAIL %-24s %s" % (aid, str(e)[:80]))
            continue
        if not got:
            bad.append((doi, "no entry"))
            continue
        sim = difflib.SequenceMatcher(None, norm(got["title"]), norm(rec["title"])).ratio()
        ok = sim >= 0.75
        out[aid] = {**got, "doi": doi, "title_similarity": round(sim, 3), "title_check": ok}
        print("  %-14s sim=%.2f %s %s" % (aid, sim, "ok " if ok else "MISMATCH", got["title"][:70]))
        for sent in re.split(r"(?<=[.!?])\s+", got["abstract"]):
            if re.search(r"\d", sent) and len(sent) < 400:
                numbers.append({"arxiv": aid, "doi": doi, "sentence": sent.strip()})
        time.sleep(3)  # arXiv asks for a pause between requests
    io.open(os.path.join(LIT, "arxiv_abstracts_%s.json" % stamp), "w", encoding="utf-8", newline="").write(
        json.dumps(out, indent=1, ensure_ascii=False))
    io.open(os.path.join(LIT, "arxiv_numbers_%s.json" % stamp), "w", encoding="utf-8", newline="").write(
        json.dumps({"generated": time.strftime("%Y-%m-%d %H:%M"), "source": "arXiv API",
                    "note": "numeric sentences from real abstracts, for manual selection", "sentences": numbers},
                   indent=1, ensure_ascii=False))
    print("\nfetched %d abstracts, %d title checks failed, %d numeric sentences" % (len(out), len(bad), len(numbers)))
    for doi, err in bad:
        print("  bad:", doi, err)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
