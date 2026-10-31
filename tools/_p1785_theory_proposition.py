# -*- coding: utf-8 -*-
r"""Upgrade 3: turn the additivity discussion into formal statements, add the counterexample appendix, rebuild.

The manuscript currently says informally how much R3' buys. This script:
  1. writes the formal note `docs/PaperA_theory_additivity.md` (propositions with proofs, referencing the numerical
     checks archived by `tools/_p1768_theory_checks.py`);
  2. replaces the informal paragraph in `20_theory.tex` with the same content as a compact proposition block
     (run-in bold headings, no new theorem environment, so the build cannot break on class differences);
  3. appends the counterexample computation as an appendix paragraph in `95_appendix_original.tex`;
  4. rebuilds the revision package and reports pages / errors, then the provenance gate.

Writes only to the revision package (`ML_PKG_DIR`), never to the frozen v1.0 package.
"""
import io
import os
import re
import subprocess

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NOTE = r"""# Additivity: what R3' buys, formally

Written for the revision. All numerical claims below are produced by `tools/_p1768_theory_checks.py`
(archive `outputs/analysis/paperA_theory_hardness_checks.json`, 4000 draws, seed 20261027).

## Setting

Energy `E: R^{d1} x R^{d2} -> R`, block gradients `g_k = dE/dx_k`, unit direction `u` with block components `u_k`, and
per-block susceptibility `Gamma_k = <g_k, u_k>`. The paper's requirements R1, R2, R4, R5 plus **R3' (additivity)**
single out `S = c * sum_k Gamma_k^2`; the question is how much R3' buys.

## Proposition 1 (the block-norm statistic is not a function of Gamma)

Let `N(x) = sum_k |g_k|^2`. If `N = c * sum_k Gamma_k^2` for all `x` and some constant `c > 0`, then `cos^2 phi_k` must be
the same for every block at every configuration. Proof: write `|g_k|^2 = Gamma_k^2 / cos^2 phi_k`
with `cos phi_k = <g_k, u_k> / |g_k|`; equality for all configurations forces `cos^2 phi_k` to be the same constant for
every `k` and every `x`. This fails for the two-block quadratic family `E = 1/2|x_1|^2 + 1/2|x_2|^2 + eps x_1^T x_2`
at generic configurations: the numerical check finds the two orderings disagree on **26%** of 4000 random draws, so no
monotone transform of `N` reproduces the ordering produced by `Gamma`. R3' therefore is not redundant: it is what makes
the ordering well defined.

## Proposition 2 (open-set additivity suffices, hence is the weakest useful form)

Let `S` and `s_k` be continuous on a nonempty open set `U`. If `S(x) = sum_k s_k(x_k)` for all `x` in `U`, then the same
identity holds for every `x`. Proof: the difference `S(x) - sum_k s_k(x_k)` is continuous and vanishes on `U`; a
continuous function that vanishes on a nonempty open set vanishes identically. Consequently R3' can be replaced by
additivity on any nonempty open set of configurations - strictly weaker than assuming it everywhere - with continuity.

## Proposition 3 (additivity on the closed subclass is not enough)

Additivity on the closed measure-zero subclass `D = {x : x_1^T x_2 = 0}` plus continuity does **not** restore uniqueness.
Counterexample: `S_lam = sum_k |g_k|^2 + lam (x_1^T x_2)^2` with `lam = 1.7` is continuous, and on `D` it equals the
separable statistic `sum_k |g_k|^2` exactly (the coupling term vanishes there), yet off `D` it differs from it (numerical
check: gap 0.00e+00 on `D`, 1.70 and 0.27 at the two off-`D` test points). Hence the natural weakening "assume additivity
only for block-orthogonal perturbations" is false as a route to uniqueness.

## Corollary

R3' cannot be weakened by restricting additivity to a measure-zero subclass, and it can be weakened to additivity on
nonempty open sets. Both statements are cheap to state and check, and together they convert "we assume additivity" into a
characterised boundary.
"""

