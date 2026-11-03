# -*- coding: utf-8 -*-
r"""提取正文中的**量级与比较类主张**，供逐条核对（投稿前审核的实质面）。

## 为什么要机械提取

措辞类问题（过度声称、循环引用、主张宽于证据）**不能靠通读发现**——本会话就漏过多次
（"across architectures"、"k=0.043"、"carry across backbones" 都是事后扫描或他人提问才暴露）。
故先把**所有含量级/比较词**的句子抽出来，再逐条判定。

## 提取目标

- 量级词：`overwhelmingly` / `substantially` / `consistently` / `always` / `never` / `uniquely`
- 比较词：`more than` / `better` / `stronger` / `larger` / `smaller`
- 范围词：`across` / `all` / `every` / `universal` / `irrespective`
- 统计词：`significant` / `robust` / `confirm`

    python tools\_extract_claims.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SEC = REPO / "paper合" / "sections"

PATTERNS = {
    "量级": r"\b(overwhelmingly|substantially|consistently|always|never|uniquely|dramatically|catastrophically)\b",
    "比较": r"\b(more than|better than|stronger|weaker|larger|smaller|outperform\w*|exceeds?)\b",
    "范围": r"\b(across (?:all|every|architectures|datasets)|universal\w*|irrespective|regardless of)\b",
    "统计": r"\b(significant\w*|robust\w*|confirm\w*|establis\w*|validat\w*)\b",
}


def sentences(text: str) -> list[tuple[str, str]]:
    """返回 (文件, 句子)。先按句号/分号切，再去掉 LaTeX 命令。"""
    out = []
    for f in sorted(SEC.glob("*.tex")):
        raw = io.open(f, encoding="utf-8", errors="ignore").read()
        # 去掉注释行与数学公式，避免噪声
        raw = re.sub(r"%.*", "", raw)
        raw = re.sub(r"\$[^$]*\$", " MATH ", raw)
        for s in re.split(r"(?<=[.;])\s+", raw):
            s2 = re.sub(r"\s+", " ", s).strip()
            if 40 < len(s2) < 600:
                out.append((f.name, s2))
    return out


def main() -> int:
    apply = "--apply" in sys.argv
    ss = sentences("")
    hits: dict[str, list[tuple[str, str]]] = {k: [] for k in PATTERNS}
    for fn, s in ss:
        for cat, pat in PATTERNS.items():
            if re.search(pat, s, re.I):
                hits[cat].append((fn, s))

    lines = ["# Paper A 主张提取（投稿前审核用）\n",
             f"> 生成：`tools/_extract_claims.py` ｜ 句子总数 {len(ss)}\n"]
    total = 0
    for cat in PATTERNS:
        lines.append(f"\n## {cat}（{len(hits[cat])} 句）\n")
        for fn, s in hits[cat]:
            total += 1
            lines.append(f"- **[{fn}]** {s}")
    text = "\n".join(lines) + "\n"
    print(f"  句子总数 {len(ss)} ｜ 命中 {total} 条")
    for cat in PATTERNS:
        print(f"    {cat}: {len(hits[cat])} 句")
    if apply:
        out = REPO / "docs" / "PAPERA_CLAIMS_EXTRACT.md"
        io.open(out, "w", encoding="utf-8", newline="").write(text)
        print(f"  ✅ 已写出 {out.relative_to(REPO)}")
    else:
        print("  （预演，加 --apply 写出）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
