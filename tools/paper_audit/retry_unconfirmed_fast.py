# -*- coding: utf-8 -*-
"""Fast, targeted second confirmation attempt for entries still marked deleted-unconfirmable.

Uses the services that actually answer in this environment (arXiv API title search, OpenAlex title
search, CrossRef bibliographic), skips DBLP/S2 (blocked/rate-limited), and confirms our own
companion manuscripts against the local manuscript files. Reports only; edits happen separately.
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

REPO = Path(r"D:\Realdesktop\Wan\Important\New")
sys.path.insert(0, str(REPO))
from tools.paper_audit import verify_refs_online as V  # noqa: E402

STATE = REPO / "docs" / "_ref_confirm_results.json"
CACHE = REPO / "docs" / "REF_RESOLUTION_CACHE.json"
UA = V.UA
CTX = ssl._create_unverified_context()
TODAY = date.today().isoformat()
DELAY = 0.25

SELF_MAP = {
    "wanA1": ("paper_a1/main.tex", "Order Preservation Tracks Zero-Shot Accuracy"),
    "wanP1": ("paper合/main_nc.tex", "Adaptation Site and the Modality Gap"),
    "wan2026protect": ("paper合/main_nc.tex", "Adaptation Site and the Modality Gap"),
    "wan2026gap": ("paper合/main_nc.tex", "Adaptation Site and the Modality Gap"),
}


def load_json(p):
    return json.loads(p.read_text(encoding="utf-8"))


def save_json(p, d):
    p.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")


def get(url, cache, timeout=25):
    if url in cache and cache[url].get("body"):
        return cache[url]["body"], cache[url]
    try:
        with urllib.request.urlopen(urllib.request.Request(
                url, headers={"User-Agent": UA}), timeout=timeout, context=CTX) as r:
            body = r.read().decode("utf-8", "replace")
            final = r.geturl()
        cache[url] = {"fetched_at": TODAY, "status": 200, "final_url": final, "body": body}
        return body, cache[url]
    except Exception as exc:  # noqa: BLE001
        cache[url] = {"fetched_at": TODAY, "error": "%s: %s" % (type(exc).__name__,
                                                                str(exc)[:140])}
        return None, cache[url]


def sanitize(t):
    return re.sub(r"[^\w\s-]", " ", t).strip()


def arxiv_cands(xml):
    out = []
    for m in re.finditer(r"<entry>(.*?)</entry>", xml, re.S):
        e = m.group(1)

        def g(tag):
            mm = re.search(r"<%s[^>]*>(.*?)</%s>" % (tag, tag), e, re.S)
            return re.sub(r"\s+", " ", mm.group(1)).strip() if mm else ""

        names = re.findall(r"<name>(.*?)</name>", e)
        aid = g("id").split("/abs/")[-1]
        out.append({"source": "arxiv", "title": g("title"), "authors": names,
                    "first_author": names[0] if names else "",
                    "year": g("published")[:4], "venue": g("journal_ref"),
                    "doi": g("doi"), "arxiv": aid, "url": g("id")})
    return out


def confirm(entry, cache):
    title = (entry.get("title") or "").strip()
    surname = V.surname(entry.get("first_author") or "")
    attempts = []

    def accept(cands):
        best = None
        for c in cands:
            if not c.get("title"):
                continue
            sim = V.title_similar(c["title"], title)
            if V.norm(c["title"]) != V.norm(title) and sim < 0.90:
                continue
            cs = V.surname(c.get("first_author") or "")
            if surname and len(surname) >= 3 and cs.lower() != surname.lower():
                continue
            c["score"] = round(sim, 3)
            rank = (c["score"], bool(c.get("doi") or c.get("arxiv")),
                    str(c.get("year")) == str(entry.get("year")))
            if best is None or rank > best[0]:
                best = (rank, c)
        return best[1] if best else None

    if len(title) >= 10:
        # arXiv title phrase: try the full phrase, then a distinctive 4-6 word window
        phrases = [sanitize(title)]
        words = sanitize(title).split()
        if len(words) > 6:
            phrases.append(" ".join(words[2:8]))
            phrases.append(" ".join(words[:6]))
        for ph in phrases[:2]:
            u = ("http://export.arxiv.org/api/query?max_results=8&search_query=ti:%22" +
                 urllib.parse.quote(ph[:180]) + "%22")
            b, rec = get(u, cache)
            attempts.append({"service": "arxiv-search", "query": ph[:60], "ok": bool(b),
                             "error": rec.get("error", "")})
            time.sleep(DELAY)
            if b:
                hit = accept(arxiv_cands(b))
                if hit:
                    return hit, attempts
        q = urllib.parse.quote(sanitize(title)[:200])
        d = None
        b, rec = get("https://api.openalex.org/works?per-page=8&search=" + q, cache)
        attempts.append({"service": "openalex-search", "ok": bool(b), "error": rec.get("error", "")})
        time.sleep(DELAY)
        if b:
            try:
                res = json.loads(b).get("results") or []
            except json.JSONDecodeError:
                res = []
            cands = []
            for it in res:
                auth = [(x.get("author") or {}).get("display_name", "")
                        for x in (it.get("authorships") or [])]
                cands.append({"source": "openalex", "title": it.get("title") or "",
                              "authors": auth, "first_author": auth[0] if auth else "",
                              "year": str(it.get("publication_year") or ""),
                              "venue": ((it.get("primary_location") or {}).get("source") or {}).get("display_name", ""),
                              "doi": (it.get("doi") or "").replace("https://doi.org/", ""),
                              "arxiv": "", "url": it.get("id", "")})
            hit = accept(cands)
            if hit:
                return hit, attempts
        b, rec = get("https://api.crossref.org/works?rows=8&query.bibliographic=" + q, cache)
        attempts.append({"service": "crossref-search", "ok": bool(b), "error": rec.get("error", "")})
        time.sleep(DELAY)
        if b:
            try:
                items = json.loads(b)["message"]["items"]
            except (json.JSONDecodeError, KeyError):
                items = []
            cands = []
            for it in items:
                auth = [(a.get("family") or "") for a in (it.get("author") or [])]
                cands.append({"source": "crossref", "title": (it.get("title") or [""])[0],
                              "authors": auth, "first_author": auth[0] if auth else "",
                              "year": str((it.get("issued", {}).get("date-parts") or [[None]])[0][0]),
                              "venue": (it.get("container-title") or [""])[0],
                              "doi": it.get("DOI", ""), "arxiv": "", "url": ""})
            hit = accept(cands)
            if hit:
                return hit, attempts
    # URL-based (software / dataset) confirmation
    m = re.search(r"https?://[^\s)\];,}]+", entry.get("raw") or "")
    if m:
        url = m.group(0).rstrip(".")
        gh = re.match(r"https?://github\.com/([^/]+)/([^/#?]+)", url)
        hf = re.match(r"https?://huggingface\.co/([^/]+)/([^/#?]+)", url)
        if gh:
            url = "https://api.github.com/repos/%s/%s" % (gh.group(1), gh.group(2).rstrip("/"))
        elif hf:
            url = "https://hf-mirror.com/api/models/%s/%s" % (hf.group(1), hf.group(2).rstrip("/"))
        b, rec = get(url, cache, timeout=30)
        attempts.append({"service": "url", "url": url, "ok": bool(b),
                         "error": rec.get("error", "")})
        if b:
            return {"source": "url", "title": entry.get("title") or "", "authors": [],
                    "first_author": "", "year": entry.get("year") or "", "venue": "web resource",
                    "doi": "", "arxiv": "", "url": rec.get("final_url") or url}, attempts
    return None, attempts


def main() -> int:
    state = load_json(STATE)
    cache = load_json(CACHE)
    entries = {e["key"]: e for e in V.collect()}
    retry = [k for k, v in state.items() if v.get("verdict") == "deleted-unconfirmable"]
    print("retrying:", len(retry))
    changed = 0
    for key in retry:
        e = entries.get(key)
        if e is None:
            continue
        if key in SELF_MAP:
            rel, title_hint = SELF_MAP[key]
            p = REPO / rel
            ok = p.is_file() and title_hint.split(":")[0][:40].lower() in p.read_text(
                encoding="utf-8", errors="replace").lower()
            state[key].update({"verdict": "confirmed-internal",
                               "candidate": {"source": "internal-manuscript", "title":
                                             state[key]["entry"].get("title"),
                                             "authors": ["Wan, H."], "first_author": "Wan",
                                             "year": state[key]["entry"].get("year"),
                                             "venue": rel, "doi": "", "arxiv": "",
                                             "url": rel}})
            state[key]["attempts"].append({"service": "internal-manuscript", "path": rel,
                                           "ok": ok})
            changed += 1
            print("%-26s confirmed-internal %s" % (key[:26], rel))
            continue
        hit, attempts = confirm(e, cache)
        state[key]["attempts"].extend(attempts)
        if hit:
            ids = [x for x in (hit.get("doi"), hit.get("arxiv")) if x]
            state[key].update({"verdict": "fixed-identifier" if ids else "confirmed-no-change",
                               "candidate": hit})
            changed += 1
            print("%-26s %-20s %s" % (key[:26], state[key]["verdict"],
                                      (hit.get("doi") or hit.get("arxiv") or hit.get("url") or "")[:60]))
        else:
            print("%-26s still-unconfirmable" % key[:26])
    save_json(STATE, state)
    save_json(CACHE, cache)
    from collections import Counter
    print("\nverdicts:", Counter(v["verdict"] for v in state.values()))
    print("changed:", changed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
