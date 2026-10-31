# -*- coding: utf-8 -*-
"""Rigorous confirmation pass for the unresolved bibliography entries.

For every entry that is still unverified in docs/REF_VERIFICATION.json:
  * self-citations to our own manuscripts -> confirm against the local manuscript (internal record)
  * dataset / URL-only citations          -> confirm by fetching the URL
  * DOI present                           -> CrossRef, OpenAlex doi, doi.org resolution, then title+author
                                             search; a different DOI is a typo -> plan the correction
  * no identifier                         -> CrossRef / OpenAlex / arXiv / DBLP / Semantic Scholar title
                                             + first-author search; a unique title+surname match confirms
Anything with no record anywhere is marked deleted-unconfirmable.

The script only REPORTS (docs/_ref_confirm_results.json); a separate step applies edits.
Raw HTTP responses are cached in docs/REF_RESOLUTION_CACHE.json (shared with verify_refs_online.py).
"""
from __future__ import annotations

import json
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tools.paper_audit import mechanical as M  # noqa: E402
from tools.paper_audit import verify_refs_online as V  # noqa: E402

CACHE = REPO / "docs" / "REF_RESOLUTION_CACHE.json"
STATE = REPO / "docs" / "_ref_confirm_results.json"
VERIFY = REPO / "docs" / "REF_VERIFICATION.json"
TODAY = date.today().isoformat()
UA = V.UA
DELAY = 0.35
SSL_CTX = ssl._create_unverified_context()

SELF_KEYS = {"wanA1", "wanP1", "wan2026protect"}
URL_KEYS_HINT = ("nksid", "oceanclip", "dataset", "huggingface", "github")


def load_cache():
    if CACHE.is_file():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


def http(url, cache, as_json=True, timeout=25, retries=2):
    if url in cache and cache[url].get("body"):
        rec = cache[url]
        return rec.get("body"), rec
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    err = ""
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as r:
                body = r.read().decode("utf-8", "replace")
                final = r.geturl()
            cache[url] = {"fetched_at": date.today().isoformat(), "status": 200,
                          "final_url": final, "body": body}
            return body, cache[url]
        except Exception as exc:  # noqa: BLE001
            err = "%s: %s" % (type(exc).__name__, str(exc)[:160])
            if attempt < retries:
                time.sleep(2 + 3 * attempt)
                continue
    cache[url] = {"fetched_at": date.today().isoformat(), "error": err}
    return None, cache[url]


def cw_get(url, cache):
    body, rec = http(url, cache)
    if not body:
        return None, rec
    try:
        return json.loads(body), rec
    except json.JSONDecodeError:
        return None, rec


# ------------------------------------------------------------------ candidates
def make_cand(source, title, authors, year, venue, doi="", arxiv="", url="", extra=None):
    names = [a.get("name") if isinstance(a, dict) else str(a) for a in (authors or [])]
    return {"source": source, "title": title or "", "authors": names,
            "first_author": names[0] if names else "", "year": str(year or ""),
            "venue": venue or "", "doi": (doi or "").rstrip("."), "arxiv": arxiv or "",
            "url": url, "extra": extra or {}}


def accept(entry, cand):
    """Unique candidate: title matches and first-author surname matches."""
    if not cand or not cand.get("title"):
        return None
    sim = V.title_similar(cand["title"], entry.get("title") or "")
    same = V.norm(cand["title"]) == V.norm(entry.get("title") or "")
    if not (same or sim >= 0.92):
        return None
    bib_surname = V.surname(entry.get("first_author") or "")
    cand_surname = V.surname(cand.get("first_author") or "")
    if bib_surname and len(bib_surname) >= 3:
        if cand_surname.lower() != bib_surname.lower():
            return None
    cand["score"] = round(sim, 3)
    return cand


