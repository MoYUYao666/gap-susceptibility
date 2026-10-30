# -*- coding: utf-8 -*-
r"""Record the six novelty additions to A1 and update every status document.

Items delivered:
  1+2  formal Proposition 1 (non-sufficiency) with proof, Corollary 1 (family-conditional informativeness),
       Proposition 2 (the gap does not bound accuracy) with proof
  3    label-free checkpoint-selection protocol: oracle 59.49, tau-max 59.44 (regret 0.05, max 0.46), CUSUM 59.35
       (0.14), patience-2 58.80 (0.69), last epoch 57.14 (2.35); CUSUM h = 6.0 calibrated leave-one-out
  4    the four controls stated as a falsification protocol (Table controls), last row filled with the second-benchmark
       spreads
  5    matched-gap replication on DTD (10.1 points at |dCG|<=0.03; 15.1 at 0.05) and Food-101 (12.1; 42.1), with
       contraction reversals +17.8 and +18.2
  6    neutral companion-work paragraph in the Discussion

Archives: outputs/analysis/a1_monitor_protocol.json, outputs/analysis/a1_matched_gap_second_dataset.json
Scripts:  _p1254 (second dataset), _p1255 (monitor protocol), _p1256 (theory), _p1257 (replication),
          _p1258 (refs), _p1259 (controls numbers)

    python tools/_p1260_record_a1_novelty_round2.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
WHICH = REPO / "哪篇是哪篇.md"
NOVDOC = REPO / "docs" / "A1_NOVELTY_STEP1_2026-10-18.md"

NOVSEC = """

---

## 第 6 步（2026-10-18 17:45）：六项新颖性增强全部落地

操作者指示"1-6 都做"。A1 从 **45 页**增至 **48 页**，编译 **0 错误 / 0 未定义 / 0 Overfull**，审计 `a1_paa`
**READY / grade A（pass=61 fail=0 warn=0）**。

