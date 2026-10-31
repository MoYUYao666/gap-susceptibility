# -*- coding: utf-8 -*-
r"""Record the 95 vs 104 decision and the package update.

    python tools/_p725_record_decision.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **⚖️ 2026-10-14 23:30 —— 判定 95 vs 104：**104 正确**，已统一并重编译**
>
> ### 一、操作者指令
>
> > **"我也不记得，你来查"**
>
> ### 二、✅ 判定依据（五条独立证据，指向同一结论）
>
> | # | 证据 | 结论 |
> |---|---|---|
> | 1 | 附录表 `tab:full_experiments` 的 **13 类逐行相加 = 117**（机理） | 机理数确认为 117 |
> | 2 | 同表 **XIV 行 = 104**，且 **117 + 104 = 221**，而**表的 Total 行也写 221** | **表内自洽 ⇒ 104** |
> | 3 | `HANDOFF.md` **L10175**：`附录目录（13 类机理 117 + XIV 类严格冻结）｜212｜221（严格冻结 95 → **104**）` | 更正记录：**95 → 104** |
> | 4 | `HANDOFF.md` **L10193**：`严格冻结实测 104 = 目录表隐含值（221 − 117）` | 实测 104 |
> | 5 | **算式一致性**：稿件摘要与结论称 **383 = 221 + 162**；若严格冻结为 95，则 **221 − 117 = 104 ≠ 95**，表就与 Total 差 9 | 只有 **104** 自洽 |
>
> **⇒ 判定：104 正确；`supplement.tex` 与 `conclusion.tex` 里的 95 是未跟上更正的旧数。**
>
> ### 三、✅ 已执行的修改
>
> | 文件 | 改动 | 理由 |
> |---|---|---|
> | `sections/supplement.tex` L3 | `95 strict-freezing controls` → **`104`** | 与**同文件表格 XIV 行**矛盾，表有 Total 自洽佐证 |
> | `sections/conclusion.tex` L5 | 同上 → **`104`** | 同上 |
> | **`sections/empirical.tex` L4** | **不改** | 原文 *"These experiments, **117 under the earlier convention and 95 under strict freezing**"* —— 这是**「两种约定」的对比**，不是控制组计数，**语义不同，改了反而错** |
>
> **⚠️ 我未擅自改 `empirical.tex`，也未改任何数字之外的表述** —— 那一句需作者确认它想表达的对比是否仍成立。
>
> ### 四、✅ 重编译与同步（`tools/_p724`）
>
> | 检查 | 结果 |
> |---|---|
> | 编译 | **63 页 / 0 错误 / 0 未定义引用 / 0 未定义引用** |
> | PDF 内 `104 strict-freezing` | ✅ 在 |
> | PDF 内 `95 strict-freezing` | ✅ **无残留** |
> | PDF 内 `221 runs` / `383 experiments` | ✅ 都在 |
> | PDF 内 `??` | 0 |
> | 源包 | `latex_source.zip` 重打：**55 成员 / 1,989,661 字节** |
> | 包内 Manuscript | `main_nc.pdf` → **927,081 字节** |
>
> ### 五、台账终态
>
> `python tools\\_claim_ledger_paperA.py --apply` ⇒ **PASS 21 ｜ GAP 0**
>
> ### 六、仍建议操作者看一眼的两处
>
> | # | 事项 | 说明 |
> |---|---|---|
> | 1 | `empirical.tex` 那句「117 earlier convention / 95 strict freezing」 | **语义判断**：若"早期约定"指的是三骨干口径、而现行是四骨干（含 BioCLIP）104，那句仍成立；若指的是别的，需改 |
> | 2 | **222 vs 215 的时间口径** | `alpha_sign_audit` 记 `ode_ledger` n=103，现行 96 ⇒ 审稿人自数得 215。建议稿件写明该计数取自审计件，或按现行归档重算 |
>
> ### 七、状态
>
> **Paper A 投稿包已就绪且内部一致**（`paper合/NC_submission/`：Manuscript 63 页、Cover Letter、Highlights、`latex_source.zip` 55 成员、README）。
> **可上传。**
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
    if "判定 95 vs 104" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("判定 95 vs 104", "104 正确", "empirical.tex` L4", "1,989,661", "语义判断"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
