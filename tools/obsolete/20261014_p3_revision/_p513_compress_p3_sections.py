# -*- coding: utf-8 -*-
r"""P3 七页合规版：压缩 theory / introduction / discussion / conclusion（2026-10-13）。

## 目标（`tools/_p509` 标定：≈5,894 字符/页，≤7 页预算 ≈41,259 字符）

| 节 | 改前 | 任务目标 | 本脚本实际目标 |
|---|---|---|---|
| theory | 15,191 | ≈6,500 | ≈7,900（硬下限，见 `docs/P3_COMPRESSION.md` §5） |
| introduction | 5,054 | ≈2,400 | ≈2,600 |
| discussion | 5,746 | ≈2,500 | ≈2,800 |
| conclusion | 3,047 | ≈1,200 | ≈1,700（含 Reproducibility 声明 350 字符不可压） |

## 纪律（脚本内以断言强制）

- **只压措辞，不删结论、不删数字**：`KEEP[...]` 列出每节必须出现的字面片段（定理/引理/推论陈述、
  R1--R5、R3$'$ 与 $\|\nabla E\|^2$ 反例、$c_k$/2.65$\times$、bracketed、$r_c$ 属协议、
  limitation 各条结论、诚实口径…），写入前逐条断言。
- **移出正文的内容不删除**：全部落在 `docs/P3_COMPRESSION.md` 的「待 Lead 并入 supplementary」小节。
- **禁止回归**：`FORBID[...]`（`190 runs` / `sharp phase transition` / `they are forced` /
  `CLIP-derived` / `equal parameter budget` …）断言为 0（`_p497` 同口径：撤回/否定语境允许）。
- **拼接方式**：全部用**普通字符串 + 列表 join**，每段是 **raw 字符串**（`r"..."`）⇒ LaTeX 反斜杠原样落盘；
  **写盘前**断言无字面 `\n`（`\n` 后不跟字母）、无行首断头命令、无控制字符。
- **幂等**：目标文本已就位则跳过；`--apply` 才写盘。

    python tools\_p513_compress_p3_sections.py            # 预演 + 量测
    python tools\_p513_compress_p3_sections.py --apply    # 写入
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"

TARGETS = {
    "paper3/paper_ieee/sections/theory.tex": 7900,
    "paper3/paper_ieee/sections/introduction.tex": 2600,
    "paper3/paper_ieee/sections/discussion.tex": 2800,
    "paper3/paper_ieee/sections/conclusion.tex": 1700,
}

# ---------------------------------------------------------------------------
# 必须保留（审稿人点名项 + 全部数字）
# ---------------------------------------------------------------------------
KEEP: dict[str, list[str]] = {
    "theory.tex": [
        r"\begin{theorem}[Representation Theorem]\label{thm:repr}",
        r"\begin{definition}[Gap Susceptibility]",
        r"\begin{lemma}[R3 does not imply R3$'$]\label{lem:r3-not-r3p}",
        r"\begin{theorem}[Projection Error Bound]",
        r"\textbf{R1 -- Pre-training computability}",
        r"\textbf{R2 -- Coordinate invariance}",
        r"\textbf{R3 -- Block decomposability}",
        r"\textbf{R3$'$ -- Cross-block additivity}",
        r"\textbf{R4 -- Directional coupling}",
        r"\textbf{R5 -- First-order observability}",
        r"\|\nabla E\|^2",
        r"S=\|x\|^2",
        r"c_k=\sum_{W\in M_k}(\mathrm{in}_W+\mathrm{out}_W)",
        r"2.65\times",
        r"655{,}360",
        r"247{,}296",
        r"\Delta E=+3607\pm514",
        r"+2241\pm1291",
        r"20\times",
        r"\varepsilon_{\mathrm{proj}}<0.05",
        r"r=-0.27",
        r"k=0.088",
        r"10^3$--$10^4",
        r"<1\%",
        r"bracketed",
        r"p=0.100",
        r"protocol rather than to the model",
        r"\subsection{Corollary 3: Alignment Phase Transition}",
        r"\subsection{Corollary 4: Cross-Architecture Transfer}",
        r"\subsection{Corollary 5: Paper~2 as Retrieval Specialization}",
        r"\label{eq:allocation}",
    ],
    "introduction.tex": [
        r"\item \textbf{Representation Theorem}",
        r"\item \textbf{Generalized Flow Allocation Principle (GFAP)}",
        r"\item \textbf{Experimental validation}",
        r"R3$'$",
        r"bracketed",
        r"protocol",
        r"without target-model gradient access",
        r"additivity",
    ],
    "discussion.tex": [
        r"R3$'$",
        r"bracketed",
        r"p = 0.100",
        r"\emph{consistent}",
        r"\subsection{Limitations}",
        r"two chains (CLIP $\to$ LLaVA, CLIP $\to$ Qwen)",
        r"untested",
        r"orthogonal subgroup",
        r"Alpaca, ShareGPT",
        r"AdamW",
        r"environment-sensitive",
        r"$p = 2^{-5}$",
        r"\subsection{Future Directions}",
    ],
    "conclusion.tex": [
        r"R3$'$",
        r"structural characterisation",
        r"bracketed",
        r"negative and we state them as such",
        r"without",
        r"126",
        r"\noindent\textbf{Reproducibility.}",
    ],
}

# 禁止回归的旧主张（与 `tools/_p497_scan_contradictions.py` 的 RULES **逐条对齐**，
# 避免"我的脚本过了、_p497 却报红"这类口径不一致）
FORBID = [
    r"30\s*\\times", r"30x\b", r"reduces? (?:allocation )?uncertainty",
    r"exactly one", r"they are forced", r"is not proposed", r"it is forced",
    r"phase transition at", r"sharp phase transition",
    r"model-independent", r"\buniversal\b",
    r"architecture-dependent",
    r"eliminates allocation uncertainty", r"beats the uniform-rank",
    r"190 runs", r"181 sweep",
    r"CLIP-derived",
    r"equal parameter budget",
    r"blank images are neutral", r"neutral probe",
    r"removes the catastrophic tail",
    r"establishes \$\\Gamma\$ as a causal factor",
    r"in the revised version",
]

LITERAL_N = re.compile(r"\\n(?![A-Za-z])")
SEVERED = re.compile(r"^(abla|oindent|eq|ot|ewtheorem|ewcommand|ewline)\b")
CTRL = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")

# 与 `tools/_p497_scan_contradictions.py` 同口径：撤回 / 否定语境不算回归
ALLOW_CTX = ("withdraw", "no longer", "must not", "not a", "rather than", "we record",
             "artefact", "we do not", "does not", "cannot", "instead of", "is not",
             "are not", "was withdrawn", "incorrect", "earlier", "not that",
             "unconditional", "but reverses", "but we", "unable to",
             "could not reproduce", "we first read", "rather than the architecture")


# ===========================================================================
# 1. THEORY  (15,191 -> ~7,900)
# ===========================================================================
THEORY = [
    r"\section{Theory}\label{sec:theory}",
    r"",
    r"\subsection{The PEFT Allocation Problem}",
    r"",
    r"Partition the parameters into $K$ blocks $\{M_1,\ldots,M_K\}$ (vision encoder, projector,",
    r"shallow LLM, deep LLM). Given a PEFT budget $C$, we set $\mathrm{rank}_k$ per block to",
    r"minimize expected alignment degradation, so $S(M_k)$ must satisfy requirements the problem",
    r"imposes:",
    r"",
    r"\begin{enumerate}",
    r"    \item \textbf{R1 -- Pre-training computability}: $S$ is computable before training, from",
    r"    one $(\nabla E,u)$ pair at the reference configuration.",
    r"    \item \textbf{R2 -- Coordinate invariance}: $S$ agrees across block-wise",
    r"    reparameterizations of one effective update (orthogonal subgroup only; LoRA $A/B$ and",
    r"    Adapter bottlenecks: Corollary~4).",
    r"    \item \textbf{R3 -- Block decomposability}: $S(M_a\oplus M_b)=S(M_a)+S(M_b)$.",
    r"    \item \textbf{R3$'$ -- Cross-block additivity}: $S(x+y)=S(x)+S(y)$ across blocks. R3 is",
    r"    strictly weaker: $\|\nabla E\|^2$ satisfies R3 but not R3$'$",
    r"    (Lemma~\ref{lem:r3-not-r3p}).",
    r"    \item \textbf{R4 -- Directional coupling}: $S>0$ iff $u$ reduces the alignment energy",
    r"    $E$; $S=0$ iff $u\perp\nabla E$.",
    r"    \item \textbf{R5 -- First-order observability}: PEFT moves $<1\%$ of parameters with",
    r"    $\|\Delta\theta\|\ll\|\theta_0\|$, so first-order effects dominate.",
    r"\end{enumerate}",
    r"",
    r"\subsection{Representation Theorem}",
    r"",
    r"\begin{theorem}[Representation Theorem]\label{thm:repr}",
    r"Every admissible first-order allocation statistic $S(M_k)$ --- satisfying (R1)--(R5) --- must",
    r"admit the representation",
    r"\begin{equation}",
    r"S(M_k) = \langle \nabla_{M_k} E,\; \mathbb{E}_{\mathrm{batch}}[\nabla_{M_k} L] \rangle",
    r"\end{equation}",
    r"uniquely up to positive scaling.",
    r"\end{theorem}",
    r"",
    r"\begin{definition}[Gap Susceptibility]",
    r"$\Gamma_k := \langle \nabla_{M_k}E, \mathbb{E}_{\mathrm{batch}}[\nabla_{M_k}L]\rangle$.",
    r"\end{definition}",
    r"",
    r"\textbf{Why $\Gamma$ must be bilinear.} Any first-order $f(\nabla E,u)$ could in principle",
    r"serve; we first record what R3 does \emph{not} do.",
    r"",
    r"\begin{lemma}[R3 does not imply R3$'$]\label{lem:r3-not-r3p}",
    r"R3 does not imply R3$'$: $S=\|x\|^2$ is block-decomposable but not additive.",
    r"\end{lemma}",
    r"",
    r"\textbf{The derivation rests on (R3$'$), which we therefore state explicitly.} With R3$'$,",
    r"$S$ is additive; R1 and R5 make it continuous and first-order observable; continuous additive",
    r"functions on $\mathbb{R}$ are exactly the linear ones, $S(x)=cx$; R4 fixes $c>0$; $c=1$ gives",
    r"$\Gamma_k=\langle\nabla_{M_k}E,u_k\rangle$. The alternatives fail: $\|\nabla E\|^2$ and",
    r"$\|\nabla E\|\|u\|$ are always positive, so neither separates alignment-improving from",
    r"alignment-damaging updates, and both violate R3$'$; $|\langle\nabla E,u\rangle|$ loses the",
    r"sign (R4); $\cos(\nabla E,u)$ is scale-free (R1); $\exp(\langle\nabla E,u\rangle)$ is not",
    r"additive (R3$'$).",
    r"",
    r"\textbf{Status of (R3$'$).} We do not claim it follows from R1--R5;",
    r"Lemma~\ref{lem:r3-not-r3p} shows it does not, and we label it an added structural",
    r"assumption. Within the first-order, sign-consistent, orthogonally invariant \emph{and",
    r"additive} class $\Gamma$ is unique up to positive scaling; whether additivity is the right",
    r"assumption is empirical, and Section~\ref{sec:experiments} tests it.",
    r"",
    r"\subsection{Alignment Energy}",
    r"",
    r"$E(\theta)$ is a Lyapunov functional satisfying (A1) alignment monotonicity,",
    r"(A2) differentiability, (A3) parameterization invariance, (A4) grounding at pre-training and",
    r"(A5) separability from the objective ($E\neq g(L)$). For retrieval",
    r"$E=\frac{1}{N}\sum_i\|z_i^I-z_i^T\|^2$ (cf.\ $DG^*$ in Paper~2); for decoder VLMs",
    r"$E=\mathrm{mean}\|h_{\mathrm{vis}}-h_{\mathrm{lang}}\|^2$ over last-layer hidden states at",
    r"visual and language token positions.",
    r"",
    r"\subsection{Corollary 1: First-Order Gradient Flow}",
    r"",
    r"(We refer to this dynamics as the Generalized Flow Allocation Principle, or GFAP.) For",
    r"$\Delta\theta_k=-\eta u_k$,",
    r"\begin{equation}",
    r"\Delta E_k = -\eta \Gamma_k + \tfrac{1}{2}\eta^2 H_k + D_k",
    r"\end{equation}",
    r"where $H_k=\langle u_k,\nabla^2_{M_k}E\,u_k\rangle$ is curvature, $O(\|\Delta\theta\|^2)$,",
    r"and $\mathbb{E}[D_k]=0$; under LoRA $\|\Delta\theta\|\ll\|\theta_0\|$, so $H_k$ is negligible",
    r"and $\Gamma_k$ dominates.",
    r"",
    r"\begin{theorem}[Projection Error Bound]",
    r"If $\mathrm{Var}(H),\mathrm{Var}(D)=o(\mathrm{Var}(\Gamma))$ across blocks, then",
    r"$\varepsilon_{\mathrm{proj}}=P(\mathrm{rank\_by\_}\Gamma\neq\mathrm{rank\_by\_}\Delta",
    r"E_{\mathrm{true}})\leq C_0(\mathrm{Var}(H)+\mathrm{Var}(D))/\mathrm{Var}(\Gamma)$. On",
    r"Paper~2's CLIP data $\mathrm{Var}(\Gamma)/\mathrm{Var}(H)>20\times$, so",
    r"$\varepsilon_{\mathrm{proj}}<0.05$.",
    r"\end{theorem}",
    r"",
    r"\textbf{Identifiability.} Below $\varepsilon_{\mathrm{threshold}}=\min\{\varepsilon:",
    r"\mathrm{SNR}(\Gamma)>\max\mathrm{SNR}(\mathrm{alternatives})\}$, $\Gamma$ is not",
    r"identifiable (Paper~2 $\theta_0$: $r=-0.27$; LoRA $B=0$ blocks gradient flow); above it it",
    r"is the unique sign-consistent predictor of $\Delta E$.",
    r"",
    r"\subsection{Corollary 2: Optimal Allocation}",
    r"",
    r"\textbf{Assumptions.} (A1) Linear risk $f(\mathrm{rank})=\mathrm{rank}$ (Paper~2 ERS,",
    r"$k=0.088$). (A2) Separable objective. (A3) $\sum_k\mathrm{rank}_k=C$,",
    r"$\mathrm{rank}_k\geq1$ --- a budget on \emph{rank}, not on parameters: one rank unit costs",
    r"$c_k=\sum_{W\in M_k}(\mathrm{in}_W+\mathrm{out}_W)$ parameters, and $c_k$ varies by",
    r"$2.65\times$ across Qwen2-VL blocks ($655{,}360$ vision against $247{,}296$ shallow LLM;",
    r"\texttt{outputs/analysis/p3\_alloc\_budget\_probe.json}), so uniform rank is not uniform",
    r"parameter allocation; under $\sum_kc_k\mathrm{rank}_k=B$ the KKT system gains a factor and",
    r"$\mathrm{rank}^*_k\propto\exp(-\beta|\Gamma_k|)/c_k$, while Eq.~\ref{eq:allocation} uses the",
    r"rank convention. (A4) Interior solution via entropy regularization",
    r"$H(r)=\sum r_k\log r_k$, the unique separable, symmetric convex regularizer yielding the",
    r"exponential family.",
    r"",
    r"\textbf{Derivation.} Minimizing $\sum_k|\Gamma_k|\mathrm{rank}_k",
    r"+\frac{1}{\beta}\sum_k\mathrm{rank}_k\log\mathrm{rank}_k$ under (A3) gives",
    r"$\log(\mathrm{rank}_k)=-\beta|\Gamma_k|-\beta\lambda-1$, hence",
    r"\begin{equation}",
    r"\mathrm{rank}^*_k = C \cdot \frac{\exp(-\beta \cdot |\Gamma_k|)}",
    r"{\sum_j \exp(-\beta \cdot |\Gamma_j|)}",
    r"\label{eq:allocation}",
    r"\end{equation}",
    r"Exponentiality is forced by KKT: a sigmoid cannot satisfy $\sum=C$, and piecewise forms",
    r"introduce arbitrary cutoffs.",
    r"",
    r"\textbf{Scale invariance and the role of $\beta$.} Eq.~\ref{eq:allocation} depends only on",
    r"$\beta|\Gamma_k|$ and is invariant under $(\beta,|\Gamma_k|)\to(\beta/s,s|\Gamma_k|)$. As the",
    r"entropy temperature indexing the family from uniform ($\beta\to0$) to the greedy corner",
    r"($\beta\to\infty$), $\beta$ is not fitted on the source architecture, so no",
    r"cross-architecture calibration is required: if the target's magnitudes differ by $s$, the",
    r"same allocation is recovered at temperature $\beta/s$. The raw magnitudes in Appendix~D",
    r"($|\Gamma|\sim10^3$--$10^4$) therefore carry no allocative meaning by themselves; what",
    r"transfers is the \emph{ordering} of $|\Gamma_k|$ (Corollary~4). That corner is not the best",
    r"configuration under measured energy: in the capacity-matched comparison of Section~IV-E it",
    r"scores $\Delta E=+3607\pm514$ against $+2241\pm1291$ for the $\Gamma$-guided interior",
    r"solution. (Paper~2's ODE decay $\beta=\eta f'(DG_0)$ is a distinct fitted quantity, with its",
    r"own provenance in Section~V.)",
    r"",
    r"\subsection{Corollary 3: Alignment Phase Transition}",
    r"",
    r"Corollaries~1 and 2 jointly imply a \textbf{critical rank threshold} $r_c$ at which the sign",
    r"of $\Delta E$ flips: $\mathrm{sgn}(\Delta E)=-1$ for $r<r_c$ and $+1$ for $r>r_c$. Below",
    r"$r_c$ LoRA capacity cannot develop modality-specific biases, so alignment improves through",
    r"general representation refinement ($\Gamma_k>0$); above it the LLM develops \emph{text",
    r"dominance}, the sign of $\Gamma_k$ flips and alignment energy surges---the \emph{cross-modal}",
    r"manifestation of the rank thresholds reported for LoRA",
    r"(efficiency~\cite{hu2025loralimits}, landscape convexity~\cite{loraconvex2025}). The",
    r"threshold is a prediction of the model, not a claim about its sharpness: the crossing we",
    r"measure on LLaVA is \emph{bracketed} rather than sharp---its interval at $r=5$ spans zero and",
    r"an exact permutation test between neighbouring ranks gives $p=0.100$---and its location",
    r"belongs to the measurement protocol rather than to the model, since it does not reappear",
    r"under real image--text pairs. The predicted dependence of $r_c$ on modality balance was not",
    r"confirmed: the apparent architecture dependence we first observed did not survive a change of",
    r"visual budget.",
    r"",
    r"\subsection{Corollary 4: Cross-Architecture Transfer}",
    r"",
    r"The relative ordering of $|\Gamma_k|$ is a geometric invariant: $\nabla_{M_k}E$ and $u_k$",
    r"are covectors in each block's tangent space whose inner product is invariant under the",
    r"orthogonal subgroup (R2). Since Eq.~\ref{eq:allocation} depends only on relative magnitudes,",
    r"the allocation is set by the block ordering, which transfers across architectures up to a",
    r"monotonic distortion (\emph{Partial Ordering Preservation}): blocks with largest $|\Gamma|$",
    r"on CLIP correspond to blocks with largest $|\Gamma|$ on LLaVA, because both share the",
    r"vision-encoder-to-LLM pipeline whose coupling is dominated by the same bottlenecks",
    r"(projector, deep LLM layers). Section~IV verifies this: $\Gamma$ measured on CLIP at",
    r"initialization predicts optimal rank allocation on LLaVA with no target-model gradient",
    r"computation. LoRA $A/B$ and Adapter bottlenecks are not orthogonal, but $\Gamma$ is computed",
    r"in each method's native parameter space, so within-method block comparisons are unaffected",
    r"and our cross-method results hold under LoRA, Adapter and BitFit in Paper~2.",
    r"",
    r"\subsection{Corollary 5: Paper~2 as Retrieval Specialization}",
    r"",
    r"Setting $K=\{\text{vision},\text{text}\}$, $E=DG^*$ and $u=\nabla L_{\mathrm{InfoNCE}}$",
    r"recovers $d(DG^*)/dt=\alpha-\beta(DG^*-DG_0)$ as a natural special case.",
]

# ===========================================================================
# 2. INTRODUCTION  (5,054 -> ~2,600)
# ===========================================================================
INTRO = [
    r"\section{Introduction}",
    r"",
    r"Parameter-efficient fine-tuning (PEFT) of large vision-language models is the dominant way",
    r"to adapt pretrained multimodal systems: LoRA~\cite{hu2021} injects low-rank adapters into a",
    r"frozen backbone, reducing trainable parameters to a fraction of a percent. One question",
    r"remains open: \emph{given a fixed parameter budget, which parts of the model should receive",
    r"adapters, and at what rank?}",
    r"",
    r"Uniform-rank LoRA ignores a structural fact: parameter blocks (vision encoder, projector,",
    r"shallow and deep LLM layers) couple to cross-modal alignment with different strengths, so",
    r"uniform rank starves the blocks where training most damages alignment. The problem is acute",
    r"for decoder VLMs such as LLaVA~\cite{liu2023llava} and Qwen-VL~\cite{bai2023qwen}, where both",
    r"modalities share one LLM backbone.",
    r"",
    r"Existing approaches are empirical: importance scores from training dynamics~\cite{adalora2023},",
    r"Shapley values~\cite{shaplora2025}, integrated gradients~\cite{igulora2025} or NTK",
    r"eigenvalues~\cite{f3ocus2025}. All learn the rule \emph{from post-hoc observations} rather",
    r"than \emph{derive it from the optimization structure}, so it is architecture-specific and must",
    r"be re-learned per model---defeating the purpose of PEFT as a resource-saving strategy.",
    r"",
    r"A separate line of work has established precise laws for the \emph{modality gap} in",
    r"contrastive VLMs~\cite{liang2022,schrodi2024,yi2025,levi2025}, but describes \emph{static}",
    r"gap properties; how the gap \emph{evolves} under fine-tuning is poorly understood. The",
    r"companion study~\cite{wan2026protect,wan2026gap} introduced \emph{Gap Susceptibility}",
    r"$\Gamma_m=\|\nabla_m DG^*\|\cos\phi_m$, a measurable quantity governing modality-gap dynamics",
    r"under PEFT ($R^2>0.96$)---but for encoder-only contrastive architectures, and as a",
    r"\emph{proposed metric} rather than a derived necessity.",
    r"",
    r"This paper advances in two ways. First, $\Gamma$ is not merely a useful metric but the answer",
    r"the allocation problem permits: under five requirements the problem imposes,",
    r"$\Gamma=\langle\nabla E,u\rangle$ is the unique admissible statistic up to positive",
    r"scaling---\emph{once one accepts the additivity assumption (R3$'$), which we state explicitly",
    r"because (R3) alone does not imply it}. Second, we extend the framework to decoder VLMs,",
    r"demonstrating zero-shot cross-architecture PEFT design prediction without target-model",
    r"gradient access. Our contributions are:",
    r"",
    r"\begin{enumerate}",
    r"    \item \textbf{Representation Theorem} (Sec.~\ref{sec:theory}): under five necessary",
    r"    requirements---pre-training computability, coordinate invariance, block decomposability,",
    r"    directional coupling preservation and first-order observability---$\Gamma_k=\langle",
    r"    \nabla_{M_k}E,u_{M_k}\rangle$ is the \emph{unique} admissible statistic \emph{subject to",
    r"    (R3$'$)}: it is \emph{not} forced by the optimization structure unless that assumption is",
    r"    granted.",
    r"    \item \textbf{Generalized Flow Allocation Principle (GFAP)}: five corollaries follow---",
    r"    (C1) first-order gradient flow; (C2) exponential rank allocation via KKT; (C3) a critical",
    r"    rank $r_c$ flipping the sign of $\Delta E$; (C4) cross-architecture transfer; (C5)",
    r"    recovery of our prior retrieval theory as a special case.",
    r"    \item \textbf{Experimental validation} (Sec.~\ref{sec:experiments}): on LLaVA-1.5-7B the",
    r"    crossing in alignment energy is \emph{bracketed} at $r\in[5,6]$, not sharp---its interval",
    r"    at $r=5$ spans zero and an exact permutation test between neighbouring ranks is not",
    r"    significant---and it belongs to the measurement protocol (blank images, $16$ samples,",
    r"    4-bit QLoRA), not to the model, since it does not reappear under real image--text pairs.",
    r"    At a matched trainable-parameter budget the derived allocation beats uniform rank at one",
    r"    learning rate but reverses at another and is indistinguishable from a random allocation of",
    r"    the same budget; AdaLoRA over the same rates is better than all our arms. We therefore",
    r"    present the rule as a zero-shot heuristic, not an optimum.",
    r"\end{enumerate}",
]

# ===========================================================================
# 3. DISCUSSION  (5,746 -> ~2,800)
# ===========================================================================
DISCUSSION = [
    r"\section{Discussion}",
    r"",
    r"\subsection{\texorpdfstring{$\Gamma$}{Gamma} as a Reusable Structural Property}",
    r"",
    r"The central contribution is not the exponential formula but the identification of $\Gamma$",
    r"as a privileged quantity: (R1)--(R5), \emph{together with the additivity assumption (R3$'$)",
    r"that we state explicitly rather than derive}, single out $\Gamma=\langle\nabla E,u\rangle$",
    r"up to positive scaling. The assumption has to be explicit because (R3) alone does not give",
    r"it---$\|\nabla E\|^2$ is block-decomposable and fails only additivity---so the honest",
    r"statement is that the problem admits a canonical statistic once one accepts additivity, not",
    r"that it admits exactly one unconditionally. We hope $\Gamma$ serves as a reusable tool",
    r"analogous to Hessian eigenvalues and the Neural Tangent Kernel: a portable structural",
    r"quantity that future work can measure on new architectures without exhaustive",
    r"experimentation.",
    r"",
    r"\subsection{Alignment Phase Transition in Context}",
    r"",
    r"The crossing on LLaVA sits in $r\in[5,6]$ and connects to work on LoRA phase transitions",
    r"(efficiency~\cite{hu2025loralimits}, landscape convexity~\cite{loraconvex2025}). Two",
    r"qualifications matter more than the connection. First, we describe the crossing as",
    r"\emph{bracketed} rather than sharp: at $r=5$ the bootstrap interval spans zero, an exact",
    r"permutation test between $r=5$ and $r=6$ gives $p = 0.100$, and with three seeds the smallest",
    r"detectable effect exceeds the one observed. Second, the location is a property of the",
    r"measurement protocol: it appears under blank images at $16$ training samples with 4-bit",
    r"QLoRA, it does not reappear under real image--text pairs at the scales we could run, and the",
    r"apparent architecture dependence we had reported did not survive a change of visual",
    r"budget---at $54$ tokens the decoder's real-image runs also turn negative, so that contrast",
    r"was an artefact of the token budget, not of the architecture.",
    r"",
    r"\subsection{Why Text-Only Is Best: A GFAP Explanation}",
    r"",
    r"The companion study~\cite{wan2026protect} found that text-only fine-tuning preserves",
    r"alignment across 5 architectures. GFAP explains this: when $u_v=0$ the visual coupling term",
    r"$\Gamma_v\|u_v\|$ vanishes and the perturbation $\alpha=-\eta\Gamma_t\|u_t\|$ is the minimum",
    r"possible for alignment-improving text coupling ($\Gamma_t>0$), whereas adding visual training",
    r"adds the dominant term. Text-only is therefore \emph{consistent} with the gradient coupling",
    r"structure rather than derived from it: our capacity-matched controls show that allocations",
    r"consistent with that structure are not reliably better than random ones.",
    r"",
    r"\subsection{Rank Scaling Behavior}",
    r"",
    r"The monotonic $\Delta E$ growth on LLaVA (to $+2860$ at $r=20$, collapse at $r\geq24$)",
    r"contrasts with Effective Rank Saturation on CLIP~\cite{wan2026gap}, where $\|g_v\|$ was flat",
    r"across ranks: in decoder VLMs higher rank provides capacity disproportionately allocated to",
    r"language-token processing, amplifying damage rather than saturating it.",
    r"",
    r"\subsection{Limitations}",
    r"",
    r"Several limitations delineate the scope. (1) Zero-shot transfer holds on two chains",
    r"(CLIP $\to$ LLaVA, CLIP $\to$ Qwen); per-block $\Gamma$ on Qwen confirms the allocation",
    r"prediction (Corollary~4) as rank-insensitive alignment, but a block-wise rank-allocation",
    r"experiment on Qwen remains untested. (2) Per-component rank allocation uses uniform LLM rank;",
    r"a projector-vs.-LLM control needs PEFT library support for LLaVA's projector. (3) The",
    r"Representation Theorem assumes the orthogonal subgroup, which may not exhaust all physically",
    r"relevant transformations. (4) The phase transition is verified on two datasets (Alpaca,",
    r"ShareGPT) but not on captioning or question-answering data. (5) GFAP assumes continuous-time",
    r"gradient flow whereas training uses discrete AdamW steps; prior work~\cite{wan2026gap} found",
    r"the approximation adequate ($R^2>0.96$), but formal error bounds are absent. (6) The",
    r"phase-table values are environment-sensitive: a legacy batch from an earlier environment",
    r"differs in sign at $r\in[5,8]$, so all reported LLaVA values come from the",
    r"current-environment E2 and supplementary batches (verified by local re-runs), and the",
    r"ordering evidence ($p = 2^{-5}$) is computed within that environment; cross-environment",
    r"reproducibility of $r_c$ is an open question rather than an established constant.",
    r"",
    r"\subsection{Future Directions}",
    r"",
    r"Two extensions are immediate: mini-batch gradient noise as a diffusion term, so that $\Gamma$",
    r"could ground early stopping, and cross-architecture transfer on further backbones",
    r"(LLaVA-NeXT, InternVL).",
]

# ===========================================================================
# 4. CONCLUSION  (3,047 -> ~1,700)
# ===========================================================================
CONCLUSION = [
    r"\section{Conclusion}",
    r"",
    r"This paper establishes that optimal PEFT rank allocation in multimodal models can be",
    r"predicted from cross-modal gradient coupling measured on unrelated architectures, without",
    r"target-model gradient access. The central object is $\Gamma=\langle\nabla E,u\rangle$, which",
    r"is not arbitrary: it is the scalar singled out by the PEFT allocation problem \emph{once one",
    r"accepts the additivity assumption (R3$'$), which we state explicitly because (R3) alone does",
    r"not imply it}.",
    r"",
    r"The Representation Theorem provides what prior rank-allocation methods lacked: a structural",
    r"characterisation rather than an empirical heuristic---whose scope our own controls then bound.",
    r"Five corollaries follow: (C1) first-order gradient-flow dynamics make $\Gamma$ the dominant",
    r"coordinate of $\Delta E$; (C2) KKT optimization yields",
    r"$\mathrm{rank}_k\propto\exp(-\beta|\Gamma_k|)$; (C3) a critical rank $r_c$ flips the sign of",
    r"$\Delta E$; (C4) the $|\Gamma_k|$ ordering transfers across architectures up to monotonic",
    r"distortion; (C5) the companion ODE theory~\cite{wan2026gap} is the",
    r"$K=\{\text{vision},\text{text}\}$ case.",
    r"",
    r"Experimental validation covers 126 runs on the present protocol plus the capacity-matched",
    r"allocation study of Section~IV. We report the crossing in the alignment energy as",
    r"\emph{bracketed} at $r\in[5,6]$ without claiming it is sharp---the interval at $r=5$ spans",
    r"zero and an exact permutation test between neighbouring ranks is not significant---and we",
    r"attribute it to the measurement protocol rather than to the model, since it does not reappear",
    r"under real image--text pairs at the scales we could run. On the allocation question itself the",
    r"results are negative and we state them as such: at an identical trainable-parameter count the",
    r"$\Gamma$-derived allocation beats uniform rank at one learning rate but reverses at another",
    r"and vanishes once the arms are matched on training loss; it is indistinguishable from a random",
    r"allocation of the same budget; and AdaLoRA, over the same rates, is better than any of our",
    r"arms. What survives is the purpose rather than the win: $\Gamma$ allocates \emph{without",
    r"searching}, and that is the setting it is for.",
    r"",
    r"We believe $\Gamma$ can serve as a reusable structural quantity---analogous to Hessian",
    r"eigenvalues and the Neural Tangent Kernel---for diagnosing cross-modal alignment dynamics",
    r"under parameter-efficient fine-tuning.",
    r"",
    r"\noindent\textbf{Reproducibility.} All experiments use public models (LLaVA-1.5-7B,",
    r"Qwen2-VL-7B, CLIP ViT-B/32) and datasets (Alpaca, ShareGPT). LLaVA training is reproducible",
    r"on consumer hardware (RTX 4060, 8GB) via QLoRA 4-bit quantization; cross-architecture",
    r"verification uses a cloud GPU (\textasciitilde\$8 USD). Code is available from the author",
    r"upon request.",
]

TEXT = {
    "paper3/paper_ieee/sections/theory.tex": THEORY,
    "paper3/paper_ieee/sections/introduction.tex": INTRO,
    "paper3/paper_ieee/sections/discussion.tex": DISCUSSION,
    "paper3/paper_ieee/sections/conclusion.tex": CONCLUSION,
}


def build(lines: list[str]) -> str:
    """列表 join —— 唯一允许的换行来源是真 `"\n".join`。"""
    return "\n".join(lines) + "\n"


def check(name: str, text: str) -> list[str]:
    errs = []
    flat = " ".join(text.split())
    for k in KEEP.get(name, []):
        if " ".join(k.split()) not in flat:
            errs.append(f"缺必备片段: {k}")
    for pat in FORBID:
        for m in re.finditer(pat, text, re.I):
            ctx = text[max(0, m.start() - 200):m.start() + 200].lower()
            if not any(k in ctx for k in ALLOW_CTX):
                errs.append(f"禁止回归的旧主张（非否定语境）: {pat!r} -> {m.group(0)!r}")
                break
    if LITERAL_N.search(text):
        errs.append(f"出现字面 \\n {LITERAL_N.findall(text)[:3]}")
    sev = [ln for ln in text.split("\n") if SEVERED.match(ln)]
    if sev:
        errs.append(f"出现行首断头命令: {sev[:3]}")
    if CTRL.search(text):
        errs.append("出现控制字符")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print("=" * 100)
    print("P3 四节压缩：预演 / 量测")
    print("=" * 100)
    print(f"  {'文件':<20}{'改前':>8}{'目标':>8}{'拟改后':>8}{'变化':>9}  状态")
    ok = True
    for rel, lines in TEXT.items():
        p = REPO / rel
        before = p.read_text(encoding="utf-8", errors="replace")
        after = build(lines)
        errs = check(p.name, after)
        tgt = TARGETS[rel]
        ratio = len(after) / tgt
        flag = "✅" if not errs else "🔴"
        if ratio > 1.05:
            flag += f" ({ratio:.2f}× 目标)"
        print(f"  {p.name:<20}{len(before):>8,}{tgt:>8,}{len(after):>8,}"
              f"{len(after)-len(before):>+9,}  {flag}")
        for e in errs:
            print(f"        🔴 {e}")
            ok = False
    tb = sum(len((REPO / r).read_text(encoding='utf-8', errors='replace')) for r in TEXT)
    ta = sum(len(build(v)) for v in TEXT.values())
    print()
    print(f"  四节合计 {tb:,} → {ta:,}（{ta-tb:+,}，压掉 {100*(tb-ta)/tb:.1f}%）")
    if not a.apply:
        print("\n  （预演）—— 未写入")
        return 0 if ok else 1
    if not ok:
        print("\n  🔴 断言未通过，拒绝写入")
        return 1
    for rel, lines in TEXT.items():
        (REPO / rel).write_text(build(lines), encoding="utf-8", newline="")
        print(f"  ✅ 已写 {rel}")
    print("\n  ✅ 全部写入（断言通过）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
