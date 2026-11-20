"""Verify and replay the derived result bundle in this directory."""
from pathlib import Path
from hashlib import sha256
import json
import re
from statistics import mean, stdev

from itertools import combinations
from math import isclose, isfinite
from statistics import correlation, median


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def decode(data):
    return json.loads(data.decode("utf-8-sig"))


def compare(actual, expected, label):
    if isinstance(expected, dict):
        for key, val in expected.items():
            compare(actual[key], val, f"{label}.{key}")
    elif isinstance(expected, list):
        require(len(actual) == len(expected), f"{label}: length mismatch")
        for index, (left, right) in enumerate(zip(actual, expected)):
            compare(left, right, f"{label}[{index}]")
    elif isinstance(expected, float):
        require(isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10),
                f"{label}: {actual!r} != {expected!r}")
    else:
        require(actual == expected, f"{label}: {actual!r} != {expected!r}")


def get(read, name):
    return decode(read("data/" + name))


def analysis(read, name):
    return get(read, f"outputs/analysis/{name}.json")


def anchored_fit(epochs, energy):
    """Historical grid and anchor; deliberately retain native epoch coordinates."""
    import numpy as np
    t, y = np.asarray(epochs, dtype=float), np.asarray(energy, dtype=float)
    require(t.shape == y.shape and t.ndim == 1 and len(t) >= 5, "Invalid fit history")
    require(np.all(np.isfinite(t)) and np.all(np.isfinite(y)) and np.all(np.diff(t) > 0),
            "Invalid trajectory coordinates")
    delta = y - y[0]
    beta = 10.0 ** np.linspace(np.log10(0.005), np.log10(20.0), 800)
    u = 1.0 - np.exp(-beta[:, None] * t)
    amp = (u * delta).sum(axis=1) / (u * u).sum(axis=1)
    residual = ((delta - amp[:, None] * u) ** 2).sum(axis=1)
    idx = int(np.argmin(residual))
    ss = float(((y - y.mean()) ** 2).sum())
    require(ss > 0, "Constant energy trajectory")
    y_line = np.polyval(np.polyfit(t, y, 1), t)
    return dict(alpha=float(amp[idx] * beta[idx]), beta=float(beta[idx]),
                R2=1 - float(residual[idx]) / ss,
                linear_R2=1 - float(((y - y_line) ** 2).sum()) / ss)


