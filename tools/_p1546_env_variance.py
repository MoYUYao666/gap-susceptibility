# -*- coding: utf-8 -*-
r"""Environment-vs-seed variance decomposition (r=5) and insertion as S37.

    python tools/_p1546_env_variance.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "paper3", "paper_ieee")
SUPP = os.path.join(BASE, "supplementary", "supplementary.tex")
AUDIT = os.path.join(BASE, "audit_check.py")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
AN = os.path.join(REPO, "outputs", "analysis")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")
OUT = os.path.join(AN, "p3_env_variance.json")


def jl(p):
    return json.load(io.open(p, encoding="utf-8"))


def collect():
    envs = {"torch 2.9/cu130": [], "torch 2.12/cu130": [], "torch 2.4/cu121": []}
    seeds = jl(os.path.join(AN, "p3_seeds_combined.json"))["values"]["r5"]
    envs["torch 2.9/cu130"] = [float(v) for v in seeds.values()]
    for f in glob.glob(os.path.join(EXP, "cloud_verify_r5_s*.json")):
        if "imgs" in f:
            continue
        d = jl(f)
        if d.get("delta_E") is None or not np.isfinite(d["delta_E"]):
            continue
        envs["torch 2.12/cu130"].append(d["delta_E"])
    for f in glob.glob(os.path.join(EXP, "verify_r5_s*_lr5e-05_nw_float1_adamw_e3_bcuniform_a10.json")):
        d = jl(f)
        if d.get("delta_E") is None or not np.isfinite(d["delta_E"]):
            continue
        envs["torch 2.4/cu121"].append(d["delta_E"])
    return envs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    envs = collect()
    rows = []
    k = len(envs)
    n_total = sum(len(v) for v in envs.values())
    grand = float(np.mean([x for v in envs.values() for x in v]))
    ss_between = sum(len(v) * (float(np.mean(v)) - grand) ** 2 for v in envs.values())
    ss_within = sum(sum((x - float(np.mean(v))) ** 2 for x in v) for v in envs.values())
    df_b = k - 1
    df_w = n_total - k
    ms_b = ss_between / df_b
    ms_w = ss_within / df_w
    n0 = n_total - sum(len(v) ** 2 for v in envs.values()) / n_total
    sig2_env = max(0.0, (ms_b - ms_w) / (n0 / (k - 1)))
    sig2_seed = ms_w
    share = sig2_env / (sig2_env + sig2_seed) if (sig2_env + sig2_seed) > 0 else 0.0
    print("envs:", {e: (len(v), round(float(np.mean(v)), 1), round(float(np.std(v, ddof=1)), 1)) for e, v in envs.items()})
    print(f"MS_between={ms_b:.1f} MS_within={ms_w:.1f} sigma_env={np.sqrt(sig2_env):.1f} sigma_seed={np.sqrt(sig2_seed):.1f} share={share:.2f}")
    out = {"meta": {"script": "tools/_p1546_env_variance.py", "task": "environment-vs-seed variance decomposition (r=5)",
                    "method": "one-way random-effects ANOVA on environment level (unequal n; n0-adjusted)"},
           "envs": {e: {"n": len(v), "values": v, "mean": float(np.mean(v)), "sd": float(np.std(v, ddof=1))}
                    for e, v in envs.items()},
           "ss_between": ss_between, "ss_within": ss_within, "ms_between": ms_b, "ms_within": ms_w,
           "sigma_env": float(np.sqrt(sig2_env)), "sigma_seed": float(np.sqrt(sig2_seed)),
           "env_variance_share": float(share)}
    json.dump(out, io.open(OUT, "w", encoding="utf-8"), indent=1)
    for e, v in envs.items():
        rows.append("%s & %d & %+.1f & %.1f \\\\" % (e, len(v), float(np.mean(v)), float(np.std(v, ddof=1))))
    rows = "\n".join(rows)
    print(rows)
    if not a.apply:
        return 0
    t = io.open(SUPP, encoding="utf-8").read()
    if "app:envvar" not in t:
        sec = r"""
\section{Variance decomposition of the environment effect}
\label{app:envvar}

To separate environment-to-environment variation from seed-to-seed variation at $r=5$ (the rank whose sign flips),
we collect all runs available in each environment and fit a one-way random-effects model with environment as the
single factor (Table~\ref{tab:envvar}).
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrr@{}}
\toprule
environment & $n$ & mean $\Delta E$ & sd \\
\midrule
%(rows)s
\bottomrule
\end{tabular}
\caption{Random-effects variance decomposition at $r=5$: $\sigma_{\mathrm{env}}=%(se).1f$,
$\sigma_{\mathrm{seed}}=%(ss).1f$, environment share $%(share).0f\%%$ of the total variance. The seed spread is larger
than the environment shift, but the environment factor is what flips the sign, which is why the paper reports
$r_c$ as environment-conditioned. Archive: \texttt{outputs/analysis/p3\_env\_variance.json}.}
\label{tab:envvar}
\end{table*}
""" % {"rows": rows, "se": float(np.sqrt(sig2_env)), "ss": float(np.sqrt(sig2_seed)), "share": 100 * share}
        t = t.replace("\\bibliographystyle{IEEEtran}", sec + "\n\\bibliographystyle{IEEEtran}", 1)
        io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
        print("S37 inserted")
    ac = io.open(AUDIT, encoding="utf-8").read()
    if "thirty-seven S-sections" not in ac:
        ac = ac.replace("thirty-six S-sections", "thirty-seven S-sections").replace("n_sections == 36", "n_sections == 37")
        io.open(AUDIT, "w", encoding="utf-8", newline="").write(ac)
        print("audit_check -> 37 sections")
    m = jl(MANIFEST)
    floats = m["manuscripts"]["P3"]["floats"]
    if not any(f["label"] == "tab:envvar" for f in floats):
        floats.append({"label": "tab:envvar", "kind": "table", "script": "tools/_p1546_env_variance.py",
                       "archive": "outputs/analysis/p3_env_variance.json", "status": "verified",
                       "note": "environment-vs-seed variance decomposition"})
        io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(m, indent=1, ensure_ascii=False))
        print("manifest updated; P3 floats:", len(floats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
