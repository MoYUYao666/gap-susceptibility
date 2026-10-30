# -*- coding: utf-8 -*-
r"""Record the pre-submission response audit in the handoff document.

    python tools/_p641_record_response_audit.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔎 2026-10-14 12:00 —— 提交前复核三个回复框：**查出 2 处真错误（其中 1 处在稿件里）**
>
> ### 一、操作者要求
>
> > **"我准备填reviewer的回复了，再检查一遍"**
>
> ### 二、🔴 查出并修好的**真问题**
>
> | # | 问题 | 性质 | 处置 |
> |---|---|---|---|
> | **1** | **稿件 `sections/experiments.tex:164` 与 `theory.tex:130` 用的是 3-seed 旧数**：`corner +3607 ± 514` vs `Γ-guided +2241 ± 1291` | **稿件引用被取代的数据** —— 6-seed 归档是 `corner +2343.9 ± 2426.1`、`Γ-guided +1477.5 ± 1563.3`；**且同一句里已经用了新值 `+1478`/`+5048` ⇒ 新旧混用，自相矛盾** | **改为 `+2344 ± 2426` / `+1477 ± 1563`**（`_p639`，8 处 / 4 个文件 + 源包 2 个） |
> | **2** | 回复写 `p = 0.2057`，**稿件写 `p = 0.21`** | **同一量两种写法**，审稿人按回复去稿件里查会查不到 | 回复统一为 **`p = 0.21`**（与稿件一致）（`_p640`，9 处 / 5 个文件） |
>
> **⇒ 出处可查**：`outputs/analysis/p3_alloc_results.json`
> `comparisons.{{exp_beta_paper_0.137,corner,inverse_beta_paper_0.137}}.vs_uniform.p_two_sided`
> = `0.0055 / 0.0587 / 0.2057`；逐 run 记录在 `outputs/analysis/p3_alloc_runs/main/<plan>__seed*.json`（每方案 6 个 seed）。
> **旧值的作废依据**：`HANDOFF.md:1920`（`exp` +2241.0 → +1477.5；`corner` +3607.2 → +2343.9）、
> `evidence/P3_EXPERIMENTS.md:524`（"**旧值一律作废**"）。
>
> ### 三、✅ 顺带核查通过的项目
>
> | 检查 | 结果 |
> |---|---|
> | **回复 vs 稿件：12 项承诺** | **12/12 在稿件文本里可查**（R3′ 公理、`‖∇E‖²` 反例、bracketed、无架构依赖、方差撤回、AdaLoRA、随机不可区分、匹配损失、反转、DOI、下游非代理、zero-shot 定义） |
> | **关键数字：17 项** | 15/17 命中；2 项经查是**写法不同**（`$7{{,}}237{{,}}632$`、`$3 \\times 10^{{-4}}$`）而非缺失 |
> | **回复文件编码** | 三份均 **UTF-8**、**0 中文字符**、**0 占位符**、**0 LaTeX 命令**、**0 `**` 粗体残留** |
> | **点数覆盖** | **R1 = 4（W1–W4）｜R2 = 5 ｜R3 = 23 ⇒ 32 点，每点都有 `Response:`** ✅ |
> | **"33" 的解释** | 原始审稿件共 **33 个编号项** = R1 的 **2 个 Summary 正面点** + R1 W1–W4 + R2 5 + R3 23；**2 个正面点写在开场致谢里** ⇒ **无漏点** |
> | **非 ASCII 字符** | 仅 en/em dash 与 2 个弯引号（EM 可正常显示）；R2 含 `Γ`/`Δ`（数学记号，保留） |
>
> **⚠️ 已知小瑕疵（不改）**：R1 用 `Point W1..W4`，R2/R3 用 `Point 1..N` ——
> **差异有据**（R1 原报告就叫 Weakness 1–4），**故意保留**，且不易误解。
>
> ### 四、✅ 重编译与同步
>
> | 项 | 结果 |
> |---|---|
> | `main.pdf` | **10 页 / 0 错误 / 0 未定义**；PDF 内 `+2344±2426`、`+1477±1563` 在，`+3607`/`+2241`/`0.2057` **全无** ✅ |
> | 源包 | **12 成员 / 128,822 字节**；**解压独立编译 3 遍 ⇒ 0 错误 / 10 页** ✅ |
> | 修订包 | `main.pdf` 已更新（414,996 字节）；`cover_letter.pdf`、`supplementary.pdf` 未变 |
>
> ### 五、📤 三个回复框（粘贴用，均为 UTF-8 纯文本）
>
> | 文件 | 字符 | 行 | 点数 |
> |---|---|---|---|
> | `response/P3_RESPONSE_Reviewer1_plain.txt` | 8,200 | 118 | 4（W1–W4） |
> | `response/P3_RESPONSE_Reviewer2_plain.txt` | 7,930 | 131 | 5 |
> | `response/P3_RESPONSE_Reviewer3_plain.txt` | 26,255 | 361 | 23 |
>
> ### 六、剩余
>
> ① **重传 EM**：`main.pdf`（414,996）＋ `cover_letter.pdf`（131,744）＋ `P3_latex_source_revision.zip`（128,822）
> ② **粘三个回复框**
> ③ **EM 表单**：Data availability 勾"数据在公开仓库中可用" + 填 `10.5281/zenodo.23341223`
> ④ 提交
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "提交前复核三个回复框" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("提交前复核三个回复框", "+2344", "p = 0.21", "33 个编号项", "128,822"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
