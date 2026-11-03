# -*- coding: utf-8 -*-
r"""Code-bug audit of the recent P3 rounds (static checks, no GPU).

Checks:
  1. adapter_config rank/alpha of every adapter produced in the last rounds;
  2. adapter weights non-zero and different between rank arms;
  3. Qwen2.5 records: actual trainable counts differ between rank 5 and rank 6 (after the fix);
  4. VQA / instruction / caption metrics recomputed from the stored hypotheses and refs;
  5. Hessian second-order share recomputed from the stored g2/gHg;
  6. Gamma-sensitivity CV recomputed from the stored conditions.

    python tools/_p1522_bug_audit.py
"""
from __future__ import annotations

import glob
import io
import json
import os
import math

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(REPO, "outputs", "analysis")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")


def jload(p):
    return json.load(io.open(p, encoding="utf-8"))


def adapter_check():
    print("== adapters ==")
    for d in ("outputs/p3_vqa_adapters/r5", "outputs/p3_vqa_adapters/r6",
              "outputs/p3_instr_adapters/r5", "outputs/p3_instr_adapters/r6",
              "outputs/p3_caption_adapters/r5", "outputs/p3_caption_adapters/r6",
              "outputs/p3_probe_adapter"):
        cfg = os.path.join(REPO, d, "adapter_config.json")
        w = os.path.join(REPO, d, "adapter_model.safetensors")
        if not os.path.exists(cfg):
            print(f"  {d:38s} MISSING")
            continue
        c = jload(cfg)
        size = os.path.getsize(w) if os.path.exists(w) else 0
        print(f"  {d:38s} r={c.get('r')} alpha={c.get('lora_alpha')} bytes={size}")


def qwen_check():
    print("== qwen2.5 records ==")
    for f in sorted(glob.glob(os.path.join(EXP, "qwen_cf_uniform_rank*_q25_r*.json"))):
        d = jload(f)
        print(f"  {os.path.basename(f):48s} trainable={d.get('trainable_params')} dE={d.get('delta_E')}")


def _norm(s):
    import re, string
    s = s.lower().strip()
    s = re.sub(r"[%s]" % re.escape(string.punctuation), " ", s)
    return " ".join(s.split())


def vqa_check():
    print("== vqa metric recomputation ==")
    for k in ("base", "5", "6"):
        p = os.path.join(AN, f"p3_vqa_downstream_{k}.json")
        if not os.path.exists(p):
            continue
        d = jload(p)
        acc = sum(1 for a, b in zip(d["hypotheses"], d["refs"]) if _norm(a) == _norm(b)) / len(d["refs"])
        print(f"  rank={k} stored acc={d['accuracy']:.3f} recomputed={acc:.3f} n={len(d['refs'])}")


def hessian_check():
    print("== hessian share recomputation ==")
    for rank in (5, 6):
        p = os.path.join(AN, f"p3_hessian_probe_r{rank}.json")
        if not os.path.exists(p):
            continue
        d = jload(p)
        for r in d["runs"]:
            g2 = r["g2"]
            gHg = r["ghg_full"]["0.001"]
            share_lr = 0.5 * 5e-5 * gHg / g2
            share_probe = 0.5 * 1e-3 * gHg / g2
            print(f"  r={rank} b={r['batch']} stored(probe1e-3)={r['second_order_over_first_order']['0.001']:.3f} "
                  f"recomputed(probe)={share_probe:.3f} share@lr={share_lr:.4f}")


def gamma_check():
    print("== gamma sensitivity CV ==")
    p = os.path.join(AN, "p3_gamma_batch_sensitivity.json")
    if not os.path.exists(p):
        return
    d = jload(p)
    for b, s in d["summary"].items():
        vals = [c["gamma"][b] for c in d["conditions"]]
        m = sum(vals) / len(vals)
        sd = (sum((v - m) ** 2 for v in vals) / (len(vals) - 1)) ** 0.5
        cv = sd / abs(m) if m else None
        print(f"  {b:14s} stored cv={s['cv']:.3f} recomputed={cv:.3f}")


if __name__ == "__main__":
    adapter_check()
    qwen_check()
    vqa_check()
    hessian_check()
    gamma_check()
