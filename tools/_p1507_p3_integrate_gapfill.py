# -*- coding: utf-8 -*-
r"""Integrate the R1 gap-fill results into the P3 manuscript next-revision draft.

    python tools/_p1507_p3_integrate_gapfill.py [--apply]

Adds supplementary sections S18-S22 (curvature, allocation baselines, newer family, captioning downstream, seed/software
matrix), extends the S17 claim table and the S13 provenance table, and inserts short main-text sentences in experiments,
discussion and conclusion. The submitted version (PRLETTERS-D-26-02671) is not touched.
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "paper3", "paper_ieee")
SUPP = os.path.join(BASE, "supplementary", "supplementary.tex")
EXP = os.path.join(BASE, "sections", "experiments.tex")
DISC = os.path.join(BASE, "sections", "discussion.tex")
CONC = os.path.join(BASE, "sections", "conclusion.tex")
AUDIT = os.path.join(BASE, "audit_check.py")
AUDIT_PDF = os.path.join(BASE, "audit_pdf.py")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
AN = os.path.join(REPO, "outputs", "analysis")


def load(name):
    return json.load(io.open(os.path.join(AN, name), encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    gap = load("p3_gapfill_summary.json")
    hess = gap["curvature"]
    ntk = gap["ntk"]
    seeds = gap["seeds"]
    caps = gap["caption_metrics"]["arms"]
    qwen = gap["qwen25"]
    arms = gap["trained_arms"]

    def stat(rank):
        rows = hess[rank]["rows"]
        g2 = sum(r["g2"] for r in rows) / len(rows)
        gHg = sum(r["gHg"] for r in rows) / len(rows)
        share = hess[rank]["mean_share_at_lr"]
        sd = hess[rank]["sd_share_at_lr"]
        # vision fraction of |gHg|
        fr = []
        for r in rows:
            pg = r["per_group"] or {}
            v = abs(pg.get("vision", 0.0))
            l = abs(pg.get("llm", 0.0))
            fr.append(v / (v + l) if (v + l) else 0.0)
        return g2, gHg, share, sd, sum(fr) / len(fr)

    hess_rows = "\n".join(
        "{:d} & {:.1f} & {:.3g} & {:+.4f} & {:+.2f} & {:.0f}\\% \\\\".format(int(rank), *stat(rank)[:4], 100 * stat(rank)[4])
        for rank in ("5", "6"))
    ntk_rows = "\n".join(
        "%s & %.1f & %d & %d & %d \\\\" % (k, ntk["ntk_trace"][k], ntk["allocation_ntk"][k],
                                           ntk["allocation_gamma"][k], ntk["allocation_uniform"][k])
        for k in ntk["allocation_ntk"])
    arm_rows = "\n".join("%s & %+.1f & %s \\\\" % (x["label"], x["delta_E"], x["E"]) for x in arms)
    qwen_rows = "\n".join("%d & %+.1f & %s \\\\" % (r, d, E) for r, d, E in qwen)
    cap_rows = "\n".join("%s & %.4f & %.4f & %.4f \\\\" % (k, v["bleu4"], v["token_f1"], v["clip_sim_mean"])
                         for k, v in caps.items())
    seed_rows = "\n".join(
        "%s & %d & %+.1f & [%+.1f, %+.1f] \\\\" % (r, len(vals), sum(vals.values()) / len(vals),
                                                   min(vals.values()), max(vals.values()))
        for r, vals in seeds["values"].items())
    sp = gap["environment"]["software_pairs"]
    tf = next((k for k in sp if "tf457" in k), None)
    tf_row = ("%s & %s & %s \\\\" % (tf, sp[tf]["delta_E"], sp.get("verify_r5_s42.json", {}).get("delta_E"))
              if tf else "")

    NEW_SECTIONS = r"""
\section{Curvature of the first-order approximation}
\label{app:hessian}

