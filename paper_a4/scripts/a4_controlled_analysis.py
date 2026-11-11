# -*- coding: utf-8 -*-
"""Analysis of the controlled PEFT block: gap/readout validity across 108 checkpoints."""
from __future__ import annotations
import io, json, os
import numpy as np
from scipy.stats import spearmanr, pearsonr

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(REPO, "outputs", "a4", "a4_controlled_peft_2026-11-10.json")
OUT = os.path.join(REPO, "outputs", "a4", "a4_controlled_analysis_2026-11-10.json")


def sp(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 3 or a[m].std() == 0 or b[m].std() == 0:
        return {"rho": None, "p": None, "n": int(m.sum())}
    r = spearmanr(a[m], b[m])
    return {"rho": float(r.correlation), "p": float(r.pvalue), "n": int(m.sum())}


def fit_cv(rows, xkey, ykey, group):
    xs = np.asarray([r[xkey] for r in rows], float); ys = np.asarray([r[ykey] for r in rows], float)
    groups = np.asarray([r[group] for r in rows])
    pred = np.full(len(xs), np.nan)
    for g in sorted(set(groups.tolist())):
        te = groups == g; tr = ~te
        if tr.sum() < 3 or te.sum() == 0: continue
        A = np.column_stack([np.ones(tr.sum()), xs[tr]])
        beta, *_ = np.linalg.lstsq(A, ys[tr], rcond=None)
        pred[te] = beta[0] + beta[1] * xs[te]
    ok = np.isfinite(pred)
    if ok.sum() < 3: return None
    r = pearsonr(pred[ok], ys[ok])[0]
    ss_res = ((ys[ok] - pred[ok]) ** 2).sum(); ss_tot = ((ys[ok] - ys[ok].mean()) ** 2).sum()
    return {"pearson": float(r), "r2": float(1 - ss_res / ss_tot) if ss_tot else None,
            "spearman": float(spearmanr(pred[ok], ys[ok]).correlation), "n": int(ok.sum())}


def main():
    d = json.load(io.open(SRC, encoding="utf-8"))
    rows = []
    for run in d["runs"]:
        meta = run["run"]
        for e in run["epochs"]:
            for cond, m in e["conditions"].items():
                r = {"backbone": meta["backbone"], "dataset": meta["dataset"], "rank": meta["rank"],
                     "seed": meta["seed"], "tower": meta.get("tower", "both"), "epoch": e["epoch"],
                     "condition": cond, "train_loss": e["train_loss"]}
                for k, v in m.items(): r[k] = v
                rows.append(r)
    orig = [r for r in rows if r["condition"] == "original"]
    out = {"n_runs": len(d["runs"]), "n_checkpoints": len(orig), "n_rows": len(rows)}
    # gap redundancy
    out["CG_DG"] = {}
    for cond in ("original", "mean_center", "gap_project", "random_project"):
        sub = [r for r in rows if r["condition"] == cond]
        out["CG_DG"][cond] = sp([r["CG"] for r in sub], [r["DG"] for r in sub])
        out["CG_DG"][cond]["CG_mean"] = float(np.mean([r["CG"] for r in sub]))
        out["CG_DG"][cond]["DG_mean"] = float(np.mean([r["DG"] for r in sub]))
    # intervention effects, all checkpoints
    out["interventions"] = {}
    out["by_tower_interventions"] = {}
    for tw in sorted(set(r["tower"] for r in orig)):
        tw_eff = {}
        for cond in ("mean_center", "gap_project", "random_project"):
            eff = {}
            for k in ("classification_top1", "R1_i2t", "R1_t2i", "ARI"):
                vals = []
                for r in orig:
                    if r["tower"] != tw: continue
                    other = next((x for x in rows if x["condition"] == cond and x["backbone"] == r["backbone"]
                                  and x["dataset"] == r["dataset"] and x["rank"] == r["rank"]
                                  and x["seed"] == r["seed"] and x["epoch"] == r["epoch"]
                                  and x["tower"] == r["tower"]), None)
                    if other and np.isfinite(r[k]) and np.isfinite(other[k]): vals.append(other[k] - r[k])
                if vals: eff[k] = {"mean": float(np.mean(vals)), "sd": float(np.std(vals)), "n": len(vals)}
            tw_eff[cond] = eff
        out["by_tower_interventions"][tw] = tw_eff
    for cond in ("mean_center", "gap_project", "random_project"):
        eff = {}
        for k in ("classification_top1", "R1_i2t", "R1_t2i", "ARI"):
            vals = []
            for r in orig:
                other = next((x for x in rows if x["condition"] == cond and x["backbone"] == r["backbone"]
                              and x["dataset"] == r["dataset"] and x["rank"] == r["rank"]
                              and x["seed"] == r["seed"] and x["epoch"] == r["epoch"]
                              and x["tower"] == r["tower"]), None)
                if other and np.isfinite(r[k]) and np.isfinite(other[k]): vals.append(other[k] - r[k])
            if vals: eff[k] = {"mean": float(np.mean(vals)), "sd": float(np.std(vals)), "n": len(vals),
                               "improved": int(sum(v > 0 for v in vals)), "worse": int(sum(v < 0 for v in vals))}
        out["interventions"][cond] = eff
    # predictive validity of static gap/spectral metrics for readouts, across checkpoints
    out["predictive"] = {}
    for m in ("CG", "DG", "spec_eff_rank", "spec_top1_share"):
        for target in ("classification_top1", "R1_i2t", "R1_t2i", "ARI"):
            out["predictive"]["%s__%s" % (m, target)] = sp([r[m] for r in orig], [r[target] for r in orig])
    out["by_tower_predictive"] = {}
    for tw in sorted(set(r["tower"] for r in orig)):
        sub = [r for r in orig if r["tower"] == tw]
        out["by_tower_predictive"][tw] = {}
        for m in ("CG", "DG", "spec_eff_rank", "spec_top1_share"):
            for target in ("classification_top1", "R1_i2t", "R1_t2i", "ARI"):
                out["by_tower_predictive"][tw]["%s__%s" % (m, target)] = sp([r[m] for r in sub], [r[target] for r in sub])
    # grouped held-out prediction
    out["grouped"] = {}
    for m in ("CG", "DG", "spec_eff_rank", "spec_top1_share"):
        for target in ("classification_top1", "R1_i2t", "R1_t2i", "ARI"):
            for g in ("dataset", "backbone", "tower"):
                out["grouped"]["%s__%s__%s" % (m, target, g)] = fit_cv(orig, m, target, g)
    # change-from-first-to-last within each run
    deltas = []
    for run in d["runs"]:
        es = sorted(run["epochs"], key=lambda x: x["epoch"])
        if len(es) < 2: continue
        a, b = es[0]["conditions"]["original"], es[-1]["conditions"]["original"]
        row = {"backbone": run["run"]["backbone"], "dataset": run["run"]["dataset"], "rank": run["run"]["rank"],
               "seed": run["run"]["seed"], "tower": run["run"].get("tower", "both")}
        for k in ("CG", "DG", "spec_eff_rank", "classification_top1", "R1_i2t", "R1_t2i", "ARI"):
            row["d" + k] = b[k] - a[k]
        deltas.append(row)
    out["delta_predictive"] = {}
    for m in ("dCG", "dDG", "dspec_eff_rank"):
        for target in ("dclassification_top1", "dR1_i2t", "dR1_t2i", "dARI"):
            out["delta_predictive"]["%s__%s" % (m, target)] = sp([r[m] for r in deltas], [r[target] for r in deltas])
    out["n_delta_runs"] = len(deltas)
    # per-adaptation-site means
    out["by_tower"] = {}
    for tw in sorted(set(r["tower"] for r in orig)):
        sub = [r for r in orig if r["tower"] == tw]
        out["by_tower"][tw] = {"n_checkpoints": len(sub),
                               "CG": float(np.mean([r["CG"] for r in sub])),
                               "DG": float(np.mean([r["DG"] for r in sub])),
                               "spec_eff_rank": float(np.mean([r["spec_eff_rank"] for r in sub])),
                               "classification_top1": float(np.mean([r["classification_top1"] for r in sub])),
                               "R1_i2t": float(np.mean([r["R1_i2t"] for r in sub])),
                               "R1_t2i": float(np.mean([r["R1_t2i"] for r in sub])),
                               "ARI": float(np.mean([r["ARI"] for r in sub]))}
    # per-dataset original means
    out["by_dataset"] = {}
    for ds in sorted(set(r["dataset"] for r in orig)):
        sub = [r for r in orig if r["dataset"] == ds]
        out["by_dataset"][ds] = {"n_checkpoints": len(sub),
                                 "CG": float(np.mean([r["CG"] for r in sub])),
                                 "DG": float(np.mean([r["DG"] for r in sub])),
                                 "spec_eff_rank": float(np.mean([r["spec_eff_rank"] for r in sub])),
                                 "classification_top1": float(np.mean([r["classification_top1"] for r in sub])),
                                 "R1_i2t": float(np.mean([r["R1_i2t"] for r in sub])),
                                 "R1_t2i": float(np.mean([r["R1_t2i"] for r in sub])),
                                 "ARI": float(np.mean([r["ARI"] for r in sub]))}
    json.dump(out, io.open(OUT, "w", encoding="utf-8"), indent=1)
    lines = ["# A4 controlled PEFT block results (2026-11-10)", "",
             "Runs: %d; checkpoints: %d; conditions: 4." % (out["n_runs"], out["n_checkpoints"]), "",
             "## CG/DG redundancy", ""]
    for c in ("original", "mean_center", "gap_project", "random_project"):
        v = out["CG_DG"][c]; lines.append("- %s: rho=%.3f, mean CG=%.3f, mean DG=%.3f" % (c, v["rho"], v["CG_mean"], v["DG_mean"]))
    lines += ["", "## Intervention effects (mean change over all checkpoints)", ""]
    for c, eff in out["interventions"].items():
        lines.append("**%s**" % c)
        for k, v in eff.items(): lines.append("- %s: %+.2f (sd %.2f, improved %d/%d)" % (k, v["mean"], v["sd"], v["improved"], v["n"]))
        lines.append("")
    lines += ["## Predictive validity (static, across checkpoints)", ""]
    for k, v in out["predictive"].items():
        if v["rho"] is not None: lines.append("- %s: rho=%+.3f (n=%d)" % (k, v["rho"], v["n"]))
    lines += ["", "## Grouped held-out R2 (selected)", ""]
    for k, v in out["grouped"].items():
        if v and v["r2"] is not None and v["r2"] > 0.1: lines.append("- %s: R2=%.2f, rho=%.2f" % (k, v["r2"], v["spearman"]))
    lines += ["", "## By adaptation site", ""]
    for tw, v in out["by_tower"].items():
        lines.append("- %s: n=%d, CG=%.3f, DG=%.3f, class=%.1f, i2t=%.1f, t2i=%.1f, ARI=%.3f" % (tw, v["n_checkpoints"], v["CG"], v["DG"], v["classification_top1"], v["R1_i2t"], v["R1_t2i"], v["ARI"]))
    lines += ["", "## Change-from-first-to-last", ""]
    for k, v in out["delta_predictive"].items():
        if v["rho"] is not None: lines.append("- %s: rho=%+.3f (n=%d)" % (k, v["rho"], v["n"]))
    io.open(os.path.join(REPO, "outputs", "a4", "A4_CONTROLLED_RESULTS_2026-11-10.md"), "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
    print("wrote", OUT)
    print("\n".join(lines[:40]))


if __name__ == "__main__":
    main()
