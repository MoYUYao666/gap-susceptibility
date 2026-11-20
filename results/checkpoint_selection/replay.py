"""Recompute archived checkpoint comparisons without loading a model."""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
from statistics import mean

import numpy as np

import algorithms as alg


HERE = Path(__file__).resolve().parent
RUN_FIELDS = ("backbone", "dataset", "tower", "rank", "seed", "split_seed")
DATASETS = ("dtd", "inat", "nksid")
TOWERS = ("both", "text", "vision")
SCHEDULE_SEEDS = (45, 46, 47, 48)
WINDOWS = {"early": (1, 2, 3), "late": (4, 5, 6), "all": tuple(range(1, 7))}
PRIVATE_COVERAGE = ("local_archive_overlap_identical", "local_archive_version_conflicts",
                    "canonical_archive_only_runs")


def require(test, label):
    if not test:
        raise ValueError(label)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads((HERE / path).read_bytes())


def same(actual, expected, path="root"):
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and actual.keys() == expected.keys(), f"Different keys at {path}")
        for k in expected:
            same(actual[k], expected[k], f"{path}.{k}")
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), f"Different lengths at {path}")
        for i, (a, b) in enumerate(zip(actual, expected)):
            same(a, b, f"{path}[{i}]")
    else:
        if type(expected) is float:
            ok = type(actual) in (int, float) and math.isclose(actual, expected, rel_tol=1e-11, abs_tol=1e-12)
        else:
            ok = type(actual) is type(expected) and actual == expected
        require(ok, f"Different value at {path}: {actual!r} != {expected!r}")


def compare_csv(name, rows, key_fields):
    """Compare an exact typed schema and a complete, unique keyed row set."""
    schema = rows[0]
    index = {}
    for row in rows:
        key = tuple(row[k] for k in key_fields)
        require(key not in index, f"Duplicate computed key in {name}: {key}")
        index[key] = row
    with (HERE / name).open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames is not None and len(reader.fieldnames) == len(schema)
                and set(reader.fieldnames) == set(schema), f"Unexpected CSV header: {name}")
        for row in reader:
            require(None not in row and all(v is not None for v in row.values()),
                    f"Malformed CSV row: {name}:{reader.line_num}")
            values = {k: type(schema[k])(v) for k, v in row.items()}
            key = tuple(values[k] for k in key_fields)
            require(key in index, f"Unexpected or duplicate CSV key in {name}: {key}")
            same(values, index.pop(key), f"{name}:{reader.line_num}")
    require(not index, f"Missing {len(index)} CSV keys in {name}")


def provenance_hashes():
    provenance = read("provenance.json")
    hashes = {}
    for row in provenance["files"]:
        path = row["destination"]
        target = (HERE / path).resolve()
        require(target.is_relative_to(HERE.resolve()) and path not in hashes,
                f"Outside or duplicate provenance destination: {path}")
        raw = target.read_bytes()
        require(sha(raw) == row["published_sha256"], f"Source integrity failure: {path}")
        hashes[path] = row["published_sha256"]
    return provenance, hashes


