# -*- coding: utf-8 -*-
r"""落账：分辨率稳健性检验证伪 + 决定不补网格（2026-10-13）。

    python tools\_p452_record_falsification.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🧪 2026-10-13 03:25 —— `p3-downstream` 自己提议的稳健性检验**证伪了它自己的核心结论**；换来一条更强的；我决定不补网格**
>
> ### 一、证伪（我已独立复核，`tools/_p450`）
>
> | `max_pixels` | token | real $\\Delta E_{\\text{train}}$ | blank $\\Delta E_{\\text{train}}$ | 配对 $\\text{blank}-\\text{real}$ |
> |---|---|---|---|---|
> | 16384 | **15** | **21/21 正**（+188.8…+499.4） | **0/21 正**（−541.4…−114.0） | **21/21 负**（−699.0） |
> | **50176** | **54** | **0/2 正**（−554.2, −471.2） | 0/2 正（−188.5, −49.1） | **0/2 负**（**+393.9**） |
>
> ⇒ **"$\\Delta E$ 的符号由图像条件决定"只在 15 token 下成立** ⇒ **成员撤回该表述**（训练确实发生：loss 3.04→1.85）
>
> ### 二、⭐ 换来一条更强、更该写的（**R3.13 的真正答案**）
>
> | token | real $E_0$ | blank $E_0$ | 差 |
> |---|---|---|---|
> | 15 | 21,752.7 | 22,373.3 | **+2.9%** |
> | **54** | **14,717.8** | 22,207.2 | **+50.9%** |
>
> ⇒ **把视觉 token 预算从 54 压到 15，"真实图 vs 空白图"的差别从 50.9% 塌到 2.9%**
> ⇒ **blank 协议的问题不只是"用空白图"，而是"在低视觉 token 预算下，空白图与真实图本来就难分"**
> —— **而该预算在论文里从未报告、也从未变动** ⇒ **目标函数与真实多模态内容的关系不可解释：换预算符号就反过来。**
>
> ### 三、同时撤回一处**差点写成架构结论的伪影**
>
> 原表 *"CLIP 双塔 real 为负 / Qwen 解码器 real 为正 ⇒ 符号是架构相关的"* ——
> **把 Qwen 提到 54 token 后 real 也变负、与 CLIP 一致**
> ⇒ **那处"架构不一致"很可能是 token 预算伪影，不是架构结论**。
> **若不撤回，这会是一条会被审稿人打死的错误架构主张。**
>
> ### 四、唯一稳健、可放心用的一条
>
> **"$r\\in[1,16]$ 上不存在 $\\Delta E$ 的符号翻转"在两档预算下都成立**
> （15 token：各条件内 7/7 不变；54 token：2/2 也不翻）
> ⇒ **R3.14 的答复用这一条**；**R3.13 用"预算敏感"那条**（不依赖符号）。**稿中已按此分工。**
>
> ### 五、✅ 已改稿（`tools/_p451`，P3 编译 **13 页 / 0 错 / 0 未定义**）
>
> 撤回了 *"the sign is set by the image condition and not by rank at all"*，
> 换为：**"we withdraw the claim that the sign of $\\Delta E$ is determined by the image condition;
> it is determined by the image condition *at this budget*"** +
> **54.9% vs 2.9% 的预算敏感量化** + **"budget is nowhere reported or varied"** +
> **架构伪影的撤回**；并保留稳健的 rank 结论。
>
> ### 六、我决定**不补** 54-token 完整网格（25 min GPU），理由
>
> `p3-allocation` 复核源码发现**三方 token 预算全不同**（我核实成立）：
>
> | 来源 | image token/样本 |
> |---|---|
> | **论文 `run_training.py:237`** | **576**（硬编码） |
> | `p3-allocation` 的实验 | **198** |
> | `p3-downstream` 两档 | **15** / **54** |
>
> **⇒ 论文的操作点是 576，比 54 还高 10.7×。** 三条理由：
> 1. 补到 3 seed × 7 rank @ 54 只能建立"**54 token 下的新规律**"，
>    而 **54 不是论文预算** ⇒ **对答复 R3.13 无增量价值**
> 2. 要真正匹配论文预算得跑 **576**（≈10× 时间，**≈4 h**），**而卡在 P1 手上**，**P1 能改变另一条主张**
> 3. **更根本**：P1 数据显示 **`random_01` 同分配内 seed 极差 10,913** ——
>    **在该噪声水平下，2 seed 与 3 seed 的"新规律"都不可信** ⇒ **补跑只会得到更精致的不可信结果**
>
> ⇒ **按"证伪 + 边界写明"交付**（**已请成员复核我的判断**：若存在某主张非 54-token 网格不可，我立刻改主意）
>
> ### 七、成员的两处**字节级纠正**（我视为正面贡献）
>
> 1. `p3-allocation` 说它的归档中文乱码 → **按字节核是合法 UTF-8**（`_p471` 11/11），
>    是 **UTF-8 被按 GBK 读的显示问题** —— **正是 AGENTS.md"判编码先看字节"那条规矩**
> 2. 说 `E_train_epochs`(4) 与 `loss_epochs`(3) 长度不一致是口径错 → **设计如此**（初始点 + 每 epoch），已加自检
>
> ### 八、门禁与状态
>
> - `_p466` **66/66 通过**；其中一条**专门锁死本次证伪**（若归档变回"成立"直接 **FAIL**，强迫改回报告）
> - `_p471` 字节级编码校验 **11/11**
> - **P3**：**13 页** / 0 错 / 0 未定义；**累计修 22 处**
> - **GPU**：归 `p3-allocation` 续 P1（30 run ≈4 h）→ 之后 P3（AdaLoRA）
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
    if "证伪了它自己的核心结论" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("证伪了它自己的核心结论", "50.9%", "2.9%", "576", "累计修 22 处"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
