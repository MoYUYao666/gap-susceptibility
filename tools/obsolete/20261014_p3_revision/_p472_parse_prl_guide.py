# -*- coding: utf-8 -*-
r"""解析 PRL Guide 的篇幅规定与补充材料机制（2026-10-13）。

## 已确认（穷举检索命中）

> **Mandatory Submission Requirements 第 1 条**：
> *"The manuscript should be in double column format and should not exceed **7 pages**.
> The 7 pages limit includes all materials e.g. narrative, figures, tables, references, etc."*
>
> 第 4 条：Authorship Confirmation 必须上传，**否则 AUTOMATIC REJECTION**

**⇒ 我们当前 14 页（IEEEtran 单栏）远超此限。**

## 本脚本要查

1. Guide 里**所有**提到页数/篇幅的地方（确认没有别的条款或例外）
2. **Supplementary material** 机制（能否把扩充内容移出正文）
3. 是否规定了**格式类**（`elsarticle`？双栏？）

    python tools\_p472_parse_prl_guide.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
G = REPO / "docs" / "guides" / "_prl_guide.txt"
OUT = REPO / "outputs" / "analysis" / "prl_guide_rules.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(G, encoding="utf-8", errors="replace").read()
    low = t.lower()
    rep = {}

    print("=" * 100)
    print("① 所有涉及篇幅/页数的句子（穷举）")
    print("=" * 100)
    seen = set()
    for pat in (r"7[ \-]?pages?", r"\bpages?\b", r"page limit", r"length", r"word"):
        for m in re.finditer(pat, low):
            key = m.start() // 120
            if key in seen:
                continue
            seen.add(key)
            seg = " ".join(t[max(0, m.start() - 170):m.start() + 200].split())
            if any(k in seg.lower() for k in ("page", "length", "word")):
                print(f"  …{seg[:360]}…")
                print()
    print(f"  （去重后候选段 {len(seen)} 个）")

    print("=" * 100)
    print("② Supplementary material 机制")
    print("=" * 100)
    idx = [m.start() for m in re.finditer(r"supplementary", low)]
    print(f"  出现 {len(idx)} 次")
    shown = 0
    for i in idx:
        seg = " ".join(t[max(0, i - 120):i + 380].split())
        if "supplementary" in seg.lower() and shown < 4:
            print(f"  …{seg[:430]}…")
            print()
            shown += 1

    print("=" * 100)
    print("③ 格式要求（模板 / 双栏 / elsarticle）")
    print("=" * 100)
    for pat in (r"double column", r"double-column", r"elsarticle", r"LaTeX", r"template"):
        ms = list(re.finditer(pat, low))
        if ms:
            print(f"  【{pat}】{len(ms)} 处")
            for m in ms[:2]:
                print(f"      …{' '.join(t[max(0,m.start()-140):m.start()+200].split())[:320]}…")
            print()
    rep["supplementary_mentions"] = len(idx)
    rep["has_7page_rule"] = "should not exceed 7 pages" in low

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
