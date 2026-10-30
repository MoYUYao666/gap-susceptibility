# -*- coding: utf-8 -*-
r"""Verify the survey bibliography against CrossRef: every citation must resolve to a real, matching record.

The rule this enforces: no reference enters the manuscript unless the DOI resolves live and the CrossRef title matches the
title we harvested. Records that fail are reported, not silently dropped, so a failure always has a name attached.

Inputs
  paper_rsvlm_survey/literature/dedup_<date>.json   (produced by tools/_p1790_rsvlm_lit_harvest.py)

Outputs
  paper_rsvlm_survey/literature/verified_<date>.json   per-DOI verdict with the CrossRef evidence
  paper_rsvlm_survey/literature/survey.bib             BibTeX built only from verified records
  paper_rsvlm_survey/literature/verify_summary_<date>.json

Usage
  D:\Anaconda\envs\pytorch\python.exe tools\_p1791_rsvlm_verify_bib.py [--limit N] [--sleep 0.15]
  Exit code 1 when any DOI fails to resolve or the title disagrees.
"""
import argparse
import difflib
import io
import json
import os
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTDIR = os.path.join("paper_rsvlm_survey", "literature")
UA = "dsh-survey-verify/1.0 (mailto:research@example.org)"


def get_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def norm_title(s):
    s = re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower())
    return re.sub(r"\s+", " ", s).strip()


def robust_get(url, attempts=4):
    """GET with backoff: CrossRef answers 429 under burst load, which is transient and must not look like a bad DOI."""
    delay = 2.0
    last = None
    for k in range(attempts):
        try:
            return get_json(url, timeout=30)
        except Exception as e:
            last = e
            msg = str(e)
            transient = ("429" in msg) or ("timed out" in msg) or ("500" in msg) or ("502" in msg) or ("503" in msg)
            if not transient or k == attempts - 1:
                raise
            time.sleep(delay)
            delay = min(delay * 2, 12.0)
    raise last


def crossref(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    return robust_get(url)["message"]


DATACITE_PREFIXES = ("10.5281", "10.6084", "10.34734", "10.48550", "10.71465")


def datacite(doi):
    url = "https://api.datacite.org/dois/" + urllib.parse.quote(doi, safe="")
    d = robust_get(url)["data"]["attributes"]
    return {"title": [ (d.get("titles") or [{}])[0].get("title", "") ],
            "issued": {"date-parts": [[(d.get("publicationYear") or None)]]},
            "container-title": [ (d.get("publisher") or "") ],
            "type": d.get("types", {}).get("resourceTypeGeneral", "dataset")}


def bib_key(rec, used):
    first = (rec["authors"][0].split()[-1] if rec.get("authors") else "anon").lower()
    first = re.sub(r"[^a-z]", "", first) or "anon"
    word = re.sub(r"[^a-z]", "", (rec["title"].split() or ["ref"])[0].lower()) or "ref"
    key = "%s%s%d" % (first, word, rec.get("year") or 0)
    base, i = key, 1
    while key in used:
        i += 1
        key = "%s%s%d%s" % (first, word, rec.get("year") or 0, chr(96 + i))
    used.add(key)
    return key


def to_bibtex(rec, key):
    authors = " and ".join(rec["authors"]) if rec.get("authors") else "Unknown"
    fields = [
        ("title", rec["title"]),
        ("author", authors),
        ("journal", rec.get("venue") or ""),
        ("year", str(rec.get("year") or "")),
        ("doi", rec["doi"]),
    ]
    body = ",\n".join("  %s = {%s}" % (k, v.replace("{", "").replace("}", "")) for k, v in fields if v)
    return "@article{%s,\n%s\n}\n" % (key, body)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sleep", type=float, default=0.15)
    a = ap.parse_args()
    stamp = time.strftime("%Y-%m-%d")
    src = os.path.join(OUTDIR, "dedup_%s.json" % stamp)
    dedup = json.load(io.open(src, encoding="utf-8"))
    items = [(k, v) for k, v in dedup.items() if v.get("doi")]
    items.sort(key=lambda kv: (-(kv[1].get("cited_by") or 0), kv[1].get("year") or 0))
    if a.limit:
        items = items[:a.limit]
    print("verifying %d DOIs against CrossRef" % len(items))

    verified, failed = {}, {}

    def check(item):
        key, rec = item
        try:
            m = datacite(rec["doi"]) if rec["doi"].startswith(DATACITE_PREFIXES) else crossref(rec["doi"])
            cr_title = (m.get("title") or [""])[0]
            score = difflib.SequenceMatcher(None, norm_title(cr_title), norm_title(rec["title"])).ratio()
            rec2 = dict(rec)
            rec2["crossref"] = {
                "title": cr_title,
                "year": (m.get("issued", {}).get("date-parts") or [[None]])[0][0],
                "container": (m.get("container-title") or [""])[0],
                "type": m.get("type"),
                "title_similarity": round(score, 3),
                "resolves": True,
            }
            rec2["verified"] = score >= 0.80
            return key, rec2, None
        except Exception as e:
            return key, {**rec, "verified": False, "crossref_error": str(e)[:160]}, str(e)[:160]

    done = 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(check, it) for it in items]
        for fut in as_completed(futures):
            key, rec2, err = fut.result()
            done += 1
            if rec2.get("verified"):
                verified[key] = rec2
            else:
                failed[key] = rec2
            if done % 100 == 0:
                print("  %d/%d verified=%d failed=%d" % (done, len(items), len(verified), len(failed)))

    used = set()
    bib = []
    for key, rec in sorted(verified.items(), key=lambda kv: (-(kv[1].get("cited_by") or 0), kv[1]["title"])):
        bkey = bib_key(rec, used)
        rec["bibkey"] = bkey
        bib.append(to_bibtex(rec, bkey))
    io.open(os.path.join(OUTDIR, "survey.bib"), "w", encoding="utf-8", newline="").write("\n".join(bib))
    io.open(os.path.join(OUTDIR, "verified_%s.json" % stamp), "w", encoding="utf-8", newline="").write(
        json.dumps(verified, indent=1, ensure_ascii=False))
    summary = {
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "checked": len(items), "verified": len(verified), "failed": len(failed),
        "crossref_api": "https://api.crossref.org/works/{doi}",
        "title_similarity_threshold": 0.80,
        "failures": {k: {"doi": v.get("doi"), "title": v.get("title"),
                         "error": v.get("crossref_error") or "title mismatch"} for k, v in list(failed.items())[:40]},
    }
    io.open(os.path.join(OUTDIR, "verify_summary_%s.json" % stamp), "w", encoding="utf-8", newline="").write(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print("\nverified %d / %d (%.1f%%), failed %d" %
          (len(verified), len(items), 100.0 * len(verified) / max(1, len(items)), len(failed)))
    print("wrote survey.bib with %d entries" % len(bib))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