def contrastive(registry, expected, hashes):
    specs = {name: (dirs, backbone, ranks, cal, test)
             for name, dirs, backbone, ranks, cal, test in alg.SPECS}
    require(registry.keys() == expected.keys() == specs.keys(), "Missing or extra contrastive blocks")
    blocks, members, selections, margins, preferences = {}, {}, {}, [], []
    for name, (dirs, backbone, ranks, cal_seeds, test_seeds) in specs.items():
        spec = registry[name]
        same(spec["calibration_seeds"], cal_seeds, f"{name}.calibration_seeds")
        same(spec["evaluation_seeds"], test_seeds, f"{name}.evaluation_seeds")
        rows, cells = [], set()
        for item in spec["records"]:
            path, member = item["path"], item["member"]
            require(member not in members and path in hashes, f"Duplicate or unbound member: {member}")
            run = alg.parse_run(read(path), member)
            m = run["meta"]
            cell = tuple(m[k] for k in RUN_FIELDS[1:5])
            require(cell not in cells and m["backbone"] == backbone and m["split_seed"] == 2026,
                    f"Invalid run cell in {name}: {member}")
            suffix = "" if m["tower"] == "both" else "__" + m["tower"]
            filename = f"{backbone}__{m['dataset']}__r{m['rank']}__s{m['seed']}{suffix}.json"
            require(Path(member).name == Path(path).name == filename,
                    f"Record, archive member and run metadata differ: {member}")
            require(Path(member).parent.name in dirs,
                    f"Archive member is in the wrong block: {member}")
            cells.add(cell)
            rows.append(run)
            members[member] = (path, hashes[path])
        require(cells == set(itertools.product(DATASETS, TOWERS, ranks, cal_seeds + test_seeds)),
                f"Missing or extra run cells in {name}")
        cal = [r for r in rows if r["meta"]["seed"] in cal_seeds]
        test = [r for r in rows if r["meta"]["seed"] in test_seeds]
        blocks[name] = (rows, cal, test)
        for r in rows:
            require(np.array_equal(r["raw"][:, 0], r["raw"][:, 1]),
                    f"Readout alias failure: {r['member']}")
        gaps = [float(r["readouts"].mean(axis=1).max() - r["readouts"].mean(axis=1)[-1]) for r in test]
        measured = {
            "n_runs": len(rows), "n_cal": len(cal), "n_test": len(test),
            "data_split_seeds": sorted({r["meta"]["split_seed"] for r in rows}),
            "calibration_seeds": sorted({r["meta"]["seed"] for r in cal}),
            "test_seeds": sorted({r["meta"]["seed"] for r in test}),
            "oracle_headroom": {
                "mean": float(np.mean(gaps)),
                "within_delta": [{"delta": d, "n_within": sum(g <= d + alg.TOL for g in gaps),
                                  "n": len(gaps)} for d in alg.DELTAS],
            },
            "proxies": {},
        }
        for pi, proxy in enumerate(alg.PROXIES):
            sign = alg.choose_sign(cal, pi)
            orientation = "higher" if sign == 1 else "lower"
            losses, coords, epochs = [], [], []
            for r in test:
                chosen = alg.select_index(r, pi, sign)
                y = r["readouts"].mean(axis=1)
                v = r["readouts"][-1, [0, 2, 3]] - r["readouts"][chosen, [0, 2, 3]]
                loss = float(y[-1] - y[chosen])
                same(loss, float(v @ alg.WEIGHTS), "Weighted component loss")
                losses.append(loss)
                coords.append(v)
                epochs.append(chosen + 1)
                scores = sign * r["proxies"][:, pi]
                key = (r["member"], proxy)
                require(key not in selections, f"Duplicate selection: {key}")
                selections[key] = {
                    "block": name, "member": r["member"], "proxy": proxy, "orientation": orientation,
                    **{k: r["meta"][k] for k in RUN_FIELDS},
                    "selected_epoch": chosen + 1, "last_epoch": len(y),
                    "proxy_tie_count_at_max": int(np.count_nonzero(scores == scores.max())),
                    "loss": loss, "gain": -loss, "classification_loss": float(v[0]),
                    "R1_t2i_loss": float(v[1]), "ARI_clipped_loss": float(v[2]),
                    "last_utility": float(y[-1]), "selected_utility": float(y[chosen]),
                    "oracle_headroom": float(y.max() - y[-1]),
                }
            m = [alg.partition_loss(losses, d) for d in alg.DELTAS]
            q = alg.preference_summary(coords)
            measured["proxies"][proxy] = {
                "sign": orientation, "original_loss": alg.cluster_ci(losses, test),
                "margin_sensitivity": m, "preference_sensitivity": q,
                "selected_last_count": epochs.count(3),
            }
            margins.extend({"block": name, "proxy": proxy, **v} for v in m)
            preferences.append({
                "block": name, "proxy": proxy, "n": len(test),
                **dict(zip(alg.COORDINATES, q["component_mean_loss"])),
                "original_mean_loss": q["original_mean_loss"],
                "equal_distinct_mean_loss": q["equal_distinct_mean_loss"],
                "full_simplex_min": q["full_simplex_range"][0],
                "full_simplex_max": q["full_simplex_range"][1],
                "balanced_simplex_min": q["balanced_simplex_range"][0],
                "balanced_simplex_max": q["balanced_simplex_range"][1],
            })
        same(measured, expected[name], f"blocks.{name}")
    compare_csv("selections.csv", list(selections.values()), ("member", "proxy"))
    compare_csv("margin_sensitivity.csv", margins, ("block", "proxy", "delta"))
    compare_csv("preference_sensitivity.csv", preferences, ("block", "proxy"))
    return blocks, members, selections


