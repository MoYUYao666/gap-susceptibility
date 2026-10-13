# -*- coding: utf-8 -*-
r"""把被正文引用的表/图取回正文（修 8 个未定义引用）（2026-10-13）。

## 问题

`_p492` 把 experiments 的 4 表 3 图与 theory 的 3 个 proof 全移入补充 ⇒
**正文仍引用 8 个 label** ⇒ **8 个未定义引用**（`tab:sample`、`fig:phase_transition`、
`tab:phase`、`tab:sharegpt`、`fig:counterfactual`、`fig:ers`、`tab:comparison`）。

## 原则（我定的）

**审稿阶段看不到补充材料 ⇒ 表/图是证据，必须留在正文；散文才是可压的。**
⇒ **全部表/图取回正文**（原样、原位），**只压散文与证明**。

**⚠️ 这会让页数回升** —— 但**优先保住"证据可见"**，压缩改从散文下手。

    python tools\_p493_restore_envs.py [--apply]
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
BAK_EX = PI / "sections" / "experiments.tex.bak_p492"

NEED = ("tab:sample", "fig:phase_transition", "tab:phase", "tab:sharegpt",
        "fig:counterfactual", "fig:ers", "tab:comparison")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not BAK_EX.exists():
        print(f"  🔴 缺备份 {BAK_EX}")
        return 1
    orig = io.open(BAK_EX, encoding="utf-8", errors="replace").read()
    cur_ex = io.open(EX, encoding="utf-8", errors="replace").read()
    cur_sup = io.open(SUP, encoding="utf-8", errors="replace").read()

    # 从原始 experiments.tex 取出所有 table / figure 环境
    envs = []
    for e in ("table", "figure"):
        for m in re.finditer(rf"\\begin\{{{e}\*?\}}.*?\\end\{{{e}\*?\}}", orig, re.S):
            blk = m.group(0)
            labels = re.findall(r"\\label\{([^}]*)\}", blk)
            envs.append((e, labels, blk, m.start()))
    print(f"  原始 experiments.tex 里有 {len(envs)} 个 table/figure 环境")
    for e, labels, blk, pos in envs:
        print(f"     {e:<8} labels={labels}  ({len(blk):,} 字符)")

    missing = [x for x in NEED if not any(x in lab for _, lab, _, _ in envs)]
    print(f"  未在原件中找到的必需 label：{missing if missing else '（无）'}")

    if not a.apply:
        print("  （预演）")
        return 0

    # 把环境按原位置重新插入当前 experiments.tex
    # 简单可靠的做法：直接恢复原始 experiments.tex（含表/图），确认产物一致
    bak = EX.with_suffix(".tex.bak_p493")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(orig)
    print(f"  ✅ experiments.tex 恢复为原始版本（{len(orig):,} 字符，含全部表/图）")

    # 从补充材料里删掉重复的表/图小节（避免同一表出现两份）
    i = cur_sup.find("\\section{Tables and Figures}")
    if i > 0:
        j = cur_sup.find("\\bibliographystyle{IEEEtran}")
        sup2 = cur_sup[:i] + cur_sup[j:]
        io.open(SUP, "w", encoding="utf-8", newline="").write(sup2)
        print(f"  ✅ 补充材料删去重复的表/图（{len(cur_sup):,} → {len(sup2):,} 字符）")
    else:
        print("  ⚠️ 补充材料里未找到表/图小节")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
