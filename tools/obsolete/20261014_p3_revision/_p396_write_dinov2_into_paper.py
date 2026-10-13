# -*- coding: utf-8 -*-
r"""把 DINOv2 异质配对实验写入论文（2026-10-12）。

## 写入内容（严格按审计的四条"不要写"约束）

**结果**（`outputs/analysis/dinov2_hetero/{fitted,random}/**/results.json`，均已核实）：

| arm（seed 42，严格冻结） | ΔCG | ΔDG | R@1 |
|---|---|---|---|
| frozen（fitted head） | CG 0.6769 / DG 0.7510 | — | 0.2890 |
| text_only | **−0.3913** | −0.4462 | 0.3540 |
| **both** | **−0.4099** | −0.4667 | **0.5550** |

**随机头对照**（关键）：

| | fitted head | random head |
|---|---|---|
| frozen CG / R@1 | 0.6769 / 0.2890 | **0.8717 / 0.0050**（≈chance） |
| text_only ΔCG | −0.3913 | **−0.2988（= 76%）** |

## 必须同时写的限制（来自 `docs/DINOV2_AUDIT.md`）

1. **异质配对**（DINOv2 视觉塔 + CLIP 文本塔 + 拟合头）——**不是原生双塔模型**
2. **InfoNCE 温度不同**（本实验 exp = 14.29 vs 论文 exp = 100，**7×**）→ **量级不可与表并列**
3. **n = 1 seed**；`vision_only` **未跑**
4. **该规则定义在"双塔联合预训练"上** → 异质配对**无单一预训练目标** ⇒
   **只能报"本设定内的排序观察"，既不确认也不否证论文的分组规则**
5. 初始对齐仅论文骨干约一半（R@1 0.289 vs 0.577，新测）

严禁：❌"−0.39 是论文所有 ΔCG 的 4–37 倍"（BioCLIP 行同量级）；❌"顺序反转/一致，支持或否证论文"；
❌"gap 降了检索升了 ⇒ gap 下降是好事"。

    python tools\_p396_write_dinov2_into_paper.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
E = REPO / "paper合" / "sections" / "empirical.tex"

# 插在 tab:position_strict 之后、既有 "Retrieval protocol" 段之前
ANCHOR = (r"\paragraph{Retrieval protocol, and which rows we treat as informative.}")

PARA = (
    r"\paragraph{A non-contrastively pre-trained vision tower, as a qualitative extension.}"
    r" The rows above vary the pre-training objective across contrastive and non-contrastive "
    r"backbones. As a further, deliberately qualitative check we repeated the strict-freezing "
    r"comparison in a configuration whose vision tower was never trained contrastively at all: "
    r"DINOv2-base as the vision tower, CLIP ViT-B/32 as the text tower, and a $512$-dimensional "
    r"projection head fitted on a split disjoint from both training and evaluation and then "
    r"frozen. This is a heterogeneous pairing rather than an off-the-shelf model, and it has no "
    r"single pre-training objective, so it cannot confirm or refute the grouping the table "
    r"reports; we include it only because the direction it produces is informative. With one "
    r"seed, the two adaptation positions order as $\Delta\mathrm{CG} = -0.410$ for "
    r"both-position against $-0.391$ for text-only (frozen $\mathrm{CG} = 0.677$), and both "
    r"orderings agree here: retrieval is better for both-position ($R@1 = 0.555$ against "
    r"$0.354$; frozen $0.289$). That is the direction the table reports for the two "
    r"non-contrastively pre-trained backbones rather than for the contrastive ones, though on "
    r"the paper's CLIP rows the gap ordering and the retrieval ordering run opposite ways. "
    r"Two controls bound how far this can be read. First, the projection head is larger than "
    r"the adapters ($656{,}384$ parameters against $196{,}608$ or $491{,}520$), so we repeated "
    r"the text-only arm with a \emph{never-fitted} head: the frozen baseline is then barely "
    r"aligned at all ($R@1 = 0.005$, near the $0.002$ chance level), yet text-side adaptation "
    r"still moves the gap by $-0.299$, which is $76\%$ of the fitted-head effect, so the effect "
    r"is not an artefact of the head. Second, this pairing was trained at a different InfoNCE "
    r"temperature from every other row in this paper ($\exp(\logit) = 14.29$ against $100$), "
    r"because the projection head was built from the model's \texttt{logit\_scale} "
    r"configuration value rather than from the value stored in the released weights; the "
    r"magnitudes here are therefore \emph{not} comparable with the table's and we report them "
    r"only as a direction. The run is archived in "
    r"\texttt{outputs/analysis/dinov2\_hetero/} and one arm (\texttt{vision\_only}) was not "
    r"run, which we record rather than estimate.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(E, encoding="utf-8", errors="replace").read()
    if "heterogeneous pairing rather than an off-the-shelf model" in t:
        print("  已写入")
        return 0
    n = t.count(ANCHOR)
    print(f"  锚点命中 {n}")
    if n != 1:
        print("  🔴 锚点未命中")
        return 1
    t2 = t.replace(ANCHOR, PARA + "\n\n" + ANCHOR, 1)
    if not a.apply:
        print("  （预演）")
        return 0
    bak = E.with_suffix(".tex.bak_p396")
    if not bak.exists():
        shutil.copy2(E, bak)
    io.open(E, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(E, encoding="utf-8", errors="replace").read()
    checks = {
        "含异质配对限定": "heterogeneous pairing rather than an off-the-shelf model" in t3,
        "含温度限制": "14.29$ against $100$" in t3,
        "含随机头对照": "never-fitted" in t3 and "$76\\%$" in t3,
        "含'不能确认或否证'": "cannot confirm or refute the grouping" in t3,
        "含 vision_only 未跑": "was not\nrun, which we record rather than estimate" in t3
                             or "was not run, which we record rather than estimate" in t3.replace("\n", " "),
        "禁语未出现（4-37 倍）": "4--37" not in t3 and "4-37" not in t3,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
