# -*- coding: utf-8 -*-
r"""Paper A 整改 · 第 1 项（重写版）：实验计数 116 → 117（精确串替换）。

## 为什么重写

第一版用宽正则 `\(116\b`，会把 `...116,608)` 这类**参数数字**也匹配进来（那是 n_trainable_params，
不是实验计数）。虽然逐处打印后发现 Paper A 当前文本里 6 处都是计数语境，但**宽正则的风险仍在**。
本版改为**逐一列出精确原文串**，命中即替换，未命中即报错——宁可不改，也不错改。

## 三处独立证据支持 117（均实测）

1. `supplement.tex` 目录表 **13 节逐节加总 = 117**；
2. 同表 `\textbf{Total}` 行声明 **117**；
3. 同文件**表注** `:9` 已写 "the per-run rows, configurations and metrics of **all 117 experiments**"。

而正文 6 处写 116，且 `:3` 与 `:9` **同文件内自相矛盾**。→ 判定 117 正确。

## 单位统一

`empirical.tex:4` 原文用 "116 **runs**"，而同文件 `:15` 与全文用 "experiments"；
目录表列头为 `Catalogue section & Experiments`，一实验一行 → **统一为 experiments**。

    python tools\_pa_fix_count_117.py            # 预演
    python tools\_pa_fix_count_117.py --apply
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# (文件, 精确原串, 替换串, 说明)
EDITS: list[tuple[str, str, str, str]] = [
    ("conclusion.tex",
     "(116 experiments)",
     "(117 experiments)",
     "实验计数"),
    ("empirical.tex",
     "These experiments, spanning 116 runs,",
     "These experiments, spanning 117 experiments,",
     "计数 + 单位统一（runs → experiments）"),
    ("empirical.tex",
     "The complete experiment catalog (116 experiments)",
     "The complete experiment catalog (117 experiments)",
     "实验计数"),
    ("introduction.tex",
     "confirmed across 116 experiments on five architectures",
     "confirmed across 117 experiments on five architectures",
     "实验计数"),
    ("introduction.tex",
     "spanning 116 experiments across two PEFT methods",
     "spanning 117 experiments across two PEFT methods",
     "实验计数"),
    ("supplement.tex",
     "Table~\\ref{tab:full_experiments} lists all 116 experiments from Part~I.",
     "Table~\\ref{tab:full_experiments} lists all 117 experiments from Part~I.",
     "实验计数（同文件表注已为 117）"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    n = 0
    for fname, old, new, why in EDITS:
        p = REPO / "paper合" / "sections" / fname
        t = io.open(p, encoding="utf-8").read()
        cnt = t.count(old)
        if cnt == 1:
            print(f"  ✅ {fname}: {why}")
            if apply:
                io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
            n += 1
        elif cnt == 0:
            print(f"  ⚠ {fname}: **未命中**（可能已改或原文不符）: {old[:60]}")
        else:
            print(f"  ⚠ {fname}: 命中 {cnt} 次（预期 1）——拒绝改动: {old[:60]}")
    print(f"\n{n}/{len(EDITS)} 处{'已改' if apply else '可改'}")
    if apply:
        # 断言①：6 处旧串均已消失
        for fname, old, _, _ in EDITS:
            t = io.open(REPO / "paper合" / "sections" / fname, encoding="utf-8").read()
            assert old not in t, f"断言失败：{fname} 仍含旧串"
        # 断言②：全篇不再有 116 作为实验计数
        import re
        left = 0
        for f in (REPO / "paper合" / "sections").glob("*.tex"):
            tt = io.open(f, encoding="utf-8").read()
            left += len(re.findall(r"(?:spanning|across|all|catalog\s*\()\s*\(?116\b", tt))
        assert left == 0, f"仍有 {left} 处计数语境 116"
        print("✅ 断言通过：6 处旧串消失，全篇无计数语境 116")
    else:
        print("（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
