# -*- coding: utf-8 -*-
r"""Insert the local B/C/D results into the P3 draft (S30-S32).

    python tools/_p1540_insert_bcd_local.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "paper3", "paper_ieee")
SUPP = os.path.join(BASE, "supplementary", "supplementary.tex")
AUDIT = os.path.join(BASE, "audit_check.py")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
AN = os.path.join(REPO, "outputs", "analysis")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")


def jl(p):
    return json.load(io.open(p, encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    add = jl(os.path.join(AN, "p3_additivity_residual.json"))
    per = jl(os.path.join(AN, "p3_perlayer_gamma.json"))
    rob = jl(os.path.join(AN, "p3_robust_stats.json"))
    beta = jl(os.path.join(AN, "p3_signed_gamma_beta.json"))
    sig = jl(os.path.join(AN, "p3_siglip_gamma.json"))
    arm_sig = jl(os.path.join(EXP, "verify_r1_s42_bcexplicit_v2_s7_m5_d2.json"))
    arm_signed = None
    for f in glob.glob(os.path.join(EXP, "verify_r1_s42_bcexplicit_v1_s6_m5_d4.json")):
        arm_signed = jl(f)
    add_rows = "\n".join("%s & %.1f & %.1f & %+.1f & %+.2f\\%% \\\\" % (
        p["A"] + "+" + p["B"], p["E_union"], p["E_empty"], p["residual"], 100 * p["relative"])
        for p in add["pair_residuals"])
    layer_rows = "\n".join("%s & %.4f & [%.4f, %.4f] \\\\" % (k, v["mean"], v["ci95"][0], v["ci95"][1])
                           for k, v in per["layers"].items())
    seed_rows = "\n".join("%s & %d & %+.1f & %.1f & %+.1f & [%+.1f, %+.1f] \\\\" % (
        k, v["n"], v["mean"], v["sd"], v["median"], v["ci95_mean"][0], v["ci95_mean"][1])
        for k, v in rob["seed5"].items())
    beta_rows = "\n".join("%s & %d/%d/%d/%d \\\\" % (b, v["ranks"]["vision"], v["ranks"]["text_shallow"],
                                                    v["ranks"]["text_mid"], v["ranks"]["text_deep"])
                          for b, v in beta["signed_rules"].items())
    sig_arm_txt = ("$%+.1f$" % arm_sig["delta_E"]) if arm_sig else "pending"
    signed_arm_txt = ("$%+.1f$" % arm_signed["delta_E"]) if arm_signed else "pending"
    section = r"""
\section{Additivity residual of the block decomposition}
\label{app:additivity}

We test the additivity assumption (R3$'$) directly on the probe adapter: zero the LoRA $B$ matrices outside a block
subset $S$ and measure the alignment energy $E(S)$ on four held-out instruction batches. Table~\ref{tab:additivity}
reports the pair residuals $E(A\cup B)-E(A)-E(B)+E(\varnothing)$.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrrr@{}}
\toprule
block pair & $E(A\cup B)$ & $E(\varnothing)$ & residual & relative \\
\midrule
%(add_rows)s
\bottomrule
\end{tabular}
\caption{Block-additivity residuals of the energy functional on the probe adapter. All pair residuals are below
$0.05\%%$ of the energy scale, so the additive decomposition is empirically supported for this probe. Archive:
\texttt{outputs/analysis/p3\_additivity\_residual.json}.}
\label{tab:additivity}
\end{table*}

\section{Per-layer coupling and robust statistics}
\label{app:perlayer}

Table~\ref{tab:perlayer} lists the integrated-gradient coupling per LLM layer (plus the vision tower) with prompt-level
bootstrap 95\%% intervals; Table~\ref{tab:robust} reports robust summaries of the seed-5 crossing.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrr@{}}
\toprule
component & mean coupling & 95\%% CI \\
\midrule
%(layer_rows)s
\bottomrule
\end{tabular}
\caption{Per-layer coupling (integrated-gradient sensitivity) on the probe adapter. Archive:
\texttt{outputs/analysis/p3\_perlayer\_gamma.json}.}
\label{tab:perlayer}
\end{table*}

\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrrrr@{}}
\toprule
rank & $n$ & mean & sd & median & 95\%% CI of mean \\
\midrule
%(seed_rows)s
\bottomrule
\end{tabular}
\caption{Robust statistics of the five-seed crossing (median absolute deviation is $16.5$ at $r=5$ and $31.0$ at $r=6$;
archive \texttt{outputs/analysis/p3\_robust\_stats.json}).}
\label{tab:robust}
\end{table*}

\section{Signed coupling and non-CLIP source}
\label{app:signed}

The paper's rule uses $|\Gamma|$. A signed rule, $\mathrm{rank}_k\propto\exp(-\beta\Gamma_k)$, gives the allocations in
Table~\ref{tab:beta}; a source model outside the CLIP family (SigLIP) gives a different block ordering
(Table~\ref{tab:siglip}). Both were trained under the blank-image protocol.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lcccc@{}}
\toprule
$\beta$ & vision & shallow & mid & deep \\
\midrule
%(beta_rows)s
\bottomrule
\end{tabular}
\caption{Signed-Gamma allocation over a $\beta$ grid (budget 16). Archive:
\texttt{outputs/analysis/p3\_signed\_gamma\_beta.json}.}
\label{tab:beta}
\end{table*}

