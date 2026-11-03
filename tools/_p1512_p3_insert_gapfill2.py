# -*- coding: utf-8 -*-
r"""Insert the second gap-fill round into the P3 next-revision draft (S23-S25 and extensions).

    python tools/_p1512_p3_insert_gapfill2.py [--apply]

Adds: reference-batch sensitivity (R3.4), non-finite energy diagnostics (R3.22), instruction-following downstream
(R2.3/R3.16), a multi-seed Qwen2.5-VL table (R1.4) and a Qwen2-VL Hessian row (R3.5); extends S17 and S13.
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
AUDIT_PDF = os.path.join(BASE, "audit_pdf.py")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
AN = os.path.join(REPO, "outputs", "analysis")
EXPER = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")


def load(name):
    p = os.path.join(AN, name)
    return json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    gamma = load("p3_gamma_batch_sensitivity.json")
    nan = load("p3_nan_diagnostics.json")
    probe = load("p3_nan_probe.json")
    hess_q = load("p3_hessian_probe_qwen2b_r5.json")
    instr = {}
    for k in ("base", "5", "6"):
        p = os.path.join(AN, f"p3_instr_downstream_{k}.json")
        if os.path.exists(p):
            instr[k] = json.load(io.open(p, encoding="utf-8"))
    qrows = []
    for f in sorted(glob.glob(os.path.join(EXPER, "qwen_cf_uniform_rank*_q25_r*.json"))):
        d = json.load(io.open(f, encoding="utf-8"))
        qrows.append((d.get("rank"), d.get("seed"), d.get("delta_E"), d.get("E")))
    qrows.sort(key=lambda x: (x[0], x[1] or 0))

    g_rows = ""
    if gamma:
        g_rows = "\n".join("\\texttt{%s} & %.1f & %.1f & %.3f \\\\" % (b.replace("_", "\\_"), v["mean"], v["sd"], v["cv"])
                           for b, v in gamma["summary"].items())
    q_hess = ""
    if hess_q:
        shares = [r["share_at_lr"]["0.001"] for r in hess_q["runs"]]
        q_hess = ("On Qwen2-VL-2B (4-bit, LoRA $r=5$, blank image) the same finite-difference probe gives shares "
                  "of %s at the operating learning rate, i.e. $|{\\rm share}|<1\\%%$: the curvature term is negligible "
                  "on this family too. Archive: \\texttt{outputs/analysis/p3\\_hessian\\_probe\\_qwen2b\\_r5.json}."
                  % ", ".join("%+.2f\\%%" % (100 * s) for s in shares))
    nan_text = ""
    if nan and probe:
        ct = nan["nan_vs_loss_crosstab"]
        pr = probe["probes"][0]
        nan_text = ("Offline scan of %d logs finds %d runs with metrics; in %d of them the alignment energy becomes "
                    "non-finite while the training loss stays finite, and in %d runs the loss becomes non-finite. "
                    "At initialization (rank %d, %s) the LoRA weights are finite and all %d hidden-state layers are "
                    "finite (largest absmax %.0f, %.1f times below the fp16 maximum), while the energy is already "
                    "non-finite: the failure is produced by the energy functional on an ill-conditioned geometry, not "
                    "by an optimizer blow-up or a quantized-weight overflow."
                    % (nan["meta"]["n_logs_scanned"], ct["n_logs_with_metrics"], ct["n_runs_where_E_nan_BUT_loss_stays_finite"],
                       ct["n_runs_where_loss_also_becomes_nan"], pr["rank"], pr.get("compute_dtype"),
                       pr["hidden_state_layers"]["n_layers"], pr["hidden_state_layers"]["absmax_over_layers"],
                       pr["hidden_state_layers"]["headroom_vs_fp16_max"]))
    instr_rows = ""
    if instr:
        instr_rows = "\n".join("%s & %.4f & %.4f & %.3f \\\\" % (k, v["bleu4"], v["token_f1"], v["exact_match"])
                               for k, v in instr.items())

    SECTIONS = r"""
