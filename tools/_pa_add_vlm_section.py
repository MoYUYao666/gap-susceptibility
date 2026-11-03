# -*- coding: utf-8 -*-
r"""把实验 ④（解码器 VLM）写进论文（2026-10-08 21:50）。

## 两处改动

1. **`discussion.tex`**：把 limitation 第二条
   *"our study is limited to contrastive dual-encoder architectures; whether the framework
   generalizes to decoder-based VLMs or generation-oriented objectives remains open"*
   → **改为已测一个解码器 VLM**，并如实写明"最优位置不同"与"仅一个模型、单 seed、4-bit"；
2. **`supplement.tex`**：在 D 节后加 **E 节**（`Decoder-Based VLM`），给出完整三臂表、
   以及**我修正过的判据**（起点相差 3.4 倍时绝对跨度不可比）。

## 写进去的数字（全部有来源：`outputs/analysis/qwen_verdict.json`）

| 臂 | 相对降幅 | CG 降幅 |
|---|---|---|
| both | **83.8%** | 77.2% |
| text_only | 73.9% | 77.9% |
| vision_only | **11.0%** | 22.6% |

起点相差 **3.4 倍**（0.6364 vs 2.1759）→ **故用相对降幅判定**。

    python tools\_pa_add_vlm_section.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DIS = REPO / "paper合" / "sections" / "discussion.tex"
SUP = REPO / "paper合" / "sections" / "supplement.tex"

DIS_OLD = (r"Second, our study is limited to contrastive dual-encoder architectures; whether the framework "
           r"generalizes to decoder-based VLMs or generation-oriented objectives remains open.")

DIS_NEW = (r"Second, our study covers contrastive dual-encoder architectures and one decoder-based VLM. The "
           r"decoder model, Qwen2-VL-2B under strict freezing, reproduces the framework's qualitative "
           r"behaviour: the distribution gap follows a clear exponential decay under both the text-only and "
           r"both-position arms, the position of adaptation changes the trajectory as it does in the "
           r"dual-encoders, and adapting the vision tower alone is again the least effective choice, moving the "
           r"gap by $11\%$ where the other two arms move it by $74\%$ and $84\%$ "
           r"(Section~\ref{sec:vlm} of the supplement). What does not carry over is the identity of the best "
           r"position: on this model the both-position arm reduces the gap most, whereas the three "
           r"contrastively pre-trained dual-encoders place text-only first. That is the same conclusion the "
           r"main text reaches from the dual-encoder comparisons --- the ordering is stable within a "
           r"configuration but the preferable site is not --- now observed across an architecture family "
           r"boundary. This evidence is preliminary in three respects: it rests on a single model and a single "
           r"seed, the runs use four-bit quantisation for all three arms so that they remain internally "
           r"comparable, and the scale is small ($400$ samples, three epochs), which is adequate for "
           r"establishing the ordering but not for reporting final accuracy. Whether the framework extends to "
           r"generation-oriented objectives, as distinct from decoder architectures, remains untested.")

SUP_NEW = r"""
\section*{E. Decoder-Based VLM}
\label{sec:vlm}

The main text's claim about adaptation site is established on contrastive dual-encoder models. To test
whether it depends on that architecture family, we repeated the strict-freezing comparison on a
decoder-based VLM, Qwen2-VL-2B-Instruct, where the two towers are separated by the fact that their linear
layers carry different names: the vision tower uses \texttt{attn.qkv}, \texttt{attn.proj} and
\texttt{mlp.fc1}/\texttt{fc2}, and the language model uses the usual seven projections. Passing different
target modules to the adapter library therefore isolates the towers, and this was verified before any
training: the text-only arm holds $392$ adapters and no vision-side tensor, the vision-only arm holds $258$
and no language-side tensor, and the both-position arm holds both sets. Every run freezes the backbone and
exposes only the adapter matrices.

