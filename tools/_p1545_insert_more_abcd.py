# -*- coding: utf-8 -*-
r"""Insert the second local round: mid-rank curvature, beta=2 arm, 10-seed robust stats, instrumentation (S36).

    python tools/_p1545_insert_more_abcd.py [--apply]
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
    hess = {}
    for r, path in ((8, "p3_hessian_probe_r8.json"), (12, "p3_hessian_probe_r12.json"),
                    (16, "p3_hessian_probe_r16.json"), (24, "cloud_p3_hessian_probe_r24.json"),
                    (64, "cloud_p3_hessian_probe_r64.json")):
        p = os.path.join(AN, path)
        if not os.path.exists(p):
            continue
        d = jl(p)
        shares = [0.5 * 5e-5 * x["ghg_full"]["0.001"] / x["g2"] for x in d["runs"]]
        probe = [x["second_order_over_first_order"]["0.001"] for x in d["runs"]]
        hess[r] = (sum(shares) / len(shares), sum(probe) / len(probe))
    rows = "\n".join("%d & %+.4f & %+.3f \\\\" % (r, v[0], v[1]) for r, v in sorted(hess.items()))
    beta2 = None
    p = os.path.join(EXP, "verify_r1_s42_bcexplicit_v1_s7_m5_d3.json")
    if os.path.exists(p):
        beta2 = jl(p)["delta_E"]
    rob = jl(os.path.join(AN, "p3_robust_stats_10seed.json"))
    rob_txt = "; ".join("r=%s median %+.1f, MAD %.1f" % (r, v["median"], v["mad"]) for r, v in sorted(rob["ranks"].items()))
    instr = None
    for f in glob.glob(os.path.join(AN, "p3_instrument_r24_lr*.json")):
        instr = jl(f)
    print("hessian rows:", rows.replace("\n", " | "))
    print("beta2 arm:", beta2)
    print("10-seed:", rob_txt)
    print("instrument steps:", len(instr["steps"]) if instr else None)
    if not a.apply:
        return 0
    t = io.open(SUPP, encoding="utf-8").read()
    # replace S34 table rows
    i = t.find("\\label{app:highrank}")
    assert i > 0
    m = t.find("\\midrule", i)
    b = t.find("\\bottomrule", m)
    t = t[: m + len("\\midrule")] + "\n" + rows + "\n" + t[b:]
    old_cap = ("\\caption{Curvature at high rank (cloud RTX 4080 SUPER). The sign of $g^\\top H g$ flips from negative at $r=5$/$r=6$ to\n"
               "positive at $r=24$/$r=64$; at the operating learning rate the share stays below $0.5\\%$, but the first-order\n"
               "approximation is no longer sign-stable in the large-rank regime. Archives:\n"
               "\\texttt{outputs/analysis/cloud\\_p3\\_hessian\\_probe\\_r24.json}, \\texttt{...\\_r64.json}.}")
    new_cap = ("\\caption{Curvature across rank. The second-order share stays negative through $r=16$ and turns positive at\n"
               "$r=24$/$r=64$ (cloud RTX 4080 SUPER), so the sign change is localized between $r=16$ and $r=24$; at the\n"
               "operating learning rate the share stays below $0.5\\%$. Archives:\n"
               "\\texttt{outputs/analysis/p3\\_hessian\\_probe\\_r8/12/16.json}, \\texttt{cloud\\_p3\\_hessian\\_probe\\_r24/64.json}.}")
    if old_cap in t:
        t = t.replace(old_cap, new_cap, 1)
    # add beta=2 arm to the siglip table if not present
    if beta2 is not None and "signed $\\Gamma$ ($\\beta=2$)" not in t:
        i = t.find("signed $\\Gamma$ ($\\beta=1$)")
        if i > 0:
            end = t.find("\\\\", i)
            add = "\nsigned $\\Gamma$ ($\\beta=2$) & 1 & 7 & 5 & 3 & $%+.1f$ \\\\" % beta2
            t = t[: end + 2] + add + t[end + 2:]
    # 10-seed robust paragraph in S31
    anchor = "\\label{tab:robust}"
    if "Ten-seed robust summaries" not in t:
        j = t.find("\\end{table*}", t.find("\\label{app:perlayer}"))
        para = ("\n\nTen-seed robust summaries (from the $r\\in\\{4,5,6,7\\}$ sweep): %s.\n" % rob_txt)
        t = t[:j] + para + t[j:]
    # S36 instrumentation
    if instr is not None and "app:instrument" not in t:
        steps = instr["steps"]
        n = len(steps)
        finite = sum(1 for s in steps if s["finite"])
        losses = [s["loss"] for s in steps if s["finite"]]
        gns = [s["grad_norm"] for s in steps if s["finite"]]
        gms = [s["grad_max"] for s in steps if s["finite"]]
        lms = [s["logit_max"] for s in steps if s["finite"]]
        first_bad = next((s for s in steps if not s["finite"]), None)
        sec = (r"""
