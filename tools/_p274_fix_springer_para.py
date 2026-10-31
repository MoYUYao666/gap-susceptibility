# -*- coding: utf-8 -*-
r"""修复 Springer 摘要里被转义写坏的统计段（2026-10-12）。

## 病因

前一版用 PowerShell 内联 here-string 写入，`$` 被吞成 `\$`，且 `0.29`→`.29`、`p`→`=`。
**这正是本项目"Windows 下必须写脚本文件、不要在命令行里拼 LaTeX"的既有教训。**

## 修法

用**行级定位**（不能靠损坏后的字面文本），找到 `cluster-robust inference` 所在的
整段（从 `Because the runs are nested` 到紧随的 `}`），替换为正确文本。

    python tools\_p274_fix_springer_para.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "main_springer.tex"

GOOD = (
    "Because the runs are nested rather than independent, we report the gap--retrieval\n"
    "association with cluster-robust inference: under dataset $\\times$ backbone clustering the\n"
    "slope is $-1.05$ (CR1 standard error $0.29$, $p=0.016$), the family-clustered bootstrap\n"
    "95\\% interval is $[-0.89,-0.62]$, and a mixed model with random intercepts for dataset,\n"
    "backbone and configuration gives $\\beta=-0.95\\pm0.08$. The within-cell and between-cell\n"
    "slopes agree ($-1.07$ vs $-1.01$), so the relation is not a between-group artefact, but its\n"
    "precision is much lower than $n=204$ suggests."
)

# 从 "Because the runs are nested" 起，到行首单独的 "}" 之前的全部内容
PAT = re.compile(r"Because the runs are nested.*?(?=\n\}\n)", re.S)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    ms = list(PAT.finditer(t))
    print(f"  锚点命中 {len(ms)}")
    if len(ms) != 1:
        for m in ms:
            print("   " + repr(m.group(0)[:160]))
        return 1
    bad = ms[0].group(0)
    print("  当前（坏）文本首 140 字符: " + repr(bad[:140]))
    t2 = PAT.sub(lambda _m: GOOD, t, count=1)
    if not a.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_p274")
    if not bak.exists():
        io.open(bak, "w", encoding="utf-8", newline="").write(t)
    io.open(F, "w", encoding="utf-8", newline="").write(t2)

    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    checks = {
        "无 \\$ 转义残留": "\\$" not in t3,
        "含 $\\times$": "$\\times$" in t3,
        "含 $0.29$": "$0.29$" in t3,
        "含 $p=0.016$": "$p=0.016$" in t3,
        "含 $n=204$": "$n=204$" in t3,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
