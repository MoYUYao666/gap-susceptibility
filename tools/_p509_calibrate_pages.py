# -*- coding: utf-8 -*-
r"""标定 P3 的"页 → 字符"映射，算出 ≤7 页的字符预算（2026-10-13）。

## 已知

| 配置 | 页数 |
|---|---|
| **IEEEtran `[journal]`**（当前） | **12** |
| **`elsarticle[final,3p,twocolumn]`**（PRL 自己的类） | **14** |

⇒ **换格式不是解法**（elsarticle 3p 反而更多页）。

    python tools\_p509_calibrate_pages.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"
OUT = REPO / "outputs" / "analysis" / "p3_page_budget.json"


def pages(pdf: Path):
    if not pdf.exists():
        return None
    r = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, encoding="utf-8", errors="replace")
    for ln in (r.stdout or "").splitlines():
        if ln.startswith("Pages:"):
            return int(ln.split(":", 1)[1].strip())
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    inputs = ["main.tex", "sections/introduction.tex", "sections/related_work.tex",
              "sections/theory.tex", "sections/experiments.tex",
              "sections/discussion.tex", "sections/conclusion.tex"]
    total = 0
    print("=" * 100)
    print("参与编译的字符总量")
    print("=" * 100)
    for f in inputs:
        p = PI / f
        if p.exists():
            n = len(io.open(p, encoding="utf-8", errors="replace").read())
            total += n
            print(f"  {f:<34} {n:>7,}")
    # 图片文件大小（图占版面的粗估）
    figs = glob.glob(str(PI / "figures" / "*"))
    figbytes = sum(os.path.getsize(x) for x in figs)
    print(f"  {'（合计，仅 tex 字符）':<34} {total:>7,}")
    print(f"  figures/ 目录 {len(figs)} 个文件 / {figbytes:,} B（图占版面另计）")

    p_ieee = pages(PI / "main.pdf")
    p_els = pages(PI / "main_els_test.pdf")
    print()
    print("=" * 100)
    print("标定")
    print("=" * 100)
    print(f"  IEEEtran [journal]      : {p_ieee} 页")
    print(f"  elsarticle[3p,twocolumn]: {p_els} 页")
    if p_ieee:
        per_page = total / p_ieee
        budget7 = total * 7 / p_ieee
        print(f"  ⇒ 实测 ≈ **{per_page:,.0f} 字符/页**（仅 tex 字符，不含图）")
        print(f"  ⇒ **≤7 页预算 ≈ {budget7:,.0f} 字符**")
        print(f"  ⇒ **需再删 {total - budget7:,.0f} 字符（现 {total:,} 的 "
              f"{100*(total-budget7)/total:.0f}%）**")

    # 逐节"若全删"的页数贡献
    print()
    print("=" * 100)
    print("逐节：现字符 → 折合页数（按上式）")
    print("=" * 100)
    rows = []
    for f in inputs[1:]:
        p = PI / f
        if not p.exists():
            continue
        n = len(io.open(p, encoding="utf-8", errors="replace").read())
        pg = n / (total / p_ieee) if p_ieee else 0
        rows.append((f.replace("sections/", "").replace(".tex", ""), n, pg))
        print(f"  {f.replace('sections/','').replace('.tex',''):<16} {n:>7,} 字符 ｜ "
              f"≈ {pg:>5.2f} 页")
    rep = {"total_tex_chars": total, "pages_ieeetran": p_ieee, "pages_elsarticle_3p": p_els,
           "chars_per_page": round(total / p_ieee, 1) if p_ieee else None,
           "budget_7_pages": round(total * 7 / p_ieee) if p_ieee else None,
           "must_cut": round(total - total * 7 / p_ieee) if p_ieee else None,
           "sections": [{"name": r[0], "chars": r[1], "pages": round(r[2], 2)} for r in rows]}
    print()
    print(f"  **结论：要合规到 ≤7 页，必须删除约 {rep['must_cut']:,} 字符（40%）。**")
    print( "  ⇒ 这**不是「压缩措辞」能完成的量级**，需要**结构性取舍**（移出整节 / 缩为要点式）。")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
