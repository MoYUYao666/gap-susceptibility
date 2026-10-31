# -*- coding: utf-8 -*-
r"""生成 P3 的正式逐条回复信（Editorial Manager 用）（2026-10-13）。

## 依据

- 意见原文：`outputs/analysis/p3_reviews_structured.json`（33 条，从 `docs/P3_REVIEW_RESPONSE.md` 导出）
- 证据：本轮三组补实验（`docs/P3_EXPERIMENTS.md` / `P3_DOWNSTREAM.md` / `P3_STATS.md`）
- 稿件：`paper3/paper_ieee/main.tex`（**10 页**，操作者选定档 ①）

## 生成物

`docs/P3_RESPONSE_LETTER.md` —— 正式英文逐条回复（可直接贴进 EM 的表单字段）

**⚠️ 纪律**：**每条回复里的数字都必须能指名产出脚本与归档字段**（项目铁律）；
**引用撤回的主张要说明"已撤回"**；**未做的要说"未做"**。

    python tools\_p529_write_response_letter.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "P3_RESPONSE_LETTER.md"

HEADER = """# Response to Reviewers

**Manuscript:** `PRLETTERS-D-26-02378`
**Title:** Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation
**Journal:** Pattern Recognition Letters
**Decision:** Revise

---

We thank the Editor and the three reviewers for a careful and unusually constructive
report. The reviews identified one genuine gap in our proof, one experiment we had not
run, and one measurement whose interpretation we had overstated. Acting on them changed
our conclusions, and in three places the change is against the paper's original claims.
We state those reversals explicitly rather than burying them.

## Summary of what changed

| # | Change | Type |
|---|---|---|
| 1 | **Axiom R3$'$ (cross-block additivity) added**; the Representation Theorem no longer claims uniqueness from R1--R5 alone. A counterexample ($\\|\\nabla E\\|^2$ is block-decomposable but not additive) is now stated. | Theory correction (R1.5, R3.1, R3.3) |
| 2 | **A true block-wise $\\Gamma$-guided allocation experiment** now exists, at an identical trainable-parameter count verified per run. | New experiment (R2.2, R3.9, R3.21) |
| 3 | **The advantage we reported does not survive our own controls.** It reverses at another learning rate and disappears under matched training loss. We have withdrawn the claim. | **Claim withdrawn** (R2.2, R2.4, R3.9) |
| 4 | **AdaLoRA, swept over the same learning rates, reaches lower alignment energy than any of our arms.** We say so in the paper. | **Negative result reported** (R2.4, R3.9) |
| 5 | **A downstream check contradicts the energy.** Lower alignment energy does not predict better retrieval. | New experiment (R1.3, R2.3, R3.15, R3.16) |
| 6 | **The blank-image probe is not neutral:** at the paper's own operating point a blank image carries $3.09\\times$ the initialization alignment energy of a real one. | New measurement (R1.4, R3.13, R3.14, R3.23) |
| 7 | **The "phase transition" is downgraded to a bracketed crossing**, and its location attributed to the measurement protocol. | **Claim downgraded** (R3.17, R3.19) |
| 8 | **The "architecture-dependent" finding is withdrawn**: the contrast tracked the visual token budget. | **Claim withdrawn** (R1.4, R3.11) |
| 9 | **The $30\\times$ variance ratio is withdrawn** ($\\eta^2 = 0.989$: it is between-rank variance). | **Claim withdrawn** (R3.17) |
| 10 | Per-block $\\Gamma_k$ values and their optimal ranks are tabulated for CLIP, LLaVA and Qwen2-VL. | New data (R3.12) |
| 11 | Reproducibility analysis across software environments, seeds and hardware. | New analysis (R3.18) |

**Note on length.** The journal's Guide for Authors specifies a two-column manuscript of
no more than seven pages including all material. The original submission was eleven pages
and entered review. This revision is **ten pages** in two-column format, with the axiom
derivation, full proofs, protocol details, per-run tables and additional figures moved to
Supplementary Material. We would rather flag this than have it discovered at production,
and we are happy to compress further if the Editor prefers.

---
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0
    print("  ⚠️ 33 条回复正文由 Lead 手工撰写（每条含实测数字与出处）；")
    print("     本脚本负责页眉、变更汇总表与长度说明。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
