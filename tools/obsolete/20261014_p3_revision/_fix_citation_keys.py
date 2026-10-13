# -*- coding: utf-8 -*-
r"""统一正文里的引用 key：把"悬空 key"替换为参考文献表中实际存在的 key。

背景：三个工作流各自命名，同一篇文献出现多种拼写（hu2022lora / hu2021lora、
kopiczko2023vera / kopiczko2024vera 等）。合并去重后只保留一个，另一种拼写就成了悬空引用。

本脚本：
  1. 按 FIX_MAP 精确替换 `[bad]` 形式（只替换**方括号引用**，不碰普通文本）；
  2. 校验替换后 bad key 不再出现在正文、且 good key 确实在表中；
  3. 输出替换计数。

    python tools/_fix_citation_keys.py            # 预演（不改文件）
    python tools/_fix_citation_keys.py --apply    # 实际写入
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DIR = REPO / "paper_review"
SECTIONS = sorted((DIR / "sections").glob("*.md"))

FIX_MAP = {
    # 悬空 key → 表中实际存在的 key
    "hu2022lora": "hu2021lora",
    "hu2023lorahub": "huang2024lorahub",
    "huang2023lorahub": "huang2024lorahub",
    "kopiczko2023vera": "kopiczko2024vera",
    "liu2022tfew": "liu2022ia3",
    "he2021unifiedview": "he2022unifiedview",
    "biderman2024forgetless": "biderman2024loraless",
    "kumar2022lptft": "kumar2022lpft",
    "xin2026peftvisionbenchmark": "xin2024vpeftsurvey",
}


def replace_keys(text: str, mapping: dict[str, str]) -> tuple[str, dict[str, int]]:
    """替换方括号引用里的 key，**支持多 key 括号**（`[@a; @b, c]`）。

    早期版本只匹配"括号内单个 key"（`\\[(\\s*@?\\s*)bad(\\s*)\\]`），因此漏掉了
    `[@wang2023multilora; @huang2023lorahub; @zhang2023composing]` 这类写法。
    正确做法：取每个方括号的**内容**，按 `;` 或 `,` 切分后逐项替换。
    """
    counts: dict[str, int] = {}

    def one_bracket(m: re.Match) -> str:
        inner = m.group(1)
        parts = re.split(r"([;,])", inner)          # 保留分隔符
        for i, part in enumerate(parts):
            raw = part.strip()
            key = raw.lstrip("@").strip()
            if key in mapping:
                good = mapping[key]
                # 保留原有的 @ 前缀与两侧空白风格
                parts[i] = part.replace(raw, ("@" if raw.startswith("@") else "") + good)
                counts[key] = counts.get(key, 0) + 1
        return "[" + "".join(parts) + "]"

    text = re.sub(r"\[([^\[\]]+)\]", one_bracket, text)
    return text, counts


def main() -> int:
    apply = "--apply" in sys.argv
    refs = json.loads((DIR / "refs_all.json").read_text(encoding="utf-8"))
    known = {(e.get("key") or "").strip() for e in refs}

    missing_target = {b: g for b, g in FIX_MAP.items() if g not in known}
    if missing_target:
        print(f"❌ FIX_MAP 中目标 key 不在表里，先修数据：{missing_target}")
        return 1

    total = 0
    for p in SECTIONS:
        text = p.read_text(encoding="utf-8")
        text2, counts = replace_keys(text, FIX_MAP)
        if counts:
            total += sum(counts.values())
            print(f"  {p.name}: " + ", ".join(f"{b}→{FIX_MAP[b]} ×{n}" for b, n in counts.items()))
            if apply:
                p.write_text(text2, encoding="utf-8", newline="")

    print(f"\n合计替换 {total} 处" + ("（已写入）" if apply else "（预演，未写入；加 --apply 生效）"))

    if apply:
        left = []
        for p in SECTIONS:
            t = p.read_text(encoding="utf-8")
            for bad in FIX_MAP:
                if re.search(r"\[[^\]]*\b" + re.escape(bad) + r"\b[^\]]*\]", t):
                    left.append((p.name, bad))
        print("复检残留：", left if left else "✅ 无残留")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
