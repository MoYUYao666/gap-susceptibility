# -*- coding: utf-8 -*-
r"""修 `publish_clean/README.md`：撤回的主张 + 旧计数 + 状态；补硬件/引用/数据可用性（2026-10-13）。

## 为什么必须改

该 README 是**对外公开的仓库首页**，但它仍在宣传**已被论文撤回的主张**：

| 现 README | 论文现况 |
|---|---|
| *"$\Gamma$ is the **unique** admissible PEFT allocation statistic"* | **需额外假设 R3′**；R3 不足以推出唯一性（有反例） |
| *"Alignment **phase transition** at $r_c\in[5,6]$"* | **降级为 bracketed**，且属测量协议 |
| *"reduces uncertainty by **$32\times$**"* | **已撤回**（$\eta^2=0.989$ 是秩间方差） |
| *"181 runs"* / 计数表 | 现协议 **126 runs**；分配研究 57 runs |
| *"**Prepared for IEEE TNNLS**"* | **已投 PRL**（`PRLETTERS-D-26-02378`），现 **Revise** |
| 缺 **硬件要求**、**引用格式**、**数据可用性** | Guide 要求数据可用性声明 |

    python tools\_p558_fix_github_readme.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RM = REPO / "publish_clean" / "README.md"

PAIRS = [
    ("### Paper 3: Predictive PEFT Allocation\n"
     "**Gradient Structure Laws as Predictors of PEFT Design**\n"
     "\n"
     "- 181 runs, 2 architectures (LLaVA-1.5-7B, Qwen2-VL-7B), 4 sample sizes\n"
     "- **Representation Theorem**: $\\Gamma = \\langle \\nabla E, u \\rangle$ is the unique admissible PEFT allocation statistic\n"
     "- Alignment phase transition at $r_c \\in [5,6]$ on LLaVA; no transition on Qwen-VL\n"
     "- Counterfactual validation: $\\Gamma$-based allocation reduces uncertainty by $32\\times$\n"
     "- Cross-architecture zero-shot Predictive Transfer\n"
     "- **Prepared for IEEE TNNLS**",
     "### Paper 3: Predictive PEFT Allocation\n"
     "**Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation**\n"
     "\n"
     "- 126 runs on the present protocol, plus a 57-run capacity-matched allocation study; "
     "2 architectures (LLaVA-1.5-7B, Qwen2-VL-7B)\n"
     "- **Representation Theorem**: given the requirements R1-R5 **and the additivity axiom R3'**, "
     "$\\Gamma = \\langle \\nabla E, u \\rangle$ is canonical up to positive scaling. "
     "R3 alone does not imply R3' (counterexample: $\\|\\nabla E\\|^2$)\n"
     "- The crossing in alignment energy on LLaVA is **bracketed** at $r \\in [5,6]$, not sharp, and its "
     "location belongs to the measurement protocol; we do not claim an architecture dependence\n"
     "- Zero-shot allocation: no target-model gradient enters the allocation decision\n"
     "- **Negative results we report rather than hide**: the allocation rule beats the uniform-rank "
     "baseline at one learning rate but reverses at another and vanishes under matched training loss; "
     "it is indistinguishable from a random allocation at the same parameter budget; and AdaLoRA, swept "
     "over the same learning rates, reaches lower alignment energy than any of our arms\n"
     "- **Submitted to Pattern Recognition Letters** (`PRLETTERS-D-26-02378`, decision: Revise)"),
    ("| Experiments | 116 | 224 | 181 |",
     "| Experiments | 116 | 224 | 126 + 57 |"),
    ("| Key Result | Text-only is optimal | ODE $R^2 > 0.97$ | Phase transition $r_c \\in [5,6]$ |",
     "| Key Result | Text-only is optimal | ODE $R^2 > 0.97$ | Zero-shot allocation without target gradients |"),
    ("| Status | → Pattern Recognition | Ready | → IEEE TNNLS |",
     "| Status | → Pattern Recognition | Ready | → PRL (Revise) |"),
    ("│   ├── paper_ICLR_backup/  ← ICLR format backup\n"
     "│   ├── paper_ieee/         ← IEEE TNNLS version\n",
     "│   ├── paper_ieee/         ← IEEEtran version (submitted to Pattern Recognition Letters)\n"),
    ("- 181 runs, 2 architectures (LLaVA-1.5-7B, Qwen2-VL-7B), 4 sample sizes",
     "- 126 runs on the present protocol plus a 57-run allocation study"),
    ("- **Representation Theorem**: $\\Gamma = \\langle \\nabla E, u \\rangle$ is the unique admissible PEFT allocation statistic",
     "- **Representation Theorem**: $\\Gamma$ is canonical given R1-R5 **and** the additivity axiom R3'"),
    ("- Alignment phase transition at $r_c \\in [5,6]$ on LLaVA; no transition on Qwen-VL",
     "- The crossing on LLaVA is bracketed at $r \\in [5,6]$, not sharp; no architecture claim"),
    ("- Counterfactual validation: $\\Gamma$-based allocation reduces uncertainty by $32\\times$",
     "- **Negative results reported**: the rule's advantage does not survive our own controls"),
    ("│   ├── paper_ICLR_backup/  ← ICLR format backup\n",
     ""),
    ("│   ├── paper_ieee/         ← IEEE TNNLS version\n",
     "│   ├── paper_ieee/         ← IEEEtran version (submitted to Pattern Recognition Letters)\n"),
    ("| Experiments | 116 | 224 | 181 |", "| Experiments | 116 | 224 | 126 + 57 |"),
]

TAIL = """

