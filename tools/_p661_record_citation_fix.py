# -*- coding: utf-8 -*-
r"""Record the citation repair in the handoff document.

    python tools/_p661_record_citation_fix.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔗 2026-10-14 15:00 —— 回复里 4 处引用指向**审稿人打不开的内部文档** ⇒ 已改指向公开存档**
>
> ### 一、缘起：操作者问"那么 review 回复要改吗"
>
> **结构上不用重写**（三项承诺、17 个数字、32 点覆盖此前均已核过，且改标题那段说明已加）；
> **但有一个真空白**：回复反复承诺"每个数字可溯源"，
> **而仓库已公开 + DOI 已给 ⇒ 审稿人现在真的会去点。**
>
> **⇒ 逐条核验回复引用的 11 个文件路径，发现 4 个在公开存档里不存在。**
>
> ### 二、🔴 问题
>
> | 被引用路径 | 状态 | 引用者 |
> |---|---|---|
> | `outputs/analysis/` 下 7 个（`ode_ledger.json`、`p3_alloc_results.json`、`p3_alloc_runs/main/*.json`（58 个匹配）、`p3_seed_provenance.json`、`p3d_clip_ranksweep.json`、`p3d_e0_vs_token_budget_train_sel_n16.json`、`p3_alloc_gamma_qwen2vl2b.json`） | ✅ **都在存档里** | — |
> | `docs/P3_DOWNSTREAM.md` | 🔴 不在 | R1（并在 R3 处被间接引用） |
> | `docs/P3_EXPERIMENTS.md` | 🔴 不在 | R2 |
> | `docs/P3_STATS.md` | 🔴 不在 | R3 |
> | `tools/_p434_alloc_train.py` | 🔴 不在（一次性脚本，已排除） | R3 |
>
> ### 三、🔴 关键判断：**这 3 份 md 不能直接公开**
>
> 实测其内容含：
> - **审稿意见原文与编号**（`## 0. 对应的审稿意见 | 意见 | 原文要点 |`、`R2.2`、`R3.21` 等）
> - **内部任务分工**（`task-11`、`_p440`–`_p44m` 归本任务）
> - **给作者的措辞建议**（`**建议表述**：**推荐 (a) 报全族 + 分层披露**`）
>
> **⇒ 这是内部工作文档，不是给审稿人的材料。**（这也解释了为何 `docs/` 当初被整体排除。）
>
> ### 四、✅ 处置：**改引用指向公开存档，而不是公开内部文档**
>
> | 原引用 | 改为 |
> |---|---|
> | `analysis in docs/P3_DOWNSTREAM.md.` | `the downstream tables are in the supplementary material.` |
> | `Analysis in docs/P3_EXPERIMENTS.md.` | `The per-run records carry their own protocol blocks, so the arm, seed and learning rate of each value can be read off directly.` |
> | `:: rows[*].device; docs/P3_STATS.md.` | `:: rows[*].device.` |
> | `assertion in tools/_p434_alloc_train.py.` | `the assertion is recorded in each per-run block under outputs/analysis/p3_alloc_runs/.` |
>
> **⇒ 覆盖 8 个文件共 16 处**（3 个 `_plain.txt` 粘贴件 + 3 个 Markdown 孪生 + 组合信 `.md`/`.txt` + `docs/P3_RESPONSE_LETTER.md`）。
> **复核：无任何回复文件再引用内部路径** ✅
>
> **⚠️ 我在这件事上试了 3 次才对**：前两次逐字/正则匹配都失败 ——
> 因为**组合信是单行不换行**，而**Markdown 孪生里路径带反引号**（`` `docs/P3_STATS.md` ``），
> 与 `_plain.txt` 的裸路径写法都不同。**⇒ 教训：跨多个副本改文本，必须先打印每份的原文再写匹配式。**
>
> ### 五、✅ 顺带：源包里也删掉了同类风险
>
> `SUBMISSION/P3_PRL_revision/manuscript/latex_source/` 下的 `evidence/P3_*.md` —— **确认已不存在**（4 份均 absent）。
> **⇒ 源包内无任何审稿标记文档。**
>
> ### 六、✅ 重新暂存与终检（全通过）
>
> | 检查 | 结果 |
> |---|---|
> | 暂存件与权威源 sha256 一致 | **7/7** ✅ |
> | 回复文件：含标题说明、0 强调标记、0 中文、0 LaTeX | **3/3** ✅ |
> | 三份 PDF：新标题在、旧标题无 | **3/3** ✅ |
> | 源包重打 | `71acf265ab5e` |
>
> **更新后的回复大小**：R1 8,749 ／ R2 8,549 ／ R3 26,788 字符。
>
> ### 七、剩余
>
> ① **只打开 `UPLOAD\\`**，按 `README_UPLOAD.txt` 上传 10 项
> ② **粘三个回复框**
> ③ **EM 表单**：新标题 + Data availability 勾公开仓库 + 填 `10.5281/zenodo.23341223` + 新 highlights 5 条
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
    if "回复里 4 处引用指向" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("回复里 4 处引用指向", "不能直接公开", "16 处", "试了 3 次才对", "71acf265ab5e"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
