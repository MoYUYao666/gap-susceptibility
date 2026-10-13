# -*- coding: utf-8 -*-
r"""多源引用核验：确认参考文献真实存在，且元数据与原文一致。

为什么必须程序化：凭记忆写条目会产生**检索不到、作者年份错、预印本冒充正式版**的引用。

数据源（按可靠性排序，逐个尝试）：
  1. **Crossref**（DOI 精确命中）—— 有 DOI 时首选；权威、含刊名
  2. **Crossref**（题名检索）—— 覆盖期刊与部分会议
  3. **arXiv API** —— 覆盖 ML 预印本与大部分会议论文（ICLR/ICML/NeurIPS 常无 Crossref DOI）
  4. **OpenReview API** —— ICLR/NeurIPS 等会议论文的正式记录

踩坑记录（改代码时别踩回去）：
  - arXiv 的 `search_query` 值必须用 `quote`（**不能** `quote_plus`），否则返回 HTTP 406 Not Acceptable；
  - `api2.openreview.net` **不能带自定义 User-Agent**（带了返回 400），必须用空头。

判定（三级，从严）：
  PASS   标题强吻合（≥TITLE_STRONG）且 年份/首作者/DOI 至少一项吻合
  WEAK   标题中等吻合（≥TITLE_MIN_RATIO），或强吻合但年份与作者都对不上 → **需人工确认，不放行**
  FAIL   标题低相似或四源皆无结果 → **疑似编造，禁止入表**

用法：
    python tools/_verify_citations.py [refs.json]     # 默认 paper_review/refs_all.json
输出：
    paper_review/refs_verified.json、paper_review/citation_report.md
"""
from __future__ import annotations

import difflib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CROSSREF_UA = "citation-verify/1.0 (mailto:contact@example.com)"
ARXIV_UA = "Mozilla/5.0 (compatible; citation-verify/1.0)"
HTML_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
TITLE_MIN_RATIO = 0.82   # 低于此 → FAIL
TITLE_STRONG = 0.90      # 高于此 + 年份或作者吻合 → PASS