| 项 | 内容 | 归档/证据 |
|---|---|---|
| **1** | **Proposition 1（非充分性）**：`top1` 只依赖相似度矩阵的行序；对文本侧做公共平移 $t_c\\mapsto t_c+v$ 保持全部行序（故 top-1、top-$k$、$\\tau$ 全不变），而 $\\mathrm{CG}=\\|\\bar t+v-\\bar x\\|$ 可取任意 $g\\ge0$。附完整证明 | `main.tex` §3.1 `sec:theory` |
| **1b** | **Corollary 1（族条件信息性）**：保序族上 top-1 为常数而 CG 在区间内变动 ⇒ 阈值不可跨族迁移 | 同上 |
| **2** | **Proposition 2**：$|a(S)-a(S')|\\le n^{-1}\\sum_i\\mathbb{1}[\\arg\\max\\text{ 改变}]$，且 CG 差为零时该质量可最大 ⇒ 不存在 $h(0)=0$ 的界 | 同上 |
| **3** | **无标签监控协议**：六种选择规则在 10 条轨迹上评测；$\\tau$-max **59.44**（相对 oracle 59.49 的 regret **0.05**、最差 0.46）、CUSUM **59.35**（0.14，LOO 标定 $h=6.0$）、patience-2 58.80（0.69）、训到末轮 57.14（2.35）；并诚实报告"首轮即最优、平凡规则并列"的限制 | `outputs/analysis/a1_monitor_protocol.json`（`_p1255`）|
| **4** | **四控制即伪证协议表**：匹配 gap / 200 随机方向 / 类收缩 / 基准扫描，各列"所伪证的假设"与实测结果 | `main.tex` §5 `tab:controls` |
| **5** | **第二数据集复现**：同一协议在 **DTD**（47 类，冻结 CG 1.019 / top-1 41.62%）与 **Food-101**（101 类，0.953 / 80.64%）上重现分离；$|\\Delta\\mathrm{CG}|\\le0.03$ 时最大 top-1 差 **10.1 / 12.1** 点，$\\le0.05$ 时 **15.1 / 42.1** 点（Food-101 的 42.1 点发生在**同一 T 族内**，$\\Delta\\mathrm{CG}=0.034$）；类收缩反向 +17.8 / +18.2 点而 gap 同步增大 | `outputs/analysis/a1_matched_gap_second_dataset.json`（`_p1254`）|
| **6** | **姊妹文关系段**：说明与"梯度流动力学"那条线互补、不重叠、结论不依赖之 | `main.tex` Discussion |

**数字溯源**：32.7（`a1_matched_gap_families.json::max_matched_gap_spread_tol003.spread = 32.68`）、52.1、27.1@0.066/@0.197、
2.5 点与 $r=0.60$（`a1_random_direction_gap.json::summary`）、+19.0/+19.4/+15.0（`a1_matched_gap_crossmodel.json`）；
第二数据集数字见 `a1_matched_gap_second_dataset.json`。控制表初稿曾误写 33.1（归档为 32.68），由 `_p1259` 修正。
"""

ENT = """> **🧪 2026-10-18 17:45 —— A1 六项新颖性增强全部落地（45 → **48 页**，审计 READY/A，0 失败 0 警告）**
>
> 操作者要求"1-6 都做"。A1（改投 Pattern Analysis and Applications）补齐六项，全部用**已有归档 + 纯推导**完成，
> 未新增大规模实验（仅本地冻结 CLIP 前向 ×2 数据集）。
>
> | 项 | 落地内容 |
> |---|---|
> | 1+2 | **Proposition 1**（非充分性，含证明：文本侧公共平移保持行序、gap 可变任意值）+ **Corollary 1**（族条件信息性）+ **Proposition 2**（gap 不构成精度界，含证明）|
> | 3 | **无标签监控协议**：$\\tau$-max 59.44 vs oracle 59.49（regret 0.05，最差 0.46）；CUSUM 59.35（0.14，LOO $h=6.0$）；训到末轮 57.14（2.35）——并诚实标注"首轮即最优"的限制 |
> | 4 | **四控制＝伪证协议**表（匹配 gap / 200 随机方向 / 类收缩 / 基准扫描）|
> | 5 | **第二数据集复现**：DTD 10.1 / Food-101 12.1 点（$|\\Delta\\mathrm{CG}|\\le0.03$）；$\\le0.05$ 时 15.1 / 42.1 点（42.1 发生于**同族内**）；收缩反向 +17.8 / +18.2 点 |
> | 6 | **姊妹文关系段**（互补、不重叠、不依赖）|
>
> **归档**：`a1_monitor_protocol.json`、`a1_matched_gap_second_dataset.json`；**脚本**：`_p1254`–`_p1259`。
> **数字溯源**：32.68（families）、52.14、27.1@0.066/0.197、2.48 点与 $r=0.60$（random-direction）、+19.0/+19.4/+15.0（crossmodel）。
> 控制表初稿误写 33.1 → 已由 `_p1259` 改为 **32.7**（与 §5.2 正文一致）。
>
> **A1 现状**：**48 页**、0/0/0；PAA 包已重建（Manuscript 48 页、源码 14 文件、staged 编译一致）；
> 审计 **READY grade A：pass=61 fail=0 warn=0**。**仍待投**（Springer EM）。
>


"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0

    n = io.open(NOVDOC, encoding="utf-8").read()
    if "六项新颖性增强全部落地" not in n:
        io.open(NOVDOC, "w", encoding="utf-8", newline="").write(n.rstrip("\n") + NOVSEC)
        print("  novelty doc appended")

    h = io.open(HANDOFF, encoding="utf-8").read()
    if "A1 六项新颖性增强全部落地" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT.replace("\\n", "\n") + h[j + 1:])
        print("  handoff added")

    w = io.open(WHICH, encoding="utf-8").read()
    old = "；前投 Neural Networks `NEUNET-D-26-09426` **2026-10-18 桌面拒稿**（未送审） | 45 + 1 title page |"
    new = ("；前投 Neural Networks `NEUNET-D-26-09426` **2026-10-18 桌面拒稿**（未送审）；"
           "**已加定理（Prop 1/Cor 1/Prop 2）+ 无标签监控协议 + 第二数据集复现** | 48 + 1 title page |")
    print(f"  which A1 row: {w.count(old)}")
    if w.count(old) == 1:
        w = w.replace(old, new, 1)
        io.open(WHICH, "w", encoding="utf-8", newline="").write(w)

    m = io.open(MAP, encoding="utf-8").read()
    row = ("83. 🧪 **A1 六项新颖性增强（2026-10-18 17:45）** —— 45→**48 页**：Prop 1（非充分性，含证明）+ Cor 1 + Prop 2（无界）；"
           "无标签监控协议（τ-max regret 0.05/CUSUM 0.14/末轮 2.35）；四控制伪证协议表；**第二数据集复现 DTD 10.1 / Food-101 12.1 点**"
           "（≤0.05 时 15.1/42.1，42.1 在同族内）；姊妹文关系段。归档 `a1_monitor_protocol.json`、`a1_matched_gap_second_dataset.json`；"
           "控制表 33.1→**32.7** 已按归档修正；审计 **READY/A pass=61 fail=0 warn=0**。\n")
    if "A1 六项新颖性增强" not in m:
        anchor = "82. 📮 **Paper A 已投出"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