A direct finite-difference measurement of $g^\top H g$ along the gradient direction on LLaVA-1.5-7B (4-bit QLoRA,
blank-image protocol, three batches per rank). The second-order share is $0.5\,\eta\,g^\top H g/\|g\|^2$ at the
operating learning rate $\eta=5\times10^{-5}$; the last column splits the curvature by block group.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrrrr@{}}
\toprule
rank & $\|g\|^2$ & $g^\top H g$ ($10^{-3}$ step) & share at $\eta$ & share at $10^{-3}$ & vision share of $|g^\top H g|$ \\
\midrule
%(hess_rows)s
\bottomrule
\end{tabular}
\caption{Measured curvature of the alignment loss along the gradient direction. At the operating learning rate the
second-order term is about $3.5\%%$ of the first-order term and negative; it grows roughly linearly with the probe step,
so the truncation is adequate at the operating step but not at large steps. Archive:
\texttt{outputs/analysis/p3\_hessian\_probe\_r5.json}, \texttt{...\_r6.json}.}
\label{tab:hessian}
\end{table*}

\section{Additional allocation baselines}
\label{app:baselines}

Per-block NTK-diagonal traces on CLIP ViT-B/32 with real marine image--caption pairs, mapped to the paper's allocation
budget alongside the $\Gamma$ rule and the uniform rule, and two trained explicit four-block arms on LLaVA
(blank-image protocol, 20 samples, three epochs, seed 42; base rank 1, $\alpha=16$, so the arms are not
parameter-matched to the uniform $r=5$/$r=6$ arms and the comparison is directional).
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrrr@{}}
\toprule
block & NTK trace & NTK rank & $\Gamma$ rank & uniform \\
\midrule
%(ntk_rows)s
\bottomrule
\end{tabular}
\caption{NTK-diagonal allocation versus the $\Gamma$ and uniform rules (budget 16). Archive:
\texttt{outputs/analysis/p3\_ntk\_allocation.json}.}
\label{tab:ntk}
\end{table*}

\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrl@{}}
\toprule
trained arm & $\Delta E$ & trajectory \\
\midrule
%(arm_rows)s
\bottomrule
\end{tabular}
\caption{Explicit four-block allocation arms trained under the blank-image protocol. Both end above their initial
energy. Archives: \texttt{verify\_r1\_s42\_ntk\_arm.json}, \texttt{verify\_r1\_s42\_bcexplicit\_v5\_s5\_m4\_d2.json}.}
\label{tab:ntkarm}
\end{table*}

\section{Newer model family}
\label{app:newer}

The same blank-image protocol on Qwen2.5-VL-3B-Instruct (20 samples, three epochs, seed 42, ranks 5 and 6).
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}rl l@{}}
\toprule
rank & $\Delta E$ & trajectory \\
\midrule
%(qwen_rows)s
\bottomrule
\end{tabular}
\caption{Newer-family control. The sign pattern is the opposite of LLaVA's (positive at $r=5$, near zero at $r=6$), so
the crossing does not replicate; this bounds the cross-architecture claim rather than extending it. Archives:
\texttt{paper3/scripts/outputs/experiments/qwen\_cf\_uniform\_rank*\_seed42\_q25\_r*.json}.}
\label{tab:newer}
\end{table*}

\section{Captioning downstream check}
\label{app:caption}

Two LLaVA adapters ($r=5,6$; 20 caption samples, three epochs) evaluated on four held-out marine caption samples, with
the base model as control.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrr@{}}
\toprule
arm & BLEU-4 & token F1 & CLIP similarity \\
\midrule
%(cap_rows)s
\bottomrule
\end{tabular}
\caption{Captioning check. Greedy generations are identical across the three arms (all BLEU-4 zero), so this check is
null and cannot support an energy-to-caption-quality claim in either direction. Archive:
\texttt{outputs/analysis/p3\_caption\_metrics.json}.}
\label{tab:caption}
\end{table*}

\section{Seed and software reproducibility matrix}
\label{app:env}

