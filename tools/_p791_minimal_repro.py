# -*- coding: utf-8 -*-
r"""Minimal reproduction of the chunked image-to-text discrepancy.

Rather than reason further, this builds a tiny synthetic gallery where the correct answer is known by
construction, then compares the loop against the chunked form. If the chunked form returns the right
answer on synthetic data, the fault is in the real data path; if it does not, the arithmetic is
wrong and the test says exactly where.

    python tools/_p791_minimal_repro.py
"""
from __future__ import annotations

import argparse
import sys

import torch


def loop_i2t(I, T, col, k=1):
    n_img = I.shape[0]
    hit = 0
    for i in range(n_img):
        top = (I[i] @ T.T).topk(k).indices
        if (col[top] == i).any():
            hit += 1
    return hit / n_img


def chunked_i2t(I, T, col, k=1, budget=500_000, fix=True):
    n_img, n_cap = I.shape[0], T.shape[0]
    hit = torch.zeros(n_img, dtype=torch.bool)
    step = max(1, budget // max(n_img, 1))
    for s in range(0, n_cap, step):
        sim = I @ T[s:s + step].T
        width = sim.shape[1]
        top = sim.topk(min(k, width), dim=1).indices
        if fix:
            top = top + s
        own = col if fix else col[s:s + width]
        hit |= (own[top] == torch.arange(n_img).unsqueeze(1)).any(dim=1)
    return float(hit.float().mean())


def main() -> int:
    ap = argparse.ArgumentParser()
    a = ap.parse_args()
    torch.manual_seed(0)
    n_img, per = 30, 5
    d = 16
    n_cap = n_img * per
    # captions of an image sit next to each other and are close to their image
    I = torch.nn.functional.normalize(torch.randn(n_img, d), dim=-1)
    T = torch.cat([I[i].unsqueeze(0).repeat(per, 1) + 0.01 * torch.randn(per, d)
                   for i in range(n_img)])
    T = torch.nn.functional.normalize(T, dim=-1)
    col = torch.tensor([i for i in range(n_img) for _ in range(per)])

    print(f"  synthetic gallery: {n_img} images, {n_cap} captions, {per} per image")
    print(f"  col[:12] = {col[:12].tolist()}")
    L = loop_i2t(I, T, col)
    print(f"  loop             R@1 = {L:.4f}   (expected 1.0000 by construction)")
    for fix in (False, True):
        for budget in (500_000, 100, 30):
            c = chunked_i2t(I, T, col, budget=budget, fix=fix)
            ok = abs(c - L) < 1e-9
            print(f"  chunked fix={str(fix):<5} budget={budget:<7} -> R@1 = {c:.4f}  "
                  f"{'OK' if ok else 'WRONG'}")
    print()
    print("  reading:")
    print("   - if fix=False is wrong and fix=True is right, the offset was the fault and is now fixed")
    print("   - if both are wrong, the accumulator itself is the fault")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
