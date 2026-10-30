# -*- coding: utf-8 -*-
r"""修复 README：把已撤回主张的更正应用到**仓库根与发布目录两处**（2026-10-14）。

## 我的第 35 个错

`_p558` 只改了 **`publish_clean/README.md`**；随后 `_p571`/`_p574` 的同步把
**仓库根 `README.md`（旧版，3,527 字符）复制进 `publish_clean/`** ⇒ **覆盖掉修改** ⇒
推送出去的是**旧 README**（仍在宣传 `unique` / `phase transition $r_c$` / `32×` / `181 runs` / TNNLS）。

**⇒ 教训：改"发布件"必须改**源头**（仓库根），而不是只改发布副本 —— 否则下一次同步就回滚。**
**⇒ 本脚本把修复应用到两处，并让同步脚本以后跳过 README 覆盖。**

    python tools\_p579_fix_readme_both.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
TARGETS = [REPO / "README.md", PC / "README.md"]

MARK_OLD = ["the unique admissible PEFT allocation statistic",
            "reduces uncertainty by",
            "phase transition at $r_c",
            "Prepared for IEEE TNNLS",
            "181 runs"]

PAIRS = [
    ("- **Representation Theorem**: $\\Gamma = \\langle \\nabla E, u \\rangle$ is the unique admissible PEFT allocation statistic",
     "- **Representation Theorem**: $\\Gamma$ is canonical up to positive scaling **given R1-R5 and the additivity axiom R3'**. "
     "R3 alone does not imply R3' --- we prove that with a counterexample ($\\|\\nabla E\\|^2$ is block-decomposable but not additive)"),
    ("- Alignment phase transition at $r_c \\in [5,6]$ on LLaVA; no transition on Qwen-VL",
     "- The crossing in alignment energy on LLaVA is **bracketed** at $r \\in [5,6]$, not sharp; "
     "its location belongs to the measurement protocol, and we do not claim an architecture dependence"),
    ("- Counterfactual validation: $\\Gamma$-based allocation reduces uncertainty by $32\\times$",
     "- **Negative results we report rather than hide**: the allocation rule beats the uniform-rank baseline at one "
     "learning rate, reverses at another, and vanishes under matched training loss; it is indistinguishable from a "
     "random allocation at the same parameter budget; and AdaLoRA, swept over the same learning rates, reaches lower "
     "alignment energy than any of our arms"),
    ("- 181 runs, 2 architectures (LLaVA-1.5-7B, Qwen2-VL-7B), 4 sample sizes",
     "- 126 runs on the present protocol plus a 57-run capacity-matched allocation study; "
     "2 architectures (LLaVA-1.5-7B, Qwen2-VL-7B)"),
    ("- **Prepared for IEEE TNNLS**",
     "- **Submitted to Pattern Recognition Letters** (`PRLETTERS-D-26-02378`, decision: Revise)"),
    ("| Experiments | 116 | 224 | 181 |", "| Experiments | 116 | 224 | 126 + 57 |"),
    ("| Key Result | Text-only is optimal | ODE $R^2 > 0.97$ | Phase transition $r_c \\in [5,6]$ |",
     "| Key Result | Text-only is optimal | ODE $R^2 > 0.97$ | Zero-shot allocation without target gradients |"),
    ("| Status | → Pattern Recognition | Ready | → IEEE TNNLS |",
     "| Status | → Pattern Recognition | Ready | → PRL (Revise) |"),
    ("│   ├── paper_ICLR_backup/  ← ICLR format backup\n", ""),
    ("│   ├── paper_ieee/         ← IEEE TNNLS version\n",
     "│   ├── paper_ieee/         ← IEEEtran version (submitted to Pattern Recognition Letters)\n"),
    ("outputs/            # Results (224 runs Paper2, 181 runs Paper3)",
     "outputs/            # Results (224 runs Paper2, 126 + 57 runs Paper3)"),
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
| CPU only | a few Qwen2-VL-2B runs (marked per run) | bf16; initial energy differs from GPU by 0.09%, recorded per run so runs are not mixed |

Peak memory for the local runs fits in 8 GB with QLoRA 4-bit and `batch=1`. Runs are
single-GPU and sequential; no cluster is required.

## Data availability

Datasets and model releases used here are **public**: Alpaca, ShareGPT, MS-COCO, Flickr30k,
an ImageNet subset, and the HuggingFace model cards for CLIP ViT-B/32, LLaVA-1.5-7B,
Qwen2-VL-7B and Qwen2-VL-2B.

What this repository adds is **derived data**: the per-run result JSON files under
`outputs/`, the analysis scripts that compute every statistic reported in the papers, and
the training configurations. **Every number in the papers traces to a named script and a
named JSON field.** The per-run records are append-only and each carries its own
hyper-parameters, so a rewritten aggregate file cannot silently change a cited number.

A versioned snapshot of this repository is archived on Zenodo; see the badge above
(DOI minted from the `v1.0-prl-revision` release).

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
    # 以 publish_clean 的新版为准重建（若已丢，则从旧版重新施加修改）
    src = None
    for p in TARGETS:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        if "Hardware and environment" in t and "bracketed" in t:
            src = t
            print(f"  ✅ 找到已有新版本：{p}")
            break
    if src is None:
        base = io.open(TARGETS[0], encoding="utf-8", errors="replace").read()
        print(f"  两个 README 都是旧版（{len(base):,} 字符）⇒ 从旧版重新施加修改")
        t = base
        n_applied = 0
        for old, new in PAIRS:
            c = t.count(old)
            if c:
                t = t.replace(old, new)
                n_applied += c
        if "## Hardware and environment" not in t:
            t = t.rstrip() + TAIL
        src = t
        print(f"  应用 {n_applied} 处替换 + 追加四节 ⇒ {len(t):,} 字符")

    print()
    print("  复核（新版本不应含）：")
    ok = True
    for m in MARK_OLD:
        n = src.count(m)
        ok = ok and n == 0
        print(f"  {'✅' if n == 0 else '🔴'} 「{m}」：{n} 处")
    print(f"  新版本含四节：{[s for s in ('Hardware and environment','Data availability','Citation','License') if s in src]}")
    print(f"  字符数：{len(src):,}")

    if not a.apply:
        print("  （预演）")
        return 0
    for p in TARGETS:
        bak = p.with_suffix(".md.bak_p579")
        if p.exists() and not bak.exists():
            shutil.copy2(p, bak)
        io.open(p, "w", encoding="utf-8", newline="").write(src)
        print(f"  ✅ 已写 {p.relative_to(REPO)}（{len(src):,} 字符）")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
