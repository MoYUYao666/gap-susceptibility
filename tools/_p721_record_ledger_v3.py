# -*- coding: utf-8 -*-
r"""Record the ledger result and the 95 vs 104 contradiction it exposed.

    python tools/_p721_record_ledger_v3.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📒 2026-10-14 22:30 —— 按操作者提示查 HANDOFF：**5 个 GAP 全部破案**；台账 **PASS 21 / GAP 0**
> 并暴露稿件一处**内部矛盾（95 vs 104）**
>
> ### 一、操作者指令
>
> > **"你查handoff看看"**
>
> ### 二、🔴 关键教训：**来源一直在 HANDOFF 里，是我搜错了地方**
>
> 我此前四轮搜索只查了**归档 JSON 与工具脚本**，**没查交接文档**。查 HANDOFF 后立刻找到：
>
> | HANDOFF 行 | 内容 |
> |---|---|
> | **L10175** | `附录目录（13 类机理 117 + XIV 类严格冻结）｜212｜**221**（严格冻结 95 → **104**）` |
> | **L10190** | `附录目录求和 : 221` |
> | **L10192** | `目录 + ODE = 221 + 162 = 383 → ✅ 一致` |
> | **L10193** | `✅ 严格冻结实测 104 = 目录表隐含值（221 − 117）` |
> | **L5432** | `CR1 稳健 SE（6 簇）｜0.0723 → **0.2911（4.03×）**，p(t₅) = **0.0155**｜cluster_robust_OLS` |
>
> **⇒ 5 个数的来源全部找到：**
>
> | 数字 | 来源 | 复现 |
> |---|---|---|
> | **117** 机理实验 | 稿件附录目录表「13 类机理」+ `supplement.tex` 正文 | ✅ 与表一致 |
> | **221** 目录 run 数 | `sections/supplement.tex :: tab:full_experiments` 的 **Total 行 = 221** | ✅ 表内断言 |
> | **104** 严格冻结 | 同表 **XIV 行 = 104**（**117 + 104 = 221**） | ✅ 表内算术自洽 |
> | **383** 验证实验数 | **221（目录）+ 162（ODE 拟合）= 383** | ✅（HANDOFF L10192） |
> | **0.29** CR1 标准误 | `pr_stats_hardened.json :: mixed_effects.cluster_robust_OLS.by_design_cell.se_cr1 = **0.2911**` | ✅ **我的字段名猜错了** —— 不是 `se` 而是 **`se_cr1`**（同组还有 `se_ols=0.0723`、`se_cr0=0.2651`、`se_inflation_vs_ols=4.0275`） |
>
> **⚠️ 我的错误**：我断言"归档无承载字段"，实际是**我的字段名假设错了** + **没查交接文档**。
> 这与项目此前"假门禁"的教训同源：**搜索方法错 → 结论错**。
>
> ### 三、✅ 台账终版（`tools/_claim_ledger_paperA.py`）
>
> **PASS 21 ｜ GAP 0 ｜ 共 21**
>
> 覆盖：ODE 拟合质量 4 项｜α 符号统计 5 项（222/203/19/50/3）｜OpenCLIP 0.943｜
> 附录目录表 4 项（104/221/117+104/221+162=383）｜gap-retrieval 5 项（n=204、r=−0.71、
> 斜率 −1.05、**SE 0.29**、p=0.016）｜零样本 2 项（60.69/60.87）。
>
> ### 四、🔴 台账顺带暴露的**真问题**：稿件 **95 vs 104 内部矛盾**
>
> | 位置 | 写法 |
> |---|---|
> | `sections/supplement.tex` **L3**（正文） | *"the 117 mechanism experiments of Part I together with the **95** strict-freezing controls"* |
> | `sections/supplement.tex` **L28**（同文件表格 XIV 行） | `Strict-Freezing Controls (four backbones) & **104**` |
> | `sections/conclusion.tex` L5 | *"covering 117 mechanism experiments and **95** strict-freezing controls"* |
> | `sections/empirical.tex` L4 | *"These experiments, 117 under the earlier convention and **95** under strict freezing"* |
>
> **⇒ 同文件正文说 95、表说 104，且结论段也用 95。**HANDOFF 记录 **95 → 104 是已知更正**
> （L10175/10193：把 BioCLIP 的 9 个补进来后 95 → 104），**但更正只落到表里，正文没跟着改**。
>
> **我尝试用"数目录"判定哪个对，结果无效**：`outputs/strict_freeze*` 下 results.json 共 **116** 个
> （含 `strict_freeze_rank` 30 个、`strict_freeze_openclip` 与 `_oclip` 可能重复计入）
> —— **数目录数不出 95 也数不出 104**，因为"一次实验"有稿件的自定义口径。
>
> **⇒ 这是作者的判断，我不擅自改数字。** 需要作者确认：**到底是 95 还是 104**，
> 然后把 `supplement.tex` L3、`conclusion.tex` L5、`empirical.tex` L4 与表统一。
> （若按 HANDOFF 的更正，应为 **104**；但 `empirical.tex` 那句是"**两种约定**"的对比
> ——「117 under the earlier convention and 95 under strict freezing」——**那句里的 95 可能是有意的**，
> 需作者确认。**这正是我不能代判的原因。**）
>
> ### 五、另一处时间性问题（仍成立）
>
> `alpha_sign_audit.json` 记 `ode_ledger` 的 **n = 103**，而**现行 `ode_ledger.json` 是 96**
> ⇒ 审稿人自数会得 **96+33+33+50+3 = 215**，**而非 222**。
> **建议**：稿件写明该计数取自审计件，或按现行归档重算。
>
> ### 六、剩余
>
> ① **95 vs 104**（需作者定，然后我统一四处）② **222 vs 215 的时间口径**（建议改口径或重算）
> ③ 投稿包已就绪，可上传
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
    if "按操作者提示查 HANDOFF" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("按操作者提示查 HANDOFF", "se_cr1", "PASS 21", "95 vs 104", "没查交接文档"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
