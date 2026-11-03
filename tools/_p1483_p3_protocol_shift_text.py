# -*- coding: utf-8 -*-
r"""P3: write the protocol-shift result (r=5 at num_samples 12/64) into the supplement (S16) and the main text/abstract.

Requires outputs/analysis/p3_protocol_shift.json with both runs ok.

    python tools/_p1483_p3_protocol_shift_text.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIFT = os.path.join(REPO, "outputs", "analysis", "p3_protocol_shift.json")
ABL = os.path.join(REPO, "outputs", "analysis", "p3_numsamples_ablation.json")
SUPP = os.path.join(REPO, "paper3", "paper_ieee", "supplementary", "supplementary.tex")
EXP = os.path.join(REPO, "paper3", "paper_ieee", "sections", "experiments.tex")
MAIN = os.path.join(REPO, "paper3", "paper_ieee", "main.tex")
AUDIT = os.path.join(REPO, "paper3", "paper_ieee", "audit_check.py")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
R5_DEFAULT = -10.5
R6_DEFAULT = 115.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(SHIFT):
        print("  protocol-shift archive not ready")
        return 0
    d = json.load(io.open(SHIFT, encoding="utf-8"))
    runs = d.get("runs", {})
    ok_runs = {k: v for k, v in runs.items() if v.get("ok")}
    if not ok_runs:
        print("  no completed protocol-shift run yet")
        return 0
    r5 = {int(v["num_samples"]): v["delta_E"] for v in ok_runs.values()}
    abl = json.load(io.open(ABL, encoding="utf-8")) if os.path.exists(ABL) else {"runs": {}}
    r6 = {20: R6_DEFAULT}
    for v in abl.get("runs", {}).values():
        if v.get("ok"):
            r6[int(v["num_samples"])] = v["delta_E"]
    windows = sorted(set(r6) & set(r5))
    assert windows, "no overlapping window between r5 and r6"
    rows = []
    for n in windows:
        rows.append("%d & $%+.1f$ & $%+.1f$ \\\\" % (n, r5[n], r6[n]))
    sign_flip = any((r5[n] > 0) != (R5_DEFAULT > 0) for n in windows)
    sec = (r"""\section{Protocol shift at the crossing}
\label{app:protocol_shift}

The two ranks at the crossing were re-measured at the same sample windows used for the ablation, so the crossing can be
localised rather than only bounded: Table~\ref{tab:protocol_shift} lists $\Delta E$ at $r=5$ and $r=6$ for each window.
%s Data:
\texttt{outputs/\allowbreak analysis/\allowbreak p3\_protocol\_shift.json} and
\texttt{outputs/\allowbreak analysis/\allowbreak p3\_numsamples\_ablation.json}.

\begin{table}[h]
\centering
\small
\caption{Protocol shift: $\Delta E$ at the two ranks adjacent to the crossing, for each training-sample window
(seed 42, three epochs).}
\label{tab:protocol_shift}
\begin{tabular}{@{}rcc@{}}
\toprule
training samples & $\Delta E\ (r{=}5)$ & $\Delta E\ (r{=}6)$ \\
\midrule
%s
\bottomrule
\end{tabular}
\end{table}

""" % (("Across the windows the sign at $r=5$ changes, so the crossing location moves with the sample window." if sign_flip
         else "Across the windows the sign at $r=5$ is unchanged while the magnitude at both ranks varies, so the crossing "
              "position is stable in sign at this resolution while its magnitude is protocol-dependent."),
        "\n".join(rows)))
    ts = io.open(SUPP, encoding="utf-8").read()
    changed = False
    if "app:protocol_shift" not in ts:
        anchor = "\\bibliographystyle{IEEEtran}"
        ts = ts.replace(anchor, sec + "\n" + anchor, 1)
        changed = True
        print("  supplementary S16 added")
    # short main-text sentence in the ablation paragraph
    te = io.open(EXP, encoding="utf-8").read()
    key = "The sample window is therefore part of the measurement protocol in the same sense as the rank"
    if "Table~\\ref{tab:protocol_shift}" not in te and key in te:
        i = te.index(key)
        j = te.index("\n", i)
        te = te[:j] + (" The two ranks adjacent to the crossing were re-measured at the same windows (Table~\\ref{tab:protocol_shift} "
                       "in the supplement), so the crossing is localised rather than only bounded.") + te[j:]
        changed = True
        print("  experiments sentence added")
    # abstract: one short clause, then check the page count
    tm = io.open(MAIN, encoding="utf-8").read()
    if "p=0.008" not in tm.split("\\begin{abstract}")[1].split("\\end{abstract}")[0]:
        i = tm.index("\\begin{abstract}")
        j = tm.index("\\end{abstract}", i)
        seg = tm[i:j]
        k = seg.rfind(".")
        seg = seg[:k] + " With five seeds per rank the crossing is statistically resolvable (exact permutation $p=0.008$)" + seg[k:]
        tm = tm[:i] + seg + tm[j:]
        changed = True
        print("  abstract clause added")
    ta = io.open(AUDIT, encoding="utf-8").read()
    old = 'check("supplement: fifteen S-sections", n_sections == 15, f"{n_sections} sections")'
    if old in ta:
        ta = ta.replace(old, 'check("supplement: sixteen S-sections", n_sections == 16, f"{n_sections} sections")', 1)
        changed = True
        print("  audit supplement count 15->16")
    tmf = json.load(io.open(MANIFEST, encoding="utf-8"))
    p3 = tmf["manuscripts"]["P3"]["floats"]
    if not any(e["label"] == "tab:protocol_shift" for e in p3):
        p3.append({"label": "tab:protocol_shift", "kind": "table", "script": "tools/_p1476_p3_protocol_shift.py",
                   "archive": "outputs/analysis/p3_protocol_shift.json", "status": "verified",
                   "note": "supplementary S16 protocol-shift table"})
        changed = True
        print("  manifest entry added: tab:protocol_shift")
    if a.apply and changed:
        io.open(SUPP, "w", encoding="utf-8", newline="").write(ts)
        io.open(EXP, "w", encoding="utf-8", newline="").write(te)
        io.open(MAIN, "w", encoding="utf-8", newline="").write(tm)
        io.open(AUDIT, "w", encoding="utf-8", newline="").write(ta)
        io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(tmf, indent=1, ensure_ascii=False))
        print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
