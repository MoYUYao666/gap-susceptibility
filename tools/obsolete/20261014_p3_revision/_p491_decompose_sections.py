# -*- coding: utf-8 -*-
r"""精确分解 P3 各节的构成，定位可移出/可压缩的部分（2026-10-13）。

## 已知

- **14 → 13 页**（移出 `appendix.tex` 8,520 字符）⇒ **≈8,500 字符/页**
- **目标 ≤7 页** ⇒ 正文需 ≈**59,500 字符**（比现在少约 **30,000**）
- 现有 sections 合计 **77,139** 字符

**⇒ 必须精确定位"散文字符"与"环境（表/图/公式/证明）字符"的分布。**

    python tools\_p491_decompose_sections.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SEC = REPO / "paper3" / "paper_ieee" / "sections"
OUT = REPO / "outputs" / "analysis" / "p3_section_decomposition.json"

ENVS = ("table", "figure", "tabular", "equation", "align", "split", "proof",
        "theorem", "lemma", "corollary", "definition", "itemize", "enumerate")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}

    print("=" * 112)
    print("逐节：散文字符 vs 环境字符")
    print("=" * 112)
    print(f"  {'节':<16} {'总字符':>7} {'环境':>7} {'散文':>7} {'散文占比':>8} ｜ 环境明细")
    tot_all = tot_env = tot_prose = 0
    for f in sorted(SEC.glob("*.tex")):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        total = len(t)
        env_chars = 0
        detail = {}
        for e in ENVS:
            num = 0
            for m in re.finditer(rf"\\begin\{{{e}\*?\}}.*?\\end\{{{e}\*?\}}", t, re.S):
                num += len(m.group(0))
            if num:
                detail[e] = num
                env_chars += num
        prose = total - env_chars
        tot_all += total
        tot_env += env_chars
        tot_prose += prose
        print(f"  {f.stem:<16} {total:>7,} {env_chars:>7,} {prose:>7,} "
              f"{100*prose/max(total,1):>7.1f}% ｜ "
              f"{', '.join(f'{k}:{v:,}' for k, v in sorted(detail.items(), key=lambda x: -x[1])[:5])}")
        rep[f.stem] = {"total": total, "env": env_chars, "prose": prose, "detail": detail}
    print()
    print(f"  {'合计':<16} {tot_all:>7,} {tot_env:>7,} {tot_prose:>7,} "
          f"{100*tot_prose/tot_all:>7.1f}%")
    rep["_totals"] = {"total": tot_all, "env": tot_env, "prose": tot_prose}

    print()
    print("=" * 112)
    print("压缩优先级（散文量最大的前三节）")
    print("=" * 112)
    order = sorted(((k, v) for k, v in rep.items() if k != "_totals"),
                   key=lambda x: -x[1]["prose"])
    for k, v in order[:4]:
        print(f"  {k:<16} 散文 {v['prose']:>7,} 字符（≈{v['prose']/8500:.1f} 页）"
              f" ｜ 环境 {v['env']:>6,}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
