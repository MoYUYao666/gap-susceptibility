# -*- coding: utf-8 -*-
r"""落账：配对检验提为主证据 + 规则补第三条（2026-10-12）。

    python tools\_p43e_record_paired_rule.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📐 2026-10-12（续 6）—— 配对检验提为主证据；流程规则补第三条**
>
> ### 一、`p3-downstream` 的第二次更正（措辞收紧），我复核后采纳
>
> 我先前写 *"同一干预在两种训练量下，**能量变化的符号相反**"* —— **过强**。
> 我独立跑配对检验（`tools/_p43c`，自实现 Wilcoxon 正态近似；对方用 scipy）：
>
> | 训练量 | 对数 | Δ(ΔE_test) | 判定 | Δ(R@1) | 判定 |
> |---|---|---|---|---|---|
> | **n=16** | 21 | −0.00641（**0/21 全负**） | **显著下降** | +0.00651（**21/0 全正**） | **显著改善** |
> | **n=1024** | 18 | **+0.00039**（7 正/11 负） | **p≈0.90 无显著变化** | −0.02244（**0/18 全负**） | **显著恶化** |
>
> ⇒ **n=1024 是"没动"，不是"略升"** ⇒ 已改稿为：
> **"An energy change is therefore neither sufficient nor necessary for the direction of
> downstream performance"**（两档**全票配对 + 双侧 Wilcoxon**）。
> （我的 p 值实现较保守：n=16 给 6.4e-5、n=1024 给 8.96e-1；对方 scipy 精确值 9.5e-7 / 0.899。
> **判定一致**；**引用时用对方的 scipy 值**，并在归档注明两种实现。）
>
> ### 二、⭐ 流程规则**补第三条**（对方建议，我采纳）
>
> > **凡报相关系数，必须同时给：**
> > **① 分层 / 子集内口径　② 簇结构说明　③ 一个不依赖相关的配对检验。**
>
> **第三条是核心**：前两条仍在"选口径"，而配对检验**独立于口径选择**，
> 审稿人无法用"你换了口径"来反打。**稿中已把配对检验提为主证据，相关系数降为辅助。**
>
> ### 三、n 口径已统一（对方重跑 `_p463`，门禁锁死四个字段）
>
> - `n_runs_total` = **79**（**1 条冻结基线 + 78 条训练**）
> - `n_runs_trained` = **78**
> - `n_runs_baseline_frozen` = **1**
> - `n_runs_used_in_energy_downstream` = **78**（冻结基线无 ΔE，进不了能量↔下游分析）
>
> ⇒ 报告里"78 run"指训练 run、"79 条"指归档总量，**两个都对且不冲突**。
>
> ### 四、状态
>
> - **P3**：**12 页 / 0 错 / 0 未定义**；**累计修 14 处**
> - **task-10**：✅ complete（保持）｜门禁 `_p466` 锁死 4 个相关系数 + 四个 n 字段
> - **task-9**：🔄 `p3-allocation`，链式任务 `pwsh-244` 挂 **23:45** 自动起；**GPU 归它**
> - **`p3-downstream` 的两段空档**（`p3-allocation` 切批切出，非让路）：GAP#1 做 Qwen2-VL-2B
>   **GPU 冒烟**（显存+单步耗时先验）、GAP#2 跑**解码器 VLM 的 rank sweep** ——
>   这是 **R3.13/R3.14 唯一还缺的那一档**（论文设定是解码器 VLM，此前只有 CLIP 双塔）。
>   **已要求：不得挤压 `p3-allocation` 的 E 组；跑成/跑不成都要如实报。**
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
    if "配对检验提为主证据" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("配对检验提为主证据", "neither sufficient nor necessary", "不依赖相关的配对检验",
              "n_runs_total", "累计修 14 处"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
