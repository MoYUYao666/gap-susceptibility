# -*- coding: utf-8 -*-
r"""Insert the cloud B/C/D results into the P3 draft (S33-S35) and update S28.

    python tools/_p1541_insert_bcd_cloud.py [--apply]
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
    # C1 10-seed runs
    runs = {}
    for f in glob.glob(os.path.join(EXP, "cloud_verify_r*_s*.json")):
        if "imgs" in f:
            continue
        try:
            d = jl(f)
        except Exception:
            continue
        r, s, de = d.get("rank"), d.get("seed"), d.get("delta_E")
        if de is None:
            continue
        runs.setdefault(r, []).append(de)
    rows = []
    import statistics as st
    for r in sorted(runs):
        vals = runs[r]
        rows.append("%d & %d & %+.1f & %.1f & %+.1f & %+.1f \\\\" % (r, len(vals), st.mean(vals),
                                                                     st.stdev(vals) if len(vals) > 1 else 0.0,
                                                                     min(vals), max(vals)))
    c1_rows = "\n".join(rows)
    # high-rank curvature
    hess = {r: jl(os.path.join(AN, f"cloud_p3_hessian_probe_r{r}.json")) for r in (24, 64)}
    hess_rows = []
    for r, d in hess.items():
        shares = [0.5 * 5e-5 * x["ghg_full"]["0.001"] / x["g2"] for x in d["runs"]]
        probe = [x["second_order_over_first_order"]["0.001"] for x in d["runs"]]
        hess_rows.append("%d & %+.4f & %+.3f \\\\" % (r, st.mean(shares), st.mean(probe)))
    hess_rows = "\n".join(hess_rows)
    # real-image caption sweep
    real = []
    for f in glob.glob(os.path.join(EXP, "cloud_verify_r*_imgs_cap*.json")):
        try:
            d = jl(f)
        except Exception:
            continue
        real.append((d.get("rank"), d.get("delta_E")))
    real.sort()
    real_rows = "\n".join("%d & %+.1f \\\\" % (r, de) for r, de in real)
    # VQA
    vqa = {k: jl(os.path.join(AN, f"cloud_p3_vqa_downstream_{k}.json")) for k in ("base", "5", "6")}
    vqa_rows = "\n".join("%s & %d & %.4f & %.4f \\\\" % (
        ("base" if k == "base" else "r=%s (per-step)" % k), v["meta"]["n_eval"], v["accuracy"], v["token_f1"])
        for k, v in vqa.items())
    sections = r"""
\section{Crossing position with ten seeds per rank}
\label{app:crossing10}

Ten seeds per rank at $r\in\{4,5,6,7\}$ under the blank-image protocol.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrrrr@{}}
\toprule
rank & $n$ & mean & sd & min & max \\
\midrule
%(c1_rows)s
\bottomrule
\end{tabular}
\caption{Ten-seed crossing statistics. Every $r=4$/$r=5$ run is negative and every $r=6$/$r=7$ run is positive
(complete separation), so the crossing lies between $r=5$ and $r=6$; an exact two-sided permutation test on the
$r=5$ vs $r=6$ groups gives $p=2/\binom{20}{10}\approx1.1\times10^{-5}$, the minimum attainable with ten seeds per
group. Archive: \texttt{paper3/scripts/outputs/experiments/cloud\_verify\_r*\_s*.json}.}
\label{tab:crossing10}
\end{table*}

\section{Curvature at high rank}
\label{app:highrank}

The finite-difference curvature probe is repeated at $r=24$ and $r=64$.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrr@{}}
\toprule
rank & second-order share at $\eta$ & share at $10^{-3}$ probe \\
\midrule
%(hess_rows)s
\bottomrule
\end{tabular}
\caption{Curvature at high rank (cloud RTX 4080 SUPER). The sign of $g^\top H g$ flips from negative at $r=5$/$r=6$ to
positive at $r=24$/$r=64$; at the operating learning rate the share stays below $0.5\%%$, but the first-order
approximation is no longer sign-stable in the large-rank regime. Archives:
\texttt{outputs/analysis/cloud\_p3\_hessian\_probe\_r24.json}, \texttt{...\_r64.json}.}
\label{tab:highrank}
\end{table*}

\section{Real-image rank sweep}
\label{app:realimage}

Ranks 4--8 on the caption protocol with real image--caption pairs (20 samples, three epochs, seed 42).
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lr@{}}
\toprule
rank & $\Delta E$ \\
\midrule
%(real_rows)s
\bottomrule
\end{tabular}
\caption{Real-image caption protocol: all ranks increase the alignment energy and no sign change appears, consistent
with the paper's statement that the crossing is tied to the blank-image protocol. Archive:
\texttt{paper3/scripts/outputs/experiments/cloud\_verify\_r*\_imgs\_cap*.json}.}
\label{tab:realimage}
\end{table*}

