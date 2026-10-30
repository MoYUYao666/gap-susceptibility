# -*- coding: utf-8 -*-
r"""把 Paper A 从 Springer `sn-jnl` 转成 Elsevier `elsarticle`（目标刊 Neurocomputing）。

## 依据

模板范例：`备选/06_归档稿件/paper_ap3/main.tex`（**已用于 Neurocomputing 的 elsarticle 稿件**，导言区与前置块照它做，
不凭记忆）。`elsarticle.cls` 与 `els-cas-templates` 本地均在
`D:\texlive\2025\texmf-dist\tex\latex\`。

## 转换内容

| 项 | sn-jnl（原） | elsarticle（新） |
|---|---|---|
| 文档类 | `sn-mathphys-num` | `review,authoryear` |
| 前置块 | `\title[...]{}` / `\author*[]{}` / `\affil*[]{}` | `\begin{frontmatter}` + `\author[]{}` + `\affiliation[]{}` + `\cortext` |
| 摘要 | `\abstract{...}` | `\begin{abstract}...\end{abstract}` |
| 关键词 | `\keywords{...}` | `\begin{keyword}...\end{keyword}` |
| 补充材料 | `\bmhead{}` | `\appendix` |
| 定理环境 | sn-jnl 自定义 `\theoremstyle` | 标准 `amsthm` 的 `\newtheorem` |

**正文 8 个 `\input` 文件不改**（正文是模板无关的），只换外壳。
引用沿用 `\cite{}`（`authoryear` 下渲染为作者-年份，与 sn-mathphys-num 的数字制不同，
但正文里的 `\cite` 无需改动）。

    python tools\_pa_to_elsarticle.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "paper合" / "main_springer.tex"
DST = REPO / "paper合" / "main_nc.tex"

TITLE = ("Protect, Don't Perturb: From Empirical Regularities to a Dynamical Theory of Cross-Modal "
         "Alignment under PEFT")

HEADER = r"""%% Paper A — Elsevier elsarticle (target: Neurocomputing)
%% 由 tools/_pa_to_elsarticle.py 从 main_springer.tex 转换；正文 sections/*.tex 未改动。
\documentclass[review,authoryear]{elsarticle}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{amsthm}
\newtheorem{theorem}{Theorem}[section]
\newtheorem{lemma}{Lemma}[section]
\newtheorem{corollary}{Corollary}[section]
\newtheorem{definition}{Definition}[section]
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{remark}{Remark}[section]
\newtheorem{assumption}{Assumption}[section]
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{longtable}
\usepackage{float}
\usepackage{placeins}
\usepackage[hidelinks]{hyperref}

\journal{Neurocomputing}

\begin{document}
\sloppy

\begin{frontmatter}

\title{%TITLE%}

\author[1]{Hongrui Wan\corref{cor1}}
\affiliation[1]{organization={University of Southampton},
  addressline={University Road},
  city={Southampton},
  postcode={SO17 1BJ},
  country={United Kingdom}}
\cortext[cor1]{Corresponding author.}
\ead{hw4c24@soton.ac.uk}

\begin{abstract}
%ABSTRACT%
\end{abstract}

\begin{keyword}
Modality gap \sep Parameter-efficient fine-tuning \sep Gap susceptibility \sep Cross-modal alignment \sep
Gradient flow \sep Distribution Gap
\end{keyword}

\end{frontmatter}

"""

FOOTER = r"""
\appendix
\input{sections/supplement}

\section*{Data availability}
Data will be made available on request.

\section*{Declaration of competing interest}
The author declares no competing financial interests or personal relationships that could have appeared
to influence the work reported in this paper.

\bibliographystyle{elsarticle-harv}
\bibliography{references}

\end{document}
"""


def extract(tex: str) -> tuple[str, str, str]:
    """返回 (abstract 正文, 正文块, 尾部块)。"""
    m = re.search(r"\\abstract\{([\s\S]*?)\n\}", tex)
    abstract = m.group(1).strip() if m else ""
    body_start = tex.find("\\maketitle")
    body_end = tex.find("\\backmatter")
    if body_start < 0 or body_end < 0:
        raise SystemExit("❌ 未找到 \\maketitle 或 \\backmatter")
    body = tex[body_start + len("\\maketitle"):body_end].strip()
    return abstract, body, tex[body_end:]


def main() -> int:
    apply = "--apply" in sys.argv
    tex = io.open(SRC, encoding="utf-8").read()
    abstract, body, _ = extract(tex)
    # 摘要里的段落空行保留
    abstract = re.sub(r"\n{3,}", "\n\n", abstract)

    out = HEADER.replace("%TITLE%", TITLE).replace("%ABSTRACT%", abstract)
    out += body + "\n" + FOOTER

    # 正文里若引用了 sn-jnl 专有命令，提示（本稿未使用，但留断言）
    for bad in ("\\bmhead", "\\keywords{", "\\affil", "\\sur{", "\\fnm{"):
        if bad in out:
            print(f"  ⚠ 输出仍含 Springer 专有命令：{bad}")

    n_in = len(re.findall(r"\\input\{", out))
    print(f"  摘要 {len(abstract.split())} 词（LaTeX 粗算）｜ \\input 数 {n_in}（应为 8）")
    print(f"  输出：{DST.relative_to(REPO)}")
    if apply:
        io.open(DST, "w", encoding="utf-8", newline="").write(out)
        t = io.open(DST, encoding="utf-8").read()
        assert "elsarticle" in t and "frontmatter" in t
        assert "\\bmhead" not in t and "\\keywords{" not in t
        print("  ✅ 已写出并断言通过")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