Five-seed spread of the crossing and the software-version control (transformers 4.57.0 against the reference 5.16.1 at
rank 5, seed 42).
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrr@{}}
\toprule
rank & $n$ & mean $\Delta E$ & range \\
\midrule
%(seed_rows)s
\bottomrule
\end{tabular}
\caption{Five-seed spread (authoritative archive \texttt{p3\_seeds\_combined.json}) and the cross-version control
\texttt{verify\_r5\_s42\_tf457.json} ($\Delta E$ %(tf_row)s). Hardware beyond the single RTX 4060 Laptop used for all
runs could not be tested; this remains a declared limitation.}
\label{tab:env}
\end{table*}

""" % {"hess_rows": hess_rows, "ntk_rows": ntk_rows, "arm_rows": arm_rows, "qwen_rows": qwen_rows,
       "cap_rows": cap_rows, "seed_rows": seed_rows, "tf_row": tf_row}

    if not a.apply:
        print("dry run; sections prepared")
        return 0
    t = io.open(SUPP, encoding="utf-8").read()
    if "app:hessian" not in t:
        anchor = "\\bibliographystyle{IEEEtran}"
        assert t.count(anchor) == 1
        t = t.replace(anchor, NEW_SECTIONS + "\n" + anchor, 1)
        # S13 provenance rows for the new floats
        old_row = "\\raggedright tab:seed5 & \\raggedright\\path{tools/_p1416_p3_seeds.py} & \\raggedright\\path{p3_rerun_seeds.json} & \\texttt{verified} \\\\"
        add_rows = old_row + "\n" + "\n".join(
            "\\raggedright %s & \\raggedright\\path{%s} & \\raggedright\\path{%s} & \\texttt{verified} \\\\" % r
            for r in (("tab:hessian", "tools/_p1499_p3_hessian_probe.py", "p3_hessian_probe_r5.json"),
                      ("tab:ntk", "tools/_p1502_p3_ntk_allocation.py", "p3_ntk_allocation.json"),
                      ("tab:ntkarm", "tools/_p1507_p3_integrate_gapfill.py", "p3_gapfill_summary.json"),
                      ("tab:newer", "paper3/scripts/run_training_qwen25.py", "qwen_cf_uniform_rank5_seed42_q25_r5.json"),
                      ("tab:caption", "tools/_p1501_p3_caption_downstream.py", "p3_caption_metrics.json"),
                      ("tab:env", "tools/_p1500_p3_env_matrix.py", "p3_environment_matrix.json")))
        assert t.count(old_row) == 1
        t = t.replace(old_row, add_rows, 1)
        # S17 claim rows
        old_bottom = "AdaLoRA is worse than our arms & \\emph{not} supported & AdaLoRA reaches lower energy in our comparison \\\\\n\\bottomrule"
        new_bottom = ("AdaLoRA is worse than our arms & \\emph{not} supported & AdaLoRA reaches lower energy in our comparison \\\\\n"
                      "first-order truncation adequate at the operating step & supported locally & second-order share $-3.5\\%$ at $\\eta=5\\times10^{-5}$; grows with the step (S18) \\\\\n"
                      "NTK-guided allocation improves the energy & \\emph{not} supported & trained NTK arm $+396.0$, $\\Gamma$ arm $+196.5$ (S19) \\\\\n"
                      "crossing transfers to a newer model family & \\emph{not} supported & Qwen2.5-VL-3B: $r=5$ $+608$, $r=6$ $-48$ (S20) \\\\\n"
                      "energy predicts caption quality & \\emph{not} supported & null caption check (S21) \\\\\n"
                      "\\bottomrule")
        assert t.count(old_bottom) == 1
        t = t.replace(old_bottom, new_bottom, 1)
        io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
        print("supplement updated (S18-S22, S13 rows, S17 rows)")

    # main-text sentences
    e = io.open(EXP, encoding="utf-8").read()
    if "app:ntkarm" not in e:
        anchor = "\\subsection{Counterfactual Validation}"
        sent = ("Two further allocation arms, trained under the same protocol, both end above their initial energy\n"
                "(NTK-guided $+396.0$, $\\Gamma$-guided explicit $+196.5$; Supplementary Section~S19); the NTK rule orders\n"
                "the blocks differently from $\\Gamma$ ($8/5/2/1$ against $5/5/4/2$), so the two rules cannot both be the\n"
                "zero-shot optimum.\n\n")
        assert e.count(anchor) == 1
        e = e.replace(anchor, sent + anchor, 1)
        io.open(EXP, "w", encoding="utf-8", newline="").write(e)
        print("experiments updated")
    d = io.open(DISC, encoding="utf-8").read()
    if "app:hessian" not in d:
        old = "(4) The phase transition is verified on two datasets (Alpaca,\nShareGPT) but not on captioning or question-answering data."
        new = ("(4) The phase transition is verified on two instruction datasets (Alpaca,\nShareGPT) and on a captioning family, but not on question-answering data; on a newer model family (Qwen2.5-VL-3B)\n"
               "the crossing does not replicate (Supplementary Section~S20), so the cross-architecture scope is bounded.")
        if old in d:
            d = d.replace(old, new, 1)
        old5 = "prior work~\\cite{wan2026gap} found\nthe approximation adequate ($R^2>0.96$), but formal error bounds are absent."
        new5 = ("prior work~\\cite{wan2026gap} found\nthe approximation adequate ($R^2>0.96$), but formal error bounds are absent; our direct measurement puts the\n"
                "second-order share at $3.5\\%$ of the first-order term at the operating learning rate (Supplementary Section~S18).")
        if old5 in d:
            d = d.replace(old5, new5, 1)
        io.open(DISC, "w", encoding="utf-8", newline="").write(d)
        print("discussion updated")
    c = io.open(CONC, encoding="utf-8").read()
    if "app:newer" not in c:
        old = "($\\Delta E=+83.0$ against $-7.5$ at $r=5$ and $r=6$ under the instruction protocol, and $+66.5$ against $-39.5$ under the caption protocol)."
        new = (old + " It also does not replicate on a newer model family (Qwen2.5-VL-3B; Supplementary Section~S20).")
        if old in c:
            c = c.replace(old, new, 1)
            io.open(CONC, "w", encoding="utf-8", newline="").write(c)
            print("conclusion updated")

    # audit expectations
    ac = io.open(AUDIT, encoding="utf-8").read()
    if "twenty-two S-sections" not in ac:
        ac = ac.replace('check("supplement: seventeen S-sections", n_sections == 17, f"{n_sections} sections")',
                        'check("supplement: twenty-two S-sections", n_sections == 22, f"{n_sections} sections")', 1)
        io.open(AUDIT, "w", encoding="utf-8", newline="").write(ac)
        print("audit_check section count -> 22")
    # manifest
    m = json.load(io.open(MANIFEST, encoding="utf-8"))
    floats = m["manuscripts"]["P3"]["floats"]
    have = {f["label"] for f in floats}
    for label, script, archive in (("tab:hessian", "tools/_p1499_p3_hessian_probe.py", "p3_hessian_probe_r5.json"),
                                   ("tab:ntk", "tools/_p1502_p3_ntk_allocation.py", "p3_ntk_allocation.json"),
                                   ("tab:ntkarm", "tools/_p1507_p3_integrate_gapfill.py", "p3_gapfill_summary.json"),
                                   ("tab:newer", "paper3/scripts/run_training_qwen25.py", "qwen_cf_uniform_rank5_seed42_q25_r5.json"),
                                   ("tab:caption", "tools/_p1501_p3_caption_downstream.py", "p3_caption_metrics.json"),
                                   ("tab:env", "tools/_p1500_p3_env_matrix.py", "p3_environment_matrix.json")):
        if label not in have:
            floats.append({"label": label, "kind": "table", "script": script, "archive": archive,
                           "status": "verified", "note": "R1 gap-fill supplement (2026-10-21)"})
    io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(m, indent=1, ensure_ascii=False))
    print("manifest updated; P3 floats:", len(floats))
    print("now compile main+supplement, then set audit_pdf SUPP_PAGES to the measured page count")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
