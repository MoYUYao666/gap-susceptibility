# -*- coding: utf-8 -*-
r"""生成 APA 第 7 版文献表并改写 A1（2026-10-10）。

## 范围（**只动参考文献机制**）

1. 加载 `\usepackage[authoryear,round]{natbib}`
2. 把 56 条 `\bibitem{key}` 改写为 `\bibitem[Author, Year]{key}`（natbib 作者-年标签）
   + APA 正文（作者. (年). 标题. venue）
3. **按字母序**排列
4. 正文 `\cite{` → `\citep{`

## 不动的

- 标题、摘要、正文文字、图、表、任何数字
- **venue 串逐字取自原 bibitem**（不重写，避免引入未核实信息）

    python tools\_p122_gen_apa.py [--apply]
"""
from __future__ import annotations

import json

import argparse
import io
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "paper_a1"
FIXED = REPO / "outputs" / "analysis" / "a1_apa_fixed.json"
MAIN = A1 / "main.tex"


def initials(given: str) -> str:
    given = (given or "").replace("-", " ").strip()
    out = []
    for w in given.split():
        if w:
            out.append(w[0].upper() + ".")
    return " ".join(out)


def fmt_authors(au: list) -> str:
    """APA 7：Family, F. M., Family2, F. M., & Family3, F. M."""
    items = []
    for x in au:
        fam = (x.get("family") or "").strip()
        ini = initials(x.get("given", ""))
        if not fam:
            continue
        items.append(f"{fam}, {ini}" if ini else fam)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) <= 20:
        return ", ".join(items[:-1]) + ", & " + items[-1]
    # >20 位：前 19 … 末位（APA 规则）
    return ", ".join(items[:19]) + ", ... " + items[-1]


def sort_key(r: dict) -> str:
    au = r.get("authors") or []
    fam = au[0]["family"] if au else r.get("bibitem_families", ["zzz"])[0]
    s = unicodedata.normalize("NFKD", fam)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return f"{s}|{r.get('year') or '0'}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    rows = json.loads(io.open(FIXED, encoding="utf-8").read())
    rows.sort(key=sort_key)
    print(f"=== 生成 APA（{len(rows)} 条，字母序）===")

    entries, labels = [], {}
    for r in rows:
        au = r.get("authors") or []
        year = r.get("year") or "n.d."
        auth = fmt_authors(au)
        title = r["title"].replace("``", "").replace("''", "").strip()
        if not title.endswith("?"):
            title = title.rstrip(".") + "."
        venue = r["rest"]
        # 去掉 venue 里重复的 DOI 前缀写法
        venue = re.sub(r"^[,;\s]+", "", venue)
        if auth:
            body = f"{auth} ({year}). {title} {venue}"
            label = f"{au[0]['family']}, {year}"
        else:
            body = f"[{title} {venue}]  % ⚠️ 作者未能查证，见 ENVIRONMENT 备注"
            label = f"[?], {year}"
        entries.append(f"\\bibitem[{label}]{{{r['key']}}} {body}")
        labels[r["key"]] = label

    print("\n=== 前 5 条预览 ===")
    for e in entries[:5]:
        print("  " + " ".join(e.split())[:190])

    if not a.apply:
        print("\n  （预演；加 --apply 写入）")
        return 0

    t = io.open(MAIN, encoding="utf-8", errors="replace").read()

    # ① 加载 natbib
    if "natbib" not in t:
        m = re.search(r"(\\usepackage(\[[^\]]*\])?\{hyperref\})", t)
        assert m, "未找到 hyperref 以插入 natbib"
        t = t[:m.start()] + "\\usepackage[authoryear,round]{natbib}\n" + t[m.start():]

    # ② 替换书目块
    i = t.find("\\begin{thebibliography}")
    j = t.find("\\end{thebibliography}")
    assert i > 0 and j > i, "未找到 thebibliography"
    head = t[:i]
    tail = t[j:]
    opening = "\\begin{thebibliography}{99}\n\\footnotesize\n"
    newblock = opening + "\n".join(entries) + "\n"
    t = head + newblock + tail

    # ③ 正文引用 → \citep
    n_cite = 0
    def repl(m):
        nonlocal n_cite
        n_cite += 1
        return "\\citep{" + m.group(1) + "}"
    # 只改 \cite{...}（不碰已存在的 \citep/\citet）
    t = re.sub(r"\\cite\{([^}]*)\}", repl, t)

    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print(f"\n  ✅ 已写 {MAIN.relative_to(REPO)}")
    print(f"     加载 natbib ｜ 替换 {len(entries)} 条文献 ｜ 改 {n_cite} 处 \\cite→\\citep")

    out = REPO / "outputs" / "analysis" / "a1_apa_labels.json"
    io.open(out, "w", encoding="utf-8", newline="").write(
        __import__("json").dumps(labels, ensure_ascii=False, indent=1))
    print(f"  ✅ 标签表 {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