def check_coverage(blocks, members, selections, target, workspace):
    runs = [r for rows, _, _ in blocks.values() for r in rows]
    coverage = {
        "n_runs": len(runs), "n_checkpoints": sum(len(r["raw"]) for r in runs),
        "n_test_runs": sum(len(test) for _, _, test in blocks.values()), "n_blocks": len(blocks),
        "n_test_proxy_decisions": len(selections),
        "top1_equals_R1_i2t_exactly_at_n_checkpoints":
            sum(int(np.count_nonzero(r["raw"][:, 0] == r["raw"][:, 1])) for r in runs),
        "negative_ARI_clipped_at_n_checkpoints":
            sum(int(np.count_nonzero(r["raw"][:, 3] < 0)) for r in runs),
    }
    public_keys = set(coverage)
    require(set(target) in (public_keys, public_keys | set(PRIVATE_COVERAGE)), "Unexpected coverage fields")
    same(coverage, {k: target[k] for k in coverage}, "Coverage from published records")
    if not set(PRIVATE_COVERAGE).issubset(target):
        return "private overlap inventory not distributed"
    private = [target[k] for k in PRIVATE_COVERAGE]
    require(all(type(n) is int and n >= 0 for n in private) and sum(private) == len(runs),
            "Invalid inherited archive/private coverage accounting")
    if workspace is None:
        return "private overlap/conflict/absence counts are reference-only (sum checked)"
    observed = [0, 0, 0]
    workspace = (workspace / "outputs").resolve()
    for member, (_, digest) in members.items():
        local = (workspace / member).resolve()
        require(local.is_relative_to(workspace), f"Private comparison path escapes outputs: {member}")
        if not local.is_file():
            observed[2] += 1
        else:
            observed[0 if sha(local.read_bytes()) == digest else 1] += 1
    same(observed, private, "Private overlap, conflicts and archive-only counts")
    return "private overlap/conflict/absence counts replayed against supplied workspace"


def compare_matched(blocks, selections, target):
    primary, _, test = blocks["b32_primary"]
    b16 = [r for name, (rows, _, _) in blocks.items() if name.startswith("b16_") for r in rows]
    pairs = alg.match_records(primary, b16)
    test_members = {r["member"] for r in test}
    heldout = [(a, b) for a, b in pairs if a["member"] in test_members]
    rows, ranks, interaction = [], {}, {}
    for rank in (8, 16, 32, 64):
        keep = [(a, b) for a, b in heldout if a["meta"]["rank"] == rank]
        require(len(keep) == 18, f"Incomplete held-out matching for rank {rank}")
        ranks[str(rank)] = {}
        for p in alg.PROXIES:
            diffs = []
            for a, b in keep:
                am, bm = a["member"], b["member"]
                m = a["meta"]
                x, y = selections[(am, p)]["loss"], selections[(bm, p)]["loss"]
                diffs.append(y - x)
                rows.append({"rank": rank, "proxy": p, "dataset": m["dataset"], "tower": m["tower"],
                             "seed": m["seed"], "b32_member": am, "b16_member": bm,
                             "b32_loss": x, "b16_loss": y, "b16_minus_b32": y - x})
            ranks[str(rank)][p] = {"mean_b16_minus_b32_loss": float(np.mean(diffs)), "n_pairs": len(keep)}
    for p in alg.PROXIES:
        groups = {rank: {(r["dataset"], r["tower"], r["seed"]): r["b16_minus_b32"]
                         for r in rows if r["rank"] == rank and r["proxy"] == p} for rank in (32, 64)}
        require(groups[32].keys() == groups[64].keys(), "Incomplete rank interaction")
        vals = [groups[64][k] - groups[32][k] for k in sorted(groups[32])]
        interaction[p] = {"mean_difference_of_differences": float(np.mean(vals)),
                          "n_quadruples": len(vals), "inference": "descriptive only"}
    same({"n_all_matched_pairs": len(pairs), "n_test_matched_pairs": len(heldout),
          "matching_fields": alg.MATCH_FIELDS, "rank_by_proxy": ranks,
          "rank64_minus_rank32": interaction}, target, "Matched backbone/rank summary")
    compare_csv("matched.csv", rows, ("rank", "proxy", "dataset", "tower", "seed"))


