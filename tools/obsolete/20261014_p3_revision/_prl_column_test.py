# -*- coding: utf-8 -*-
r"""对照测试：哪种 Elsevier 模板/选项组合能产出真正的**双栏**排版，及每页词密度。

PRL 要求 "double column format and should not exceed 7 pages"，因此必须确认真实双栏下的容量。
本脚本对若干候选配置各编译一次，测量：页数、每页词数、是否双栏（按行宽与行内大空白判定）。

    python tools/_prl_column_test.py
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "paper_review_prl"

WORDS = ("the of and to in a is that for it as with on be by this are from or an at which "
         "we can model data method results show performance training adapters rank budget "
         "multimodal vision language evaluation benchmark protocol comparable evidence").split()

CONFIGS = [
    ("cas-dc", r"\documentclass[a4paper]{cas-dc}", True),
    ("cas-dc-final", r"\documentclass[a4paper,final]{cas-dc}", True),
    ("elsarticle-3p-twocol", r"\documentclass[3p,twocolumn,times]{elsarticle}", False),
    ("elsarticle-5p", r"\documentclass[5p,times]{elsarticle}", False),
]


def body(n: int) -> str:
    w = [WORDS[(i * 7) % len(WORDS)] for i in range(n)]
    return " ".join(w)


def make_doc(preamble: str, is_cas: bool, n_words: int) -> str:
    b = body(n_words)
    if is_cas:
        return rf"""{preamble}
\usepackage[numbers]{{natbib}}
\begin{{document}}
\shorttitle{{Column test}}
\shortauthors{{H. Wan}}
\title[mode=title]{{Column layout measurement}}
\author[1]{{Hongrui Wan}}
\affiliation[1]{{organization={{University of Southampton}}, city={{Southampton}}, country={{United Kingdom}}}}
\begin{{abstract}}Column layout measurement only.\end{{abstract}}
\begin{{highlights}}\item One\item Two\item Three\end{{highlights}}
\begin{{keywords}}a \sep b \sep c\end{{keywords}}
\maketitle
\section{{Introduction}} {b}
\section{{Body}} {b}
\section{{Discussion}} {b}
\end{{document}}
"""
    return rf"""{preamble}
\usepackage[numbers]{{natbib}}
\begin{{document}}
\title{{Column layout measurement}}
\author{{Hongrui Wan}}
\address{{University of Southampton, Southampton, United Kingdom}}
\begin{{abstract}}Column layout measurement only.\end{{abstract}}
\maketitle
\section{{Introduction}} {b}
\section{{Body}} {b}
\section{{Discussion}} {b}
\end{{document}}
"""


def measure(pdf: Path) -> tuple[int, int, str]:
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True).stdout.decode("utf-8", "ignore")
    m = re.search(r"Pages:\s+(\d+)", info)
    pages = int(m.group(1)) if m else -1
    txt = subprocess.run(["pdftotext", "-layout", "-f", "2", "-l", "2", str(pdf), "-"],
                         capture_output=True).stdout.decode("utf-8", "ignore")
    lines = [l for l in txt.splitlines() if l.strip()]
    n_words = sum(len(l.split()) for l in lines)
    gaps = sum(1 for l in lines if re.search(r"\S {12,}\S", l))
    kind = "双栏" if gaps >= 8 else "单栏"
    return pages, n_words, kind


def main() -> int:
    n = 1500
    print(f"每个配置：{3*n} 词正文\n")
    print(f"{'配置':<24}{'页数':>6}{'第2页词数':>10}{'版面':>8}")
    print("-" * 52)
    for name, preamble, is_cas in CONFIGS:
        tex = OUT / f"_col_{name}.tex"
        tex.write_text(make_doc(preamble, is_cas, n), encoding="utf-8", newline="")
        for _ in range(3):
            subprocess.run(["pdflatex", "-interaction=nonstopmode", tex.name], cwd=OUT, capture_output=True)
        pdf = tex.with_suffix(".pdf")
        if not pdf.exists():
            print(f"{name:<24}{'编译失败':>6}")
            continue
        pages, w, kind = measure(pdf)
        print(f"{name:<24}{pages:>6}{w:>10}{kind:>8}")
    print("\n注：'第2页词数'由 pdftotext 计数，双栏页约为单栏的两倍。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