def crossref_cand(it):
    return make_cand("crossref", (it.get("title") or [""])[0],
                     [(a.get("family") or "") for a in (it.get("author") or [])],
                     (it.get("issued", {}).get("date-parts") or [[None]])[0][0],
                     (it.get("container-title") or [""])[0],
                     it.get("DOI", ""), "", "")


def openalex_cand(it):
    auth = [(x.get("author") or {}).get("display_name", "") for x in (it.get("authorships") or [])]
    return make_cand("openalex", it.get("title") or it.get("display_name") or "", auth,
                     it.get("publication_year"),
                     ((it.get("primary_location") or {}).get("source") or {}).get("display_name", ""),
                     (it.get("doi") or "").replace("https://doi.org/", ""), "", "")


def arxiv_cands(xml):
    out = []
    for m in re.finditer(r"<entry>(.*?)</entry>", xml, re.S):
        e = m.group(1)

        def g(tag):
            mm = re.search(r"<%s[^>]*>(.*?)</%s>" % (tag, tag), e, re.S)
            return re.sub(r"\s+", " ", mm.group(1)).strip() if mm else ""

        names = re.findall(r"<name>(.*?)</name>", e)
        aid = g("id").split("/abs/")[-1]
        out.append(make_cand("arxiv", g("title"), names, g("published")[:4], g("journal_ref"),
                             g("doi"), aid, g("id")))
    return out


# ------------------------------------------------------------------ services
def try_doi(entry, cache, attempts):
    doi = (entry.get("doi") or "").strip().rstrip(".")
    if not doi:
        return None
    for label, url in (("crossref-doi",
                        "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")),
                       ("openalex-doi", "https://api.openalex.org/works/doi:" + doi)):
        d, rec = cw_get(url, cache)
        attempts.append({"service": label, "ok": bool(d), "error": rec.get("error", "")})
        time.sleep(DELAY)
        if not d:
            continue
        if label == "crossref-doi":
            cand = crossref_cand((d.get("message") or {}))
        else:
            cand = openalex_cand(d)
        got = accept(entry, cand)
        if got:
            got["matched_doi"] = cand["doi"] or doi
            return got
    # doi.org existence check (publisher redirect)
    body, rec = http("https://doi.org/" + doi, cache, timeout=25)
    attempts.append({"service": "doi.org", "ok": bool(rec.get("final_url")),
                     "final_url": rec.get("final_url", ""), "error": rec.get("error", "")})
    time.sleep(DELAY)
    if body:
        title = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
        if title:
            cand = make_cand("doi.org", re.sub(r"\s+", " ", title.group(1)).strip(),
                             [], "", "", doi, "", rec.get("final_url", ""))
            got = accept(entry, cand)
            if got:
                return got
    return None


