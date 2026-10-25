#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""P3 balanced common-seed design for the S29 environment matrix / S37 variance decomposition.

WHY THIS SCRIPT EXISTS
----------------------
S29 (the environment matrix) reports four torch/CUDA stacks and S37 decomposes the r=5 spread into
sigma_env, sigma_seed and the environment share.  Both rest on an *unbalanced* design: every stack
carries a different seed set, so the environment term is confounded with "which seeds this stack
happens to have".  This script audits the cells that exist today, plans the minimum set of runs that
makes the four stacks share one common seed set, prices that plan in GPU hours, and quantifies what
the balanced design buys in terms of the confidence interval of the environment share.

WHAT A "CELL" IS
----------------
One (stack, rank, seed) training run of the archived 20-sample / 3-epoch protocol.  A cell is
*bounded by its own archive*: the stack label comes from an explicit registry whose entries are
grounded in fields the archives themselves carry (see STACKS below), never from a loose filename
glob.  The loose glob of tools/_p1570_env_variance_update.py (`verify_r5_s*_a10*.json`) is known to
be wrong today -- it also matches `_a10_torch26.json` rows and would mis-file them as torch 2.4/cu121
-- and is deliberately not reproduced here.

STACK REGISTRY (stack identity, and the evidence for it)
--------------------------------------------------------
Each entry's `evidence` names the archive and field that carry the label; `protocol` pins the
per-file validation applied to every candidate (the file must agree with its own payload, otherwise
it is reported as a contradiction rather than silently used):

* torch29_cu130   -- outputs/analysis/p3_seeds_combined.json, fields `values.r5` / `values.r6`;
                     its `source_archives` name outputs/analysis/p3_rerun_{protocol,seeds,extra}.json.
* torch212_cu130  -- paper3/scripts/outputs/experiments/cloud_verify_r<R>_s*.json, `delta_E`, minus
                     partial/imgs/_e1_ rows (the rule of tools/_p1595_p3_rank_separation.py).
* torch24_cu121   -- rows carrying the explicit `_torch24` filename suffix (the label is in the
                     file name by construction, because run_training.py cannot write a stack suffix)
                     plus the rank-5 `_a10` rows for seeds 123/999, which are exactly the four values
                     archived in outputs/analysis/p3_env_variance.json's "torch 2.4/cu121" bucket
                     (hyperparameters {epochs 3, batch 1, lr 5e-05, block_config uniform, adamw,
                     float16, grad_mask none, attn_targets qkvo}, stored in
                     outputs/analysis/p3_env_matrix3.json, whose `env3_local_torch24_cu121` block
                     names the stack `torch 2.4.1+cu121` / `cuda 12.1`).
* torch26_cu124   -- rows carrying the explicit `_torch26` filename suffix, same explicit-suffix
                     argument; seed 42 is archived, seeds 7/123/999 are produced by the round that is
                     running locally as this plan is written.

METHOD AND FIELD NAMES (the decomposition is *the same one already used*)
------------------------------------------------------------------------
`decomposition()` below is `tools/_p1570_env_variance_update.py`'s decomposition and
`tools/_p1613_p3_cloud_runner.py`'s `decomposition()`: a one-way random-effects ANOVA on the
environment level with the unequal-n correction n0 =
(n - sum(n_i^2)/n)/(k - 1), sigma_seed^2 = MS_within and
sigma_env^2 = max(0, (MS_between - MS_within)/n0).  The archive fields this script writes into
`power_comparison` carry the same names as the archives it is compared against:

* outputs/analysis/p3_env_variance.json  -> `sigma_env`, `sigma_seed`, `env_share`,
  `bootstrap.share_mean`, `bootstrap.share_ci95` (method string in `meta.method`);
* outputs/analysis/p3_env_stack_seeds.json (written by the cloud runner when the round finishes)
  -> `sigma_env`, `sigma_seed`, `env_variance_share`, `sigma_by_rank.*.balanced_common_seed`.

The bootstrap is a resampling over the cells of the design, which is this script's own addition; the
archived bootstrap resampled seeds within each environment.  Both are reported so the comparison of
the CI width is not an artefact of switching the resampling unit, and the archive-consistent variant
is the one whose *today* value can be checked against the archived `bootstrap.share_ci95`.

USAGE
-----
    python tools/_p1638_p3_balanced_env_design.py --audit
    python tools/_p1638_p3_balanced_env_design.py --plan --common-seeds 42,7,123,999
    python tools/_p1638_p3_balanced_env_design.py --power --common-seeds 42,7,123,999
    python tools/_p1638_p3_balanced_env_design.py --plan --dry-run      # prints, writes nothing

