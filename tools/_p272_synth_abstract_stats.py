# -*- coding: utf-8 -*-
r"""PR 改稿合成·第一批（再补）：摘要统计限制（空白容忍）（2026-10-12）。

锚点原文（跨行，故字面替换失败）：
```
Across $n=204$ archived experiments the Distribution Gap predicts
retrieval degradation ($r=-0.71$) ...
```

    python tools\_p272_synth_abstract_stats.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PAT = re.compile(r"Across\s+\$n=204\$\s+archived\s+experiments\s+the\s+Distribution\s+Gap\s+"
                 r"predicts\s+retrieval\s+degradation")
NEW = (r"Across $n=204$ archived runs drawn from six dataset $\times$ backbone cells---so the "
       r"effective sample size is far smaller than $204$---the Distribution Gap predicts "
       r"retrieval degradation")

LIMIT_PAT = re.compile(r"cluster-robust inference")

ADD = (
    "\n"
    r"Because the runs are nested rather than independent, we report the gap--retrieval "
    r"association with cluster-robust inference: under dataset $\times$ backbone clustering "
    r"the slope is $-1.05$ (CR1 standard error $0.29$, $p=0.016$), the family-clustered "
    r"bootstrap 95\% interval is $[-0.89,-0.62]$, and a mixed model with random intercepts for "
    r"dataset, backbone and configuration gives $\beta=-0.95\pm0.08$. The within-cell and "
    r"between-cell slopes agree ($-1.07$ vs $-1.01$), so the relation is not a between-group "
    r"artefact, but its precision is much lower than $n=204$ suggests."
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    for rel in ("paper合/main_nc.tex",
                "paper合/NC_submission/latex_source/main_nc.tex",
                "paper合/main_springer.tex"):
        p = REPO / rel
        if not p.exists():
            print(f"  ❌ 缺 {rel}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = len(PAT.findall(t))
        has = bool(LIMIT_PAT.search(t))
        print(f"  {rel}: 锚点 {n} ｜ 已有统计段 {'✅' if has else '❌'}")
        if not a.apply or n == 0:
            continue
        t = PAT.sub(lambda m: NEW, t)
        if not has:
            i = t.find(r"\end{abstract}")
            if i > 0:
                t = t[:i] + ADD + "\n" + t[i:]
            else:
                print(f"    🔴 {rel} 找不到 \\end{{abstract}}")
        io.open(p, "w", encoding="utf-8", newline="").write(t)

    if not a.apply:
        print("  （预演）")
        return 0

    print()
    print("=" * 92)
    print("核对")
    print("=" * 92)
    ok = True
    for rel in ("paper合/main_nc.tex",
                "paper合/NC_submission/latex_source/main_nc.tex",
                "paper合/main_springer.tex"):
        p = REPO / rel
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        six = "six dataset" in t
        cr = "cluster-robust inference" in t
        print(f"  {'✅' if (six and cr) else '🔴'} {rel}: six-cells {six} ｜ CR 段 {cr}")
        ok = ok and six and cr
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
