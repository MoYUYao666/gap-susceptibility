# -*- coding: utf-8 -*-
r"""手写锚点移出 3 个下游检验块 + 种子出处块到 Supplementary（2026-10-13）。

## 依据（`tools/_p522` 诊断）

| 块 | 现字符 | 正文留 | 理由 |
|---|---|---|---|
| `A downstream check,` | 1,215 | ~500 | R3.15/R3.16 的**细节**；结论 + 关键数字留正文 |
| `A decoder VLM,` | 752 | ~450 | R1.4/R3.13 的细节 |
| `The probe measured at the paper's own operating point.` | 1,663 | ~900 | **3.09× 必须留**（R3.14/R3.23） |
| `Seed provenance and a numerical-environment control.` | 716 | ~350 | R3.17–R3.22 的**出处细节** |

**⇒ 目标：experiments 27,087 → ≈24,600（省 ~2,500）**

**⚠️ 与前两次失败的关键区别**：**只用"手写的完整段落字符串"做整块替换，
不用正则扫 `\begin/\end`** ⇒ **不可能破坏环境配平**。改完必跑配平断言。

    python tools\_p523_manual_block_moves.py [--apply]
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


def block(t: str, start: str, end: str):
    i = t.find(start)
    if i < 0:
        return None, -1, -1
    j = t.find(end, i)
    if j < 0:
        return None, i, -1
    return t[i:j + len(end)], i, j + len(end)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    orig = len(t)

    SPECS = [
        ("下游检验", "\\textbf{A downstream check,", "reliably improve retrieval.",
         r"""\noindent\textbf{A downstream check, and it does not go the way the energy
suggests (Supplementary Section~S7).} We repeated the rank sweep on CLIP ViT-B/32
with real Flickr30k pairs and compared it against the blank-image protocol. The
conditions disagree by more than degree: at $n=1024$, $r=16$ real pairs reach
$R@1=0.7241$ while blank images reach $0.6927$, yet it is the blank runs whose
energy improves. Pooled over $78$ runs the two correlate at $-0.374$, but within
the $54$ runs whose energy falls the correlation is $+0.172$, and the
training-condition energy correlates at $+0.478$---so a larger energy reduction
goes with a \emph{smaller} downstream gain. Paired and correlation-free, swapping
real images for blank ones at $n=16$ lowers energy ($21/21$, $p=9.5\times10^{-7}$)
and \emph{improves} retrieval ($21/21$, $p=5.9\times10^{-5}$), whereas at
$n=1024$ it leaves energy unchanged ($p=0.90$) and degrades retrieval ($18/18$,
$p=7.6\times10^{-6}$). An energy change is neither sufficient nor necessary for
the direction of downstream performance: minimising $E$ does not reliably improve
retrieval.
"""),
        ("解码器 VLM", "\\textbf{A decoder VLM,", "cross from $-260$ at $r = 1$ to $+179$ at $r = 16$.",
         r"""\noindent\textbf{A decoder VLM, and what does not replicate (Supplementary
Section~S6).} On Qwen2-VL-2B with real COCO pairs the rank behaviour is stable
(no sign flip at any rank, $7$ of $7$), but two claims did not survive a change of
visual budget. The sign of $\Delta E$ tracks the image condition at $15$ visual
tokens and reverses at $54$, so we withdraw the claim that the image condition
determines the sign; and the apparent dual-encoder-versus-decoder contrast
disappears at $54$ tokens, so it was very likely a token-budget artefact. Training
on blank images only looks like it improves alignment when alignment is measured
on blank images: evaluated on held-out real images the real-pair runs improve at
every rank ($-135$ to $-271$) while the blank-image runs cross from $-260$ at
$r=1$ to $+179$ at $r=16$.
"""),
        ("操作点探针", "\\textbf{The probe measured at the paper's own operating point.}",
         "curve and flag the counter-example.",
         r"""\noindent\textbf{The probe at the paper's own operating point.} The comparison
above is about a probe at a particular budget, so we measured the budget dependence
directly. This needs no training---the initialization energy is one forward pass and
is deterministic given an input---so we could sweep to the paper's own operating
point rather than extrapolate to it. On one fixed set of $16$ samples, $E_0$ for
real images falls monotonically: $21{,}752$ at $15$ tokens, $14{,}718$ at $55$,
$9{,}150$ at $188$ and $7{,}472$ at $595$, a fall of $66\%$; over the same range
$E_0$ for blank images barely moves ($22{,}400$, $22{,}313$, $22{,}697$,
$23{,}118$). At the paper's operating point ($595$ tokens here against the paper's
$576$) a blank image therefore sits at $3.09\times$ the initialization energy of a
real one. The objection is not that the images are blank but that at a realistic
budget a blank image is a \emph{different} input with three times the alignment
energy, and the $\Delta E$ reported in this line of work is measured against that
inflated baseline. Two boundaries: the absolute percentage is sample-dependent
($3.0\%$ on this sample set at $15$ tokens against $18.6\%$ on a held-out one), so
we report a trend within a fixed sample set; and two held-out samples reverse it at
one budget ($+122\%$ against $+104\%$), which is why we report the $n=16$ curve and
flag the counter-example.
"""),
    ]

    plans = []
    for label, s, e, new in SPECS:
        seg, i, j = block(t, s, e)
        if seg is None:
            print(f"  🔴 {label}: 锚点未命中（i={i}, j={j}）")
            return 1
        plans.append((label, seg, i, j, new))
        print(f"  {label:<14} {j - i:>7,} → {len(new):>6,} 字符（省 {j - i - len(new):>6,}）")
    saved = sum(len(s) - len(n) for _, s, _, _, n in plans)
    print(f"  ⇒ 计划省 {saved:,} → {orig - saved:,}")
    if not a.apply:
        print("  （预演）")
        return 0

    bak = EX.with_suffix(".tex.bak_p523")
    if not bak.exists():
        shutil.copy2(EX, bak)
    for label, seg, i, j, new in sorted(plans, key=lambda x: -x[2]):
        t = t[:i] + new + t[j:]
    io.open(EX, "w", encoding="utf-8", newline="").write(t)

    # 移出内容并入补充
    sup = io.open(SUP, encoding="utf-8", errors="replace").read()
    add = ["\n\n\\section{Deferred Downstream and Probe Detail}\n",
           "Summarised in the main text; kept here so that the main text can meet the "
           "journal's page limit.\n"]
    for label, seg, _, _, _ in plans:
        add.append(f"\n\\subsection{{{label}}}\n{seg}\n")
    sup2 = sup.replace("\\bibliographystyle{IEEEtran}", "".join(add) + "\n\\bibliographystyle{IEEEtran}")
    io.open(SUP, "w", encoding="utf-8", newline="").write(sup2)

    # ⚠️ 配平断言（写盘后复核）
    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    print()
    ok = True
    for name in ("table", "table*", "figure", "figure*", "tabular", "itemize"):
        nb = len(re.findall(r"\\begin\{" + re.escape(name) + r"\}", t2))
        ne = len(re.findall(r"\\end\{" + re.escape(name) + r"\}", t2))
        good = nb == ne
        ok = ok and good
        print(f"  {'✅' if good else '🔴'} {name:<9} begin {nb} ｜ end {ne}")
    print(f"  → experiments {orig:,} → {len(t2):,} ｜ supplementary {len(sup):,} → {len(sup2):,}")
    print(f"  **判定：{'✅ 环境配平' if ok else '🔴 环境不配平'}**")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
