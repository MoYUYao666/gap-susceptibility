# -*- coding: utf-8 -*-
r"""Record what the search for Paper A's unsourced numbers found.

    python tools/_p718_record_search.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔎 2026-10-14 21:30 —— 追查 Paper A 的 GAP：**2 项已解决，5 项确认无承载字段**
>
> ### 一、操作者指令
>
> > **"查"** —— 追查上一轮 GAP 7 项的来源。
>
> ### 二、✅ 已解决 2 项（GAP 7 → 5）
>
> | 数字 | 真正的来源 | 复现 |
> |---|---|---|
> | **OpenCLIP BitFit 平均 R² = 0.943** | `outputs/theory/openclip/openclip_results.json :: mean(r_squared)` | **实测 0.942799**（n=3）✅<br>（**P3 的 `_claim_ledger.py:262` 早已断言同一数** —— 线索来自搜脚本）
> | **「222 个拟合 / 203 个为负 / 19 个例外」** | `outputs/analysis/alpha_sign_audit.json` 各文件计数之和 | **实测 n=222、neg=203、nonneg=19** —— 与稿件逐字一致 ✅ |
> | 「五十 Adapter fits」 | `outputs/theory/adapter/adapter_all_results.json :: len` | **50** ✅ |
> | 「三个 CLIP BitFit」 | `outputs/theory/bitfit/bitfit_results.json :: len` | **3** ✅ |
>
> **222 的分解（可逐项复核）**：
> ```
> ode_ledger.json                 n=103  neg= 99  nonneg= 4
> ode_loco.json                   n= 33  neg= 32  nonneg= 1
> ode_loco2.json                  n= 33  neg= 32  nonneg= 1
> theory/adapter/adapter_all_results.json  n= 50  neg= 40  nonneg=10
> theory/bitfit/bitfit_results.json        n=  3  neg=  0  nonneg= 3
> ─────────────────────────────────────────────────────────
> 合计                            n=222  neg=203  nonneg=19
> ```
>
> ### 三、🔴 **一项必须处理的时间性问题**（`alpha_sign_audit` 是历史快照）
>
> `alpha_sign_audit.json` 记 `ode_ledger` 的 **n = 103**，而**现在的 `ode_ledger.json` 是 96**
> ⇒ **该审计做于 ODE 台账重算之前**。
>
> **⇒ 后果**：审稿人若自己去数，会得到 **96+33+33+50+3 = 215**，**而不是 222**。
> **⇒ 建议**：稿件改为引用 `alpha_sign_audit` 的口径（写明"审计件"），**或按现行归档重算**。
> **（这是我能查出的最要紧的一处，比 5 个 GAP 更实际。）**
>
> ### 四、🔴 确认无承载字段的 5 项
>
> 搜索共四轮，覆盖：① 全部 1,613 个已跟踪 JSON 的**数值匹配** ② 1,603 个工具脚本的**字面值** 
> ③ 10 类"数目录"规则的**计数复现** ④ **严格判据**（字段名须自称在数什么：experiment/run/fit/control/count…）。
>
> | 数字 | 结论 |
> |---|---|
> | 斜率 CR1 标准误 **0.29** | 🔴 全库 `0.29±0.03` 只命中无关字段；`cluster_robust_OLS` 各分组**只有 `p_cr1`，没有 `se`** |
> | 机制实验 **117** | 🔴 严格判据下 16 处命中**全部来自 `ocean_fauna_margins`（另一课题）** |
> | 严格冻结对照 **95** | 🔴 唯一命中 `monitor_dg_check2` 的规则名，无关 |
> | 实验目录 run 数 **221** | 🔴 **0 处**名字合格的命中；数目录最接近 232 |
> | 验证实验数 **383** | 🔴 **0 处**名字合格的命中；数目录最接近 385（`gap_history.json`） |
>
> **⇒ 这 5 个数在已跟踪归档里没有承载字段。** 两条出路：**(a)** 作者指出产出脚本/字段 → 我改台账复核；
> **(b)** 从稿件删除。
>
> ### 五、台账现状（`tools/_claim_ledger_paperA.py`）
>
> **PASS 17 ｜ GAP 5 ｜ 共 22**
>
> 已核：ODE 拟合质量 5 项、222/203/19 及 50/3 共 5 项、OpenCLIP 0.943、关联分析 n=204 与
> r=−0.71 / 斜率 −1.05 / p=0.016、零样本 60.69 / 60.87。
>
> ### 六、剩余
>
> ① **5 个 GAP**（需作者给出产出脚本，或删除）② **3.4 节的时间性问题**（建议改口径或重算）
> ③ 投稿包本身已就绪，可上传
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "追查 Paper A 的 GAP" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("追查 Paper A 的 GAP", "0.942799", "n=222、neg=203", "n = 103", "PASS 17"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