def try_title_search(entry, cache, attempts):
    title = entry.get("title") or ""
    if len(title) < 8:
        return None
    surname = V.surname(entry.get("first_author") or "")
    q = urllib.parse.quote(re.sub(r"[^\w\s]", " ", title)[:220])
    cands = []
    # CrossRef bibliographic (+ optional author)
    url = "https://api.crossref.org/works?rows=8&query.bibliographic=" + q
    if surname:
        url += "&query.author=" + urllib.parse.quote(surname)
    d, rec = cw_get(url, cache)
    attempts.append({"service": "crossref-search", "ok": bool(d), "error": rec.get("error", "")})
    time.sleep(DELAY)
    if d:
        cands += [crossref_cand(it) for it in ((d.get("message") or {}).get("items") or [])]
    # OpenAlex
    d, rec = cw_get("https://api.openalex.org/works?per-page=8&search=" + q, cache)
    attempts.append({"service": "openalex-search", "ok": bool(d), "error": rec.get("error", "")})
    time.sleep(DELAY)
    if d:
        cands += [openalex_cand(it) for it in (d.get("results") or [])]
    # arXiv
    if len(title) >= 10:
        aq = ("http://export.arxiv.org/api/query?max_results=8&search_query=ti:%22" +
              urllib.parse.quote(re.sub(r"[^\w\s-]", " ", title)[:180]) + "%22")
        body, rec = http(aq, cache)
        attempts.append({"service": "arxiv-search", "ok": bool(body), "error": rec.get("error", "")})
        time.sleep(DELAY)
        if body:
            cands += arxiv_cands(body)
    # DBLP
    d, rec = cw_get("https://dblp.org/search/publ/api?format=json&h=8&q=" + q, cache)
    attempts.append({"service": "dblp", "ok": bool(d), "error": rec.get("error", "")})
    time.sleep(DELAY)
    if d:
        for hit in ((d.get("result") or {}).get("hits") or {}).get("hit") or []:
            info = hit.get("info") or {}
            au = info.get("authors", {}).get("author") if isinstance(info.get("authors"), dict) else info.get("authors")
            names = [ (a.get("text") if isinstance(a, dict) else str(a)) for a in (au if isinstance(au, list) else [au] if au else []) ]
            cands.append(make_cand("dblp", info.get("title", ""), names, info.get("year", ""),
                                   info.get("venue", ""), info.get("doi", ""), info.get("ee", ""),
                                   info.get("url", "")))
    # Semantic Scholar
    d, rec = cw_get("https://api.semanticscholar.org/graph/v1/paper/search?limit=8&fields="
                    "title,authors,year,venue,externalIds,url&query=" + q, cache)
    if not d:
        time.sleep(6)
        d, rec = cw_get("https://api.semanticscholar.org/graph/v1/paper/search?limit=8&fields="
                        "title,authors,year,venue,externalIds,url&query=" + q, cache)
    attempts.append({"service": "semanticscholar", "ok": bool(d), "error": rec.get("error", "")})
    time.sleep(DELAY)
    if d:
        for it in (d.get("data") or []):
            ext = it.get("externalIds") or {}
            cands.append(make_cand("semanticscholar", it.get("title", ""),
                                   [(a.get("name") or "") for a in (it.get("authors") or [])],
                                   it.get("year", ""), it.get("venue", ""),
                                   ext.get("DOI", ""), ext.get("ArXiv", ""), it.get("url", "")))
    ok = [c for c in cands if accept(entry, c)]
    if not ok:
        return None
    # prefer the candidate that agrees on year and carries an identifier
    ok.sort(key=lambda c: (str(c.get("year") or "") == str(entry.get("year") or ""),
                           bool(c.get("doi") or c.get("arxiv")), c.get("score", 0)), reverse=True)
    return ok[0]


def try_url(entry, cache, attempts):
    raw = entry.get("raw") or ""
    m = re.search(r"https?://[^\s)\];,}]+", raw)
    if not m:
        return None
    url = m.group(0).rstrip(".")
    gh = re.match(r"https?://github\.com/([^/]+)/([^/#?]+)", url)
    hf = re.match(r"https?://huggingface\.co/([^/]+)/([^/#?]+)", url)
    if gh:
        url = "https://api.github.com/repos/%s/%s" % (gh.group(1), gh.group(2).rstrip("/"))
    elif hf:
        url = "https://hf-mirror.com/api/models/%s/%s" % (hf.group(1), hf.group(2).rstrip("/"))
    body, rec = http(url, cache, timeout=30)
    attempts.append({"service": "url", "url": url, "ok": bool(body),
                     "final_url": rec.get("final_url", ""), "error": rec.get("error", "")})
    time.sleep(DELAY)
    if not body:
        return None
    return {"source": "url", "title": entry.get("title") or "", "authors": [],
            "first_author": "", "year": entry.get("year") or "", "venue": "web resource",
            "doi": "", "arxiv": "", "url": rec.get("final_url") or url, "score": 1.0}