--plan and --power write outputs/analysis/p3_balanced_design_plan.json (deterministic: integer rng
seed, no wall-clock field).  --dry-run prints every command and writes nothing.  --audit writes
nothing at all.
"""
from __future__ import annotations

import argparse
import glob
import importlib.util
import io
import json
import math
import os
import sys

import numpy as np

# ------------------------------------------------------------------------------------------------
# Paths and frozen constants
# ------------------------------------------------------------------------------------------------
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(REPO, "outputs", "analysis")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")
OUT_JSON = os.path.join(AN, "p3_balanced_design_plan.json")

SCRIPT_NAME = "tools/_p1638_p3_balanced_env_design.py"
RANKS = (5, 6)
DEFAULT_COMMON_SEEDS = (42, 7, 123, 999)
N_BOOT = 10000
RNG_SEED = 7                      # same rng seed as tools/_p1570_env_variance_update.py
SIGMA_ENV_ARCHIVE = 31.148928826613844
SIGMA_SEED_ARCHIVE = 34.294997813092216
ENV_SHARE_ARCHIVE = 0.4520380976240466
SHARE_CI95_ARCHIVE = (0.21198180448528658, 0.7471951281145658)

# Per-run wall clock recorded by the archives of this protocol (see cost_estimate.basis in the
# emitted JSON).  Keys are archive paths relative to the repository root.
LOCAL_TIMING_SOURCES = (
    "outputs/analysis/p3_rerun_protocol.json",
    "outputs/analysis/p3_rerun_seeds.json",
    "outputs/analysis/p3_rerun_extra.json",
)
LOCAL_TRAINING_LOG_GLOB = os.path.join(REPO, "outputs", "run_*.log")
LOCAL_TIMING_RANKS = (5, 6)
CLOUD_NOTES = "docs/p3_cloud_round_notes.md"
LOCAL_RUNNER = "tools/_p1613_p3_cloud_runner.py"
RUN_TRAINING = "paper3/scripts/run_training.py"

# The archived 20-sample / 3-epoch protocol of every row this design balances.  It is the expected
# value of `row_is_valid()` in tools/_p1613_p3_cloud_runner.py and is the training command emitted by
# build_train_command() there; both are reproduced here so the emitted commands are the archived ones.
PROTOCOL = {
    "epochs": 3,
    "num_samples": 20,
    "lr": 5e-05,
    "lr_flag": "5e-5",
    "batch_size": 1,
    "block_config": "uniform",
    "opt": "adamw",
    "compute_dtype": "float16",
    "attn_targets": "qkvo",
    "grad_mask": "none",
    "warmup": False,
}
PROTOCOL_FIELDS = ("rank", "seed", "epochs", "num_samples", "lr", "warmup", "compute_dtype", "opt",
                   "block_config", "grad_mask", "lora_alpha", "attn_targets", "batch_size",
                   "proj_rank", "data_offset", "target_proj", "lang_only", "ok", "delta_E")


def alpha_for(rank: int) -> float:
    """LoRA alpha of the archived rows: 2 * rank, passed explicitly as --lora-alpha."""
    return float(2 * rank)


def fmt_alpha(alpha: float) -> str:
    return "%g" % alpha


# ------------------------------------------------------------------------------------------------
# Stack registry: identity from explicit lists, every entry naming the archive field that labels it
# ------------------------------------------------------------------------------------------------
STACKS = (
    {
        "id": "torch29_cu130",
        "label": "torch 2.9/cu130",
        "machine": "RTX 4060 Laptop (local)",
        "torch": "2.9.1+cu130",
        "cuda": "13.0",
        "place": "LOCAL",
        "interpreter": r"D:\Anaconda\envs\pytorch\python.exe",
        "kind": "analysis_map",
        "source": "outputs/analysis/p3_seeds_combined.json",
        "source_field": "values.r%d.<seed>",
        "evidence": "p3_seeds_combined.json values.r5/r6; its source_archives name "
                    "p3_rerun_protocol.json, p3_rerun_seeds.json and p3_rerun_extra.json, whose runs "
                    "recorded E0 3921 and the same deltas",
        "protocol": dict(PROTOCOL, lora_alpha="2*rank"),
    },
    {
        "id": "torch212_cu130",
        "label": "torch 2.12/cu130",
        "machine": "RTX 4080 SUPER (cloud)",
        "torch": "2.12.1+cu130",
        "cuda": "13.0",
        "place": "CLOUD",
        "interpreter": "python (instance interpreter, torch 2.12.x)",
        "kind": "files",
        "pattern": "paper3/scripts/outputs/experiments/cloud_verify_r%d_s*.json",
        "exclude_substrings": ("partial", "imgs", "_e1_"),
        "name_check": "untagged",
        "source_field": "delta_E",
        "evidence": "cloud_verify_r<R>_s*.json delta_E, excluding partial/imgs/_e1_ rows (the rule of "
                    "tools/_p1595_p3_rank_separation.py); E0 of these rows is 3926",
        "protocol": dict(PROTOCOL, lora_alpha="2*rank"),
    },
    {
        "id": "torch24_cu121",
        "label": "torch 2.4/cu121",
        "machine": "RTX 4060 Laptop (local)",
        "torch": "2.4.1+cu121",
        "cuda": "12.1",
        "place": "LOCAL",
        "interpreter": r"D:\Anaconda\envs\torch24\python.exe",
        "kind": "files",
        "patterns": (
            "paper3/scripts/outputs/experiments/verify_r%d_s*_lr5e-05_nw_float1_adamw_e3_bcuniform_"
            "a%s_torch24.json",
            "paper3/scripts/outputs/experiments/verify_r%d_s*_lr5e-05_nw_float1_adamw_e3_bcuniform_"
            "a%s.json",
        ),
        "name_check": "tagged",
        "source_field": "delta_E",
        "evidence": "the explicit `_torch24` filename suffix (run_training.py cannot write a stack "
                    "suffix; the label is in the name by construction) plus the rank-5 `_a10` rows for "
                    "seeds 123/999, which are exactly the four values of the archived bucket "
                    "'torch 2.4/cu121' in outputs/analysis/p3_env_variance.json ([-2.5, 41.0, -2.0, "
                    "64.5]); the stack's own metadata is "
                    "p3_env_matrix3.json.env3_local_torch24_cu121 (torch 2.4.1+cu121, cuda 12.1)",
        "protocol": dict(PROTOCOL, lora_alpha="2*rank"),
    },
    {
        "id": "torch26_cu124",
        "label": "torch 2.6/cu124",
        "machine": "RTX 4060 Laptop (seed 42) + cloud GPU (seeds 7/123/999)",
        "torch": "2.6.0+cu124",
        "cuda": "12.4",
        "place": "LOCAL",
        "interpreter": r"D:\Anaconda\envs\torch26\python.exe",
        "kind": "files",
        "patterns": (
            "paper3/scripts/outputs/experiments/verify_r%d_s*_lr5e-05_nw_float1_adamw_e3_bcuniform_"
            "a%s_torch26.json",
        ),
        "name_check": "tagged",
        "source_field": "delta_E",
        "evidence": "the explicit `_torch26` filename suffix (same explicit-suffix argument as "
                    "torch24); seed 42 archived, seeds 7/123/999 produced by the round of "
                    "tools/_p1613_p3_cloud_runner.py --job env-seeds",
        "protocol": dict(PROTOCOL, lora_alpha="2*rank"),
    },
)

# Where the labels of the local stacks come from, verbatim, in the operator-facing report.
STACK_METADATA_ARCHIVE = ("outputs/analysis/p3_env_matrix3.json fields "
                          "env1_local_torch29_cu130 / env2_cloud_torch212_cu130 / "
                          "env3_local_torch24_cu121: `torch`, `cuda`, `gpu`")

MAIN_HYPOTHESIS_RANK = 5          # S37 decomposes the rank-5 spread; rank 6 is reported beside it


# ------------------------------------------------------------------------------------------------
# Small helpers
# ------------------------------------------------------------------------------------------------
def rel(path: str) -> str:
    return os.path.relpath(path, REPO).replace(os.sep, "/")


def load_json(path: str) -> dict:
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=True)
        fh.write("\n")


def finite(value) -> float | None:
    """Float value of an archive field, or None when it is absent / non-numeric / non-finite."""
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if out != out or out in (float("inf"), float("-inf")):
        return None
    return out


def plain_name(rank: int, seed: int) -> str:
    """The untagged filename run_training.py writes for this protocol (alpha passed explicitly).

    The training script's own tag rule is not re-derived here: `predict_plain_name()` of
    tools/_p1613_p3_cloud_runner.py is imported and used, because that function is checked against
    the archived filenames by that script's --self-test (`_a10`/`_a12` appear in a run_training.py
    filename tag only when --lora-alpha is passed explicitly).
    """
    runner = _runner_module()
    if runner is not None:
        return runner.predict_plain_name(rank, seed, alpha_for(rank))
    raise RuntimeError("cannot import %s to predict the archived filename of r%d seed %d"
                       % (LOCAL_RUNNER, rank, seed))


_RUNNER_CACHE: list = []


def _runner_module():
    """Import tools/_p1613_p3_cloud_runner.py by path (no sys.path mutation)."""
    if _RUNNER_CACHE:
        return _RUNNER_CACHE[0]
    path = os.path.join(REPO, LOCAL_RUNNER)
    spec = importlib.util.spec_from_file_location("_p1613_p3_cloud_runner", path)
    module = None
    if spec is not None and spec.loader is not None:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    _RUNNER_CACHE.append(module)
    return module


def build_train_command(rank: int, seed: int, data_path: str | None = None,
                        python: str | None = None) -> list:
    """The exact argv of the archived seed-42 protocol (same flags as the cloud runner's builder)."""
    cmd = [
        python or sys.executable,
        os.path.join(REPO, RUN_TRAINING),
        "--rank", str(rank),
        "--seed", str(seed),
        "--epochs", str(PROTOCOL["epochs"]),
        "--num-samples", str(PROTOCOL["num_samples"]),
        "--lr", PROTOCOL["lr_flag"],
        "--batch-size", str(PROTOCOL["batch_size"]),
        "--block-config", PROTOCOL["block_config"],
        "--opt", PROTOCOL["opt"],
        "--compute-dtype", PROTOCOL["compute_dtype"],
        "--attn-targets", PROTOCOL["attn_targets"],
        "--grad-mask", PROTOCOL["grad_mask"],
        "--lora-alpha", fmt_alpha(alpha_for(rank)),
    ]
    if data_path:
        cmd += ["--data-path", data_path]
    return cmd


def printable(cmd: list, stack: dict) -> str:
    """A copy-pasteable form of argv: repo-relative script, stack's own interpreter."""
    parts = []
    for i, tok in enumerate(cmd):
        if i == 0:
            parts.append(stack["interpreter"] if stack["place"] == "LOCAL" else "python")
        elif isinstance(tok, str) and os.path.isabs(tok) and tok.startswith(REPO):
            parts.append(rel(tok))
        else:
            parts.append(tok)
    return " ".join(parts)


# ------------------------------------------------------------------------------------------------
# Census: which (stack, rank, seed) cells exist today, each bounded by its own archive
# ------------------------------------------------------------------------------------------------
def file_records(stack: dict) -> tuple:
    """Read one file-based stack's explicit lists and return (records, census)."""
    records, files, contradictions, notes = [], [], [], []
    for rank in RANKS:
        alpha = fmt_alpha(alpha_for(rank))
        templates = stack.get("patterns") or (stack["pattern"],)
        used_patterns = []
        for template in templates:
            # "%d" is the rank and "%s" the lora alpha of the protocol's filename; substitute the
            # alpha first so a plain substitution cannot collide.
            pattern = os.path.join(REPO, template.replace("%s", alpha).replace("%d", str(rank)))
            used_patterns.append(pattern)
            for path in sorted(glob.glob(pattern)):
                name = os.path.basename(path)
                if any(x in name for x in stack.get("exclude_substrings", ())):
                    continue
                if path in files:
                    continue
                try:
                    d = load_json(path)
                except Exception as exc:                                   # noqa: BLE001
                    contradictions.append({"source_file": rel(path),
                                           "reason": "unreadable (%r)" % (exc,)})
                    continue
                why = payload_contradiction(d, rank, alpha_for(rank))
                if why:
                    contradictions.append({"source_file": rel(path), "reason": why})
                    continue
                # The payload's own `name` field must be the name this cluster of archives states
                # for the run.  The 2.12/cu130 rows are the `verify_r{rank}_s{seed}` variant (the
                # payload of cloud_verify_r5_s42.json is "verify_r5_s42"), the torch24/torch26 rows
                # carry run_training.py's own tagged name, and the 2.9 rows are seed->value fields
                # in a map archive, so they have no per-run name to check.
                if stack.get("name_check") == "untagged":
                    expect_name = "verify_r%d_s%d" % (rank, int(d["seed"]))
                    allowed = (expect_name,)
                elif stack.get("name_check") == "tagged":
                    expect_name = plain_name(rank, int(d["seed"]))[:-len(".json")]
                    allowed = (expect_name, expect_name + "_torch24", expect_name + "_torch26")
                else:
                    allowed = None
                if allowed is not None and d.get("name") not in allowed:
                    contradictions.append({
                        "source_file": rel(path),
                        "reason": "payload name %r is not the expected name %r"
                                  % (d.get("name"), expect_name)})
                    continue
                value = finite(d.get("delta_E"))
                if value is None:
                    contradictions.append({"source_file": rel(path),
                                           "reason": "delta_E is absent or non-finite"})
                    continue
                energy = d.get("E") or []
                e0 = finite(energy[0]) if energy else None
                if e0 is not None and abs(value - (finite(energy[-1]) - e0)) > 1e-9:
                    contradictions.append({"source_file": rel(path),
                                           "reason": "delta_E is not E[-1] - E[0]"})
                    continue
                files.append(path)
                records.append({"stack": stack["id"], "stack_label": stack["label"],
                                "machine": stack["machine"], "torch": stack["torch"],
                                "cuda": stack["cuda"], "place": stack["place"],
                                "rank": rank, "seed": int(d["seed"]), "alpha": alpha_for(rank),
                                "delta_E": value, "E0": e0,
                                "source_file": rel(path), "source_field": stack["source_field"]})
        notes.append("%s: rank %d -> %d row(s) from %s"
                     % (stack["id"], rank,
                        len([r for r in records if r["rank"] == rank]),
                        ", ".join(os.path.basename(p) for p in used_patterns)))
    census = {"id": stack["id"], "kind": stack["kind"], "label": stack["label"],
              "machine": stack["machine"], "torch": stack["torch"], "cuda": stack["cuda"],
              "place": stack["place"], "evidence": stack["evidence"],
              "source_field": stack["source_field"],
              "protocol": stack["protocol"], "notes": notes,
              "contradictions": contradictions,
              "files": [rel(p) for p in files]}
    return records, census


def payload_contradiction(d: dict, rank: int, alpha: float) -> str | None:
    """Check a candidate file against its own payload: rank, alpha and the archived protocol."""
    if int(d.get("rank", -1)) != rank:
        return "payload rank %r != bucket rank %d" % (d.get("rank"), rank)
    if d.get("lora_alpha") is None or abs(float(d["lora_alpha"]) - alpha) > 1e-9:
        return "payload lora_alpha %r != 2*rank (%g)" % (d.get("lora_alpha"), alpha)
    for key, want in (("epochs", PROTOCOL["epochs"]), ("num_samples", PROTOCOL["num_samples"]),
                      ("lr", PROTOCOL["lr"]), ("warmup", PROTOCOL["warmup"]),
                      ("compute_dtype", PROTOCOL["compute_dtype"]), ("opt", PROTOCOL["opt"]),
                      ("block_config", PROTOCOL["block_config"]),
                      ("grad_mask", PROTOCOL["grad_mask"]), ("attn_targets", PROTOCOL["attn_targets"]),
                      ("batch_size", PROTOCOL["batch_size"]), ("proj_rank", None),
                      ("data_offset", 0), ("target_proj", False), ("lang_only", False)):
        if key not in d:
            return "payload has no field %s" % key
        if d[key] != want:
            return "payload %s = %r != protocol %r" % (key, d[key], want)
    if d.get("ok") is not True:
        return "payload ok is not true"
    if not isinstance(d.get("E"), list) or len(d["E"]) != PROTOCOL["epochs"] + 1:
        return "payload E must carry %d values" % (PROTOCOL["epochs"] + 1)
    return None


def map_records(stack: dict) -> tuple:
    """Read the analysis-map stack (torch29) from the archive that carries its seeds as fields."""
    path = os.path.join(REPO, stack["source"])
    d = load_json(path)
    records, notes, contradictions = [], [], []
    for rank in RANKS:
        key = "r%d" % rank
        values = d.get("values", {}).get(key)
        if not values:
            contradictions.append({"source_file": stack["source"], "reason": "no values.%s" % key})
            continue
        for seed, value in sorted(values.items(), key=lambda kv: int(kv[0])):
            value = finite(value)
            if value is None:
                contradictions.append({"source_file": stack["source"],
                                       "reason": "values.%s.%s is not finite" % (key, seed)})
                continue
            records.append({"stack": stack["id"], "stack_label": stack["label"],
                            "machine": stack["machine"], "torch": stack["torch"],
                            "cuda": stack["cuda"], "place": stack["place"],
                            "rank": rank, "seed": int(seed), "alpha": alpha_for(rank),
                            "delta_E": value, "E0": None,
                            "source_file": stack["source"],
                            "source_field": stack["source_field"] % rank + ".%s" % seed})
        notes.append("%s: rank %d -> %d row(s) from %s (values.%s)"
                     % (stack["id"], rank, len([r for r in records if r["rank"] == rank]),
                        stack["source"], key))
    census = {"id": stack["id"], "kind": stack["kind"], "label": stack["label"],
              "machine": stack["machine"], "torch": stack["torch"], "cuda": stack["cuda"],
              "place": stack["place"], "evidence": stack["evidence"],
              "source_field": stack["source_field"], "protocol": stack["protocol"],
              "notes": notes, "contradictions": contradictions, "files": [stack["source"]]}
    return records, census


def collect_records() -> tuple:
    """Every (stack, rank, seed) cell on disk today, plus the census and the overlap guard."""
    records, census = [], []
    for stack in STACKS:
        rows, block = (map_records(stack) if stack["kind"] == "analysis_map"
                       else file_records(stack))
        records += rows
        census.append(block)
    # Guard: no archive may be claimed by two stacks (a silent overlap would re-introduce exactly the
    # confounding this script exists to remove).
    owner = {}
    for r in records:
        owner.setdefault(r["source_file"], set()).add(r["stack"])
    overlaps = [{"source_file": f, "stacks": sorted(s)} for f, s in owner.items() if len(s) > 1]
    return records, census, overlaps


def in_flight_targets() -> list:
    """The six (stack, rank, seed) cells of the round running now, by target name (not by glob)."""
    out = []
    for rank in RANKS:
        for seed in (7, 123, 999):
            plain = plain_name(rank, seed)
            target = os.path.join(EXP, plain[:-len(".json")] + "_torch26.json")
            untagged = os.path.join(EXP, plain)
            out.append({"stack": "torch26_cu124", "rank": rank, "seed": seed,
                        "target": rel(target), "untagged": rel(untagged),
                        "target_exists": os.path.exists(target),
                        "untagged_exists": os.path.exists(untagged)})
    return out


def matrix(records_by_stack: dict, rank: int) -> dict:
    """Seeds present per stack at one rank, on the whole seed set and on a common seed subset."""
    return {sid: sorted(r["seed"] for r in rows if r["rank"] == rank)
            for sid, rows in records_by_stack.items()}


# ------------------------------------------------------------------------------------------------
# Decomposition and bootstrap (the method already used, plus a cell bootstrap)
# ------------------------------------------------------------------------------------------------
def decomposition(vals_by_env: dict) -> dict:
    """One-way random-effects ANOVA on environment level, exactly as the existing archives.

    sigma_seed^2 = MS_within; sigma_env^2 = max(0, (MS_between - MS_within)/n0) with the unequal-n
    correction n0 = (n - sum(n_i^2)/n)/(k - 1).  `sigma_env_squared_raw` is the same estimate
    *before* the max(0, .) clamp, which is what tells a genuine low environment variance apart from
    a moment estimate that cannot be formed (negative numerator).
    """
    envs = {k: [float(x) for x in v] for k, v in vals_by_env.items() if v}
    if len(envs) < 2:
        return {"k": len(envs), "n": sum(len(v) for v in envs.values()),
                "sigma_env": None, "sigma_seed": None, "env_variance_share": None,
                "sigma_env_squared_raw": None, "n_per_env": {k: len(v) for k, v in envs.items()},
                "note": "fewer than two environments populated"}
    k = len(envs)
    allv = [x for v in envs.values() for x in v]
    n = len(allv)
    grand = float(np.mean(allv))
    ssb = sum(len(v) * (float(np.mean(v)) - grand) ** 2 for v in envs.values())
    ssw = sum(sum((x - float(np.mean(v))) ** 2 for x in v) for v in envs.values())
    dfb, dfw = k - 1, n - k
    msb = ssb / dfb if dfb else 0.0
    msw = ssw / dfw if dfw else 0.0
    n0 = (n - sum(len(v) ** 2 for v in envs.values()) / n) / (k - 1)
    raw = (msb - msw) / n0 if n0 else 0.0
    sig2_env = max(0.0, raw)
    sig2_seed = msw
    share = sig2_env / (sig2_env + sig2_seed) if (sig2_env + sig2_seed) > 0 else 0.0
    return {
        "k": k, "n": n, "n_per_env": {k2: len(v) for k2, v in envs.items()},
        "grand_mean": grand, "ss_between": ssb, "ss_within": ssw,
        "df_between": dfb, "df_within": dfw, "ms_between": msb, "ms_within": msw, "n0": n0,
        "sigma_env": float(np.sqrt(sig2_env)), "sigma_seed": float(np.sqrt(sig2_seed)),
        "env_variance_share": float(share), "sigma_env_squared_raw": float(raw),
        "clamped_at_zero": bool(raw < 0),
    }


def bootstrap(env_values: dict, mode: str, n_boot: int, rng_seed: int) -> dict:
    """Percentile bootstrap of the decomposition, fixed rng seed.

    mode "within"  -- resample each environment's own values independently (the resampling unit of
                      the archived tools/_p1570_env_variance_update.py bootstrap);
    mode "paired"  -- use one index set per draw for every environment, i.e. resample *cells* while
                      keeping the seed pairing across stacks (this is what a common-seed design
                      makes possible; it requires equal n per environment).
    """
    envs = {k: [float(x) for x in v] for k, v in env_values.items() if v}
    counts = {len(v) for v in envs.values()}
    if len(envs) < 2 or not counts:
        return {"mode": mode, "n_boot": 0, "note": "fewer than two environments populated"}
    if mode == "paired" and len(counts) != 1:
        return {"mode": mode, "n_boot": 0,
                "note": "paired bootstrap needs an equal number of observations per environment "
                        "(got %s)" % sorted(counts)}
    rng = np.random.default_rng(rng_seed)
    names = sorted(envs)
    m = sorted(counts)[0]
    env_sigma, seed_sigma, shares, raw = [], [], [], []
    for _ in range(n_boot):
        if mode == "paired":
            idx = rng.integers(0, m, m)
            draw = {k: [envs[k][i] for i in idx] for k in names}
        else:
            draw = {k: list(rng.choice(envs[k], len(envs[k]))) for k in names}
        dec = decomposition(draw)
        if dec.get("sigma_env") is None:
            continue
        env_sigma.append(dec["sigma_env"])
        seed_sigma.append(dec["sigma_seed"])
        shares.append(dec["env_variance_share"])
        raw.append(dec["sigma_env_squared_raw"])
    if not shares:
        return {"mode": mode, "n_boot": 0, "note": "no replicate produced a decomposition"}
    lo, hi = float(np.percentile(shares, 2.5)), float(np.percentile(shares, 97.5))
    elo, ehi = float(np.percentile(env_sigma, 2.5)), float(np.percentile(env_sigma, 97.5))
    slo, shi = float(np.percentile(seed_sigma, 2.5)), float(np.percentile(seed_sigma, 97.5))
    rlo, rhi = float(np.percentile(raw, 2.5)), float(np.percentile(raw, 97.5))
    return {
        "mode": mode, "n_boot": len(shares), "rng_seed": rng_seed,
        "share_mean": float(np.mean(shares)), "share_ci95": [lo, hi],
        "share_ci95_width": hi - lo, "share_sd": float(np.std(shares, ddof=1)),
        "sigma_env_mean": float(np.mean(env_sigma)),
        "sigma_env_ci95": [elo, ehi], "sigma_env_ci95_width": ehi - elo,
        "sigma_seed_mean": float(np.mean(seed_sigma)),
        "sigma_seed_ci95": [slo, shi], "sigma_seed_ci95_width": shi - slo,
        "sigma_env_squared_raw_ci95": [rlo, rhi],
        "sigma_env_neg_raw_fraction": float(np.mean([1.0 if x < 0 else 0.0 for x in raw])),
        "note": "percentile bootstrap over the cells of the design; the fixed rng seed makes the "
                "archive deterministic",
    }


# ------------------------------------------------------------------------------------------------
# Cost: per-run wall clock measured by the existing archives
# ------------------------------------------------------------------------------------------------
def measured_local_times() -> tuple:
    """Every per-run wall clock this protocol actually recorded, with the archive path per value."""
    runs, sources = [], []
    for rel_path in LOCAL_TIMING_SOURCES:
        path = os.path.join(REPO, rel_path)
        if not os.path.exists(path):
            continue
        d = load_json(path)
        sources.append(rel_path)
        for key, row in sorted(d.get("runs", {}).items()):
            if int(row.get("rank", -1)) not in LOCAL_TIMING_RANKS:
                continue
            minutes = finite(row.get("elapsed_min"))
            if minutes is None:
                continue
            runs.append({"rank": int(row["rank"]), "seed": int(row.get("seed", -1)),
                         "elapsed_min": minutes, "source_file": rel_path,
                         "source_field": "runs.%s.elapsed_min" % key})
    logs = []
    values = []
    for path in sorted(glob.glob(LOCAL_TRAINING_LOG_GLOB)):
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for line in text.splitlines():
            if "Training time:" not in line:
                continue
            digits = "".join(c for c in line.split("Training time:")[1] if c.isdigit())
            if not digits:
                continue
            minutes = int(digits) / 60.0
            values.append(minutes)
            logs.append({"source_file": rel(path), "source_field": "Training time (seconds)",
                         "elapsed_min": minutes})
    return {"runs": runs, "logs": logs, "sources": sources}, [r["elapsed_min"] for r in runs] + values


def cost_estimate(missing: list, common_seeds: tuple) -> dict:
    """GPU hours for the missing cells, with the basis of every per-run time stated."""
    timing, values = measured_local_times()
    values = sorted(values)
    median = float(np.median(values)) if values else None
    used = {}
    for cell in missing:
        sid = cell["stack"]
        if sid not in used:
            # Only the torch29 archives of this protocol recorded a per-run wall clock, and those
            # runs are on the machine of the two local stacks (RTX 4060 Laptop); the cloud stack's
            # rows carry no elapsed field at all.  Anything else is stated as unknown.
            used[sid] = {
                "per_run_min": median if sid == "torch29_cu130" else None,
                "basis": ("median of the %d per-run `elapsed_min` values recorded by %s for this "
                          "protocol (ranks 5/6): %s minutes; the runs are on the same machine as the "
                          "stack" % (len(values), ", ".join(timing["sources"]),
                                     ", ".join("%.1f" % v for v in values))
                          if sid == "torch29_cu130" else
                          "unknown: no per-run wall clock for this stack exists in the archives of "
                          "this protocol (the cloud_verify rows carry no elapsed field)"),
            }
    measured_min = 0.0
    unknown_cells = 0
    for cell in missing:
        per_run = used[cell["stack"]]["per_run_min"]
        if per_run is None:
            unknown_cells += 1
        else:
            measured_min += per_run
    by_place = {}
    for cell in missing:
        by_place[cell["place"]] = by_place.get(cell["place"], 0) + 1
    return {
        "n_missing_cells": len(missing),
        "n_missing_by_place": by_place,
        "per_run_minutes_by_stack": used,
        "measured_local_runs": timing["runs"],
        "measured_local_log_runs": timing["logs"],
        "measured_median_min_per_run": median,
        "measured_n_runs": len(values),
        "gpu_hours_measured_only": round(measured_min / 60.0, 2),
        "gpu_hours_if_unknown_priced_at_measured_median": (
            round((measured_min + (unknown_cells * median)) / 60.0, 2) if median else None),
        "n_cells_with_unknown_per_run_time": unknown_cells,
        "note": "every emitted cell is the archived 20-sample / 3-epoch protocol; the measured "
                "per-run times are the ones this protocol recorded on the local machine, and the "
                "cloud rows of the same protocol carry no elapsed field, so the cloud share of the "
                "estimate is reported as unknown rather than priced by assumption.  The in-flight "
                "torch26 round logs its own wall time to "
                "outputs/analysis/p3_env_seeds_runlog.json (elapsed_seconds) and will replace the "
                "unknown for that stack.",
    }


# ------------------------------------------------------------------------------------------------
# Audit mode
# ------------------------------------------------------------------------------------------------
def audit(common_seeds: tuple) -> dict:
    records, census, overlaps = collect_records()
    by_stack = {}
    for r in records:
        by_stack.setdefault(r["stack"], []).append(r)
    stacks = [c["id"] for c in census]
    today = {rank: matrix(by_stack, rank) for rank in RANKS}
    counts = {rank: {sid: len(today[rank].get(sid, [])) for sid in stacks} for rank in RANKS}
    common = {rank: {sid: [s for s in today[rank].get(sid, []) if s in common_seeds]
                     for sid in stacks} for rank in RANKS}
    single = [{"stack": sid, "rank": rank, "seed": today[rank][sid][0]}
              for rank in RANKS for sid in stacks if len(today[rank].get(sid, [])) == 1]
    all_counts = [c for rank in RANKS for c in counts[rank].values()]
    return {"records": records, "census": census, "overlaps": overlaps,
            "by_stack": by_stack, "stacks": stacks, "today": today, "counts": counts,
            "common_today": common, "single_seed_cells": single,
            "imbalance": {
                "n_cells": len(records),
                "seed_count_min": min(all_counts) if all_counts else 0,
                "seed_count_max": max(all_counts) if all_counts else 0,
                "seed_count_range": (max(all_counts) - min(all_counts)) if all_counts else 0,
                "per_rank_seed_counts": {str(r): counts[r] for r in RANKS},
                "n_cells_with_one_seed": len(single),
                "common_seed_overlap": {str(r): {sid: len(common[r][sid]) for sid in stacks}
                                        for r in RANKS},
                "design": "4 stacks x 2 ranks x (%d common seeds) = %d cells for a balanced design"
                          % (len(common_seeds), len(stacks) * len(RANKS) * len(common_seeds)),
            }}


def print_audit(a: dict, common_seeds: tuple) -> None:
    stacks = a["stacks"]
    print("=" * 118)
    print("P3 ENVIRONMENT MATRIX AUDIT -- cells present today, stack identified from each file's own")
    print("metadata / archive field, never from a loose glob")
    print("=" * 118)
    print("\nRegistry (stack identity and the evidence for it)")
    print("  %-16s %-16s %-20s %-9s %s" % ("stack", "label", "machine", "place", "archives / fields"))
    for c in a["census"]:
        print("  %-16s %-16s %-20s %-9s %s" % (c["id"], c["label"], c["machine"][:20], c["place"],
                                               "%d file(s)" % len(c["files"])))
        print("      evidence: %s" % c["evidence"])
        print("      validating field(s): %s" % c["source_field"])
    if a["overlaps"]:
        print("\n  !! OVERLAP: %s" % a["overlaps"])
    else:
        print("\n  overlap guard: no archive is claimed by two stacks (OK)")

    for rank in RANKS:
        print("\n" + "-" * 118)
        print("RANK %d -- seeds present per stack" % rank)
        print("-" * 118)
        print("  %-16s %-16s %-6s  %s" % ("stack", "label", "n", "seeds present"))
        for sid in stacks:
            c = next(x for x in a["census"] if x["id"] == sid)
            seeds = a["today"][rank].get(sid, [])
            flag = "  <- SINGLE SEED" if len(seeds) == 1 else ""
            print("  %-16s %-16s %-6d  %s%s" % (sid, c["label"], len(seeds),
                                                ", ".join(str(s) for s in seeds), flag))
        n = a["counts"][rank]
        print("  seeds per stack: min %d, max %d (range %d)"
              % (min(n.values()), max(n.values()), max(n.values()) - min(n.values())))

    print("\n" + "-" * 118)
    print("IMBALANCE (common seed set %s)" % ",".join(str(s) for s in common_seeds))
    print("-" * 118)
    im = a["imbalance"]
    print("  cells today                                   : %d" % im["n_cells"])
    print("  seeds per (stack, rank) cell: min %d, max %d, range %d"
          % (im["seed_count_min"], im["seed_count_max"], im["seed_count_range"]))
    print("  (stack, rank) blocks resting on ONE seed      : %d  %s"
          % (im["n_cells_with_one_seed"],
             ", ".join("%s r%d (seed %d)" % (c["stack"], c["rank"], c["seed"])
                       for c in a["single_seed_cells"]) or "-"))
    for rank in RANKS:
        overlap = im["common_seed_overlap"][str(rank)]
        print("  rank %d: seeds of the common set present per stack: %s"
              % (rank, ", ".join("%s %d/%d" % (sid, overlap[sid], len(common_seeds))
                                 for sid in stacks)))
    print("  balanced design                               : %s" % im["design"])
    print()


# ------------------------------------------------------------------------------------------------
# Plan mode
# ------------------------------------------------------------------------------------------------
def plan(common_seeds: tuple) -> dict:
    records, census, overlaps = collect_records()
    by_stack = {}
    for r in records:
        by_stack.setdefault(r["stack"], []).append(r)
    stacks = [c["id"] for c in census]
    present = {(r["stack"], r["rank"], r["seed"]) for r in records}
    existing_cells = [{"stack": r["stack"], "rank": r["rank"], "seed": r["seed"],
                       "delta_E": r["delta_E"], "E0": r["E0"],
                       "source_file": r["source_file"], "source_field": r["source_field"],
                       "place": r["place"]}
                      for r in sorted(records, key=lambda x: (x["stack"], x["rank"], x["seed"]))]

    flight = in_flight_targets()
    flight_keys = {(f["stack"], f["rank"], f["seed"]) for f in flight}

    existing = []
    missing = []
    for sid in stacks:
        stack = next(s for s in STACKS if s["id"] == sid)
        for rank in RANKS:
            for seed in common_seeds:
                key = (sid, rank, seed)
                if key in present:
                    existing.append({"stack": sid, "rank": rank, "seed": seed})
                    continue
                item = {"stack": sid, "stack_label": stack["label"], "rank": rank, "seed": seed,
                        "alpha": alpha_for(rank), "place": stack["place"],
                        "interpreter": stack["interpreter"] if stack["place"] == "LOCAL" else None,
                        "in_flight": key in flight_keys}
                if stack["kind"] == "files":
                    suffix = {"torch24_cu121": "torch24", "torch26_cu124": "torch26",
                              "torch212_cu130": None}.get(sid)
                    plain = os.path.join(EXP, plain_name(rank, seed))
                    target = (plain if suffix is None
                              else plain[:-len(".json")] + "_%s.json" % suffix)
                    if sid == "torch212_cu130":
                        target = os.path.join(EXP, "cloud_" + os.path.basename(plain))
                    item["target_archive"] = rel(target)
                    if sid == "torch26_cu124":
                        item["target_archive_note"] = (
                            "tools/_p1613_p3_cloud_runner.py writes this row, validates it and "
                            "renames it to the _torch26 suffix; run_training.py itself cannot write "
                            "the suffix")
                    if suffix:
                        item["tagging"] = ("run %s, then copy the untagged output to %s -- the "
                                           "training script cannot write the stack suffix, and the "
                                           "untagged name belongs to another stack's archived row"
                                           % (os.path.basename(plain), os.path.basename(target)))
                else:
                    item["target_archive"] = "outputs/analysis/p3_seeds_combined.json"
                    item["target_archive_note"] = ("this stack's rows are seed->value fields in the "
                                                   "map archive, added by the analysis of its runs")
                missing.append(item)

    cost = cost_estimate(missing, common_seeds)
    commands = []
    for item in sorted(missing, key=lambda x: (x["place"] != "LOCAL", x["stack"], x["rank"],
                                               x["seed"])):
        stack = next(s for s in STACKS if s["id"] == item["stack"])
        argv = build_train_command(item["rank"], item["seed"], python=stack["interpreter"])
        per_run = cost["per_run_minutes_by_stack"][item["stack"]]["per_run_min"]
        entry = {
            "stack": item["stack"], "stack_label": item["stack_label"],
            "rank": item["rank"], "seed": item["seed"], "alpha": item["alpha"],
            "place": item["place"], "in_flight": item["in_flight"],
            "interpreter": stack["interpreter"], "cwd": ".",
            "command": printable(argv, stack),
            "argv": argv,
            "target_archive": item["target_archive"],
            "expected_runtime": ("~%.1f min (measured median of this protocol)" % per_run
                                 if per_run else "unknown: no per-run wall clock archived for this "
                                                 "stack"),
        }
        if item["place"] == "CLOUD":
            entry["command"] = printable(argv, {**stack, "place": "CLOUD"})
            entry["cloud_entry_point"] = "cloud_next/p3_env_seeds.sh / %s --job env-seeds" % LOCAL_RUNNER
            entry["cloud_note"] = ("on the instance the archived invocation of " + CLOUD_NOTES +
                                   " section 3 is reproduced by %s --job env-seeds, which refuses "
                                   "to write a _torch26/-tagged row from a mismatched torch and "
                                   "records the row's sha256 and wall time in "
                                   "outputs/analysis/p3_env_seeds_runlog.json" % LOCAL_RUNNER)
        else:
            entry["local_note"] = ("run with this stack's own interpreter; the file's payload "
                                   "records the protocol, which is what makes the stack label "
                                   "trustworthy")
        if item["in_flight"]:
            # These cells are produced by the round running now; the runnable command for this stack
            # is the round's own runner, which skips a cell whose output already validates.
            entry["resume_guard"] = (
                "already scheduled by the round in flight: do NOT run this command by hand. Check "
                "%s first; if it exists the cell is done. The round's own resumable path is `%s "
                "--job env-seeds` (it skips every cell whose output already validates), and its "
                "aggregation is `%s --job env-seeds --aggregate`."
                % (item["target_archive"], LOCAL_RUNNER, LOCAL_RUNNER))
        if item.get("tagging"):
            entry["tagging"] = item["tagging"]
        commands.append(entry)

    return {"records": records, "census": census, "overlaps": overlaps, "by_stack": by_stack,
            "stacks": stacks, "existing_cells": existing_cells, "missing_cells": missing,
            "commands": commands, "cost_estimate": cost, "in_flight_cells": flight,
            "common_seeds": list(common_seeds), "present_keys": present}


# ------------------------------------------------------------------------------------------------
# Power mode
# ------------------------------------------------------------------------------------------------
def env_values_for(design: str, plan_data: dict, common_seeds: tuple) -> dict:
    """Rank-5 values per stack for one of the three designs this script compares."""
    records = plan_data["records"]
    if design == "today_all_seeds":
        return {sid: [r["delta_E"] for r in records if r["stack"] == sid
                      and r["rank"] == MAIN_HYPOTHESIS_RANK] for sid in plan_data["stacks"]}
    if design == "balanced_common_seed":
        return {sid: [r["delta_E"] for r in records if r["stack"] == sid
                      and r["rank"] == MAIN_HYPOTHESIS_RANK and r["seed"] in common_seeds]
                for sid in plan_data["stacks"]}
    if design == "balanced_archived_common_seed":
        return {sid: [r["delta_E"] for r in records if r["stack"] == sid
                      and r["rank"] == MAIN_HYPOTHESIS_RANK and r["seed"] in common_seeds]
                for sid in plan_data["stacks"]}
    raise ValueError(design)


def power(plan_data: dict, common_seeds: tuple) -> dict:
    """What sigma_env / sigma_seed / the environment share would be, and the CI width change."""
    today = {sid: [r["delta_E"] for r in plan_data["records"]
                   if r["stack"] == sid and r["rank"] == MAIN_HYPOTHESIS_RANK]
             for sid in plan_data["stacks"]}
    today = {k: v for k, v in today.items() if v}
    flights = plan_data["in_flight_cells"]
    arrived = {(f["stack"], f["rank"], f["seed"]) for f in flights if f["target_exists"]}
    balanced = {sid: [r["delta_E"] for r in plan_data["records"]
                      if r["stack"] == sid and r["rank"] == MAIN_HYPOTHESIS_RANK
                      and r["seed"] in common_seeds]
                for sid in plan_data["stacks"]}
    balanced = {k: v for k, v in balanced.items() if v}
    reached = [sid for sid, v in balanced.items()
               if len(v) == len(common_seeds) and all(
                   (sid, MAIN_HYPOTHESIS_RANK, s) in plan_data["present_keys"]
                   for s in common_seeds)]

    dec_today = decomposition(today)
    dec_balanced = decomposition(balanced)
    boot_today = bootstrap(today, "within", N_BOOT, RNG_SEED)
    boot_balanced_cells = bootstrap(balanced, "paired", N_BOOT, RNG_SEED) if reached else {
        "mode": "paired", "n_boot": 0,
        "note": "the balanced common-seed design is not fully archived yet: %d/%d stacks carry all "
                "%d common seeds, so the paired (cell) bootstrap of the planned design cannot be "
                "computed from measured values" % (len(reached), len(plan_data["stacks"]),
                                                   len(common_seeds))}
    boot_balanced_within = bootstrap(balanced, "within", N_BOOT, RNG_SEED)
    boot_archived_within = bootstrap(today, "within", N_BOOT, RNG_SEED)

    # The strongest statement the *today* design allows about the environment term: the seed set
    # that is actually common to every populated stack at this rank.  When that intersection is a
    # single seed every environment contributes exactly one observation, so the within-environment
    # term has 0 degrees of freedom and sigma_seed / the environment share are not identified --
    # which is the confounding this plan removes, and it is worth showing next to the CI widths.
    seeds_by_stack = {sid: {r["seed"] for r in plan_data["records"]
                            if r["stack"] == sid and r["rank"] == MAIN_HYPOTHESIS_RANK}
                      for sid in plan_data["stacks"]}
    seeds_by_stack = {k: v for k, v in seeds_by_stack.items() if v}
    anchor_seeds = tuple(sorted(set.intersection(*seeds_by_stack.values()))) \
        if len(seeds_by_stack) >= 2 else ()
    anchor = anchor_seeds[0] if anchor_seeds else None
    anchor_design = {sid: [r["delta_E"] for r in plan_data["records"]
                           if r["stack"] == sid and r["rank"] == MAIN_HYPOTHESIS_RANK
                           and r["seed"] in anchor_seeds]
                     for sid in plan_data["stacks"]} if anchor_seeds else {}
    anchor_design = {k: v for k, v in anchor_design.items() if v}
    dec_anchor = decomposition(anchor_design) if anchor_design else {}
    anchor_identified = bool(dec_anchor) and (dec_anchor.get("df_within") or 0) > 0

    # The design the plan lands on, priced from measured values only: for the cells that are
    # already archived this is a real value, for the cells still missing the value does not exist
    # yet and is reported as missing rather than predicted.  It is here so the operator can see the
    # shape the plan produces (4 seeds on 4 stacks at each rank) before any run starts.
    planted_shape = {sid: len(balanced.get(sid, [])) for sid in plan_data["stacks"]}
    planted_missing = [{"stack": c["stack"], "rank": c["rank"], "seed": c["seed"]}
                       for c in plan_data["missing_cells"]]

    def ci_width(boot: dict) -> float | None:
        return boot.get("share_ci95_width")

    out = {
        "method": {
            "estimator": "one-way random-effects ANOVA on the environment level, with the unequal-n "
                         "correction n0 = (n - sum(n_i^2)/n)/(k - 1); sigma_seed^2 = MS_within, "
                         "sigma_env^2 = max(0, (MS_between - MS_within)/n0)",
            "cited_implementation": "%s decomposition() (the same one-way random-effects ANOVA with "
                                    "the unequal-n correction n0 as tools/_p1570_env_variance_update.py)"
                                    % LOCAL_RUNNER,
            "cited_archive_fields": {
                "outputs/analysis/p3_env_variance.json": ["meta.method", "sigma_env", "sigma_seed",
                                                          "env_share", "bootstrap.share_mean",
                                                          "bootstrap.share_ci95"],
                "outputs/analysis/p3_env_stack_seeds.json": ["sigma_env", "sigma_seed",
                                                             "env_variance_share",
                                                             "sigma_by_rank.<rank>.all_rows",
                                                             "sigma_by_rank.<rank>."
                                                             "balanced_common_seed"],
                "outputs/analysis/p3_balanced_design_plan.json (this file)":
                    ["power_comparison.designs.*"]},
            "bootstrap": "percentile bootstrap, %d replicates, fixed rng seed %d; the archive-"
                         "consistent variant resamples seeds within each environment, the cell "
                         "variant resamples cells with one shared index set (possible only for a "
                         "common-seed design) -- both are reported" % (N_BOOT, RNG_SEED),
        },
        "rank": MAIN_HYPOTHESIS_RANK,
        "common_seeds": list(common_seeds),
        "archived_reference_today": {
            "source_file": "outputs/analysis/p3_env_variance.json",
            "sigma_env": SIGMA_ENV_ARCHIVE, "sigma_seed": SIGMA_SEED_ARCHIVE,
            "env_share": ENV_SHARE_ARCHIVE,
            "bootstrap_share_ci95": list(SHARE_CI95_ARCHIVE),
            "bootstrap_share_ci95_width": SHARE_CI95_ARCHIVE[1] - SHARE_CI95_ARCHIVE[0],
            "note": "the archived three-stack value; it is NOT reproducible today because that "
                    "script's torch 2.4/cu121 bucket uses the loose glob verify_r5_s*_a10*.json, "
                    "which now also matches the _a10_torch26 rows",
        },
        "designs": {
            "unbalanced_today": {
                "definition": "every seed each stack happens to have at rank 5",
                "n_per_stack": dec_today.get("n_per_env"),
                "values_by_stack": today,
                "decomposition": dec_today,
                "bootstrap_within": boot_today,
                "bootstrap_archived_method_same_inputs": boot_archived_within,
            },
            "balanced_common_seed": {
                "definition": "the %d common seeds on every stack at rank 5" % len(common_seeds),
                "n_per_stack": dec_balanced.get("n_per_env"),
                "values_by_stack": balanced,
                "stacks_with_all_common_seeds": reached,
                "missing_common_seed_cells": planted_missing,
                "decomposition": dec_balanced,
                "bootstrap_cells_paired": boot_balanced_cells,
                "bootstrap_within": boot_balanced_within,
            },
            "anchor_seed_today": {
                "definition": "the seed set common to every populated stack at rank 5: the strongest "
                              "environment statement today's design permits",
                "common_seed_intersection": list(anchor_seeds),
                "n_common_anchor_seeds": len(anchor_seeds),
                "seed": (anchor if len(anchor_seeds) == 1 else None),
                "seeds": list(anchor_seeds),
                "n_per_stack": dec_anchor.get("n_per_env") if dec_anchor else None,
                "values_by_stack": anchor_design,
                "decomposition": dec_anchor,
                "identified": anchor_identified,
                "estimability_note": (
                    "identified" if anchor_identified else
                    "NOT identified: this intersection leaves %s degree(s) of freedom within "
                    "environments, so neither sigma_seed nor the environment share can be formed "
                    "from this design (the estimator returns sigma_seed 0 and share 1, which is a "
                    "degenerate artefact, not a measurement). This is the confounding the "
                    "common-seed plan removes."
                    % (dec_anchor.get("df_within") if dec_anchor else 0)),
            },
        },
        "planned_design_shape": {
            "note": "what the plan produces once every missing cell is archived; no value is "
                    "predicted for a cell that does not exist yet",
            "seeds_per_stack_at_rank5_now": planted_shape,
            "seeds_per_stack_at_rank5_after_plan": {sid: len(common_seeds)
                                                    for sid in plan_data["stacks"]},
            "cells_still_missing_at_rank5": [c for c in planted_missing
                                             if c["rank"] == MAIN_HYPOTHESIS_RANK],
            "cells_still_missing_at_rank6": [c for c in planted_missing
                                             if c["rank"] != MAIN_HYPOTHESIS_RANK],
        },
        "ci_width_change": {
            "basis": "the archive-consistent bootstrap (resample seeds within each environment, "
                     "fixed rng seed) is the one comparable to the archived bootstrap.share_ci95",
            "unbalanced_today_share_ci95": boot_today.get("share_ci95"),
            "unbalanced_today_share_ci95_width": ci_width(boot_today),
            "balanced_common_seed_share_ci95": boot_balanced_within.get("share_ci95"),
            "balanced_common_seed_share_ci95_width": ci_width(boot_balanced_within),
            "width_ratio_balanced_over_today": (
                (ci_width(boot_balanced_within) / ci_width(boot_today))
                if ci_width(boot_today) and ci_width(boot_balanced_within) else None),
            "width_change_pct": (
                100.0 * (ci_width(boot_balanced_within) - ci_width(boot_today)) / ci_width(boot_today)
                if ci_width(boot_today) and ci_width(boot_balanced_within) else None),
            "sigma_env_ci95_today": boot_today.get("sigma_env_ci95"),
            "sigma_env_ci95_balanced": boot_balanced_within.get("sigma_env_ci95"),
            "sigma_env_ci95_width_today": boot_today.get("sigma_env_ci95_width"),
            "sigma_env_ci95_width_balanced": boot_balanced_within.get("sigma_env_ci95_width"),
            "cell_bootstrap_note": boot_balanced_cells.get("note"),
            "reading_the_width_change": (
                "Today's share CI95 width %.3f comes from a design in which the stacks contribute "
                "%s seeds; the balanced width %.3f comes from a design in which every stack "
                "contributes exactly %d. The balanced width is the one estimated from matched seed "
                "sets, so it is the one that can be read as an environment effect; today's narrower "
                "or wider interval is not comparable because it mixes the between-stack contrast "
                "with which seeds each stack happens to carry. sigma_env itself moves from %.1f to "
                "%.1f (sigma_env CI95 width %.1f -> %.1f), and the share from %.3f to %.3f."
                % (ci_width(boot_today) or float("nan"),
                   dec_today.get("n_per_env"), ci_width(boot_balanced_within) or float("nan"),
                   len(common_seeds), dec_today.get("sigma_env") or float("nan"),
                   dec_balanced.get("sigma_env") or float("nan"),
                   boot_today.get("sigma_env_ci95_width") or float("nan"),
                   boot_balanced_within.get("sigma_env_ci95_width") or float("nan"),
                   dec_today.get("env_variance_share") or float("nan"),
                   dec_balanced.get("env_variance_share") or float("nan"))),
            "clamped_estimate_note": (
                "sigma_env of the unbalanced design is %s (sigma_env^2 raw %.1f%s); the balanced "
                "design gives %s (raw %.1f%s). A clamped value means the moment estimate could not "
                "be formed (negative numerator), which is itself a consequence of the imbalance and "
                "not evidence that the environment variance is zero"
                % (dec_today.get("sigma_env"), dec_today.get("sigma_env_squared_raw") or 0.0,
                   ", clamped" if dec_today.get("clamped_at_zero") else "",
                   dec_balanced.get("sigma_env"), dec_balanced.get("sigma_env_squared_raw") or 0.0,
                   ", clamped" if dec_balanced.get("clamped_at_zero") else "")),
        },
    }
    return out


# ------------------------------------------------------------------------------------------------
# Report mode: assemble the plan archive
# ------------------------------------------------------------------------------------------------
def build_archive(args, plan_data: dict, power_block: dict) -> dict:
    common_seeds = plan_data["common_seeds"]
    audit_block = audit(tuple(common_seeds))
    n_local = len([c for c in plan_data["missing_cells"] if c["place"] == "LOCAL"])
    n_cloud = len([c for c in plan_data["missing_cells"] if c["place"] == "CLOUD"])
    cost = plan_data["cost_estimate"]
    reached = power_block["designs"]["balanced_common_seed"]["stacks_with_all_common_seeds"]
    gpu_hours = cost["gpu_hours_if_unknown_priced_at_measured_median"]

    conclusion = {
        "gpu_hours_for_a_balanced_design": {
            "measured_only": cost["gpu_hours_measured_only"],
            "with_unknown_per_run_times_priced_at_the_measured_median":
                cost["gpu_hours_if_unknown_priced_at_measured_median"],
            "n_cells_with_unknown_per_run_time": cost["n_cells_with_unknown_per_run_time"],
            "n_missing_cells": cost["n_missing_cells"],
            "n_missing_cells_already_scheduled_by_the_round_in_flight":
                len([c for c in plan_data["missing_cells"] if c["in_flight"]]),
            "n_missing_cells_that_need_a_new_run":
                len([c for c in plan_data["missing_cells"] if not c["in_flight"]]),
            "basis": cost["note"],
        },
        "what_it_buys": (
            "A balanced common-seed design removes the confounding between the environment term and "
            "the seeds a stack happens to have: with %d seeds on all %d stacks at rank %d the "
            "between-environment and within-environment sums of squares are no longer driven by "
            "which stack has more seeds, and the environment share is estimated from matched seed "
            "sets%s. %d/%d stacks currently carry all %d common seeds; after the plan the "
            "environment share is %.3f with CI95 %s (width %.3f) against %.3f with CI95 %s "
            "(width %.3f) today, and sigma_env is %.1f against %.1f."
            % (len(common_seeds), len(plan_data["stacks"]), MAIN_HYPOTHESIS_RANK,
               (" (on today's design the seed set common to every populated stack is %s, which "
                "leaves %s degree(s) of freedom within environments, so the share is not even "
                "identified)"
                % (",".join(str(s) for s in
                            power_block["designs"]["anchor_seed_today"]
                            ["common_seed_intersection"]),
                   power_block["designs"]["anchor_seed_today"]["decomposition"].get("df_within")
                   if power_block["designs"]["anchor_seed_today"]["decomposition"] else 0)
                if not power_block["designs"]["anchor_seed_today"]["identified"] else
                " (the seed set common to every populated stack today is %s)"
                % ",".join(str(s) for s in
                           power_block["designs"]["anchor_seed_today"]
                           ["common_seed_intersection"])),
               len(reached), len(plan_data["stacks"]), len(common_seeds),
               power_block["designs"]["balanced_common_seed"]["decomposition"]
               ["env_variance_share"],
               _fmt_ci(power_block["ci_width_change"]["balanced_common_seed_share_ci95"]),
               power_block["ci_width_change"]["balanced_common_seed_share_ci95_width"]
               or float("nan"),
               power_block["designs"]["unbalanced_today"]["decomposition"]["env_variance_share"],
               _fmt_ci(power_block["ci_width_change"]["unbalanced_today_share_ci95"]),
               power_block["ci_width_change"]["unbalanced_today_share_ci95_width"] or float("nan"),
               power_block["designs"]["balanced_common_seed"]["decomposition"]["sigma_env"],
               power_block["designs"]["unbalanced_today"]["decomposition"]["sigma_env"])),
        "caveats": [
            "the rank-6 side of the design is planned and priced the same way; S37's headline "
            "decomposition is the rank-5 one",
            "the torch26 rows are produced by the training script and only become stack-tagged rows "
            "after the runner copies them to the _torch26 name; run_training.py overwrites the "
            "untagged name, which belongs to another stack's archived row, so that name must be "
            "preserved (the runner saves and restores it)",
            "a common-seed design does not remove the hardware mixing inside the torch26 stack "
            "(seed 42 on the workstation, seeds 7/123/999 on the cloud GPU), which the S29 machine "
            "column must state",
            "the per-run wall clock of the torch24 and cloud stacks is not recorded by any archive "
            "of this protocol, so their share of the GPU-hour estimate is stated as unknown",
        ],
    }
    return {
        "meta": {
            "script": SCRIPT_NAME,
            "generated_by": " ".join(sys.argv),
            "modes": {"audit": bool(args.audit), "plan": bool(args.plan), "power": bool(args.power),
                      "dry_run": bool(args.dry_run)},
            "common_seeds": list(common_seeds),
            "ranks": list(RANKS),
            "main_hypothesis_rank": MAIN_HYPOTHESIS_RANK,
            "protocol": PROTOCOL,
            "protocol_fields_validated_per_file": list(PROTOCOL_FIELDS),
            "stack_registry": [
                {"id": s["id"], "label": s["label"], "machine": s["machine"], "torch": s["torch"],
                 "cuda": s["cuda"], "place": s["place"], "interpreter": s["interpreter"],
                 "evidence": s["evidence"]} for s in STACKS],
            "stack_metadata_archive": STACK_METADATA_ARCHIVE,
            "no_loose_globs": ("stack membership comes from the explicit registry above; the loose "
                              "glob of tools/_p1570_env_variance_update.py "
                              "(verify_r5_s*_a10*.json) is known to be wrong today and is not reused"),
            "deterministic": "integer rng seed %d, no wall-clock field" % RNG_SEED,
            "n_boot": N_BOOT,
            "rng_seed": RNG_SEED,
        },
        "existing_cells": plan_data["existing_cells"],
        "in_flight_cells": plan_data["in_flight_cells"],
        "missing_cells": plan_data["missing_cells"],
        "commands": plan_data["commands"],
        "cost_estimate": cost,
        "power_comparison": power_block,
        "audit": {
            "imbalance": audit_block["imbalance"],
            "single_seed_cells": audit_block["single_seed_cells"],
            "seeds_by_stack_and_rank": {str(r): audit_block["today"][r] for r in RANKS},
            "common_seed_overlap": audit_block["common_today"],
            "census": audit_block["census"],
            "archive_overlaps": audit_block["overlaps"],
        },
        "conclusion": conclusion,
    }


def print_plan(arch: dict) -> None:
    cost, missing = arch["cost_estimate"], arch["missing_cells"]
    n_local = len([c for c in missing if c["place"] == "LOCAL"])
    n_cloud = len([c for c in missing if c["place"] == "CLOUD"])
    print("=" * 118)
    print("P3 BALANCED COMMON-SEED PLAN -- common seeds %s"
          % ",".join(str(s) for s in arch["meta"]["common_seeds"]))
    print("=" * 118)
    print("\nMISSING CELLS (%d): %d LOCAL, %d CLOUD  [%d already present]"
          % (len(missing), n_local, n_cloud, len(arch["existing_cells"])))
    print("  %-16s %-5s %-6s %-6s %-9s %-8s %s"
          % ("stack", "rank", "seed", "alpha", "place", "in-flight", "target archive"))
    for c in sorted(missing, key=lambda x: (x["place"] != "LOCAL", x["stack"], x["rank"], x["seed"])):
        print("  %-16s %-5d %-6d %-6g %-9s %-8s %s"
              % (c["stack"], c["rank"], c["seed"], c["alpha"], c["place"],
                 "yes" if c["in_flight"] else "-", c["target_archive"]))
    print("\nCOMMANDS (copy-pasteable; %d)" % len(arch["commands"]))
    for e in arch["commands"]:
        print("  [%s] %s" % (e["place"], e["command"]))
        if e.get("tagging"):
            print("        then: copy the untagged output to %s" % e["target_archive"])
        if e.get("resume_guard"):
            print("        RESUME GUARD: %s" % e["resume_guard"])
    print("\nCOST")
    print("  measured per-run values (%d runs, %s): %s minutes (median %.1f)"
          % (cost["measured_n_runs"], ", ".join(_timing_sources(cost)),
             ", ".join("%.1f" % r["elapsed_min"] for r in
                       sorted(cost["measured_local_runs"], key=lambda x: x["elapsed_min"])),
             cost["measured_median_min_per_run"] or float("nan")))
    for sid, block in sorted(cost["per_run_minutes_by_stack"].items()):
        print("  %-16s per-run %s" % (sid,
                                      ("%.1f min" % block["per_run_min"]) if block["per_run_min"]
                                      else "UNKNOWN"))
    print("  GPU hours, measured times only                     : %.2f"
          % cost["gpu_hours_measured_only"])
    print("  GPU hours, unknown times at the measured median    : %.2f (%d cell(s) unknown)"
          % (cost["gpu_hours_if_unknown_priced_at_measured_median"] or float("nan"),
             cost["n_cells_with_unknown_per_run_time"]))
    print("\nPOWER (rank %d, common seeds %s)"
          % (arch["power_comparison"]["rank"],
             ",".join(str(s) for s in arch["meta"]["common_seeds"])))
    ch = arch["power_comparison"]["ci_width_change"]
    print("  sigma_env / sigma_seed / share today  : %.1f / %.1f / %.3f"
          % (arch["power_comparison"]["designs"]["unbalanced_today"]["decomposition"]["sigma_env"],
             arch["power_comparison"]["designs"]["unbalanced_today"]["decomposition"]["sigma_seed"],
             arch["power_comparison"]["designs"]["unbalanced_today"]["decomposition"]
             ["env_variance_share"]))
    print("  sigma_env / sigma_seed / share balanced: %.1f / %.1f / %.3f"
          % (arch["power_comparison"]["designs"]["balanced_common_seed"]["decomposition"]
             ["sigma_env"],
             arch["power_comparison"]["designs"]["balanced_common_seed"]["decomposition"]
             ["sigma_seed"],
             arch["power_comparison"]["designs"]["balanced_common_seed"]["decomposition"]
             ["env_variance_share"]))
    print("  share CI95 width today %.3f %s -> balanced %.3f %s"
          % (ch["unbalanced_today_share_ci95_width"] or float("nan"),
             _fmt_ci(ch["unbalanced_today_share_ci95"]),
             ch["balanced_common_seed_share_ci95_width"] or float("nan"),
             _fmt_ci(ch["balanced_common_seed_share_ci95"])))
    anchor = arch["power_comparison"]["designs"]["anchor_seed_today"]
    if anchor["identified"]:
        print("  anchor design (seed(s) %s common to every populated stack): sigma_seed %.3f, "
              "share %.3f"
              % (",".join(str(s) for s in anchor["common_seed_intersection"]),
                 anchor["decomposition"]["sigma_seed"],
                 anchor["decomposition"]["env_variance_share"]))
    else:
        print("  anchor design (seed(s) %s common to every populated stack): NOT identified -- "
              "df_within %s, so sigma_seed / share cannot be formed"
              % (",".join(str(s) for s in anchor["common_seed_intersection"]),
                 anchor["decomposition"].get("df_within") if anchor["decomposition"] else "-"))
    print("  stacks carrying all %d common seeds at rank %d: %d/%d"
          % (len(arch["meta"]["common_seeds"]), arch["power_comparison"]["rank"],
             len(arch["power_comparison"]["designs"]["balanced_common_seed"]
                 ["stacks_with_all_common_seeds"]), len(arch["audit"]["census"])))
    print()


def _timing_sources(cost: dict) -> list:
    return sorted({r["source_file"] for r in cost["measured_local_runs"]})


def _fmt_ci(ci) -> str:
    if not ci:
        return "[n/a]"
    return "[%.3f, %.3f]" % (ci[0], ci[1])


# ------------------------------------------------------------------------------------------------
# Modes
# ------------------------------------------------------------------------------------------------
def parse_common_seeds(text: str) -> tuple:
    seeds = []
    for chunk in text.replace(" ", "").split(","):
        if not chunk:
            continue
        seeds.append(int(chunk))
    if not seeds:
        raise SystemExit("--common-seeds must name at least one integer, got %r" % text)
    if len(set(seeds)) != len(seeds):
        raise SystemExit("--common-seeds repeats a value: %r" % text)
    return tuple(seeds)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="P3 balanced common-seed design for the S29 environment matrix / S37 variance "
                    "decomposition")
    ap.add_argument("--audit", action="store_true",
                    help="print the (stack, rank, seed) matrix that exists today and its imbalance")
    ap.add_argument("--plan", action="store_true",
                    help="compute the missing cells of a balanced design, their commands and cost")
    ap.add_argument("--power", action="store_true",
                    help="report the variance decomposition and the CI width of today's design "
                         "versus the balanced one")
    ap.add_argument("--common-seeds", default=",".join(str(s) for s in DEFAULT_COMMON_SEEDS),
                    help="the common seed set of the balanced design (default 42,7,123,999)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print everything and write nothing")
    args = ap.parse_args(argv)
    if not (args.audit or args.plan or args.power):
        args.plan = True
    common_seeds = parse_common_seeds(args.common_seeds)

    if args.audit:
        print_audit(audit(common_seeds), common_seeds)
        if not (args.plan or args.power):
            return 0

    plan_data = plan(common_seeds)
    power_block = power(plan_data, common_seeds)
    archive = build_archive(args, plan_data, power_block)
    print_plan(archive)
    if args.audit:
        print_audit(audit(common_seeds), common_seeds)

    if args.dry_run:
        print("dry run: nothing was written (would write %s)" % rel(OUT_JSON))
        return 0
    dump_json(OUT_JSON, archive)
    print("wrote %s (%d existing cells, %d missing cells, %d commands)"
          % (rel(OUT_JSON), len(archive["existing_cells"]), len(archive["missing_cells"]),
             len(archive["commands"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())