# ---------------------------------------------------------------- 工具
def norm_title(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s or "")
    s = re.sub(r"[^a-z0-9\u4e00-\u9fff ]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, norm_title(a), norm_title(b)).ratio()


def http_get(url: str, ua, tries: int = 3) -> str | None:
    """ua 可为字符串（User-Agent 头）、dict（完整头）或 None（不带自定义头）。"""
    for i in range(tries):
        try:
            if isinstance(ua, dict):
                headers = dict(ua)
            elif ua:
                headers = {"User-Agent": ua}
            else:
                headers = {}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception:
            if i == tries - 1:
                return None
            time.sleep(1.2 * (i + 1))
    return None


# ---------------------------------------------------------------- 数据源
def crossref_by_doi(doi: str) -> dict | None:
    raw = http_get(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}", CROSSREF_UA)
    if not raw:
        return None
    try:
        d = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return d.get("message") if d.get("status") == "ok" else None


def crossref_by_title(title: str, rows: int = 8) -> list[dict]:
    q = urllib.parse.quote(title)
    raw = http_get(f"https://api.crossref.org/works?query.bibliographic={q}&rows={rows}", CROSSREF_UA)
    if not raw:
        return []
    try:
        return json.loads(raw)["message"].get("items", [])
    except Exception:
        return []


def arxiv_html_by_id(aid: str) -> dict | None:
    """通过 arXiv **abs 页面**（HTML 通道）核对 id → 标题/首作者/日期。

    为什么不用 arXiv API：本网络环境下 API 被限流，间歇性返回 HTTP 406
    （实测 `all:electron` 能过、`all:LoRA` 却 406，与大小写无关，属限流）。
    HTML 页面自带 citation_title / citation_author / citation_date 元标签，稳定可用。

    ⚠️ **必须校验 citation_arxiv_id 与请求 id 一致**：对尾数为 0 的 id（如 2304.15010），
    页面元标签解析可能**静默截掉尾零**、返回另一篇论文——不校验就会"核到错论文却判 PASS"。
    """
    aid = aid.strip().replace("arXiv:", "").replace("arxiv:", "")
    raw = http_get(f"https://arxiv.org/abs/{aid}", HTML_UA)
    if not raw or "citation_title" not in raw:
        return None

    # id 一致性守卫
    got_id = ""
    m_id = re.search(r'<meta name="citation_arxiv_id" content="(.*?)"', raw)
    if m_id:
        got_id = m_id.group(1).strip()
    if got_id:
        # 去掉版本号后比较
        norm = lambda s: re.sub(r"v\d+$", "", s.strip())
        if norm(got_id) != norm(aid):
            return None

    ti = re.search(r'<meta name="citation_title" content="(.*?)"', raw)
    au = re.search(r'<meta name="citation_author" content="(.*?)"', raw)
    dt = re.search(r'<meta name="citation_date" content="(\d{4})', raw)
    if not ti:
        return None
    return {
        "title": ti.group(1).strip(),
        "year": int(dt.group(1)) if dt else None,
        "doi": aid,
        "venue": "arXiv",
        "first_author": (au.group(1).split(",")[0].strip() if au else ""),
        "source": "arXiv-html",
    }


def arxiv_by_title(title: str, max_results: int = 10) -> list[dict]:
    """arXiv API 检索（可能被限流返回空）；调用方应容忍空结果。"""
    url = ("https://export.arxiv.org/api/query?search_query=all:"
           f"{urllib.parse.quote(title)}&max_results={max_results}")
    raw = http_get(url, ARXIV_UA)
    if not raw:
        return []
    out = []
    for e in re.findall(r"<entry>(.*?)</entry>", raw, re.S):
        t = re.search(r"<title>(.*?)</title>", e, re.S)
        p = re.search(r"<published>(\d{4})", e)
        i = re.search(r"<id>(.*?)</id>", e, re.S)
        names = re.findall(r"<name>(.*?)</name>", e)
        out.append({
            "title": " ".join(t.group(1).split()) if t else "",
            "year": int(p.group(1)) if p else None,
            "doi": (i.group(1).split("/abs/")[-1] if i else ""),
            "venue": "arXiv",
            "first_author": names[0] if names else "",
            "source": "arXiv-api",
        })
    return out


def openreview_by_title(title: str, limit: int = 10) -> list[dict]:
    """OpenReview：`notes/search?term=` 可用；**不要带自定义 UA**，也不要走 `content.title=` 过滤（403）。"""
    url = ("https://api2.openreview.net/notes/search?term="
           f"{urllib.parse.quote(title)}&limit={limit}")
    raw = http_get(url, None)
    if not raw:
        return []
    try:
        notes = json.loads(raw).get("notes", [])
    except Exception:
        return []
    out = []
    for n in notes:
        c = n.get("content", {}) or {}

        def val(k):
            v = c.get(k)
            return v.get("value") if isinstance(v, dict) else v

        t = val("title")
        if not t:
            continue
        authors = val("authors") or []
        ts = n.get("pdate") or n.get("cdate") or n.get("tcdate")
        out.append({
            "title": str(t),
            "year": int(time.gmtime(ts / 1000).tm_year) if ts else None,
            "doi": "",
            "venue": str(val("venue") or "OpenReview"),
            "first_author": str(authors[0]) if authors else "",
            "source": "OpenReview",
        })
    return out


# ---------------------------------------------------------------- 归一化
def cr_norm(msg: dict) -> dict:
    def year() -> int | None:
        for k in ("published-print", "published-online", "issued", "created"):
            dp = (msg.get(k) or {}).get("date-parts") or []
            if dp and dp[0] and dp[0][0]:
                return int(dp[0][0])
        return None

    ct = msg.get("container-title") or []
    fam = ""
    for a in msg.get("author", []) or []:
        if a.get("family"):
            fam = a["family"]
            break
    return {
        "title": (msg.get("title") or [""])[0],
        "year": year(),
        "doi": msg.get("DOI", ""),
        "venue": ct[0] if ct else (msg.get("publisher") or ""),
        "first_author": fam,
        "source": "Crossref",
    }


# ---------------------------------------------------------------- 核验单条
def verify_one(entry: dict) -> dict:
    key = entry.get("key", "?")
    title = entry.get("title", "")
    wants_doi = (entry.get("doi") or "").strip()
    want_year = entry.get("year")
    authors = entry.get("authors") or []
    want_surname = str(authors[0]).split()[-1] if authors else ""

    out = dict(entry, verified=False, status="", source="", found_title="", found_doi="",
               found_year=None, found_venue="", title_ratio=0.0, notes=[])

    cand: dict | None = None
    tried: list[str] = []

    def accept(c: dict | None) -> dict | None:
        """候选必须达到最低标题相似度才接受，否则丢弃并继续尝试下一通道。

        修复的 bug：早期版本对"有 arXiv id"的条目直接采信 abs 页面返回的内容，
        不检查它与条目标题是否吻合——若 arxiv_id 本身写错，会拿到**另一篇论文**，
        且不再回退到 DOI 通道，导致真引用被误判 FAIL。
        """
        if not c:
            return None
        if ratio(title, c["title"]) < TITLE_MIN_RATIO:
            tried.append(f"{c['source']} 命中『{c['title'][:52]}』但标题不吻合 → 丢弃")
            return None
        return c

    # 0) arXiv id → abs 页面（最稳，但必须校验吻合）
    aid = entry.get("arxiv_id") or ""
    if not aid and wants_doi and "arxiv" in wants_doi.lower():
        aid = wants_doi.split("/")[-1]
        aid = re.sub(r"(?i)^arxiv[.:]", "", aid)
        aid = re.sub(r"v\d+$", "", aid)
    if aid:
        cand = accept(arxiv_html_by_id(aid))
    # 1) Crossref DOI（权威；有 DOI 时必须走）
    if cand is None and wants_doi and "arxiv" not in wants_doi.lower():
        m = crossref_by_doi(wants_doi)
        if m:
            cand = accept(cr_norm(m))
        else:
            tried.append(f"Crossref 无此 DOI（{wants_doi}）")
    # 2) Crossref 题名
    if cand is None:
        items = crossref_by_title(title)
        if items:
            best = max(items, key=lambda m: ratio(title, (m.get("title") or [""])[0]))
            cand = accept(cr_norm(best))
    # 3) arXiv API 检索（可能被限流）
    if cand is None:
        items = arxiv_by_title(title)
        if items:
            best = max(items, key=lambda m: ratio(title, m["title"]))
            cand = accept(best)
    # 4) OpenReview
    if cand is None:
        items = openreview_by_title(title)
        if items:
            best = max(items, key=lambda m: ratio(title, m["title"]))
            cand = accept(best)

    # 🔴 DOI 冲突检查（必须早于任何 return——无候选时恰恰最需要查"这个 DOI 到底指向哪篇"）
    doi_conflict = ""
    doi_msg: dict | None = None
    if wants_doi and "arxiv" not in wants_doi.lower():
        doi_msg = crossref_by_doi(wants_doi)
        if doi_msg:
            other = cr_norm(doi_msg)
            via_doi = (cand is not None and cand["source"] == "Crossref"
                       and (cand["doi"] or "").lower() == wants_doi.lower())
            if not via_doi and ratio(title, other["title"]) < TITLE_MIN_RATIO:
                doi_conflict = (f"🔴 DOI 冲突：`{wants_doi}` 在 Crossref 上指向"
                                f"『{other['title'][:70]}』（{other['year']}），与条目标题不符 → "
                                "DOI 写错，必须改正或删除该条目")

    if cand is None:
        out["status"] = "FAIL"
        out["notes"].extend(tried[:4])
        if doi_conflict:
            out["notes"].append(doi_conflict)
        out["notes"].append("Crossref（DOI/题名）+ arXiv + OpenReview 均无足够吻合的结果 → 疑似条目不存在或元数据有误")
        return out

    out.update(source=cand["source"], found_title=cand["title"], found_doi=cand["doi"],
               found_year=cand["year"], found_venue=cand["venue"])
    r = out["title_ratio"] = round(ratio(title, cand["title"]), 3)

    year_ok = (not want_year) or (not cand["year"]) or abs(int(want_year) - int(cand["year"])) <= 1
    got = (cand["first_author"] or "").split()[-1].lower()
    author_ok = (not want_surname) or (not got) or (want_surname.lower() == got)
    doi_exact = bool(wants_doi) and wants_doi.lower() == (cand["doi"] or "").lower()

    if r >= TITLE_STRONG and (year_ok or author_ok or doi_exact):
        out["status"] = "PASS"
        out["verified"] = True
        if doi_conflict:
            out["notes"].append(doi_conflict)
        if cand["source"] == "arXiv-html" and entry.get("venue") not in (None, "", "arXiv"):
            out["notes"].append(f"⚠️ arXiv abs 页面核到（稿件标注 venue=『{entry.get('venue')}』）→ "
                                "需确认正式发表版本，arXiv 预印本不得冒充正式版")
        elif cand["source"] in ("arXiv-api",) and entry.get("venue") not in (None, "", "arXiv"):
            out["notes"].append(f"⚠️ 仅在 arXiv 核到（稿件标注 venue=『{entry.get('venue')}』）→ 需确认正式版")
    elif r >= TITLE_MIN_RATIO:
        out["status"] = "WEAK"
        if not year_ok:
            out["notes"].append(f"年份存疑：稿件 {want_year} vs {cand['source']} {cand['year']}")
        if not author_ok:
            out["notes"].append(f"首作者存疑：稿件 {want_surname} vs {cand['source']} {cand['first_author']}")
        if doi_conflict:
            out["notes"].append(doi_conflict)
        out["notes"].append("标题中等吻合 → 需人工确认")
    else:
        out["status"] = "FAIL"
        out["notes"].append(f"标题相似度 {r} < {TITLE_MIN_RATIO}；{cand['source']} 最近=『{cand['title'][:80]}』")
        if doi_conflict:
            out["notes"].append(doi_conflict)
    return out


# ---------------------------------------------------------------- 主流程
def main() -> int:
    src = (Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "paper_review" / "refs_all.json").resolve()
    if not src.exists():
        print(f"找不到 {src}（先准备文献候选 JSON）")
        return 1
    entries = json.loads(src.read_text(encoding="utf-8"))
    if isinstance(entries, dict):
        entries = entries.get("references", [])

    try:
        label = src.relative_to(REPO)
    except ValueError:
        label = src.name
    print(f"核验 {len(entries)} 条（源：{label}）\n")

    results = []
    for e in entries:
        r = verify_one(e)
        flag = {"PASS": "✅", "FAIL": "❌", "WEAK": "⚠️"}[r["status"]]
        print(f"  {flag} {r['key']:<24} {r['status']:<5} src={r['source'] or '—':<10} ratio={r['title_ratio']:.2f}")
        for nt in r["notes"]:
            print(f"        - {nt}")
        results.append(r)

    n = {s: sum(1 for r in results if r["status"] == s) for s in ("PASS", "WEAK", "FAIL")}
    print(f"\n合计 {len(results)}：PASS {n['PASS']} ／ WEAK {n['WEAK']}（需人工核） ／ FAIL {n['FAIL']}（疑似编造）")

    out_dir = REPO / "paper_review"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "refs_verified.json").write_text(json.dumps(results, ensure_ascii=False, indent=2),
                                                encoding="utf-8")
    lines = ["# 引用核验报告", "",
             f"源：`{src.name}` ｜ 合计 **{len(results)}** ｜ "
             f"PASS **{n['PASS']}** ／ WEAK **{n['WEAK']}** ／ FAIL **{n['FAIL']}**", "",
             "| 状态 | key | 稿件标题 | 核到来源 | DOI/arXiv id | 相似度 | 备注 |",
             "|---|---|---|---|---|---|---|"]
    for r in results:
        flag = {"PASS": "✅", "FAIL": "❌", "WEAK": "⚠️"}[r["status"]]
        lines.append(f"| {flag} | `{r['key']}` | {r['title'][:58]} | {r['source'] or '—'} | "
                     f"{r['found_doi'] or '—'} | {r['title_ratio']:.2f} | {'；'.join(r['notes'])[:130] or '—'} |")
    lines += ["", "## 判定规则", "",
              f"- **PASS**：标题相似度 ≥{TITLE_STRONG} 且 年份/首作者/DOI 至少一项吻合",
              f"- **WEAK**：标题相似度 ≥{TITLE_MIN_RATIO} 但需人工确认（**不放行**）",
              f"- **FAIL**：标题相似度 <{TITLE_MIN_RATIO} 或四源皆无结果（**禁止入表**）",
              "", "> 数据源：Crossref（DOI→题名）→ arXiv → OpenReview。",
              "> arXiv 命中的条目若稿件标注了会议/期刊 venue，会附警告——**预印本不得冒充正式版**。"]
    (out_dir / "citation_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"写出 {out_dir.name}/refs_verified.json 与 citation_report.md")
    return 1 if (n["FAIL"] or n["WEAK"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
