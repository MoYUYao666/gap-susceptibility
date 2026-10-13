# -*- coding: utf-8 -*-
r"""落账：随机池含负值 run + 池层面功效不足（2026-10-13）。

    python tools\_p459_record_pool.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📉 2026-10-13 04:08 —— 随机池出**负值 run**（随机分配**可以**改善对齐）；池 sd 6,937 > 方案间差 4,172 ⇒ 两层都判功效不足**
>
> ### 一、P1 第 3 次 ping：新增逐 run（我已核，全部对上）
>
> | 方案 | 逐 run ΔE | 均值 | 同分配内极差 |
> |---|---|---|---|
> | `random_02` | +4243.3 / +4559.6 / **+18574.7** | **+9125.9** | **14,331.4** |
> | `random_03`（1/3） | **−1799.5** | — | — |
>
> **独立随机池 n=7**：
> ```
> mean=+5992.8  sd=6937.4  min=−1799.5  max=+18574.7
> 排序: [−1799.5, 839.0, 3780.3, 4243.3, 4559.6, 11751.8, 18574.7]
> Γ-guided 均值 +2240.9 ｜ 池内更低 2/7 = 28.6%
> |Γ-guided − uniform| = 4172.5 ｜ 池 sd 6937.4 > 4172.5 ✅
> ```
>
> ### 二、✅ 负值 run 是**健康 run**（我核了健康度，不是异常）
>
> `random_03__seed42`：`ok=True`｜`skipped_nonfinite=0`｜**loss 单调降 1.550→1.405**｜
> **E 轨迹 23470.8 → 21464.5 → 20742.4 → 21760.2 → 21671.4**（单调下降）｜预算断言通过｜`ranks={4,1,7,1}`
>
> **⇒ 结论成立：随机分配可以改善对齐（$\\Delta E < 0$）。**
> **对论文的意义**：它**削弱**"Γ-guided 能避免伤害"的叙事（随机也能），
> 但**支持更诚实的一条**：**"对齐能量对分配敏感，而 Γ 的排序只是众多可行分配中的一种启发式"**。
>
> ### 三、⚠️ 方差那条我降为"待检验的观察"（我要求成员这样写）
>
> `Γ-guided sd = 1290.6` vs `池 sd = 6937.4`（**5.38×**）看起来支持"方差更小"，**但三条理由不能现在下结论**：
> 1. **n=7**，且池内含 **`max=+18574.7` 极端离群**（它单独把池 sd 抬高）
> 2. **Γ-guided 只有 n=3** —— 3 点 sd 极不稳定（本项目已两次踩到"小数样本 sd 不可信"）
> 3. **Levene 检验要等池齐**，且方差齐性检验**对离群极敏感**
>
> **⇒ 要求写成**：*"the $\\Gamma$-guided arm's spread (sd 1291 over 3 seeds) is smaller than the random
> pool's (sd 6937 over 7 runs), but with 3 seeds and an extreme draw in the pool this comparison is not
> yet informative; we report the Levene test once the pool is complete and do not claim a variance
> advantage before then."*
>
> ### 四、⭐ 池层面与单方案层面**都**判功效不足（两层一致）
>
> | 层面 | 该层面的离散 | 方案间差 | 判定 |
> |---|---|---|---|
> | **单方案内（seed 极差）** | **10,913–14,331** | 4,172 | **UNDERPOWERED** |
> | **池 sd** | **6,937** | 4,172 | **UNDERPOWERED** |
>
> **⇒ 两层都指向同一判定**：**均值比较在该噪声水平下没有判别力。**
>
> ### 五、E0 锚点表述（成员已按我要求写，我核认可）
>
> - blank 侧：它 **23470.85** vs `p3-downstream` **22696.9**，差 **3.4%** ⇒ **blank 侧对文本集不敏感** ✅
> - ~190 token 下喂真实图时 `E0` 只有 blank 基准的 **1/2.48** ✅
> - 表述：*"本实验的 ΔE 一律是 **blank-image 基准**下的量；同一模型在 ~190 token 下喂真实图时，
>   初始化能量只有该基准的 **1/2.48**。"* ✅
> - **限定**：其 ΔE 与**论文可比**（论文也走 blank）、**与真实图文不可比**；
>   **论文 $E_0$ ≈ 3927–3931 是 576 token 下的数，不可与其 23470 直接比数值**
> - **⚠️ 我补的一条归属纪律**：**论文未报**它自己的 real/blank 差（它只跑 blank）
>   ⇒ **不得说"论文的 gap 是多少"**，只能说"**论文未报该差；我们测出在论文操作点上它是 3.09×**"。
>   **谁测的、在什么预算下、哪一批样本，必须写清。**
>
> ### 六、状态
>
> - **P3**：**14 页** / 0 错 / 0 未定义；**累计修 23 处**
> - **P1**：**9/30 run 完成**（`random_01` 满 3、`random_02` 满 3、`random_03` 1/3，其余待跑），剩 **21 run ≈2.6 h**
> - **P2 已砍**；**P3（AdaLoRA）排在 P1 之后**
> - **任务板**：**12/12 completed**（`task-3` 已标注"被 `task-5` 取代"并保留记录）
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
    if "随机池出" in t and "−1799.5" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("−1799.5", "+18574.7", "6,937", "5.38", "12/12 completed"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
