# -*- coding: utf-8 -*-
r"""Stop Table S3 (and the other supplement tables) squeezing their text.

Reported fault: "TABLE S3 文字有被压到". Table S3 is built as tabular{lcccc} inside a table*, so every
column takes its natural width: the two text columns collapse toward their longest word while the three
verdict columns stay wide, and the caption -- set to the table's width -- ends up wider than the rules
above it.

Changes:
* Table S3: fixed-width columns (p{}) sized to the class's 3.5 in text width, ragged-right so the short
  cells are not stretched by justification, headers shortened, caption shortened to one line.
* Tables S4 and S5: fixed-width columns, header "std" capitalised, "regime" -> "Regime".
* The supplement gets hypersetup{hidelinks}: it drew a coloured box around every citation and
  cross-reference, which is what makes the reference markers look crowded. The main text is fixed the
  same way already.
* All five tables set in the same 8 pt face.

NOTE ON BACKSLASHES: every LaTeX backslash is built from chr(92). Writing them as escape sequences in
string literals collapses them, and this repository has already lost document text that way twice.

    python tools/_p916_fix_supp_tables.py [--apply]
"""
from __future__ import annotations

import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.tex"
B = chr(92)

HYPER_OLD = B + "usepackage{hyperref}\n"
HYPER_NEW = (B + "usepackage{array}   % >{...} column modifiers, used by the fixed-width tables\n"
             + B + "usepackage{hyperref}\n"
             + B + "hypersetup{hidelinks}   % no coloured link boxes in the print version\n")

S3_OLD = (B + "begin{table*}[t]\n"
          + B + "centering\n"
          + B + "footnotesize\n"
          + B + "begin{tabular}{lcccc}\n"
          + B + "toprule\n"
          + "Method & Rank Allocation Basis & Phase Transition? & Cross-Arch? & Zero-Shot? " + B * 2 + "\n"
          + B + "midrule\n"
          + "HALoRA~" + B + "cite{halora2025} & Learned budget allocator & No & No & No " + B * 2 + "\n"
          + "AdaLoRA~" + B + "cite{adalora2023} & Sensitivity score (training) & No & No & No " + B * 2 + "\n"
          + "IGU-LoRA~" + B + "cite{igulora2025} & Integrated Gradients & No & No & No " + B * 2 + "\n"
          + "Hu et al.~" + B + "cite{hu2025loralimits} & Computational limits & Yes (efficiency) & No & No " + B * 2 + "\n"
          + B + "textbf{GFAP (Ours)} & " + B + "textbf{$" + B + "Gamma$ from axioms} & "
          + B + "textbf{Yes (alignment)} & " + B + "textbf{Yes} & " + B + "textbf{Yes} " + B * 2 + "\n"
          + B + "bottomrule\n"
          + B + "end{tabular}\n"
          + B + "caption{Only GFAP combines zero-shot prediction, phase transition detection,\n"
          + "and cross-architecture validation from first principles.}\n"
          + B + "label{tab:comparison}\n"
          + B + "end{table*}")

PCOL = B + "raggedright" + B + "arraybackslash"
CCOL = B + "centering" + B + "arraybackslash"
S3_NEW = (B + "begin{table*}[t]\n"
          + B + "centering\n"
          + B + "fontsize{8}{9.5}" + B + "selectfont\n"
          + B + "setlength{" + B + "tabcolsep}{4pt}\n"
          + B + "renewcommand{" + B + "arraystretch}{1.05}\n"
          + B + "begin{tabular}{@{}>{" + PCOL + "}p{1.6cm}\n"
          + "                    >{" + PCOL + "}p{3.7cm}\n"
          + "                    >{" + PCOL + "}p{1.9cm}\n"
          + "                    >{" + PCOL + "}p{1.7cm}\n"
          + "                    >{" + PCOL + "}p{1.7cm}@{}}\n"
          + B + "toprule\n"
          + "Method & Rank basis & Phase? & Cross-arch? & Zero-shot? " + B * 2 + "\n"
          + B + "midrule\n"
          + "HALoRA~" + B + "cite{halora2025} & Learned budget allocator & No & No & No " + B * 2 + "\n"
          + "AdaLoRA~" + B + "cite{adalora2023} & Sensitivity score, from training & No & No & No " + B * 2 + "\n"
          + "IGU-LoRA~" + B + "cite{igulora2025} & Integrated Gradients & No & No & No " + B * 2 + "\n"
          + "Hu et al.~" + B + "cite{hu2025loralimits} & Computational limits & Yes, efficiency & No & No " + B * 2 + "\n"
          + B + "textbf{GFAP (Ours)} & " + B + "textbf{$" + B + "Gamma$, from axioms} & "
          + B + "textbf{Yes, alignment} & " + B + "textbf{Yes} & " + B + "textbf{Yes} " + B * 2 + "\n"
          + B + "bottomrule\n"
          + B + "end{tabular}\n"
          + B + "caption{Only GFAP predicts the phase transition and validates across architectures\n"
          + "without training.}\n"
          + B + "label{tab:comparison}\n"
          + B + "end{table*}")

