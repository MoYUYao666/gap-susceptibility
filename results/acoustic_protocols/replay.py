"""Read-only replay of archived benchmark or retrieval records."""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from itertools import product
import json
import math
from pathlib import Path
import re
import statistics as st


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(blob):
    return sha256(blob).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def packed(data):
    return (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def summary_stats(values):
    return {"n": len(values), "mean": st.mean(values),
            "sample_sd": st.stdev(values) if len(values) > 1 else None}


def order_regression():
    # The near-tie and fixed-list cases use orthogonal unit axes;
    # each score/field pair has a unit-vector completion.
    def shift(score, field, dose, projection=0):
        return (score-dose*projection) / math.sqrt(1-2*dose*field+dose*dose)

    score, field, q = .4, .3, .2
    h = 1e-4
    plus, minus = [shift(score, field, a, q) for a in (h,-h)]
    first = field*score-q
    second = (1.5*field**2-.5)*score-q*field
    require(abs((plus-minus)/(2*h)-first) < 1e-8, "Wrong signed first-order coefficient")
    require(abs((plus+minus-2*score)/(2*h*h)-second) < 1e-7, "Wrong second-order cross term")
    require(shift(.6,-.5,.001) < shift(.59999,.5,.001), "Near-tie reversal disappeared")
    baseline = (.5,.4,.3,.2,.1,0.)
    shifted = tuple(s+m for s,m in zip(baseline, (0,0,0,0,0,.8)))
    require(shifted[:5] == baseline[:5] and shifted[5] > max(shifted[:5]), "Fixed-list counterexample failed")
    return {"synthetic_only": True, "signed_terms_checked": True,
            "near_tie_can_flip": True, "fixed_list_does_not_certify_all_class_winner": True}


def sonar(root):
    records = root / "records"
    scope = read(root / "protocols.json")
    benchmarks = {}
    files = scope["benchmark_protocols"]
    for name, spec in files.items():
        src = read(records / "benchmark" / (name + ".json"))
        meta = src["meta"]
        n = meta.get("n_eval", meta.get("n_images"))
        require(n == spec["evaluation_images"], f"Wrong benchmark denominator: {name}")
        if "per_class" in meta:
            require(sum(meta["per_class"].values()) == n, f"Bad class counts: {name}")
        rows = {}
        frozen_spread = src["clip_frozen" if name.startswith("sonar_") else "frozen"]["sigma_m"]
        for checkpoint, status in spec["checkpoints"].items():
            model = src[checkpoint]
            by_dose = {r["lambda"]: r for r in model["rows"]}
            grid = (-1, -.5, 0, .5, 1, 2)
            require(all(x in by_dose for x in grid), f"Incomplete dose grid: {name}/{checkpoint}")
            exact = sum(by_dose[x]["tau_pred"] == by_dose[x]["tau_meas"] for x in grid)
            require(not name.startswith("sonar_") or exact == len(grid),
                    f"Archived exact predictor differs: {name}/{checkpoint}")
            require(by_dose[0]["top1"] == model["top1_0"], f"Baseline mismatch: {checkpoint}")
            rows[checkpoint] = {"status": status, "sigma_m": model["sigma_m"],
                                "top1_percent": model["top1_0"], "tau_at_image_plus_1": by_dose[1]["tau_meas"],
                                "equal_at_archived_precision_conditions": exact,
                                "text_minus_image_tau_at_plus_1": round(by_dose["text1.0"]["tau_meas"]-by_dose[1]["tau_meas"], 4),
                                "same_protocol_flattening_ratio": frozen_spread/model["sigma_m"]}
        benchmarks[name] = {"evaluation_images": n, "checkpoints": rows}
    tank, riku = [read(records / "benchmark" / (x + "_protocol.json"))["meta"]["classes"]
                  for x in ("watertank", "riku")]
    require(set(tank) < set(riku) and set(riku) - set(tank) == {"mine"}, "Incorrect shared-class roster")
    zero_shot = {}
    for p in sorted((records / "zero_shot").glob("*.json")):
        r = read(p)
        cm = r["confusion"]
        correct = sum(row.get(label, 0) for label, row in cm.items())
        classified = sum(sum(row.values()) for row in cm.values())
        require(correct == r["correct"] and classified in (r["images"], r["images"]-r.get("unknown_answers",0))
                and r["images"] == 380 and len(cm) == 7, f"Confusion mismatch: {p.name}")
        accuracy = correct / r["images"]
        require(abs(accuracy-r["accuracy"]) < 0.0001, f"Accuracy mismatch: {p.name}")
        zero_shot[r["model"]] = {"correct": correct, "images": r["images"], "accuracy_fraction": accuracy}
    require(len(zero_shot) == 4, "Missing zero-shot result")
    backbones = {}
    paired = read(records / "aggregate/sonar_b16_seed_paired_2026-11-08.json")["backbones"]
    for protocol, n in (("balanced", 650), ("full", 2617)):
        backbones[protocol] = {}
        for b in ("b16", "b32"):
            prefix = "sonar_protocol_" + b if protocol == "balanced" else "sonar_full_vit-b-" + b[1:]
            baseline = ("sonar_protocol" if n == 650 else "sonar_protocol_full")
            names = [f"records/backbone/{prefix}_seed{s}.json" for s in (42, 43, 44)]
            if b == "b32":
                names[0] = f"records/benchmark/{baseline}.json"
            elif n == 650:
                names[0] = "records/backbone/sonar_protocol_b16.json"
            samples = []
            for name in names:
                run = read(root / name)
                models = [run["clip_frozen"], run["sonar_ft" if n == 650 else "sonar_ft_full"]]
                require(run["meta"]["n_images"] == n and len(models) >= 2, f"Wrong seed protocol: {name}")
                observed = {"file": Path(name).name}
                for prefix2, model in zip(("frozen", "ft"), models):
                    dose = next(row for row in model["rows"] if row["lambda"] == 1)
                    observed.update({f"{prefix2}_top1_l0": model["top1_0"],
                                     f"{prefix2}_CG_l0": model["gap_norm"],
                                     f"{prefix2}_CG_lp1": dose["CG"],
                                     f"{prefix2}_tau_lp1": dose["tau_meas"]})
                samples.append(observed)
            if n == 650:
                require(samples == paired[b]["per_seed"], f"Balanced seed archive mismatch: {b}")
            backbones[protocol][b] = {
                "per_seed": samples,
                "means": {k: st.mean(s[k] for s in samples) for k in samples[0] if k != "file"},
                "population_sd": {k: st.pstdev(s[k] for s in samples) for k in samples[0] if k != "file"},
            }
    grid = read(records / "aggregate/threshold_calibration.json")
    operating = read(records / "aggregate/deployment_operating_points_2026-11-08_recomputed.json")
    require(len(grid["cells"]) == grid["n_points"] == 118 and len(operating["rows"]) == 10,
            "Calibration row mismatch")
    operating_counts = []
    for row in operating["rows"]:
        pos = [c for c in grid["cells"] if c["ret"] >= float(row["health"].split("_")[-1])]
        neg = [c for c in grid["cells"] if c not in pos]
        tp, fp = (sum(c["tau"] >= row["cutoff"] for c in group) for group in (pos, neg))
        sens, spec = tp/len(pos), 1-fp/len(neg)
        expected = {"n_positive": len(pos), "n_negative": len(neg), "sensitivity": round(sens, 3),
                    "specificity": round(spec, 3), "miss": round(1-sens, 3), "false_alarm": round(1-spec, 3),
                    "precision": round(tp/(tp+fp), 3) if tp+fp else 1.0}
        require(all(row[k] == v for k, v in expected.items()), f"Operating point differs: {row}")
        operating_counts.append({"health": row["health"], "cutoff": row["cutoff"], "tp": tp, "fp": fp,
                                 "tn": len(neg)-fp, "fn": len(pos)-tp})
    base, extra = [read(records/"aggregate"/(name+".json"))
                   for name in ("sonar_peft","sonar_peft_ms")]
    peft = {}
    for arm in ("lora_both","fullft"):
        runs = [base[arm], *(extra[f"{arm}__s{seed}"] for seed in (1,99))]
        peft[arm] = {"source_rows": runs, "metrics": {
            k: {"mean": st.mean(r[k] for r in runs), "population_sd": st.pstdev(r[k] for r in runs)}
            for k in ("top1_0","tau_l1","R1") if all(k in r for r in runs)}}
    require(round(peft["fullft"]["metrics"]["top1_0"]["mean"],1) == 72.8
            and round(peft["lora_both"]["metrics"]["tau_l1"]["mean"],3) == .575,
            "Adaptation aggregate differs")
    return {"order_regression": order_regression(), "in_sample_adaptation": peft, "benchmarks": benchmarks, "zero_shot": zero_shot, "backbones": backbones,
            "water_tank_labels_shared_with_riku": len(tank), "riku_additional_labels": ["mine"],
            "exploratory_operating_counts": operating_counts}


def text_provenance(root, manifest):
    records = root / "records"
    origins = {r["destination"]: r["source_sha256"] for r in manifest["sources"]}
    folder = records / "paired_rsicd"
    a = read(folder / "ScheduleResults.json")
    plan = read(folder / "schedule_lock.json")
    require(plan["train_pairs"] == 8000 and plan["test_unique_images"] == 1024 and plan["batch"] == 32
            and plan["site"] == "both" and plan["seeds"] == [0,1,2] and plan["epochs"] == [2,6],
            "Unexpected paired experiment design")
    plan_sha = digest((folder / "schedule_lock.json").read_bytes())
    require(a["plan_sha256"] == plan_sha, "Plan hash mismatch")
    index = {(r["arm"], r["epochs"], r["seed"]): r for r in a["runs"]}
    cells = set(product(("human", "metadata"), (2, 6), range(3)))
    require(set(index) == cells and len(index) == len(a["runs"]), "Paired grid missing or duplicate cells")
    hits = {}
    for arm, epochs, seed in sorted(cells):
        expected = index[arm, epochs, seed]
        stem = f"{arm}_8000_e{epochs}_s{seed}"
        p, receipt, pre = [folder/(stem+x+".json") for x in ("", ".receipt", ".pre-eval")]
        r, proof = read(p), read(receipt)
        sha = origins[p.relative_to(root).as_posix()]
        proof_expected = {"plan_sha256": plan_sha, "run_sha256": sha,
                          "train_sha256": plan["corpora"][arm+"_8000.jsonl"]["train_sha256"],
                          "test_reference_sha256": plan["test_reference_sha256"]}
        require(proof == proof_expected and read(pre) == {k: proof[k] for k in ("train_sha256","test_reference_sha256")},
                f"Receipt does not bind run and reference pool: {stem}")
        value = r["metrics"]["R@1_i2t"]
        hit = round(value*1024)
        require(round(hit/1024, 4) == value and 0 <= hit <= 1024, f"Invalid hit count: {stem}")
        require(r["epochs"] == epochs and r["seed"] == seed and r["site"] == "both" and r["batch"] == 32
                and r["pairs_used"] == 8000 and r["eval_pairs"] == 1024, f"Wrong runtime units: {stem}")
        computed = {"arm": arm, "epochs": epochs, "seed": seed, "file": p.name, "sha256": sha,
                    "receipt_sha256": digest(receipt.read_bytes()), "R@1_i2t": value, "hits": hit,
                    "optimizer_steps": epochs * 250, "peak_vram_gb": r["peak_vram_gb"],
                    "train_wall_seconds": r["wall_seconds"]}
        require(expected == computed, f"Paired summary mismatch: {stem}")
        hits[arm, epochs, seed] = hit
    paired = []
    for seed in range(3):
        short, long = [hits["metadata", e, seed] - hits["human", e, seed] for e in (2, 6)]
        paired.append({"seed": seed, "metadata_minus_human_2_hits": short, "metadata_minus_human_6_hits": long,
                       "difference_in_differences_hits": long-short})
    crossover = all(r["metadata_minus_human_2_hits"] < 0 < r["metadata_minus_human_6_hits"] for r in paired)
    require(paired == a["paired"] and crossover == a["all_seed_crossover"], "Invalid crossover summary")
    main = read(records / "aggregate/site_grid.json")
    require(len(main["main_grid"]) == 48, "Missing main grid cells")
    grid = []
    for row in main["main_grid"]:
        scores = []
        for info in row["records"]:
            path = "records/descriptive/full_10k/" + Path(info["source"]).name
            record = read(root / path)
            require(origins[path] == info["sha256"] and record["seed"] == info["seed"]
                    and record["epochs"] == info["epochs"] and record["batch"] == info["batch"]
                    and record["metrics"]["R@1_i2t"] == info["R@1_i2t"], f"Grid binding fails: {path}")
            scores.append(record["metrics"]["R@1_i2t"])
        stats = summary_stats(scores)
        require(len(scores) == 3 and round(stats["mean"],4) == row["mean"]
                and round(stats["sample_sd"],4) == row["sample_sd"], f"Grid aggregate differs: {row}")
        grid.append({k: row[k] for k in ("dataset","arm","site","mean","sample_sd")})
    transfer = read(records / "aggregate/transfer_matrix.json")["rows"]
    transfer_keys = {(r["source_corpus"],r["target_corpus"],r["arm"]) for r in transfer}
    require(len(transfer_keys) == len(transfer) == 18 and all(r["seed"] == 0 and r["n"] == 600 for r in transfer),
            "Invalid transfer grid")
    transfers = [{**r, "comparison": "same_corpus" if r["source_corpus"] == r["target_corpus"]
                  else "cross_corpus"} for r in transfer]
    families = defaultdict(list)
    for dir_name in ("held_out", "descriptive"):
        for p in sorted((records / dir_name).glob("*/*.json")):
            r = read(p)
            match = re.fullmatch(r"(.+)_s(\d+)", p.stem)
            require(match and int(match[2]) == r["seed"], f"Filename does not bind seed: {p.name}")
            families[dir_name, p.parent.name, match[1]].append((r["seed"], r["metrics"]))
    summaries = {}
    for (category, family, condition), rows in sorted(families.items()):
        seeds, metrics = zip(*rows)
        require(len(set(seeds)) == len(seeds) and all(set(m) == set(metrics[0]) for m in metrics),
                f"Inconsistent run group: {family}/{condition}")
        summaries.setdefault(category, {}).setdefault(family, {})[condition] = {
            "seeds": list(seeds), "metrics": {k: summary_stats([m[k] for m in metrics]) for k in sorted(metrics[0])}}
    fixed_reference = read(records/"aggregate/fixed_eval_comparison.json")
    for family in ("b32_fixed","l14_fixed","flickr_fixed"):
        legacy = fixed_reference[family]
        expected = ({arm:row for arm,row in legacy.items()} if family == "flickr_fixed" else
                    {f"{ds}_{arm}": row for ds, group in legacy.items() for arm,row in group.items()})
        actual = summaries["held_out"][family]
        require(set(actual) == set(expected), f"Fixed archive is missing conditions: {family}")
        for key, row in expected.items():
            require(actual[key]["seeds"] == [0,1] and row["n"] == 2 and all(
                round(actual[key]["metrics"][metric]["mean"],4) == row[metric]
                for metric in ("R@1_i2t","R@5_i2t","R@10_i2t")), f"Fixed aggregate differs: {family}/{key}")
    captioning = read(records/"aggregate/captioning_rsicd.json")["arms"]
    require(len(captioning) == 4 and all(row == read(records/"captioning"/(row["arm"]+".json"))
                                         for row in captioning), "Caption metrics do not bind to arm records")
    return {"paired": paired, "all_seed_crossover": crossover,
            "paired_query_denominator": 1024, "paired_cell_R@1": {
                f"{arm}_e{e}": summary_stats([hits[arm,e,s]/1024 for s in range(3)])
                for arm,e in product(("human","metadata"),(2,6))},
            "main_grid": grid, "transfer": transfers, "run_groups": summaries}


def replay(root, track):
    manifest = read(root / "provenance.json")
    require(manifest["track"] == track, "Wrong bundle")
    hashes = {r["destination"]: r["sha256"] for r in manifest["sources"]} | manifest["generated"]
    expected = set(hashes) | {"provenance.json", "summary.json"}
    entries = list(root.rglob("*"))
    require(not any(p.is_symlink() for p in entries), "Symlinks are not allowed")
    actual = {p.relative_to(root).as_posix() for p in entries if p.is_file()}
    require(actual == expected, f"Unexpected or missing files: {sorted(actual ^ expected)}")
    for name, h in hashes.items():
        require(digest((root / name).read_bytes()) == h, f"Hash mismatch: {name}")
    computed = sonar(root) if track == "a2" else text_provenance(root, manifest)
    require(computed == read(root/"summary.json"), "Public summary differs from replay")
    print(f"PASS: {track}: {len(actual)} files; verified archived inputs and recomputed summary.")

if __name__ == '__main__':
    replay(Path(__file__).resolve().parent, 'a2')
