# -*- coding: utf-8 -*-
r"""按操作者唯一原则处理 COCO 表：**只留可复现的 3 行**（2026-10-07）。

## 操作者的唯一原则

> **"所有数据必须要可复现有来源"**

## 违规项

`supplement.tex` 的 `tab:coco_ode`（L140–166）有 **15 行**，caption 称
*"Cross-dataset ODE validation on MS-COCO (5-seed means)"*，正文称 *"81 recorded runs
(14 configurations × 5 seeds, 5 frozen evaluations, and 5 full-FT seeds)"*。

**但 `outputs/theory/coco/` 只有 3 配置 × 3 seed = 9 run**，且**无 frozen**：
`coco_both_r8`、`coco_text_r8`、`coco_full_ft`（rank 8 のみ）。

**→ 该表 14 个 PEFT 配置里，只有 2 个（both r8 / text r8）+ full-FT 可复现；
其余 12 行（各 rank r∈{1,2,4,16,32,64}）在归档中不存在 → 无来源 → 必须删。**

## 改法

用**实测值**（逐 run 拟合，与 `tools/_p1_ledger.py` 同法）替换整表：

| 配置 | α | β | R² |
|---|---|---|---|
| Text-only, $r{=}8$ | $-0.028 \pm 0.017$ | $0.107 \pm 0.177$ | $0.897$ |
| Both, $r{=}8$ | $-0.013 \pm 0.004$ | $0.057 \pm 0.055$ | $0.910$ |
| Full FT | $-0.034 \pm 0.004$ | $0.007 \pm 0.004$ | $0.966$ |

并同步更正 caption 与正文句（81 runs → 9 runs / 3 配置）。

    python tools\_pa_fix_coco_table.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "supplement.tex"

OLD_ROWS = r"""Text-only, $r{=}1$  & $-0.027 \pm 0.018$ & $0.093 \pm 0.035$ & $0.971$ & --- \\
Text-only, $r{=}2$  & $-0.027 \pm 0.013$ & $0.104 \pm 0.045$ & $0.970$ & --- \\
Text-only, $r{=}4$  & $-0.044 \pm 0.037$ & $0.176 \pm 0.143$ & $0.960$ & --- \\
Text-only, $r{=}8$  & $-0.034 \pm 0.018$ & $0.155 \pm 0.071$ & $0.972$ & --- \\
Text-only, $r{=}16$ & $-0.037 \pm 0.038$ & $0.142 \pm 0.111$ & $0.969$ & --- \\
Text-only, $r{=}32$ & $-0.061 \pm 0.035$ & $0.265 \pm 0.214$ & $0.967$ & --- \\
Text-only, $r{=}64$ & $-0.069 \pm 0.068$ & $0.284 \pm 0.265$ & $0.974$ & --- \\
Both, $r{=}1$       & $-0.050 \pm 0.036$ & $0.269 \pm 0.152$ & $0.970$ & --- \\
Both, $r{=}2$       & $-0.024 \pm 0.006$ & $0.124 \pm 0.041$ & $0.964$ & --- \\
Both, $r{=}4$       & $-0.024 \pm 0.006$ & $0.125 \pm 0.041$ & $0.970$ & --- \\
Both, $r{=}8$       & $-0.025 \pm 0.014$ & $0.118 \pm 0.074$ & $0.984$ & --- \\
Both, $r{=}16$      & $-0.061 \pm 0.075$ & $0.223 \pm 0.200$ & $0.984$ & --- \\
Both, $r{=}32$      & $-0.024 \pm 0.009$ & $0.139 \pm 0.085$ & $0.964$ & --- \\
Both, $r{=}64$      & $-0.029 \pm 0.015$ & $0.162 \pm 0.103$ & $0.977$ & --- \\
Full FT             & $-0.044 \pm 0.030$ & $0.166 \pm 0.054$ & $0.971$ & --- \\"""

NEW_ROWS = r"""Text-only, $r{=}8$ & $-0.028 \pm 0.017$ & $0.107 \pm 0.177$ & $0.897$ & --- \\
Both, $r{=}8$       & $-0.013 \pm 0.004$ & $0.057 \pm 0.055$ & $0.910$ & --- \\
Full FT             & $-0.034 \pm 0.004$ & $0.007 \pm 0.004$ & $0.966$ & --- \\"""

OLD_CAP = r"\caption{Cross-dataset ODE validation on MS-COCO (5-seed means).}"
NEW_CAP = (r"\caption{Cross-dataset ODE validation on MS-COCO (3-seed means, $n=3$ runs per "
           r"configuration). The configurations are those for which trajectories are archived; "
           r"the rank sweep reported for Flickr30k is not available on MS-COCO in this release.}")

OLD_TXT = (r"Table~\ref{tab:coco_ode} reports ODE metrics on MS-COCO (81 recorded runs: 14 configurations "
           r"$\times$ 5 seeds, 5 frozen evaluations, and 5 full-FT seeds; one archived text-r16 run "
           r"duplicates an existing seed, so per-config means use the 5 unique seeds).")
NEW_TXT = (r"Table~\ref{tab:coco_ode} reports ODE metrics on MS-COCO for the three configurations whose "
           r"trajectories are archived (rank $8$ in the text-only and both positions, plus a full-fine-tuning "
           r"pilot), each at three seeds, fitted one run at a time.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    ok = 0
    for old, new, why in ((OLD_ROWS, NEW_ROWS, "表体 15 行 → 3 行"),
                          (OLD_CAP, NEW_CAP, "caption"),
                          (OLD_TXT, NEW_TXT, "正文句")):
        c = t.count(old)
        print(f"  {'✅' if c == 1 else '⚠'} {why}：命中 {c}")
        if c == 1:
            t = t.replace(old, new, 1)
            ok += 1
    if ok != 3:
        print("  ❌ 未全部命中，未写入")
        return 1
    if not apply:
        print("  （预演）")
        return 0
    ast.parse("pass")
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    for k in ("$0.897$", "$0.910$", "$0.966$", "3-seed means"):
        assert k in t2, f"断言失败：缺 {k}"
    for k in ("$0.971$", "$0.984$", "81 recorded runs"):
        assert k not in t2, f"断言失败：旧值仍在 {k}"
    print("  ✅ 已写入：COCO 表只剩 3 行可复现数据，旧值全清")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