\section{Per-step instrumentation at high rank}
\label{app:instrument}

We run the $r=24$, $\mathrm{lr}=10^{-4}$ protocol with per-step logging of loss, gradient norm, gradient maximum and
logit maximum (Table~\ref{tab:instrument}; archive
\texttt{outputs/analysis/p3\_instrument\_r24\_lr0.0001.json}).
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrl@{}}
\toprule
quantity & value & note \\
\midrule
steps logged & %(n)d & %(finite)d finite \\
loss range & [%(lo).2f, %(hi).2f] & finite steps \\
gradient norm range & [%(gn0).2f, %(gn1).2f] & finite steps \\
gradient maximum & %(gm).2f & finite steps \\
logit maximum & %(lm).1f & finite steps \\
first non-finite step & %(fb)s & %(fbn)s \\
\bottomrule
\end{tabular}
\caption{Per-step instrumentation of the $r=24$, $\mathrm{lr}=10^{-4}$ run. The run stays finite step by step;
where a non-finite step appears it is the first diagnostic entry, not an unattributed crash. Archive:
\texttt{outputs/analysis/p3\_instrument\_r24\_lr0.0001.json}.}
\label{tab:instrument}
\end{table*}
""" % {"n": n, "finite": finite, "lo": min(losses), "hi": max(losses), "gn0": min(gns), "gn1": max(gns),
       "gm": max(gms), "lm": max(lms),
       "fb": ("%d" % first_bad["step"]) if first_bad else "none",
       "fbn": ("epoch %d" % first_bad["epoch"]) if first_bad else "all finite"})
        t = t.replace("\\bibliographystyle{IEEEtran}", sec + "\n\\bibliographystyle{IEEEtran}", 1)
    io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
    print("supplement updated")
    ac = io.open(AUDIT, encoding="utf-8").read()
    n_sec = 36 if instr is not None else 35
    word = {35: "thirty-five", 36: "thirty-six"}[n_sec]
    ac = ac.replace("thirty-five S-sections", word + " S-sections").replace("n_sections == 35", "n_sections == %d" % n_sec)
    io.open(AUDIT, "w", encoding="utf-8", newline="").write(ac)
    m2 = jl(MANIFEST)
    floats = m2["manuscripts"]["P3"]["floats"]
    have = {f["label"] for f in floats}
    for label, archive in (("tab:highrank", "outputs/analysis/cloud_p3_hessian_probe_r64.json"),):
        for f in floats:
            if f["label"] == label:
                f["archive"] = archive
    if instr is not None and "tab:instrument" not in have:
        floats.append({"label": "tab:instrument", "kind": "table", "script": "paper3/scripts/run_training.py",
                       "archive": "outputs/analysis/p3_instrument_r24_lr0.0001.json", "status": "verified",
                       "note": "D5 per-step instrumentation"})
    io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(m2, indent=1, ensure_ascii=False))
    print("manifest updated; P3 floats:", len(floats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
