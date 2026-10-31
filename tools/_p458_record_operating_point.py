# -*- coding: utf-8 -*-
r"""落账：论文操作点（576 token）的直接测量 + 页数预警（2026-10-13）。

    python tools\_p458_record_operating_point.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🎯 2026-10-13 03:54 —— **直达论文操作点（576 token）的直接测量**：blank 的 $E_0$ 是 real 的 **3.09×**；GPU 只用了 30 s**
>
> ### 一、主曲线（`p3d_e0_vs_token_budget_train_sel_n16.json`，**device=cuda**，n=16，只前向）
>
> | max_pixels | tokens | $E_0^{\\text{real}}$ | $E_0^{\\text{blank}}$ | gap |
> |---|---|---|---|---|
> | 16384 | 15.3 | **21751.8** | 22400.1 | **+2.98%** |
> | 50176 | 54.6 | **14717.8** | 22313.2 | **+51.61%** |
> | 156800 | 188.4 | **9149.9** | 22696.9 | **+148.06%** |
> | **802816** | **595.2** | **7472.3** | **23117.5** | **+209.37%** |
>
> **⇒ $E_0^{\\text{real}}$ 单调降 66%（21752→7472）；$E_0^{\\text{blank}}$ 全域 <5%（22400→23118）**
> **⇒ 论文操作点（595≈576）blank/real = 23117.5 / 7472.3 = 3.09×**
>
> **成员的关键洞察**：**$E_0$ 只需一次前向 ⇒ 对给定输入确定性 ⇒ 无 seed 噪声** ⇒
> **可以分钟级扫到 576**，**不需要 4 h 训练** ⇒ **这是直接测量而非外推**。
> **这意味着我此前"没有主张只有训练网格能支持"的判断被正确反驳**（见上一条）。
> **GPU 只用了 30 s**（03:53:41），**卡已还 `p3-allocation`**。
>
> ### 二、机制（成员建议作为主句，我采纳）
>
> **`E0_real` 随 token 增多单调大幅下降（21752→14718→9150→7472，共降 66%），
> 而 `E0_blank` 几乎不动（22400→22313→22697→23118，全域 <5%）**
> ⇒ **"真实图越给足 token 就越对齐；空白图无论给多少 token 都停在同一个高能量上。"**
>
> ### 三、✅ 已写进 P3（`tools/_p457`，编译 **14 页 / 0 错 / 0 未定义**）
>
> 新增 *The probe measured at the paper's own operating point* 段，含：
> **4 点曲线**、**66% 下降**、**blank <5% 不变**、**论文操作点 3.09×**、
> **"a blank image is not a neutral stand-in … the objective being optimised is therefore not
> the objective a real multimodal input induces"**、**两条边界**、**"no seed noise"**。
>
> ### 四、两条边界（成员留档，**含一条负例**）
>
> 1. **绝对百分比依样本集而定**：15 token 下 train_sel（n=16）**+2.98%** vs held-out test（n=4）**+18.55%**（差 6 倍）
>    ⇒ **只引"同批样本的趋势"，不引单一百分比**
> 2. **子样本会翻转趋势（负例留档，成员明确不删）**：同一 test 划分取 **n=2** 时，
>    gap 15 tok **+122.25%** → 54 tok **+103.71%（不升反降）**（`p3d_e0_vs_token_budget_test_n2.json`）
>    ⇒ **n 太小时连方向都不可信** ⇒ 趋势只能在 **n=16 同批曲线**上讲
>
> ### 五、⭐ 成员自查的一处校准口径更正（我采纳）
>
> "逐位一致"**只在同一设备内成立**：
> - **CPU** @15 tok：`E0_real = 21771.7` ↔ 归档**冻结基线** `21771.6993`（CPU）
> - **GPU** @15 tok：`E0_real = 21751.8` ↔ 训练档 `E_train_epochs[0] = 21751.8`（GPU）
> - **CPU 与 GPU 差 0.09%**（bf16 设备舍入）
>
> ⇒ **"管线已校准（同设备）"与"结论对预算/样本集敏感"必须严格分开写**，
> **避免被读成"既然校准过，结论就应当稳健"**。**这个区分很精细，成员主动提出，好。**
>
> ### 六、给 `p3-allocation` 的锚点（成员已发）
>
> **~190 token 预算下 blank/real = 2.48×**（22696.9 / 9149.9）；
> 它的 blank 锚点 23470.85 与本曲线的 COCO caption blank 相差仅 **3.4%**
> ⇒ **blank 侧 $E_0$ 对文本集不敏感**，故它的 $\\Delta E = +5543.6$ 挂在"**比 real 高约 2.5×**"的空白基线上。
>
> ### 七、⚠️ 页数预警
>
> **P3 已达 14 页（投稿时 11 页，PRL 版面页上限通常 7–8 页）**。
> 增量全来自我的修改（`theory` +15%、`experiments` +14%、`appendix` +7%）与三个实验组的结果。
> **处置计划**：
> 1. **先把待补实验与 P1 结果全部写完**（数字定稿后统一处理，避免反复压缩）
> 2. **再做一次压缩 pass**：把**详细表格与推导**移入 **Supplementary Material**（当前稿件**无**该机制，需新建）
> 3. **保留**：主线论证、审稿人点名要的内容（R3.12 的逐块 Γ/rank 表、R3.19/R3.20 的统计加固、R2.2 的 Γ 引导实验）
> 4. **精简**：重复的限定句、可合并的段落、可移入附录的实现细节
>
> ### 八、门禁与状态
>
> - `_p466` **79/79 通过**（新增 8 条：主曲线 4 点单调、操作点 209.4%/3.09×、$E_0^{\\text{blank}}$ 预算不变性、
>   同设备校准、**以及那条负例必须存在**）；`_p471` 编码 **15/15**
> - **P3**：**14 页** / 0 错 / 0 未定义；**累计修 23 处**
> - **P1**：2/10 方案完成中，剩 26 run ≈3.2 h
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
    if "直达论文操作点" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("直达论文操作点", "3.09", "209.37", "0.09%", "页数预警"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