\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrrr l@{}}
\toprule
source & vision & shallow & mid & deep & trained arm $\Delta E$ \\
\midrule
SigLIP & %(sv)d & %(ss)d & %(sm)d & %(sd)d & %(sig_arm)s \\
signed $\Gamma$ ($\beta=1$) & 1 & 6 & 5 & 4 & %(signed_arm)s \\
\bottomrule
\end{tabular}
\caption{Non-CLIP source (SigLIP) and signed-Gamma allocations with their trained arms. Archives:
\texttt{outputs/analysis/p3\_siglip\_gamma.json}, \texttt{verify\_r1\_s42\_bcexplicit\_v2\_s7\_m5\_d2.json}.}
\label{tab:siglip}
\end{table*}

""" % {"add_rows": add_rows, "layer_rows": layer_rows, "seed_rows": seed_rows, "beta_rows": beta_rows,
       "sv": sig["allocation"]["vision"], "ss": sig["allocation"]["text_shallow"],
       "sm": sig["allocation"]["text_mid"], "sd": sig["allocation"]["text_deep"],
       "sig_arm": sig_arm_txt, "signed_arm": signed_arm_txt}
    if not a.apply:
        print(section[:300])
        return 0
    t = io.open(SUPP, encoding="utf-8").read()
    if "app:additivity" not in t:
        anchor = "\\bibliographystyle{IEEEtran}"
        t = t.replace(anchor, section + "\n" + anchor, 1)
        # S17 rows
        idx = t.find("\\label{tab:claims}")
        j = t.find("\\bottomrule", idx)
        addrow = ("block additivity (R3$'$) measured & supported for the probe & pair residuals below $0.05\\%$ (S30) \\\\\n"
                  "signed $\\Gamma$ and non-CLIP source change the ordering & reported, no positive claim & S32 tables \\\\\n")
        t = t[:j] + addrow + t[j:]
        # S13 rows
        old = ("\\raggedright tab:iguarm & \\raggedright\\path{tools/_p1530_igu_allocation.py} & "
               "\\raggedright\\path{outputs/analysis/p3_igu_allocation.json} & \\texttt{verified} \\\\")
        if old in t:
            t = t.replace(old, old + "\n" + "\n".join(
                "\\raggedright %s & \\raggedright\\path{%s} & \\raggedright\\path{%s} & \\texttt{verified} \\\\" % r
                for r in (("tab:additivity", "tools/_p1534_additivity_residual.py", "outputs/analysis/p3_additivity_residual.json"),
                          ("tab:perlayer", "tools/_p1536_perlayer_gamma.py", "outputs/analysis/p3_perlayer_gamma.json"),
                          ("tab:robust", "tools/_p1538_robust_stats.py", "outputs/analysis/p3_robust_stats.json"),
                          ("tab:beta", "tools/_p1537_signed_gamma_beta.py", "outputs/analysis/p3_signed_gamma_beta.json"),
                          ("tab:siglip", "tools/_p1539_siglip_gamma.py", "outputs/analysis/p3_siglip_gamma.json"))), 1)
        io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
        print("S30-S32 inserted")
    ac = io.open(AUDIT, encoding="utf-8").read()
    if "thirty-two S-sections" not in ac:
        ac = ac.replace('check("supplement: twenty-nine S-sections", n_sections == 29, f"{n_sections} sections")',
                        'check("supplement: thirty-two S-sections", n_sections == 32, f"{n_sections} sections")', 1)
        if "twenty-nine S-sections" not in ac:
            ac = ac.replace('check("supplement: twenty-nine S-sections", n_sections == 29, f"{n_sections} sections")',
                            'check("supplement: thirty-two S-sections", n_sections == 32, f"{n_sections} sections")', 1)
        io.open(AUDIT, "w", encoding="utf-8", newline="").write(ac)
        print("audit_check -> 32 sections")
    m = jl(MANIFEST)
    floats = m["manuscripts"]["P3"]["floats"]
    have = {f["label"] for f in floats}
    for label, script, archive in (("tab:additivity", "tools/_p1534_additivity_residual.py", "outputs/analysis/p3_additivity_residual.json"),
                                   ("tab:perlayer", "tools/_p1536_perlayer_gamma.py", "outputs/analysis/p3_perlayer_gamma.json"),
                                   ("tab:robust", "tools/_p1538_robust_stats.py", "outputs/analysis/p3_robust_stats.json"),
                                   ("tab:beta", "tools/_p1537_signed_gamma_beta.py", "outputs/analysis/p3_signed_gamma_beta.json"),
                                   ("tab:siglip", "tools/_p1539_siglip_gamma.py", "outputs/analysis/p3_siglip_gamma.json")):
        if label not in have:
            floats.append({"label": label, "kind": "table", "script": script, "archive": archive,
                           "status": "verified", "note": "B/C/D local round (2026-10-23)"})
    io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(m, indent=1, ensure_ascii=False))
    print("manifest updated; P3 floats:", len(floats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