def compare_vqa(registry, hashes):
    target = read("reference/vqa.json")["datasets"]
    require(registry.keys() == target.keys() == {"chartqa", "textvqa", "vqav2"}, "Incomplete VQA tasks")
    count = 0
    for task, spec in registry.items():
        rows, cells = [], set()
        for item in spec:
            require(item["path"] in hashes, f"Unbound VQA record: {item['path']}")
            doc = read(item["path"])
            m = doc["run"]
            rank, seed = m["rank"], m["seed"]
            require(type(rank) is int and type(seed) is int and (rank, seed) not in cells,
                    f"Invalid or duplicate VQA cell: {task}/{rank}/{seed}")
            cells.add((rank, seed))
            # The older TextVQA schema has no dataset field; its roster binds the task.
            if task != "textvqa" or "dataset" in m:
                same(m["dataset"], task, "VQA task")
            filename = f"qwen2vl__{task}__r{rank}__s{seed}__both.json"
            require(Path(item["path"]).name == Path(item["member"]).name == filename,
                    f"VQA record/member identity mismatch: {filename}")
            same({k: m[k] for k in ("train", "test", "epochs", "tower")},
                 {"train": 80, "test": 12, "epochs": 3, "tower": "both"}, f"VQA metadata: {filename}")
            same([e["epoch"] for e in doc["epochs"]], [1, 2, 3], "VQA checkpoints")
            em = [float(e["em"]) for e in doc["epochs"]]
            require(all(0 <= v <= 1 for v in em), f"Invalid VQA exact-match scale: {filename}")
            rows.append({"rank": rank, "seed": seed, "em": em,
                         "last_oracle": bool(np.isclose(em[-1], max(em))), "gap": float(max(em)-em[-1])})
        require(cells == set(itertools.product((8, 16, 32, 64), SCHEDULE_SEEDS)), f"Incomplete VQA grid: {task}")
        ranks = {}
        for rank in (8, 16, 32, 64):
            rr = [r for r in rows if r["rank"] == rank]
            n, good = len(rr), sum(r["last_oracle"] for r in rr)
            ranks[str(rank)] = {"n": n, "last_oracle": good, "last_oracle_fraction": good/n,
                                "mean_gap": float(np.mean([r["gap"] for r in rr]))}
        same({"n_runs": len(rows), "ranks": ranks, "runs": rows}, target[task], f"VQA {task}")
        count += len(rows)
    return count


