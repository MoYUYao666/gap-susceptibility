# -*- coding: utf-8 -*-
r"""落账：三方 token 口径 + 功效不足（2026-10-13）。

    python tools\_p44f_record_power.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📐 2026-10-13 03:15 —— 三方 token 口径全不同；同分配内 seed 极差（10,913）**大于方案间差异** ⇒ 判据须加"功效不足"档**
>
> ### 一、成员复核我的两处指正 —— 全部成立（我逐行核源码）
>
> | 事实 | 出处 | 核实 |
> |---|---|---|
> | 论文**评估 4 个样本** | `run_training.py:256 eval_data = processed[:4]`、`:262 max_n=4` | ✅ |
> | 那 4 条**文本各不相同** | `:234 f"USER: {s['instruction']}..."` | ✅ |
> | **CE 覆盖全部 token（无 mask）** | `:249 "labels": input_ids[0].clone()` | ✅ |
> | 论文每样本 **576 image token** | `:237 torch.full((1, 576), ...)`（**硬编码**） | ✅ |
> | 论文 `max_length=1024` 文本截断 | `:235` | ✅ |
>
> ⇒ 成员的 `sd = 0.00` 是**它自己 32 个同图同提示设置的产物**，**不是论文的性质**。
> 它已加自我约束：**"不得写成'论文用 32 个'或'论文的有效 n 是 1'"** —— **正确**。
> 且它明确：**论文归档 `per_sample` 字段 0 个 ⇒ 无法从产物判定论文有效 n 是 4 还是 1
> ⇒ 这只能写成"口径需澄清"，不可当作缺陷断言** —— **这正是本项目"证据不足时只说未复现"的口径。**
>
> ### 二、⭐ 三方 token 预算全不同（新发现的跨实验不可比性）
>
> | 来源 | image token/样本 | 备注 |
> |---|---|---|
> | **论文** `run_training.py` | **576**（硬编码） | 另有 `max_length=1024` 文本截断 ⇒ 总序列 ≈1600+ |
> | **task-9**（成员实验） | **198**（Qwen2-VL 处理器默认） | — |
> | **task-10**（`p3-downstream`） | **15**（`max_pixels=16384`） | — |
>
> ⇒ **凡跨实验引用耗时 / 显存 / 能量，都不可直接比。**
> **引用纪律（采纳为项目规则）**：必须同时带 `max_pixels`（或 token 数）、`n_train`、`epochs`、`batch`。
>
> ### 三、🔴 决定性的新数：**同一分配内 seed 极差 = 10,912.9**
>
> 成员 P1 前两个 run（`random_01`，`ranks` **逐位相同**）：
>
> | seed | ΔE |
> |---|---|
> | 42 | **+839.0** |
> | 123 | **+11751.8** |
>
> **我完成的全部 17 run**：
>
> | 方案 | 均值 ± sd | 极差 |
> |---|---|---|
> | `corner` | +3607.2 ± **513.6** | 1015.6 |
> | **`exp`（Γ-guided）** | **+2241.0 ± 1290.6** | 2452.5 |
> | `inverse` | +2225.2 ± **1763.5** | 3331.9 |
> | `random_00` | +1103.1 ± 1043.2 | 2084.8 |
> | **`random_01`** | **+6295.4 ± 7716.6** | **10,912.9** |
> | `uniform` | +6413.4 ± 1552.3 | 2714.6 |
>
> **全池 17 run：均值 +3491.8 ｜ sd 3006.4 ｜ 范围 83.8 … 11751.8**
>
> **⇒ 同一分配内的 seed 间极差（10,913）**远大于**方案间差异**（`exp` +2241 vs `uniform` +6413 = **4,172**）**
>
> **⇒ 三条直接后果**：
> 1. **"Γ-guided 优于 uniform（p=0.024，n=3）"必须加限定**：同分配内 seed 极差可达方案间差异的 **2.6 倍** ⇒ **该 p 值不可靠**
> 2. **"vs 随机"在 n=3 下无判别力**（随机池自身 sd **7,717** 已超过所有方案间差异）
> 3. **⇒ P1~P3 跑完后最可能的诚实结论**：**"在本机可行的 n 与规模下无法区分这些方案；
>    能稳健主张的只有 worst-case 与同秩方差两条"**
>
> ### 四、⭐ 新增判据档（我要求成员加）
>
> 在 `_p458` 原有的三档
> （`GAMMA_NOT_BETTER_THAN_RANDOM` / `INDISTINGUISHABLE_BUT_LOWER_VARIANCE` / `INDISTINGUISHABLE`）之外，
> **加第四档 `UNDERPOWERED_TO_DISTINGUISH`**：
> **判据：若池内同分配 seed 极差 ≥ 方案间差异，则判定为功效不足。**
> **这比强行在三档里选一个更诚实。**
>
> ### 五、成员让卡的处置（我核过，正确）
>
> 停在 `random_01__seed456` 的 epoch 1 开头、**只废约 1 min**、
> 已完成的 `seed42/123` **不重跑**（断点续跑）、净代价 ≈ **6.5 min**。
> **它用自己的实测做了代价判断** —— 这正是我把裁量权交给它的原因。
>
> ### 六、状态
>
> - **P3**：**13 页** / 0 错 / 0 未定义；**累计修 21 处**（待 P1 与论文侧 n 口径核实后一并改）
> - **GPU**：`p3-downstream` 用 5 min 窗（`--max-pixels 50176`）→ 归还 `p3-allocation` 续 P1
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
    if "同分配内 seed 极差" in t and "10,912.9" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("10,912.9", "UNDERPOWERED_TO_DISTINGUISH", "576", "198", "15（`max_pixels=16384`）"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