S4_OLD_SPEC = B + "begin{tabular}{@{}l" + "c" * 5 + "@{}}"
S4_NEW_SPEC = (B + "fontsize{8}{9.5}" + B + "selectfont\n"
               + B + "setlength{" + B + "tabcolsep}{3pt}\n"
               + B + "begin{tabular}{@{}>{" + PCOL + "}p{1.7cm}"
               + (">{" + CCOL + "}p{1.45cm}") * 5 + "@{}}")
S4_OLD_HEAD = "Samples & $r=4$ & $r=5$ & $r=6$ & $r=7$ & $r=16$ " + B * 2
S4_NEW_HEAD = (B + "textbf{Samples} & " + B + "textbf{$r=4$} & " + B + "textbf{$r=5$} & "
               + B + "textbf{$r=6$} & " + B + "textbf{$r=7$} & " + B + "textbf{$r=16$} " + B * 2)

S5_OLD = (B + "footnotesize\n"
          + B + "begin{tabular}{lccc}\n"
          + B + "toprule\n"
          + "$r$ & $" + B + "Delta E$ (mean) & std & regime " + B * 2)
S5_NEW = (B + "fontsize{8}{9.5}" + B + "selectfont\n"
          + B + "setlength{" + B + "tabcolsep}{5pt}\n"
          + B + "begin{tabular}{@{}>{" + CCOL + "}p{0.9cm}\n"
          + "                    >{" + CCOL + "}p{2.0cm}\n"
          + "                    >{" + CCOL + "}p{1.4cm}\n"
          + "                    >{" + PCOL + "}p{1.7cm}@{}}\n"
          + B + "toprule\n"
          + "$r$ & $" + B + "Delta E$ (mean) & Std & Regime " + B * 2)

# Tables S1 and S2 are already balanced (numeric columns, short first column); only their face changes,
# so that all five tables in the document match.
S12_FACE = []
for _lab, _spec in (("tab:gamma_detail", "lrrrr"), ("tab:gamma_rank", "lrrrrr")):
    S12_FACE.append((
        B + "footnotesize\n" + B + "begin{tabular}{" + _spec + "}",
        B + "fontsize{8}{9.5}" + B + "selectfont\n"
        + B + "setlength{" + B + "tabcolsep}{5pt}\n"
        + B + "begin{tabular}{@{}l" + "r" * (len(_spec) - 1) + "@{}}",
    ))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SUPP.read_text(encoding="utf-8")
    edits = [
        ("array package and hyperref hidelinks", HYPER_OLD, HYPER_NEW),
        ("Table S3 rebuilt with fixed-width columns", S3_OLD, S3_NEW),
        ("Table S4 fixed-width columns", S4_OLD_SPEC, S4_NEW_SPEC),
        ("Table S4 header in bold", S4_OLD_HEAD, S4_NEW_HEAD),
        ("Table S5 fixed-width columns", S5_OLD, S5_NEW),
        ("Table S1 face", S12_FACE[0][0], S12_FACE[0][1]),
        ("Table S2 face", S12_FACE[1][0], S12_FACE[1][1]),
    ]
    out = t
    for name, old, new in edits:
        c = out.count(old)
        if c == 0 and new in out:
            print(f"  {name}: already applied")
            continue
        assert c == 1, f"{name}: anchor found {c} times, expected 1"
        out = out.replace(old, new, 1)
        print(f"  {name}: applied")

    left = [ln for ln, line in enumerate(out.splitlines(), 1) if B + "footnotesize" in line]
    assert not left, f"a table still uses footnotesize at lines {left}"

    if not a.apply:
        print("  (dry run)")
        return 0
    SUPP.write_text(out, encoding="utf-8", newline="")
    check = SUPP.read_text(encoding="utf-8")
    assert B + "hypersetup{hidelinks}" in check, "hidelinks missing"
    assert "p{3.7cm}" in check, "Table S3 columns missing"
    assert check.count(B + "fontsize{8}{9.5}") == 5, \
        f"expected all five tables in the same face, found {check.count(B + 'fontsize{8}{9.5}')}"
    print("  written and verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
