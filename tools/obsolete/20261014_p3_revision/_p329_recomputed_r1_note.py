# -*- coding: utf-8 -*-
r"""兑现 caption 的承诺：给 6 个 R@1 格补**重算值注**（2026-10-12）。

## 为什么

`_p327` 的 caption 写了 *"give the recomputed value in the text beside it"*，
但正文并没有逐格给重算值 → **承诺落空**。按"每个数字要有来源"铁律，
**要么兑现，要么改承诺**。此处选择兑现。

## 6 个格（`tools/_p322_strict_final_match.json`）

| 行/臂 | 发表 | 重算（归档 5-seed 均值） | 来源树 |
|---|---|---|---|
| OpenCLIP text_only | 0.643 | 0.6366 | `strict_freeze_oclip/r4` |
| OpenCLIP both | 0.680 | 0.6818 | 同上 |
| OpenCLIP vision_only | 0.672 | 0.6698 | 同上 |
| CLIP B/32† text_only | 0.621 | 0.6222 | `strict_freeze_b32_r4` |
| CLIP B/32† both | 0.679 | 0.6796 | 同上 |
| CLIP B/16† text_only | 0.651 | 0.6502 | `strict_freeze_b16/r4` |

    python tools\_p329_recomputed_r1_note.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

ANCHOR = (r"reproducible from the archive at the printed precision and give the recomputed "
          r"value in the text beside it.")

ADD = (r"reproducible from the archive at the printed precision. The recomputed five-seed "
       r"means, from \texttt{outputs/strict\_freeze\_oclip/r4}, "
       r"\texttt{outputs/strict\_freeze\_b32\_r4} and \texttt{outputs/strict\_freeze\_b16/r4} "
       r"respectively, are: OpenCLIP text-only $0.6366$, both-position $0.6818$, vision-only "
       r"$0.6698$; CLIP B/32$^\dagger$ text-only $0.6222$, both-position $0.6796$; and "
       r"CLIP B/16$^\dagger$ text-only $0.6502$.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = t.count(ANCHOR)
    print(f"  锚点命中 {n}")
    if n != 1:
        print("  🔴 未命中")
        return 1
    t2 = t.replace(ANCHOR, ADD)
    if not a.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_p329")
    if not bak.exists():
        shutil.copy2(F, bak)
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    checks = {
        "含重算值 0.6366": "0.6366" in t3,
        "含重算值 0.6796": "0.6796" in t3,
        "含重算值 0.6502": "0.6502" in t3,
        "承诺句已兑现（不再有 'in the text beside it'）":
            "in the text beside it" not in t3,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