SECTION_INSERT = r"""
\textbf{Proposition 1.} Let $N(x)=\sum_k\|g_k\|^2$. If $N=c\sum_k\Gamma_k^2$ for all $x$ and some $c>0$, then
$\cos^2\phi_k$ is the same constant for every block and every configuration. The identity fails for
$E=\tfrac12\|x_1\|^2+\tfrac12\|x_2\|^2+\epsilon x_1^\top x_2$ at generic configurations: the block-norm ordering and the
$\Gamma$ ordering disagree on $26\%$ of four thousand random draws, so no monotone transform of $N$ reproduces the
$\Gamma$ ordering. \textbf{Proposition 2.} If the statistic is additive on any nonempty \emph{open} set of configurations
and both sides are continuous, then it is additive everywhere, because a continuous function vanishing on an open set
vanishes identically. This is the weakest form of additivity that still yields the unique form
$S=c\sum_k\Gamma_k^2$, and it is strictly weaker than assuming additivity globally. \textbf{Proposition 3.} Additivity on
the closed measure-zero subclass $\{x:x_1^\top x_2=0\}$ plus continuity does \emph{not} suffice: the statistic
$\sum_k\|g_k\|^2+\lambda(x_1^\top x_2)^2$ with $\lambda=1.7$ coincides with the separable statistic on that subclass
(gap $0.00$) and differs from it off the subclass (by $1.70$ and $0.27$). The corollary is that R3$'$ cannot be weakened
by restricting it to a measure-zero subclass, only by restricting it to an open set; Appendix~\ref{app:additivity} gives
the computation.
"""

APPENDIX_INSERT = r"""
\section{Additivity counterexample}\label{app:additivity}

For $E=\tfrac12\|x_1\|^2+\tfrac12\|x_2\|^2+\epsilon x_1^\top x_2$ with $\epsilon=0.9$ and the direction
$u=(1,0.3)/\|(1,0.3)\|$, the block-norm ordering of $g_1,g_2$ and their $\Gamma$ ordering disagree on $26.0\%$ of four
thousand random draws (seed $20261027$), so the norm statistic is not a function of $\Gamma$. The natural weakening of
additivity to the closed subclass $\{x:x_1^\top x_2=0\}$ fails as well: $S_\lambda=\sum_k\|g_k\|^2+\lambda(x_1^\top
x_2)^2$ with $\lambda=1.7$ equals the separable statistic exactly on the subclass and differs from it by $1.70$ and
$0.27$ at the two off-subclass test points. Both checks are produced by \texttt{tools/\_p1768\_theory\_checks.py} and
archived in \texttt{outputs/analysis/paperA\_theory\_hardness\_checks.json}.
"""

# ---- 1. the formal note
io.open("docs/PaperA_theory_additivity.md", "w", encoding="utf-8", newline="").write(NOTE)
print("wrote docs/PaperA_theory_additivity.md")

# ---- 2. replace the informal paragraph in the theory section
P2 = "paper合/reframed/sections/20_theory.tex"
t2 = io.open(P2, encoding="utf-8").read()
start = t2.find("How much does additivity buy")
if start < 0:
    print("WARN: informal paragraph not found; inserting before the first subsection")
    start = t2.find("\\subsection")
    end = start
else:
    end = t2.find("\n\n", start)
    if end < 0:
        end = len(t2)
t2 = t2[:start] + SECTION_INSERT.strip() + "\n" + t2[end:]
io.open(P2, "w", encoding="utf-8", newline="").write(t2)
print("theory section: proposition block installed")

# ---- 3. appendix counterexample
PA = "paper合/reframed/sections/95_appendix_original.tex"
ta = io.open(PA, encoding="utf-8").read()
if "app:additivity" not in ta:
    cut = ta.rfind("\\section{Data and code provenance}")
    if cut < 0:
        cut = len(ta)
    ta = ta[:cut] + APPENDIX_INSERT + "\n" + ta[cut:]
    io.open(PA, "w", encoding="utf-8", newline="").write(ta)
    print("appendix: additivity counterexample added")

# ---- 4. rebuild the revision package
env = dict(os.environ)
env["ML_PKG_DIR"] = os.path.abspath("SUBMISSION/PaperA_MachineLearning_revision")
r = subprocess.run([r"D:\Anaconda\python.exe", "tools/_p1720_build_ml_package.py", "--apply"],
                   capture_output=True, text=True, env=env)
tail = [ln for ln in r.stdout.splitlines() if ("pages:" in ln or "RESULT" in ln or "round-trip" in ln or "FATAL" in ln)]
print("\n".join(tail) if tail else r.stdout[-1500:])
if r.returncode != 0:
    raise SystemExit("revision build failed")

# ---- 5. provenance gate (the appendix section needs an entry only if it carries a float; it does not)
g = subprocess.run([r"D:\Anaconda\python.exe", "tools/_p1428_provenance_gate.py", "--apply"],
                   capture_output=True, text=True)
print([ln for ln in g.stdout.splitlines() if "gate:" in ln][-1:])
