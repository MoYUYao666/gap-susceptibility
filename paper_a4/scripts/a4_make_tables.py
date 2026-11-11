# -*- coding: utf-8 -*-
"""Generate A4 LaTeX tables from the analysis JSON."""
import io, json, os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A = json.load(io.open(os.path.join(REPO, "outputs", "a4", "a4_analysis_2026-11-09.json"), encoding="utf-8"))
G = json.load(io.open(os.path.join(REPO, "outputs", "a4", "a4_grouped_validity_2026-11-09.json"), encoding="utf-8"))
OUT = os.path.join(REPO, "paper_a4", "draft")
os.makedirs(OUT, exist_ok=True)

keys = [("classification_top1", "Class."), ("R1_i2t", "$R@1_{i2t}$"), ("R1_t2i", "$R@1_{t2i}$"),
        ("ARI", "ARI"), ("mixed_R1", "Mixed")]
conds = [("mean_center", "Mean-center"), ("gap_project", "Gap-project"), ("random_project", "Random-project")]
lines = [r"\begin{table}[t]", r"\centering", r"\caption{Readout changes under three linear interventions (mean change relative to the original features; sd across cells in parentheses). Positive means the readout improves. Classification and ARI are defined on the three class datasets; all other columns use all six datasets.}", r"\label{tab:interventions}", r"\small", r"\begin{tabular}{@{}lccc@{}}", r"\toprule", r"Readout & Mean-center & Gap-project & Random-project \\", r"\midrule"]
for k, lab in keys:
    vals = []
    for c, _ in conds:
        v = A["C2_effect_means"][c].get(k)
        vals.append("$%+.2f$ (%.2f)" % (v["mean"], v["sd"]) if v else "---")
    lines.append("%s & %s \\\\" % (lab, " & ".join(vals)))
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
io.open(os.path.join(OUT, "table_interventions.tex"), "w", encoding="utf-8", newline="").write("\n".join(lines))

metrics = [("CG", "CG"), ("DG", "DG"), ("spec_eff_rank", "Spec. ER"), ("spec_top1_share", "Spec. top-1")]
targets = [("class", "classification_top1", "Class."), ("class", "R1_i2t", "$R@1_{i2t}$"),
           ("class", "R1_t2i", "$R@1_{t2i}$"), ("class", "ARI", "ARI"), ("caption", "R1_i2t", "Cap. $R@1$")]
lines = [r"\begin{table}[t]", r"\centering", r"\caption{Spearman correlation between each gap metric and each readout across cells, in the original (untransformed) features. $n=15$ class cells or $15$ caption cells.}", r"\label{tab:validity}", r"\small", r"\begin{tabular}{@{}lccccc@{}}", r"\toprule",
         "Metric & " + " & ".join(t[2] for t in targets) + r" \\", r"\midrule"]
for m, ml in metrics:
    row = []
    for kind, t, _ in targets:
        v = A["C3_predictive_spearman"].get("%s__%s__%s" % (kind, m, t), {})
        row.append("$%+.2f$" % v["rho"] if v.get("rho") is not None else "---")
    lines.append("%s & %s \\\\" % (ml, " & ".join(row)))
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
io.open(os.path.join(OUT, "table_validity.tex"), "w", encoding="utf-8", newline="").write("\n".join(lines))

# grouped CV table
lines = [r"\begin{table}[t]", r"\centering", r"\caption{Grouped held-out prediction: linear model fitted on all but one dataset (or encoder) and evaluated on the held-out group; entries are $R^2$ (Spearman in parentheses).}", r"\label{tab:grouped}", r"\small", r"\begin{tabular}{@{}lcccc@{}}", r"\toprule",
         r"Metric / target & LODO (class) & LOOE (class) & LODO (all) & LOOE (all) \\", r"\midrule"]
def cell(key):
    v = G.get(key);
    if not v: return "---"
    return "%.2f (%.2f)" % (v["r2"], v["spearman"])
lines.append("CG / R@1$_{i2t}$ & %s & %s & %s & %s \\\\" % (
    cell("class__CG__R1_i2t__dataset"), cell("class__CG__R1_i2t__encoder"),
    cell("all__CG__R1_i2t__dataset"), cell("all__CG__R1_i2t__encoder")))
lines.append("DG / R@1$_{i2t}$ & %s & %s & %s & %s \\\\" % (
    cell("class__DG__R1_i2t__dataset"), cell("class__DG__R1_i2t__encoder"),
    cell("all__DG__R1_i2t__dataset"), cell("all__DG__R1_i2t__encoder")))
lines.append("Spec. ER / R@1$_{i2t}$ & %s & %s & %s & %s \\\\" % (
    cell("class__spec_eff_rank__R1_i2t__dataset"), cell("class__spec_eff_rank__R1_i2t__encoder"),
    cell("all__spec_eff_rank__R1_i2t__dataset"), cell("all__spec_eff_rank__R1_i2t__encoder")))
lines.append("Spec. top-1 / ARI & %s & %s & --- & --- \\\\" % (
    cell("class__spec_top1_share__ARI__dataset"), cell("class__spec_top1_share__ARI__encoder")))
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
io.open(os.path.join(OUT, "table_grouped.tex"), "w", encoding="utf-8", newline="").write("\n".join(lines))

# appendix per-cell table
lines = [r"\begin{longtable}{@{}llcccccc@{}}", r"\caption{Per-cell values in the original features. Class. is top-1 for class datasets; $R1_{i2t}$ and $R1_{t2i}$ are retrieval; ARI only for class datasets.}\\", r"\toprule",
         r"Encoder & Dataset & CG & DG & Spec. ER & Class. & $R1_{i2t}$ & $R1_{t2i}$ \\", r"\midrule", r"\endfirsthead",
         r"\toprule Encoder & Dataset & CG & DG & Spec. ER & Class. & $R1_{i2t}$ & $R1_{t2i}$ \\ \midrule \endhead",
         r"\bottomrule \endfoot"]
for r in sorted(A["cells"], key=lambda x: (x["encoder"], x["dataset"])):
    def fmt(k):
        v = r.get("original_" + k)
        return "%.1f" % v if isinstance(v, (int, float)) else "---"
    lines.append("%s & %s & %.3f & %.3f & %.1f & %s & %s & %s \\\\" % (
        r["encoder"], r["dataset"], r["original_CG"], r["original_DG"],
        r["original_spec_eff_rank"], fmt("classification_top1"), fmt("R1_i2t"), fmt("R1_t2i")))
lines += [r"\bottomrule", r"\end{longtable}", ""]
io.open(os.path.join(OUT, "table_cells.tex"), "w", encoding="utf-8", newline="").write("\n".join(lines))
print("tables written", OUT)
