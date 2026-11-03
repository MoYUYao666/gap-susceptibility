# -*- coding: utf-8 -*-
r"""稿件自查：找出可改进的具体位置（重复、冗长句、密度失衡、清单措辞、自称不一致等）。

不是风格主观评价，而是可核的机械检查，输出"哪里值得改"的清单。

    python tools/_manuscript_diagnostics.py
"""
from __future__ import annotations

import io
import re
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MD = REPO / "paper_review_prl" / "MANUSCRIPT.md"


def main() -> int:
    t = io.open(MD, encoding="utf-8").read()
    body = t.split("## 1. Introduction", 1)[-1]

    print("=" * 78)
    print("1) 超长句（>45 词）——审稿人最常抱怨的可读性问题")
    print("=" * 78)
    sents = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", body))
    for s in sorted(sents, key=lambda x: -len(x.split()))[:6]:
        n = len(s.split())
        if n > 45:
            print(f"  [{n} 词] {s[:150]}…")

    print()
    print("=" * 78)
    print("2) 高频词（可能是无意识重复，也可能是必要的术语）")
    print("=" * 78)
    words = Counter(w.lower() for w in re.findall(r"\b[a-zA-Z]{6,}\b", body))
    for w, c in words.most_common(12):
        flag = "⚠️ 偏多" if c > 12 else ""
        print(f"  {w:<22} {c:>3}  {flag}")

    print()
    print("=" * 78)
    print("3) 各节引用密度（引用应集中在方法/证据节，而非前言堆砌）")
    print("=" * 78)
    for sec in re.split(r"\n(?=### |## )", body):
        head = sec.split("\n", 1)[0].replace("## ", "").replace("### ", "")[:46]
        nk = len(re.findall(r"\[[a-z][a-z0-9_]*\d", sec))
        nw = len([w for w in re.split(r"\s+", sec) if re.search(r"[A-Za-z]", w)])
        if nw > 80:
            dens = nk / (nw / 1000) if nw else 0
            print(f"  {head:<48} {nk:>3} 引用 / {nw:>4} 词 = {dens:>5.1f} 引用/千词")

    print()
    print("=" * 78)
    print("4) 清单措辞（每条是否可勾选：动词开头 + 可判定）")
    print("=" * 78)
    m = re.search(r"## 4\..*?(?=## 5\.)", body, re.S)
    if m:
        items = re.findall(r"^\s*(\d+)\.\s+(.+?)$", m.group(0), re.M)
        weak = []
        for num, txt in items:
            txt = re.sub(r"\s+", " ", txt).strip()
            first = txt.split()[0].lower().rstrip(".,")
            ok = first in {"the", "whether", "if", "how", "which", "where", "a", "an"}
            print(f"  {num:>2}. {txt[:88]}{'' if ok else '   ⚠️'}")
            if not ok:
                weak.append(num)
        print(f"\n  以名词短语开头（需人工确认是否可判定）: {weak if weak else '无'}")

    print()
    print("=" * 78)
    print("5) 自称一致性（'we' vs 'I'；单作者稿件应统一）")
    print("=" * 78)
    for p in ("\\bwe\\b", "\\bWe\\b", "\\bI\\b(?!\\s*\\w)", "\\bour\\b", "\\bmy\\b"):
        print(f"  {p:<14} {len(re.findall(p, body)):>3} 次")

    print()
    print("=" * 78)
    print("6) 是否有未定义的术语（首次出现处应给出定义）")
    print("=" * 78)
    for term in ["PEFT", "LoRA", "VLM", "adapter rank", "capacity budget"]:
        first = body.find(term)
        if first >= 0:
            ctx = re.sub(r"\s+", " ", body[max(0, first - 60):first + 60]).strip()
            print(f"  {term:<16} 首现: …{ctx}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