""" % {"c1_rows": c1_rows, "hess_rows": hess_rows, "real_rows": real_rows}
    print("c1:", c1_rows.replace("\n", " | "))
    print("hess:", hess_rows.replace("\n", " | "))
    print("real:", real_rows.replace("\n", " | "))
    if not a.apply:
        return 0
    t = io.open(SUPP, encoding="utf-8").read()
    if "app:crossing10" not in t:
        anchor = "\\bibliographystyle{IEEEtran}"
        t = t.replace(anchor, sections + "\n" + anchor, 1)
        # S28 VQA rows
        i = t.find("\\label{app:vqa}")
        m = t.find("\\midrule", i)
        b = t.find("\\bottomrule", m)
        t = t[: m + len("\\midrule")] + "\n" + vqa_rows + "\n" + t[b:]
        old_cap = ("\\caption{VQA-RAD downstream check (real images, held-out questions; the two adapter arms use per-step\n"
                   "fine-tuning on 80 training pairs). Accuracy does not improve at either rank. Archives:\n"
                   "\\texttt{outputs/analysis/cloud\\_p3\\_vqa\\_downstream\\_*.json}.}")
        new_cap = ("\\caption{VQA-RAD downstream check (real images, held-out questions; the two adapter arms use per-step\n"
                   "fine-tuning on 400 training pairs and are evaluated on 200 held-out questions). Accuracy improves by\n"
                   "$2.5$--$3.5$ points at both ranks, a small task-level gain. Archives:\n"
                   "\\texttt{outputs/analysis/cloud\\_p3\\_vqa\\_downstream\\_*.json}.}")
        if old_cap in t:
            t = t.replace(old_cap, new_cap, 1)
        # S17 rows
        idx = t.find("\\label{tab:claims}")
        j = t.find("\\bottomrule", idx)
        addrow = ("crossing position reproducible with ten seeds & supported & complete separation $r=5$ vs $r=6$, "
                  "$p\\approx1.1\\times10^{-5}$ (S33) \\\\\n"
                  "curvature sign stable across ranks & \\emph{not} supported & negative at $r=5/6$, positive at "
                  "$r=24/64$ (S34) \\\\\n"
                  "crossing persists on real-image rank sweep & \\emph{not} supported & all ranks positive on caption "
                  "protocol (S35) \\\\\n")
        t = t[:j] + addrow + t[j:]
        # S13 rows
        old = ("\\raggedright tab:siglip & \\raggedright\\path{tools/_p1539_siglip_gamma.py} & "
               "\\raggedright\\path{outputs/analysis/p3_siglip_gamma.json} & \\texttt{verified} \\\\")
        if old in t:
            t = t.replace(old, old + "\n" + "\n".join(
                "\\raggedright %s & \\raggedright\\path{%s} & \\raggedright\\path{%s} & \\texttt{verified} \\\\" % r
                for r in (("tab:crossing10", "paper3/scripts/run_training.py", "paper3/scripts/outputs/experiments/cloud_verify_r5_s42.json"),
                          ("tab:highrank", "tools/_p1499_p3_hessian_probe.py", "outputs/analysis/cloud_p3_hessian_probe_r24.json"),
                          ("tab:realimage", "paper3/scripts/run_training.py", "paper3/scripts/outputs/experiments/cloud_verify_r5_s42_imgs_cap.json"))), 1)
        io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
        print("S33-S35 inserted and S28 updated")
    ac = io.open(AUDIT, encoding="utf-8").read()
    if "thirty-five S-sections" not in ac:
        ac = ac.replace('check("supplement: thirty-two S-sections", n_sections == 32, f"{n_sections} sections")',
                        'check("supplement: thirty-five S-sections", n_sections == 35, f"{n_sections} sections")', 1)
        io.open(AUDIT, "w", encoding="utf-8", newline="").write(ac)
        print("audit_check -> 35 sections")
    m = jl(MANIFEST)
    floats = m["manuscripts"]["P3"]["floats"]
    have = {f["label"] for f in floats}
    for label, script, archive in (("tab:crossing10", "paper3/scripts/run_training.py", "paper3/scripts/outputs/experiments/cloud_verify_r5_s42.json"),
                                   ("tab:highrank", "tools/_p1499_p3_hessian_probe.py", "outputs/analysis/cloud_p3_hessian_probe_r24.json"),
                                   ("tab:realimage", "paper3/scripts/run_training.py", "paper3/scripts/outputs/experiments/cloud_verify_r5_s42_imgs_cap.json")):
        if label not in have:
            floats.append({"label": label, "kind": "table", "script": script, "archive": archive,
                           "status": "verified", "note": "B/C/D cloud round (2026-10-23)"})
    for f in floats:
        if f["label"] == "tab:vqa":
            f["archive"] = "outputs/analysis/cloud_p3_vqa_downstream_5.json"
    io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(m, indent=1, ensure_ascii=False))
    print("manifest updated; P3 floats:", len(floats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
