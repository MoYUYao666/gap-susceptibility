# -*- coding: utf-8 -*-
r"""修两处溯源错误/不一致（2026-10-12）。

## C4：噪声描述与代码不符（`empirical.tex:144`）

原句：*"an earlier single evaluation of **isotropic Gaussian noise** in the encoder parameters
suggested that vision-side noise degrades retrieval $2.6\times$ more than text-side noise"*

**代码事实**（`paper/scripts/noise_sensitivity.py`，由 `tools/_p255` 复核）：
- 噪声是 **`σ · std(W_i)` 逐张量缩放**，**不是各向同性/绝对**；
- "skip LayerNorm" 判据 `'layernorm' in name.lower()` **静默失效**（HF 命名为 `layer_norm1.weight`）
  → **LayerNorm 实际被注入**（192 张量/塔），占 vision 注入 Frobenius 范数的 **73.9%**。

## C5：`55` 与 `49` 的计数不一致

稿里写 *"55 archived LoRA runs (43 on Flickr30k, 6 on MS-COCO)"*（43+6=49≠55），
而 `outputs/analysis/ode_ledger.json::subsets` 给 **`lora n=55` / `lora_flickr n=49` /
`lora_coco n=6`**（**49+6=55** ✅）。

→ **稿里的括号拆分写错了**：应为 **49 on Flickr30k + 6 on MS-COCO = 55**。

    python tools\_p279_fix_noise_and_counts.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

NOISE_OLD = (r"An earlier single evaluation of isotropic Gaussian noise in the encoder "
             r"parameters suggested")
NOISE_NEW = (r"An earlier single evaluation in which each encoder tensor was perturbed by "
             r"Gaussian noise scaled to a fixed multiple of that tensor's own standard "
             r"deviation ($\sigma\,\mathrm{std}(W_i)$; despite a filter intended to exclude "
             r"them, LayerNorm parameters were perturbed too, and they carry $73.9\%$ of the "
             r"vision tower's injected Frobenius norm) suggested")

# 43 on Flickr30k → 49 on Flickr30k（43+6=49≠55 是错的；49+6=55 才对）
COUNT_PAIRS = [
    (r"55 archived LoRA runs (43 on Flickr30k, 6 on MS-COCO)",
     r"55 archived LoRA runs (49 on Flickr30k, 6 on MS-COCO)"),
    (r"$55$ LoRA runs are archived and reproducible ($43$ on Flickr30k, $6$ on MS-COCO)",
     r"$55$ LoRA runs are archived and reproducible ($49$ on Flickr30k, $6$ on MS-COCO)"),
    (r"We validate the ODE framework across 55 archived LoRA runs (43 on Flickr30k, "
     r"6 on MS-COCO)",
     r"We validate the ODE framework across 55 archived LoRA runs (49 on Flickr30k, "
     r"6 on MS-COCO)"),
    (r"The ODE framework derived in Section~\ref{sec:theory} makes quantitative predictions "
     r"that we now test against data. We fit the ODE on the 55 archived LoRA runs "
     r"(43 on Flickr30k, 6 on MS-COCO)",
     r"The ODE framework derived in Section~\ref{sec:theory} makes quantitative predictions "
     r"that we now test against data. We fit the ODE on the 55 archived LoRA runs "
     r"(49 on Flickr30k, 6 on MS-COCO)"),
    (r"Of the runs performed for this sweep, 55 LoRA trajectories are archived and analysed "
     r"here (43 on Flickr30k, 6 on MS-COCO)",
     r"Of the runs performed for this sweep, 55 LoRA trajectories are archived and analysed "
     r"here (49 on Flickr30k, 6 on MS-COCO)"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex"))) + \
        sorted(glob.glob(str(REPO / "paper合" / "main*.tex")))

    print("=" * 92)
    print("C4 噪声描述")
    print("=" * 92)
    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        n = t.count(NOISE_OLD)
        if not n:
            continue
        print(f"  {Path(f).name}: 命中 {n}")
        if a.apply:
            bak = Path(f).with_suffix(Path(f).suffix + ".bak_p279")
            if not bak.exists():
                shutil.copy2(f, bak)
            io.open(f, "w", encoding="utf-8", newline="").write(
                t.replace(NOISE_OLD, NOISE_NEW))
        break

    print()
    print("=" * 92)
    print("C5 计数拆分（43→49）")
    print("=" * 92)
    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for old, new in COUNT_PAIRS:
            n = t.count(old)
            if not n:
                continue
            print(f"  {Path(f).name}: 命中 {n}  →  {new[:60]}…")
            if a.apply:
                t = t.replace(old, new)
        if a.apply:
            io.open(f, "w", encoding="utf-8", newline="").write(t)

    if not a.apply:
        print("\n  （预演）")
        return 0

    print()
    print("=" * 92)
    print("核对")
    print("=" * 92)
    bad43 = badiso = 0
    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        bad43 += t.count("(43 on Flickr30k") + t.count("($43$ on Flickr30k")
        badiso += len(re.findall(r"isotropic Gaussian noise", t))
    print(f"  残留 '43 on Flickr30k': {bad43}（应 0）")
    print(f"  残留 'isotropic Gaussian noise': {badiso}（应 0）")
    return 0 if (bad43 == 0 and badiso == 0) else 2


if __name__ == "__main__":
    raise SystemExit(main())
