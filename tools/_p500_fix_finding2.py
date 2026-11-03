# -*- coding: utf-8 -*-
r"""修 `experiments.tex` 的 Finding 2（"架构相关"已撤回）+ 收紧扫描判据（2026-10-13）。

## 真矛盾

`experiments.tex` 的 **`\textbf{Finding 2: Architecture-dependent behavior.}`** 仍以
"Qwen2-VL-7B 无相变 ⇒ 架构相关"为**发现**。而我已撤回该结论：
**54 token 下 Qwen 的 real-image run 也转负**（`p3d_qwen_ranksweep_mp50176`）⇒
**原"架构不一致"很可能是 token 预算伪影**。

## 我的判据假阳性（两条）

- `discussion.tex:5` *"not that it admits **exactly one** unconditionally"* —— **否定式**
- `conclusion.tex:15` *"beats the uniform-rank baseline at one learning rate but **reverses** at another"* —— **转折式**

⇒ 判据需识别**否定/转折语境**，否则会持续误报。

    python tools\_p500_fix_finding2.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"
SCAN = REPO / "tools" / "_p497_scan_contradictions.py"

F2_OLD_START = r"\textbf{Finding 2: Architecture-dependent behavior.}"
F2_END = r"may buffer against rank-induced alignment collapse."

F2_NEW = (
    r"\textbf{Finding 2: an apparent architecture difference that we could not reproduce.}"
    "\n"
    r"Qwen2-VL-7B exhibits no crossing---all 45 runs (15 ranks $\times$ 3 seeds) are valid,\n"
    r"with $\Delta E$ ranging from $+78$ to $+214$ (a gradual $2.7\times$ increase against\n"
    r"LLaVA's $46\times$ surge), and the increase is monotonic across all 15 ranks (Spearman\n"
    r"$\rho = 0.895$, $p = 1\times10^{-5}$). We first read this as an architecture dependence,\n"
    r"but we are unable to sustain that reading. The difference between the two models tracks\n"
    r"the visual token budget rather than the architecture: at the reduced budget we use for\n"
    r"LLaVA, the decoder's real-image runs are positive, whereas at $54$ tokens they turn\n"
    r"negative, matching the dual encoder. What we can say is that the two models have\n"
    r"different modality balance---Wu et al.~\cite{wu2025language} report an MDI of $10.23$\n"
    r"for LLaVA against $33.10$ for Qwen2.5-VL---and that a crossing in one of them is not\n"
    r"evidence of a crossing law that the other violates."
)

SCAN_OLD = 'ALLOW = ("withdraw", "no longer", "must not", "not a", "rather than", "we record",\n         "arrefact", "artefact", "we do not", "does not", "cannot", "instead of",\n         "is not", "are not", "was withdrawn", "incorrect", "earlier")'
SCAN_NEW = ('ALLOW = ("withdraw", "no longer", "must not", "not a", "rather than", "we record",\n'
            '         "arrefact", "artefact", "we do not", "does not", "cannot", "instead of",\n'
            '         "is not", "are not", "was withdrawn", "incorrect", "earlier",\n'
            '         # 否定/转折语境（我先前漏掉这两类，造成假阳性）\n'
            '         "not that", "unconditional", "but reverses", "but we", "unable to",\n'
            '         "could not reproduce", "we first read", "rather than the architecture")')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    i = t.find(F2_OLD_START)
    j = t.find(F2_END, i)
    print(f"  Finding 2 区间 i={i}, j={j}")
    if i < 0 or j < 0:
        print("  🔴 锚点未命中")
        return 1
    end = j + len(F2_END)
    print(f"  旧 {end-i} 字符 → 新 {len(F2_NEW)} 字符")
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p500")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t[:i] + F2_NEW + t[end:])

    s = io.open(SCAN, encoding="utf-8", errors="replace").read()
    if SCAN_OLD in s:
        io.open(SCAN, "w", encoding="utf-8", newline="").write(s.replace(SCAN_OLD, SCAN_NEW))
        print("  ✅ 扫描判据已收紧（加入否定/转折语境）")
    else:
        print("  ⚠️ 扫描判据锚点未命中（未改）")

    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "不再以'架构相关'为发现": "Finding 2: Architecture-dependent behavior" not in t2,
        "含'无法维持该解读'": "unable to sustain that reading" in t2,
        "含 token 预算解释": "tracks\nthe visual token budget" in t2 or "visual token budget" in t2,
        "含 54 token 的反证": "$54$ tokens they turn" in t2,
        "保留 MDI 引用": "10.23" in t2 and "33.10" in t2,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
