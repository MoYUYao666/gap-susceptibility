# -*- coding: utf-8 -*-
r"""Record A1 novelty step 3 (random-direction control, cross-model replication, boundary subsection, proposition).

    python tools/_p1216_record_a1_novelty_step3.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "docs" / "A1_NOVELTY_STEP1_2026-10-18.md"
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"

APPEND = """

---

# 第 3 步（2026-10-18 13:25）：控制实验、跨模型复现、边界小节、形式命题

> 脚本 `_p1213`（随机方向）、`_p1214`（跨模型）、`_p1215`（入稿）
> 归档 `outputs/analysis/a1_random_direction_gap.json`、`a1_matched_gap_crossmodel.json`

## 1. 随机方向控制（诚实负结果）

200 个随机单位方向，各自平移以把 CG 恢复到 frozen 值（CG 匹配到 0.858±0.003，最大偏差 0.013）：
**top-1 仅 57.0–59.5%（跨度 2.5 点，mean 58.7，frozen 59.1）**；τ 跨度 0.70–0.90，与 top-1 相关 r=0.60。

⇒ **匹配 gap 的 33/52 点塌缩不是普遍现象**，只发生在**相干方向**平移（正是微调轨迹的方向）；随机扰动保 gap 时也保准确率。
这条已如实写入正文，既避免过度声称，也预先挡掉"你挑了 λ"的质疑。

## 2. 跨模型复现（OpenCLIP）

| 量 | CLIP ViT-B/32 | OpenCLIP laion2B |
|---|---|---|
| frozen CG / top-1 | 0.855 / 59.1% | 0.791 / 62.4% |
| 类收缩 a=0.5：CG / top-1 | 0.897 / 78.1%（**+19.0**）| 1.187 / 81.8%（**+19.4**）|
| 回程分支 | λ=0.5 CG 0.426/46.8 vs λ=2 CG 0.398/14.1（ΔCG 0.028 → **32.7 点**）| λ=0.5 CG 0.394/55.6 vs λ=2 CG 0.328/28.5（ΔCG 0.066 → **27.1 点**）|

**方向反转在两模型上一致（+19.0 vs +19.4）**；回程分支的反例在 OpenCLIP 上也存在（27.1 点），只是 ΔCG 略大。
**SigLIP 不采用**：本 harness 上 zero-shot 基线仅 1.86%，明显是文本塔路径损坏，不能作为科学结果。

## 3. 写入 A1 的三块新内容

1. **形式命题**（Setup 之前）：top-1 只依赖相似度的行内序；CG 是这些序的函数之外的量；|ΔCG|≤0.03 可对应 >30 点准确率差
   ⇒ 任何 CG 阈值都不可能是零样本分类的充分健康判据。并注明反例只对相干变换成立（随机方向仅 2.5 点）。
2. **随机方向控制 + 跨模型复现**（并入 5.2 节，在 Figure 2 之前）。
3. **新小节 "The first-order law keeps shape but not level across benchmarks"**（`sec:boundary`）：exact 分支 MAE 0.0013（自洽）、
   闭式 0.115、单常数 0.017 后跨四基准 MAE 0.079–0.120、最优常数 0.36–0.98 ⇒ 保形不保水平，缺的是 margin–bias **联合**结构。

## 4. 编译

A1：**45 页**（42 → 44 → 45），**0 错误 / 0 未定义 / 0 Overfull**。
"""

ENT = """> **🧪 2026-10-18 13:25 —— A1 新颖性第 3 步：控制实验 + 跨模型复现 + 边界小节 + 形式命题**
>
> ① **随机方向控制（诚实负结果）**：200 个随机方向各自平移以匹配 frozen CG（0.858±0.003），top-1 仅 **57.0–59.5%（跨度 2.5 点）**
> ⇒ 33/52 点塌缩**只发生在相干方向**，不是普遍现象；已如实写入，反而挡掉"挑 λ"质疑。
> ② **跨模型复现（OpenCLIP）**：类收缩方向反转 **+19.4 点**（CLIP +19.0）一致；回程分支反例仍在（λ=0.5 CG 0.394/55.6% vs λ=2 CG 0.328/28.5%，
> **27.1 点**，ΔCG 0.066）。**SigLIP 弃用**：基线 1.86% 说明 harness 文本塔路径坏了，不能当结果。
> ③ **新小节 `sec:boundary`**：一阶定律 exact 分支 MAE 0.0013（自洽）、闭式 0.115、单常数 k=0.55 后 0.017；冻结后跨四基准
> MAE **0.079–0.120**、最优常数 **0.36–0.98** ⇒ **保形不保水平**，缺 margin–bias 联合结构。
> ④ **形式命题**（Setup 前）：top-1 只依赖行内序，CG 非其函数 ⇒ **任何 CG 阈值都不是充分健康判据**。
>
> A1 编译 **45 页**（42→44→45）、**0 错误 / 0 未定义 / 0 Overfull**。归档 `a1_random_direction_gap.json`、`a1_matched_gap_crossmodel.json`；
> 脚本 `_p1213`–`_p1216`。**A1 仍未投**，冻结件 `SUBMISSION/A1_NeuralNetworks/` 未动。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    d = io.open(DOC, encoding="utf-8").read()
    if "第 3 步（2026-10-18" not in d:
        io.open(DOC, "w", encoding="utf-8", newline="").write(d.rstrip("\n") + APPEND)
        print("  doc updated")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "A1 新颖性第 3 步" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("68. 🧪 **A1 新颖性第 3 步（2026-10-18 13:25）** —— 随机方向控制（200 方向匹配 CG，top-1 仅跨 2.5 点 ⇒ 反例只对相干方向成立）；"
           "OpenCLIP 复现方向反转（+19.4 vs CLIP +19.0）与回程反例（27.1 点，ΔCG 0.066）；**SigLIP 弃用**（基线 1.86% 说明 harness 坏了）；"
           "新增 `sec:boundary`（一阶定律保形不保水平：四基准 MAE 0.079–0.120、最优常数 0.36–0.98）与**形式命题**（CG 非充分统计量）。"
           "A1 **45 页**、0/0/0。\\n")
    if "A1 新颖性第 3 步" not in m:
        anchor = "67. 🧪 **A1 新颖性第 2 步"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row.replace("\\n", "\n") + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
