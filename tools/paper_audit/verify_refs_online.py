# -*- coding: utf-8 -*-
"""One-time online verification of the bibliography (N-05 cache filler).

    python tools/paper_audit/verify_refs_online.py [--limit N] [--apply] [--no-cache]

Resolution order per entry: CrossRef /works/{doi} -> arXiv API (id_list) -> CrossRef
bibliographic title search (accept only an unambiguous candidate). Raw responses are cached in
docs/REF_RESOLUTION_CACHE.json so reruns are offline. Writes docs/REF_VERIFICATION.json
(offline N-05 cache) and prints a verified/mismatch/unverified summary.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tools.paper_audit import mechanical as M  # noqa: E402

CACHE = REPO / "docs" / "REF_RESOLUTION_CACHE.json"
OUT = REPO / "docs" / "REF_VERIFICATION.json"
UA = "paper-audit-refcheck/1.0 (mailto:hw4c24@soton.ac.uk)"
TODAY = date.today().isoformat()

LIVE_FILES = [
    ("paper_a1", ["main.tex", "related_work_bibitems.tex"]),
    ("paper_a2", ["main_ieee.tex"]),
    ("paper3/paper_ieee", ["main.tex"]),
    ("paper_review_prl", ["main_prl.tex"]),
]
LIVE_BIB = ["paper合/references.bib", "paper3/paper_ieee/references.bib",
            "paper3/paper_ieee/supplementary/references.bib"]


# --------------------------------------------------------------------------- network
def http_json(url: str, cache: dict, allow_cache=True):
    if allow_cache and url in cache:
        return cache[url].get("body"), url, "cache"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read().decode("utf-8", "replace")
        cache[url] = {"fetched_at": datetime.now().isoformat(timespec="seconds"),
                      "status": 200, "body": body}
        return body, url, "live"
    except Exception as exc:  # noqa: BLE001
        cache[url] = {"fetched_at": datetime.now().isoformat(timespec="seconds"),
                      "error": "%s: %s" % (type(exc).__name__, str(exc)[:160])}
        return None, url, "error"


def http_text(url: str, cache: dict, allow_cache=True):
    if allow_cache and url in cache:
        return cache[url].get("body"), url, "cache"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read().decode("utf-8", "replace")
        cache[url] = {"fetched_at": datetime.now().isoformat(timespec="seconds"),
                      "status": 200, "body": body}
        return body, url, "live"
    except Exception as exc:  # noqa: BLE001
        cache[url] = {"fetched_at": datetime.now().isoformat(timespec="seconds"),
                      "error": "%s: %s" % (type(exc).__name__, str(exc)[:160])}
        return None, url, "error"


def crossref_from_json(payload: str):
    d = json.loads(payload)["message"]
    authors = d.get("author") or []
    first = authors[0].get("family") if authors else ""
    issued = (d.get("issued", {}) or {}).get("date-parts") or [[None]]
    year = str(issued[0][0]) if issued and issued[0] and issued[0][0] else ""
    venue = (d.get("container-title") or [""])[0] or d.get("publisher", "")
    return {"title": (d.get("title") or [""])[0], "first_author": first, "year": year,
            "venue": venue, "doi": (d.get("DOI") or ""), "type": d.get("type", ""),
            "event": (d.get("event") or {}).get("name", "")}


def arxiv_from_xml(xml: str):
    m = re.search(r"<entry>(.*?)</entry>", xml, re.S)
    if not m:
        return None
    entry = m.group(1)

    def g(tag):
        mm = re.search(r"<%s[^>]*>(.*?)</%s>" % (tag, tag), entry, re.S)
        return re.sub(r"\s+", " ", mm.group(1)).strip() if mm else ""

    authors = re.findall(r"<name>(.*?)</name>", entry, re.S)
    first = authors[0].strip() if authors else ""
    surname = first.split()[-1] if first else ""
    published = g("published")
    year = published[:4] if published else ""
    venue = g("journal_ref") or g("doi")
    aid = g("id")
    return {"title": g("title"), "first_author": surname, "year": year, "venue": venue,
            "doi": g("doi"), "arxiv": aid.split("/abs/")[-1] if aid else ""}



# --------------------------------------------------------------------------- bibitem heuristics
QUOTED_RE = re.compile(r"``(.+?)''|\u201c(.+?)\u201d|\"(.+?)\"", re.S)


def parse_bibitem(key, body):
    flat = M.norm_text(body)
    q = QUOTED_RE.search(flat)
    title = (q.group(1) or q.group(2) or q.group(3) or "").strip() if q else ""
    if not title:  # fall back to text after "(YYYY)."
        m = re.search(r"\((?:19|20)\d{2}\)\.?\s*(.+?)(?:\.\s|$)", flat)
        title = m.group(1).strip() if m else ""
    if len(title) < 12:
        # Commentary / IEEE style has no quotes and no (YYYY): "Authors..., Title, Venue (year)."
        segs = [x.strip() for x in flat.split(", ") if x.strip()]
        venue_re = re.compile(r"(arxiv|preprint|proceedings|conference|journal|transactions|"
                              r"letters|workshop|symposium|press|vol\.|pp\.|\(\d{4}\)|"
                              r"advances|neurips|icml|iclr|cvpr|eccv|iccv|acl|emnlp|naacl)", re.I)
        cand, fallback = [], []
        for seg in segs:
            words = seg.split()
            if len(words) < 3 or venue_re.search(seg):
                continue
            # author segments are usually "First Last" (2 capitalised words) or bare initials
            if len(words) == 2 and all(w[0].isupper() for w in words if w):
                continue
            fallback.append((len(words), seg))
            # a real title usually contains lowercase function words
            if re.search(r"\b(the|of|for|and|with|in|on|to|a|an|is|are|from|via|under|"
                         r"across|through|using|towards|beyond|when|why|how|what)\b",
                         seg, re.I):
                cand.append((len(words), seg))
        pool = cand or fallback
        if pool:
            title = max(pool)[1].strip()
            title = re.sub(r"^[A-Z]\.\s+", "", title)  # drop an author initial that stuck
    ea = re.split(r" et al| and ", flat)[0]
    ea = re.sub(r"^\[[^\]]*\]\s*", "", ea).strip()
    first = ea.split(",")[0].strip()
    tokens = [t for t in re.split(r"\s+", first) if t]
    surname = tokens[-1] if tokens else ""
    if surname.lower() in ("al", "al.", "others"):
        surname = tokens[-2] if len(tokens) > 1 else ""
    doi = re.search(r"10\.\d{4,9}/[^\s\]<>,;\"]+", flat)
    doi_s = doi.group(0).rstrip(").,;'\"") if doi else ""
    arx = re.search(r"arXiv:\s*(\d{4}\.\d{4,5})", flat, re.I)
    year = re.search(r"\((?:19|20)\d{2}\)", flat)
    return {"key": key, "title": title, "first_author": surname,
            "year": year.group(0).strip("()") if year else "",
            "venue": "", "doi": doi_s, "arxiv": arx.group(1) if arx else "",
            "raw": flat[:500], "kind": "bibitem"}

def openalex_search(title: str, cache: dict):
    q = urllib.parse.quote(title[:220])
    url = "https://api.openalex.org/works?per-page=5&search=" + q
    payload, url, route = http_json(url, cache)
    if not payload:
        return None, url
    try:
        items = json.loads(payload).get("results") or []
    except json.JSONDecodeError:
        return None, url
    cands = []
    for it in items:
        src = {"title": it.get("title") or it.get("display_name") or "",
               "first_author": "", "year": str(it.get("publication_year") or ""),
               "venue": ((it.get("primary_location") or {}).get("source") or {}).get(
                   "display_name", "") or "",
               "doi": (it.get("doi") or "").replace("https://doi.org/", ""),
               "type": it.get("type", "")}
        auth = it.get("authorships") or []
        if auth:
            src["first_author"] = ((auth[0].get("author") or {}).get("display_name") or "")
        if title_similar(src["title"], title) >= 0.90:
            cands.append(src)
    return (cands[0] if len(cands) == 1 else None), url


# --------------------------------------------------------------------------- comparison
def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())




def title_similar(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


VENUE_WORDS = re.compile(r"(pp\.|proc\.|proceedings|conference|volume|vol\.|journal|"
                         r"transactions|letters|arxiv|iclr|icml|cvpr|neurips|eccv|iccv|"
                         r"adv\.|advances)", re.I)


def title_comparable(t: str) -> bool:
    return bool(t) and len(t) >= 8 and not VENUE_WORDS.search(t)

def surname(name):
    n = (name or "").strip()
    if not n:
        return ""
    if "," in n:
        return n.split(",")[0].strip()
    return n.split()[-1]


def compare(entry, src):
    problems, compared = [], []
    bib_title = (entry.get("title") or "").strip()
    if src.get("title") and title_comparable(bib_title) and norm(bib_title) != norm(src["title"]):
        problems.append(("title", bib_title, src["title"]))
    elif src.get("title") and title_comparable(bib_title):
        compared.append("title")
    bib_author = surname(entry.get("first_author", ""))
    if src.get("first_author") and re.match(r"^[A-Za-z][A-Za-z\-']{2,}$", bib_author):
        if bib_author.lower() != surname(src["first_author"]).lower():
            problems.append(("first_author", bib_author, surname(src["first_author"])))
        else:
            compared.append("first_author")
    if src.get("year") and entry.get("year") and str(src["year"]) != str(entry["year"]):
        problems.append(("year", entry["year"], src["year"]))
    elif src.get("year") and entry.get("year"):
        compared.append("year")
    venue_bib = (entry.get("venue") or "").lower()
    venue_src = (src.get("venue") or "").lower()
    repo_venue = re.search(r"(arxiv|cornell|hal\b|ssrn|researchgate|openreview|biorxiv|"
                           r"preprint|repository)", venue_src)
    if venue_src and venue_bib and not repo_venue:
        arxiv_only = ("arxiv" in venue_bib) and ("arxiv" not in venue_src)
        weak = norm(venue_bib)[:12] not in norm(venue_src) and norm(venue_src)[:12] not in norm(venue_bib)
        if arxiv_only or (weak and not re.search(r"(conference|proceedings|journal|transactions|letters|biometrika|trends)", venue_bib)):
            problems.append(("venue", entry.get("venue"), src.get("venue")))
    return problems


# --------------------------------------------------------------------------- collect
def collect():
    entries = {}
    order = []
    for rel_dir, names in LIVE_FILES:
        for name in names:
            p = REPO / rel_dir / name
            if not p.is_file():
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            for key, body in M.BIB_RE.findall(text):
                e = parse_bibitem(key, body)
                e["source_file"] = str(p.relative_to(REPO)).replace("\\", "/")
                add(entries, order, e)
    for rel in LIVE_BIB:
        p = REPO / rel
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for kind, key, body in M.BIB_FILE_RE.findall(text):
            fields = M._bib_fields(body)
            flat = M.norm_text(" ".join(fields.values()))
            arx = re.search(r"arXiv:\s*(\d{4}\.\d{4,5})", flat, re.I)
            e = {"key": key,
                 "title": fields.get("title", ""),
                 "first_author": fields.get("author", "").split(" and ")[0].split(",")[0],
                 "year": fields.get("year", ""),
                 "venue": fields.get("booktitle") or fields.get("journal", ""),
                 "doi": (fields.get("doi") or "").rstrip("."),
                 "arxiv": fields.get("eprint", "") or (arx.group(1) if arx else ""),
                 "raw": flat[:500],
                 "source_file": str(p.relative_to(REPO)).replace("\\", "/")}
            add(entries, order, e)
    return [entries[k] for k in order]


def add(entries, order, e):
    ident = (e["key"].lower(), norm(e["title"])[:60])
    if ident in entries:
        return
    entries[ident] = e
    order.append(ident)


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--no-cache", action="store_true")
    a = ap.parse_args()
    cache = {}
    if CACHE.is_file() and not a.no_cache:
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
    entries = collect()
    todo = [e for e in entries if e.get("doi") or e.get("arxiv")] + \
           [e for e in entries if not (e.get("doi") or e.get("arxiv"))]
    if a.limit:
        todo = todo[:a.limit]
    print("entries collected: %d (unique key+title); resolving %d" % (len(entries), len(todo)))
    results, requests = {}, 0
    last = 0.0
    for i, e in enumerate(todo, 1):
        src, url, route = None, "", ""
        try:
            if e.get("doi"):
                url = "https://api.crossref.org/works/" + urllib.parse.quote(e["doi"], safe="")
                payload, url, route = http_json(url, cache)
                if payload:
                    src = crossref_from_json(payload)
            elif e.get("arxiv"):
                url = ("http://export.arxiv.org/api/query?id_list=" +
                       urllib.parse.quote(e["arxiv"]))
                xml, url, route = http_text(url, cache)
                if xml and "<entry>" in xml:
                    src = arxiv_from_xml(xml)
            else:
                q = urllib.parse.quote(re.sub(r"[^\w\s]", " ", e["title"])[:220])
                url = ("https://api.crossref.org/works?rows=5&query.bibliographic=" + q)
                payload, url, route = http_json(url, cache)
                if payload:
                    items = (json.loads(payload).get("message") or {}).get("items") or []
                    cands = []
                    for it in items[:5]:
                        c = crossref_from_json(json.dumps({"message": it}))
                        if norm(c["title"]) == norm(e["title"]) or title_similar(c["title"], e["title"]) >= 0.90:
                            cands.append(c)
                    if len(cands) == 1:
                        src = cands[0]
                if src is None and e.get("title") and len(e["title"]) >= 8:
                    src, url2 = openalex_search(e["title"], cache)
                    if src is not None:
                        url = url2
            if route == "live":
                requests += 1
                wait = 1.0 - (time.time() - last)
                if wait > 0:
                    time.sleep(wait)
                last = time.time()
        except Exception as exc:  # noqa: BLE001
            src, url = None, "exception:%s" % type(exc).__name__
        if src is None or not src.get("title"):
            results[(e["key"].lower(), norm(e["title"])[:60])] = {
                "status": "unverified",
                "reason": "no authoritative match" if not url else "no match (%s)" % route,
                "source_url": url, "checked_at": TODAY}
            continue
        problems = compare(e, src)
        ident = (e["key"].lower(), norm(e["title"])[:60])
        if not problems and not src.get("title"):
            results[ident] = {"status": "unverified", "reason": "source gave no title",
                              "source_url": url, "checked_at": TODAY}
            continue
        results[ident] = {
            "status": "mismatch" if problems else "verified",
            "source": {"title": src.get("title"), "first_author": src.get("first_author"),
                       "year": src.get("year"), "venue": src.get("venue"),
                       "doi": src.get("doi"), "arxiv": src.get("arxiv"), "type": src.get("type")},
            "problems": problems,
            "source_url": url, "checked_at": TODAY, "route": route,
        }
        if i % 20 == 0 or i == len(todo):
            print("  %d/%d resolved (live requests=%d)" % (i, len(todo), requests), flush=True)
    (REPO / "docs" / "_ref_resolution_results.json").write_text(
        json.dumps({("%s|%s" % k): v for k, v in results.items()}, indent=1,
                   ensure_ascii=False), encoding="utf-8")
    if not a.no_cache:
        CACHE.write_text(json.dumps(cache, indent=0, ensure_ascii=False), encoding="utf-8")
    counts = {}
    for r in results.values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print("result:", counts, "| live requests:", requests, "| cache size:", len(cache))

    if a.apply:
        # merge into the offline N-05 cache; keep the pre-existing curated verified entries
        old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.is_file() else {"entries": {}}
        for e in entries:
            ident = (e["key"].lower(), norm(e["title"])[:60])
            r = results.get(ident)
            if not r:
                continue
            prev = old["entries"].get(e["key"], {})
            if r["status"] == "verified":
                src = r["source"]
                if src.get("first_author") and src.get("title"):
                    old["entries"][e["key"]] = {
                        "title": src["title"], "first_author": surname(src["first_author"]),
                        "year": src.get("year", ""), "venue": src.get("venue", ""),
                        "doi_or_arxiv": e.get("doi") or ("arXiv:" + e["arxiv"] if e.get("arxiv") else ""),
                        "source_url": r["source_url"], "checked_at": TODAY,
                        "status": "verified", "source": "crossref/arxiv one-time resolution"}
            elif r["status"] == "mismatch":
                prev.setdefault("mismatch", r["problems"])
                prev["checked_at"] = TODAY
                old["entries"][e["key"]] = prev
            else:
                prev.setdefault("reason", r.get("reason", ""))
                old["entries"].setdefault(e["key"], prev)
        old["built_at"] = TODAY
        old["counts"] = {"total": len(old["entries"]),
                         "verified": sum(1 for v in old["entries"].values()
                                         if not str(v.get("source", "")).startswith("unverified")
                                         and v.get("status") != "unverified"),
                         "unverified": sum(1 for v in old["entries"].values()
                                           if str(v.get("source", "")).startswith("unverified")
                                           or v.get("status") == "unverified")}
        OUT.write_text(json.dumps(old, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print("wrote", OUT.relative_to(REPO), old["counts"])
    else:
        print("(dry run: pass --apply to merge into docs/REF_VERIFICATION.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
