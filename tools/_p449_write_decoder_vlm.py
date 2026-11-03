# -*- coding: utf-8 -*-
r"""把解码器 VLM 的真实图文结果写进 P3（2026-10-13）。

## 已核（`outputs/analysis/p3d_qwen_ranksweep.json`，43 run）

模型 `Qwen2-VL-2B-Instruct`（bf16，LoRA q/k/v/o，**视觉塔冻结**），数据 **COCO val2014 真实图文**，
rank **{1,2,4,5,6,8,16}** × {real, blank} × 3 seed。

**① 无符号翻转，符号由图像条件决定、与 rank 无关**：

| 条件 | 逐 rank 均值范围 | 符号 |
|---|---|---|
| **blank** | −518.9 … −184.5 | **7/7 全负** |
| **real** | +193.6 … +449.9 | **7/7 全正** |

配对（同 rank 同 seed）blank−real：**21/21 全负**，均值 **−699.0**
⇒ **解码器 VLM 上同样未复现 $r_c\\in[5,6]$**，与论文自报"Qwen2-VL-7B 无相变"一致。

**② ⭐ 最锋利的一条（用 held-out 真实图复用评测 `dE_eval_real`）**：

| rank | real | blank |
|---|---|---|
| 1 | −236.0 | −260.2 |
| 4 | −211.0 | −28.9 |
| 6 | −212.8 | **+7.6** |
| 8 | −169.2 | **+149.2** |
| 16 | −134.7 | **+178.7** |

⇒ **用真实图测：real 7/7 全负（改善）；blank 随 rank 由负转正**（−260 → +179）
⇒ **"blank 改善对齐"只在你用 blank 测 E 时成立；换一组图结论就反过来。**

**③ 一处必须两边一起报的不一致**：n=16 下 **CLIP 双塔** real 的 $\\Delta E_{\\text{train}}$ 为**负**、
blank 为**正**；**Qwen 解码器恰好相反** ⇒ **"真实图文训练是否有益于对齐"的符号是架构相关的**
（加强"blank 不可外推"，但**削弱**"真实图文一定更好"的简单叙事）。

**④ 它自己标注的简化限制**：为控显存把图上限设为 `max_pixels=16384`（128×128）
→ **每样本只有 15 个 visual token** —— **这本身就是一种"简化视觉输入"，与被批评的 blank 同源**。
它据此**只主张"在低视觉 token 预算下差异显著且方向稳定"**，**不主张**完整分辨率下成立。

    python tools\_p449_write_decoder_vlm.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"

ANCHOR = "\\textbf{Blank images are not a neutral probe.}"

BLOCK = (
    "\\textbf{The same experiment on a decoder VLM, and the sharpest form of the\n"
    "blank-image problem.} To check that these conclusions are not an artefact of a dual\n"
    "encoder, we repeated the sweep on a decoder VLM---Qwen2-VL-2B with LoRA on\n"
    "$q,k,v,o$ and the vision tower frozen---using real image-text pairs from COCO\n"
    "validation, at ranks $\\{1,2,4,5,6,8,16\\}$ with three seeds per cell. No sign flip\n"
    "reappears: $\\Delta E$ is positive at all seven ranks for real pairs ($+194$ to\n"
    "$+450$) and negative at all seven for blank images ($-519$ to $-185$), so the sign is\n"
    "set by the image condition and not by rank at all ($21$ of $21$ paired comparisons\n"
    "negative). This is consistent with the absence of a transition we report for\n"
    "Qwen2-VL-7B. The sharper result is what happens when the same trained model is\n"
    "evaluated on \\emph{held-out real} images instead of on its own training condition:\n"
    "the real-pair runs then improve at every rank ($-135$ to $-271$), while the\n"
    "blank-image runs cross from $-260$ at $r = 1$ to $+179$ at $r = 16$. Training on\n"
    "blank images only looks like it improves alignment when alignment is measured on\n"
    "blank images. We note one asymmetry between architectures rather than hiding it: at\n"
    "$n = 16$ the dual encoder's real-image training \\emph{lowers} $\\Delta E$ while the\n"
    "decoder's \\emph{raises} it, so the sign of the effect of real data is\n"
    "architecture-dependent, which weakens any simple claim that real images are\n"
    "uniformly better even as it strengthens the case against blank probes. This run used a\n"
    "reduced visual budget (15 visual tokens per sample), so we claim the direction is\n"
    "stable at that budget rather than at full resolution.\n"
    "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    if "The same experiment on a decoder VLM" in t:
        print("  已写入")
        return 0
    n = t.count(ANCHOR)
    print(f"  锚点命中 {n}")
    if n != 1:
        print("  🔴 锚点未命中")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p449")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(
        t.replace(ANCHOR, BLOCK + ANCHOR, 1))
    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "含 Qwen2-VL-2B 与 COCO": "Qwen2-VL-2B" in t2 and "COCO" in t2,
        "含 7/7 全正与全负": "$+194$ to\n$+450$" in t2 and "$-519$ to $-185$" in t2,
        "含 21/21 配对": "$21$ of $21$" in t2,
        "含 held-out 翻转 −260→+179": "$-260$ at $r = 1$ to $+179$" in t2,
        "含'只在 blank 上测 E 才成立'": "only looks like it improves alignment when alignment is measured on" in t2,
        "含架构相关的符号不一致": "architecture-dependent" in t2,
        "含低视觉预算限制": "15 visual tokens per sample" in t2,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
