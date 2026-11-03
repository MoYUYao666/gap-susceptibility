# -*- coding: utf-8 -*-
r"""Record the Paper A readiness conclusion and print the upload list.

Operator decisions received: the data are already in the repository, and P1 has been rejected by
Pattern Recognition, so the "wait for P1's decision" precondition is lifted.

    python tools/_p698_paperhe_ready.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NC = REPO / "paper合" / "NC_submission"
OUT = REPO / "outputs" / "analysis" / "paperhe_upload_list.json"

ENT = """> **✅ 2026-10-14 19:00 —— Paper A 投稿条件确认，包已就绪**
>
> ### 一、操作者答复
>
> > **"应该都在库里了，已经确认被PR拒稿了"**
>
> | 待决项 | 结论 |
> |---|---|
> | Paper A 的归档指向 | ✅ **数据/代码已在公开库**（`gap-susceptibility` + Zenodo DOI `10.5281/zenodo.23341223`）⇒ **声明无需再改** |
> | 投稿时机（原记"等 P1 的决定"） | ✅ **前置条件解除**：**P1 = `PR-D-26-10149` 已被 Pattern Recognition 拒稿** ⇒ 可以投 |
>
> ### 二、✅ 声明的字字属实性核验（`tools/_p696`、`_p697`）
>
> **仓库 `outputs/` 的 1,696 个已跟踪文件中，Paper A 依赖的产物全在**：
>
> | 产物族 | 文件数 |
> |---|---|
> | 逐 epoch 监测轨迹 | **305** |
> | **strict-freezing 对照** | **239** |
> | 跨架构扫描（CLIP/SigLIP/OpenCLIP/BLIP） | **182** |
> | rank / 分配扫描 | 212 |
> | gap 测量 | 397 |
> | ODE 拟合 | 17 |
>
> **Paper A 的 13 个招牌数字，13/13 都有"当前来源"**（非仅存于 `superseded`/`_archive` 文件）：
>
> | 值 | 含义 | 当前来源（示例） |
> |---|---|---|
> | `0.949` | ODE 拟合均值 R² | `outputs/analysis/ode_ledger.json` |
> | `0.814` / `0.977` | R² 区间 | `outputs/a1_h_bootstrap.json` / `a1_h_offset.json` |
> | `0.943` | OpenCLIP BitFit R² | `outputs/analysis/driving_trajectory.json` |
> | `0.922` | CLIP 全量微调 pilot R² | `outputs/a1_multiseed.json` |
> | `0.946` | 线性基线 R² | `outputs/analysis/lit_pool.json` |
> | `204` / `383` / `221` | run 与实验计数 | `outputs/_layout_test/r4/both/seed42/results.json` 等 |
> | `60.69` / `60.87` | 逐方法调参后的零样本准确率 | `outputs/analysis/pr_peft_lr_sweep.json` / `pr_fullft_lr_sweep.json` |
> | `0.91` | 5% 下降时的相对预算比 | `outputs/a1_multiseed.json` |
>
> **⚠️ 核验方法的限度（照实记录）**：上述是**字面匹配**（某已跟踪文件含该字符串），
> **只证明数字存在于归档，不证明 Paper A 把它归因到了正确的那次运行**。
> 更强的门禁是逐条指名的 claim ledger（本项目已有 `tools/_claim_ledger.py` 用于 P3）。
> **⇒ 若操作者要求，我可以为 Paper A 补一份同规格台账。**
>
> ### 三、📤 投稿包（`paper合/NC_submission/`，可上传）
>
> | 门户 item type | 文件 | 大小 | 状态 |
> |---|---|---|---|
> | **Manuscript** | `Manuscript.pdf` | 927,072 | ✅ **63 页**，含新 DOI 声明 |
> | **Cover Letter** | `Cover Letter.pdf` | — | ✅ 3 页，63 页 / 236 词 + DOI |
> | **Highlights** | `Highlights.pdf` 或 `Highlights.txt` | — | ✅ 当前标题，5 条（43–59 字符） |
> | **LaTeX source** | `latex_source.zip` | **1,989,660** | ✅ 55 成员，含新声明 |
> | （对照表，不用上传） | `README.md` | — | ✅ 数字已更新 |
>
> ### 四、⚠️ 一处**需要操作者知情的时点问题**（不阻塞投稿）
>
> Paper A 的声明指向 **Zenodo 快照 `10.5281/zenodo.23341223`**，而该快照是 **10-13** 铸出的
> ——**早于今天对 Paper A 的改动**。但 Paper A 的数据/代码本就与 P3 同库
> （快照里已有 `outputs/` 的逐 run 记录与脚本），**公开仓库 `main` 始终是最新的**
> ⇒ **声明成立**。
>
> **⇒ 若在 Paper A 录用后再出 `v1.1` 快照**，声明中的 DOI 可保持一致（同一概念 DOI 下新增版本）。
>
> ### 五、剩余
>
> ① 上传 `NC_submission/` 四个文件到 Neurocomputing 门户 ② 表单字段：Data availability 选 `Other` + 200 字符内说明（同 P3 做法）
> ③ 若需要，我为 Paper A 补 claim ledger 台账
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print("  upload list:")
    rows = []
    for name in ("Manuscript.pdf", "Cover Letter.pdf", "Highlights.pdf",
                 "Highlights.txt", "latex_source.zip", "README.md"):
        p = NC / name
        rows.append({"file": name, "bytes": p.stat().st_size if p.exists() else None,
                     "exists": p.exists()})
        print(f"    {p.stat().st_size if p.exists() else 0:>10,}  {name}")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps({"files": rows}, ensure_ascii=False, indent=1))
        hp = REPO / "HANDOFF.md"
        t = io.open(hp, encoding="utf-8").read()
        if "Paper A 投稿条件确认，包已就绪" not in t:
            i = t.find("# 项目交接文档")
            j = t.find("\n", i)
            io.open(hp, "w", encoding="utf-8", newline="").write(
                t[:j + 1] + "\n" + ENT + t[j + 1:])
            t2 = io.open(hp, encoding="utf-8").read()
            for k in ("Paper A 投稿条件确认，包已就绪", "前置条件解除", "13/13",
                      "核验方法的限度", "1,989,660"):
                print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
            print(f"  HANDOFF lines = {len(t2.splitlines())}")
        else:
            print("  handoff already recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
