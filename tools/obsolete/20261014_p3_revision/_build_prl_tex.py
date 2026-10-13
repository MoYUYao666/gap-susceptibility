# -*- coding: utf-8 -*-
r"""把 MANUSCRIPT.md 转成 Elsevier cas-dc 双栏 LaTeX（PRL 投稿用）。

- 参考文献由 `_refs_used.json`（取自已核验的 refs_all.json）自动生成，**不手抄**
- 首页脚注含机构邮箱（PRL 强制要求）
- highlights / keywords 从稿内抽取
- 编译后用 pdfinfo 读页数，对照 7 页硬上限

    python tools/_build_prl_tex.py
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "paper_review_prl"
MD = OUT / "MANUSCRIPT.md"
TEX = OUT / "main_prl.tex"
REFS = OUT / "_refs_used.json"

HIGHLIGHTS = [
    "Adaptation is two decisions: where capacity goes, and how it is divided",
    "Most multimodal PEFT papers conflate the two decisions",
    "Reported POPE values differ without naming the benchmark subset",
    "A protocol change moves MMBench scores by an order of magnitude",
    "Twelve reporting items would make adaptation results comparable",
]


def md_emphasis(s: str) -> str:
    """把 markdown 强调转成 LaTeX：**x** → \\textbf{x}，*x* → \\emph{x}。

    修复的缺陷：摘要此前只做字符转义，未做强调转换，导致编译出的 PDF 里
    字面印着 `problem of *method selection*`（星号进入投稿稿）。
    """
    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s, flags=re.S)
    s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"\\emph{\1}", s, flags=re.S)
    return s


def clean_abstract(s: str) -> str:
    """摘要：先接 markdown 强调，再对其余部分做 LaTeX 转义，避免把命令转义掉。"""
    s = re.sub(r"\s+", " ", s).strip()
    parts = re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", s)
    out = []
    for p in parts:
        if p.startswith("**") and p.endswith("**") and len(p) > 4:
            out.append("\\textbf{" + latex_escape(p[2:-2]) + "}")
        elif p.startswith("*") and p.endswith("*") and len(p) > 2:
            out.append("\\emph{" + latex_escape(p[1:-1]) + "}")
        else:
            out.append(latex_escape(p))
    return "".join(out)


def latex_escape(s: str) -> str:
    s = s.replace("\\", r"\textbackslash{}")
    for a, b in [("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"), ("_", r"\_"),
                 ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}")]:
        s = s.replace(a, b)
    # 已转义的 \& 等不要被二次转义
    return s


def md_table_to_tex(block: str) -> str:
    """markdown 管道表 → LaTeX tabular（单栏通栏，放 table* 里）。"""
    rows = [r.strip() for r in block.splitlines() if r.strip().startswith("|")]
    if len(rows) < 2:
        return ""
    cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
    header, body = cells[0], [r for r in cells[2:]] if len(cells) > 2 else []
    ncol = len(header)
    spec = "p{%.2f\\linewidth}" % (0.96 / ncol)
    lines = [r"\begin{table}[t]", r"\centering", r"\footnotesize",
             r"\begin{tabular}{%s}" % ("l" + spec * (ncol - 1)), r"\toprule",
             " & ".join(inline(c) for c in header) + r" \\", r"\midrule"]
    for r in body:
        r = (r + [""] * ncol)[:ncol]
        lines.append(" & ".join(inline(c) for c in r) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines)


def md_to_tex(text: str) -> str:
    """极简 markdown→LaTeX：标题、段落、加粗、斜体、引用键、管道表。"""
    out: list[str] = []
    for block in text.split("\n\n"):
        b = block.strip()
        if not b:
            continue
        if b.startswith("|"):
            t = md_table_to_tex(b)
            if t:
                out.append(t)
            continue
        if b.startswith("**Table"):          # 表题紧随表体，单独处理
            cap = re.sub(r"^\*\*Table\s*\d+\.?\*\*\s*", "", b)
            out.append(r"\noindent\textbf{Table 1.} " + inline(cap.replace("\n", " ")))
            continue
        if b.startswith("## "):
            out.append("\\section{%s}" % latex_escape(b[3:].strip()))
            continue
        if b.startswith("### "):
            out.append("\\subsection{%s}" % latex_escape(b[4:].strip()))
            continue
        if b.startswith("# ") or b.startswith(">") or b.startswith("- ["):
            continue
        if b.startswith("**Keywords"):
            continue
        if b.startswith("---"):
            continue
        # 列表项
        if re.match(r"^\d+\.\s", b) or b.startswith("- "):
            items = []
            for line in b.splitlines():
                line = re.sub(r"^(\d+\.|-)\s+", "", line.strip())
                if line:
                    items.append("  \\item " + inline(line))
            if items:
                out.append("\\begin{enumerate}\n" + "\n".join(items) + "\n\\end{enumerate}")
            continue
        out.append(inline(b.replace("\n", " ")))
    return "\n\n".join(out)


def inline(s: str) -> str:
    # 引用键 [a; b] → \cite{a,b}
    def cite(m: re.Match) -> str:
        keys = [k.strip() for k in re.split(r"[;,]", m.group(1)) if re.match(r"^[a-z][a-z0-9_]*\d", k.strip())]
        return "\\cite{%s}" % ",".join(keys) if keys else m.group(0)
    s = re.sub(r"\[([a-z][a-z0-9_]*(?:\s*[;,]\s*[a-z][a-z0-9_]*)*)\]", cite, s)
    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
    s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"\\emph{\1}", s)
    # 转义剩余特殊字符（保留已生成的命令）
    parts = re.split(r"(\\cite\{[^}]*\}|\\textbf\{[^}]*\}|\\emph\{[^}]*\})", s)
    return "".join(p if p.startswith("\\") else latex_escape(p) for p in parts)


def bibitems() -> str:
    items = json.loads(REFS.read_text(encoding="utf-8"))
    lines = ["\\begin{thebibliography}{00}"]
    for r in sorted(items, key=lambda x: x["key"]):
        au = r["authors"] or "Unknown"
        ti = r["title"] or ""
        yr = r["year"] or ""
        ve = r["venue"] or ""
        bits = f"{au}, {ti}"
        if ve:
            bits += f", {ve}"
        if yr:
            bits += f" ({yr})"
        lines.append(f"\\bibitem{{{r['key']}}} {latex_escape(bits)}.")
    lines.append("\\end{thebibliography}")
    return "\n".join(lines)


def main() -> int:
    md = MD.read_text(encoding="utf-8")
    # 抽摘要
    m = re.search(r"## Abstract\s*(.+?)\n\n\*\*Keywords", md, re.S)
    abstract = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
    # 抽正文（Abstract 之后、到结论）
    body_md = md.split("## 1. Introduction", 1)[-1]
    body_md = body_md.split("## Abstract", 1)[0]
    body = md_to_tex("## 1. Introduction" + body_md)

    hl = "\n".join(f"\\item {latex_escape(h)}" for h in HIGHLIGHTS)

    # Figure 1：决策空间示意图（由 tools/_make_prl_figure.py 生成）
    figure = r"""