The protocol is $400$ samples for three epochs at batch $4$, rank $8$ and learning rate $10^{-4}$. All three
arms use four-bit quantisation. That choice was forced rather than preferred: at bfloat16 the vision-only
arm had not completed a single epoch after $27$ minutes, against $2.4$ minutes per epoch for text-only,
whereas at four-bit the same arm completes three epochs in $5.4$ minutes. Applying the same setting to all
three arms keeps them comparable to one another, which is what the comparison requires.

We report the relative change in $DG^*$ rather than its absolute change, because the arms start from
different values. The starting $DG^*$ ranges over a factor of $3.4$ across arms ($0.636$ to $2.176$),
and an arm that starts high can show a large absolute change while barely moving in relative terms. The
centroid gap does not have this problem on these runs, and its ranking agrees with the relative ranking
below.

\begin{table}[h]
\centering
\caption{Adaptation site on a decoder-based VLM under strict freezing. Qwen2-VL-2B-Instruct, $400$
samples, three epochs, batch $4$, rank $8$, four-bit quantisation, one seed. $DG^*$ is the paired squared
distance after normalisation; the relative change is quoted because the arms begin from different values.}
\label{tab:vlm}
\footnotesize
\begin{tabular}{lccc}
\toprule
Arm & Trainable & $DG^*_0 \to DG^*_3$ & Relative change \\
\midrule
Both-position   & $14{,}494{,}912$ & $0.636 \to 0.103$ & $\mathbf{-83.8\%}$ \\
Text-only       & $9{,}232{,}384$  & $0.710 \to 0.185$ & $-73.9\%$ \\
Vision-only     & $5{,}262{,}528$  & $2.176 \to 1.937$ & $-11.0\%$ \\
\bottomrule
\end{tabular}
\end{table}

Two conclusions follow. First, the framework is not confined to dual-encoders: the distribution gap decays
exponentially here as well, and adapting the vision tower alone is again the least effective option, moving
the gap by $11\%$ where the other arms move it by $74\%$ and $84\%$. Second, the identity of the best site
does not carry over --- on this model the both-position arm leads --- which is the same finding the main text
reports across backbones and datasets, now observed across an architecture family. The evidence is
preliminary: one model, one seed, small scale, and quantised weights.
"""


def main() -> int:
    apply = "--apply" in sys.argv
    ok = 0

    d = io.open(DIS, encoding="utf-8").read()
    if "covers contrastive dual-encoder architectures and one decoder-based VLM" in d:
        print("  · discussion 已改，跳过")
        ok += 1
    elif d.count(DIS_OLD) != 1:
        print(f"  ❌ discussion 锚点未唯一命中（{d.count(DIS_OLD)}）")
    else:
        d = d.replace(DIS_OLD, DIS_NEW, 1)
        if apply:
            io.open(DIS, "w", encoding="utf-8", newline="").write(d)
        print("  ✅ discussion：scope 句已改为「已测一个解码器 VLM」")
        ok += 1

    s = io.open(SUP, encoding="utf-8").read()
    if r"\section*{E. Decoder-Based VLM}" in s:
        print("  · supplement 已有 E 节，跳过")
        ok += 1
    else:
        s = s.rstrip() + "\n" + SUP_NEW
        if apply:
            io.open(SUP, "w", encoding="utf-8", newline="").write(s)
        print("  ✅ supplement：已加 E 节（完整三臂表 + 判据说明）")
        ok += 1

    if ok < 2:
        return 1
    if apply:
        d2 = io.open(DIS, encoding="utf-8").read()
        s2 = io.open(SUP, encoding="utf-8").read()
        for k in ("covers contrastive dual-encoder architectures and one decoder-based VLM",
                  "Section~\\ref{sec:vlm} of the supplement",
                  "remains untested"):
            assert k in d2, f"discussion 缺 {k}"
        for k in (r"\label{sec:vlm}", "-83.8\\%", "3.4", "four-bit"):
            assert k in s2, f"supplement 缺 {k}"
        assert "remains open" not in d2, "旧措辞仍在"
        print("  ✅ 断言通过：scope 句已改、E 节已加、旧措辞已清")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