def try_internal(entry):
    title = (entry.get("title") or "").strip()
    if len(title) < 12:
        return None
    words = [w for w in re.findall(r"[A-Za-z]{5,}", title)][:4]
    if not words:
        return None
    pat = re.compile(r"\s+".join(re.escape(w) for w in words), re.I)
    for rel in ("paper_a1/main.tex", "paper合/main_nc.tex", "paper合/main_springer.tex",
                "paper3/paper_ieee/main.tex", "paper_a2/main_ieee.tex"):
        p = REPO / rel
        if p.is_file() and pat.search(p.read_text(encoding="utf-8", errors="replace")):
            return {"source": "internal-manuscript", "title": title, "authors": ["Wan, H."],
                    "first_author": "Wan", "year": entry.get("year") or "",
                    "venue": rel, "doi": "", "arxiv": "", "url": rel, "score": 1.0}
    return None


# ------------------------------------------------------------------ main
def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--retry-deleted", action="store_true")
    args = ap.parse_args()
    cache = load_cache()
    verify = json.loads(VERIFY.read_text(encoding="utf-8"))
    entries = V.collect()
    results = {}
    if args.retry_deleted and STATE.is_file():
        prev = json.loads(STATE.read_text(encoding="utf-8"))
        results = {k: v for k, v in prev.items() if v.get("verdict") != "deleted-unconfirmable"}
        skipped = {k for k, v in prev.items() if v.get("verdict") == "deleted-unconfirmable"}
        entries = [e for e in entries if e["key"] in skipped]
        print("retrying", len(entries), "previously unconfirmed entries")
    for e in entries:
        c = verify["entries"].get(e["key"]) or {}
        status = c.get("status")
        if status == "verified":
            continue
        key = e["key"]
        attempts = []
        verdict = None
        if key in SELF_KEYS:
            hit = try_internal(e)
            attempts.append({"service": "internal-manuscript", "ok": bool(hit)})
            if hit:
                verdict = {"kind": "confirmed-internal", "candidate": hit}
        if verdict is None and not (e.get("doi") or e.get("arxiv")):
            hit = try_url(e, cache, attempts)
            if hit:
                verdict = {"kind": "confirmed-url", "candidate": hit}
        if verdict is None and e.get("doi"):
            hit = try_doi(e, cache, attempts)
            if hit:
                kind = "confirmed-no-change"
                if V.norm(hit.get("doi") or "") and V.norm(hit["doi"]) != V.norm(e["doi"]):
                    kind = "fixed-doi"
                verdict = {"kind": kind, "candidate": hit}
        if verdict is None:
            hit = try_title_search(e, cache, attempts)
            if hit:
                kind = "confirmed-no-change"
                cand_ids = set(filter(None, [(hit.get("doi") or "").lower(),
                                             (hit.get("arxiv") or "").lower()]))
                bib_ids = set(filter(None, [(e.get("doi") or "").lower(),
                                            (e.get("arxiv") or "").lower()]))
                if cand_ids and not (cand_ids & bib_ids):
                    kind = "fixed-identifier"
                verdict = {"kind": kind, "candidate": hit}
        if verdict is None:
            verdict = {"kind": "deleted-unconfirmable", "candidate": None}
        results[key] = {"entry": {k: e.get(k) for k in
                                  ("key", "title", "first_author", "year", "venue", "doi",
                                   "arxiv", "source_file", "raw")},
                        "verdict": verdict["kind"], "candidate": verdict["candidate"],
                        "attempts": attempts}
        print("%-26s %-24s %s" % (key[:26], verdict["kind"],
                                  (verdict["candidate"] or {}).get("summary", "")
                                  or ((verdict["candidate"] or {}).get("source", "") + " "
                                      + str((verdict["candidate"] or {}).get("doi", ""))[:40])), flush=True)
    STATE.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    CACHE.write_text(json.dumps(cache, indent=0, ensure_ascii=False), encoding="utf-8")
    from collections import Counter
    print("\nverdicts:", Counter(v["verdict"] for v in results.values()))
    print("wrote", STATE.relative_to(REPO), "| cache entries:", len(cache))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