def position_summary(read):
    import numpy as np
    fits = analysis(read, "ode_ledger")
    scope = analysis(read, "paper_a_archive_scope_2026-11-18")["strict_freezing"]
    rows = []
    identifiers = set()
    for row in fits["runs"]:
        source = f'outputs/theory/{row["conf"]}/{row["seed"]}/dg_star_history.json'
        require(source not in identifiers, f"Duplicate fit input: {source}")
        identifiers.add(source)
        d = get(read, source)
        fit = anchored_fit(d["epochs"], d["dg_star"])
        compare(len(d["epochs"]), row["n_epoch"], source)
        compare(fit, {k: row[k] for k in ("alpha", "beta", "R2")}, source)
        rows.append(dict(fit, family=row["family"], source=source))
    for family, archived in fits["subsets"].items():
        # Some subgroups have additional design selectors; replay the central families here.
        sub = [r["R2"] for r in rows if family == "all" or r["family"] == family]
        if sub:
            compare(dict(n=len(sub), mean=mean(sub), median=median(sub), min=min(sub), max=max(sub),
                         sd=stdev(sub) if len(sub) > 1 else 0.0),
                    {k: archived[k] for k in ("n", "mean", "median", "min", "max", "sd")
                     if k in archived}, family)
    strict_ids = set()
    for r in scope["records"]:
        key = (r["source"], r["field"])
        require(key not in strict_ids, f"Duplicate strict-freeze record: {key}")
        strict_ids.add(key)
        data = get(read, r["source"])
        if r["field"] != "$":
            i = int(re.fullmatch(r"records\[(\d+)\]", r["field"])[1])
            compare([data["records"][i][k] for k in ("rank", "arm", "seed")],
                    r["record_key"], r["source"])
    lora = [r for r in rows if r["family"] == "lora"]
    result = dict(ode_inputs=len(rows), matched_lora=len(lora),
                  matched_lora_ode_mean=mean(r["R2"] for r in lora),
                  matched_lora_linear_mean=mean(r["linear_R2"] for r in lora),
                  negative_fitted_alpha=sum(r["alpha"] < 0 for r in rows),
                  strict_freeze_records=len(strict_ids))
    audit = get(read, "reference/trajectory_audit.json")
    compare(result, dict(ode_inputs=96, matched_lora=55,
                         matched_lora_ode_mean=audit["mean_ode_r2"],
                         matched_lora_linear_mean=audit["mean_linear_r2"],
                         negative_fitted_alpha=92, strict_freeze_records=104), "Fit and inventory")
    for row, expected in zip(rows, audit["run_replays"], strict=True):
        compare(row, dict(source=expected["path"], family=expected["family"], alpha=expected["alpha"],
                          beta=expected["beta"], R2=expected["ode_r2"], linear_R2=expected["linear_r2"]),
                row["source"])
    result["pilot_signed_alpha"] = {}
    for r in audit["pilot_diagnostics"]:
        d = get(read, r["path"])
        g = d.get("gamma", {})
        keys = ("Gamma_v", "Gamma_t", "norm_g_v", "norm_g_t")
        value = (-d["learning_rate"] * (g[keys[0]] * g[keys[2]] + g[keys[1]] * g[keys[3]])
                 if all(k in g for k in keys) else None)
        compare(value, r["recomputed_alpha"], r["path"])
        if value is not None:
            require(value < 0 and isclose(value, -d["alpha_estimated"], abs_tol=1e-14),
                    "Pilot sign mismatch")
        result["pilot_signed_alpha"][r["path"]] = value
    require(len(result["pilot_signed_alpha"]) == 9 and
            sum(v is not None for v in result["pilot_signed_alpha"].values()) == 8, "Wrong pilot scope")
    ident = get(read, "outputs/theory/gradflow_identity/identity_check.json")
    p = [r["predicted_delta"] for r in ident["records"]]
    a = [r["actual_delta"] for r in ident["records"]]
    result["sgd_identity_check"] = dict(n=len(p), correlation=correlation(p, a),
                                       median_relative_error=median(abs(x-y)/abs(x) for x,y in zip(p,a)))
    compare(result["sgd_identity_check"], {k: audit["identity"][k] for k in result["sgd_identity_check"]},
            "Single-step SGD")
    recall = analysis(read, "dg_r1_reproducible")["rows"]
    recall_ref = get(read, "reference/gap_recall.json")
    for row in recall:
        raw = get(read, f'outputs/{row["path"]}/results.json')
        compare(raw["final_gap"]["distribution_gap"], row["dg_final"], row["path"])
        compare(raw["final_gap"]["centroid_gap"], row["cg_final"], row["path"])
        compare(raw["final_task_metrics"]["R@1"], row["r1"], row["path"])
    rr = [r["r1"] for r in recall]
    corr = [correlation([r[k] for r in recall], rr) for k in ("dg_final", "cg_final")]
    compare(len(recall), recall_ref["pooled_n"], "Pooled recall size")
    compare(corr, recall_ref["pearson_dg_cg"], "Pooled recall correlations")
    result["pooled_recall"] = dict(n=len(recall), pearson_dg_cg=corr,
                                   stratified_n=recall_ref["stratified_n"])
    noise = get(read, "outputs/noise_fixed_aug.json")["rows"]
    no_noise = [r for r in noise if r["sigma"] == 0]
    require(len(no_noise) == 10 and all(r["drop_pct"] == 0 for r in no_noise), "Zero-noise control")
    sig = {site: [r["drop_pct"] for r in noise if r["sigma"] == 0.1 and r["encoder"] == site]
           for site in ("vision", "text")}
    require(all(len(v) == 5 for v in sig.values()), "Wrong noise seed count")
    result["noise_sigma_0.1"] = {site: dict(mean=mean(v), sample_sd=stdev(v)) for site,v in sig.items()}
    result["noise_sigma_0.1"]["vision_over_text"] = mean(sig["vision"]) / mean(sig["text"])
    c5 = analysis(read, "a_c5_llava_bf16_vs_4bit_2026-11-08")
    for label, folder, size in PRECISION:
        for arm in ("text_only", "both", "vision_only"):
            raw = [get(read, f"{folder}/{arm}_s{seed}.json") for seed in (42, 123, 456)]
            require(all(r["samples"] == size for r in raw), "Cohorts differ in expected train size")
            delta = [r["cg_after"] - r["cg_before"] for r in raw]
            compare(round(mean(delta), 5), c5[label][arm]["dCG_mean"], "Descriptive precision mean")
            compare(round(stdev(delta), 5), c5[label][arm]["dCG_sd"], "Descriptive precision SD")
    return result


