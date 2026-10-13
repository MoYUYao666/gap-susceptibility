# -*- coding: utf-8 -*-
r"""受控测量 cas-dc 模板下「7 页预算」：分别量化前置块与参考文献的占用，再反推正文词数。

关键发现：cas-dc 把 abstract / highlights / keywords 排成**通栏前置块**（约占一整页），
正文才是双栏。因此"7 页含一切"时，必须先扣掉前置块与参考文献，剩下的才是正文预算。

做法（受控对照）：
  A. 只放前置块 + 标题，正文空      → 测前置块占几页
  B. 前置块 + 正文 N 词，无参考文献  → 测正文词密度（词/页）
  C. 前置块 + 正文 N 词 + M 条引用   → 测每条引用占多少页
再按 7 页上限组合出正文词预算。

    python tools/_prl_budget_measure.py
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "paper_review_prl"

WORDS = ("the of and to in a is that for it as with on be by this are from or an at which "
         "we can model data method results show performance training adapters rank budget "
         "multimodal vision language evaluation benchmark protocol comparable evidence "
         "however therefore because between within without across both each such more less").split()


def body(n: int) -> str:
    return " ".join(WORDS[(i * 7) % len(WORDS)] for i in range(n))


def doc(n_body: int, n_refs: int) -> str:
    refs = "\n".join(
        f"\\bibitem{{r{i}}} A. Author{i}, B. Author{i}, Title of test reference {i}, "
        f"Journal of Testing {i} ({2000 + i % 25}) 1--10."
        for i in range(1, n_refs + 1))
    bib = (f"\\begin{{thebibliography}}{{00}}\n{refs}\n\\end{{thebibliography}}" if n_refs else "")
    secs = ""
    if n_body:
        per = n_body // 3
        secs = (f"\\section{{Introduction}} {body(per)}\n"
                f"\\section{{Body}} {body(per)}\n"
                f"\\section{{Discussion}} {body(n_body - 2 * per)}\n")
    return rf"""\documentclass[a4paper]{{cas-dc}}
\usepackage[numbers]{{natbib}}
\begin{{document}}
\shorttitle{{Budget measurement}}
\shortauthors{{H. Wan}}
\title[mode=title]{{A seven-page double-column review: measuring the writing budget before drafting}}
\author[1]{{Hongrui Wan}}
\affiliation[1]{{organization={{University of Southampton}}, city={{Southampton}}, postcode={{SO17 1BJ}}, country={{United Kingdom}}}}
\begin{{abstract}}
We measure how much of a seven-page double-column article is consumed by its front matter and its
reference list, so that the word budget for the body can be fixed before writing begins rather than
discovered after a desk-rejection-triggering overflow. The measurement is deliberately literal: we
compile variants of the same document while varying only the body length and the number of
references, then read the resulting page count from the compiled output. This abstract is
representative in length of the abstract the actual review will carry, so that the front matter
measurement is not an underestimate.
\end{{abstract}}
\begin{{highlights}}
\item Front matter and references consume page budget
\item Body word budget follows from the measurement
\item Seven pages is a hard limit at this journal
\end{{highlights}}
\begin{{keywords}}
page budget \sep writing plan \sep double column \sep reference list
\end{{keywords}}
\maketitle
{secs}
{bib}
\end{{document}}
"""


def compile_variant(tag: str, n_body: int, n_refs: int) -> int:
    tex = OUT / f"_budget_{tag}.tex"
    tex.write_text(doc(n_body, n_refs), encoding="utf-8", newline="")
    for _ in range(3):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", tex.name], cwd=OUT, capture_output=True)
    pdf = tex.with_suffix(".pdf")
    if not pdf.exists():
        return -1
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True).stdout.decode("utf-8", "ignore")
    m = re.search(r"Pages:\s+(\d+)", info)
    return int(m.group(1)) if m else -1


def main() -> int:
    print("=== A. 前置块占用（正文空、无引用）===")
    p_front = compile_variant("front", 0, 0)
    print(f"  标题+摘要+highlights+关键词 → {p_front} 页\n")

    print("=== B. 正文词密度（含前置块，无引用）===")
    n_b = 3000
    p_b = compile_variant("body", n_b, 0)
    body_pages = p_b - p_front
    density = n_b / body_pages if body_pages > 0 else 0
    print(f"  正文 {n_b} 词 → 总 {p_b} 页（扣前置 {p_front} 页 = 正文 {body_pages} 页）")
    print(f"  → 词密度 ≈ {density:.0f} 词/页\n")

    print("=== C. 参考文献占用（正文 1500 词，加 50 条引用）===")
    p_r0 = compile_variant("ref0", 1500, 0)
    p_r50 = compile_variant("ref50", 1500, 50)
    ref_pages = p_r50 - p_r0
    per_ref = ref_pages / 50 if ref_pages > 0 else 0
    print(f"  1500 词 + 0 引用 → {p_r0} 页 ；+50 引用 → {p_r50} 页")
    print(f"  → 50 条引用占 {ref_pages} 页，约 {per_ref:.3f} 页/条\n")

    print("=== 结论：7 页上限下的写作预算 ===")
    for n_refs in (40, 50, 60):
        used = p_front + n_refs * per_ref
        remaining = 7 - used
        words = int(remaining * density)
        verdict = "可行" if words >= 2500 else "引用偏多"
        print(f"  {n_refs:>3} 条引用：前置 {p_front} 页 + 引用 {used - p_front:.1f} 页 "
              f"= {used:.1f} 页 → 正文余 {remaining:.1f} 页 ≈ **{words} 词**  ({verdict})")
    print("\n建议：目标 ~3,000 词正文 + 50 条引用，留 0.3–0.5 页余量应对图表与排版误差。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
