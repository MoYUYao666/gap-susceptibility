# -*- coding: utf-8 -*-
r"""Tier A fixes: clear the Paper A dead-label warnings, declare the A23 small-caps substitution, and add a data
statement link to the commentary.

    python tools/_p1407_tier_a_fixes.py [--apply]
"""
from __future__ import annotations

import argparse
import io

SUPP = "paper合/sections/supplement.tex"
VAL = "paper合/sections/validation.tex"
EMP = "paper合/sections/empirical.tex"
THE = "paper合/sections/theory.tex"
A23 = "paper_a2/main_ieee.tex"
COMM = "paper_review_prl/MANUSCRIPT.md"


def patch(path: str, reps: list) -> int:
    t = io.open(path, encoding="utf-8").read()
    n = 0
    for old, new in reps:
        if old not in t:
            print("   MISSING in", path, ":", old[:70])
            continue
        t = t.replace(old, new, 1)
        n += 1
    io.open(path, "w", encoding="utf-8", newline="").write(t)
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0

    # --- Paper A: explicit references for the middle elements of figure ranges and for the labels never cited
    n = patch(SUPP, [
        ("Figures~\\ref{fig:weight_svd}--\\ref{fig:vision_untouched} give the weight-level evidence for the Visual Fragility Interpretation,",
         "Figures~\\ref{fig:weight_svd}--\\ref{fig:vision_untouched} (including the trainable-parameter budget, Figure~\\ref{fig:budget}) give the weight-level evidence for the Visual Fragility Interpretation,"),
        ("Figures~\\ref{fig:noise_sensitivity}--\\ref{fig:ratio} the parameter-noise probe together with the control",
         "Figures~\\ref{fig:noise_sensitivity}--\\ref{fig:ratio} (including the $\\sigma{=}0$ control, Figure~\\ref{fig:sigma0_control}) the parameter-noise probe together with the control"),
        ("move it either way and the sign is informative.\n",
         "move it either way and the sign is informative. Table~\\ref{tab:llava} reports the four arms.\n"),
    ])
    print("  supplement refs added:", n)

    n = patch(VAL, [
        ("and full fine-tuning---with three seeds each.",
         "and full fine-tuning---with three seeds each, reported in Table~\\ref{tab:beta_pilot}."),
        ("Across PEFT configurations the ODE achieves mean",
         "Figure~\\ref{fig:ode} shows representative trajectories; across PEFT configurations the ODE achieves mean"),
        ("not reduce the perturbation, it removes the visual term from it.",
         "not reduce the perturbation, it removes the visual term from it. Table~\\ref{tab:grad_side} lists the measured norms."),
    ])
    print("  validation refs added:", n)

    n = patch(EMP, [
        ("beyond first-order centroid shift.",
         "beyond first-order centroid shift (Table~\\ref{tab:corr})."),
    ])
    print("  empirical refs added:", n)

    n = patch(THE, [
        ("$DG^*$ is differentiable in $\\theta$",
         "$DG^*$ (Definition~\\ref{def:dgstar}) is differentiable in $\\theta$"),
        ("$\\Gamma_m$ decomposes into two orthogonal factors",
         "$\\Gamma_m$ (Definition~\\ref{def:gamma}) decomposes into two orthogonal factors"),
        ("During training, $\\Gamma_m$ and $\\|g_m\\|$ fluctuate across steps.",
         "Equation~(\\ref{eq:dynamics}) is exact at each step; during training, $\\Gamma_m$ and $\\|g_m\\|$ fluctuate across steps."),
        ("The ODE~(\\ref{eq:ode_main}) admits an explicit solution:",
         "The ODE~(\\ref{eq:ode_main}) admits the explicit solution~(\\ref{eq:solution}):"),
    ])
    print("  theory refs added:", n)

    # --- A23: declare the small-caps-italic substitution once, so the log is clean
    n = patch(A23, [
        ("\\usepackage{url}\n\\usepackage{lineno}\n\\usepackage{setspace}",
         "\\usepackage{url}\n\\usepackage{lineno}\n\\usepackage{setspace}\n"
         "% IEEEtran's Times setup requests OT1/ptm/m/scit in a few inline contexts; declare the\n"
         "% substitution once so each occurrence does not emit a LaTeX font warning. Glyphs unchanged.\n"
         "\\DeclareFontShape{OT1}{ptm}{m}{scit}{<->ssub * ptm/m/it}{}"),
    ])
    print("  A23 font declaration added:", n)

    # --- Commentary: data statement with repository and DOI
    n = patch(COMM, [
        ("**Data availability.** No data was used for the research described in the article.",
         "**Data availability.** No new data were generated for this article. The analysis archive and the scripts "
         "behind the six instances are openly available at https://github.com/MoYUYao666/gap-susceptibility "
         "(archived under DOI 10.5281/zenodo.23341223)."),
    ])
    print("  commentary data statement updated:", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