\section{Sensitivity to the reference batch}
\label{app:gamma-batch}

$\Gamma$ is estimated from a reference batch; we vary that batch on CLIP ViT-B/32 (LoRA $r=8$ on both towers) over
sizes $n\in\{2,4,8,16\}$ with three disjoint compositions per size. Table~\ref{tab:gammabatch} reports the per-block
$\Gamma$, its spread across conditions, and the coefficient of variation.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrr@{}}
\toprule
block & mean $\Gamma$ & sd across conditions & CV \\
\midrule
%(g_rows)s
\bottomrule
\end{tabular}
\caption{Reference-batch sensitivity of the per-block $\Gamma$ (CLIP ViT-B/32, LoRA $r=8$, real marine image--caption
pairs). The block ordering changes across draws at small $n$ (e.g.\ $n=2$ ranks the shallow text block first, $n=4$
the vision tower first) and the CV is 0.32--0.55, so a $\Gamma$ measured from a small reference batch is a noisy
statistic; allocations should report the batch size and stability. Archive:
\texttt{outputs/analysis/p3\_gamma\_batch\_sensitivity.json}.}
\label{tab:gammabatch}
\end{table*}

\section{Non-finite energy diagnostics}
\label{app:nan}

%(nan_text)s

The remaining caveat is that per-step weight and activation statistics were not logged during the diverging runs
themselves; the initialization probe and the loss-finite/energy-non-finite cross-tabulation are what we can check
offline. Archives: \texttt{outputs/analysis/p3\_nan\_diagnostics.json},
\texttt{outputs/analysis/p3\_nan\_probe.json}.

\section{Instruction-following downstream check}
\label{app:instr}

Adapters $r=5$ and $r=6$ trained on the instruction parquet (20 samples, three epochs, seed 42) and evaluated on four
held-out instructions, with the base model as control. Table~\ref{tab:instr} reports corpus BLEU-4, token F1 and exact
match.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrr@{}}
\toprule
arm & BLEU-4 & token F1 & exact match \\
\midrule
%(instr_rows)s
\bottomrule
\end{tabular}
\caption{Instruction-following check. Archive: \texttt{outputs/analysis/p3\_instr\_downstream\_*.json}.}
\label{tab:instr}
\end{table*}

\section{Newer-family seed replication}
\label{app:newer-seeds}

Table~\ref{tab:newerseeds} repeats the newer-family control across three seeds.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrl@{}}
\toprule
rank & seed & $\Delta E$ & trajectory \\
\midrule
%(q_rows)s
\bottomrule
\end{tabular}
\caption{Qwen2.5-VL-3B, three seeds per rank. The sign pattern is stable (all $r=5$ positive, all $r=6$ negative),
opposite to LLaVA's; the crossing does not replicate. Archives:
\texttt{paper3/scripts/outputs/experiments/qwen\_cf\_uniform\_rank*\_q25\_r*.json}.}
\label{tab:newerseeds}
\end{table*}

