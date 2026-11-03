# -*- coding: utf-8 -*-
r"""落账：p3-downstream 的更正 + 我的第 18 个错 + 一条新流程规则（2026-10-12）。

    python tools\_p43b_record_spearman_lesson.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📊 2026-10-12（续 5）—— 一条重要的统计更正：整体相关不能当单调关系；我也犯了同型错（第 18 个）**
>
> ### 一、`p3-downstream` 主动更正了自己上一条的统计解释
>
> 它先前写 *"Spearman(ΔE_test, ΔR@1) = −0.3742 → 能量降幅与下游收益负相关"* ——
> **把整体相关当成了子集内的单调关系**。更正后（**我已用 `tools/_p439b` 从
> `outputs/analysis/p3d_clip_ranksweep.json` 独立重算，全部对上**）：
>
> | 口径 | Spearman | n |
> |---|---|---|
> | **ΔE_train vs ΔR@1**（论文 ΔE 的直接类比） | **+0.4778** | 78 |
> | **ΔE_test vs ΔR@1（全体）** | **−0.3742** | 78 |
> | **ΔE_test vs ΔR@1（仅 ΔE_test<0）** | **+0.1715** | 54 |
> | ΔE_test vs ΔR@1（仅 real） | −0.6912 | 39 |
> | ΔE_test vs ΔR@1（仅 blank） | −0.6385 | 39 |
>
> ⇒ **在"能量下降"的 54 个 run 内部几乎无关（+0.17）**；
> 全体 −0.374 **来自 real/blank 两簇的结构差异**，**不是"降得越多、下游越差"的单调关系**。
>
> ### 二、⚠️ 我犯了**同型错误**（本阶段第 18 个）
>
> 我在 `experiments.tex` 写了 *"…the rank correlation … is $-0.3819$:
> **improving the energy is associated with worse retrieval**"* —— **依赖的就是那个全体相关**。
> **已改**（`tools/_p43a`）：改为**分层汇报四个口径**、明确写
> *"restricted to the $54$ runs whose energy actually falls … the correlation is $+0.172$,
> which is to say there is essentially no relationship"*、**以配对比较为主证据**。
>
> **若它不主动更正，我就会把这个错误留在稿子里。**
>
> ### 三、配对比较比我先前写的更锋利（**符号反转**）
>
> 同 rank / 同 n / 同 seed，**real → blank**：
>
> | 训练量 | 对数 | Δ(ΔE_test) 均值 | Δ(ΔR@1) 均值 | R@1 范围 |
> |---|---|---|---|---|
> | **n=16** | 21 | **−0.00641**（blank 能量更降） | **+0.00651**（下游**升**） | [+0.0027, +0.0099] |
> | **n=1024** | 18 | **+0.00039**（blank 能量**略升**） | **−0.02244**（下游**降**） | **[−0.0346, −0.0081]** |
>
> ⇒ **同一干预在两种训练量下，能量变化的符号相反、下游变化的符号也相反**
> ⇒ **"能量符号不决定下游符号"**——**比"负相关"或"无相关"都更干净地否证代理关系**
> （不依赖簇结构、不依赖相关口径）。**稿中已用这个版本。**
>
> ### 四、⭐ 新增流程规则（我采纳并推广）
>
> > **凡报相关系数，必须同时给出「子集内」的口径，并说明簇结构是否主导。**
> > 整体相关在"两个簇"的数据上会**伪装成**一个可解释的单调关系。
>
> **依据**：本阶段同类错误已第四次——① 我"88 of 94 无归档"（只搜英文词）② 我"2 格无来源"（实为抽样+provenance）
> ③ 队友"No interior minimum"（实有一处）④ **本次"整体相关当单调关系"**（我与队友各犯一次）。
> **共性**：**把一个统计量当成它并不成立的解释**。
>
> ### 五、任务与状态
>
> - **task-10**：✅ complete（**保持**，无需再跑）；`p3-downstream` 已将本次错误**原文留在
>   `docs/P3_DOWNSTREAM.md` §5.2**，图标题**同时标两个 Spearman**，门禁 `_p466` **41/41** 加断言锁死 4 个系数
> - **task-9**：🔄 `p3-allocation`，链式任务 `pwsh-244` 挂 **23:45** 自动起（GPU 归它）
> - **P3**：**12 页 / 0 错 / 0 未定义**；**累计修 13 处**（本轮 +1：修我自己那句相关表述）
> - **一处 n 口径待核**：`p3d_summary.json` 写 `n_runs: 78`，`p3d_clip_ranksweep.json` 有 **79** 条
>   → 已要求成员统一口径（**口径必须唯一**，否则日后复核对不上）
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "整体相关不能当单调关系" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("整体相关不能当单调关系", "+0.4778", "+0.1715", "符号反转", "凡报相关系数"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