---

## Hardware and environment

Every run in this repository was produced on one of two configurations, and the archived
run records state which:

| Configuration | Used for | Notes |
|---|---|---|
| Local workstation | LLaVA-1.5-7B sweeps, CLIP retrieval sweeps | **NVIDIA RTX 4060 Laptop, 8 GB**; QLoRA 4-bit; ~34 min per LLaVA run |
| Cloud | Qwen2-VL-7B sweeps | NVIDIA A800 80 GB |
| CPU only | a small number of Qwen2-VL-2B runs (marked per run) | bf16; initial energy differs from GPU by 0.09%, recorded per run so runs are not mixed |

Peak memory for the local runs fits in 8 GB with QLoRA 4-bit and `batch=1`. Runs are
single-GPU and sequential; the repository does not require a cluster.

## Data availability

Datasets and model releases used here are **public**: Alpaca, ShareGPT, MS-COCO, Flickr30k,
ImageNet (subset), and the HuggingFace model cards for CLIP ViT-B/32, LLaVA-1.5-7B,
Qwen2-VL-7B and Qwen2-VL-2B.

What this repository adds is **derived data**: the per-run result JSON files under
`outputs/`, the analysis scripts that compute every statistic reported in the papers, and
the training configurations. Those are archived here. **Each paper's numbers can be traced
to a named script and a named JSON field** — the per-run records are append-only and each
carries its own hyper-parameters, so an aggregate file being rewritten cannot silently
change a cited number.

## Citation

If you use this code or these results, please cite the corresponding paper:

```bibtex
@article{wan2026gradient,
  title   = {Gradient Structure Laws as Predictors of {PEFT} Design:
             Zero-Shot Cross-Architecture Rank Allocation},
  author  = {Wan, Hongrui},
  journal = {Pattern Recognition Letters},
  note    = {Manuscript PRLETTERS-D-26-02378, under revision},
  year    = {2026}
}
```

## License

See `LICENSE` in this repository.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(RM, encoding="utf-8", errors="replace").read()
    print(f"  README {len(t):,} 字符 / {len(t.splitlines())} 行")
    applied = 0
    for old, new in PAIRS:
        n = t.count(old)
        if n:
            t = t.replace(old, new)
            applied += n
            print(f"  ✅ 替换 {n} 处：{old.splitlines()[0][:60]}")
    # 关键撤回串是否已清
    print()
    print("  复核（不应残留）：")
    ok = True
    for bad, label in (("unique admissible PEFT allocation statistic", "unique 主张"),
                       ("reduces uncertainty by", "32x 主张"),
                       ("phase transition at $r_c", "sharp 相变"),
                       ("Prepared for IEEE TNNLS", "TNNLS 状态"),
                       ("181 runs", "旧计数"),
                       ("ICLR format backup", "ICLR 残留")):
        n = t.count(bad)
        # 允许"negative results"这类否定语境
        flag = n == 0
        ok = ok and flag
        print(f"  {'✅' if flag else '🔴'} {label}: {n} 处")
    if not a.apply:
        print("  （预演）")
        return 0
    if "## Hardware and environment" not in t:
        t = t.rstrip() + TAIL
        print("  ✅ 已追加 Hardware / Data availability / Citation / License 四节")
    bak = RM.with_suffix(".md.bak_p558")
    if not bak.exists():
        shutil.copy2(RM, bak)
    io.open(RM, "w", encoding="utf-8", newline="").write(t.rstrip() + "\n")
    t2 = io.open(RM, encoding="utf-8", errors="replace").read()
    print(f"  → {len(t2):,} 字符 / {len(t2.splitlines())} 行")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
