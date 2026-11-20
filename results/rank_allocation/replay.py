"""Build and verify the two v3.3 derived-result bundles."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
from itertools import combinations, product
import json
import math
from pathlib import Path
import re
import statistics
import string
import sys

MODES = ("original", "mean_center", "gap_project", "random_project")
GAMMA = ("gamma_n2", "gamma_n4", "gamma_n8", "gamma_n16")
CONTROLS = ("uniform", "random", "target_calibrated")
TASKS = ("flickr30k", "coco5k", "pope", "marinelife", "inat", "dtd", "scienceqa", "mmbench")
PUBLIC_SUFFIXES = {".json", ".py", ".md"}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_bytes())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    return sha(path.read_bytes())


def encoded(obj):
    return (json.dumps(obj, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode()


def same(actual, expected, path="result"):
    if isinstance(expected, dict) and isinstance(actual, dict):
        need(actual.keys() == expected.keys(), f"Field mismatch: {path}")
        for k, v in expected.items():
            same(actual[k], v, f"{path}.{k}")
    elif isinstance(expected, list) and isinstance(actual, (list, tuple)):
        need(len(actual) == len(expected), f"Length mismatch: {path}")
        for i, (a, b) in enumerate(zip(actual, expected)):
            same(a, b, f"{path}[{i}]")
    elif type(expected) is float and type(actual) in (int, float):
        need(math.isclose(actual, expected, rel_tol=2e-11, abs_tol=2e-11), f"Numeric mismatch: {path}: {actual} != {expected}")
    else:
        need(type(actual) is type(expected) and actual == expected, f"Mismatch: {path}: {actual} != {expected}")


def records(directory):
    return [read(p) for p in sorted(directory.glob("*.json"))]


def inventory(root):
    paths = set()
    for path in root.rglob("*"):
        need(not path.is_symlink() and not path.is_junction(), f"Linked bundle member: {path}")
        if path.is_file():
            need(path.suffix in PUBLIC_SUFFIXES, f"Unexpected file format: {path}")
            paths.add(path.relative_to(root).as_posix())
    return paths


def verify_manifest(root, track=None):
    manifest = read(root / "provenance.json")
    need(manifest["schema"] == "derived-result-bundle/1", "Unsupported provenance format")
    need(manifest["track"] in {"a4", "p3"}, "Unknown track")
    if track is not None:
        need(manifest["track"] == track, "Bundle track mismatch")
    entries = manifest["files"]
    paths = {e["destination"] for e in entries}
    need(len(paths) == len(entries) and paths | {"provenance.json"} == inventory(root),
         "Missing, duplicate or unlisted bundle file")
    for e in entries:
        p = root / e["destination"]
        need(digest(p) == e["public_sha256"], f"Bundle hash mismatch: {e['destination']}")
        if e["operation"] == "verbatim":
            same(e["source_sha256"], e["public_sha256"], e["destination"])
    return manifest


def producer(root, name):
    source = root / "code" / (name + ".py")
    module = importlib.util.module_from_spec(importlib.util.spec_from_file_location(name, source))
    # Execute the validated source without producing bytecode, even without -B.
    exec(compile(source.read_bytes(), str(source), "exec"), module.__dict__)
    return module


def a4_replay(root):
    import numpy as np
    from scipy.stats import spearmanr


    def corr(a, b):
        return float(spearmanr(a, b).statistic)

    def effects(checkpoints, metrics, ddof=1):
        return {
            f"{mode}__{m}": {
                "mean": float(np.mean(v)), "sd": float(np.std(v, ddof=ddof)), "n": len(v)
            }
            for mode in MODES[1:] for m in metrics
            for v in [[e[mode][m] - e["original"][m] for e in checkpoints]]
        }

    frozen = read(root / "frozen/readouts.json")
    need(len(frozen) == 30 and Counter(r["kind"] for r in frozen.values()) ==
         {"class": 15, "caption": 15}, "Frozen matrix incomplete")
    frozen_analysis = producer(root, "frozen_analysis").analyze(frozen)
    same(frozen_analysis, read(root / "frozen/analysis.json"), "frozen analysis")
    direction = read(root / "frozen/direction-correction.json")["records"]
    need({r["cell"] for r in direction} == {k for k, v in frozen.items() if v["kind"] == "caption"},
         "Caption direction coverage differs")
    for record in direction:
        key = record["cell"]
        need(set(record["conditions"]) == set(MODES), f"Incomplete direction receipt: {key}")
        for mode, metrics in record["conditions"].items():
            same({m: frozen[key][mode][m] for m in metrics}, metrics, f"{key}/{mode}")

    cv = producer(root, "grouped_prediction").cv
    grouped = {}
    for kind in ("class", "caption", "all"):
        sub = [r for r in frozen_analysis["cells"] if kind in ("all", r["kind"])]
        targets = ("classification_top1", "R1_i2t", "R1_t2i", "ARI") if kind == "class" else ("R1_i2t", "R1_t2i")
        for m, t, g in product(("CG", "DG", "spec_eff_rank", "spec_top1_share"), targets, ("dataset", "encoder")):
            grouped[f"{kind}__{m}__{t}__{g}"] = cv(sub, m, t, g)
    same(grouped, read(root / "frozen/grouped-prediction.json"), "frozen grouped prediction")

    def run_id(r):
        m = r["run"]
        return m["backbone"], m["dataset"], m["seed"], m["rank"], m.get("tower", "both")

    controlled = read(root / "controlled/run-summary.json")
    runs = records(root / "controlled/runs")
    indexed = {run_id(r): r for r in runs}
    # The aggregate's order is part of the producer's floating-point reductions.
    same([indexed[run_id(r)] for r in controlled["runs"]], controlled["runs"], "controlled archive")
    need(len(runs) == len(indexed) == controlled["n_runs"] == 90 and
         all([e["epoch"] for e in r["epochs"]] == [1, 2, 3] and
             all(set(e["conditions"]) == set(MODES) for e in r["epochs"]) for r in runs),
         "Expected 90 unique controlled runs with three complete checkpoints")
    ca = producer(root, "controlled_analysis").analyze(controlled)
    same(ca, read(root / "controlled/analysis.json"), "controlled analysis")
    rank16 = {}
    for tower in ("both", "text", "vision"):
        rs = [r for r in runs if run_id(r)[3:] == (16, tower)]
        cs = [e["conditions"] for r in rs for e in r["epochs"]]
        rank16[tower] = {"runs": len(rs), "checkpoints": len(cs),
                         "rho_CG_DG": corr([c["original"]["CG"] for c in cs], [c["original"]["DG"] for c in cs]),
                         "effects": effects(cs, ("classification_top1", "R1_i2t", "R1_t2i", "ARI"))}
    need(all(r["runs"] == 18 and r["checkpoints"] == 54 for r in rank16.values()), "Incomplete rank-16 sites")
    same(rank16, read(root / "controlled/rank16.json"), "rank-matched sensitivity")

    retrieval = read(root / "caption-adaptation/run-summary.json")
    rr = records(root / "caption-adaptation/runs")
    same(rr, retrieval["runs"], "corrected retrieval raw runs")
    need(len(rr) == len({run_id(r) for r in rr}) == retrieval["n_runs"] == 8, "Retrieval run cohort incomplete")
    cc = [e["conditions"] for r in rr for e in r["epochs"]]
    need(len(cc) == 24 and all(set(c) == set(MODES) for c in cc), "Retrieval checkpoint cohort incomplete")
    metrics = ("R1_i2t", "R1_t2i", "R5_i2t", "R5_t2i")
    ra = {"n_runs": len(rr), "n_checkpoints": len(cc),
          "rho_CG_DG": corr([c["original"]["CG"] for c in cc], [c["original"]["DG"] for c in cc]),
          "effects": effects(cc, metrics),
          "predictive": {f"{m}__{t}": corr([c["original"][m] for c in cc], [c["original"][t] for c in cc])
                         for m, t in product(("CG", "DG", "spec_eff_rank", "spec_top1_share"), metrics[:2])},
          "means": {m: float(np.mean([c["original"][m] for c in cc])) for m in ("CG", "DG", *metrics[:2])}}
    same(ra, read(root / "caption-adaptation/analysis.json"), "corrected caption adapter analysis")

    external = read(root / "external/cell-summary.json")
    ec = records(root / "external/cells")
    same(ec, external["cells"], "external raw cells")
    need(len(ec) == len({(x["adapter"], x["dataset"]) for x in ec}) == external["n_cells"] == 20 and
         Counter(x["kind"] for x in ec) == {"class": 12, "caption": 8}, "External cohort incomplete")
    rows = []
    for c in ec:
        a, b = c["adapted"]["original"], c["base"]["original"]
        row = {k: c[k] for k in ("adapter", "dataset", "kind")}
        for k in ("CG", "DG", "classification_top1", "R1_i2t", "R1_t2i", "ARI"):
            if k in a and k in b:
                row.update({f"base_{k}": b[k], f"adapt_{k}": a[k], f"delta_{k}": a[k] - b[k]})
        rows.append(row)
    ea = {"n_cells": len(rows), "by_adapter": {}, "cells": rows}
    for adapter in sorted({r["adapter"] for r in rows}):
        sub = [r for r in rows if r["adapter"] == adapter]
        held = [r for r in sub if r["dataset"] != adapter]
        ea["by_adapter"][adapter] = dict(n_cells=len(sub), heldout_cells=len(held),
            mean_delta_CG=float(np.mean([x["delta_CG"] for x in sub])),
            mean_delta_DG=float(np.mean([x["delta_DG"] for x in sub])),
            heldout_delta_i2t=float(np.mean([x["delta_R1_i2t"] for x in held])))
    for label, sub in (("static_all", rows), ("static_heldout", [r for r in rows if r["dataset"] != "dtd"])):
        ea[label] = {"n": len(sub), **{f"{m}__R1_i2t": corr([r[f"adapt_{m}"] for r in sub],
                    [r["adapt_R1_i2t"] for r in sub]) for m in ("CG", "DG")}}
    same(ea, read(root / "external/analysis.json"), "corrected external analysis")
    for name, n in (("methods", 24), ("siglip", 6), ("rank_b16", 4), ("rank_b32", 4)):
        runs = records(root / f"robustness/{name}/runs")
        arc = read(root / f"robustness/{name}/run-summary.json")
        need(len(runs) == len(arc["runs"]) == arc["n_runs"] == n, f"Incomplete {name} block")
        same(runs, arc["runs"], name)
        check = read(root / f"robustness/{name}/analysis.json")
        ids = {(run_id(r), r["run"].get("method", "lora")) for r in runs}
        checkpoints = [e["conditions"] for r in runs for e in r["epochs"]]
        need(len(ids) == n and all(set(c) == set(MODES) for c in checkpoints),
             f"Incomplete robustness grid: {name}")

        def column(field):
            return [c["original"].get(field) for c in checkpoints]

        def available_corr(x, y):
            a, b = np.asarray(column(x), float), np.asarray(column(y), float)
            valid = np.isfinite(a) & np.isfinite(b)
            if valid.sum() < 3 or np.std(a[valid]) == 0 or np.std(b[valid]) == 0:
                return None
            return corr(a[valid], b[valid])

        readouts = ("classification_top1", "R1_i2t", "R1_t2i", "ARI")
        proxies = ("CG", "DG", "spec_eff_rank", "spec_top1_share")
        observed = dict(n_runs=len(ids), n_checkpoints=len(checkpoints),
                        rho_CG_DG=available_corr("CG", "DG"),
                        effects={}, predictive={}, means={})
        for mode, metric in product(MODES[1:], readouts):
            deltas = [c[mode][metric] - c["original"][metric] for c in checkpoints
                      if c[mode].get(metric) is not None and c["original"].get(metric) is not None]
            if deltas:
                observed["effects"][f"{mode}__{metric}"] = {
                    "mean": float(np.mean(deltas)), "sd": float(np.std(deltas, ddof=0)), "n": len(deltas)}
        for proxy, metric in product(proxies, readouts):
            rho = available_corr(proxy, metric)
            if rho is not None:
                observed["predictive"][f"{proxy}__{metric}"] = rho
        for metric in ("CG", "DG", "spec_eff_rank", *readouts):
            vals = [v for v in column(metric) if v is not None]
            if vals:
                observed["means"][f"original_{metric}"] = float(np.mean(vals))
        same(observed, check, f"{name} robustness aggregate")

    controls = records(root / "norm-matched/cells")
    nm = read(root / "norm-matched/summary.json")
    need(len(controls) == nm["cells"] == 30 and {r["cell"] for r in controls} == set(frozen) and
         nm["direction_seeds"] == list(range(64)), "Incomplete norm-matched matrix")
    summarize = producer(root, "normmatched").summary
    errors = []
    for r in controls:
        need(set(r["targets"]) == {"mean_center", "gap_project"}, "Missing norm-matched target")
        for t in r["targets"].values():
            directions = t["directions"]
            same([d["seed"] for d in directions], nm["direction_seeds"], "placebo directions")
            for d in directions:
                errors.extend(d["matching"].values())
            for k, base in r["original"].items():
                effect = t["targeted_readouts"][k] - base
                same(effect, t["targeted_effects"][k], "targeted effect")
                for d in directions:
                    same(d["readouts"][k] - base, d["effects"][k], "placebo effect")
                same(summarize(effect, [d["effects"][k] for d in directions]), t["summaries"][k], "cell distribution")
    need(len(errors) == 2 * nm["placebo_conditions"] == 7680 and nm["targeted_conditions"] == 60,
         "Wrong norm-matched design size")
    for field in ("max_displacement_error", "max_unit_norm_error"):
        need(max(row[field] for row in errors) == nm[field] and nm[field] < 2e-11, f"Failed {field}")
    for kind in ("class", "caption", "all"):
        rs = [r for r in controls if kind in ("all", r["kind"])]
        ms = set.intersection(*(set(r["original"]) for r in rs))
        for mode in ("mean_center", "gap_project"):
            summary = {}
            for m in ms:
                v = [float(np.mean([r["targets"][mode]["directions"][i]["effects"][m] for r in rs])) for i in range(64)]
                t = float(np.mean([r["targets"][mode]["targeted_effects"][m] for r in rs]))
                summary[m] = dict(n_cells=len(rs), **summarize(t, v), direction_mean_effects=v)
            same(summary, nm["groups"][kind][mode], f"{kind}/{mode} distribution")
    return dict(frozen_cells=30, corrected_frozen_caption_conditions=60, controlled_runs=90,
                controlled_checkpoints=270, rank16_checkpoints_per_site=54, robustness_runs=46,
                caption_adaptation_runs=8, caption_adaptation_checkpoints=24, external_cells=20,
                normmatched_targets=60, normmatched_placebos=3840)


def target_replay(root):
    hits = read(root / "hit-counts.json")
    aggregate = read(root / "aggregate.json")
    n = hits["query_count"]
    fit_freeze = read(root / "fit-freeze.json")
    need(n == aggregate["query_count"] == 256 and digest(root / "fit-freeze.json") == aggregate["fit_freeze_sha256"],
         "Target query or fit freeze mismatch")
    same(hits["reference_count"], aggregate.get("caption_count", aggregate.get("reference_count")), "gallery size")
    grid = {(r["seed"], r["arm"]): r["hits"] for r in hits["cells"]}
    order = list(product(range(3), GAMMA + CONTROLS))
    need(len(grid) == len(hits["cells"]) == 21 and set(grid) == set(order), "Target arm grid incomplete")
    same(aggregate["cells"], [dict(seed=s, arm=a, hits=grid[s, a], r1=grid[s, a] / n) for s, a in order], "target recalls")
    by_seed = []
    for s in range(3):
        clocks = []
        for a in GAMMA + CONTROLS:
            name = f"S{s}-{a}.json"
            p = root / "fit" / name
            r = read(p)
            need(r["seed"] == s and r["arm"] == a and r["actual_trainables"] == 245760
                 and sum(r["block_trainables"].values()) == 245760 and r["frozen_parameters_unchanged"]
                 and r["clock"]["update_count"] == r["clock"]["planned_updates"] == 32,
                 f"Mismatched fit budget: {p.name}")
            if isinstance(fit_freeze["cells"][0], list):
                expected = dict(fit_freeze["cells"])[name]
            else:
                expected = {x["receipt"]: x["sha256"] for x in fit_freeze["cells"]}[name]
            same(digest(p), expected, name)
            clocks.append({k: r["clock"][k] for k in ("example_sequence", "microbatches_per_update", "lr_used")})
            need(type(grid[s, a]) is int and 0 <= grid[s, a] <= n, f"Invalid hits: {s}/{a}")
        need(all(c == clocks[0] for c in clocks), "Training clocks differ within seed")
        contrasts = {a: {b: (grid[s, a] - grid[s, b]) / n for b in CONTROLS} for a in GAMMA}
        by_seed.append(dict(seed=s, gamma_deltas=contrasts,
                            worst_gamma_delta_vs_uniform=min(r["uniform"] for r in contrasts.values())))
    same(by_seed, aggregate["by_seed"], "target paired differences")
    return {"cells": len(grid), "queries": n, "references": hits["reference_count"],
            "worst_source_minus_uniform_pp": [100 * x["worst_gamma_delta_vs_uniform"] for x in by_seed]}


def score_projected(record):
    rows = record["rows"]
    result = {}
    for k in ("accuracy", "exact_match", "token_f1", "yes_no_accuracy"):
        if k in rows[0]:
            result[k] = statistics.mean(r[k] for r in rows if r[k] is not None)
    if "ngram_counts" in rows[0]:
        counts = [tuple(map(sum, zip(*(r["ngram_counts"][i] for r in rows)))) for i in range(4)]
        ratios = [a / b if b else 0 for a, b in counts]
        result["bleu4"] = math.exp(sum(map(math.log, ratios)) / 4) if min(ratios) else 0.0
    return result


def historical_tables(root):
    result = {}
    for block in ("benchmark", "qwen", "heldout", "vqa-rad", "caption", "instruction"):
        out = {}
        for path in sorted((root / block / "rows").glob("*.json")):
            d = read(path)
            need(d["n"] == len(d["rows"]) > 0, f"Wrong scored row count: {path.name}")
            metrics = score_projected(d)
            for k in d["archived_metrics"].keys() & metrics.keys():
                same(metrics[k], d["archived_metrics"][k], f"{path.name}.{k}")
            out.setdefault(d["task"], {})[d["arm"]] = {**d["archived_metrics"], **metrics}
        need(out, f"Empty historical block: {block}")
        result[block] = out
    return result


def p3_replay(root):
    import numpy as np
    from scipy.stats import kendalltau

    targets = {name: target_replay(root / "public-retrieval" / name) for name in ("vizwiz", "textcaps")}
    h = root / "historical"
    tables = historical_tables(h)
    same(tables, read(h / "scored-tables.json"), "historical scored tables")
    paths = {block: {task: len(arms) for task, arms in rows.items()} for block, rows in tables.items()}
    same(paths, {
        "benchmark": {t: 3 for t in TASKS if t != "marinelife"},
        "qwen": {t: 2 for t in ("coco", "flickr", "mmbench", "pope", "scienceqa", "vqarad")},
        "heldout": {"caption": 3, "instruction": 3}, "vqa-rad": {"vqa-rad": 3},
        "caption": {"caption": 3}, "instruction": {"instruction": 3}
    }, "historical task coverage")
    bench = h / "benchmark/rows"
    corrections = read(h / "allocation-contrasts.json")
    labels = ("Flickr30k", "COCO5k", "POPE", "MarineLife", "iNaturalist", "DTD", "ScienceQA", "MMBench")
    same([r["dataset"] for r in corrections], [*labels, "VQA-RAD (F1)", "VQA-RAD (exact)"], "contrast coverage")
    rng = np.random.default_rng(20261113)
    for task, row in zip(TASKS, corrections):
        # Consume the original draw layout without reintroducing the withdrawn scores.
        indices = rng.integers(0, 100, (20000, 100))
        if task == "marinelife":
            need(row["status"] == "withdrawn" and all(row[k] is None for k in ("delta_pp", "lo", "hi", "n")),
                 "Invalid MarineLife classification must not be reported")
            continue
        metric = "contrast_f1" if task in ("flickr30k", "coco5k") else ("accuracy" if task == "pope" else "contrast_accuracy")
        a, b = ([r[metric] for r in read(bench / f"{task}-{arm}.json")["rows"]] for arm in ("5", "6"))
        if task == "pope":
            same(a, b, "POPE paired correctness vectors")
            same([round(100 * tables["benchmark"][task][arm]["accuracy"]) for arm in ("base", "5", "6")],
                 [86, 87, 87], "POPE counts")
        delta = np.array(a) - np.array(b)
        ci = np.quantile(delta[indices].mean(1) * 100, [.025, .975])
        same([int(len(delta)), float(100 * delta.mean()), *map(float, ci)],
             [row[k] for k in ("n", "delta_pp", "lo", "hi")], task)
    vqa = read(h / "vqa-rad/equivalence.json")
    for arm, scores in tables["vqa-rad"]["vqa-rad"].items():
        for k in ("accuracy", "token_f1", "yes_no_accuracy"):
            same(scores[k], vqa["arms"][arm][k], f"VQA {arm} {k}")
    vqa_arrays = {}
    for arm in ("base", "5", "6"):
        rows = read(h / f"vqa-rad/rows/vqa-rad-{arm}.json")["rows"]
        vqa_arrays[arm] = {"correct": np.array([r["accuracy"] for r in rows], dtype=float),
                           "f1": np.array([r["token_f1"] for r in rows], dtype=float)}
    rng = np.random.default_rng(vqa["meta"]["rng_seed"])
    compare = producer(root, "paired_bootstrap").vqa_contrast
    for a, b in (("base", "5"), ("base", "6"), ("5", "6")):
        same(compare(vqa_arrays[a], vqa_arrays[b], rng, vqa["meta"]["n_boot"]),
             vqa["vqa_equivalence"]["contrasts"][f"{a}_minus_{b}"], f"VQA paired bootstrap {a}/{b}")
    for row, k in zip(corrections[-2:], ("token_f1", "accuracy")):
        scores = tables["vqa-rad"]["vqa-rad"]
        same(100 * (scores["5"][k] - scores["6"][k]), row["delta_pp"], f"VQA {k} difference")
        same([100 * x for x in vqa["rank5_equivalence"][k]["vs_r6_ci95"]], [row["lo"], row["hi"]],
             f"VQA {k} interval reference")

    pilot = read(root / "stability/pact-pilot.json")
    ref = read(root / "stability/reference-batches.json")
    panel = {f"n={r['n']}/draw={r['draw']}": [r["ranks"][b] for b in pilot["blocks"]] for r in ref["conditions"]}
    need(len(panel) == pilot["n_protocols"] == 4, "PACT pilot panel incomplete")
    taus = {}
    for a, b in combinations(panel, 2):
        tau = float(kendalltau(panel[a], panel[b], variant="b").statistic)
        need(math.isfinite(tau), "Tied panel has undefined Kendall tau-b; do not assign a stability score")
        taus[frozenset((a, b))] = tau
    need(len(pilot["pairs"]) == len(taus), "PACT pair evidence incomplete")
    for p in pilot["pairs"]:
        same(taus[frozenset((p["protocol_a"], p["protocol_b"]))], p["kendall_tau"], "PACT pair")
    for reduce, name in ((min, "min"), (statistics.mean, "mean"), (max, "max")):
        same(reduce(taus.values()), pilot[f"pact_{name}"], f"PACT {name}")
    for r in pilot["leave_one_out"]:
        same(min(v for p, v in taus.items() if r["dropped"] not in p), r["pact_min_if_dropped"], "PACT leave-one-out")
    archive = read(root / "allocation/comparisons.json")
    runs = records(root / "allocation/runs")
    need(len(runs) == archive["n_runs_total"] == 57 and len({(r["plan"], r["seed"]) for r in runs}) == 57,
         "Incomplete matched-budget archive")
    for p, result in archive["per_plan"].items():
        cohort = [r for r in runs if r["plan"] == p]
        valid = [r for r in cohort if r["ok"] and r["delta_E"] is not None]
        need(len(cohort) == result["delta_E"]["n"] + result["n_failed"] and
             all(r["n_trainable_params_measured"] == archive["budget_params"] for r in valid),
             f"Run coverage or budget mismatch: {p}")
        for field in ("delta_E", "delta_E_per_sample_mean", "loss_first", "loss_last", "peak_gpu_gib"):
            vals = [r[field] for r in valid if r.get(field) is not None and math.isfinite(r[field])]
            described = {"n": len(vals)}
            if vals:
                described.update(mean=statistics.mean(vals), sd=statistics.stdev(vals) if len(vals) > 1 else 0.,
                                 median=statistics.median(vals), min=min(vals), max=max(vals))
            same(described, result[field], f"matched-budget {p}.{field}")
    return dict(public_retrieval=targets, historical_scored_records=sum(sum(r.values()) for r in paths.values()),
                pact_protocols=len(panel), pact_min=min(taus.values()), matched_budget_runs=len(runs))


def verify_track(directory, track=None):
    manifest = verify_manifest(directory, track)
    track = manifest["track"]
    body = a4_replay if track == "a4" else p3_replay
    return {"status": "PASS", "track": track, "files": len(manifest["files"]) + 1, **body(directory)}



if __name__ == "__main__":
    try:
        print(json.dumps(verify_track(Path(__file__).resolve().parent), indent=2))
    except (ValueError, OSError, KeyError, TypeError, IndexError) as exc:
        raise SystemExit(f"FAIL: {exc}") from exc
