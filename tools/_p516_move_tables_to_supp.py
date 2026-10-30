# -*- coding: utf-8 -*-
r"""把 `experiments.tex` 的表/图移到 Supplementary（正文留一句结论 + 补充引用）（2026-10-13）。

## 依据

`tools/_p507`：`experiments.tex` = **27,799 字符**，其中表/图约 **5,500**：
- `tab:phase`（3 行表 + 长注）、`tab:sample`、`tab:sharegpt`、`tab:comparison`
- `fig:phase_transition`、`fig:counterfactual`、`fig:ers`

**⇒ 移入补充 = 省约 1 页，且内容完整保留**（补充材料本来就有这些表）。

**⚠️ 引用必须仍可解析**：正文的 `\ref{tab:phase}` 指向补充里的 label ⇒
**改为 `Supplementary Table~S1`** 这类**显式文本**（不依赖跨文档 label），
并在补充文档中给这些表加对应编号。

    python tools\_p516_move_tables_to_supp.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"
EX = PI / "sections" / "experiments.tex"
SUP = PI / "supplementary" / "supplementary.tex"

# label → 补充里的显式编号文本
MAP = {
    "tab:phase": "Supplementary Table~S1",
    "fig:phase_transition": "Supplementary Figure~S1",
    "fig:counterfactual": "Supplementary Figure~S2",
    "tab:sample": "Supplementary Table~S2",
    "tab:sharegpt": "Supplementary Table~S3",
    "fig:ers": "Supplementary Figure~S3",
    "tab:comparison": "Supplementary Table~S4",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ex = io.open(EX, encoding="utf-8", errors="replace").read()
    sup = io.open(SUP, encoding="utf-8", errors="replace").read()
    print(f"  experiments {len(ex):,} ｜ supplementary {len(sup):,}")

    envs = []
    for e in ("table", "figure", "table*", "figure*"):
        for m in re.finditer(rf"\\begin\{{{re.escape(e)}\}}.*?\\end\{{{re.escape(e)}\}}", ex, re.S):
            labs = re.findall(r"\\label\{([^}]*)\}", m.group(0))
            if labs:
                envs.append((labs[0], m.start(), m.end(), m.group(0)))
    envs.sort(key=lambda x: x[1])
    print(f"  找到 {len(envs)} 个带 label 的表/图：{[x[0] for x in envs]}")
    saved = 0
    t = ex
    for lab, i, j, blk in sorted(envs, reverse=True):
        saved += len(blk)
        t = t[:i] + t[j:]
    # 正文引用 → 显式补充编号
    for lab, txt in MAP.items():
        t = t.replace(rf"\ref{{{lab}}}", txt)
    print(f"  ⇒ 移出 {saved:,} 字符 → experiments {len(t):,}")

    if not a.apply:
        print("  （预演）")
        return 0
    for p in (EX, SUP):
        bak = p.with_suffix(".tex.bak_p516")
        if not bak.exists():
            shutil.copy2(p, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t)
    add = ["\n\n\\section{Tables and Figures}\n",
           "Kept here so that the main text can meet the journal's page limit; each is "
           "cited from the main text by its number below.\n"]
    for lab, i, j, blk in envs:
        add.append(f"\n% ---- {lab} ----\n{blk}\n")
    sup2 = sup.replace("\\bibliographystyle{IEEEtran}", "".join(add) + "\n\\bibliographystyle{IEEEtran}")
    io.open(SUP, "w", encoding="utf-8", newline="").write(sup2)
    print(f"  ✅ supplementary {len(sup):,} → {len(sup2):,}")
    # 复核：正文里不应再有这些 label 的 \ref
    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    left = [lab for lab in MAP if rf"\ref{{{lab}}}" in t2]
    print(f"  {'✅' if not left else '🔴'} 正文残留 \\ref：{left if left else '无'}")
    return 0 if not left else 2


if __name__ == "__main__":
    raise SystemExit(main())
