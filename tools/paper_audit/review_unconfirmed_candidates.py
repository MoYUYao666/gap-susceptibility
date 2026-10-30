# -*- coding: utf-8 -*-
"""Manual-review helper for the last unconfirmed entries: query several services and print the
candidates so a human can judge (no automatic edits)."""
import json
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(r"D:\Realdesktop\Wan\Important\New")
sys.path.insert(0, str(REPO))
from tools.paper_audit import verify_refs_online as V  # noqa: E402

UA = V.UA
CTX = ssl._create_unverified_context()
CACHE = json.loads((REPO / "docs" / "REF_RESOLUTION_CACHE.json").read_text(encoding="utf-8"))
STATE = json.loads((REPO / "docs" / "_ref_confirm_results.json").read_text(encoding="utf-8"))
ENTRIES = {e["key"]: e for e in V.collect()}
DELAY = 0.3


def get(url, timeout=25):
    if url in CACHE and CACHE[url].get("body"):
        return CACHE[url]["body"]
    try:
        with urllib.request.urlopen(urllib.request.Request(
                url, headers={"User-Agent": UA}), timeout=timeout, context=CTX) as r:
            body = r.read().decode("utf-8", "replace")
        CACHE[url] = {"fetched_at": "2026-10-25", "status": 200, "body": body}
        return body
    except Exception as exc:  # noqa: BLE001
        CACHE[url] = {"fetched_at": "2026-10-25", "error": str(exc)[:120]}
        return None


def sanitize(t):
    return re.sub(r"[^\w\s-]", " ", t).strip()


def arxiv(xml):
    out = []
    for m in re.finditer(r"<entry>(.*?)</entry>", xml, re.S):
        e = m.group(1)

        def g(tag):
            mm = re.search(r"<%s[^>]*>(.*?)</%s>" % (tag, tag), e, re.S)
            return re.sub(r"\s+", " ", mm.group(1)).strip() if mm else ""

        names = re.findall(r"<name>(.*?)</name>", e)
        out.append({"src": "arxiv", "title": g("title"), "author": names[0] if names else "",
                    "year": g("published")[:4], "ids": g("id").split("/abs/")[-1],
                    "venue": g("journal_ref")})
    return out


def oa(jsonstr):
    out = []
    try:
        res = json.loads(jsonstr).get("results") or []
    except json.JSONDecodeError:
        return out
    for it in res:
        auth = [(x.get("author") or {}).get("display_name", "") for x in (it.get("authorships") or [])]
        out.append({"src": "openalex", "title": it.get("title") or "",
                    "author": auth[0] if auth else "", "year": str(it.get("publication_year") or ""),
                    "ids": (it.get("doi") or "").replace("https://doi.org/", ""),
                    "venue": ((it.get("primary_location") or {}).get("source") or {}).get(
                        "display_name", "")})
    return out


def cr(jsonstr):
    out = []
    try:
        items = json.loads(jsonstr)["message"]["items"]
    except (json.JSONDecodeError, KeyError):
        return out
    for it in items:
        auth = [(a.get("family") or "") for a in (it.get("author") or [])]
        out.append({"src": "crossref", "title": (it.get("title") or [""])[0],
                    "author": auth[0] if auth else "",
                    "year": str((it.get("issued", {}).get("date-parts") or [[None]])[0][0]),
                    "ids": it.get("DOI", ""), "venue": (it.get("container-title") or [""])[0]})
    return out


def run(key):
    e = ENTRIES.get(key)
    if not e:
        print(key, "NO ENTRY")
        return
    title = (e.get("title") or "").strip()
    surname = V.surname(e.get("first_author") or "")
    print("\n== %s | surname=%s | year=%s | title=%s" % (key, surname, e.get("year"), title[:110]))
    words = sanitize(title).split()
    phrases = []
    if words:
        phrases = [" ".join(words), " ".join(words[:6]), " ".join(words[:8])]
        if len(words) > 6:
            phrases.append(" ".join(words[2:8]))
    cands = []
    for ph in dict.fromkeys(phrases):
        b = get("http://export.arxiv.org/api/query?max_results=6&search_query=ti:%22" +
                urllib.parse.quote(ph[:170]) + "%22")
        time.sleep(DELAY)
        if b:
            cands += arxiv(b)
    q = urllib.parse.quote(sanitize(title)[:200]) if title else ""
    if q:
        b = get("https://api.openalex.org/works?per-page=10&search=" + q)
        time.sleep(DELAY)
        if b:
            cands += oa(b)
        b = get("https://api.crossref.org/works?rows=8&query.bibliographic=" + q)
        time.sleep(DELAY)
        if b:
            cands += cr(b)
    seen = set()
    for c in cands:
        nt = V.norm(c["title"])
        if not nt or nt in seen:
            continue
        sim = V.title_similar(c["title"], title) if title else 0
        contain = bool(title) and (V.norm(title) in nt or nt in V.norm(title))
        if sim < 0.80 and not contain:
            continue
        seen.add(nt)
        print("   %-8s sim=%.2f contain=%s | %s | %s (%s) | %s | %s" % (
            c["src"], sim, contain, c["title"][:90], c["author"], c["year"], c["ids"] or "-",
            c["venue"][:40]))


for k, v in STATE.items():
    if v["verdict"] == "deleted-unconfirmable":
        run(k)
(REPO / "docs" / "REF_RESOLUTION_CACHE.json").write_text(
    json.dumps(CACHE, indent=0, ensure_ascii=False), encoding="utf-8")
print("\nDONE")
