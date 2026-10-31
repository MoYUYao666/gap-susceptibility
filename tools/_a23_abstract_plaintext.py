"""Produce a plain-text (no TeX, no HTML) version of the A23 abstract for the
PaperCept abstract box, which rejects TeX/HTML commands and caps at 2000 chars.

Every substitution is explicit so the result is auditable. Superscripts become
caret notation (10^-4) because a copied PDF renders them ambiguously as 10-4.
Kept ASCII-only on purpose: it survives any web-form encoding.
"""
import re

SRC = r"D:\Realdesktop\Wan\Important\New\paper_a2\main_ieee.tex"
OUT = r"D:\Realdesktop\Wan\Important\New\SUBMISSION\A23_JOE\abstract_plaintext.txt"

src = open(SRC, encoding="utf-8").read()
abs_tex = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", src, re.S).group(1).strip()

SUBS = [
    # LaTeX thousands separator: 2{,}617 renders as 2,617
    (r"{,}", ","),
    (r"$10^{-4}$", "10^-4"),
    (r"$\le0.016$", "<= 0.016"),
    (r"$\lambda$", "lambda"),
    (r"$\Delta\tau$", "delta-tau"),
    (r"$\tau$", "tau"),
    (r"$3.6\times$", "3.6x"),
    (r"$3.8\times$", "3.8x"),
    (r"$1.8\times$", "1.8x"),
    (r"$1.1\times$", "1.1x"),
    (r"$-2.8\%$", "-2.8%"),
    (r"$-8.1\%$", "-8.1%"),
    (r"$-15\%$", "-15%"),
    (r"$-62\%$", "-62%"),
    (r"$27.65\%$", "27.65%"),
    (r"$0.26\%$", "0.26%"),
    (r"$+0.061$", "+0.061"),
    (r"$2\times2$", "2x2"),
    (r"$3$", "3"),
    (r"$6$", "6"),
    (r"\emph{five}", "five"),
    (r"``", '"'),
    (r"''", '"'),
    (r"\%", "%"),
    (r"--", "-"),
    (r"~", " "),
]

txt = abs_tex
for pat, rep in SUBS:
    txt = txt.replace(pat, rep)

leftover = re.findall(r"\$[^$]*\$|\\[a-zA-Z]+", txt)
txt = re.sub(r"\s+", " ", txt).strip()

print(f"原 TeX 摘要长度 : {len(abs_tex)} 字符")
print(f"纯文本长度      : {len(txt)} 字符   (上限 2000)")
print(f"余量            : {2000 - len(txt)} 字符")
print(f"残留 TeX 构造   : {leftover if leftover else '无'}")
print(f"非 ASCII 字符   : {sorted({c for c in txt if ord(c) > 127}) or '无'}")
print()
print("=" * 78)
print(txt)
print("=" * 78)

open(OUT, "w", encoding="utf-8").write(txt + "\n")
print(f"\n已写出: {OUT}")