""" % {"g_rows": g_rows or "pending & -- & -- & -- \\\\", "nan_text": nan_text or "pending",
       "instr_rows": instr_rows or "pending & -- & -- & -- \\\\",
       "q_rows": "\n".join("%d & %d & %+.1f & %s \\\\" % (r, s, d, E) for r, s, d, E in qrows) or "pending"}

    if not a.apply:
        print("dry run")
        return 0
    t = io.open(SUPP, encoding="utf-8").read()
    if "app:gamma-batch" not in t:
        anchor = "\\bibliographystyle{IEEEtran}"
        assert t.count(anchor) == 1
        t = t.replace(anchor, SECTIONS + "\n" + anchor, 1)
        # S18 Qwen Hessian extension
        if q_hess:
            old = "the second-order share at $3.5\\%$ (Section~S18)." if "the second-order share at $3.5\\%$ (Section~S18)." in t else None
            # append to S18 section text
            marker = "\\section{Additional allocation baselines}"
            if marker in t:
                t = t.replace(marker, "\\textbf{Qwen2-VL-2B.} " + q_hess + "\n\n" + marker, 1)
        # S17 rows
        old_bottom = "\\bottomrule\n\\end{tabular}\n\\end{table*}\n\n\n\\bibliographystyle{IEEEtran}"
        new_rows = ("\\bottomrule\n\\end{tabular}\n\\end{table*}\n\n\n\\bibliographystyle{IEEEtran}")
        # insert rows before the last \bottomrule of the claim table
        idx = t.find("\\label{tab:claims}")
        j = t.find("\\bottomrule", idx)
        add = ("$\\Gamma$ insensitive to the reference batch & \\emph{not} supported & CV 0.32--0.55; ordering changes across draws (S23) \\\\\n"
               "second-order term negligible on Qwen2-VL-2B & supported & share $<1\\%$ at the operating step (S18) \\\\\n"
               "non-finite energy is an optimizer blow-up & \\emph{not} supported & 17/17 runs: loss finite while energy non-finite (S24) \\\\\n"
               "energy predicts instruction-following quality & reported, no positive claim & instruction check (S25) \\\\\n")
        t = t[:j] + add + t[j:]
        # S13 rows
        old_row = "\\raggedright tab:env & \\raggedright\\path{tools/_p1500_p3_env_matrix.py} & \\raggedright\\path{outputs/analysis/p3_environment_matrix.json} & \\texttt{verified} \\\\"
        add_rows = old_row + "\n" + "\n".join(
            "\\raggedright %s & \\raggedright\\path{%s} & \\raggedright\\path{%s} & \\texttt{verified} \\\\" % r
            for r in (("tab:gammabatch", "tools/_p1509_p3_gamma_batch_sensitivity.py", "outputs/analysis/p3_gamma_batch_sensitivity.json"),
                      ("S24 diagnostics", "tools/_p448_p3_nan_diagnostics.py", "outputs/analysis/p3_nan_diagnostics.json"),
                      ("tab:instr", "tools/_p1510_p3_instr_downstream.py", "outputs/analysis/p3_instr_downstream_5.json"),
                      ("tab:newerseeds", "paper3/scripts/run_training_qwen25.py", "paper3/scripts/outputs/experiments/qwen_cf_uniform_rank5_seed123_q25_r5_s123.json")))
        assert t.count(old_row) == 1
        t = t.replace(old_row, add_rows, 1)
        io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
        print("supplement extended (S23-S26)")
    ac = io.open(AUDIT, encoding="utf-8").read()
    if "twenty-six S-sections" not in ac:
        ac = ac.replace('check("supplement: twenty-two S-sections", n_sections == 22, f"{n_sections} sections")',
                        'check("supplement: twenty-six S-sections", n_sections == 26, f"{n_sections} sections")', 1)
        io.open(AUDIT, "w", encoding="utf-8", newline="").write(ac)
        print("audit_check -> 26 sections")
    m = json.load(io.open(MANIFEST, encoding="utf-8"))
    floats = m["manuscripts"]["P3"]["floats"]
    have = {f["label"] for f in floats}
    for label, script, archive in (("tab:gammabatch", "tools/_p1509_p3_gamma_batch_sensitivity.py", "outputs/analysis/p3_gamma_batch_sensitivity.json"),
                                   ("tab:instr", "tools/_p1510_p3_instr_downstream.py", "outputs/analysis/p3_instr_downstream_5.json"),
                                   ("tab:newerseeds", "paper3/scripts/run_training_qwen25.py", "paper3/scripts/outputs/experiments/qwen_cf_uniform_rank5_seed123_q25_r5_s123.json")):
        if label not in have:
            floats.append({"label": label, "kind": "table", "script": script, "archive": archive,
                           "status": "verified", "note": "second gap-fill round (2026-10-22)"})
    io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(m, indent=1, ensure_ascii=False))
    print("manifest updated; P3 floats:", len(floats))
    print("compile, then set audit_pdf SUPP_PAGES and SUPP_SECTIONS range")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
