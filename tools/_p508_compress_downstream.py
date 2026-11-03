# -*- coding: utf-8 -*-
r"""压缩下游检验三块（`experiments.tex`）（2026-10-13）。

## 依据（`tools/_p507`）

`Counterfactual Validation` = **19,971 字符（全文 53%）**，其中三块共 **7,718**：
| 块 | 现字符 | 目标 | 保留要点 |
|---|---|---|---|
| `A downstream check` | 2,476 | ~1,300 | 两条件矛盾 + 分层相关系数 + 配对检验 + **否证结论** |
| `The same experiment on a decoder VLM` | 3,239 | ~1,500 | 预算翻转 + **撤回"符号由图像条件决定"** + **撤回架构依赖** |
| `The probe measured at the paper's own operating point` | 2,003 | ~1,600 | **595-vs-576 token、blank = 3.09×** + **两条边界**（样本依赖、n=2 反例） |

**⚠️ 三块都承载审稿人点名的结论**（R3.15/R3.16 下游、R1.4/R3.13/R3.14/R3.23 blank 探针）⇒
**只压措辞，不删结论、不删数字。**

    python tools\_p508_compress_downstream.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"

# ---------- ① 下游检验 ----------
D1_START = "\\textbf{A downstream check, and it does not go the way the energy would suggest.}"
D1_END = "diagnostic of representation geometry rather than a proxy for task accuracy."
D1_NEW = (
    r"\textbf{A downstream check, and it does not go the way the energy would suggest.}"
    "\n"
    r"Alignment energy is a statement about representation geometry, so it is worth asking"
    "\n"
    r"whether lowering it improves retrieval. We repeated the rank sweep on CLIP ViT-B/32"
    "\n"
    r"with real Flickr30k pairs ($1000$ images, five captions each; frozen baseline"
    "\n"
    r"$R@1 = 0.7058$), with LoRA on the text tower only, and compared it against the"
    "\n"
    r"blank-image protocol. The two conditions disagree by more than degree: at $n = 1024$"
    "\n"
    r"and $r = 16$, real pairs reach $R@1 = 0.7241$ while blank images reach $0.6927$---yet"
    "\n"
    r"it is the blank runs whose energy improves ($-0.0059$ against $-0.0004$). Correlations"
    "\n"
    r"must be read within condition, because a pooled coefficient is dominated by the"
    "\n"
    r"difference between conditions rather than by any trend inside one. Pooled over all"
    "\n"
    r"$78$ runs the two correlate at $-0.374$; within the $54$ runs whose energy actually"
    "\n"
    r"falls---the only ones that could support a ``lower energy, better task'' reading---the"
    "\n"
    r"correlation is $+0.172$, i.e.\ no relationship; and the training-condition energy, the"
    "\n"
    r"quantity closest to the $\Delta E$ this paper reports, correlates at $+0.478$, so a"
    "\n"
    r"larger energy reduction accompanies a \emph{smaller} downstream gain. The cleanest"
    "\n"
    r"evidence is paired and assumes no correlation structure: fixing rank, training size and"
    "\n"
    r"seed and swapping real images for blank ones, at $n = 16$ the swap significantly lowers"
    "\n"
    r"energy ($21$ of $21$ pairs, Wilcoxon $p = 9.5\times10^{-7}$) and significantly improves"
    "\n"
    r"retrieval ($21$ of $21$, $p = 5.9\times10^{-5}$), whereas at $n = 1024$ it leaves energy"
    "\n"
    r"unchanged ($7$ positive of $18$, $p = 0.90$) and significantly degrades retrieval"
    "\n"
    r"($18$ of $18$, $p = 7.6\times10^{-6}$). An energy change is thus neither sufficient nor"
    "\n"
    r"necessary for the direction of downstream performance: minimising $E$ does not reliably"
    "\n"
    r"improve retrieval, and $E$ is a diagnostic of representation geometry rather than a"
    "\n"
    r"proxy for task accuracy."
)

# ---------- ② 解码器 VLM ----------
D2_START = "\\textbf{The same experiment on a decoder VLM, and the sharpest form of the"
D2_END = "stable at that budget rather than at full resolution."
D2_NEW = (
    r"\textbf{The same experiment on a decoder VLM.} To check that this is not an artefact of"
    "\n"
    r"a dual encoder we repeated the sweep on Qwen2-VL-2B (LoRA on $q,k,v,o$, vision tower"
    "\n"
    r"frozen) with real COCO validation pairs, at ranks $\{1,2,4,5,6,8,16\}$ and three seeds"
    "\n"
    r"per cell. Rank behaviour is stable---no sign flip at any rank in either condition,"
    "\n"
    r"$7$ of $7$---but the condition comparison does not survive a change of visual budget,"
    "\n"
    r"and we report that plainly. At $15$ tokens real pairs give a positive $\Delta E$ at all"
    "\n"
    r"seven ranks ($+194$ to $+450$) and blank images a negative one ($-519$ to $-185$), so"
    "\n"
    r"the sign appears to track the image condition; raising the budget to $54$ tokens"
    "\n"
    r"reverses it (real pairs $-554$, $-471$; the paired comparison flips from $-699$ to"
    "\n"
    r"$+394$). We therefore withdraw the claim that the sign of $\Delta E$ is determined by"
    "\n"
    r"the image condition. It is determined by the image condition \emph{at a given budget},"
    "\n"
    r"which is a sharper statement about the probe than about the images. The initial real--blank gap is $50.9\%$ at $54$ tokens ($14{,}718$ against"
    "\n"
    r"$22{,}207$) but only $2.9\%$ at $15$ ($21{,}753$ against $22{,}373$): compressing the"
    "\n"
    r"visual budget destroys the information that separates real content from none, so at a"
    "\n"
    r"low budget a blank image and a real one are nearly the same input. That budget is"
    "\n"
    r"rarely reported or varied in this line of work, which is why the relation between the"
    "\n"
    r"objective and real multimodal content is not interpretable across budgets. The same"
    "\n"
    r"control also removes an architecture contrast we had been reporting: at $54$ tokens the"
    "\n"
    r"decoder's real-image runs turn negative too, so the dual-encoder-versus-decoder"
    "\n"
    r"difference was very likely an artefact of the token budget. The sharper result is what"
    "\n"
    r"happens when the trained model is evaluated on \emph{held-out real} images rather than"
    "\n"
    r"on its own training condition: the real-pair runs then improve at every rank ($-135$ to"
    "\n"
    r"$-271$) while the blank-image runs cross from $-260$ at $r = 1$ to $+179$ at $r = 16$."
    "\n"
    r"Training on blank images only looks like it improves alignment when alignment is"
    "\n"
    r"measured on blank images. One asymmetry we do not hide: at $n = 16$ the dual encoder's"
    "\n"
    r"real-image training lowers $\Delta E$ while the decoder's raises it, so the sign of the"
    "\n"
    r"effect of real data depends on the architecture---which weakens any simple claim that"
    "\n"
    r"real images are uniformly better even as it strengthens the case against blank probes."
    "\n"
    r"This run used $15$ visual tokens per sample, so the direction is claimed at that budget"
    "\n"
    r"rather than at full resolution."
)

# ---------- ③ 操作点探针（保留两条边界） ----------
D3_START = "\\textbf{The probe measured at the paper's own operating point.}"
D3_END = "$n = 16$ curve and flag the counter-example rather than quote a percentage."
D3_NEW = (
    r"\textbf{The probe measured at the paper's own operating point.} The comparison above is"
    "\n"
    r"about a probe measured at a particular budget, so we measured the budget dependence"
    "\n"
    r"directly. This needs no training---the initialization energy is one forward pass and is"
    "\n"
    r"therefore deterministic given an input, with no seed noise---so we could sweep to the"
    "\n"
    r"paper's own operating point rather than extrapolate to it. On one fixed set of $16$"
    "\n"
    r"samples, $E_0$ for real images falls monotonically as the budget grows: $21{,}752$ at"
    "\n"
    r"$15$ tokens, $14{,}718$ at $55$, $9{,}150$ at $188$ and $7{,}472$ at $595$, a fall of"
    "\n"
    r"$66\%$; over the same range $E_0$ for blank images barely moves ($22{,}400$, $22{,}313$,"
    "\n"
    r"$22{,}697$, $23{,}118$, a spread under $5\%$). At the paper's operating point ($595$"
    "\n"
    r"tokens here against the paper's $576$) a blank image therefore sits at $3.09\times$ the"
    "\n"
    r"initialization energy of a real one. This is the sharpest form of the objection: at a"
    "\n"
    r"realistic budget a blank image is not an uninformative stand-in but a \emph{different}"
    "\n"
    r"input with three times the alignment energy, and the $\Delta E$ reported in this line"
    "\n"
    r"of work is measured against that inflated baseline. Two boundaries belong with the"
    "\n"
    r"number. The absolute percentage is sample-dependent---at $15$ tokens the same"
    "\n"
    r"measurement gives $3.0\%$ on this sample set and $18.6\%$ on a held-out one---so we"
    "\n"
    r"report a trend within a fixed sample set rather than a single figure; and the trend is"
    "\n"
    r"not robust to very small samples, since two held-out samples reverse it at one budget"
    "\n"
    r"($+122\%$ at $15$ tokens against $+104\%$ at $55$). We therefore report the $n = 16$"
    "\n"
    r"curve and flag the counter-example."
)


def cut(t: str, start: str, end: str, new: str, label: str):
    i = t.find(start)
    j = t.find(end, i) if i >= 0 else -1
    if i < 0 or j < 0:
        print(f"  🔴 {label}: 锚点未命中（i={i}, j={j}）")
        return t, 0
    e = j + len(end)
    print(f"  {label}: {e - i:,} → {len(new):,} 字符（省 {e - i - len(new):,}）")
    return t[:i] + new + t[e:], e - i - len(new)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    print(f"  原 {len(t):,} 字符")
    saved = 0
    t, s = cut(t, D3_START, D3_END, D3_NEW, "③ 操作点探针")   # 从后往前
    saved += s
    t, s = cut(t, D2_START, D2_END, D2_NEW, "② 解码器 VLM")
    saved += s
    t, s = cut(t, D1_START, D1_END, D1_NEW, "① 下游检验")
    saved += s
    print(f"  ⇒ 共省 {saved:,} 字符 → {len(t):,}")
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p508")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "保留 3.09×": "$3.09\\times$" in t2,
        "保留两条边界（3.0% / 18.6%）": "$3.0\\%$" in t2 and "$18.6\\%$" in t2,
        "保留 n=2 反例": "+122\\%$ at $15$ tokens against $+104\\%$" in t2,
        "保留撤回'符号由图像条件决定'": "withdraw the claim that the sign" in t2,
        "保留两条件都改写检索": "$0.7241$" in t2 and "$0.6927$" in t2,
        "保留配对检验": "$p = 9.5\\times10^{-7}$" in t2,
        "保留 +0.172 分层系数": "$+0.172$" in t2,
        "保留 66% 下降": "$66\\%$" in t2,
        "字符数下降": len(t2) < len(io.open(bak, encoding="utf-8", errors="replace").read()),
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
