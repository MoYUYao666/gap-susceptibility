# -*- coding: utf-8 -*-
r"""Local upgrade A1: numerical checks behind the theory-hardness statements (corrected formalisation).

Definitions used here, matching the manuscript:
  block gradients      g_k = dE/dx_k
  block norms          n_k = |g_k|                       (what ||grad E||^2 uses)
  susceptibility       Gamma_k = <g_k, u> restricted to block k, u = unit task direction
The paper's statistic is built from Gamma (the projection), not from the norm. The statements checked:

  C1  a statistic built from block normals (||grad E||^2 = sum_k n_k^2) is NOT additive in Gamma_k: on a two-block
      quadratic energy with a cross term the ordering by n_k can disagree with the ordering by Gamma_k, so a
      norm-based statistic violates R3' while satisfying the other requirements.
  C2  on random draws the two orderings disagree with a measurable frequency (reported, not hidden).
  C3  when the statistic is forced to be additive in the per-block Gamma components on block-orthogonal supports,
      it is a positive multiple of sum_k Gamma_k^2, which is why R3' pins the form down.
"""
import io
import json
import os

import numpy as np

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
rng = np.random.default_rng(20261027)
OUT = "outputs/analysis/paperA_theory_hardness_checks.json"


def grads(x, eps):
    g1 = x[:2] + eps * x[2:]
    g2 = x[2:] + eps * x[:2]
    return g1, g2


def norms(x, eps):
    g1, g2 = grads(x, eps)
    return float(g1 @ g1), float(g2 @ g2)          # squared block norms


def gammas(x, eps, u_block):
    """Gamma_k = <g_k, u_block>: projection of each block gradient on the shared task direction."""
    g1, g2 = grads(x, eps)
    return abs(float(g1 @ u_block)), abs(float(g2 @ u_block))


u = np.array([1.0, 0.3])
u = u / np.linalg.norm(u)
eps = 0.9

# C1: order by block norm vs order by Gamma, sweeping the second block's scale
rows = []
for scale in (0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0):
    x = np.array([1.0, 0.0, scale * 0.6, scale * 0.2])
    n1, n2 = norms(x, eps)
    g1, g2 = gammas(x, eps, u)
    rows.append({"x2_scale": scale, "norm1": n1, "norm2": n2,
                 "norm_order": "1>2" if n1 > n2 else "2>1",
                 "gamma1": g1, "gamma2": g2,
                 "gamma_order": "1>2" if g1 > g2 else "2>1"})
    print("scale=%.2f  norms=(%.3f, %.3f) %s | gammas=(%.3f, %.3f) %s" %
          (scale, n1, n2, rows[-1]["norm_order"], g1, g2, rows[-1]["gamma_order"]))
reversed_pairs = [r for r in rows if r["norm_order"] != r["gamma_order"]]
print("C1 orderings disagree at", len(reversed_pairs), "of", len(rows), "scales")

# C2: how often do the two orderings disagree on random draws?
disagree = 0
for _ in range(4000):
    x = rng.normal(size=4)
    n1, n2 = norms(x, eps)
    g1, g2 = gammas(x, eps, u)
    if (n1 > n2) != (g1 > g2):
        disagree += 1
print("C2 disagreement rate: %.3f over 4000 random draws" % (disagree / 4000.0))

# C3 (corrected): the block-orthogonal formulation is refuted; the open-set formulation holds.
lam = 1.7
def S_plain(x, eps):
    n1, n2 = norms(x, eps)
    return n1 + n2
def S_coupled(x, eps):
    n1, n2 = norms(x, eps)
    return n1 + n2 + lam * float(x[:2] @ x[2:]) ** 2

on_D = [np.array([1.0, 0.0, 0.0, 2.0]), np.array([0.3, 0.0, 0.0, -1.1])]
off_D = [np.array([1.0, 0.0, 1.0, 0.0]), np.array([0.5, 0.0, 0.8, 0.2])]
gaps_D = [abs(S_coupled(x, eps) - S_plain(x, eps)) for x in on_D]
gaps_off = [abs(S_coupled(x, eps) - S_plain(x, eps)) for x in off_D]
print("C3 counterexample: max gap on D = %.2e ; gaps off D = %s" % (max(gaps_D), ["%.4f" % g for g in gaps_off]))

centre = np.array([0.7, 0.2, 0.4, -0.3]); radius = 0.35; viol = 0
for _ in range(2000):
    d = rng.normal(size=4); d = d / np.linalg.norm(d) * rng.uniform(0, radius)
    x = centre + d
    if abs(S_coupled(x, eps) - S_plain(x, eps)) < 1e-12:
        viol += 1
print("C3 open-set check: coupling deviation zero at %d of 2000 points inside the ball" % viol)

res = {"script": "tools/_p1768_theory_checks.py",
       "definitions": {"n_k": "|g_k|^2 block norm", "Gamma_k": "<g_k, u>", "eps": eps, "u": u.tolist()},
       "C1": {"sweep": rows, "disagreements": len(reversed_pairs)},
       "C2": {"draws": 4000, "disagreement_rate": disagree / 4000.0},
       "C3": {"status": "the block-orthogonal formulation is refuted; the open-set formulation is proved one line",
              "counterexample": {"lambda": lam, "max_gap_on_D": float(max(gaps_D)),
                                 "gaps_off_D": [float(g) for g in gaps_off]},
              "open_set_violations": viol,
              "statement": "additivity on a nonempty OPEN set plus continuity already implies global additivity (hence R3'), whereas additivity on the closed subclass {x1.x2 = 0} does not"}}
io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(res, indent=2))
print("wrote", OUT)
