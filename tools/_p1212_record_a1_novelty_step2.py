# -*- coding: utf-8 -*-
r"""Record A1 novelty step 2: the matched-gap control inserted into the manuscript.

    python tools/_p1212_record_a1_novelty_step2.py [--apply]
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

# 第 2 步（2026-10-18 13:05）：把"匹配 gap"实验写进 A1

> 脚本：`_p1209`（三扰族扫描）、`_p1210`（作图）、`_p1211`（小节插入）
> 归档：`outputs/analysis/a1_matched_gap_families.json`；图：`paper_a1/figures/fig5_matched_gap.{pdf,png}`

## 实验（冻结 CLIP ViT-B/32，5 000 张 ImageNet，1 000 类，各自基准 gap 方向）

| 族 | 参数 | CG | top-1 (%) |
|---|---|---|---|
| — | frozen | 0.855 | 59.1 |
| 平移 | λ=0.25 / 0.5 / 1 / 2 / 4 | 0.651 / **0.426** / 0.045 / **0.398** / 0.613 | 55.6 / 46.8 / 33.6 / **14.1** / 3.5 |
| 类收缩 | a=0.1 / 0.25 / 0.5 | 0.865 / 0.878 / 0.897 | 63.3 / 69.2 / **78.1** |
| 噪声 | σ=0.05 / 0.2（3 seeds）| 0.855 / 0.849 | 58.9 / 57.9 |

**关键结果**：
- **匹配 gap（ΔCG=0.028）：top-1 差 32.7 点**（λ=0.5 的 46.8% vs λ=2 的 14.1%）；
- 放宽到 ΔCG≤0.05：**差 52.1 点**（λ=0.25 的 55.6% vs λ=4 的 3.5%）；
- **方向可反转**：类收缩在 gap **更大**（0.855→0.897）时准确率**更高**（59.1%→78.1%）；
- 噪声族为对照：两个量都不动。

## 写入稿件

- 新增小节 **5.2 “A matched-gap control: the same gap can hide 33 accuracy points”**（`\\label{sec:matchedgap}`），
  含图 `fig:matchedgap`（Figure 2）与表 `tab:matchedgap`（Table 1）；
- 摘要新增一句：*"The gap is not even a sufficient statistic for the accuracy it is often used to monitor: two
  configurations whose centroid gaps agree to 0.03 can differ by 33 accuracy points, and at 0.05 by 52."*
- 编译：**44 页**（原 42），**0 错误 / 0 未定义 / 0 Overfull**；图注与表注措辞已修正（图例移出数据区）。

## 为什么这一步对"新颖性"有效

AE 的拒稿理由是"technical novelty marginal"。本步把 A1 的核心命题从**经验观察**改成**可构造检验的非充分性陈述**，
并给出一个**尖锐、可复现、与控制实验并列**的量化反例（同 gap 差 33/52 点 + 反向族 + 对照族）。
这不是加篇幅，而是把"gap 不是通用指标"升级为"gap 非充分统计量，且我们给出构造证明"。
"""

ENT = """> **🧪 2026-10-18 13:05 —— A1 新颖性第 2 步：匹配 gap 实验写入正文（+图 +表 +摘要句）**
>
> 新增 **5.2 节 "A matched-gap control"**：冻结 CLIP 上三个扰族（gap 方向平移 / 类收缩 / 各向同性噪声），
> 在**显式匹配的 centroid gap** 下比较准确率。结果：
> - **ΔCG=0.028 时 top-1 差 32.7 点**（λ=0.5: CG 0.426/top-1 46.8% vs λ=2: CG 0.398/top-1 14.1%）；
> - ΔCG≤0.05 时**差 52.1 点**（λ=0.25 的 55.6% vs λ=4 的 3.5%）；
> - **方向可反转**：类收缩使 gap 更大（0.855→0.897）而准确率更高（59.1%→78.1%）；
> - 噪声族为对照（两者都不动）。
>
> 摘要加一句："two configurations whose centroid gaps agree to 0.03 can differ by 33 accuracy points, and at 0.05 by 52."
> 新增 `fig:matchedgap`（Figure 2）与 `tab:matchedgap`（Table 1）。
> A1 重建 **44 页**（原 42）、**0 错误 / 0 未定义 / 0 Overfull**。
>
> 归档 `outputs/analysis/a1_matched_gap_families.json`；脚本 `_p1209`–`_p1212`；说明见 `docs/A1_NOVELTY_STEP1_2026-10-18.md` 第 2 步。
> ⚠️ A1 仍**未投**（NN 已桌面拒），本节为下一轮投稿的新颖性主证据；`SUBMISSION/A1_NeuralNetworks/` 冻结件未动。
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
    if "第 2 步（2026-10-18" not in d:
        io.open(DOC, "w", encoding="utf-8", newline="").write(d.rstrip("\n") + APPEND)
        print("  doc updated")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "A1 新颖性第 2 步" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("67. 🧪 **A1 新颖性第 2 步：匹配 gap 实验入稿（2026-10-18 13:05）** —— 新增 5.2 节 + Figure 2 + Table 1："
           "**ΔCG=0.028 时 top-1 差 32.7 点**、ΔCG≤0.05 差 **52.1 点**；类收缩反向（gap 0.855→0.897、top-1 59.1%→78.1%）；"
           "噪声族对照。摘要加「非充分统计量」句。A1 重建 **44 页**、0/0/0。归档 `outputs/analysis/a1_matched_gap_families.json`。\n")
    if "A1 新颖性第 2 步" not in m:
        anchor = "66. 🔬 **A1 新颖性升级第 1 步"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
