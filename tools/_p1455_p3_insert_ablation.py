# -*- coding: utf-8 -*-
r"""P3: write the sample-window protocol ablation into the supplementary material (S15) and the manifest.

Reads outputs/analysis/p3_numsamples_ablation.json. The default num_samples=20 seed-42 r=6 run is the existing baseline
(+115.0 from p3_rerun_protocol.json), so the table lists 12/20/32/64 and the archive of each row.

    python tools/_p1455_p3_insert_ablation.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ABL = os.path.join(REPO, "outputs", "analysis", "p3_numsamples_ablation.json")
SUPP = os.path.join(REPO, "paper3", "paper_ieee", "supplementary", "supplementary.tex")
AUDIT = os.path.join(REPO, "paper3", "paper_ieee", "audit_check.py")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
BASELINE = 115.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(ABL):
        print("  ablation archive not ready")
        return 0
    d = json.load(io.open(ABL, encoding="utf-8"))
    rows = {20: BASELINE}
    for k, v in d.get("runs", {}).items():
        if v.get("ok") and v.get("delta_E") is not None:
            rows[int(v["num_samples"])] = float(v["delta_E"])
    if len(rows) < 4:
        print("  ablation incomplete:", sorted(rows))
        return 0
    table_rows = "\n".join("%d & %+.1f \\\\" % (n, rows[n]) for n in sorted(rows))
    sec = ("""\\section{Sample-window protocol ablation}
\\label{app:numsamples}

Holding rank ($r=6$) and seed (42) fixed while varying only the number of training samples changes the three-epoch
$\\Delta E$ by up to $3.8\\times$: the default window (20 samples) gives $%+.1f$, while 12/32/64 samples give $%+.1f$,
$%+.1f$ and $%+.1f$. The sample window is therefore part of the measurement protocol in the same sense as the rank,
even though the sign at this rank is unchanged. We did not relocate the crossing for the other windows, so we do not
claim that its position moves; we claim only that the effect size at fixed rank and seed is protocol-dependent. Data:
\\texttt{outputs/\\allowbreak analysis/\\allowbreak p3\\_numsamples\\_ablation.json}.

\\begin{table}[h]
\\centering
\\small
\\caption{Protocol ablation at $r=6$, seed 42, three epochs: only the sample window changes.}
\\label{tab:numsamples}
\\begin{tabular}{@{}rr@{}}
\\toprule
training samples & $\\Delta E$ \\\\
\\midrule
%s
\\bottomrule
\\end{tabular}
\\end{table}

""" % (rows[20], rows[12], rows[32], rows[64], table_rows))
    ts = io.open(SUPP, encoding="utf-8").read()
    changed = False
    if "app:numsamples" not in ts:
        anchor = "\\bibliographystyle{IEEEtran}"
        ts = ts.replace(anchor, sec + "\n" + anchor, 1)
        changed = True
        print("  supplementary S15 added")
    ta = io.open(AUDIT, encoding="utf-8").read()
    for old, new in (('check("supplement: fourteen S-sections", n_sections == 14, f"{n_sections} sections")',
                      'check("supplement: fifteen S-sections", n_sections == 15, f"{n_sections} sections")'),):
        if old in ta:
            ta = ta.replace(old, new, 1)
            changed = True
            print("  audit supplement count 14->15")
    tm = json.load(io.open(MANIFEST, encoding="utf-8"))
    p3 = tm["manuscripts"]["P3"]["floats"]
    have = {e["label"] for e in p3}
    add = []
    if "tab:seed5" not in have:
        add.append({"label": "tab:seed5", "kind": "table", "script": "tools/_p1416_p3_seeds.py",
                    "archive": "outputs/analysis/p3_rerun_seeds.json", "status": "verified",
                    "note": "supplementary S14 per-seed crossing values"})
    if "tab:numsamples" not in have:
        add.append({"label": "tab:numsamples", "kind": "table", "script": "tools/_p1417_p3_numsamples.py",
                    "archive": "outputs/analysis/p3_numsamples_ablation.json", "status": "verified",
                    "note": "supplementary S15 sample-window ablation"})
    if add:
        p3.extend(add)
        changed = True
        print("  manifest entries added:", [e["label"] for e in add])
    if a.apply and changed:
        io.open(SUPP, "w", encoding="utf-8", newline="").write(ts)
        io.open(AUDIT, "w", encoding="utf-8", newline="").write(ta)
        io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(tm, indent=1, ensure_ascii=False))
        print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
