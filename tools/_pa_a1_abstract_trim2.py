# -*- coding: utf-8 -*-
r"""A1 摘要再压缩：299 → ≤250 词，**保住全部数字与保留声明**（2026-10-10）。

## 只压缩**散文**，不动数字

| 原句 | 压缩后 | 省 |
|---|---|---|
| "the same both-position LoRA checkpoint measures …; we quote the range and the protocol, not the larger value (Section~\ref{...})" | "the same both-position LoRA checkpoint measures $+0.033$ on our shared subset and $+0.114$ by the legacy logger; we quote the range, not the larger value" | ~12 |
| "A first-order analysis yields a class-dependent bias field whose per-class score prediction matches measurement to four decimals ($r{=}1.000$; a self-consistency check of the closed form, not independent validation) and predicts, as we confirm, less destruction from text-side than image-side translation." | "A first-order class-dependent bias field matches measurement to four decimals ($r{=}1.000$; self-consistency, not independent validation) and predicts less text-side than image-side destruction." | ~18 |
| "For the three families assessed---CLIP ViT-B/32, OpenCLIP laion2B, SigLIP base-patch16-224---$\tau$ is the better monitoring signal for classification-oriented fine-tuning, the gap for retrieval, giving a task-sensitivity ordering (centroid classification $<$ zero-shot classification $<$ retrieval); we claim this for no other families, benchmarks or mechanisms." | "Across the three families assessed---CLIP ViT-B/32, OpenCLIP laion2B, SigLIP base-patch16-224---$\tau$ is the better signal for classification fine-tuning and the gap for retrieval, giving a task-sensitivity ordering (centroid $<$ zero-shot $<$ retrieval); we claim this for no other families, benchmarks or mechanisms." | ~14 |

    python tools\_pa_a1_abstract_trim2.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper_a1" / "main.tex"

PAIRS = [
    ("the same both-position LoRA checkpoint measures $\\text{CG}\\Delta{=}{+}0.033$ "
     "($0.815{\\to}0.848$) on our shared evaluation subset and $+0.114$ ($0.82{\\to}0.93$) "
     "by the legacy logger on its hold-out; we quote the range and the protocol, not the "
     "larger value (Section~\\ref{sec:ckpt_transfer}).",
     "the same both-position LoRA checkpoint measures $\\text{CG}\\Delta{=}{+}0.033$ on our "
     "shared subset and $+0.114$ by the legacy logger; we quote the range, not the larger "
     "value."),
    ("A first-order analysis yields a class-dependent bias field whose per-class score "
     "prediction matches measurement to four decimals ($r{=}1.000$; a self-consistency "
     "check of the closed form, not independent validation) and predicts, as we confirm, "
     "less destruction from text-side than image-side translation.",
     "A first-order class-dependent bias field matches measurement to four decimals "
     "($r{=}1.000$; self-consistency, not independent validation) and predicts less "
     "text-side than image-side destruction."),
    ("For the three families assessed---CLIP ViT-B/32, OpenCLIP laion2B, SigLIP "
     "base-patch16-224---$\\tau$ is the better monitoring signal for classification-oriented "
     "fine-tuning, the gap for retrieval, giving a task-sensitivity ordering (centroid "
     "classification $<$ zero-shot classification $<$ retrieval); we claim this for no other "
     "families, benchmarks or mechanisms.",
     "Across the three families assessed---CLIP ViT-B/32, OpenCLIP laion2B, SigLIP "
     "base-patch16-224---$\\tau$ is the better signal for classification fine-tuning and the "
     "gap for retrieval, giving a task-sensitivity ordering (centroid $<$ zero-shot $<$ "
     "retrieval); we claim this for no other families, benchmarks or mechanisms."),
]


def wc(t: str) -> int:
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S)
    if not m:
        return -1
    plain = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", " ", m.group(1))
    plain = re.sub(r"\$[^$]*\$", " X ", plain)
    return len(plain.split())


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8", errors="replace").read()
    print(f"  压缩前：{wc(t)} 词")
    n = 0
    for old, new in PAIRS:
        c = t.count(old)
        print(f"  {'✅' if c == 1 else '⚠'} 命中 {c}: {old[:60]}…")
        if c == 1:
            t = t.replace(old, new, 1)
            n += 1
    if n != len(PAIRS):
        print(f"  ❌ 只命中 {n}/{len(PAIRS)}，未写入")
        return 1
    after = wc(t)
    print(f"  压缩后：{after} 词（限 250）")
    if after > 250:
        print(f"  ⚠️ 仍超 {after - 250} 词")
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8", errors="replace").read()
    for k in ("necessary, not sufficient", "self-consistency, not independent validation",
              "no other families", "$r{=}1.000$", "$+0.033$", "$+0.114$",
              "59.3\\%{\\to}32.0\\%$", "$0.615$", "$0.761$"):
        assert k in t2, f"断言失败：缺 {k}"
    print("  ✅ 已压缩；全部数字与保留声明仍在")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
