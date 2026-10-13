# -*- coding: utf-8 -*-
r"""落账：GPU 裁量（选项 C），并把裁量权交给代价承担方（2026-10-13）。

    python tools\_p44e_record_gpu_call.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **⚖️ 2026-10-13 03:10 —— GPU 排期裁量：选 C（最小版 4 run ≈5 min），但**裁量权交给代价承担方****
>
> ### 一、`p3-downstream` 的请求（它自己把账算清，不替我做决定）
>
> 它要一段 **~5–10 min** 的 GPU 窗口，跑 `--max-pixels 50176`（224×224，约 60 token），
> 目的是补掉它自己标注的洞：**当前实验只用 15 visual token/样本，而这本身就是"简化视觉输入"，
> 与被批评的 blank images 同源**。
>
> | 方案 | 收益 | 代价 |
> |---|---|---|
> | **A. 等 `p3-allocation` 的窗口 1**（P1 完 ≈07:04） | 同样跑完 | **空等 ~4 h 墙钟** |
> | **B. 让 ~10 min** | 立刻跑完 | 它损失 1 个 run（≈9 min） |
> | **C. 最小版**（`ranks{4,16}×{real,blank}×1 seed` = **4 run ≈5 min**） | 仍能回答**"符号是否还一致"**（二值问题） | 约 5 min |
> | **D. 不做** | §3.3 的限制如实留着 | 无 |
>
> **它建议 C**，理由：该检验的**唯一目的是验"real 全正 / blank 全负"这个二值符号模式**是否仍成立，
> **1 个 seed 就够证伪**；3 seed 只是把"一致性"也量化，属锦上添花。
>
> ### 二、我的裁量
>
> **选 C**，并补一条它没算的：**A 的真实成本不是 4 h 墙钟，
> 而是"用 4 h 挡住一个 5 min 的检验"**。且 `p3-allocation` 的断点续跑
> **本来就是为这种插入设计的**（每个 run 的 JSON 单独落盘）。
>
> ⭐ **但我把"代价"那一侧的裁量权交给 `p3-allocation`**：
> - **请它用实测判断**在 run 边界让出 5 min 是否真的只损失"当前 run 进度"；
>   **若总代价 ≈14 min 或风险高，直接拒绝**
> - **由它决定插入时机、由它通知 `p3-downstream` 起跑、两者自行交接**（不再经过我）
> - **我明确声明：这是我的判断，不是它的实测——它若有实测显示代价更大，我就撤回请求**
>
> ### 三、纪律边界（三者都遵守）
>
> - **`p3-downstream` 不主动抢**（它遵守）；**由我向 `p3-allocation` 提出**
> - **`p3-allocation` 的 P1 优先**：它是 R3.21 的核心实验，30 run，**能改变结论方向**
> - **插进去的检验写独立归档** `p3d_qwen_ranksweep_mp50176.json`，**不污染主结果**；
>   "**同一归档不许混不同预算**"守卫**已从 warning 改成硬失败**（`raise SystemExit`）
> - **若走 A 且会话结束前未跑成** → 记为**待办**（§8 注明"命令已就绪"）
>
> ### 四、我采纳的两处成员做法
>
> 1. **`p3-downstream` §4.1 的措辞**：*"在 Qwen2-VL-2B 上未复现 `uniformly negative`，
>    **不是**'稿件错了'"*，并注明"看起来是 7B 或另一套分块口径，**本机无 7B 权重、无法核实**"
>    —— **"证据不足以判定别人错时只说未复现"，这是正确做法，我落笔时用同一口径**
> 2. **它的自查**：`real`/`blank` 是**确定性配对**（同 rank/同 seed），
>    **不是从池子里抽的随机对照** ⇒ **不存在"与规则解重合"的风险**；
>    它把"**构造对照时必须先验证它不与任何规则解重合**"记进做法 —— 与"随机对照污染"那条纪律同源
>
> ### 五、状态
>
> - **P3**：**13 页** / 0 错 / 0 未定义；**累计修 21 处**
> - **GPU**：`p3-allocation` P1 在跑（`_p434_alloc_train.py`，30 run ≈4 h）
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
    if "裁量权交给代价承担方" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("裁量权交给代价承担方", "max-pixels 50176", "p3d_qwen_ranksweep_mp50176", "硬失败"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