\begin{figure*}[t]
\centering
\includegraphics[width=0.92\textwidth]{figures/fig1_decision_space.pdf}
\caption{The two decisions and their independence. The horizontal axis is where adaptive capacity is
placed; the vertical axis is how a fixed budget is divided. Points mark the approximate position of
representative methods (a qualitative sketch, not measured coordinates). The shaded column shows that
one site admits several allocation strategies, which is why the two decisions have to be reported
separately.}
\label{fig:decision}
\end{figure*}
"""

    tex = rf"""%% PRL 投稿稿（build 由 tools/_build_prl_tex.py 生成，请勿手改）
\documentclass[a4paper]{{cas-dc}}
\usepackage[numbers]{{natbib}}
\usepackage{{amsmath,amssymb}}
\usepackage{{booktabs}}
\usepackage{{graphicx}}
\usepackage{{hyperref}}

\begin{{document}}
\shorttitle{{Allocation, not selection}}
\shortauthors{{H. Wan}}

\title[mode=title]{{Allocation, not selection: comparability in parameter-efficient multimodal adaptation}}

\author[1]{{Hongrui Wan}}
\cormark[1]
\ead{{hw4c24@soton.ac.uk}}
\affiliation[1]{{organization={{University of Southampton}}, city={{Southampton}}, postcode={{SO17 1BJ}}, country={{United Kingdom}}}}
\cortext[1]{{Corresponding author. Institutional email: hw4c24@soton.ac.uk}}

\begin{{abstract}}
{clean_abstract(abstract)}
\end{{abstract}}

\begin{{highlights}}
{hl}
\end{{highlights}}

\begin{{keywords}}
parameter-efficient fine-tuning \sep multimodal models \sep vision-language models \sep comparability \sep reporting standards
\end{{keywords}}

\maketitle

{figure}

{body}

{bibitems()}

\end{{document}}
"""
    TEX.write_text(tex, encoding="utf-8", newline="")
    for _ in range(3):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", TEX.name], cwd=OUT, capture_output=True)
    pdf = TEX.with_suffix(".pdf")
    if not pdf.exists():
        log = TEX.with_suffix(".log")
        errs = [l for l in log.read_text(encoding="utf-8", errors="ignore").splitlines() if l.startswith("!")] \
            if log.exists() else []
        print("❌ 编译失败：", errs[:3] if errs else "无日志")
        return 1
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True).stdout.decode("utf-8", "ignore")
    pages = re.search(r"Pages:\s+(\d+)", info)
    errs = [l for l in TEX.with_suffix(".log").read_text(encoding="utf-8", errors="ignore").splitlines()
            if l.startswith("!")]
    print(f"✅ 编译成功：{TEX.name}")
    print(f"  页数: {pages.group(1) if pages else '?'}（PRL 上限 7 页）")
    print(f"  error: {len(errs)}")
    print(f"  摘要: {len(abstract.split())} 词（上限 250）")
    print(f"  highlights: {len(HIGHLIGHTS)} 条，最长 {max(len(h) for h in HIGHLIGHTS)} 字符（上限 85）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