def compare_schedule(primary, members, hashes):
    runs, cal, _ = primary
    # The historical schedule pin maximizes the sum of utilities on the primary calibration grid.
    def utility(e):
        r = e["conditions"]["original"]
        return (sum(r[k] / 100 for k in alg.READOUTS[:3]) + min(max(r["ARI"], 0), 1)) / 4

    def distinct(e):
        r = e["conditions"]["original"]
        return (r["classification_top1"] / 100 + r["R1_t2i"] / 100 + min(max(r["ARI"], 0), 1)) / 3

    calibration = [read(members[r["member"]][0])["epochs"] for r in sorted(cal, key=lambda r: r["member"])]
    signs = {}
    for p in alg.PROXIES:
        scores = {s: sum(utility(max(eps, key=lambda e: s * e["conditions"]["original"][p]))
                         for eps in calibration) for s in (1, -1)}
        signs[p] = 1 if scores[1] >= scores[-1] else -1

    anchor = {r["meta"]["seed"]: r for r in runs if
              (r["meta"]["dataset"], r["meta"]["rank"], r["meta"]["tower"]) == ("inat", 8, "text")}
    require(set(anchor) == set(SCHEDULE_SEEDS), "Incomplete historical schedule anchors")
    schedule = read("schedule_summary.json")
    rows = []
    for seed in SCHEDULE_SEEDS:
        path = f"records/schedule/seed{seed}.json"
        raw = (HERE / path).read_bytes()
        raw_sha = sha(raw)
        same(raw_sha, hashes[path], "Published schedule source hash")
        doc = json.loads(raw)
        ref_path, ref_sha = members[anchor[seed]["member"]]
        ref_raw = (HERE / ref_path).read_bytes()
        same(sha(ref_raw), ref_sha, "Published historical prefix source hash")
        baseline = json.loads(ref_raw)
        meta = doc["run"]
        same({k: meta[k] for k in (*alg.MATCH_FIELDS, "backbone")},
             {**{k: baseline["run"][k] for k in (*alg.MATCH_FIELDS, "backbone")}, "epochs": 6},
             f"Schedule metadata: seed {seed}")
        eps, old = doc["epochs"], baseline["epochs"]
        same([e["epoch"] for e in eps], list(WINDOWS["all"]), f"Six checkpoints: seed {seed}")
        same([e["epoch"] for e in old], list(WINDOWS["early"]), f"Historical prefix: seed {seed}")
        for e in eps:
            r = e["conditions"]["original"]
            values = [e["train_loss"], e["seconds"], *(r[k] for k in (*alg.READOUTS, *alg.PROXIES))]
            require(all(type(v) in (int, float) and math.isfinite(v) for v in values),
                    f"Invalid schedule metric: seed {seed}, epoch {e['epoch']}")
            alg.normalize_readout([r[k] for k in alg.READOUTS])
        drifts = {"train_loss": max(abs(a["train_loss"] - b["train_loss"]) for a, b in zip(eps[:3], old))}
        for k in (*alg.READOUTS, *alg.PROXIES):
            drifts[k] = max(abs(a["conditions"]["original"][k] - b["conditions"]["original"][k])
                            for a, b in zip(eps[:3], old))
        alias = all(e["conditions"]["original"]["classification_top1"] ==
                    e["conditions"]["original"]["R1_i2t"] for e in eps)
        windows = {}
        for name, steps in WINDOWS.items():
            subset = [eps[i - 1] for i in steps]
            last = subset[-1]
            selections = {}
            for proxy, sign in signs.items():
                chosen = max(subset, key=lambda e: sign * e["conditions"]["original"][proxy])
                selections[proxy] = {"chosen": chosen["epoch"], "gain_equal_four": utility(chosen) - utility(last),
                                     "gain_equal_distinct": distinct(chosen) - distinct(last) if alias else None}
            windows[name] = {
                "steps": list(steps), "last_equal_four": utility(last),
                "oracle_headroom_equal_four": max(map(utility, subset)) - utility(last),
                "oracle_headroom_equal_distinct": max(map(distinct, subset)) - distinct(last) if alias else None,
                "proxy": selections,
            }
        rows.append({"seed": seed, "raw_sha256": raw_sha,
                     "forward_prefix": {"exact": all(v == 0 for v in drifts.values()), "max_abs_by_field": drifts},
                     "classification_and_i2t_equal": alias, "windows": windows})
    evaluation = [r for r in rows if r["seed"] in (47, 48)]
    eval_means = {name: {
        "mean_gain_equal_four": {p: mean(r["windows"][name]["proxy"][p]["gain_equal_four"] for r in evaluation)
                                 for p in alg.PROXIES},
        "mean_oracle_headroom_equal_four": mean(r["windows"][name]["oracle_headroom_equal_four"] for r in evaluation),
    } for name in WINDOWS}
    same({"calibration_directions": signs, "seeds": rows,
          "eval_seed_count": len(evaluation), "eval_means": eval_means}, schedule, "Schedule summary")
    return len(rows)


