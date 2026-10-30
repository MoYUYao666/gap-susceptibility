# -*- coding: utf-8 -*-
r"""Record the line-by-line audit of the P1 rejection letter as its own handoff entry.

The audit itself was worked out against the manuscript and the archives; this script only writes it
down, so that the five outstanding items are discoverable from HANDOFF.md instead of existing only in
a chat reply. Each number it quotes was measured first and is repeated here with its source file.

Idempotent; asserts that the earlier entry still points at this one and that the neighbours survive.

    python tools/_p856_record_pr_audit.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MARK = "PR 拒稿信逐条审核结果"
ANCHOR = ("> **📂 2026-10-15 13:14 —— PR 拒稿信已入库；审稿/决定文档统一整理到 "
          "`docs/reviews/`（零删除）**")
FIX = ("详见下一条 13:20 条目", "详见上一条条目（2026-10-15 13:20 逐条审核）")

ENT = """> **🔍 2026-10-15 13:20 —— PR 拒稿信逐条审核结果：四大硬伤已闭环，剩 5 项**
>
> 来源：`docs/reviews/P1_PR-D-26-10149_reviews.txt`（= Desktop `PR_reject.txt`，SHA-256 `3e73d0362ca49d36…`）。
>
> ### 一、⚠️ 先纠正我自己的记数口径
>
> 拒稿信**问题单只有 8 个编号题**（题号 1–4、6–9，**第 5 题缺失**）；
> 带编号建议的只有 **14 条**（Q1×1、Q2×1、Q3×1、Q4×2、Q7×1、Q8×3；**Q6 三位都说好、无内容**）。
> 加上 3 位审稿人 weaknesses 清单（**R1 6 + R2 5 + R3 4 = 15**）才是「29 条」的出处。
> **⇒ 我此前把"29 条意见"当作"29 条可逐条回应项"是不准确的**：其中 **15 条无编号内容**，
> **R2/R3 在题 4/8/9 只写 "Yes/Fair"**。这解释了为何"27/29 已回应"这个口径一直对不上。
>
> ### 二、✅ 已闭环（逐条验过）
>
> | 原意见 | 现状与证据 |
> |---|---|
> | R1-W1 `+0.079` vs `−0.081` 数值不一致 | ✅ `empirical.tex`：`−0.064`（r8/α16）与 *"an earlier version … quoted $+0.079$ … belongs to a different configuration, $\\alpha=64$, whose $R@1$ is $0.389$, and it is withdrawn"* |
> | R1-W2 / R3-2 伪重复、缺留出 | ✅ cluster-robust −1.05（CR1 SE 0.29, p=0.016）+ family-clustered bootstrap [−0.89,−0.62] + mixed model β=−0.95±0.08 + **样本外** 12 folds R²=0.449/0.396、6 folds 0.236/0.227 |
> | R1-W3 / R2-4 / R3-3 "direct causal" | ✅ 全文 0 命中；噪声线**标注 withdrawn**（5 seed：1.90±1.83 vs 2.48±3.25, p=0.77）；匹配相对扰动 0.91±0.45 / 0.99±0.45 |
> | R1-W4 / R3-4 COCO 近随机、BLIP-1 选择性解冻 | ✅ 三处披露齐全（COCO 复用 gallery、BLIP-1 非真 LoRA 且两臂同训 196,672,514 参、ViT-L 两行近随机）|
> | R1-W5 / R2-5 DG-ES 零开销 | ✅ `zero-overhead` 0 命中、整章删除；改述为"可监控 ≠ 可停机"并给 94 run 反证 |
> | R1-W6 同一 lr 不公平 | ✅ 逐方法 lr 扫描（`discussion.tex`）：LoRA@1e-5 60.69±0.05% vs 全量微调@1e-6 60.87±0.21%，差 0.18 pt 落在 seed 波动内 |
> | R2-1 标题过泛 | ✅ 已改名 *Adaptation Site and the Modality Gap…* |
> | R1-Q2 配置差异未澄清 | ✅ `empirical.tex` 开头明写"injected 而非 optimizer 所见"，并给实测参数预算（145,170,177 / 131,290,881 等）；附录 A 221-run 目录 |
>
> ### 三、⚠️ 剩 5 项（按优先级）
>
> | # | 项 | 实测证据 | 性质 |
> |---|---|---|---|
> | **1** | 🔴 **语言编辑：编译件有 28 处单词被截断** | 从 `paper合/main_nc.pdf`（64 页）抽文实测：`analyz` 10、`optimiz` 10、`minimiz` 5、`normaliz` 2、`characteriz` 1；`main_nc.tex` 摘要/正文/CRediT 里也有 | **三位审稿人一致点名的 Q9**；纯语言、零风险 |
> | **2** | 🔴 **两条与实测相反的秩断言（且互相矛盾）** | `validation.tex`：「Increasing configured rank beyond the task's effective rank **expands alignment-vulnerable parameters without adding gradient capacity**」＋「text-only **improves monotonically with rank**」。实测 `outputs/analysis/flickr_rank.json`：dCG = −0.0195(r1) → **−0.0244(r4)** → −0.0019(r64)（**中段最优、高秩趋近 0**）；R@1 才单调 0.765→0.806。COCO 秩扫（`rank_rerun.json`）dCG 才单调 | **R1-W1 同类问题**，须改写为"秩效应随数据集变号" |
> | **3** | 🟠 **全量 COCO 放大实验未进稿** | 稿内最新只到 10,000 训练 / 3,000 评测（0.579 / 0.607±0.002 / 0.623±0.001）；已验证的 **40,504 图全 gallery**（frozen 0.5655 → text-only **0.5823±0.0002**）在 `outputs/analysis/full_coco.json`，**文稿外** | **R2-3「larger datasets」** 的正面回应 |
> | **4** | 🟠 **多一个 decoder VLM** | 稿内仅 Qwen2-VL-2B（13 seed，supplement `sec:vlm`）；LLaVA-1.5-7B 全量 12 run 进行中（0/12 有效） | **R2-3「modern VLMs」** |
> | **5** | 🟡 **R1-Q4 只做了一半** | 附录 A 221-run 目录表 ✅；**按 model/dataset 分层的 DG–R@1 图未补**（现只有按 family 重抽样与留出折的文字） | 补图成本低 |
>
> 另：`empirical.tex` 有一处 markdown `**not used**` 漏进 LaTeX，会印成字面星号（与第 1 项同批修）。
>
> ### 四、复投前须操作者确认
>
> **Zenodo 有两条 DOI**（`10.5281/zenodo.23341083` 与 `23341223`），稿内 Data availability 钉的是 `23341223`。
> **arXiv 预印本会与在投稿并行**（`paper_a1/` NEUNET、`paper_a2/` JOE、`paper3/` PRL 均在审）⇒
> **复投 Paper A 前需操作者决定：是否上预印本、走哪条 DOI，或只投期刊不上 arXiv。**
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    text = io.open(HANDOFF, encoding="utf-8").read()
    if MARK in text:
        print("  already recorded")
        return 0
    assert text.count(ANCHOR) == 1, "the 13:14 entry heading was not found exactly once"
    if not a.apply:
        print("  (dry run)")
        print(f"  would insert {len(ENT.splitlines())} lines above the 13:14 entry")
        return 0

    # the 13:14 entry references this one; point the reference the right way round
    old_ref, new_ref = FIX
    assert text.count(old_ref) == 1, "the forward reference in the 13:14 entry was not found"
    text = text.replace(old_ref, new_ref, 1)
    text = text.replace(ANCHOR, ENT + ANCHOR, 1)

    # verify the neighbours and the claims, then write
    lines = text.split("\n")
    assert lines[2].startswith("> **🔍 2026-10-15 13:20"), "the audit entry is not first"
    assert text.count(MARK) == 1, "audit entry duplicated"
    assert ANCHOR in text, "the 13:14 entry was lost"
    assert text.split("\n")[2 + len(ENT.splitlines())].startswith("> **📂 2026-10-15 13:14"), \
        "the audit entry does not sit directly above the 13:14 entry"
    assert "按操作者要求重排任务" in text, "the 2026-10-16 entry was lost"
    assert "2026-10-15 12:54" in text, "the P3 entry was lost"
    io.open(HANDOFF, "w", encoding="utf-8", newline="").write(text)

    check = io.open(HANDOFF, encoding="utf-8").read()
    for k in ("第 5 题缺失", "14 条", "28 处单词被截断", "flickr_rank.json", "full_coco.json",
              "23341083", "23341223", "not used"):
        print(f"  {'OK ' if k in check else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(check.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
