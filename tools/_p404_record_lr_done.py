# -*- coding: utf-8 -*-
r"""落账：task-7 收官（19 runs / 7 lr）+ 我核出的一处全称否定错误（2026-10-12）。

    python tools\_p404_record_lr_done.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = r"""> **✅ 2026-10-12（续）—— task-7 收官（19 runs / 7 lr），lr 段落定稿**
>
> ### 最终表（我已**独立重算逐格一致**；sd = ddof=1；冻结 59.91% / CG 0.8157）
>
> | lr | n | zero-shot % | **ΔCG** | 区 |
> |---|---|---|---|---|
> | 1e-07 | 2 | 60.52 ± 0.02 | **−0.0058 ± 0.0004** | functional |
> | 3e-07 | 2 | 61.07 ± 0.01 | **−0.0069 ± 0.0012** | functional |
> | 1e-06 | 3 | 60.87 ± 0.21 | **−0.0016 ± 0.0052** | functional |
> | 1e-05 | 3 | 52.18 ± 1.03 | **+0.1860 ± 0.0047** | functional |
> | 3e-05 | 3 | 29.72 ± 1.50 | **+0.2531 ± 0.0029** | functional |
> | 1e-04 | 3 | 2.63 ± 2.17 | **+0.4416 ± 0.3077** | **collapse** |
> | 3e-04 | 3 | 0.10 ± 0.03 | **+0.1545 ± 0.8551** | **collapse** |
>
> 出处：`outputs/analysis/pr_fullft_lr_sweep_full.json::analysis.per_lr.*`（19 runs = 9 carried + 10 new，
> **从未覆盖**）；表 `outputs/analysis/pr_fullft_tables.md` T1–T7。
>
> ### sd 差异的根因（成员解释，我已验证）
>
> 我先前误判为"基准不同"——**错**。两者都用**冻结基准 0.8157**（同一字段
> `:: frozen.gap_retrieval.CG`）。真实差异是 **ddof + n**：
> `1e-4`：ddof=0 **0.2512**（我的）vs ddof=1 **0.3077**（成员的）；
> `3e-4`：ddof=0 **0.6981** vs ddof=1 **0.8551**。→ **引用必须同时给 n 与 ddof**。
>
> ### 🔴 我核出成员一处**全称否定不成立**
>
> 其 A 段写 *"**No interior minimum**"* —— **不成立**。逐点 ΔCG：
> `−0.0058, **−0.0069**, −0.0016, +0.1860, +0.2531, +0.4416, +0.1544`
> → **`3e-07` 的 −0.0069 低于两侧**（`1e-07` 的 −0.0058、`1e-06` 的 −0.0016）⇒ **是内部极小值**。
> **但**该极小值只比邻点低 **0.0011 ≈ 2× ΔCG 噪声 sd（0.00045–0.00070）** ⇒
> **结论不变，只是不可写成"无极小值"**。已要求改为
> *"the shallowest point is $3\times10^{-7}$ (−0.0069), but it lies only 0.0011 below its
> neighbours — about twice the sampling sd — so it does not establish an optimal rate."*
>
> **同类错我犯过两次**（"88 of 94 无归档"、"2 格无来源"），**这是第三次出现于本阶段**：
> **全称否定（"无 X"）必须先穷举**才能写。
>
> ### 3e-4 的两种退化几何（**必须逐 seed 并列，均值无意义**）
>
> | seed | ΔCG | CG | zero-shot |
> |---|---|---|---|
> | 42 | +0.8001 | 1.6158 | 0.08% |
> | **123** | **−0.8153** | **0.0004**（DG 0.0008） | 0.08% |
> | 999 | +0.4785 | 1.2942 | 0.13% |
>
> → 符号由 seed 决定；seed123 是**嵌入塌成常数点**（loss 卡在 `ln 64`）。
> **均值 +0.155 ± 0.855 无意义**——稿中已改为**只报逐 seed 值**。
>
> ### 稿中定稿（`tools/_p403`，提交 `8f6bed8`）
>
> `empirical.tex` + `discussion.tex` 现写：**7 个 lr**；**lr ≤ 1e-6 每个 seed ΔCG 皆为负**
> （−0.007…−0.0001）、zero-shot 60.5–61.1%（≥ 冻结 59.91%）；**符号在 1e-6 与 1e-5 之间翻转**；
> **单调升至 +0.2531 ± 0.0029**；**最浅点 3e-7 仅低 0.0011 ≈ 2× 噪声 sd ⇒ 不宣称最优 lr**；
> **塌缩区**（1e-4 掉 93–99.9% zero-shot；3e-4 spread ±0.86 且两种退化几何）**只报逐 seed**。
>
> ### 成员交付（我已接受）
>
> `docs/PR_FAIRNESS_FIX3.md`｜`_p295_fullft_extend.py`／`_p296_adapter_init_check.py`／`_p297_divergence_compare.py`
> ｜19 个权重文件｜**CUDA 错误 3 条**全部重跑成功并入最终文件（失败记录留在 `_ext.json` 作过程证据）｜
> **C 项两侧答案**：轨迹**从 epoch 1 即分叉**（排除后期浮点漂移），但最终指标吻合（seed123/999 ΔCG 差 ≤0.0009），
> **仅 seed42 为真离群**；成因**未定**（归档无版本记录、无数据指纹）。
>
> ### 状态
>
> | 稿 | 页数 | 错误 | 未定义 | Overfull |
> |---|---|---|---|---|
> | `main_nc` | **63** | 0 | 0 | 0 |
> | `main_springer` | **45** | 0 | 0 | 0 |
> | 投稿包 | **63** | 0 | 0 | — |
>
> **PR 核验 26/26** ｜ **GPU 已全部释放**（task-7、task-8、审计探针均结束）
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
    if "task-7 收官（19 runs / 7 lr）" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("task-7 收官（19 runs / 7 lr）", "0.8551", "No interior minimum",
              "−0.8153", "8f6bed8"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
