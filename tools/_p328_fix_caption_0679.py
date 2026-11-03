# -*- coding: utf-8 -*-
r"""修正 caption 里关于 0.679 的**不准确**表述（2026-10-12）。

## 我自己的错

`_p327` 先写入的版本说
*"Two cells … match no archived group to the printed precision"*，
但 `_p326` 的容差扫描发现 **`strict_freeze_rank/r4/both` 的 3-seed 子集**
（seeds 42/123/456，n_tr=245,760）均值 = **0.679667 → 四舍五入 0.679**，**确实命中**。

→ 必须改为精确表述：**0.651 无任何组命中；0.679 只有一个 3-seed 子集命中（非本行所报的 5-seed 单元）**。

    python tools\_p328_fix_caption_0679.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

OLD = (
    r"Two cells, CLIP B/32$^\dagger$ both-position ($0.679$) and CLIP B/16$^\dagger$ "
    r"text-only ($0.651$), match no archived group to the printed precision: the recomputed "
    r"strict-freezing means are $0.6796$ and $0.6502$, and an exhaustive scan of the $94$ "
    r"archived groups with at least three runs finds no group whose mean rounds to $0.651$. "
    r"We therefore flag these $R@1$ entries as unreproducible from the archive and report the "
    r"recomputed means in the text rather than repeat the printed ones.")

NEW = (
    r"Two cells, CLIP B/32$^\dagger$ both-position ($0.679$) and CLIP B/16$^\dagger$ "
    r"text-only ($0.651$), do not match the strict-freezing archive to the printed precision: "
    r"the recomputed means are $0.6796$ and $0.6502$. An exhaustive scan of the $94$ archived "
    r"groups with at least three runs finds no group whose mean rounds to $0.651$; the only "
    r"group whose mean rounds to $0.679$ is a three-seed subset "
    r"(\texttt{strict\_freeze\_rank/r4/both}, seeds $42$/$123$/$456$, $0.6797$), which is not "
    r"the five-seed cell this row reports. We therefore flag both $R@1$ entries as not "
    r"reproducible from the archive at the printed precision and give the recomputed value in "
    r"the text beside it.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"  旧句命中 {n}")
    if n == 0:
        i = t.find("match no archived group")
        print("  附近: " + repr(t[max(0, i - 300):i + 300]) if i >= 0 else "  （找不到旧句）")
        if "three-seed subset" in t:
            print("  ✅ caption 已是修正版，无需处理")
            return 0
        return 1
    t2 = t.replace(OLD, NEW)
    if not a.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_p328")
    if not bak.exists():
        shutil.copy2(F, bak)
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    checks = {
        "已含 3-seed 子集说明": "three-seed subset" in t3,
        "已含 0.651 无命中": "no group whose mean rounds to $0.651$" in t3,
        "旧的不准确句已去": "match no archived group" not in t3,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
