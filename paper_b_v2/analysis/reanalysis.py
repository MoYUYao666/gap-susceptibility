#!/usr/bin/env python3
"""Paper B v2 G2 reanalysis of the frozen 144-run matrix.

Reads only `outputs/paper_b/runs/*.json`; never trains or downloads anything.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "outputs" / "paper_b" / "runs"
OUT = ROOT / "paper_b_v2" / "results" / "reanalysis.json"

READOUTS = ["classification_top1", "R1_i2t", "R1_t2i", "ARI"]
PROXIES = ["CG", "DG", "spec_eff_rank", "spec_top1_share"]
SITES = ["both", "text", "vision"]
DATASETS = ["dtd", "inat", "nksid"]
RANKS = [8, 16, 32, 64]


def norm_readout(name: str, value: float) -> float:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        raise ValueError(f"missing {name}")
    if name in ("classification_top1", "R1_i2t", "R1_t2i"):
        return float(value) / 100.0
    if name == "ARI":
        return float(np.clip(value, 0.0, 1.0))
    raise KeyError(name)


def rankdata(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x)
    ranks = np.empty(len(x), dtype=float)
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and x[order[j + 1]] == x[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra, rb = rankdata(a), rankdata(b)
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    den = float(np.sqrt((ra * ra).sum() * (rb * rb).sum()))
    if den == 0.0:
        return 0.0
    return float((ra * rb).sum() / den)


def load_runs() -> list[dict]:
    rows = []
    for path in sorted(RUNS.glob("*.json")):
        if path.name == "summary.json":
            continue
        d = json.loads(path.read_text(encoding="utf-8"))
        meta = d.get("run", {})
        eps = d.get("epochs", [])
        if len(eps) < 3:
            continue
        cps = []
        for rec in eps:
            cond = rec["conditions"]["original"]
            cps.append(
                {
                    "epoch": int(rec["epoch"]),
                    "proxy": [float(cond[p]) for p in PROXIES],
                    "readout": [norm_readout(r, cond[r]) for r in READOUTS],
                }
            )
        cps = sorted(cps, key=lambda c: c["epoch"])
        rows.append(
            {
                "run_id": path.stem,
                "site": meta.get("tower", "unknown"),
                "seed": int(meta.get("seed", -1)),
                "dataset": meta.get("dataset", "unknown"),
                "rank": int(meta.get("rank", -1)),
                "checkpoints": cps,
            }
        )
    return rows


def summarize(values: list[float]) -> dict:
    a = np.asarray(values, dtype=float)
    return {
        "n": int(a.size),
        "mean": float(a.mean()),
        "median": float(np.median(a)),
        "q10": float(np.quantile(a, 0.10)),
        "q25": float(np.quantile(a, 0.25)),
        "q75": float(np.quantile(a, 0.75)),
        "q90": float(np.quantile(a, 0.90)),
        "min": float(a.min()),
        "max": float(a.max()),
    }


def analyse() -> dict:
    runs = load_runs()
    run_by_id = {r["run_id"]: r for r in runs}
    per_run = []
    for r in runs:
        y = np.asarray([np.mean(c["readout"]) for c in r["checkpoints"]], dtype=float)
        last = float(y[-1])
        oracle = float(y.max())
        gap = oracle - last
        monotone = bool(np.all(np.diff(y) >= 0.0))
        last_is_oracle = bool(np.isclose(last, oracle, atol=1e-12, rtol=0.0))
        proxy_stats = {}
        for pi, pname in enumerate(PROXIES):
            g = np.asarray([c["proxy"][pi] for c in r["checkpoints"]], dtype=float)
            sel = int(np.argmax(g))
            proxy_stats[pname] = {
                "rho": spearman(g, y),
                "selected_epoch": sel + 1,
                "selected_y": float(y[sel]),
                "regret": float(oracle - y[sel]),
                "diff_vs_last": float(y[sel] - last),
            }
        per_run.append(
            {
                "run_id": r["run_id"],
                "site": r["site"],
                "seed": r["seed"],
                "dataset": r["dataset"],
                "rank": r["rank"],
                "y": [float(v) for v in y],
                "last": last,
                "oracle": oracle,
                "gap": gap,
                "monotone": monotone,
                "last_is_oracle": last_is_oracle,
                "proxy": proxy_stats,
            }
        )

    n = len(per_run)
    gaps = [x["gap"] for x in per_run]
    nonmono = [x for x in per_run if not x["monotone"]]
    mono = [x for x in per_run if x["monotone"]]
    last_oracle = [x for x in per_run if x["last_is_oracle"]]

    per_proxy = {}
    for pname in PROXIES:
        rhos = [x["proxy"][pname]["rho"] for x in per_run]
        signs = {}
        for sign, label in [(1.0, "higher"), (-1.0, "lower")]:
            regrets = []
            diffs = []
            acc = []
            for x in per_run:
                y = np.asarray(x["y"], dtype=float)
                g = np.asarray(
                    [
                        c["proxy"][PROXIES.index(pname)]
                        for c in run_by_id[x["run_id"]]["checkpoints"]
                    ],
                    dtype=float,
                )
                sel = int(np.argmax(sign * g))
                regret = float(y.max() - y[sel])
                diff = float(y[sel] - y[-1])
                regrets.append(regret)
                diffs.append(diff)
                acc.append(1.0 if sel == int(np.argmax(y)) else 0.0)
            signs[label] = {
                "selection_accuracy": float(np.mean(acc)),
                "mean_regret": float(np.mean(regrets)),
                "mean_diff_vs_last": float(np.mean(diffs)),
                "fraction_better_than_last": float(np.mean(np.asarray(diffs) > 0.0)),
            }
        best_label = min(signs, key=lambda k: signs[k]["mean_regret"])
        per_proxy[pname] = {
            "spearman_mean": float(np.mean(rhos)),
            "spearman_abs_mean": float(np.mean(np.abs(rhos))),
            "best_sign": best_label,
            **signs[best_label],
        }

    by_site = {}
    for site in SITES:
        xs = [x for x in per_run if x["site"] == site]
        if xs:
            by_site[site] = {
                "n": len(xs),
                "mean_gap": float(np.mean([x["gap"] for x in xs])),
                "last_oracle_fraction": float(np.mean([x["last_is_oracle"] for x in xs])),
                "nonmonotone_fraction": float(np.mean([not x["monotone"] for x in xs])),
            }

    by_dataset = {}
    for ds in DATASETS:
        xs = [x for x in per_run if x["dataset"] == ds]
        if xs:
            by_dataset[ds] = {
                "n": len(xs),
                "mean_gap": float(np.mean([x["gap"] for x in xs])),
                "last_oracle_fraction": float(np.mean([x["last_is_oracle"] for x in xs])),
            }

    by_rank = {}
    for rank in RANKS:
        xs = [x for x in per_run if x["rank"] == rank]
        if xs:
            by_rank[str(rank)] = {
                "n": len(xs),
                "mean_gap": float(np.mean([x["gap"] for x in xs])),
                "last_oracle_fraction": float(np.mean([x["last_is_oracle"] for x in xs])),
            }

    # Per-readout sensitivity: oracle gap computed on one readout at a time.
    per_readout = {}
    for j, name in enumerate(READOUTS):
        gaps_j = []
        last_oracle_j = 0
        for r in runs:
            vals = np.asarray([c["readout"][j] for c in r["checkpoints"]], dtype=float)
            last = float(vals[-1])
            oracle = float(vals.max())
            gaps_j.append(oracle - last)
            last_oracle_j += int(np.isclose(last, oracle, atol=1e-12, rtol=0.0))
        per_readout[name] = {
            "mean_gap": float(np.mean(gaps_j)),
            "median_gap": float(np.median(gaps_j)),
            "last_oracle_fraction": float(last_oracle_j / len(runs)),
        }

    h1 = float(len(nonmono) / n)
    h2_last = float(len(last_oracle) / n)
    h2_median_gap = float(np.median(gaps))
    best_proxy = min(per_proxy, key=lambda p: per_proxy[p]["mean_regret"])
    last_mean_regret = float(np.mean(gaps))
    h3 = {
        "best_proxy": best_proxy,
        "best_proxy_mean_regret": per_proxy[best_proxy]["mean_regret"],
        "last_mean_regret": last_mean_regret,
        "best_proxy_mean_abs_spearman": per_proxy[best_proxy]["spearman_abs_mean"],
        "regret_above_last": bool(per_proxy[best_proxy]["mean_regret"] > last_mean_regret),
        "alignment_below_0.5": bool(per_proxy[best_proxy]["spearman_abs_mean"] < 0.5),
        "supported": bool(
            per_proxy[best_proxy]["mean_regret"] > last_mean_regret
            and per_proxy[best_proxy]["spearman_abs_mean"] < 0.5
        ),
    }

    return {
        "source": {
            "runs_dir": "outputs/paper_b/runs",
            "n_runs": n,
            "condition": "original",
            "epochs": 3,
        },
        "coverage": {
            "sites": {s: sum(1 for x in per_run if x["site"] == s) for s in SITES},
            "datasets": {d: sum(1 for x in per_run if x["dataset"] == d) for d in DATASETS},
            "seeds": {str(s): sum(1 for x in per_run if x["seed"] == s) for s in sorted({x["seed"] for x in per_run})},
        },
        "aggregate": {
            "gap": summarize(gaps),
            "nonmonotone_fraction": h1,
            "last_is_oracle_fraction": h2_last,
            "n_nonmonotone": len(nonmono),
            "n_monotone": len(mono),
            "monotone_last_oracle_fraction": float(np.mean([x["last_is_oracle"] for x in mono])) if mono else None,
            "n_last_oracle": len(last_oracle),
            "proxy": per_proxy,
            "by_site": by_site,
            "by_dataset": by_dataset,
            "by_rank": by_rank,
            "per_readout": per_readout,
        },
        "hypotheses": {
            "H1_nonmonotone_at_least_20pct": {"value": h1, "supported": bool(h1 >= 0.20)},
            "H2_last_oracle_at_least_50pct_and_median_gap_le_0.01": {
                "last_oracle_fraction": h2_last,
                "median_gap": h2_median_gap,
                "supported": bool(h2_last >= 0.50 and h2_median_gap <= 0.01),
            },
            "H3_best_proxy_alignment_and_regret": h3,
        },
        "per_run": per_run,
    }


def main() -> None:
    result = analyse()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(result["aggregate"], indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
