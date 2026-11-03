# -*- coding: utf-8 -*-
r"""修 P3 理论缺口（审稿意见 R1.5 / R3.3）：block additivity ≠ bilinearity（2026-10-12）。

## 审稿人的原话

> **R1.5**: *"the proof contains an important gap. In the appendix, the manuscript states
> that block decomposability implies that the 'most general first-order functional' must be
> bilinear, S(x,y)=x^T A y, but **block additivity alone does not imply bilinearity**;
> quantities such as $\|x\|^2$ are also block-additive."*

> **R3.3**: *"Could the authors provide a more rigorous treatment of the claim that the
> Representation Theorem establishes uniqueness, particularly under practical non-orthogonal
> PEFT parameterizations?"*

## 我核到的确切病处

1. `appendix.tex` *"Full Axiom Derivation"* 第 1 步：
   *"By (AX3), the most general first-order functional of (∇E, u) **is** a bilinear form
   S(x,y)=xᵀAy"* —— **这是断言，不是推导**。
2. `theory.tex` 的 *"Why must Γ be bilinear?"* 段写
   *"(R3) ⟹ f(x+y) = f(x) + f(y) (additivity over blocks)"* ——
   **把 R3（块级分解可加）当成了自变量求和可加**。
3. 而 **R3 的定义**（`theory.tex`）是 $S(M_a \oplus M_b) = S(M_a) + S(M_b)$，
   **对 `‖∇E‖²` 同样成立** → 审稿人正确。
4. 证明后半段有一句 *"Nonlinear f (e.g., |x|, x², exp(x)) either lose sign or break additivity"*
   —— `x²` 确实破坏 R4（符号），**但 `‖∇E‖²` 破坏的是 R4 还是 R3 并未论证清楚**，
   且 `exp(x)` 保号保序、只在"自变量求和"下破坏可加性。

## 修法（如实承认 + 显式补上 + 给反例）

- **不**声称原来的证明完整；**明确写出** R3 不足以推出双线性。
- **补一条显式的新公理 R3′**（cross-block additivity，作为**自变量的函数**），
  并说明它比 R3 强在何处。
- **给 Lemma + 反例**证明 R3 ⇏ R3′。
- 定理重述为"**在 R1–R5 加 R3′ 下唯一**"，并**如实标注** R3′ 是**新增的结构假设**
  （即：不是从 R1–R5 推出来的）——这同时回应 R3.1（"R1–R5 是必要条件还是强加假设"）。

    python tools\_p416_fix_p3_theory_gap.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TH = REPO / "paper3" / "paper_ieee" / "sections" / "theory.tex"
AP = REPO / "paper3" / "paper_ieee" / "sections" / "appendix.tex"

# ---------- ① theory.tex：R3 之后插入 R3′ ----------
R3_ANCHOR = (
    r"    \item  \textbf{R3 -- Block decomposability}: Allocation is per-block. The"
    "\n"
    r"    total risk must equal the sum of per-block risks:"
    "\n"
    r"    $S(M_a \oplus M_b) = S(M_a) + S(M_b)$."
    "\n")

R3P_INSERT = (
    "\n"
    r"    \item  \textbf{R3$'$ -- Cross-block additivity}: R3 fixes how the \emph{total}"
    "\n"
    r"    risk decomposes over separate blocks; it does not by itself constrain the"
    "\n"
    r"    functional form of $S$ in its arguments. We therefore state separately the"
    "\n"
    r"    property the derivation actually uses: $S$ is additive as a function of the"
    "\n"
    r"    per-block contributions, i.e.\ $S(x + y) = S(x) + S(y)$ for the arguments"
    "\n"
    r"    contributed by any two blocks. R3 alone is strictly weaker than R3$'$:"
    "\n"
    r"    $\|\nabla E\|^2$ satisfies R3 (it separates over blocks) but not R3$'$"
    "\n"
    r"    (Lemma~\ref{lem:r3-not-r3p})."
    "\n")

# ---------- ② theory.tex：替换 "Why must Γ be bilinear?" 整段 ----------
WHY_OLD_START = r"\textbf{Why must $\Gamma$ be bilinear?}"
WHY_NEW = (
    r"\textbf{Why must $\Gamma$ be bilinear?} A criticism of (R5) is that "
    r"any first-order function $f(\nabla E, u)$ could serve---not just the bilinear "
    r"$\langle\nabla E, u\rangle$ (e.g., $\|\nabla E\|^2$, "
    r"$\exp(\langle\nabla E, u\rangle)$, $\cos(\nabla E, u)$, "
    r"$|\langle\nabla E, u\rangle|$). We first record what (R3) does \emph{not} do."
    "\n\n"
    r"\begin{lemma}[R3 does not imply R3$'$]\label{lem:r3-not-r3p}"
    "\n"
    r"(R3) does not imply (R3$'$)."
    "\n"
    r"\end{lemma}"
    "\n"
    r"\begin{proof}"
    "\n"
    r"Take $S(x) = \|x\|^2$. Partition the parameter space into blocks and let $x_k$ be "
    r"the restriction of $x$ to block $M_k$. Then $S(M_a \oplus M_b) = \|x_a\|^2 + "
    r"\|x_b\|^2 = S(M_a) + S(M_b)$, so $S$ satisfies (R3). But $S(x + y) = "
    r"\|x + y\|^2 \neq \|x\|^2 + \|y\|^2 = S(x) + S(y)$ whenever $\langle x, y\rangle "
    r"\neq 0$, so $S$ fails (R3$'$). The same construction works for any nonlinear "
    r"function of a block-separable quantity, and it is exactly the alternative the "
    r"reviewers of this work identified: \emph{block decomposability constrains how a "
    r"quantity is summed over blocks, not how it depends on its arguments}."
    "\n"
    r"\end{proof}"
    "\n\n"
    r"\textbf{The derivation therefore rests on (R3$'$), and we state it explicitly.} "
    r"With (R3$'$) the argument closes: (R3$'$) makes $S$ additive in its arguments; "
    r"(R1) and (R5) make it continuous and first-order observable; the continuous "
    r"additive functions on $\mathbb{R}$ are exactly the linear ones, $S(x) = c\\,x$; "
    r"and (R4) fixes $c > 0$ because the statistic must be positive precisely when the "
    r"update reduces $E$. Setting $c = 1$ gives the canonical representative "
    r"$\Gamma_k = \langle\nabla_{M_k}E, u_k\rangle$. "
    r"The nonlinear alternatives are excluded as follows: $\|\nabla E\|^2$ and "
    r"$\|\nabla E\|\cdot\|u\|$ are always positive and so cannot distinguish "
    r"alignment-improving from alignment-damaging updates, and both fail (R3$'$); "
    r"$|\langle\nabla E, u\rangle|$ loses the sign and fails (R4); "
    r"$\cos(\nabla E, u)$ preserves the sign but is scale-free, so it assigns the same "
    r"risk to perturbations of very different magnitude and fails (R1); "
    r"$\exp(\langle\nabla E, u\rangle)$ preserves sign and ordering but is not additive, "
    r"so it fails (R3$'$). "
    "\n\n"
    r"\textbf{Status of (R3$'$).} We do not claim that (R3$'$) follows from (R1)--(R5); "
    r"Lemma~\ref{lem:r3-not-r3p} shows that it does not. It is an additional "
    r"structural assumption, and we label it as such. This sharpens --- rather than "
    r"removes --- what the Representation Theorem establishes: within the class of "
    r"statistics that are first-order observable, sign-consistent with alignment, "
    r"invariant under block-wise orthogonal reparameterisation \emph{and additive in "
    r"their arguments}, $\Gamma$ is the unique representative up to positive scaling. "
    r"Whether additivity is the right structural assumption is an empirical question, "
    r"and Section~\ref{sec:experiments} is the test of it."
    "\n\n")

# ---------- ③ appendix.tex：替换第 1 步 ----------
APX_OLD = (
    r"    \item By (AX3), the most general first-order functional of $(\nabla E, u)$"
    "\n"
    r"    is a bilinear form $S(x, y) = x^T A y$."
    "\n")
APX_NEW = (
    r"    \item By (AX3) alone the most general first-order functional of $(\nabla E, u)$ "
    r"is \emph{not} determined: block decomposability constrains how a quantity is summed "
    r"over blocks, not how it depends on its arguments, and $\|\nabla E\|^2$ is "
    r"block-additive while being neither bilinear nor sign-consistent "
    r"(Lemma~\ref{lem:r3-not-r3p}). The step requires the additional structural "
    r"assumption (AX3$'$), additivity in the per-block arguments, which we now state "
    r"explicitly rather than assume silently. Under (AX3$'$) the functional is additive "
    r"in its arguments, and continuity fixes $S(x) = c\,x$; the bilinear form "
    r"$S(x, y) = x^T A y$ then follows from (AX2), which forces $A = c\,I$ "
    r"(Schur's lemma)."
    "\n")

PAIRS = [
    (TH, R3_ANCHOR, R3_ANCHOR + R3P_INSERT, "插入 R3′ 公理"),
    (AP, APX_OLD, APX_NEW, "替换 appendix 第 1 步（承认缺口）"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for p, old, new, label in PAIRS:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(old)
        print(f"  {'✅' if n == 1 else '⚠️ '} {p.name}: {label} 命中 {n}")
        if n == 1 and a.apply:
            bak = p.with_suffix(".tex.bak_p416")
            if not bak.exists():
                shutil.copy2(p, bak)
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
            total += 1

    # 替换 "Why must Γ be bilinear?" 整段（到 "\subsection{Alignment Energy}" 之前）
    if a.apply:
        t = io.open(TH, encoding="utf-8", errors="replace").read()
        i = t.find(WHY_OLD_START)
        j = t.find(r"\subsection{Alignment Energy}")
        if i > 0 and j > i:
            t2 = t[:i] + WHY_NEW + t[j:]
            io.open(TH, "w", encoding="utf-8", newline="").write(t2)
            print(f"  ✅ 替换 'Why must Γ be bilinear?' 段（{j - i} 字符 → {len(WHY_NEW)} 字符）")
            total += 1
        else:
            print(f"  🔴 找不到该段（i={i}, j={j}）")

    if not a.apply:
        print("  （预演）")
        return 0
    print(f"\n  → 共改 {total} 处")
    th = io.open(TH, encoding="utf-8", errors="replace").read()
    apx = io.open(AP, encoding="utf-8", errors="replace").read()
    checks = {
        "theory 含 R3′ 公理": "R3$'$ -- Cross-block additivity" in th,
        "theory 含 lemma:r3-not-r3p": "lem:r3-not-r3p" in th,
        "theory 含反例 ‖x‖²": "\\|x\\|^2" in th,
        "theory 标注 R3′ 是新增假设": "It is an additional" in th,
        "appendix 不再断言 AX3 直接给双线性": "is a bilinear form $S(x, y) = x^T A y$." not in apx,
        "appendix 引用 lemma": "lem:r3-not-r3p" in apx,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
