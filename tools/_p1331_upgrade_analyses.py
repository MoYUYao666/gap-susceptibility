# -*- coding: utf-8 -*-
r"""Archive-only analyses for the upgrade package (no new model runs).

  P0-1  certificate monitoring rule      -> outputs/analysis/a1_certificate_rule.json
  P0-3  rank x position dose-response     -> outputs/analysis/paperA_rank_position_dynamics.json
  P0-4  ODE per-condition diagnostics     -> outputs/analysis/paperA_ode_diagnostics.json
  P1-8  LoRA vs full fine-tuning table    -> outputs/analysis/paperA_lora_vs_fullft.json
  P2-10 within-trajectory correlations    -> outputs/analysis/a1_showdown_within_run.json

    python tools/_p1331_upgrade_analyses.py [--apply]
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(REPO, "outputs", "analysis")


def load(p):
    return json.load(io.open(p, encoding="utf-8"))


def save(name, payload, apply):
    if apply:
        io.open(os.path.join(AN, name), "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        print("  wrote", name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # ------------------------------------------------------------ P0-1 rule
    camp = load(os.path.join(AN, "a1_campaign.json"))
    mass = load(os.path.join(AN, "a1_margin_mass.json"))
    frozen_m = next(r for r in mass["rows"] if r["family"] == "frozen")["mass_eps_0.01"]
    runs = {}
    for key, run in camp["runs"].items():
        runs[key] = [{"epoch": c["epoch"], "top1": c["top1"], "mass": c["mass_0.01"]} for c in run["checkpoints"]]
    deltas = [0.0, 0.005, 0.01, 0.02, 0.03, 0.05, 0.08]
    rule_rows = []
    for delta in deltas:
        regrets = []
        stops = []
        for key, ck in runs.items():
            oracle = max(c["top1"] for c in ck)
            # stop at the last epoch whose margin mass has not drifted beyond frozen + delta;
            # if the first epoch already exceeds it, stop at epoch 1
            chosen = ck[0]
            for c in ck:
                if c["mass"] <= frozen_m + delta:
                    chosen = c
            regrets.append(oracle - chosen["top1"])
            stops.append(chosen["epoch"])
        rule_rows.append({"delta": delta, "mean_regret": float(np.mean(regrets)),
                          "max_regret": float(np.max(regrets)),
                          "mean_stop_epoch": float(np.mean(stops)),
                          "stop_at_epoch1_share": float(np.mean([s == 1 for s in stops]))})
    # baselines
    base = {}
    for name, pick in (("last_epoch", lambda ck: ck[-1]), ("first_epoch", lambda ck: ck[0])):
        regrets = []
        for key, ck in runs.items():
            oracle = max(c["top1"] for c in ck)
            regrets.append(oracle - pick(ck)["top1"])
        base[name] = {"mean_regret": float(np.mean(regrets)), "max_regret": float(np.max(regrets))}
    rec = min(rule_rows, key=lambda r: (r["mean_regret"], r["max_regret"]))
    p0 = {"n_runs": len(runs), "frozen_M01": frozen_m, "delta_grid": deltas, "rules": rule_rows,
          "baselines": base, "recommended": rec,
          "definition": "stop at the last epoch with M(0.01) <= frozen M(0.01) + delta; epoch 1 if already exceeded"}
    print(f"  P0-1 recommended delta={rec['delta']} mean_regret={rec['mean_regret']:.2f} "
          f"(last-epoch baseline {base['last_epoch']['mean_regret']:.2f})")
    save("a1_certificate_rule.json", p0, a.apply)

    # ------------------------------------------------------------ P0-3 rank x position
    led = load(os.path.join(REPO, "outputs", "analysis", "ode_ledger.json"))
    runs_ = [r for r in led["runs"] if r.get("rank") is not None]
    grid = collections.defaultdict(lambda: {"alpha": [], "beta": [], "R2": []})
    for r in runs_:
        key = (r.get("family"), r.get("site"), int(r["rank"]))
        for k in ("alpha", "beta", "R2"):
            if r.get(k) is not None:
                grid[key][k].append(float(r[k]))
    rows = []
    for (fam, site, rank), v in sorted(grid.items()):
        rows.append({"family": fam, "site": site, "rank": rank, "n": len(v["alpha"]),
                     "alpha_mean": float(np.mean(v["alpha"])) if v["alpha"] else None,
                     "beta_mean": float(np.mean(v["beta"])) if v["beta"] else None,
                     "R2_mean": float(np.mean(v["R2"])) if v["R2"] else None})
    # position effect at matched rank (text_only - both), LoRA family
    pos = []
    for rank in sorted({r["rank"] for r in rows}):
        t = [r for r in rows if r["family"] == "lora" and r["site"] == "text_only" and r["rank"] == rank]
        b = [r for r in rows if r["family"] == "lora" and r["site"] == "both" and r["rank"] == rank]
        if t and b and t[0]["alpha_mean"] is not None and b[0]["alpha_mean"] is not None:
            pos.append({"rank": rank, "alpha_text_only": t[0]["alpha_mean"], "alpha_both": b[0]["alpha_mean"],
                        "position_effect": t[0]["alpha_mean"] - b[0]["alpha_mean"]})
    from scipy import stats as st
    trend = {}
    for site in ("text_only", "both"):
        xs = [r["rank"] for r in rows if r["family"] == "lora" and r["site"] == site]
        ys = [r["alpha_mean"] for r in rows if r["family"] == "lora" and r["site"] == site]
        if len(xs) >= 3:
            trend[site] = {"spearman_rank_alpha": float(st.spearmanr(xs, ys)[0]), "n": len(xs)}
    p03 = {"n_trajectories": len(runs_), "grid": rows, "position_effect_by_rank": pos, "trend": trend,
           "note": "alpha is the initial gap-closing velocity from the first-order ODE fit"}
    print(f"  P0-3 grid cells={len(rows)} position-effect points={len(pos)}")
    save("paperA_rank_position_dynamics.json", p03, a.apply)

    # ------------------------------------------------------------ P0-4 ODE diagnostics
    by_cond = collections.defaultdict(lambda: {"R2": [], "alpha": [], "beta": [], "rank": [], "seed": []})
    for r in led["runs"]:
        key = (r.get("family"), r.get("site"))
        for k in ("R2", "alpha", "beta"):
            if r.get(k) is not None:
                by_cond[key][k].append(float(r[k]))
    diag = []
    for (fam, site), v in sorted(by_cond.items()):
        r2 = np.array(v["R2"]) if v["R2"] else np.array([])
        if len(r2) == 0:
            continue
        diag.append({"family": fam, "site": site, "n": len(v["R2"]),
                     "R2_mean": float(r2.mean()), "R2_min": float(r2.min()), "R2_max": float(r2.max()),
                     "share_R2_above_0.9": float(np.mean(r2 > 0.9)),
                     "share_R2_below_0.5": float(np.mean(r2 < 0.5)),
                     "alpha_mean": float(np.mean(v["alpha"])) if v["alpha"] else None,
                     "beta_mean": float(np.mean(v["beta"])) if v["beta"] else None})
    all_r2 = np.array([r["R2"] for r in led["runs"] if r.get("R2") is not None])
    worst = sorted([r for r in led["runs"] if r.get("R2") is not None], key=lambda r: r["R2"])[:5]
    p04 = {"n_runs": len(led["runs"]), "R2_overall": {"mean": float(all_r2.mean()), "median": float(np.median(all_r2)),
                                                       "min": float(all_r2.min()), "max": float(all_r2.max()),
                                                       "share_above_0.9": float(np.mean(all_r2 > 0.9)),
                                                       "share_below_0.5": float(np.mean(all_r2 < 0.5))},
           "by_condition": diag,
           "worst_runs": [{"conf": r["conf"], "family": r["family"], "site": r["site"],
                           "rank": r.get("rank"), "R2": r["R2"]} for r in worst]}
    print(f"  P0-4 conditions={len(diag)} mean R2={p04['R2_overall']['mean']:.3f}")
    save("paperA_ode_diagnostics.json", p04, a.apply)

    # ------------------------------------------------------------ P1-8 LoRA vs full FT
    fam_rows = []
    for fam in ("lora", "adapter", "full_ft"):
        sub = [r for r in led["runs"] if r.get("family") == fam]
        if not sub:
            continue
        a_ = [r["alpha"] for r in sub if r.get("alpha") is not None]
        b_ = [r["beta"] for r in sub if r.get("beta") is not None]
        r_ = [r["R2"] for r in sub if r.get("R2") is not None]
        fam_rows.append({"family": fam, "n_runs": len(sub),
                         "n_configs": len({r["conf"] for r in sub}),
                         "alpha_mean": float(np.mean(a_)) if a_ else None,
                         "beta_mean": float(np.mean(b_)) if b_ else None,
                         "R2_mean": float(np.mean(r_)) if r_ else None})
    # matched site comparison where available
    site_rows = []
    for site in ("text_only", "both"):
        for fam in ("lora", "adapter"):
            sub = [r for r in led["runs"] if r.get("family") == fam and r.get("site") == site]
            if sub:
                site_rows.append({"site": site, "family": fam, "n": len(sub),
                                  "alpha_mean": float(np.mean([r["alpha"] for r in sub])),
                                  "beta_mean": float(np.mean([r["beta"] for r in sub])),
                                  "R2_mean": float(np.mean([r["R2"] for r in sub]))})
    p18 = {"by_family": fam_rows, "matched_site": site_rows,
           "note": "alpha/beta/R2 are first-order ODE parameters of the gap trajectory; full-tower runs use the "
                   "'other' site label in the ledger"}
    print(f"  P1-8 families={[r['family'] for r in fam_rows]}")
    save("paperA_lora_vs_fullft.json", p18, a.apply)

    # ------------------------------------------------------------ P2-10 within-run correlations
    camp_an = load(os.path.join(AN, "a1_campaign_analysis.json"))
    runs_by_key = camp["runs"]
    within = {"CG": [], "tau5": [], "M(0.01)": [], "M(0.02)": []}
    for key, run in runs_by_key.items():
        ck = run["checkpoints"]
        top = np.array([c["top1"] for c in ck], dtype=float)
        for name, getter in (("CG", lambda c: c["CG"]), ("tau5", lambda c: c["tau5"]),
                             ("M(0.01)", lambda c: c["mass_0.01"]), ("M(0.02)", lambda c: c["mass_0.02"])):
            v = np.array([getter(c) if getter(c) is not None else np.nan for c in ck], dtype=float)
            ok = np.isfinite(v) & np.isfinite(top)
            if ok.sum() >= 3 and np.std(v[ok]) > 1e-12 and np.std(top[ok]) > 1e-12:
                r = float(np.corrcoef(v[ok], top[ok])[0, 1])
                if np.isfinite(r):
                    within[name].append(r)
    p210 = {"n_runs": len(runs_by_key),
            "within_run_pearson": {k: {"mean": float(np.mean(v)), "min": float(np.min(v)), "max": float(np.max(v)),
                                       "n": len(v)} for k, v in within.items() if v}}
    print("  P2-10 within-run:", {k: (round(v["mean"], 3) if v else None) for k, v in p210["within_run_pearson"].items()})
    save("a1_showdown_within_run.json", p210, a.apply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