def sequential(rows, key, delta):
    best = 0
    for i in range(1, len(rows)):
        if rows[i][key] > rows[best][key] + delta:
            return best
        if rows[i][key] < rows[best][key]:
            best = i
    return best


def monitor_summary(read):
    runs = {}
    raw_names = ("a1_monitor_interior_v2", "a1_monitor_interior_extra")
    for name in raw_names:
        block = analysis(read, name)["runs"]
        require(not runs.keys() & block.keys(), f"Duplicate monitor runs: {name}")
        runs.update(block)
    ref = analysis(read, "a1_monitor_combined")
    per_run, pooled, groups = {}, [], {"small": [], "large": []}
    for key, rows in runs.items():
        require([r["epoch"] for r in rows] == list(range(1, 11)), f"Missing monitor epoch: {key}")
        top = [r["top1"] for r in rows]
        recorded_rules = (("minM", "mass_0.01", min), ("minCG", "CG", min),
                          ("minEntropy", "entropy", min), ("maxSoftmax", "maxsoftmax", max),
                          ("maxLogit", "maxlogit", max), ("minEnergy", "energy", min))
        values = {"oracle": max(top), "first": top[0], "last": top[-1],
                  "seqM": top[sequential(rows, "mass_0.01", .01)],
                  "seqCG": top[sequential(rows, "CG", .01)]}
        for rule, field, fn in recorded_rules:
            if all(field in r for r in rows):
                vals = [r[field] for r in rows]
                values[rule] = top[vals.index(fn(vals))]
        compare(values, ref["per_run"][key], key)
        require(values.keys() == ref["per_run"][key].keys(), "Different monitor rule coverage")
        per_run[key] = values
        pooled.extend(rows)
        groups["small" if any(d in key for d in ("fathomnet8", "inat_wild")) else "large"].append(values)
    rules = {}
    for rule, expected in ref["rules"].items():
        regret = [v["oracle"] - v[rule] for v in per_run.values() if rule in v]
        rules[rule] = dict(mean_regret=mean(regret), max_regret=max(regret), n_runs=len(regret),
                           n_checkpoints=10 * len(regret))
        compare(rules[rule], expected, f"Monitor {rule}")
    stratified = analysis(read, "a1_monitor_split_diagnosis")["summary"]
    split = {}
    for name, group in groups.items():
        split[name] = dict(n_runs=len(group))
        for rule, field in (("minM", "minM"), ("last", "last_epoch"), ("first", "first_epoch")):
            split[name][f"mean_regret_{field}"] = mean(v["oracle"] - v[rule] for v in group)
        compare(stratified[name], split[name], f"{name} holdout")
    r = correlation([x["mass_0.01"] for x in pooled], [x["top1"] for x in pooled])
    compare(r, ref["correlation"]["pooled_M"], "Monitor pooled correlation")
    require(len(runs) == ref["n_runs"] == 20 and len(pooled) == ref["correlation"]["n_checkpoints"] == 200,
            "Wrong monitor scope")
    return dict(n_runs=len(runs), n_checkpoints=len(pooled), rules=rules, split=split, pooled_M=r)


def widest(rows, tol):
    pairs = [(abs(a["top1"] - b["top1"]), abs(a["CG"] - b["CG"]), a, b)
             for a, b in combinations(rows, 2) if abs(a["CG"] - b["CG"]) <= tol]
    return max(pairs, key=lambda p: p[0])


