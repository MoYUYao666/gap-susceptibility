# -*- coding: utf-8 -*-
r"""落账：P1 首个方案完成 + E0 口径 + 2 min 补充批准（2026-10-13）。

    python tools\_p453_record_p1_first.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📊 2026-10-13 03:28 —— P1 首个方案完成：同分配内 seed 极差 = 方案间差的 2.62×；论文协议确认为 blank**
>
> ### 一、`random_01` 完成（我已核，逐格一致）
>
> | seed | ΔE | ranks |
> |---|---|---|
> | 42 | **+839.0** | {4,7,1,7} |
> | 123 | **+11751.8** | {4,7,1,7} |
> | 456 | **+3780.3** | {4,7,1,7} |
>
> 均值 **+5457.0** ｜ sd **5646.3**（我按 $n-1$；成员报 5574.0，差在 ddof）｜ **极差 10,912.9**
> **极差 / 方案间差（$+6413.4-+2241.0=4172.4$）= 2.62×**
>
> ### 二、⭐ 成员新增第 4 档判据（我认可，且这是我要求的）
>
> `_p458` 原有三档之外加 **`UNDERPOWERED_TO_DISTINGUISH`**，**判据写死**：
> **最大同分配内 seed 极差 ≥ 方案间均值差 ⇒ 判功效不足**（**不看 p 值、不硬选三档之一**）。
> 用部分数据试跑已触发：*最大同分配内极差 10,912.9 ｜ 方案间差 4,054.4 ｜ 比值 2.69×*。
> **它避免了我用 $p=0.024$ 写一个站不住的因果主张。**
>
> ### 三、✅ 论文协议确认为 **blank images**（我核源码）
>
> `paper3/scripts/run_training.py`：
> - **L27** `--images-dir ... default=None`
> - **L240–244** `if args.images_dir: ... else: pv = pixel_vals.squeeze(0)`（**固定像素值 = 空白图**）
> - **L401/L403** 仅在提供 `--images-dir` 时给 tag 加 `_imgs`；**归档文件名无 `_imgs`**
>
> ⇒ **论文全部 run 走 blank 分支** ⇒ **成员的 ΔE 与论文可比，与真实图文实验不可比**（它的判断成立）。
>
> ### 四、🔴 我核出的 E0 口径事实（决定 ΔE 的可解释性）
>
> 论文 `E2_results.json`（**72 run**）：**`E(0)` 只有 2 个取值**（3927.0 / 3930.5）。
> ⇒ **论文的 $E_0$ 在同一环境块内几乎恒定**（初始化相同 + blank 像素固定）
> ⇒ **$\\Delta E$ 的差异完全来自"训练把 $E$ 推了多远"，不是起点不同** ✅
>
> **已要求成员报**：它 15 run 的逐 run `E_0` + 是否随方案/seed 变化 + 变化幅度相对 ΔE 的比例。
> **若其 $E_0$ 近似恒定** ⇒ 其 ΔE 是干净的"训练位移"，可比性更强；
> **若有明显散布** ⇒ ΔE 里混了初始化差异（**必须报**）。
>
> ### 五、✅ 批准 2 min 补充（它提议，我加了一条）
>
> **它提议**：同一 **198-token** 预算下**只测不训**，报 **blank $E_0$ vs real $E_0$**，
> 给它的 ΔE 一个"real/blank 差多少"的锚点，**避免别人拿它与真实图文的数直接比**。**批准（2 min）。**
> **我加的一条**：顺带报 15 run 的逐 run $E_0$（**不用额外跑，从已有归档读**）——见上。
>
> ### 六、⚠️ 我要求它写进报告的一条自我限定（比多跑任何 run 都有价值）
>
> > 在本协议下，**同一分配的 seed 间极差可达 10,913，超过所比较的方案间差异（4,172）**。
> > 因此：**(i) 单次运行的 ΔE 不可用于比较方案；(ii) 本实验的 $n=3$ 不足以区分表中所列方案的均值；
> > (iii) 能稳健主张的只有 worst-case 与同秩方差两条。**
>
> **写清这条，让审稿人看到作者自己知道该实验的判别力边界。**
>
> ### 七、成员的两处自我更正（我记账）
>
> 1. **编码误判**：它说对方的归档"中文乱码" → **按字节复核是合法 UTF-8**（3065 B / 0 NUL / 无 BOM / 严格通过），
>    乱码是**它用 PowerShell `Get-Content` 读**造成的（此机默认非 UTF-8）。
>    **它自认"犯了 AGENTS.md 专门警告过的那条"并已更正** —— 处置正确
>    （我本阶段也犯过同型错：编码损伤扫描第一版判据过宽，**误报 43+ 个文件**）
> 2. **`E_train_epochs`(4) vs `loss_epochs`(3)** 是**设计如此**（初始化点 + 每 epoch），非口径错
>
> ### 八、状态
>
> - **P3**：**13 页** / 0 错 / 0 未定义；**累计修 22 处**
> - **P1**：**1/10 方案完成**（`random_01`），剩 **27 run ≈3.4 h**
> - **GPU**：归 `p3-allocation`
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
    if "P1 首个方案完成" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("P1 首个方案完成", "2.62", "UNDERPOWERED_TO_DISTINGUISH", "3917", "E(0)` 只有 2 个取值"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
