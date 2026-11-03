# -*- coding: utf-8 -*-
r"""落账：成员正确反驳了我一次判断（E0 曲线 vs 训练网格）（2026-10-13）。

    python tools\_p456_record_reversal.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔄 2026-10-13 03:39 —— 成员**正确反驳**了我一次判断：$E_0$ 曲线不是训练网格，我那三条理由对它都不适用；我改判为同意**
>
> ### 一、我上次的判断与它的反驳
>
> 我说"**不存在只有 54-token 训练网格才能支持的主张**"，并给了三条理由
> （54≠576；匹配 576 要 4 h；该噪声下补跑只会得到更精致的不可信结果）。**它反驳：有一条，而且不需要训练。**
>
> **主张**：*"真实图 vs 空白图 的**初始化**对齐能量差，是否随视觉 token 预算增长、到论文的 576 会变成多大？"*
>
> **它的三条反反驳**：
> 1. **$E_0$ 只需一次前向 ⇒ 对给定输入确定性 ⇒ 无 seed 噪声** ⇒ 我第 3 条**不适用**
> 2. **分钟级可扫到 576** ⇒ 我第 1、2 条**不适用**（不需要 4 h 训练）
> 3. 因此这是对**论文操作点（576 token）的直接测量**，不是外推
>
> **⇒ 我接受反驳。我上次把它误当成了"训练网格"。**
>
> ### 二、我核实了它的曲线（`tools/_p456` 前的核验）
>
> | 样本集 | 15 token | 54 token |
> |---|---|---|
> | `train_sel`（n=16） | `E0_real` **21771.7** ｜ gap **+3.10%** | （来自训练档）**+50.9%** |
> | `test`（n=4，held-out） | `E0_real` 19211.9 ｜ gap **+18.55%** | `E0_real` **9439.5** ｜ gap **+139.16%** |
>
> **⭐ 方法学自证（比结论更重要）**：15 token 下 `E0_real = 21771.699279785156`
> vs 归档冻结基线 **21771.6993** ⇒ **逐位一致（差 <1e-3）**
> ⇒ **它的扫描与前向口径与训练档完全相同**，因此曲线可信。
>
> **机制**：`E0_real` 随预算**大幅下降**（train_sel 21752→14718；test 19212→9440），
> 而 `E0_blank` **几乎不动**（22373→22207；22776→22576）
> ⇒ **"真实图随 token 增多而越来越对齐，空白图始终差"** ⇒ **blank 协议与被批评点同源的直接证据。**
>
> ### 三、✅ 它自查并修正了一处会**被审稿人打掉**的表述
>
> 它上一条说"15 token 差 **2.9%**，54 token 差 **50.9%**"，**并暗示这是一般量级**。
> 现在两个独立样本集测下来：**15 token 下 3.10%（train_sel）与 18.55%（test）—— 差 6 倍**。
> ⇒ **不能写单一百分比**，只能写**方向 + 两个独立样本集**：
> > *"on a fixed sample set, increasing the visual token budget from 15 to 54 increased the
> > real-vs-blank initialization-energy gap substantially (train_sel: +3%→+51%; held-out test:
> > +19%→+139%); the absolute level is sample-dependent, but the direction replicates on two
> > independent sample sets."*
>
> **我采纳该表述（不写任何单一百分比）并通知了 `p3-allocation` 引用时照此。**
>
> ### 四、我提出的合并（避免重复的 GPU 会话）
>
> - **`p3-allocation`** 想测：198-token 下 blank vs real 的 $E_0$（它已有 blank = 23470.846）
> - **`p3-downstream`** 想测：gap 随预算到 576 的曲线
>
> **两者是同一类测量（只前向、$E_0$），一次扫描可同时满足。**
> 已向 `p3-allocation` 提出：**由它判断时机、由它通知起跑、两者自行交接；它若判断插入代价高可直接拒绝**；
> 被拒则 `p3-downstream` 在 CPU 上跑到 ~370 token 并把"未达 576"写进边界。
> **纪律照旧**：**P1 优先，只在自然缝做，不主动抢。**
>
> ### 五、状态
>
> - **P3**：**13 页** / 0 错 / 0 未定义；**累计修 22 处**
> - **P1**：**2/10 方案完成中**，剩 **26 run ≈3.2 h**
> - **已批准的两项小测量**：198-token blank/real $E_0$ 锚点 + 预算曲线到 576（**≈2 min，只前向**）
> - 两个归档按 `split` 分开存（`train_sel` / `test`）**避免混不同总体** —— 引用必须带 `split` 名
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
    if "正确反驳**了我一次判断" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("正确反驳", "21771.699279785156", "+139.16%", "18.55%", "不写任何单一百分比"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
