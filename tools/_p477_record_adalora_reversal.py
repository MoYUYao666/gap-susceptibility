# -*- coding: utf-8 -*-
r"""落账：AdaLoRA lr 反转 + Γ 侧对称扫描裁决（2026-10-13 10:35）。

    python tools\_p477_record_adalora_reversal.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **⚖️ 2026-10-13 10:35 —— AdaLoRA 结论**反转**：合适 lr 下其 $\\Delta E$ **优于我们全部 Γ 侧方案**；我裁决**补 Γ 侧对称 lr 扫描****
>
> ### 一、实测（判据 `loss_last < 0.9×loss_first` **预先写死**；我逐项核实）
>
> | `lr` | seed | loss 首→末 | **降幅** | **$\\Delta E$** | E 轨迹 | 真训练？ |
> |---|---|---|---|---|---|---|
> | 5e-5 | 42 | 1.5595 → 1.5604 | +0.06% | −181.6 | 平坦 | ❌ |
> | 5e-5 | 123 | 1.5598 → 1.5590 | −0.06% | −84.3 | 平坦 | ❌ |
> | **3e-4** | 42 | 1.5590 → 1.4866 | **−4.64%** | **−1468.2** | 23471→23467→22824→**22088→22003**（**单调降**） | ❌（未过 10%） |
> | **1e-3** | 42 | 1.5458 → **0.9767** | **−36.81%** | **−757.3** | 23471→20886→**27331**→22574→22714（**不稳**） | ✅ |
>
> **⇒ 三条实质结论**：
> 1. **"AdaLoRA 未能有效训练"只在 `lr=5e-5` 成立** ⇒ **"不可比"是我方 lr 选择造成的，不是方法性质。已更正。**
> 2. **`3e-4` 与 `1e-3` 下 $\\Delta E$ 都为负** ⇒ **优于本实验全部 Γ 侧方案**
>    （Γ-guided **+1477.5**、`uniform` **+5047.5**；随机池最好者 `random_03` −1450.3 与之同量级）
> 3. **⚠️ 不对称**：**AdaLoRA 扫了 3 个 lr（5e-5/3e-4/1e-3），Γ 侧全部只用 lr=5e-5** ⇒
>    **其优势有一部分来自"调过 lr"，Γ 侧没调。**
>
> ### 二、✅ 我裁决：**补 Γ 侧对称 lr 扫描**（8 run ≈1.4 h）
>
> **`exp` 与 `uniform` × `lr ∈ {3e-4, 1e-3}` × 2 seed（42, 123）**，**独立 tag**
> （`exp_lr0.0003` / `exp_lr0.001` / `uniform_lr0.0003` / `uniform_lr0.001`）。
>
> **理由（三条，按重要性）**：
> 1. **不对称会杀死这条答复**：审稿人 **R1.6 的原话就是** *"directly using the same learning rate …
>    may not constitute a fair comparison"* ⇒ **我们若拿"调过 lr 的 AdaLoRA"比"没调 lr 的 Γ 侧"，
>    正是他批评的那个错。必须对称。**
> 2. **两种结果都有用**：Γ 侧也改善 ⇒ 对比对称、AdaLoRA 优势可能缩小；
>    Γ 侧恶化/平台 ⇒ **AdaLoRA 优势成立**，且**"Γ 侧对 lr 敏感而 AdaLoRA 不敏感"本身是发现**
> 3. **成本 1.4 h，截止 Nov 02 尚有 20 天** ⇒ 不构成障碍
>
> **⚠️ 我给成员的预期警告（免得结果出来才被动）**：论文自己的 full-FT 扫描显示
> **lr ≥1e-5 时 $\\Delta E$ 变差（塌缩区）**；Γ 侧用 Qwen2-VL-2B + LoRA，**1e-3 下很可能也变差**。
> **⇒ 我预期"Γ 侧在 3e-4/1e-3 下变差或平台" ⇒ AdaLoRA 的优势会被确认。**
> **但这不改变裁决**：**一个对称的、对我们不利的对比，比一个不对称的"我们赢了"有价值得多。**
>
> ### 三、⭐ 成员修的 `--tag` bug（静默覆盖类，与聚合产物同族）
>
> `_p451_baseline_adalora.py` **无 `--tag` 支持**，而 lr 队列传了 `--tag` ⇒
> **两个 lr 会写同一文件、后者覆盖前者**。已加 `--tag` → `outdir = OUTDIR/tag`，并验证分目录落盘。
>
> **⇒ 已要求把两条并列为同一类缺陷**：
> > **静默覆盖类缺陷**：① 聚合产物每次重写（丢方案）② 参数/tag 缺失导致多配置写同一文件。
> > **共同特征：两个不同的事实指向同一个存储位置。**
>
> ### 四、答复口径（我审后要求改一处）
>
> 成员原写：*"我们不声称本方法优于 AdaLoRA；同预算机制已证，方法优劣方向相反且未做对称调参。"*
> **⇒ 补完 lr 扫描后去掉最后半句**（那正是要消除的不对称），改为：
> > 我们实现了 AdaLoRA 的同预算对比并**对两侧做了相同范围的 lr 扫描**；
> > **在该设置下 AdaLoRA 的 $\\Delta E$ 优于本方法的分配方案**；
> > **我们方法的贡献在于"零样本、无需目标模型梯度的分配规则"，而非在 $\\Delta E$ 上取胜。**
>
> **⚠️ 并要求在报告与回复信建议里都写明这条边界（能站住的地方）**：
> > **本方法的卖点是"分配决策不含目标模型梯度"，不是"分配结果最优"。**
> > **在能承担目标模型训练的场合，AdaLoRA 这类自适应方法应当更优** ——
> > 我们的规则面向的是**不能/不愿在目标模型上做搜索**的场景。
>
> **这与稿件 Summary 的 zero-shot / cross-architecture 定位一致。**
>
> ### 五、其余要求
>
> - **AdaLoRA `n=1`** 的限制写清（Γ 侧 $n=6$）
> - **`3e-4` 的 E 单调降 vs `1e-3` 的能量震荡**都写（**loss 低 ≠ 能量稳**）
> - 所需 $n$ 的 **11–28** 与逐 run 出处保持一致
>
> ### 六、状态
>
> - **P1 ✅（30）｜P2 ✅（6 seed，57 run）｜P3 ✅（AdaLoRA 同预算 + lr 扫描）**
> - **Γ 侧对称 lr 扫描**：8 run ≈1.4 h **进行中**
> - **P3 稿件**：**14 页** / 0 错 / 0 未定义；**累计修 24 处**
> - **PRL 硬约束**：**双栏 ≤7 页**（官方 Mandatory Submission Requirements）⇒ **待压缩 + 新建 Supplementary**
> - **修订包**：`SUBMISSION/P3_PRL_revision/`（待压缩后重新生成）
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
    if "AdaLoRA 结论**反转**" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("AdaLoRA 结论", "−1468.2", "补 Γ 侧对称 lr 扫描", "静默覆盖类缺陷", "分配决策不含目标模型梯度"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