def order_summary(read):
    import numpy as np
    raw = analysis(read, "a1_campaign")["runs"]
    ref = analysis(read, "a1_campaign_analysis")
    correctness = get(read, "records/campaign_correctness.json")
    checkpoints = [dict(c, dataset=r["dataset"], tower=r["tower"], seed=r["seed"], run=k)
                   for k, r in raw.items() for c in r["checkpoints"]]
    require(len(checkpoints) == 72 and len(raw) == 18, "Wrong campaign scope")
    compare(len(checkpoints), ref["n_checkpoints"], "Campaign checkpoints")
    compare(len(raw), ref["n_runs"], "Campaign runs")
    flags = {}
    for c in checkpoints:
        key = f'{c["run"]}|ep{c["epoch"]}'
        vector = correctness[key]
        require(len(vector) == 5000 and set(vector) <= {"0", "1"}, f"Bad correctness vector: {key}")
        flags[key] = np.fromiter((int(v) for v in vector), dtype=np.int8)
        compare(float(flags[key].mean()) * 100, c["top1"], key)
    require(flags.keys() == correctness.keys(), "Unexpected correctness vectors")
    pairs = [(a, b) for a, b in combinations(checkpoints, 2)]
    gap = lambda p: abs(p[0]["CG"] - p[1]["CG"])
    spread = lambda p: abs(p[0]["top1"] - p[1]["top1"])
    counts = {str(t): sum(gap(p) <= t for p in pairs) for t in (.01, .02, .03, .05)}
    compare(counts, ref["pairs"]["n_pairs_at_tol"], "Campaign pair counts")
    widest_pairs = {}
    for mode in ("all", "within_run"):
        subset = [p for p in pairs if gap(p) <= .03 and (mode == "all" or p[0]["run"] == p[1]["run"])]
        a, b = max(subset, key=spread)
        archive = ref["pairs"]["widest"][mode]
        compare(a, archive["a"], f"{mode} endpoint a")
        compare(b, archive["b"], f"{mode} endpoint b")
        ca, cb = [flags[f'{c["run"]}|ep{c["epoch"]}'].astype(float) for c in (a, b)]
        rng = np.random.RandomState(0)
        diffs = []
        for _ in range(1000):
            ix = rng.randint(0, len(ca), len(ca))
            diffs.append(float(ca[ix].mean() - cb[ix].mean()) * 100)
        signed = np.percentile(diffs, [2.5, 97.5]).tolist()
        absolute = signed if a["top1"] >= b["top1"] else [-signed[1], -signed[0]]
        actual = dict(dCG=gap((a, b)), dtop1=spread((a, b)), signed_a_minus_b_ci95=signed,
                      oriented_spread_ci95=absolute)
        compare(actual, {k: archive[k] for k in actual}, f"{mode} paired bootstrap")
        widest_pairs[mode] = actual
    matched = analysis(read, "a1_matched_gap_families")
    matched_spreads = {}
    for tol, suffix in ((.03, "003"), (.05, "005")):
        diff, dcg, _, _ = widest(matched["rows"], tol)
        match = matched["max_matched_gap_spread_tol" + suffix]
        compare(dict(spread=diff, dCG=dcg), {k:match[k] for k in ("spread", "dCG")}, f"Matched gap {tol}")
        matched_spreads[str(tol)] = dict(spread=diff, dCG=dcg)
    traj = get(read, "outputs/a1_tau_trajectory.json")
    compare(traj, get(read, "reference/training_readouts.json")["rows"], "Training readouts")
    return dict(campaign=dict(n_runs=len(raw), n_checkpoints=len(checkpoints), pair_counts=counts,
                              widest=widest_pairs), matched_gap=matched_spreads, monitor=monitor_summary(read))


PRECISION = (("bf16", "outputs/analysis/llava_sites_bf16_2026-11-08", 400),
             ("4bit", "outputs/llava_canonical_cloud", 1500))


def summary(track, read):
    return {"paper_a": position_summary, "a1": order_summary}[track](read)


def replay(read, paths):
    manifest = decode(read("provenance.json"))
    listed = manifest["files"]
    require(set(paths) == set(listed) | {"provenance.json"}, "Unexpected or missing bundle files")
    for name, sha in listed.items():
        require(digest(read(name)) == sha, f"Public hash mismatch: {name}")
    for item in manifest["sources"]:
        require(listed[item["destination"]] == item["public_sha256"], "Provenance mapping mismatch")
    value = summary(manifest["track"], read)
    expected = decode(read("summary.json"))
    compare(value, expected, "Corrected summary")
    compare(expected, value, "Corrected summary field coverage")
    return value


def run_folder(folder):
    files = {}
    for p in folder.rglob("*"):
        require(not p.is_symlink(), f"Symlink in bundle: {p.name}")
        if p.is_file():
            files[p.relative_to(folder).as_posix()] = p
    return replay(lambda key: files[key].read_bytes(), files)


if __name__ == "__main__":
    print(json.dumps(run_folder(Path(__file__).resolve().parent), indent=2))
