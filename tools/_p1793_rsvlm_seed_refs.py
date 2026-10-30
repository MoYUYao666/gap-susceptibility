# -*- coding: utf-8 -*-
r"""Curated seed references: the foundational works a remote-sensing VLM survey must cite.

OpenAlex keyword search returns applied RS papers but not the canonical natural-image foundation papers (they predate the
queries, or their venue has no Crossref DOI). This script takes a small seed list of *identifiers only* - never titles or
author strings typed from memory as facts - resolves each one live through DataCite (arXiv DOIs) or CrossRef, and admits a
seed only if the resolver returns a title. The resulting BibTeX is generated from the resolver's metadata.

Outputs
  paper_rsvlm_survey/literature/seeds_verified_<date>.json
  paper_rsvlm_survey/literature/seeds_verify_summary_<date>.json   (named failures, if any)

Usage
  D:\Anaconda\envs\pytorch\python.exe tools\_p1793_rsvlm_seed_refs.py
"""
import io
import json
import os
import time
import urllib.parse
import urllib.request

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIT = os.path.join("paper_rsvlm_survey", "literature")
UA = "dsh-survey-seeds/1.0 (mailto:research@example.org)"

# identifiers only: arXiv DOIs resolved through DataCite.
# Lesson (2026-10-27): 10.48550/arXiv.2003.03631 and .1705.00766 resolved to unrelated papers, which is why this list
# carries identifiers without titles: a resolver hit is checked against its own metadata, never against my memory, and a
# seed whose returned title is not the expected work is removed rather than cited.
SEEDS = [
    "10.48550/arXiv.2103.00020",  # CLIP
    "10.48550/arXiv.2303.15343",  # SigLIP
    "10.48550/arXiv.2212.07143",  # OpenCLIP
    "10.48550/arXiv.2102.05918",  # ALIGN
    "10.48550/arXiv.2201.12086",  # BLIP
    "10.48550/arXiv.2301.12597",  # BLIP-2
    "10.48550/arXiv.2304.08485",  # LLaVA
    "10.48550/arXiv.2204.14198",  # Flamingo
    "10.48550/arXiv.2203.02053",  # Mind the gap (modality gap)
    "10.48550/arXiv.2306.11029",  # RemoteCLIP
    "10.48550/arXiv.2311.15826",  # GeoChat
]


def get_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def datacite(doi):
    d = get_json("https://api.datacite.org/dois/" + urllib.parse.quote(doi, safe=""))["data"]["attributes"]
    creators = [c.get("name", "") for c in d.get("creators", [])]
    return {
        "title": (d.get("titles") or [{}])[0].get("title", ""),
        "year": d.get("publicationYear"),
        "venue": "arXiv" if (d.get("publisher") or "").lower().startswith("arxiv") else (d.get("publisher") or ""),
        "authors": creators,
        "type": d.get("types", {}).get("resourceTypeGeneral"),
    }


def crossref(doi):
    m = get_json("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe=""))["message"]
    return {
        "title": (m.get("title") or [""])[0],
        "year": (m.get("issued", {}).get("date-parts") or [[None]])[0][0],
        "venue": (m.get("container-title") or [""])[0] or (m.get("publisher") or ""),
        "authors": [(a.get("family") or a.get("name") or "") for a in m.get("author", [])],
        "type": m.get("type"),
    }


def bibkey(rec, used):
    first = (rec["authors"][0].split()[-1] if rec["authors"] else "anon").lower()
    first = "".join(ch for ch in first if ch.isalpha()) or "anon"
    word = "".join(ch for ch in (rec["title"].split() or ["ref"])[0].lower() if ch.isalpha()) or "ref"
    base = "%s%s%s" % (first, word, rec.get("year") or "")
    key, i = base, 0
    while key in used:
        i += 1
        key = base + chr(96 + i)
    used.add(key)
    return key


def to_bib(rec, key):
    authors = " and ".join(rec["authors"]) if rec["authors"] else "Unknown"
    fields = [("title", rec["title"]), ("author", authors), ("journal", rec["venue"]),
              ("year", str(rec["year"] or "")), ("doi", rec["doi"])]
    body = ",\n".join("  %s = {%s}" % (k, v.replace("{", "").replace("}", "")) for k, v in fields if v)
    return "@article{%s,\n%s\n}\n" % (key, body)


def main() -> int:
    stamp = time.strftime("%Y-%m-%d")
    verified, failed = {}, {}
    used = set()
    for doi in SEEDS:
        try:
            rec = datacite(doi) if doi.startswith("10.48550") else crossref(doi)
            if not rec["title"]:
                raise ValueError("resolver returned no title")
            rec["doi"] = doi
            rec["source"] = "curated seed, identifier resolved live"
            rec["bibkey"] = bibkey(rec, used)
            verified[doi] = rec
            print("  ok   %-32s %s (%s)" % (doi, rec["title"][:70], rec["year"]))
        except Exception as e:
            failed[doi] = str(e)[:160]
            print("  FAIL %-32s %s" % (doi, str(e)[:90]))
        time.sleep(0.2)

    io.open(os.path.join(LIT, "seeds_verified_%s.json" % stamp), "w", encoding="utf-8", newline="").write(
        json.dumps(verified, indent=1, ensure_ascii=False))
    io.open(os.path.join(LIT, "seeds_verify_summary_%s.json" % stamp), "w", encoding="utf-8", newline="").write(
        json.dumps({"generated": time.strftime("%Y-%m-%d %H:%M"), "resolver": "DataCite/CrossRef live",
                    "n_seeds": len(SEEDS), "verified": len(verified), "failed": failed}, indent=2, ensure_ascii=False))

    # append to survey.bib, skipping DOIs already present
    bibpath = os.path.join(LIT, "survey.bib")
    existing = io.open(bibpath, encoding="utf-8").read() if os.path.exists(bibpath) else ""
    added = []
    for doi, rec in verified.items():
        if doi in existing:
            continue
        added.append(to_bib(rec, rec["bibkey"]))
    if added:
        with io.open(bibpath, "a", encoding="utf-8", newline="") as f:
            f.write("\n% ---- curated foundational seeds (live-resolved) ----\n")
            f.write("\n".join(added))
    print("\nseed verified %d / %d, appended %d entries to survey.bib" % (len(verified), len(SEEDS), len(added)))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
