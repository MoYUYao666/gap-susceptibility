# -*- coding: utf-8 -*-
r"""第三轮：在**不增加行数**的前提下提高证据密度。

做法：把新 key 挂到已有的引用点上（同一括号内追加），并移除一条已过时的 arXiv-only 版本记录
（`gao2022clipadapter`，已被其 IJCV 正式版 `gao2024clipadapter` 取代）——净增引用数而不增篇幅。

    python tools/_add_refs_free.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MD = REPO / "paper_review_prl" / "MANUSCRIPT.md"

EDITS: list[tuple[str, str]] = [
    # 视觉适配：补 CLIP-Adapter 的正式版（特征适配器的代表）
    ("[chen2022adaptformer; jie2022convpass; he2023safe]",
     "[chen2022adaptformer; jie2022convpass; he2023safe; gao2024clipadapter]"),
    # 低秩注入：补 LoRA+ / rsLoRA（秩缩放的实现细节，属"预算组成"）
    ("[dettmers2023qlora; jiang2024mora]",
     "[dettmers2023qlora; jiang2024mora; hayou2024loraphus; kalajdzievski2023rslora]"),
    # 方法学批评：补 HElm（评测报告的清单化先例）
    ("[song2025bothleaked;",
     "[song2025bothleaked; liang2023helm;"),
    # 视觉适配少样本：补 CLIP 少样本适配的系统分析
    ("[zhang2023adalora; wang2024loraga; silvarodriguez2024closerlook]",
     "[zhang2023adalora; wang2024loraga; silvarodriguez2024closerlook; zanella2024cliplora]"),
]

# 移除被正式版取代的 arXiv-only 记录（同一工作的重复入口）
DROP = ["gao2022clipadapter"]


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(MD, encoding="utf-8").read()
    n = 0
    for old, new in EDITS:
        if old in t:
            t = t.replace(old, new, 1); n += 1
        else:
            print(f"  ⚠ 未命中: {old[:52]}…")
    d = 0
    for k in DROP:
        pat = re.compile(r"\[([^\]\[]*?)\b" + re.escape(k) + r"\b([^\]\[]*?)\]")
        def fix(m):
            inner = re.sub(r"[;,]\s*" + re.escape(k) + r"\b|\b" + re.escape(k) + r"\b[;,]\s*", "", m.group(1) + m.group(2))
            inner = inner.strip(";, ")
            return f"[{inner}]" if inner else ""
        t, c = pat.subn(fix, t)
        d += c

    keys = set()
    for m in re.finditer(r"\[([^\]\[]+)\]", t):
        if "://" in m.group(1):
            continue
        for part in re.split(r"[;,]", m.group(1)):
            kk = part.strip()
            if re.match(r"^[a-z][a-z0-9_]*\d[a-z0-9_]*$", kk):
                keys.add(kk)
    print(f"\n追加 {n}/{len(EDITS)} 处 ｜ 移除 {d} 处 ｜ 唯一 key {len(keys)} 条")
    if apply:
        io.open(MD, "w", encoding="utf-8", newline="").write(t)
        print("已写入")
    else:
        print("（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
