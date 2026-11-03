# -*- coding: utf-8 -*-
r"""落账：P3 已修 4 处实质错误（理论缺口 + 记账口径 + β 来源）+ 成员发现核实（2026-10-12）。

    python tools\_p423_record_p3_fixes.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🛠️ 2026-10-12（续）—— P3 已自行修掉 4 处实质错误；三成员发现的 5 条我已逐条核实**
>
> ### 我亲自改的 4 处（`paper3/paper_ieee/sections/`，P3 编译 **11 页 / 0 错 0 未定义**）
>
> | # | 意见 | 病处 | 修法 | 脚本 |
> |---|---|---|---|---|
> | 1 | **R1.5 / R3.3** | `appendix.tex` 把 *"由 (AX3)，最一般的一阶泛函**是**双线性"* 当**断言**；`theory.tex` 把 **R3（块级分解可加）** 当作**自变量求和可加**用。而 R3 对 $\\|\\nabla E\\|^2$ **同样成立** | 新增公理 **R3′**；新增 **Lemma + 反例 $S=\\|x\\|^2$**（`lem:r3-not-r3p`）证明 R3 ⇏ R3′；定理重述为「R1–R5 **加 R3′** 下唯一」并**如实标注 R3′ 是新增结构假设**（同时回应 **R3.1**）；appendix 改为承认缺口 | `_p416` |
> | 2 | **R3.21** | `theory.tex` (A3) 是 **rank 记账** `Σ rank_k = C`，而 `experiments.tex` 写 *"under **equal parameter budget** (C=64)"* → **术语冲突** | 改为 *"equal **rank** budget"*，并在 (A3) 处**补参数记账说明**：$c_k=\\sum_{W\\in M_k}(\\mathrm{in}_W+\\mathrm{out}_W)$、块间差 **2.65×**（vision **655,360** vs shallow **247,296**）、**参数预算下解变为 $\\mathrm{rank}^*_k \\propto \\exp(-\\beta\\|\\Gamma_k\\|)/c_k$**、并声明 Eq.5 是 rank 口径 | `_p421`+`_p422` |
> | 3 | **R3.7** | `experiments.tex` 写 *"**The CLIP-derived allocation** ($\\beta=0.137$)"*，但实际出处是 `ode_ledger.json::runs[90]`（配置 **`v1_trajectory/v1_text_only_r64`**、**`family=lora`**）——**不是 CLIP**；且 `theory.tex` **自己声明**该 β 与 Eq.5 的 β 是**不同量** | 删去 "CLIP-derived"，改为**只用 Γ 的排序**做预测（**不依赖 β 数值**）；**显式区分两个 β** 并给出出处（96 次拟合**中位数 0.072**；0.137 是其中**单次**拟合，$R^2=0.951$） | `_p422` |
> | 4 | — | `theory.tex:117` 的 (A3) 与 `theory.tex:173` 的 (A3) **同名不同义**（一个是 $E$ 的公理，一个是分配约束） | 已识别，**待改编号**（避免读者混淆） | 待办 |
>
> ### 三成员发现的 5 条，我已逐条独立核实
>
> **(a) `30×` 必须降级**（`p3-stats`，R3.20）
> 27 vs 808 的比较里 **$\\eta^2(\\mathrm{rank})=0.989$** —— 808 的 sd **几乎全部来自"抽到哪个 rank"**（r=16 的 4 个 run）；
> **同秩 r=4 对 r=4 的 sd 比 = 0.98（不是 30×）**、Welch **p=0.47**。
> → **"30×" 是"混了秩"的产物**，不能用来证明 Γ 降低不确定性。
>
> **(b) R3.18「环境敏感」有实质答案**（`p3-stats`）
> 归档里有**干净的受控跨版本对照**（我已核 **4 个文件全部 epochs=3 / samples=20**）：
>
> | | 主版（transformers 5.16.1） | `tf457`（4.57.0） |
> |---|---|---|
> | **r=5 $\\Delta E$** | **−18.0** | **0.0** ← **符号翻转** |
> | **r=6 $\\Delta E$** | **+93.5** | **+96.5** ← 符号保持 |
>
> **⚠️ 我查出成员未提的一点**：两版**初始 $E$ 也不同**（3930.5 vs **3921.0**，差 **0.24%**）→ 已要求它
> ①逐版本给初始 $E$ ②说明来源③**检验"符号翻转是否只是初始差 + r=5 本身接近 0 的放大"**，
> **若不够硬就如实降级**。另有本地 vs 云 A800 的硬件对照（batch_size=2）符号保持。
>
> **(c) 记账口径**（`p3-allocation`，R3.21）→ 已修，见上表 #2。
> 同预算的**精确同参数整数分配只有 15 个**（`p3_alloc_plans.json::exact_budget_allocations`）。
>
> **(d) Eq.5 的记账口径**（`p3-allocation`）→ 已修，见上表 #2。
>
> **(e) β=0.137 的出处**（`p3-allocation`，R3.7）→ 已修，见上表 #3。
>
> ### 成员纪律
>
> - `p3-stats` **不抢 GPU**（现在被占），**继续做完 CPU 部分**并写 `docs/P3_STATS.md` ✅
> - `p3-allocation` **预算对齐做到逐位相等**：所有方案 $\\sum_k \\mathrm{rank}_k\\cdot c_k = 7{,}237{,}632$（**非"约等于"**）
>   并带**单测 0 失败**（`tools/_p435_tests_alloc_math.py`）✅
> - 三成员均**不改 `paper3/**/*.tex`**（分工正确）
>
> ### 待办
>
> - **33 条回复的正式文本**（工作文档 `docs/P3_REVIEW_RESPONSE.md` 已就绪，待补实验数据）
> - `theory.tex` 两处 (A3) **同名不同义** → 需改编号
> - 三成员实验数值（E/F+G/I 组）
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
    if "P3 已自行修掉 4 处实质错误" in t:
        print("  已记录")
    else:
        i = t.find("# 项目交接文档")
        j = t.find("\n", i)
        io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
        t = io.open(hp, encoding="utf-8").read()
        for k in ("4 处实质错误", "lem:r3-not-r3p", "0.989", "2.65", "runs[90]"):
            print(f"  {'✅' if k in t else '🔴'} {k}")
        print(f"  HANDOFF 行数 = {len(t.splitlines())}")

    # 文件地图
    fm = REPO / "文件地图.md"
    if fm.exists():
        ft = io.open(fm, encoding="utf-8").read()
        if "P3_REVIEW_RESPONSE" not in ft:
            add = ("\n## P3（`PRLETTERS-D-26-02378`）Revise（2026-10-12）\n\n"
                   "- **决定**：**Revise**（可修改后重审）｜**截止 2026-11-02**（逾期视为撤稿）\n"
                   "- **意见量**：**33 条**（R1 5 ｜ R2 5 ｜ R3 23），集中于 **10 个根问题**\n"
                   "- **应答工作文档**：`docs/P3_REVIEW_RESPONSE.md`（逐条含建议动作与空回复块）\n"
                   "- **意见原文解析**：`outputs/analysis/p3_reviews_parsed.json`；分类：`p3_review_classes.json`\n"
                   "- **原始件**：`docs/_inbox/P3_reviews/`（编辑邮件 txt + 审稿意见 pdf + 提取文本）\n"
                   "- **已修的 4 处实质错误**：理论缺口（新增 R3′ + Lemma + 反例）｜记账口径（rank vs 参数，2.65×）"
                   "｜β 来源（`ode_ledger.json::runs[90]`，非 CLIP）｜**待办**：`theory.tex` 两处 (A3) 同名不同义\n"
                   "- **补实验分工**：`task-9`（`p3-allocation`，E 组）｜`task-10`（`p3-downstream`，F+G 组）"
                   "｜`task-11`（`p3-stats`，I 组）\n")
            io.open(fm, "w", encoding="utf-8", newline="").write(ft.rstrip() + "\n" + add)
            print("  ✅ 文件地图已追加 P3 段")
        else:
            print("  文件地图已有 P3 段")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
