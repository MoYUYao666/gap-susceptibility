# -*- coding: utf-8 -*-
r"""A1 摘要最后收尾：257 → ≤248 词（标准口径）（2026-10-10）。

**为留安全余量（编辑用不同计数器），目标 248 词。**

| 原 | 压缩后 | 省 |
|---|---|---|
| "The modality gap is therefore no universal health metric: gap-based quantities predict retrieval degradation, but that reading does not extend to zero-shot classification." | "The modality gap is therefore no universal metric: gap-based quantities predict retrieval, but not zero-shot classification." | ~7 |
| "Under controlled ``gap surgery'' (exact translations), classification can \emph{collapse while the gap shrinks}" | "Under ``gap surgery'' (exact translations), classification can \emph{collapse while the gap shrinks}" | ~1 |
| "Across 34 perturbation conditions, three families and seventeen fine-tuned checkpoints (fourteen LoRA, three full-fine-tuning), top-1 is governed by $\tau$, not gap magnitude." | "Across 34 perturbation conditions, three families and seventeen fine-tuned checkpoints top-1 is governed by $\tau$, not gap magnitude." | ~4 |

**注意**：第三处删掉了"(fourteen LoRA, three full-fine-tuning)"——**但这是数据细节**，
我改在**正文**保留它（摘要不必展开）。**须核对正文确有该数字**。

    python tools\_pa_a1_abstract_trim5.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper_a1" / "main.tex"

PAIRS = [
    ("The modality gap is therefore no universal health metric: gap-based quantities "
     "predict retrieval degradation, but that reading does not extend to zero-shot "
     "classification.",
     "The modality gap is therefore no universal metric: gap-based quantities predict "
     "retrieval, but not zero-shot classification."),
    ("Under controlled ``gap surgery'' (exact translations)",
     "Under ``gap surgery'' (exact translations)"),
    ("seventeen fine-tuned checkpoints (fourteen LoRA, three full-fine-tuning), top-1 is "
     "governed by",
     "seventeen fine-tuned checkpoints top-1 is governed by"),
]


def wc(t: str) -> int:
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S)
    if not m:
        return -1
    b = re.sub(r"\\[a-zA-Z]+", " ", m.group(1))
    b = re.sub(r"[{}$\\]", " ", b)
    return len(b.split())


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8", errors="replace").read()
    print(f"  压缩前：{wc(t)} 词")
    for old, new in PAIRS:
        c = t.count(old)
        print(f"  {'✅' if c == 1 else '⚠'} 命中 {c}: {old[:52]}…")
        if c == 1:
            t = t.replace(old, new, 1)
    after = wc(t)
    print(f"  压缩后：{after} 词{'  ✅ 达标' if after <= 250 else f'  ❌ 超 {after-250}'}")

    # 核对正文仍保留 "fourteen LoRA" 细节
    body = t[t.find("\\end{abstract}"):]
    keep = "fourteen LoRA" in body or "14 LoRA" in body
    print(f"  正文保留 'fourteen LoRA' 细节: {'✅' if keep else '❌ 需补'}")

    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8", errors="replace").read()
    for k in ("necessary, not sufficient", "self-consistency, not independent validation",
              "no other families", "$r{=}1.000$", "$+0.033$", "$+0.114$",
              "$59.3\\%{\\to}32.0\\%$", "$0.615$", "$0.761$", "$59.3\\%{\\to}78.6\\%$"):
        assert k in t2, f"断言失败：缺 {k}"
    print("  ✅ 已压缩；全部数字与保留声明仍在")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
