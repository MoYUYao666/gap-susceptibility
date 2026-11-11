# -*- coding: utf-8 -*-
"""Cluster-bootstrap uncertainty for the A4 controlled block headline numbers."""
from __future__ import annotations
import io, json, os
import numpy as np
from scipy.stats import spearmanr

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(REPO, "outputs", "a4", "a4_controlled_peft_2026-11-10.json")
OUT = os.path.join(REPO, "outputs", "a4", "a4_controlled_bootstrap_2026-11-10.json")
B = 2000


def flatten(d):
    runs = []
    for run in d["runs"]:
        m = run["run"]; tower = m.get("tower", "both")
        for e in run["epochs"]:
            runs.append({"key": (m["backbone"], m["dataset"], m["rank"], m["seed"], tower, e["epoch"]),
                         "tower": tower, "epoch": e["epoch"], "conds": e["conditions"]})
    return runs


def rho_xy(rows, xkey, ykey):
    a = np.asarray([r[xkey] for r in rows], float); b = np.asarray([r[ykey] for r in rows], float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 4 or np.std(a[m]) == 0 or np.std(b[m]) == 0: return np.nan
    return float(spearmanr(a[m], b[m]).correlation)


def boot(rows, fn, B=B):
    # rows is a list of runs, each with checkpoints; resample runs with replacement
    vals = []
    for _ in range(B):
        pick = np.random.RandomState(_).randint(0, len(rows), len(rows)) if False else None
        idx = np.random.randint(0, len(rows), len(rows))
        sample = [x for i in idx for x in rows[i]["checkpoints"]]
        vals.append(fn(sample))
    vals = np.asarray([v for v in vals if np.isfinite(v)], float)
    return {"mean": float(np.mean(vals)), "lo": float(np.percentile(vals, 2.5)), "hi": float(np.percentile(vals, 97.5)), "n_boot": int(len(vals))}


def mean_effect(sample, cond, k):
    vals = []
    for c in sample:
        if cond in c["conds"] and c["conds"][cond].get(k) is not None and c["conds"]["original"].get(k) is not None:
            vals.append(c["conds"][cond][k] - c["conds"]["original"][k])
    return float(np.mean(vals)) if vals else np.nan


def rho_static(sample, m, t):
    return rho_xy(sample, "original_" + m, "original_" + t)


def main():
    d = json.load(io.open(SRC, encoding="utf-8"))
    flat = flatten(d)
    # attach metric fields
    for r in flat:
        for cond, m in r["conds"].items():
            for k, v in m.items(): r["%s_%s" % (cond, k)] = v
    # organize by run
    runs = {}
    for r in flat:
        b, ds, rk, sd, tw, ep = r["key"]
        key = (b, ds, rk, sd, tw)
        runs.setdefault(key, {"meta": key, "checkpoints": []})["checkpoints"].append(r)
    runlist = list(runs.values())
    out = {"n_runs": len(runlist), "n_checkpoints": len(flat), "B": B, "headline": {}, "by_site": {}}
    # headline functions use original/condition rows
    for cond in ("mean_center", "gap_project", "random_project"):
        for k in ("classification_top1", "R1_i2t", "R1_t2i", "ARI"):
            out["headline"]["%s__%s" % (cond, k)] = boot(runlist, lambda s, c=cond, kk=k: mean_effect(s, c, kk))
    for m in ("CG", "DG", "spec_eff_rank", "spec_top1_share"):
        for t in ("classification_top1", "R1_i2t", "R1_t2i", "ARI"):
            out["headline"]["rho_%s__%s" % (m, t)] = boot(runlist, lambda s, mm=m, tt=t: rho_static(s, mm, tt))
    # CG-DG rho
    out["headline"]["rho_CG__DG"] = boot(runlist, lambda s: rho_xy(s, "original_CG", "original_DG"))
    # site-specific
    for tw in ("both", "text", "vision"):
        sub = [x for x in runlist if x["meta"][4] == tw]
        out["by_site"][tw] = {"n_runs": len(sub)}
        for cond in ("mean_center", "gap_project"):
            for k in ("classification_top1", "R1_i2t", "R1_t2i", "ARI"):
                out["by_site"][tw]["%s__%s" % (cond, k)] = boot(sub, lambda s, c=cond, kk=k: mean_effect(s, c, kk))
        out["by_site"][tw]["rho_CG__DG"] = boot(sub, lambda s: rho_xy(s, "original_CG", "original_DG"))
        for m in ("CG", "DG", "spec_eff_rank", "spec_top1_share"):
            out["by_site"][tw]["rho_%s__R1_i2t" % m] = boot(sub, lambda s, mm=m: rho_static(s, mm, "R1_i2t"))
    json.dump(out, io.open(OUT, "w", encoding="utf-8"), indent=1)
    lines = ["# A4 controlled-block bootstrap (2026-11-10)", "", "Cluster bootstrap over %d runs (%d checkpoints), 2000 resamples." % (len(runlist), len(flat)), ""]
    for k, v in out["headline"].items():
        lines.append("- %s: %.3f [%.3f, %.3f]" % (k, v["mean"], v["lo"], v["hi"]))
    for tw, v in out["by_site"].items():
        lines.append("")
        lines.append("**%s** (n=%d)" % (tw, v["n_runs"]))
        for k, q in v.items():
            if isinstance(q, dict) and "mean" in q: lines.append("- %s: %.3f [%.3f, %.3f]" % (k, q["mean"], q["lo"], q["hi"]))
    io.open(os.path.join(REPO, "outputs", "a4", "A4_BOOTSTRAP_2026-11-10.md"), "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
    print("wrote", OUT)
    print("\n".join(lines[:20]))


if __name__ == "__main__":
    main()
