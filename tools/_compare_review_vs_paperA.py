# -*- coding: utf-8 -*-
r"""导出 PRL 综述（Commentary）与 Paper A 的标题/摘要/关键词/节标题，用于**区别与重叠**判断。

    python tools\_compare_review_vs_paperA.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def grab_braced(t: str, cmd: str) -> str:
    """取 \\cmd{...}（支持嵌套花括号）。"""
    m = re.search(re.escape(cmd) + r"\s*\{", t)
    if not m:
        return ""
    i, d, j = m.end(), 1, m.end()
    while d and j < len(t):
        if t[j] == "{":
            d += 1
        elif t[j] == "}":
            d -= 1
        j += 1
    return re.sub(r"\s+", " ", t[i:j - 1]).strip()


def grab_env(t: str, env: str) -> str:
    m = re.search(r"\\begin\{" + env + r"\}(.*?)\\end\{" + env + r"\}", t, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def report(label: str, path: Path) -> dict:
    t = io.open(path, encoding="utf-8", errors="ignore").read()
    print("=" * 100)
    print(f"  【{label}】{path.relative_to(REPO)}")
    print("=" * 100)
    title = grab_braced(t, r"\title") or grab_braced(t, r"\begin{frontmatter}\title")
    ab = grab_env(t, "abstract")
    kw = grab_env(t, "keyword") or grab_env(t, "keywords")
    print(f"  标题  : {title[:240]}")
    print(f"  摘要  : {ab[:1000]}")
    print(f"  关键词: {kw.replace(chr(92)+'sep', ' | ')[:300]}")
    secs = re.findall(r"\\section\*?\{([^}]*)\}", t)
    print(f"  节    : {' / '.join(secs[:14])}")
    print(f"  词数  : 摘要 {len(re.sub(r'[\\][a-zA-Z]+', ' ', ab).split())} ｜ 全文约 "
          f"{len(re.sub(r'[\\][a-zA-Z]+', ' ', t).split())}")
    print()
    return {"label": label, "title": title, "abstract": ab, "kw": kw, "secs": secs,
            "words": len(re.sub(r"[\\][a-zA-Z]+", " ", t).split())}


def main() -> int:
    out = []
    c = REPO / "paper_review_prl" / "main_prl.tex"
    if c.exists():
        out.append(report("PRL 综述（Commentary, 在审 PRLETTERS-D-26-02402）", c))
    pa = REPO / "paper合" / "main_nc.tex"
    if pa.exists():
        t = io.open(pa, encoding="utf-8").read()
        print("=" * 100)
        print("  【Paper A（paper合/，候选投 CVIU/ESWA）】main_nc.tex + sections/")
        print("=" * 100)
        title = grab_braced(t, r"\title")
        ab = grab_env(t, "abstract")
        kw = grab_env(t, "keyword")
        secs = []
        for f in sorted((REPO / "paper合" / "sections").glob("*.tex")):
            s = io.open(f, encoding="utf-8").read()
            secs += [f"[{f.stem}] {x}" for x in re.findall(r"\\section\*?\{([^}]*)\}", s)]
        print(f"  标题  : {title[:240]}")
        print(f"  摘要  : {ab[:1000]}")
        print(f"  关键词: {kw.replace(chr(92)+'sep',' | ')[:300]}")
        print(f"  节    : {' / '.join(secs[:14])}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
