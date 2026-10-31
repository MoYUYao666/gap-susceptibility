# -*- coding: utf-8 -*-
r"""Define and test the two gap metrics before any VLM run depends on them.

The earlier draft computed the centroid gap and the distribution gap with the same expression, which
makes the two columns identical and meaningless. This fixes the definitions and proves them on
synthetic data where the answer is known:

  centroid gap      ||mean(A) - mean(B)|| on L2-normalised embeddings
  distribution gap  mean cross-set distance minus the average of the two within-set distances
                    (a kernel-free MMD, zero when the sets are drawn from the same distribution)

Checks performed:
  1. two halves of one Gaussian  -> DG near zero, CG near zero
  2. two Gaussians 5 sigma apart -> both clearly positive
  3. DG is invariant to a rotation of both sets together
  4. the two metrics are not the same number on a non-degenerate sample
  5. identical inputs give DG = 0 and CG = 0 exactly

    python tools/_p821_gap_defs.py --apply
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "gap_definitions.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    import torch.nn.functional as F

    def centroid_gap(A, B):
        A = F.normalize(A.float(), p=2, dim=-1)
        B = F.normalize(B.float(), p=2, dim=-1)
        return float((A.mean(0) - B.mean(0)).norm())

    def distribution_gap(A, B):
        A = F.normalize(A.float(), p=2, dim=-1)
        B = F.normalize(B.float(), p=2, dim=-1)
        cross = torch.cdist(A, B).mean()
        within = 0.5 * (torch.cdist(A, A).mean() + torch.cdist(B, B).mean())
        return float(cross - within)

    torch.manual_seed(0)
    d = 64
    results = {}
    ok = True

    print("=" * 100)
    print("1. two halves of one Gaussian: both gaps should be near zero")
    print("=" * 100)
    X = torch.randn(200, d)
    A, B = X[:100], X[100:]
    cg, dg = centroid_gap(A, B), distribution_gap(A, B)
    print(f"  CG {cg:.4f}   DG {dg:+.4f}")
    near = cg < 0.35 and abs(dg) < 0.10
    ok = ok and near
    print(f"  [{'ok  ' if near else 'FAIL'}] both small")
    results["same_distribution"] = {"cg": cg, "dg": dg, "pass": near}

    print()
    print("=" * 100)
    print("2. two Gaussians separated by 5 sigma: both gaps clearly positive")
    print("=" * 100)
    A = torch.randn(100, d) + 5.0
    B = torch.randn(100, d) - 5.0
    cg, dg = centroid_gap(A, B), distribution_gap(A, B)
    print(f"  CG {cg:.4f}   DG {dg:+.4f}")
    sep = cg > 0.5 and dg > 0.2
    ok = ok and sep
    print(f"  [{'ok  ' if sep else 'FAIL'}] both large")
    results["separated"] = {"cg": cg, "dg": dg, "pass": sep}

    print()
    print("=" * 100)
    print("3. rotation invariance: DG and CG must not depend on orientation")
    print("=" * 100)
    A = torch.randn(100, d) + 2.0
    B = torch.randn(100, d) - 2.0
    Q, _ = torch.linalg.qr(torch.randn(d, d))
    cg1, dg1 = centroid_gap(A, B), distribution_gap(A, B)
    cg2, dg2 = centroid_gap(A @ Q, B @ Q), distribution_gap(A @ Q, B @ Q)
    print(f"  CG {cg1:.5f} -> {cg2:.5f}   DG {dg1:+.5f} -> {dg2:+.5f}")
    inv = abs(cg1 - cg2) < 1e-4 and abs(dg1 - dg2) < 1e-4
    ok = ok and inv
    print(f"  [{'ok  ' if inv else 'FAIL'}] invariant")
    results["rotation"] = {"cg_before": cg1, "cg_after": cg2, "dg_before": dg1,
                           "dg_after": dg2, "pass": inv}

    print()
    print("=" * 100)
    print("4. the two metrics are different numbers on a non-degenerate sample")
    print("=" * 100)
    A = torch.randn(100, d)
    B = torch.randn(100, d) * 2.0 + 2.0
    cg, dg = centroid_gap(A, B), distribution_gap(A, B)
    print(f"  CG {cg:.4f}   DG {dg:+.4f}   difference {abs(cg - dg):.4f}")
    diff = abs(cg - dg) > 0.01
    ok = ok and diff
    print(f"  [{'ok  ' if diff else 'FAIL'}] the metrics are distinct")
    results["distinct"] = {"cg": cg, "dg": dg, "pass": diff}

    print()
    print("=" * 100)
    print("5. identical inputs: DG = 0 and CG = 0 exactly")
    print("=" * 100)
    A = torch.randn(50, d)
    cg, dg = centroid_gap(A, A.clone()), distribution_gap(A, A.clone())
    print(f"  CG {cg:.6f}   DG {dg:+.6f}")
    zero = cg == 0.0 and abs(dg) < 1e-9
    ok = ok and zero
    print(f"  [{'ok  ' if zero else 'FAIL'}] both zero")
    results["identical"] = {"cg": cg, "dg": dg, "pass": zero}

    print()
    print(f"  OVERALL: {'GAP DEFINITIONS VERIFIED' if ok else 'DEFINITIONS NEED WORK'}")
    results["overall_pass"] = ok
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
