# -*- coding: utf-8 -*-
r"""落账：有效 n 审计 + 论文相变点的不确定度（2026-10-13）。

    python tools\_p44d_record_effective_n.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📉 2026-10-13 03:04 —— 成员自查披露"有效 n"：task-9 的 32 个评估样本**逐位相同**（sd=0）⇒ 有效 n=3 seed；并核出论文相变点附近 sd 与效应同量级**
>
> ### 一、成员的自我披露（它主动报，我逐项核）
>
> 它在"为在 8 GB 卡上跑起来砍了什么"一节里列了 6 条折衷，**其中第 3 条最关键**：
>
> > 空白图 + 单一重复提示 `"Describe this image."`，**32 个评估样本的提示完全相同**
> > ⇒ **逐样本配对 ΔE 的 sd 恒为 0.00** ⇒ 不确定度只能来自 seed 间，即每方案**有效 n = 3**
>
> **✅ 我核实成立**（`outputs/analysis/p3_alloc_runs/main/*.json`）：
> ```
> E0_per_sample         = [23470.845703125] × 32   ← 32 个值逐位相同
> delta_E_per_sample    = [3518.380859375] × 32
> delta_E_per_sample_sd = 0.0
> ```
> `_p43x_common.py :: alignment_energy` 确实返回 `(mean, per_sample)` ⇒ **逐样本值被算出来并存档，且逐位相同**。
>
> ### 二、⚠️ 一处表述收窄（我要求它改）
>
> **"32 个评估样本"是它自己脚本的设置，不是论文的**：
> - 它的 `_p434_alloc_train.py`：`N_TRAIN=32`、`N_EVAL=32`、`eval_texts=[PROMPT_TEXT]*N_EVAL`
> - **论文的 `paper3/scripts/run_training.py`**：`eval_data = processed[:4]`、`compute_E(..., max_n=4)`
>   ⇒ **评估样本是 4 个**（那 4 个 `instruction` **不同**，同图不同文）
>
> ⇒ 已要求措辞改为"**我的主实验**用 32 个评估样本"，**不得写成"论文的"**。
> **这条会直接影响回复信里对论文设置的描述。**
>
> ### 三、论文侧的有效 n：我查了（`tools/_p44c`）
>
> - **论文归档里 `per_sample` 字段 0 个** ⇒ **无法从产物判定论文的有效 n 是 4 还是 1**
>   （`E2_results.json` 每 run 只存**逐 epoch 的均值**）
> - **但论文报的 sd 确实是跨 seed 的**（`E2/extra/sweep` 共 72 run，按 rank 聚合）：
>
> | rank | n | ΔE 均值 | **sd（跨 seed）** | 极差 |
> |---|---|---|---|---|
> | 4 | 6 | −67.67 | 44.54 | 101.5 |
> | **5** | 6 | **−34.83** | **25.75** | 68.0 |
> | **6** | 6 | **+3.92** | **71.78** | **179.5** |
> | 7 | 6 | +65.33 | 142.28 | 300.5 |
> | 8 | 6 | +119.83 | 213.17 | 450.0 |
> | 16 | 6 | +1261.08 | 679.29 | 1781.5 |
> | 20 | 3 | +2859.67 | 286.01 | 529.0 |
>
> **⇒ 在相变点附近（$r=5,6$），跨 seed sd 与效应本身同量级**——
> $r=6$ 的 sd **71.78 > 均值 3.92**。
> **这与 `p3-stats` 的"功效不足、单步不显著"完全一致，是同一条结论的两种独立证据。**
> 且 **E(0) 只有 2 个取值**（3927.0 / 3930.5）覆盖全部 72 run ⇒ **两个数值环境块的又一独立确认**。
>
> ### 四、其余 5 条折衷（我全部接受，要求它单列并与影响方向一起写）
>
> | # | 折衷 | 对结论的可能影响 |
> |---|---|---|
> | 1 | **`batch=1`**（batch=2 峰值 10.28 GiB 超限） | 梯度噪声比 batch>1 大 |
> | 2 | **`n_train=32`、`n_eval=32`、4 epoch** | 远小于正常 SFT 规模 |
> | 3 | **同图同提示 ⇒ 有效 n = 3** | **不确定度只来自 seed 间**（最关键） |
> | 4 | **端到端峰值 9.08 GiB > 8 GB ⇒ 溢出到共享显存** | "**能跑起来但已在超限运行**"，单 run 2.8→8–10 min |
> | 5 | 图像分辨率用处理器默认（**视觉 token 198**） | 与 `p3-downstream` 的 **15 token 差 13×** ⇒ **单 run 耗时不可互证** |
> | 6 | **LLaVA 完全没跑** | 结论仅在 2B 上 |
>
> ### 五、已要求它做的两处改动
>
> 1. **把该节标题从"我砍了什么"扩成"我砍了什么 + 它对统计口径意味着什么"**，
>    并**引用上面那列跨 seed sd** 作为"**论文自身数据也支持'相变点附近不确定度与效应同量级'**"的证据
> 2. **"未胜随机"连"方向"也暂不写**（它建议，我采纳）——
>    稿中现为 **provisional**：写明**可行集只有 15 个不同分配**、**4 个抽样与规则解重合**、
>    **10 个独立样本 obj 26,527–64,825**、**被排除者恰在中位数（44,505）**，**明确不从被污染对照下结论**
>    - ⚠️ **`random_05`（obj 26,527，仅比 Γ-guided 的 25,356 高 4.6%）要单独看**：
>      若它 ΔE 接近 Γ-guided，则**obj 与 ΔE 的关系比假设的松** ⇒ **"随机 vs Γ-guided"的框架本身要重述**
>
> ### 六、⭐ 流程规则再补一条
>
> > **凡报"n = N"，必须标明 N 是「独立样本数」还是「run/seed 数」；
> > 若评估样本之间无任何变化（同图同提示），则有效 n 等于 run 数，不得按样本数报。**
>
> **依据**：本条与"随机对照污染"同源——**都是"把名义结构当成了有效结构"**。
>
> ### 七、状态
>
> - **P3**：**13 页** / 0 错 / 0 未定义；**累计修 21 处**（本条为审计，未改稿；待 P1 与论文侧 n 核实后一并改）
> - **GPU**：`p3-allocation` P1 在跑（30 run ≈4 h）→ 之后 P3（AdaLoRA）
> - **task-9/10/11 全部 complete**
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
    if "成员自查披露" in t and "delta_E_per_sample_sd = 0.0" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("有效 n", "delta_E_per_sample_sd = 0.0", "71.78 > 均值 3.92", "有效 n = 3", "E(0) 只有 2 个取值"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