def compare_fallback(cal, test):
    target = read("reference/empirical_fallback.json")["proxies"]
    measured = {}
    for pi, proxy in enumerate(alg.PROXIES):
        xs = np.array([x for r in cal for x in r["proxies"][:, pi]])
        ys = np.array([x for r in cal for x in r["readouts"].mean(axis=1)])
        slope, intercept = np.polyfit(xs, ys, 1)
        epsilon = float(np.abs(slope * xs + intercept - ys).max())
        selected, risks, diffs, last = 0, [], [], []
        for r in test:
            pred = slope * r["proxies"][:, pi] + intercept
            y = r["readouts"].mean(axis=1)
            switch = bool(pred.max() - pred[-1] > 2 * epsilon)
            selected += switch
            chosen = y[int(np.argmax(pred))] if switch else y[-1]
            risks.append(chosen < y[-1] - 1e-12)
            diffs.append(chosen - y[-1])
            last.append(y[-1])
        measured[proxy] = {"slope": float(slope), "intercept": float(intercept), "epsilon": epsilon,
                           "n_test": len(test), "coverage": selected / len(test),
                           "risk_worse_than_last": float(np.mean(risks)), "mean_diff": float(np.mean(diffs)),
                           "mean_last": float(np.mean(last))}
    same(measured, target, "Empirical fallback")


def main(workspace=None):
    provenance, hashes = provenance_hashes()
    required = {"registry.json", "summary.json", "schedule_summary.json", "selections.csv",
                "matched.csv", "margin_sensitivity.csv", "preference_sensitivity.csv",
                "reference/reanalysis.json", "reference/vqa.json", "reference/empirical_fallback.json"}
    require(required <= hashes.keys(), f"Missing provenance entries: {sorted(required - hashes.keys())}")
    registry, expected = read("registry.json"), read("summary.json")
    same(registry["archive_sha256"], provenance["archive_sha256"], "Canonical archive identity")
    blocks, members, selections = contrastive(registry["blocks"], expected["blocks"], hashes)
    coverage_scope = check_coverage(blocks, members, selections, expected["coverage"], workspace)
    definitions = expected["definitions"]
    for name, value in (("coordinates", alg.COORDINATES), ("original_effective_weights", alg.WEIGHTS.tolist()),
                        ("balanced_preference_min_weight", 0.2), ("deltas", alg.DELTAS),
                        ("numeric_tolerance", alg.TOL)):
        same(value, definitions[name], f"Numeric definition {name}")
    compare_matched(blocks, selections, expected["matched_backbone_rank"])
    primary = blocks["b32_primary"]
    y = [r["readouts"].mean(axis=1) for r in primary[0]]
    reanalysis = read("reference/reanalysis.json")["aggregate"]
    same(sum(not np.all(np.diff(a) >= 0) for a in y), reanalysis["n_nonmonotone"], "Reanalysis nonmonotone count")
    same(sum(bool(np.isclose(a[-1], a.max(), atol=1e-12, rtol=0)) for a in y),
         reanalysis["n_last_oracle"], "Reanalysis last-oracle count")
    same(float(np.mean([a.max() - a[-1] for a in y])), reanalysis["gap"]["mean"], "Reanalysis mean oracle gap")
    vqa = compare_vqa(registry["vqa"], hashes)
    schedule = compare_schedule(primary, members, hashes)
    compare_fallback(*primary[1:])
    print(f"PASS: {len(members)} contrastive trajectories, {vqa} VQA trajectories, {schedule} schedule reruns; "
          "all four CSVs, matched interactions, calibration and empirical fallback replayed.")
    print(f"SCOPE: {coverage_scope}.")
    print("SCOPE: inherited reanalysis is reference-only except the three replayed primary aggregates.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, help="Also check the private archive-overlap counts in place.")
    main(parser.parse_args().workspace_root)
