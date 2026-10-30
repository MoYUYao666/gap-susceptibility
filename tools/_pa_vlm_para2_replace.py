# -*- coding: utf-8 -*-
r"""替换 `supplement.tex` 那段收尾（旧单 seed 结论）（2026-10-10）。

## 原文（站不住）

> *"Two conclusions follow. First, the framework is not confined to dual-encoders: … adapting the
> vision tower alone is **again the least effective option**, moving the gap by $11\\%$ where the
> other arms move it by $74\\%$ and $84\\%$. Second, **the identity of the best site does not carry
> over** --- on this model the both-position arm leads … The evidence is preliminary: one model,
> one seed, small scale, and quantised weights."*

**问题**：① 数字是单 seed 4-bit；② "both leads" 在 3 seed 下**不显著**（$0.23$ sd）；
③ "quantised weights" 已改为 bf16。

    python tools\_pa_vlm_para2_replace.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "supplement.tex"

OLD = (r"""Two conclusions follow. First, the framework is not confined to dual-encoders: the distribution gap decays
exponentially here as well, and adapting the vision tower alone is again the least effective option, moving
the gap by $11\%$ where the other arms move it by $74\%$ and $84\%$. Second, the identity of the best site
does not carry over --- on this model the both-position arm leads --- which is the same finding the main text
reports across backbones and datasets, now observed across an architecture family. The evidence is
preliminary: one model, one seed, small scale, and quantised weights.""")

NEW = (r"""Two conclusions follow. First, the framework is not confined to dual-encoders: the distribution gap
decays here as well, and adapting the vision tower alone is again the weakest of the three arms, reducing
$DG^*$ by $12.4\pm4.7\%$ against $66.8\pm6.5\%$ and $85.2\pm11.2\%$ for the other two, a separation of
$4.9$ pooled standard deviations on the centroid gap. Second, and in contrast to the dual-encoder result,
the ordering between the two stronger arms is not resolved on this model: they differ by $0.23$ pooled
standard deviations, and three seeds are needed before that becomes visible, since one seed alone produces
a gap between them of the size the dual-encoders show. The evidence remains preliminary --- one model, small
scale, and a training pipeline whose quantised variant we could not reproduce --- but it is enough to say
that on a decoder VLM the site that is weakest is the same one, while the identity of the best site is
not established.""")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"=== 锚点命中 {n} ===")
    if n != 1:
        return 1
    t2 = t.replace(OLD, NEW, 1)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    for k in (r"$4.9$ pooled standard deviations", r"$0.23$ pooled", "is not established"):
        assert k in t3, f"断言失败：缺 {k}"
    assert "least effective option" not in t3
    assert "quantised weights" not in t3
    print("  ✅ 已替换")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
