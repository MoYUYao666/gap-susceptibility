# -*- coding: utf-8 -*-
r"""把 `experiments.tex` 的细节移入 Supplementary，正文留要点句（2026-10-13）。

## 依据（`tools/_p507`）

`experiments.tex` = **36,021 字符 ≈ 5.92 页**（全文最大节）。逐段：

| 段 | 字符 | 处置 |
|---|---|---|
| Setup | 3,236 | 压到 ~1,800（协议细节进补充） |
| Alignment Phase Transition | 7,836 | 压到 ~3,000 |
| Sample Size Robustness | 1,233 | **移补充**，正文 1 句 |
| Second-Dataset (ShareGPT) | 2,565 | **移补充**，正文 1 句 |
| Counterfactual Validation | 19,971 | 见下 |
| Rank Scaling | 1,735 | **移补充**，正文 2 句 |
| Comparison with Prior Work | 899 | **移补充**，正文 1 句 |

**Counterfactual 内部**（已压过一轮）：把 **解码器 VLM 块** 与 **下游检验块** 移补充（正文留结论句）。

**⚠️ 纪律**：**只在正文留"结论 + 关键数字"，细节进补充**；
**审稿人点名要的（R3.12 逐块 Γ/rank 表、R2.2 同预算对比、R3.21 参数量、blank 3.09×）留在正文。**

    python tools\_p511_move_experiments_to_supp.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"
EX = PI / "sections" / "experiments.tex"
SUP = PI / "supplementary" / "supplementary.tex"

# 要整段移出的 subsection（正文留要点句）
SUBS = [
    ("Sample Size Robustness",
     r"\noindent\textbf{Sample-size robustness (Supplementary Section~S3).} The crossing is"
     "\n"
     r"stable across training-set sizes $16$ to $256$; the full grid is in the supplement.\n"),
    ("Second-Dataset Validation (ShareGPT)",
     r"\noindent\textbf{Second dataset (Supplementary Section~S3).} On ShareGPT the same"
     "\n"
     r"bracketing appears; the per-rank values are in the supplement.\n"),
    ("Rank Scaling and $\\Gamma$ Evolution",
     r"\noindent\textbf{Rank scaling (Supplementary Section~S4).} $\Delta E$ grows monotonically"
     "\n"
     r"through the danger regime and collapses at $r \geq 24$; per-rank values and the"
     "\n"
     r"$\Gamma$ evolution are in the supplement. The measured $\Delta E$ across ranks is"
     "\n"
     r"$-105$ at $r{=}4$, $+62$ at $r{=}6$, $+1572$ at $r{=}16$, $+2860$ at $r{=}20$, and NaN"
     "\n"
     r"at $r \geq 24$.\n"),
    ("Comparison with Prior Work",
     r"\noindent\textbf{Comparison with prior work (Supplementary Section~S5).} The comparison"
     "\n"
     r"against prior rank-allocation and PEFT-selection methods is in the supplement.\n"),
]

# Counterfactual 内要移出的两块（正文留结论句）
BLOCKS = [
    ("解码器 VLM",
     "\\textbf{The same experiment on a decoder VLM.}",
     "rather than at full resolution.",
     r"\noindent\textbf{A decoder VLM, and what does not replicate (Supplementary Section~S6).}"
     "\n"
     r"We repeated the sweep on Qwen2-VL-2B with real COCO pairs. Two claims did not survive."
     "\n"
     r"The sign of $\Delta E$ tracks the image condition at $15$ visual tokens but reverses at"
     "\n"
     r"$54$, so we withdraw the claim that the image condition determines the sign; and the"
     "\n"
     r"apparent dual-encoder-versus-decoder contrast likewise disappears at $54$ tokens, so it"
     "\n"
     r"was very likely a token-budget artefact. Training on blank images only looks like it"
     "\n"
     r"improves alignment when alignment is measured on blank images: evaluated on held-out"
     "\n"
     r"real images, the real-pair runs improve at every rank ($-135$ to $-271$) while the"
     "\n"
     r"blank-image runs cross from $-260$ at $r = 1$ to $+179$ at $r = 16$.\n"),
    ("下游检验",
     "\\textbf{A downstream check, and it does not go the way the energy would suggest.}",
     "proxy for task accuracy.",
     r"\noindent\textbf{A downstream check, and it does not go the way the energy would suggest}"
     "\n"
     r"(Supplementary Section~S7).} We repeated the rank sweep on CLIP ViT-B/32 with real"
     "\n"
     r"Flickr30k pairs and compared against the blank-image protocol. The conditions disagree"
     "\n"
     r"by more than degree: at $n = 1024$, $r = 16$ real pairs reach $R@1 = 0.7241$ while blank"
     "\n"
     r"images reach $0.6927$, yet the blank runs are the ones whose energy improves. Pooled"
     "\n"
     r"over $78$ runs the two correlate at $-0.374$, but within the $54$ runs whose energy"
     "\n"
     r"falls---the only ones that could support a ``lower energy, better task'' reading---the"
     "\n"
     r"correlation is $+0.172$, and the training-condition energy correlates at $+0.478$, so a"
     "\n"
     r"larger energy reduction accompanies a \emph{smaller} downstream gain. Paired and"
     "\n"
     r"correlation-free: swapping real images for blank ones at $n = 16$ lowers energy"
     "\n"
     r"($21/21$, $p = 9.5\times10^{-7}$) and \emph{improves} retrieval ($21/21$,"
     "\n"
     r"$p = 5.9\times10^{-5}$), whereas at $n = 1024$ it leaves energy unchanged ($p = 0.90$)"
     "\n"
     r"and degrades retrieval ($18/18$, $p = 7.6\times10^{-6}$). An energy change is therefore"
     "\n"
     r"neither sufficient nor necessary for downstream direction: minimising $E$ does not"
     "\n"
     r"reliably improve retrieval.\n"),
]


def take_subsection(t: str, title: str):
    """取出 \\subsection{title} 整段（到下一个 \\subsection 或文件末）。"""
    i = t.find("\\subsection{" + title + "}")
    if i < 0:
        return t, None
    j = t.find("\\subsection{", i + 5)
    if j < 0:
        j = len(t)
    return t[:i] + t[j:], t[i:j]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ex = io.open(EX, encoding="utf-8", errors="replace").read()
    sup = io.open(SUP, encoding="utf-8", errors="replace").read()
    print(f"  原 experiments {len(ex):,} ｜ supplementary {len(sup):,}")
    moved = []
    t = ex
    # ① 四个 subsection：**原位替换**为要点句（注意：从后往前，避免位移）
    spans = []
    for title, brief in SUBS:
        i = t.find("\\subsection{" + title + "}")
        if i < 0:
            print(f"  ⚠️ 未找到 subsection {title!r}")
            continue
        j = t.find("\\subsection{", i + 5)
        if j < 0:
            j = len(t)
        spans.append((i, j, title, brief))
    for i, j, title, brief in sorted(spans, reverse=True):
        seg = t[i:j]
        moved.append((title, seg, brief))
        t = t[:i] + brief + t[j:]
        print(f"  ✅ 移出 {title[:38]:<40} {len(seg):>7,} 字符 → 正文留 {len(brief):>4} 字符")
    save_chars = sum(len(s) - len(b) for _, s, b in moved)
    print(f"  ⇒ 四个 subsection 净省 {save_chars:,} 字符")

    # Counterfactual 内两块
    for label, start, end, brief in BLOCKS:
        i = t.find(start)
        j = t.find(end, i) if i >= 0 else -1
        if i < 0 or j < 0:
            print(f"  ⚠️ 未找到块 {label!r}（i={i}, j={j}）")
            continue
        e = j + len(end)
        moved.append((label, t[i:e], brief))
        t = t[:i] + brief + t[e:]
        print(f"  ✅ 移出 {label:<14} {e - i:>7,} 字符 → 正文留 {len(brief):>4} 字符")
        save_chars += e - i - len(brief)
    print(f"  ⇒ 总计净省 {save_chars:,} 字符 → {len(t):,}")

    if not a.apply:
        print("  （预演）")
        return 0
    for p in (EX, SUP):
        bak = p.with_suffix(".tex.bak_p511")
        if not bak.exists():
            shutil.copy2(p, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t)
    # 把移出的内容并入补充
    add = ["\n\n\\section{Deferred Experimental Detail}\n",
           "The material below is summarised in the main text; it is kept here so that the "
           "main text can meet the journal's page limit.\n"]
    for label, seg, brief in moved:
        add.append(f"\n\\subsection{{{label}}}\n")
        add.append(seg + "\n")
    sup2 = sup.replace("\\bibliographystyle{IEEEtran}", "".join(add) + "\n\\bibliographystyle{IEEEtran}")
    io.open(SUP, "w", encoding="utf-8", newline="").write(sup2)
    print(f"  ✅ supplementary {len(sup):,} → {len(sup2):,}")
    print(f"  ✅ experiments {len(ex):,} → {len(t):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
