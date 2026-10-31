# -*- coding: utf-8 -*-
r"""只把表/图环境插回正文（**不恢复整个文件**，避免抹掉 26 处修改）（2026-10-13）。

## 为什么改法

`_p493` 的初版打算**用备份整体覆盖** `experiments.tex` —— **那会抹掉本轮对该节的全部修改**
（30× 降级、容量混淆、下游否证、matched-loss 重写、3/10 收紧……）。
**⇒ 改为：从备份里**只取 table/figure 环境**，插入当前文件的首次引用处。**

## 插入点

对每个 label，找**当前文件中 `\ref{<label>}` 首次出现**的位置，把该环境插到其**所在段落之后**。

    python tools\_p494_insert_envs.py [--apply]
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
BAK = PI / "sections" / "experiments.tex.bak_p492"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not BAK.exists():
        print(f"  🔴 缺备份 {BAK}")
        return 1
    orig = io.open(BAK, encoding="utf-8", errors="replace").read()
    cur = io.open(EX, encoding="utf-8", errors="replace").read()

    # 从备份收集环境 → 主 label
    envs = {}
    for e in ("table", "figure"):
        for m in re.finditer(rf"\\begin\{{{e}\*?\}}.*?\\end\{{{e}\*?\}}", orig, re.S):
            blk = m.group(0)
            labs = re.findall(r"\\label\{([^}]*)\}", blk)
            if labs:
                envs[labs[0]] = blk
    print(f"  备份里有 {len(envs)} 个带 label 的表/图：{sorted(envs)}")

    need = [l for l in envs if f"\\ref{{{l}}}" in cur]
    print(f"  正文当前引用其中 {len(need)} 个：{sorted(need)}")

    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p494")
    if not bak.exists():
        shutil.copy2(EX, bak)

    t = cur
    inserted = []
    for lab in need:
        blk = envs[lab]
        # 找首次 \ref 出现的段落末尾（下一个空行）
        m = re.search(rf"\\ref\{{{re.escape(lab)}\}}", t)
        if not m:
            continue
        end = t.find("\n\n", m.end())
        if end < 0:
            end = len(t)
        t = t[:end] + "\n\n" + blk + t[end:]
        inserted.append(lab)
    io.open(EX, "w", encoding="utf-8", newline="").write(t)
    print(f"  ✅ 插回 {len(inserted)} 个：{inserted}")
    print(f"  experiments.tex {len(cur):,} → {len(t):,} 字符")

    # 补充材料里去掉重复的表/图小节
    sup = io.open(SUP, encoding="utf-8", errors="replace").read()
    i = sup.find("\\section{Tables and Figures}")
    j = sup.find("\\bibliographystyle{IEEEtran}")
    if 0 < i < j:
        sup2 = sup[:i] + sup[j:]
        io.open(SUP, "w", encoding="utf-8", newline="").write(sup2)
        print(f"  ✅ 补充材料去重：{len(sup):,} → {len(sup2):,} 字符")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
