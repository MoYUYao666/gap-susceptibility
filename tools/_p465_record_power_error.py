# -*- coding: utf-8 -*-
r"""落账：我的功效算错（漏因子 2）+ P1 完成 + 归档键名漂移（2026-10-13）。

    python tools\_p465_record_power_error.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🧮 2026-10-13 07:37 —— P1 完成（30/30）；成员拒绝照抄我的**错数**，我复算确认**是我漏了因子 2**（n=87 → 正确 20–43）**
>
> ### 一、🔴 我的第 20 个错：功效公式漏了因子 2
>
> 我在 07:19 写 *"$n \\approx 2\\sigma^2(z_{1-\\alpha/2}+z_{1-\\beta})^2/\\Delta^2 \\approx \\mathbf{87}$"*，
> **成员复算不出 87**，明确写 **"我不写一个自己复算不出的数"**（项目铁律的正面执行）。
>
> **我复算后确认它是对的**（`tools/_p464_power_from_runs.py`）：
>
> | σ | **正确**（$K=2(z+z)^2=15.6978$） | 我误用的（$K=(z+z)^2=7.8489$） |
> |---|---|---|
> | **4771.2**（池 sd，n=30 最终） | **20.5** | 10.2 |
> | **6937.4**（n=7 时最保守） | **43.4** | **21.7** |
>
> **⇒ 正确所需 $n$ = 20–43 每方案 ⇒ 成员报的 "21–44" 正确；我报的 87 作废。**
> **错因**：我引用的 σ 是 **4771**（不是我以为的 6937），**但推导时把 $K$ 少乘了 2**
> —— 而 $87 \\approx 2\\times43.4$，**表象上像"σ 取大了"，实际是"公式少了因子 2"**。
> **教训：报出任何推导数之前必须自己代入复算一遍。**
>
> ### 二、⭐ 成员拒绝照抄 Lead 的错数 —— 本条值得写进复盘
>
> **它完全有理由直接采用我的 87（我是 Lead），但它在归档里复算、发现对不上、宁可不写、并明确要求我核对。**
> **这是「所有数据必须要可复现有来源」的实际执行**，也是本阶段第 6 次"队友影响我的判断"。
>
> ### 三、🔴 顺带核出一类"来源失效"：归档键名漂移
>
> 成员引 `p3_alloc_results.json :: per_plan.*.delta_E.mean`（exp / uniform），
> **但该文件的 `per_plan` 现在只含 10 个随机方案** —— 规则方案已移出。
> **⇒ 出处必须写成逐 run 明细的 glob**（键名稳定）：
> ```
> outputs/analysis/p3_alloc_runs/main/{exp_beta_paper_0.137,uniform}__seed{42,123,456}.json :: delta_E
> ⇒ exp +2240.9648 ｜ uniform +6413.4395 ｜ Δ = 4172.4746
> ```
> **⚠️ 聚合文件会被后续合并改动 ⇒ 指向它的字段路径会静默失效。** 已要求成员改。
>
> ### 四、P1 最终池统计（**30 个独立随机 run = 10 方案 × 3 seed**，我已核，全部对上）
>
> ```
> 池 n=30: mean=+3347.4  sd=4771.2  min=−1987.7  max=+18574.7
> 负值（随机分配改善对齐）: 7/30
> Γ-guided 均值经验分位: 16/30 = 53.3%
> 池 sd(4771.2) vs Δ(4172.5) ⇒ 噪声/信号 = 1.14
> Welch t=−0.965 p=0.3573 ｜ Mann-Whitney U=41.0 p=0.8365 ｜ Levene W=1.335 p=0.2567
> 判定: UNDERPOWERED_TO_DISTINGUISH
> ```
>
> **同预算断言**：`measured_n_trainable_params = [7237632]`（唯一值），**45 run 全部逐位相同、0 失败** ✅
>
> **定稿依据（我认可）**：
> 1. **`uniform` 是均值最差者之一（+6413.4）** ⇒ "Γ-guided 优于 uniform" **仍成立**（但受功效限制）
> 2. **Γ-guided 与同预算随机分配不可区分**（分位 **53.3%**、Welch p=0.36、MWU p=0.84）⇒ **"未胜随机"成立**
> 3. **池 sd（4771）> |Γ-guided − uniform|（4172）** ⇒ **两层都判 `UNDERPOWERED`**
>
> **⚠️ 我核出一处措辞要改准**："10 个随机方案里有 **2 个**均值优于 Γ-guided" ——
> 实际是 **3 个**：`random_03`（−1450.3）、`random_05`（−222.2）、**`random_11`（+1741.3）**。
> **（我先前快照里 `random_11` 只有 n=1，现在 n=3 均值 +1741.3 < +2241.0）已要求成员核对后写准。**
>
> ### 五、方差那条已撤回"更小"（成员照做）
>
> 报告 §4.3e(ii-b) 写成"**待检验、且可能不成立**"，并列出三条理由
> （n=3、极端离群 +18574.7、**7/28 负值 run ⇒ 池横跨改善与损伤、近似双峰**）。回复信英文按我给版本落地。
>
> ### 六、P3（AdaLoRA）进度：成员修掉一个真 bug
>
> `peft` 校验 `tinit < total_step − tfinal`；原 `tinit=100, tfinal=400, total_step=400` 直接 `ValueError`。
> 现按真实步数（`32/1×4 = 96`）取 `tinit=19, tfinal=38`，**并显式复现该校验以提前失败**。
> **"提前失败"优于"跑到一半崩"** ⇒ 已要求写进报告的"修掉的 bug"清单。
>
> ### 七、状态
>
> - **P1 ✅ 完成**（30/30）｜**P3（AdaLoRA）** 07:37 起跑｜**P2** 排在 P3 之后
> - **P3 稿件**：**14 页** / 0 错 / 0 未定义；**累计修 23 处**
> - **P3 修订包**：`SUBMISSION/P3_PRL_revision/`（12 文件 / 754 KB）已备份，`文件地图.md` 已登记
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
    if "我漏了因子 2" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("我漏了因子 2", "20.5", "43.4", "53.3%", "归档键名漂移"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
