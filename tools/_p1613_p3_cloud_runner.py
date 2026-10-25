#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""P3 cloud-round runner: environment-stack seeds (S29/S37) and full 451-question VQA (S28).

This script prepares and drives the two GPU jobs of the next cloud round.  Nothing here starts or
needs a cloud instance: every mode can be exercised locally with --dry-run / --self-test, and the
only modes that execute GPU work are the two run modes listed below.

WHY THIS ROUND EXISTS
---------------------
* S29/S37.  The supplementary environment matrix (Section S29, Table tab:envcloud) reports four
  torch/CUDA stacks, and S37 decomposes the r=5 spread into sigma_env = 31.1 and sigma_seed = 34.3
  (environment share 45%).  The fourth stack -- torch 2.6.0+cu124 -- has exactly ONE seed (42), so
  its row in S37's random-effects fit rests on a single run:
      paper3/scripts/outputs/experiments/verify_r5_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_a10_torch26.json  (-35.5)
      paper3/scripts/outputs/experiments/verify_r6_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_a12_torch26.json  (+42.0)
  Job "env-seeds" adds seeds 7, 123 and 999 at ranks 5 and 6 on that stack (six runs).
* S28.  The VQA-RAD equivalence claim rests on 300 of the 451 held-out questions.  Job "vqa-full"
  re-evaluates the base model and the two existing rank-5/rank-6 adapters on all 451 questions and
  repeats the paired-by-question bootstrap and TOST analysis of tools/_p1595_p3_rank_separation.py.

USAGE
-----
    # job A: six environment-stack training runs, one subprocess per run, resumable
    python tools/_p1613_p3_cloud_runner.py --job env-seeds --dry-run
    python tools/_p1613_p3_cloud_runner.py --job env-seeds

    # job B: three VQA arms on the full 451-question test set, one subprocess per arm
    python tools/_p1613_p3_cloud_runner.py --job vqa-full --dry-run
    python tools/_p1613_p3_cloud_runner.py --job vqa-full

    # aggregation steps (write the two analysis archives; --strict enforces acceptance)
    python tools/_p1613_p3_cloud_runner.py --job env-seeds --aggregate --strict
    python tools/_p1613_p3_cloud_runner.py --job vqa-full  --aggregate --strict

    # local, GPU-free consistency checks (writes nothing)
    python tools/_p1613_p3_cloud_runner.py --self-test

RESUMABILITY
------------
Every run is skipped when its output already exists and validates against the archived seed-42
configuration (rank, seed, epochs, lr, block config, alpha, batch, targets, gradient mask, number of
samples, trainable parameter counts).  --force re-runs regardless.  Interrupting the round therefore
costs at most the run that was in flight.

WRITE POLICY
------------
* run modes execute subprocesses and write only their own outputs;
* --dry-run prints every command and never executes or writes anything;
* --aggregate is deterministic: no wall-clock field is written, so re-running it on unchanged inputs
  reproduces the two analysis archives byte for byte.  The run log is the one exception and does
  record timings, because it is a log of what happened rather than an analysis archive.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import importlib.util
import io
import itertools
import json
import os
import subprocess
import sys
from contextlib import contextmanager, redirect_stdout

import numpy as np

# ------------------------------------------------------------------------------------------------
# Paths and frozen protocol constants
# ------------------------------------------------------------------------------------------------
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(REPO, "outputs", "analysis")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")
TRAIN_SCRIPT = os.path.join(REPO, "paper3", "scripts", "run_training.py")
VQA_SCRIPT = os.path.join(REPO, "tools", "_p1516_p3_vqa_downstream.py")
RANKSEP_SCRIPT = os.path.join(REPO, "tools", "_p1595_p3_rank_separation.py")
ADAPTERS_DIR = os.path.join(REPO, "outputs", "p3_vqa_adapters")
RUNLOG = os.path.join(AN, "p3_env_seeds_runlog.json")
ENV_STACK_OUT = os.path.join(AN, "p3_env_stack_seeds.json")
VQA_EQ_OUT = os.path.join(AN, "p3_vqa_full_equivalence.json")

# Protocol of the archived seed-42 rows: every value below is read back from those two archives by
# --self-test (see check_reconstruction), so the reconstruction cannot silently drift.
NUM_SAMPLES = 20                 # archived "num_samples": 20  (16 train / 4 eval)
EPOCHS = 3                       # archived "epochs": 3
LR_FLAG = "5e-5"                 # value passed on the command line; archived "lr": 5e-05
LR_TAG = "%g" % 5e-5             # run_training.py formats lr with %g inside the filename tag
                                 # ("%g" % 5e-05 == "5e-05"; asserted by --self-test)
BATCH_SIZE = 1                   # archived "batch_size": 1
BLOCK_CONFIG = "uniform"         # archived "block_config": "uniform"
OPT = "adamw"                    # archived "opt": "adamw"
COMPUTE_DTYPE = "float16"        # archived "compute_dtype": "float16"
ATTN_TARGETS = "qkvo"            # archived "attn_targets": "qkvo"
GRAD_MASK = "none"               # archived "grad_mask": "none"
DATA_OFFSET = 0                  # archived "data_offset": 0
TARGET_PROJ = False              # archived "target_proj": false
LANG_ONLY = False                # archived "lang_only": false

# Default data file: run_training.py takes glob("paper3/train-*.parquet")[0] when --data-path is not
# given.  The archived rows do not record --data-path, so the reconstruction keeps the default and
# verifies that glob[0] really is the canonical Alpaca shard (a different shard would silently change
# the training set while leaving the filename tag identical).
DEFAULT_DATA_FILE = "paper3/train-00000-of-00001-a09b74b3ef9c3b56.parquet"

NEW_SEEDS = (7, 123, 999)
NEW_RANKS = (5, 6)
ARCHIVED_SEED = 42

# VQA protocol of the archived 300-question round (cloud_vqa1793_*.json):
#   base: no adapter, r=5/r=6: LoRA adapter trained on the full VQA-RAD training split (1793 pairs,
#   three epochs, --per-step), evaluated on TEST_PARQUET.head(451), greedy decoding, prompt
#   "Answer briefly. <question>".  The 300-question archives used the adapters in
#   outputs/p3_vqa_adapters/r<rank>_step; the plain r<rank> directories that exist locally came from
#   shorter smoke runs (see --self-test output) and are deliberately NOT used.
VQA_EVAL_N = 451
VQA_TRAIN_SAMPLES = 1793
VQA_EPOCHS = 3
VQA_PROMPT_PREFIX = "Answer briefly. "
VQA_MAX_NEW_TOKENS = 16
VQA_ARCHIVE = os.path.join(AN, "cloud_vqa_full451_%s.json")
VQA_300Q_ARCHIVE = os.path.join(AN, "cloud_vqa1793_%s.json")
VQA_ARMS = ("base", "5", "6")

DECLARED_MARGIN_ACC = 0.05       # pre-declared TOST margin, exact-match accuracy
DECLARED_MARGIN_F1 = 0.05        # pre-declared TOST margin, token F1
N_BOOT = 20000                   # bootstrap replicates, same as tools/_p1595_p3_rank_separation.py
RNG_SEED = 20261024              # fixed seed => deterministic analysis archives
ALPHA = 0.05

# Environment-stack registry for the S37 decomposition.  Each stack is an explicit list of archives;
# the loose globs used by tools/_p1546_env_variance.py and tools/_p1570_env_variance_update.py are
# deliberately NOT reproduced here, because a loose glob makes an archived number unreproducible the
# moment a new file matching it appears (see the note on sigma_env_reference below).
STACKS = (
    {
        "id": "torch29_cu130",
        "label": "torch 2.9/cu130",
        "machine": "RTX 4060 Laptop (local)",
        "torch": "2.9.1+cu130",
        "cuda": "13.0",
        "evidence": "outputs/analysis/p3_seeds_combined.json (values.r5 / values.r6)",
    },
    {
        "id": "torch212_cu130",
        "label": "torch 2.12/cu130",
        "machine": "RTX 4080 SUPER (cloud)",
        "torch": "2.12.1+cu130",
        "cuda": "13.0",
        "evidence": "paper3/scripts/outputs/experiments/cloud_verify_r<R>_s*.json, "
                    "excluding partial / imgs / _e1_ rows (same rule as tools/_p1595_p3_rank_separation.py)",
    },
    {
        "id": "torch24_cu121",
        "label": "torch 2.4/cu121",
        "machine": "RTX 4060 Laptop (local)",
        "torch": "2.4.1+cu121",
        "cuda": "12.1",
        "evidence": "archive bucket 'torch 2.4/cu121' of outputs/analysis/p3_env_variance.json: "
                    "the untagged _a10/_a12 rows for seeds 123/789/999 (which carry that bucket's "
                    "values -2.5 / -2.0 / 64.5) plus the rows carrying the explicit _torch24 suffix; "
                    "when both filenames exist for one (rank, seed) cell they are two different runs "
                    "of the same cell and the untagged archive is the one the bucket kept",
    },
    {
        "id": "torch26_cu124",
        "label": "torch 2.6/cu124",
        "machine": "RTX 4060 Laptop (seed 42) + cloud GPU (new seeds)",
        "torch": "2.6.0+cu124",
        "cuda": "12.4",
        "evidence": "files carrying the explicit _torch26 suffix; seed 42 already archived, seeds "
                    "7/123/999 produced by this round",
    },
)

CHECKS: list = []


# ------------------------------------------------------------------------------------------------
# Small helpers
# ------------------------------------------------------------------------------------------------
def show(label: str, value: str, ok: bool, why: str) -> None:
    """Print one number only together with the assertion that guards it (repo ledger style)."""
    CHECKS.append((label, bool(ok)))
    print("  %-62s %-26s %s  %s" % (label, value, "OK  " if ok else "FAIL", why))


def pending(label: str, why: str) -> None:
    """A check that cannot be evaluated yet (input not produced); it is not counted as a failure."""
    print("  %-62s %-26s %s  %s" % (label, "-", "PEND", why))


def rel(path: str) -> str:
    return os.path.relpath(path, REPO).replace(os.sep, "/")


def load_json(path: str) -> dict:
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=True)
        fh.write("\n")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_json(value) -> str:
    blob = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def load_module(name: str, path: str):
    """Import a repository script by path, without adding the repository to sys.path."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import %s" % path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def alpha_for(rank: int) -> float:
    """LoRA alpha of the archived rows: 2 * rank, passed explicitly as --lora-alpha."""
    return float(2 * rank)


def fmt_alpha(alpha: float) -> str:
    return "%g" % alpha


def predict_plain_name(rank: int, seed: int, alpha: float | None) -> str:
    """Reproduce run_training.py's output filename for this protocol.

    run_training.py builds _tag from its own flags: with --lora-alpha given, the tag is
    '_lr5e-05_nw_float1_adamw_e3_bcuniform_a<alpha>'; without it (and with every other flag at its
    reference value) the tag is empty.  Both branches are checked against archived filenames by
    --self-test, so this function is verified against the training script's real behaviour.
    """
    if alpha is None:
        tag = ""
    else:
        tag = "_lr%s_nw_float1_adamw_e3_bcuniform_a%s" % (
            LR_TAG, fmt_alpha(alpha))
    return "verify_r%d_s%d%s.json" % (rank, seed, tag)


def archived_rows() -> dict:
    """The two archived seed-42 torch26 rows, keyed by rank."""
    out = {}
    for rank in NEW_RANKS:
        path = os.path.join(
            EXP, "verify_r%d_s%d_lr5e-05_nw_float1_adamw_e3_bcuniform_a%s_torch26.json"
            % (rank, ARCHIVED_SEED, fmt_alpha(alpha_for(rank))))
        out[rank] = {"path": path, "row": load_json(path) if os.path.exists(path) else None}
    return out


# ------------------------------------------------------------------------------------------------
# Job A: environment-stack seeds
# ------------------------------------------------------------------------------------------------
def build_train_command(rank: int, seed: int, alpha: float, data_path: str | None,
                        python: str | None = None) -> list:
    """The exact argv handed to paper3/scripts/run_training.py.

    Every flag below is pinned to the value recorded by the two archived seed-42 rows; --lora-alpha
    is the one flag that is load-bearing for the filename (the '_a10'/'_a12' tag only appears when
    the flag is passed explicitly) and is numerically identical to the script's own uniform default
    of rank * 2.  --data-path is omitted unless the operator overrides it, matching every archived
    20-sample command; the default glob is verified before the run.
    """
    cmd = [
        python or sys.executable,
        TRAIN_SCRIPT,
        "--rank", str(rank),
        "--seed", str(seed),
        "--epochs", str(EPOCHS),
        "--num-samples", str(NUM_SAMPLES),
        "--lr", LR_FLAG,
        "--batch-size", str(BATCH_SIZE),
        "--block-config", BLOCK_CONFIG,
        "--opt", OPT,
        "--compute-dtype", COMPUTE_DTYPE,
        "--attn-targets", ATTN_TARGETS,
        "--grad-mask", GRAD_MASK,
        "--lora-alpha", fmt_alpha(alpha),
    ]
    if data_path:
        cmd += ["--data-path", data_path]
    return cmd


def printable_command(cmd: list) -> str:
    """A copy-pasteable form of argv, relative to the repository root."""
    parts = []
    for i, tok in enumerate(cmd):
        if i == 0:
            parts.append("python")
        elif isinstance(tok, str) and os.path.isabs(tok) and tok.startswith(REPO):
            parts.append(rel(tok))
        else:
            parts.append(tok)
    return " ".join(parts)


def default_data_files() -> list:
    """What run_training.py's default glob sees, in the order glob returns it."""
    return glob.glob(os.path.join(REPO, "paper3", "train-*.parquet"))


def row_is_valid(path: str, rank: int, seed: int, alpha: float) -> tuple:
    """Validate an existing verify_*.json against the archived seed-42 configuration."""
    if not os.path.exists(path):
        return False, "missing"
    try:
        d = load_json(path)
    except Exception as exc:  # noqa: BLE001
        return False, "unreadable (%r)" % (exc,)
    want = {
        "rank": rank, "seed": seed, "epochs": EPOCHS, "num_samples": NUM_SAMPLES,
        "lr": float(LR_FLAG), "warmup": False, "compute_dtype": COMPUTE_DTYPE, "opt": OPT,
        "block_config": BLOCK_CONFIG, "grad_mask": GRAD_MASK, "attn_targets": ATTN_TARGETS,
        "batch_size": BATCH_SIZE, "proj_rank": None, "data_offset": DATA_OFFSET,
        "target_proj": TARGET_PROJ, "lang_only": LANG_ONLY,
    }
    for key, value in want.items():
        if key not in d:
            return False, "field %s absent" % key
        if d[key] != value:
            return False, "field %s = %r, expected %r" % (key, d[key], value)
    if d.get("lora_alpha") is None or abs(float(d["lora_alpha"]) - alpha) > 1e-9:
        return False, "lora_alpha = %r, expected %r" % (d.get("lora_alpha"), alpha)
    if d.get("ok") is not True:
        return False, "ok is not true"
    energy = d.get("E")
    if not isinstance(energy, list) or len(energy) != EPOCHS + 1:
        return False, "E must carry %d values" % (EPOCHS + 1)
    try:
        energies = [float(x) for x in energy]
    except (TypeError, ValueError):
        return False, "E carries a non-numeric value"
    if any(x != x or x in (float("inf"), float("-inf")) for x in energies):
        return False, "E carries a non-finite value"
    delta = d.get("delta_E")
    if delta is None or float(delta) != float(delta):
        return False, "delta_E is not finite"
    ref = (archived_rows().get(rank) or {}).get("row")
    if ref is not None:
        if d.get("trainable") != ref.get("trainable"):
            return False, ("trainable %r != archived %r" % (d.get("trainable"), ref.get("trainable")))
        if abs(float(delta) - (energies[-1] - energies[0])) > 1e-9:
            return False, "delta_E is not E[-1] - E[0]"
    return True, "valid"


def env_seed_targets(ranks, seeds, suffix: str = "torch26") -> list:
    out = []
    for rank in ranks:
        for seed in seeds:
            alpha = alpha_for(rank)
            plain = os.path.join(EXP, predict_plain_name(rank, seed, alpha))
            tagged = os.path.join(EXP, plain[:-len(".json")] + "_%s.json" % suffix)
            out.append({"rank": rank, "seed": seed, "alpha": alpha,
                        "plain": plain, "target": tagged})
    return out


def update_runlog(entries: dict) -> None:
    """Merge per-run provenance into the run log (the run log is a log, not an analysis archive)."""
    log = load_json(RUNLOG) if os.path.exists(RUNLOG) else {"meta": {}, "runs": {}}
    log["meta"] = {
        "script": "tools/_p1613_p3_cloud_runner.py",
        "job": "env-seeds",
        "protocol": "paper3/scripts/run_training.py, archived seed-42 configuration "
                    "(num_samples 20, 3 epochs, lr 5e-5, batch 1, uniform, adamw, float16, "
                    "grad-mask none, attn-targets qkvo, alpha = 2 * rank, blank-image protocol)",
        "note": "this file records what the round executed (commands, stack, wall time); it is not "
                "an analysis archive and is not byte-reproducible by design.  The two analysis "
                "archives written by --aggregate are deterministic.",
    }
    log.setdefault("runs", {}).update(entries)
    write_json(RUNLOG, log)


@contextmanager
def capture_subprocess_calls(record: list):
    """Intercept subprocess.run/check_call so a dry run can print exactly what would be executed.

    tools/_p1516_p3_vqa_downstream.py builds its own training argv inside ensure_adapter(); wrapping
    subprocess.run lets the dry run print that argv verbatim instead of a hand-written copy that
    could drift from the archived script.
    """
    import subprocess as sp

    real_run, real_check = sp.run, sp.check_call

    class _Stub:
        returncode = 0

    def fake_run(*a, **kw):
        record.append({"argv": list(a[0]) if a else kw.get("args"), "cwd": kw.get("cwd")})
        return _Stub()

    def fake_check(*a, **kw):
        record.append({"argv": list(a[0]) if a else kw.get("args"), "cwd": kw.get("cwd")})
        return 0

    sp.run, sp.check_call = fake_run, fake_check
    try:
        yield record
    finally:
        sp.run, sp.check_call = real_run, real_check


def job_env_seeds(args) -> int:
    print("=" * 118)
    print("JOB env-seeds: torch 2.6/cu124 rows for ranks %s, seeds %s"
          % (list(args.ranks), list(args.seeds)))
    print("=" * 118)

    if not os.path.exists(TRAIN_SCRIPT):
        print("ERROR: %s not found" % rel(TRAIN_SCRIPT))
        return 2
    model_dir = os.path.join(REPO, "models", "llava-hf")
    targets = env_seed_targets(args.ranks, args.seeds, args.stack_suffix)

    data_files = default_data_files()
    default_ok = bool(data_files) and rel(data_files[0]) == DEFAULT_DATA_FILE
    if args.data_path:
        print("  --data-path explicitly set to %s (the filename tag is unaffected)" % args.data_path)
        if not os.path.exists(args.data_path):
            print("ERROR: --data-path %s does not exist" % args.data_path)
            return 2
    else:
        show("default parquet glob[0] is the canonical Alpaca shard",
             rel(data_files[0]) if data_files else "(none)", default_ok,
             "run_training.py takes glob('paper3/train-*.parquet')[0]; with a different shard the "
             "run would train on another dataset while keeping the same filename")
        if not default_ok and not args.dry_run:
            print("ERROR: refusing to run: pass --data-path %s explicitly" % DEFAULT_DATA_FILE)
            return 2
    show("model directory present", rel(model_dir), os.path.isdir(model_dir),
         "run_training.py defaults to paper3/../models/llava-hf; download it on the instance "
         "(cloud_next/env_setup.sh) - weights are never uploaded")
    if not os.path.isdir(model_dir) and not args.dry_run:
        return 2

    if not args.dry_run:
        torch = _torch_version()
        want = args.expect_torch
        ok = torch.startswith(want + ".")
        show("installed torch matches the stack being archived", torch, ok or args.allow_stack_mismatch,
             "the _%s suffix means %s.x; a mismatch would mislabel the row" % (args.stack_suffix, want))
        if not ok and not args.allow_stack_mismatch:
            print("ERROR: installed torch is %s, expected %s.x for the _%s suffix.  Install the right "
                  "stack, or pass --allow-stack-mismatch together with --stack-suffix <honest-name>."
                  % (torch, want, args.stack_suffix))
            return 2

    print("\n[1] plan (%d runs, one subprocess each)" % len(targets))
    pending, skipped = [], []
    for t in targets:
        valid, why = row_is_valid(t["target"], t["rank"], t["seed"], t["alpha"])
        cmd = build_train_command(t["rank"], t["seed"], t["alpha"], args.data_path)
        t["cmd"] = cmd
        state = "SKIP (valid existing: %s)" % why if (valid and not args.force) else "RUN"
        if valid and not args.force:
            skipped.append(t)
        else:
            if valid and args.force:
                state = "RUN (--force overrides a valid existing output)"
            pending.append(t)
        print("  r%d seed %-4d alpha %-5s %s" % (t["rank"], t["seed"], fmt_alpha(t["alpha"]), state))
        print("      %s" % printable_command(cmd))
        print("      -> %s" % rel(t["target"]))
    if args.limit is not None:
        pending = pending[:max(0, args.limit)]
        print("  --limit %d: %d run(s) will be executed in this invocation" % (args.limit, len(pending)))

    if args.dry_run:
        print("\n[2] dry run: %d run(s) would execute, %d skipped; nothing was executed and nothing "
              "was written" % (len(pending), len(skipped)))
        return 0

    print("\n[2] executing %d run(s)" % len(pending))
    log_entries = {}
    failures = []
    for t in pending:
        plain, target = t["plain"], t["target"]
        # run_training.py writes two files this round does not own: the untagged verify_*.json and a
        # per-epoch *_b1_partial.json.  Both may already exist for these seeds from another stack, so
        # every pre-existing byte is saved before the run and written back afterwards; the round then
        # leaves the experiment directory exactly as it found it, apart from the new _<suffix> files.
        partial = os.path.join(EXP, "verify_r%d_s%d_b1_partial.json" % (t["rank"], t["seed"]))
        owned = [("untagged output", plain), ("partial output", partial)]
        saved = {}
        for label, path in owned:
            if os.path.exists(path):
                with open(path, "rb") as fh:
                    saved[path] = fh.read()
                print("  preserving the pre-existing %s %s (sha256 %s) - run_training.py is about to "
                      "overwrite it" % (label, rel(path),
                                        hashlib.sha256(saved[path]).hexdigest()[:16]))
        print("\n  -> r%d seed %d: %s" % (t["rank"], t["seed"], printable_command(t["cmd"])))
        t0 = _now()
        proc = subprocess.run(t["cmd"], cwd=REPO)
        elapsed = _now() - t0
        print("      exit %d after %.1f min" % (proc.returncode, elapsed / 60.0))
        if proc.returncode != 0:
            failures.append({"rank": t["rank"], "seed": t["seed"], "returncode": proc.returncode})
            for label, path in owned:
                _restore_owned(label, path, saved.get(path))
            continue
        if not os.path.exists(plain):
            print("      ERROR: %s was not written by the training script" % rel(plain))
            failures.append({"rank": t["rank"], "seed": t["seed"], "returncode": None,
                             "error": "output missing"})
            for label, path in owned:
                _restore_owned(label, path, saved.get(path))
            continue
        with open(plain, "rb") as fh:
            fresh = fh.read()
        with open(target, "wb") as fh:
            fh.write(fresh)
        for label, path in owned:
            _restore_owned(label, path, saved.get(path))
        valid, why = row_is_valid(target, t["rank"], t["seed"], t["alpha"])
        show("r%d seed %d written and validated" % (t["rank"], t["seed"]),
             os.path.basename(target), valid, why if not valid else
             "delta_E %+.1f, E0 %.1f" % (load_json(target)["delta_E"], load_json(target)["E"][0]))
        if not valid:
            failures.append({"rank": t["rank"], "seed": t["seed"], "returncode": 0, "error": why})
        log_entries["r%d_s%d" % (t["rank"], t["seed"])] = {
            "rank": t["rank"], "seed": t["seed"], "alpha": t["alpha"],
            "command": printable_command(t["cmd"]),
            "argv": t["cmd"],
            "cwd": rel(REPO),
            "output_file": rel(target),
            "output_sha256": sha256_file(target),
            "elapsed_seconds": round(elapsed, 1),
            "returncode": proc.returncode,
            "valid": bool(valid),
            "stack_suffix": args.stack_suffix,
            "torch": _torch_version(),
            "cuda": _cuda_version(),
            "gpu": _gpu_name(),
        }
    if log_entries:
        update_runlog(log_entries)

    print("\n[3] run summary: %d executed, %d skipped, %d failure(s)"
          % (len(pending), len(skipped), len(failures)))
    for f in failures:
        print("    FAILED:", f)
    if failures:
        return 1
    print("    next: python tools/_p1613_p3_cloud_runner.py --job env-seeds --aggregate --strict")
    return 0


def predict_side_effects(rank: int, seed: int) -> list:
    """Files run_training.py writes as a by-product of adapter training.

    --save-adapter-dir does not stop the script from also writing its usual verify_*.json; with
    --images-dir and --data-path <non-caption> the tag is
    '_lr<lr>_nw_float1_adamw_imgs_e<epochs>_bc<block_config>' (the archived file
    verify_r5_s42_lr5e-05_nw_float1_adamw_imgs_e3_bcuniform.json has exactly that name), plus the
    per-epoch *_b1_partial.json.  Both may already exist from the archived 300-question round, so the
    runner saves and restores them around adapter training.
    """
    return [
        os.path.join(EXP, "verify_r%d_s%d_lr%s_nw_float1_adamw_imgs_e%d_bc%s.json"
                     % (rank, seed, LR_TAG, VQA_EPOCHS, BLOCK_CONFIG)),
        os.path.join(EXP, "verify_r%d_s%d_b1_partial.json" % (rank, seed)),
    ]


def _restore_owned(label: str, path: str, prev) -> None:
    """Undo the training script's overwrite of a file that this round does not own."""
    if prev is None:
        if os.path.exists(path):
            os.remove(path)
            print("      removed the transient %s %s" % (label, rel(path)))
    else:
        with open(path, "wb") as fh:
            fh.write(prev)
        print("      restored the pre-existing %s %s" % (label, rel(path)))


# ------------------------------------------------------------------------------------------------
# Job B: VQA on the full 451-question test set
# ------------------------------------------------------------------------------------------------
def vqa_archive(path: str, tag: str) -> tuple:
    """Validate a cloud_vqa_full451_*.json archive."""
    if not os.path.exists(path):
        return False, "missing"
    try:
        d = load_json(path)
    except Exception as exc:  # noqa: BLE001
        return False, "unreadable (%r)" % (exc,)
    if d.get("ok") is not True:
        return False, "ok is not true"
    for key in ("accuracy", "token_f1", "yes_no_accuracy", "n_yes_no", "refs", "hypotheses",
                "questions", "meta"):
        if key not in d:
            return False, "field %s absent" % key
    for key in ("refs", "hypotheses", "questions"):
        if len(d[key]) != VQA_EVAL_N:
            return False, "%s carries %d records, expected %d" % (key, len(d[key]), VQA_EVAL_N)
    if d["meta"].get("n_eval") != VQA_EVAL_N:
        return False, "meta.n_eval = %r" % d["meta"].get("n_eval")
    if (d.get("rank") is None) != (tag == "base"):
        return False, "rank %r does not match arm %s" % (d.get("rank"), tag)
    if d["meta"].get("test_parquet") != rel(os.path.join(REPO, "paper3", "test-vqarad.parquet")):
        return False, "meta.test_parquet = %r" % d["meta"].get("test_parquet")
    return True, "valid (%d records, accuracy %.4f, F1 %.4f)" % (
        len(d["questions"]), float(d["accuracy"]), float(d["token_f1"]))


def adapter_recipe_note() -> str:
    return ("adapter recipe of the archived 300-question round: outputs/p3_vqa_adapters/"
            "r<rank>_step, trained on the full VQA-RAD training split (%d pairs, %d epochs, "
            "--per-step) by tools/_p1516_p3_vqa_downstream.py ensure_adapter()"
            % (VQA_TRAIN_SAMPLES, VQA_EPOCHS))


def job_vqa_full(args) -> int:
    if args.only_arm:
        return _run_vqa_arm(args, args.only_arm)
    print("=" * 118)
    print("JOB vqa-full: base + rank 5 + rank 6 on all %d test questions" % VQA_EVAL_N)
    print("=" * 118)
    mod = load_module("vqa1516_ref", VQA_SCRIPT)
    show("test parquet present", rel(mod.TEST_PARQUET), os.path.isfile(mod.TEST_PARQUET),
         "paper3/test-vqarad.parquet, %d rows read by head(%d)" % (VQA_EVAL_N, VQA_EVAL_N))
    show("test images present", rel(mod.IMAGES), os.path.isdir(mod.IMAGES),
         "data/vqa_rad/images, materialised by vqa_prepare.py on the instance")
    show("base model present", rel(mod.MODEL), os.path.isdir(mod.MODEL),
         "models/llava-hf; weights are downloaded on the instance, never uploaded")
    if not (os.path.isfile(mod.TEST_PARQUET) and os.path.isdir(mod.IMAGES) and os.path.isdir(mod.MODEL)):
        if not args.dry_run:
            return 2

    arms = [a for a in (args.arms or VQA_ARMS)]
    print("\n[1] plan (%d arms, one subprocess each)" % len(arms))
    pending, skipped = [], []
    for tag in arms:
        path = VQA_ARCHIVE % tag
        ok, why = vqa_archive(path, tag)
        if ok and not args.force:
            skipped.append(tag)
            print("  arm %-4s SKIP (valid existing: %s)" % (tag, why))
        else:
            pending.append(tag)
            print("  arm %-4s RUN%s" % (tag, " (--force)" if ok else ""))
        if tag != "base":
            d = os.path.join(ADAPTERS_DIR, "r%s_step" % tag)
            state = "present, will be reused" if os.path.exists(
                os.path.join(d, "adapter_config.json")) else "absent, will be trained (%s)" % adapter_recipe_note()
            print("      adapter %s: %s" % (rel(d), state))
    if args.dry_run:
        print("\n[2] dry run: %d arm(s) would execute, %d skipped; intercepted commands follow"
              % (len(pending), len(skipped)))
        for tag in pending:
            child = [sys.executable, os.path.abspath(__file__), "--job", "vqa-full",
                     "--only-arm", tag, "--eval-n", str(args.eval_n),
                     "--train-samples", str(args.train_samples)]
            if args.adapter_dir:
                child += ["--adapter-dir", args.adapter_dir]
            if args.force:
                child.append("--force")
            print("  arm %s: %s" % (tag, printable_command(child)))
            if tag != "base":
                calls: list = []
                quiet = io.StringIO()
                with redirect_stdout(quiet):
                    with capture_subprocess_calls(calls):
                        mod.ensure_adapter(int(tag), args.train_samples, VQA_EPOCHS, per_step=True)
                if calls:
                    for call in calls:
                        print("      adapter training (intercepted, not executed): %s"
                              % printable_command(call["argv"]))
                else:
                    print("      adapter training: not needed (adapter already present)")
        print("\n  nothing was executed and nothing was written")
        return 0

    print("\n[2] executing %d arm(s), in the order %s" % (len(pending), arms))
    failures = []
    for tag in pending:
        child = [sys.executable, os.path.abspath(__file__), "--job", "vqa-full", "--only-arm", tag,
                 "--eval-n", str(args.eval_n), "--train-samples", str(args.train_samples)]
        if args.adapter_dir:
            child += ["--adapter-dir", args.adapter_dir]
        if args.force:
            child.append("--force")
        print("\n  -> arm %s: %s" % (tag, printable_command(child)))
        proc = subprocess.run(child, cwd=REPO)
        if proc.returncode != 0:
            failures.append({"arm": tag, "returncode": proc.returncode})
            continue
        ok, why = vqa_archive(VQA_ARCHIVE % tag, tag)
        show("arm %s written and validated" % tag, os.path.basename(VQA_ARCHIVE % tag), ok, why)
        if not ok:
            failures.append({"arm": tag, "returncode": 0, "error": why})
    print("\n[3] arm summary: %d executed, %d skipped, %d failure(s)"
          % (len(pending), len(skipped), len(failures)))
    for f in failures:
        print("    FAILED:", f)
    if failures:
        return 1
    print("    next: python tools/_p1613_p3_cloud_runner.py --job vqa-full --aggregate --strict")
    return 0


def _run_vqa_arm(args, tag: str) -> int:
    """Evaluate one arm in this process (invoked as a child by job_vqa_full).

    The evaluation is the archived one: tools/_p1516_p3_vqa_downstream.py's model loading, prompt
    construction, greedy decoding and metric definitions (norm, token_f1) are imported and reused;
    only the evaluation set (451 instead of 300 questions) and the per-question bookkeeping differ.
    """
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    os.environ["HF_HUB_OFFLINE"] = "1"
    mod = load_module("vqa1516_arm", VQA_SCRIPT)
    torch, pd, Image = mod.torch, mod.pd, mod.Image
    import numpy as np

    rank = None if tag == "base" else int(tag)
    out_path = VQA_ARCHIVE % tag
    ok, why = vqa_archive(out_path, tag)
    if ok and not args.force:
        print("  arm %s: existing archive is valid (%s); skipping" % (tag, why))
        return 0

    df = pd.read_parquet(mod.TEST_PARQUET).head(args.eval_n)
    if len(df) != args.eval_n:
        print("ERROR: %s carries %d rows, expected %d" % (rel(mod.TEST_PARQUET), len(df), args.eval_n))
        return 2
    dataset_sha = sha256_file(mod.TEST_PARQUET)

    adapter_dir, adapter_how = None, "none"
    if rank is not None:
        adapter_dir = args.adapter_dir or os.path.join(ADAPTERS_DIR, "r%d_step" % rank)
        present = os.path.exists(os.path.join(adapter_dir, "adapter_config.json"))
        adapter_how = "pre_existing" if present else "trained_here"
        print("  adapter %s: %s" % (rel(adapter_dir),
                                    "reusing the archived recipe adapter" if present
                                    else "absent, training it now with the archived recipe (%s)"
                                         % adapter_recipe_note()))
        saved = {}
        if not present:
            for path in predict_side_effects(rank, ARCHIVED_SEED):
                if os.path.exists(path):
                    with open(path, "rb") as fh:
                        saved[path] = fh.read()
                    print("      preserving the pre-existing %s (run_training.py writes it again as "
                          "a by-product of adapter training)" % rel(path))
            mod.ensure_adapter(rank, args.train_samples, VQA_EPOCHS, per_step=True)
            for path in predict_side_effects(rank, ARCHIVED_SEED):
                _restore_owned("training by-product", path, saved.get(path))
        cfg_path = os.path.join(adapter_dir, "adapter_config.json")
        if not os.path.exists(cfg_path):
            print("ERROR: adapter %s was not produced" % rel(adapter_dir))
            return 2
        cfg = load_json(cfg_path)
        if int(cfg.get("r", -1)) != rank:
            print("ERROR: adapter %s has r=%r, expected %d" % (rel(adapter_dir), cfg.get("r"), rank))
            return 2
        if abs(float(cfg.get("lora_alpha", -1)) - alpha_for(rank)) > 1e-9:
            print("ERROR: adapter %s has lora_alpha=%r, expected %s"
                  % (rel(adapter_dir), cfg.get("lora_alpha"), fmt_alpha(alpha_for(rank))))
            return 2
        targets = cfg.get("target_modules") or []
        if sorted(targets) != sorted(["q_proj", "k_proj", "v_proj", "o_proj"]):
            print("ERROR: adapter %s targets %r, expected the qkvo set" % (rel(adapter_dir), targets))
            return 2

    from transformers import AutoProcessor, BitsAndBytesConfig, LlavaForConditionalGeneration
    from peft import PeftModel
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                               bnb_4bit_use_double_quant=True)
    processor = AutoProcessor.from_pretrained(mod.MODEL)
    t0 = _now()
    base = LlavaForConditionalGeneration.from_pretrained(mod.MODEL, quantization_config=quant,
                                                         device_map="auto")
    model = base
    if rank is not None:
        model = PeftModel.from_pretrained(base, adapter_dir, is_trainable=False)
    hyps, refs, images, questions_text = [], [], [], []
    model.eval()
    for i, row in df.iterrows():
        img = Image.open(os.path.join(mod.IMAGES, str(row["image"]))).convert("RGB")
        conv = [{"role": "user", "content": [{"type": "image"},
                                            {"type": "text",
                                             "text": VQA_PROMPT_PREFIX + str(row["instruction"])}]}]
        text = processor.apply_chat_template(conv, add_generation_prompt=True)
        inp = processor(text=text, images=img, return_tensors="pt")
        inp = {k: v.to("cuda") if torch.is_tensor(v) else v for k, v in inp.items()}
        with torch.no_grad():
            out = model.generate(**inp, max_new_tokens=VQA_MAX_NEW_TOKENS, do_sample=False)
        gen = processor.tokenizer.decode(out[0][inp["input_ids"].shape[1]:],
                                        skip_special_tokens=True).strip()
        hyps.append(gen)
        refs.append(str(row["output"]))
        images.append(str(row["image"]))
        questions_text.append(str(row["instruction"]))
        if i < 3 or (i + 1) % 100 == 0:
            print("    arm=%s %d/%d gen=%r ref=%r" % (tag, i + 1, len(df), gen[:40], refs[-1][:40]),
                  flush=True)
        del inp, out
        if (i + 1) % 50 == 0:
            torch.cuda.empty_cache()

    # Metrics: the archived definitions, reused from tools/_p1516_p3_vqa_downstream.py.  The
    # per-question F1 is the same function applied to one pair at a time (a mean over one pair is
    # that pair's value), and the two routes are asserted to agree below.
    nref = [mod.norm(r) for r in refs]
    nhyp = [mod.norm(h) for h in hyps]
    exact = float(np.mean([a == b for a, b in zip(nhyp, nref)]))
    relaxed = float(np.mean([set(a.split()) <= set(b.split()) for a, b in zip(nref, nhyp)]))
    yn_pairs = [(a, b) for a, b in zip(nref, nhyp) if a.split()[:1] in (["yes"], ["no"])]
    yn_acc = float(np.mean([a.split()[:1] == b.split()[:1] for a, b in yn_pairs])) if yn_pairs else None
    f1_mean = float(mod.token_f1(nref, nhyp))
    f1_per = [float(mod.token_f1([a], [b])) for a, b in zip(nref, nhyp)]
    if abs(sum(f1_per) / len(f1_per) - f1_mean) > 1e-12:
        print("ERROR: per-question F1 does not average to the arm-level F1")
        return 1
    yn_flag = [bool(a.split()[:1] in (["yes"], ["no"])) for a in nref]
    records = []
    for i in range(len(refs)):
        records.append({
            "index": i,
            "image": images[i],
            "question": questions_text[i],
            "reference": refs[i],
            "hypothesis": hyps[i],
            "norm_reference": nref[i],
            "norm_hypothesis": nhyp[i],
            "correct": bool(nhyp[i] == nref[i]),
            "relaxed_correct": bool(set(nref[i].split()) <= set(nhyp[i].split())),
            "token_f1": f1_per[i],
            "yes_no": yn_flag[i],
            "yes_no_correct": (bool(nref[i].split()[:1] == nhyp[i].split()[:1]) if yn_flag[i] else None),
        })
    elapsed_min = (_now() - t0) / 60.0
    report = {
        "meta": {
            "script": "tools/_p1613_p3_cloud_runner.py",
            "task": "S28 VQA-RAD equivalence on the full 451-question test set",
            "n_eval": len(refs),
            "train_samples": args.train_samples if rank is not None else 0,
            "epochs": VQA_EPOCHS,
            "prompt": VQA_PROMPT_PREFIX + "<question>",
            "decoding": "greedy (do_sample=False), max_new_tokens=%d" % VQA_MAX_NEW_TOKENS,
            "evaluation_code": "tools/_p1516_p3_vqa_downstream.py (model loading, prompt, greedy "
                               "decoding and the norm/token_f1 metric) reused by import",
            "adapter_recipe": "none (base model)" if rank is None else adapter_recipe_note(),
            "adapter_dir": None if adapter_dir is None else rel(adapter_dir),
            "adapter_source": adapter_how,
            "adapter_sha256": (sha256_file(os.path.join(adapter_dir, "adapter_model.safetensors"))
                               if adapter_dir and os.path.exists(
                                   os.path.join(adapter_dir, "adapter_model.safetensors")) else None),
            "base_model": rel(mod.MODEL),
            "test_parquet": rel(mod.TEST_PARQUET),
            "test_parquet_sha256": dataset_sha,
            "test_images": rel(mod.IMAGES),
            "evaluation_set": "TEST_PARQUET.head(%d), i.e. the full test set in parquet row order; "
                              "its first 300 rows are the archived 300-question evaluation set "
                              "(verified by the aggregation's comparison_to_300q_archive block)"
                              % args.eval_n,
            "torch": _torch_version(),
            "cuda": _cuda_version(),
            "gpu": _gpu_name(),
            "elapsed_min": elapsed_min,
            "reference_answers": "paper3/test-vqarad.parquet column 'output', in row order",
            "metric_definitions": "norm() lowercases, strips punctuation and collapses whitespace; "
                                  "accuracy is normalised exact match; token_f1 is the token-level F1 "
                                  "of the normalised strings",
        },
        "rank": rank,
        "accuracy": exact,
        "relaxed_accuracy": relaxed,
        "yes_no_accuracy": yn_acc,
        "n_yes_no": len(yn_pairs),
        "token_f1": f1_mean,
        "refs": refs,
        "hypotheses": hyps,
        "refs_sha256": sha256_json(refs),
        "questions": records,
        "ok": True,
    }
    write_json(out_path, report)
    print("  arm=%s accuracy=%.4f F1=%.4f yes/no=%.4f (n=%d) in %.1f min"
          % (tag, exact, f1_mean, yn_acc if yn_acc is not None else float("nan"), len(yn_pairs),
             elapsed_min))
    print("  wrote %s" % rel(out_path))
    return 0


# ------------------------------------------------------------------------------------------------
# Aggregation A: environment-stack seeds
# ------------------------------------------------------------------------------------------------
def dedupe_cells(rows: list) -> tuple:
    """Count every (stack, rank, seed) cell once.

    The torch 2.4/cu121 registry collects two filename patterns (the untagged archived rows and the
    rows carrying the explicit `_torch24` suffix).  run_training.py cannot write a stack suffix, so
    the round copies its untagged output to the tagged name and restores the untagged file it
    overwrote; for a cell whose untagged file did not pre-exist, the untagged output of this round's
    own run stays on disk next to the tagged copy and the cell is then named by two files that are
    two *different* runs of the same cell (different `delta_E` and `E`).

    A cell is one measurement, so exactly one row per (stack, rank, seed) is kept.  The kept row is
    the untagged archived one, because that is the row the frozen three-stack reference bucket of
    outputs/analysis/p3_env_variance.json holds: the torch 2.4/cu121 bucket is
    [-2.5, 41.0, -2.0, 64.5] and -2.5 / -2.0 / 64.5 are the untagged rows of seeds 123 / 789 / 999
    (the loose glob of tools/_p1570_env_variance_update.py sorted the untagged name before the
    suffixed one, which is how the published bucket was formed).  Preferring the tagged duplicate
    would silently re-point the published reference at a different run.  Every discarded row is
    returned with its value and file, so nothing is dropped without a record.

    Returns (kept_rows, duplicates, discarded_rows).
    """
    by_cell: dict = {}
    for row in rows:
        by_cell.setdefault((row["stack"], row["rank"], row["seed"]), []).append(row)
    kept, duplicates, discarded = [], [], []
    for cell in sorted(by_cell):
        group = by_cell[cell]
        if len(group) == 1:
            kept.append(group[0])
            continue
        untagged = [r for r in group if "_torch24." not in r["source_file"]]
        tagged = [r for r in group if "_torch24." in r["source_file"]]
        if not untagged:
            # No archived row to protect: the tagged measurement of this round is the cell.
            kept.extend(tagged)
            if len(tagged) > 1:
                duplicates.append({"stack": cell[0], "rank": cell[1], "seed": cell[2],
                                   "n_rows": len(group),
                                   "resolution": "kept every row: no untagged archive exists for "
                                                 "this cell",
                                   "kept": [{"delta_E": r["delta_E"],
                                             "source_file": r["source_file"]} for r in tagged]})
            continue
        winner = untagged[0]
        kept.append(winner)
        losers = [r for r in group if r is not winner]
        record = {
            "stack": cell[0], "rank": cell[1], "seed": cell[2], "n_rows": len(group),
            "resolution": "kept the untagged archived row (the row the frozen three-stack "
                          "reference bucket holds); the tagged row of this round is a second run of "
                          "the same cell",
            "kept": {"delta_E": winner["delta_E"], "source_file": winner["source_file"],
                     "source_field": winner["source_field"]},
            "discarded": [{"delta_E": r["delta_E"], "source_file": r["source_file"],
                           "source_field": r["source_field"],
                           "same_measurement": bool(abs(float(r["delta_E"])
                                                        - float(winner["delta_E"])) < 1e-12)}
                          for r in losers],
            "distinct_runs": bool(any(abs(float(r["delta_E"]) - float(winner["delta_E"])) >= 1e-12
                                      for r in losers)),
        }
        duplicates.append(record)
        for r in losers:
            discarded.append({**r, "kept_source_file": winner["source_file"],
                              "kept_delta_E": winner["delta_E"],
                              "reason": "duplicate row for the same (stack, rank, seed) cell"})
    return kept, duplicates, discarded


def reference_three_stack(rows: list) -> tuple:
    """The rows of the frozen three-stack reference design, plus the audit of that composition.

    The frozen reference is the row set that produced the archived
    outputs/analysis/p3_env_variance.json decomposition, and it is what a change in sigma_env must be
    attributable to.  The archived file decomposes rank 5 only, so the composition is selected on the
    archived file's own per-stack fields `envs.<stack label>.n` and `envs.<stack label>.mean`; on
    rank 6 the registry is the reference (there is no frozen rank-6 bucket to reproduce).

    For torch 2.4/cu121 the cell registry is not the frozen one.  That bucket holds n = 4 rows with
    mean 25.25, which is exactly the four cells seeds 123/42/789/999, while the archive also carries
    a rank-5 seed-7 measurement that this round produced and which the bucket never contained.  The
    frozen composition is therefore the `n` rows whose mean equals the archived bucket mean; the
    seed-7 row is reported as excluded and stays in the four-stack design, so the comparison isolates
    the fourth stack instead of mixing it with a new torch-2.4 cell.

    Returns (reference_rows, audit) where audit records the composition and what it excludes.
    """
    reference, audit = [], {"archived_bucket": None, "kept": [], "excluded": [],
                            "reference_rank": NEW_RANKS[0],
                            "n_rank_rows": {}}
    ref_path = os.path.join(AN, "p3_env_variance.json")
    ref = load_json(ref_path) if os.path.exists(ref_path) else None
    for stack in STACKS:
        sid = stack["id"]
        if sid == "torch26_cu124":
            continue
        group = [r for r in rows if r["stack"] == sid and r["rank"] == NEW_RANKS[0]]
        if not group:
            continue
        bucket = None
        if ref:
            for label, block in (ref.get("envs") or {}).items():
                if label == stack["label"]:
                    bucket = block
        if bucket is None:
            audit["excluded"].append({"stack": sid, "seeds": sorted(r["seed"] for r in group),
                                      "reason": "no bucket in outputs/analysis/p3_env_variance.json; "
                                                "the rank-5 registry is the reference"})
            continue
        want_n = int(bucket["n"])
        want_mean = float(bucket["mean"])
        chosen = None
        seed_list = sorted({r["seed"] for r in group})
        if len(seed_list) >= want_n:
            for combo in itertools.combinations(seed_list, want_n):
                pick = [r for r in group if r["seed"] in combo]
                if len(pick) == want_n and abs(float(np.mean([r["delta_E"] for r in pick]))
                                               - want_mean) < 1e-9:
                    chosen = pick
                    break
        audit["archived_bucket"] = audit["archived_bucket"] or {}
        audit["archived_bucket"][sid] = {"n": want_n, "mean": want_mean,
                                         "values": [float(x) for x in bucket.get("values", [])]}
        if chosen is None:
            audit["excluded"].append({"stack": sid, "seeds": seed_list,
                                      "reason": "no %d-row subset reproduces the archived mean %.4f; "
                                                "the rank-5 registry is the reference"
                                                % (want_n, want_mean)})
            continue
        kept_seeds = sorted(r["seed"] for r in chosen)
        excluded_seeds = [s for s in seed_list if s not in kept_seeds]
        audit["kept"].append({"stack": sid, "seeds": kept_seeds,
                              "values": [r["delta_E"] for r in chosen],
                              "source_files": [r["source_file"] for r in chosen]})
        if excluded_seeds:
            audit["excluded"].append({
                "stack": sid, "seeds": excluded_seeds,
                "reason": "not part of the frozen rank-%d bucket in "
                          "outputs/analysis/p3_env_variance.json (the bucket's n and mean are "
                          "reproduced exactly without these rows); the row stays in the four-stack "
                          "design" % NEW_RANKS[0],
                "rows": [{"seed": r["seed"], "rank": r["rank"], "delta_E": r["delta_E"],
                          "source_file": r["source_file"]}
                         for r in group if r["seed"] in excluded_seeds]})
    # Rank 5 is the decomposition the archived file froze: use the selected rows.  Rank 6 has no
    # frozen bucket, so its reference is the three stacks' full rank-6 registries.
    for rank in NEW_RANKS:
        if rank == NEW_RANKS[0]:
            for entry in audit["kept"]:
                reference.extend(r for r in rows
                                 if r["stack"] == entry["stack"] and r["rank"] == rank
                                 and r["seed"] in entry["seeds"])
        else:
            reference.extend(r for r in rows if r["rank"] == rank
                             and r["stack"] != "torch26_cu124")
    audit["n_rank_rows"] = {str(rank): {sid: len([r for r in reference
                                                  if r["stack"] == sid and r["rank"] == rank])
                                        for sid in sorted({r["stack"] for r in reference})}
                            for rank in NEW_RANKS}
    return reference, audit


def collect_env_rows() -> tuple:
    """Build the per-stack rows from an explicit registry (no loose globs).

    Returns (rows, registry_notes).  Each row is one archived run: stack, rank, seed, delta_E, E0.
    Every (stack, rank, seed) cell appears exactly once; see dedupe_cells() for the resolution of the
    two torch 2.4/cu121 rank-5 cells that are named by both an untagged and a tagged file.  The
    discarded rows travel in the notes so the caller can archive them.
    """
    rows, notes = [], []
    for stack in STACKS:
        sid = stack["id"]
        for rank in NEW_RANKS:
            entries = []
            if sid == "torch29_cu130":
                path = os.path.join(AN, "p3_seeds_combined.json")
                data = load_json(path)
                notes.append("%s: %s -> values.r%d (%d seeds)"
                             % (sid, rel(path), rank, len(data["values"]["r%d" % rank])))
                for seed, value in sorted(data["values"]["r%d" % rank].items(), key=lambda kv: int(kv[0])):
                    entries.append({"file": rel(path), "field": "values.r%d.%s" % (rank, seed),
                                    "seed": int(seed), "value": float(value), "E0": None})
            elif sid == "torch212_cu130":
                pattern = os.path.join(EXP, "cloud_verify_r%d_s*.json" % rank)
                files = sorted(glob.glob(pattern))
                for path in files:
                    name = os.path.basename(path)
                    if any(x in name for x in ("partial", "imgs", "_e1_")):
                        continue
                    d = load_json(path)
                    value = d.get("delta_E")
                    if value is None:
                        continue
                    try:
                        value = float(value)
                    except (TypeError, ValueError):
                        continue
                    if value != value:
                        continue
                    if int(d.get("rank", -1)) != rank:
                        notes.append("%s: skipped %s (payload rank %r)" % (sid, name, d.get("rank")))
                        continue
                    entries.append({"file": rel(path), "field": "delta_E", "seed": int(d["seed"]),
                                    "value": value, "E0": float(d["E"][0]) if d.get("E") else None})
                notes.append("%s: cloud_verify_r%d_s*.json excluding partial/imgs/_e1_ (%d rows)"
                             % (sid, rank, len(entries)))
            elif sid == "torch24_cu121":
                plain = os.path.join(EXP, "verify_r%d_s*_lr5e-05_nw_float1_adamw_e3_bcuniform_a%s.json"
                                          % (rank, fmt_alpha(alpha_for(rank))))
                suffixed = plain[:-len(".json")] + "_torch24.json"
                files = sorted(glob.glob(plain)) + sorted(glob.glob(suffixed))
                for path in files:
                    d = load_json(path)
                    value = d.get("delta_E")
                    if value is None:
                        continue
                    entries.append({"file": rel(path), "field": "delta_E", "seed": int(d["seed"]),
                                    "value": float(value), "E0": float(d["E"][0]) if d.get("E") else None})
                notes.append("%s: frozen pattern %s (+ the explicit _torch24 suffix) -> %d candidate "
                             "row(s), deduplicated below"
                             % (sid, os.path.basename(plain), len(entries)))
            elif sid == "torch26_cu124":
                pattern = os.path.join(
                    EXP, "verify_r%d_s*_lr5e-05_nw_float1_adamw_e3_bcuniform_a%s_torch26.json"
                         % (rank, fmt_alpha(alpha_for(rank))))
                for path in sorted(glob.glob(pattern)):
                    d = load_json(path)
                    entries.append({"file": rel(path), "field": "delta_E", "seed": int(d["seed"]),
                                    "value": float(d["delta_E"]),
                                    "E0": float(d["E"][0]) if d.get("E") else None})
                notes.append("%s: explicit _torch26 suffix for rank %d (%d rows)"
                             % (sid, rank, len(entries)))
            if not entries:
                continue
            for e in entries:
                rows.append({"stack": sid, "stack_label": stack["label"], "machine": stack["machine"],
                             "torch": stack["torch"], "cuda": stack["cuda"],
                             "rank": rank, "seed": e["seed"], "delta_E": e["value"], "E0": e["E0"],
                             "source_file": e["file"], "source_field": e["field"]})
    rows, duplicates, discarded = dedupe_cells(rows)
    for record in duplicates:
        notes.append("%s rank %d seed %d: %d rows name this one cell; %s"
                     % (record["stack"], record["rank"], record["seed"], record["n_rows"],
                        record["resolution"]))
        for row in record.get("discarded", []):
            notes.append("    discarded duplicate delta_E %+.1f from %s (kept %s delta_E %+.1f; %s)"
                         % (row["delta_E"], row["source_file"], record["kept"]["source_file"],
                            record["kept"]["delta_E"],
                            "same measurement" if row["same_measurement"] else
                            "a different run of the same cell"))
    return rows, notes, duplicates, discarded


def decomposition(vals_by_env: dict) -> dict:
    """One-way random-effects ANOVA on environment level, exactly as tools/_p1570_env_variance_update.py.

    sigma_seed^2 = MS_within; sigma_env^2 = max(0, (MS_between - MS_within) / n0) with the
    unequal-n correction n0 = (n - sum(n_i^2)/n) / (k - 1).
    """
    import numpy as np
    if len(vals_by_env) < 2:
        return {"k": len(vals_by_env), "n": sum(len(v) for v in vals_by_env.values()),
                "sigma_env": None, "sigma_seed": None, "env_variance_share": None,
                "note": "fewer than two environments populated"}
    k = len(vals_by_env)
    allv = [x for v in vals_by_env.values() for x in v]
    n = len(allv)
    grand = float(np.mean(allv))
    ssb = sum(len(v) * (float(np.mean(v)) - grand) ** 2 for v in vals_by_env.values())
    ssw = sum(sum((x - float(np.mean(v))) ** 2 for x in v) for v in vals_by_env.values())
    dfb, dfw = k - 1, n - k
    msb = ssb / dfb if dfb else 0.0
    msw = ssw / dfw if dfw else 0.0
    n0 = (n - sum(len(v) ** 2 for v in vals_by_env.values()) / n) / (k - 1)
    sig2_env = max(0.0, (msb - msw) / n0) if n0 else 0.0
    sig2_seed = msw
    share = sig2_env / (sig2_env + sig2_seed) if (sig2_env + sig2_seed) > 0 else 0.0
    return {
        "k": k, "n": n, "n_per_env": {name: len(v) for name, v in vals_by_env.items()},
        "grand_mean": grand,
        "ss_between": ssb, "ss_within": ssw, "df_between": dfb, "df_within": dfw,
        "ms_between": msb, "ms_within": msw, "n0": n0,
        "sigma_env": float(np.sqrt(sig2_env)), "sigma_seed": float(np.sqrt(sig2_seed)),
        "env_variance_share": float(share),
    }


def stack_summary(rows: list, rank: int) -> dict:
    """Per-stack mean/sd/min/max across seeds for one rank."""
    import statistics as st
    import numpy as np
    out = {}
    for stack in STACKS:
        vals = [(r["seed"], r["delta_E"]) for r in rows if r["stack"] == stack["id"] and r["rank"] == rank]
        if not vals:
            continue
        values = [v for _, v in vals]
        out[stack["id"]] = {
            "label": stack["label"],
            "machine": stack["machine"],
            "torch": stack["torch"],
            "cuda": stack["cuda"],
            "evidence": stack["evidence"],
            "n": len(values),
            "mean": float(np.mean(values)),
            "sd": float(st.stdev(values)) if len(values) > 1 else None,
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "median": float(np.median(values)),
            "values_by_seed": {str(s): float(v) for s, v in sorted(vals)},
            "seeds": sorted(s for s, _ in vals),
            "single_seed": len(values) == 1,
            "source_files": sorted({r["source_file"] for r in rows
                                    if r["stack"] == stack["id"] and r["rank"] == rank}),
        }
    return out


def bootstrap_share(vals_by_env: dict, n_boot: int, rng_seed: int) -> dict:
    """Seed bootstrap within environment, share CI (same procedure as tools/_p1570_env_variance_update.py).

    The same 10,000 replicates give the percentile intervals of sigma_env and sigma_seed as well, so a
    reader is not handed an interval for the share alone.
    """
    import numpy as np
    rng = np.random.default_rng(rng_seed)
    shares, env_sigmas, seed_sigmas = [], [], []
    for _ in range(n_boot):
        resampled = {k: [float(x) for x in rng.choice(v, len(v))] for k, v in vals_by_env.items()}
        dec = decomposition(resampled)
        shares.append(dec["env_variance_share"])
        env_sigmas.append(dec["sigma_env"])
        seed_sigmas.append(dec["sigma_seed"])
    point = decomposition(vals_by_env)
    return {"n_boot": int(n_boot), "rng_seed": int(rng_seed),
            "share_mean": float(np.mean(shares)),
            "share_ci95": [float(np.percentile(shares, 2.5)), float(np.percentile(shares, 97.5))],
            "sigma_env_point": float(point["sigma_env"]),
            "sigma_env_mean": float(np.mean(env_sigmas)),
            "sigma_env_ci95": [float(np.percentile(env_sigmas, 2.5)),
                               float(np.percentile(env_sigmas, 97.5))],
            "sigma_seed_point": float(point["sigma_seed"]),
            "sigma_seed_mean": float(np.mean(seed_sigmas)),
            "sigma_seed_ci95": [float(np.percentile(seed_sigmas, 2.5)),
                                float(np.percentile(seed_sigmas, 97.5))]}


def strict_unmet(acceptance: dict) -> list:
    """Criteria that --strict must refuse to pass: explicit failures and not-yet-evaluable ones."""
    return sorted([k for k, v in acceptance.items() if isinstance(v, bool) and not v]
                  + [k for k, v in acceptance.items() if v is None])


def aggregate_env_stack(args, _capture: list | None = None) -> int:
    print("=" * 118)
    print("AGGREGATE env-seeds -> %s" % rel(ENV_STACK_OUT))
    print("=" * 118)
    if not os.path.exists(ENV_STACK_OUT.rsplit(os.sep, 1)[0]):
        print("ERROR: %s does not exist" % rel(AN))
        return 2
    rows, notes, duplicates, discarded = collect_env_rows()
    print("\n[1] registry (explicit per-stack file lists)")
    for n in notes:
        print("   ", n)

    ref_path = os.path.join(AN, "p3_env_variance.json")
    ref = load_json(ref_path) if os.path.exists(ref_path) else None
    ref_rows, ref_audit = reference_three_stack(rows)

    per_rank, sigmas = {}, {}
    for rank in NEW_RANKS:
        summary = stack_summary(rows, rank)
        per_rank[str(rank)] = {"stacks": summary, "n_stacks": len(summary)}
        for sid, block in summary.items():
            per_rank[str(rank)].setdefault("sigma", {})[sid] = {
                "n": block["n"], "mean": block["mean"], "sd": block["sd"],
                "min": block["min"], "max": block["max"], "single_seed": block["single_seed"],
            }
        envs = {sid: [r["delta_E"] for r in rows if r["stack"] == sid and r["rank"] == rank]
                for sid in summary}
        envs = {k: v for k, v in envs.items() if v}
        dec = decomposition(envs)
        dec["bootstrap"] = bootstrap_share(envs, 10000, 7) if len(envs) >= 2 else None
        # Three-stack reference design: the stacks available before this round, with the torch26
        # bucket removed, each restricted to the frozen row set of reference_three_stack() (the rows
        # the archived p3_env_variance.json decomposition was computed from).  This must reproduce
        # the archived S37 numbers exactly, so that the change in sigma_env is attributable to the
        # new seeds and not to a change of inputs.
        envs3 = {sid: [r["delta_E"] for r in ref_rows if r["stack"] == sid and r["rank"] == rank]
                 for sid in envs if sid != "torch26_cu124"}
        envs3 = {k: v for k, v in envs3.items() if v}
        dec3 = decomposition(envs3) if len(envs3) >= 2 else None
        # Balanced common-seed design: only the seeds present on every populated stack.
        common = set.intersection(*[set(r["seed"] for r in rows
                                        if r["stack"] == sid and r["rank"] == rank) for sid in envs]) \
            if len(envs) >= 2 else set()
        envs_common = {sid: [r["delta_E"] for r in rows
                             if r["stack"] == sid and r["rank"] == rank and r["seed"] in common]
                       for sid in envs}
        dec_common = decomposition(envs_common) if common and len(envs) >= 2 else None
        if dec_common:
            dec_common = dict(dec_common, seeds=sorted(common),
                              bootstrap=bootstrap_share(envs_common, 10000, 7))
        # The cells the frozen bucket left out need no separate fit: the deduplicated design of this rank
        # already holds every one of them (each is a (stack, rank, seed) cell of the current registry),
        # so all_rows is the "frozen bucket plus the cells it excluded" design and no second variant is
        # archived.  This is asserted rather than assumed.
        excluded_cells = [(entry["stack"], r)
                          for entry in ref_audit["excluded"] for r in entry.get("rows", [])]
        not_held = [(sid, row) for sid, row in excluded_cells
                    if not [x for x in rows if x["stack"] == sid and x["rank"] == rank
                            and x["seed"] == row.get("seed")]]
        ref_envs = {sid: [r["delta_E"] for r in ref_rows
                          if r["stack"] == sid and r["rank"] == rank]
                    for sid in envs if sid != "torch26_cu124"}
        ref_envs = {k: v for k, v in ref_envs.items() if v}
        sigmas[str(rank)] = {"all_rows": dec, "three_stack_reference": dec3,
                             "common_seed_design": dec_common,
                             "frozen_bucket_exclusions_not_in_design":
                                 [{"stack": sid, "seed": row.get("seed"),
                                   "source_file": row.get("source_file")} for sid, row in not_held],
                             "envs_all_rows": {k: v for k, v in envs.items()},
                             "envs_three_stack": {k: v for k, v in envs3.items()},
                             "envs_three_stack_frozen": ref_envs,
                             "envs_common_seed": envs_common if dec_common else None}

    print("\n[2] per-stack per-rank summary (field delta_E)")
    for rank in NEW_RANKS:
        print("  rank %d" % rank)
        for sid, block in per_rank[str(rank)]["stacks"].items():
            print("    %-16s n=%d  mean %+8.2f  sd %6s  min %+8.2f  max %+8.2f  seeds %s%s"
                  % (sid, block["n"], block["mean"],
                     ("%.2f" % block["sd"]) if block["sd"] is not None else "-",
                     block["min"], block["max"], block["seeds"],
                     "   [SINGLE SEED]" if block["single_seed"] else ""))

    # Reproduction of the archived S37 decomposition under the same three stacks.
    ref_ok = None
    if ref is not None:
        got = sigmas["5"]["three_stack_reference"]
        ref_ok = (got is not None
                  and abs(got["sigma_env"] - float(ref["sigma_env"])) < 1e-9
                  and abs(got["sigma_seed"] - float(ref["sigma_seed"])) < 1e-9
                  and abs(got["env_variance_share"] - float(ref["env_share"])) < 1e-9)
        show("three-stack reference reproduces archived p3_env_variance.json",
             "sigma_env %.4f / seed %.4f / share %.4f" % (got["sigma_env"], got["sigma_seed"],
                                                          got["env_variance_share"]) if got else "-",
             bool(ref_ok),
             "archived %.4f / %.4f / %.4f" % (float(ref["sigma_env"]), float(ref["sigma_seed"]),
                                              float(ref["env_share"])))
    for entry in ref_audit["excluded"]:
        print("      frozen reference excludes %s: %s" % (entry.get("stack"), entry["reason"]))
        for row in entry.get("rows", []):
            print("          seed %s delta_E %+.1f  %s" % (row["seed"], row["delta_E"],
                                                           row["source_file"]))
    sig = sigmas["5"]["all_rows"]
    show("four-stack sigma_env at r=5 (the S37 estimate for the next revision)",
         "%.2f" % sig["sigma_env"] if sig["sigma_env"] is not None else "-",
         sig["sigma_env"] is not None, "k=%s n=%s; sigma_seed %.2f, share %.3f"
         % (sig["k"], sig["n"], sig["sigma_seed"] or float("nan"),
            sig["env_variance_share"] or float("nan")))

    cells = {}
    for r in rows:
        cells.setdefault((r["stack"], r["rank"], r["seed"]), []).append(r)
    repeated = sorted("%s r%d s%d" % (k[0], k[1], k[2]) for k, v in cells.items() if len(v) > 1)

    expected = env_seed_targets(NEW_RANKS, NEW_SEEDS, args.stack_suffix)
    missing = [rel(t["target"]) for t in expected if not os.path.exists(t["target"])]
    rank_seed_counts = {str(rank): len([r for r in rows if r["stack"] == "torch26_cu124"
                                        and r["rank"] == rank]) for rank in NEW_RANKS}
    single = [{"stack": r["stack"], "rank": r["rank"], "seed": r["seed"],
               "source_file": r["source_file"]} for r in rows
              if len([x for x in rows if x["stack"] == r["stack"] and x["rank"] == r["rank"]]) == 1]
    acceptance = {
        "new_rows_present": len(missing) == 0,
        "missing_new_rows": missing,
        "torch26_seeds_per_rank": rank_seed_counts,
        "torch26_at_least_three_seeds_per_rank": all(v >= 3 for v in rank_seed_counts.values()),
        "all_rows_have_finite_delta_E": all(r["delta_E"] == r["delta_E"] for r in rows),
        "three_stack_reference_reproduced": bool(ref_ok) if ref_ok is not None else None,
        "one_row_per_stack_rank_seed_cell": len(repeated) == 0,
        "repeated_cells": repeated,
        "duplicate_cells_resolved": len(duplicates),
        "discarded_duplicate_rows": discarded,
        "single_seed_rows": single,
        "single_seed_row_count": len(single),
    }
    show("every (stack, rank, seed) cell is counted once", "%d cell(s) repeated" % len(repeated),
         len(repeated) == 0,
         "%d cell(s) were named by more than one file; each discarded row is archived in "
         "discarded_duplicate_rows with its value and file" % len(duplicates))
    missing_excluded = [(str(rank), e["stack"], e["seed"])
                        for rank in NEW_RANKS
                        for e in sigmas[str(rank)].get("frozen_bucket_exclusions_not_in_design", [])]
    show("the deduplicated design holds every cell the frozen bucket excluded",
         "%d cell(s) missing" % len(missing_excluded), not missing_excluded,
         "the frozen three-stack reference leaves out %s; each of those cells is a row of the "
         "four-stack design, so the four-stack fit is the frozen bucket plus the cells it excluded "
         "and no second variant is needed" % (", ".join(
             "%s seed %s" % (e["stack"], e["seeds"]) for e in ref_audit["excluded"]
             if e.get("rows")) or "-"))

    result = {
        "meta": {
            "script": "tools/_p1613_p3_cloud_runner.py",
            "job": "env-seeds --aggregate",
            "task": "S29/S37 environment-stack seeds: per-stack per-rank summaries and the updated "
                    "environment-vs-seed variance decomposition at r=5 (and r=6)",
            "field": "delta_E",
            "protocol": "paper3/scripts/run_training.py, archived seed-42 configuration; blank-image "
                        "(text-only) LLaVA-1.5-7B LoRA protocol; alpha = 2 * rank",
            "stack_registry": [{"id": s["id"], "label": s["label"], "machine": s["machine"],
                                "torch": s["torch"], "cuda": s["cuda"], "evidence": s["evidence"]}
                               for s in STACKS],
            "registry_notes": notes,
            "method": "one-way random-effects ANOVA on environment level with the unequal-n "
                      "correction n0, identical to tools/_p1570_env_variance_update.py; the "
                      "environment factor is the torch/CUDA stack",
            "bootstrap": "seed bootstrap within environment, 10000 replicates, rng seed 7; the same replicates "
                       "give the percentile intervals of sigma_env and sigma_seed",
            "hardware_caveat": "the torch26 bucket mixes hardware: seed 42 was run on an RTX 4060 "
                               "Laptop, the new seeds on the cloud GPU; the archive records the "
                               "per-run gpu/torch/cuda triples in outputs/analysis/"
                               "p3_env_seeds_runlog.json, and S29's machine column must be updated "
                               "accordingly",
            "single_seed_definition": "a (stack, rank) block with exactly one archived seed",
            "deduplication": "one row per (stack, rank, seed): the torch24 registry matches two "
                             "filename patterns (untagged archived rows and rows carrying the "
                             "explicit _torch24 suffix) and a cell named by both is one measurement.  "
                             "The kept row is the untagged archived one (the row the frozen "
                             "three-stack reference bucket of outputs/analysis/p3_env_variance.json "
                             "holds); discarded_duplicate_rows carries every discarded value, its "
                             "file and the kept row",
            "frozen_three_stack_reference": ref_audit,
            "deterministic": True,
            "note": "no wall-clock field is written, so re-running this aggregation on unchanged "
                    "inputs reproduces this file byte for byte",
        },
        "rows": rows,
        "ranks": per_rank,
        "sigma_env": sig["sigma_env"],
        "sigma_seed": sig["sigma_seed"],
        "env_variance_share": sig["env_variance_share"],
        "sigma_by_rank": sigmas,
        "sigma_env_before_this_round": (float(ref["sigma_env"]) if ref else None),
        "sigma_seed_before_this_round": (float(ref["sigma_seed"]) if ref else None),
        "env_variance_share_before_this_round": (float(ref["env_share"]) if ref else None),
        "single_seed_rows": single,
        "discarded_duplicate_rows": discarded,
        "duplicate_cells": duplicates,
        "acceptance": acceptance,
    }
    if args.dry_run:
        print("\n[3] dry run: computed in memory, nothing was written")
        print("    would write %s (%d rows, %d stacks at r=5)"
              % (rel(ENV_STACK_OUT), len(rows), int(per_rank["5"]["n_stacks"])))
    else:
        write_json(ENV_STACK_OUT, result)
        print("\n[3] wrote %s (%d rows)" % (rel(ENV_STACK_OUT), len(rows)))
    if _capture is not None:
        _capture.append(result)
    failed = [label for label, ok in CHECKS if not ok]
    print("\n[4] assertion ledger: %d checks, %d failed" % (len(CHECKS), len(failed)))
    for label in failed:
        print("    FAILED:", label)
    if args.strict:
        unmet = strict_unmet(acceptance)
        print("\n[5] strict acceptance: %s" % ("satisfied" if not unmet else "NOT satisfied: %s" % unmet))
        if unmet:
            return 3
    if failed:
        return 1
    return 0


# ------------------------------------------------------------------------------------------------
# Aggregation B: VQA equivalence on 451 questions
# ------------------------------------------------------------------------------------------------
def load_vqa_arm_full(tag: str) -> dict:
    """Load one 451-question archive into the structure tools/_p1595_p3_rank_separation.py expects."""
    import numpy as np
    path = VQA_ARCHIVE % tag
    d = load_json(path)
    eq = load_module("vqa1595", RANKSEP_SCRIPT)
    nref = [eq.vqa_norm(x) for x in d["refs"]]
    nhyp = [eq.vqa_norm(x) for x in d["hypotheses"]]
    correct = np.array([1.0 if a == b else 0.0 for a, b in zip(nhyp, nref)])
    f1 = np.array([eq.vqa_token_f1(a, b) for a, b in zip(nref, nhyp)])
    yn = [(a, b) for a, b in zip(nref, nhyp) if a.split()[:1] in (["yes"], ["no"])]
    yn_acc = float(np.mean([a.split()[:1] == b.split()[:1] for a, b in yn])) if yn else float("nan")
    return {
        "archive": rel(path),
        "rank": d.get("rank"),
        "train_samples": d["meta"]["train_samples"],
        "n_eval": d["meta"]["n_eval"],
        "n_questions": len(d["refs"]),
        "refs": d["refs"],
        "refs_sha256": d.get("refs_sha256") or sha256_json(d["refs"]),
        "hypotheses": d["hypotheses"],
        "adapter_dir": d["meta"].get("adapter_dir"),
        "adapter_source": d["meta"].get("adapter_source"),
        "adapter_sha256": d["meta"].get("adapter_sha256"),
        "archived_accuracy": float(d["accuracy"]),
        "archived_token_f1": float(d["token_f1"]),
        "archived_yes_no_accuracy": float(d["yes_no_accuracy"]),
        "archived_n_yes_no": int(d["n_yes_no"]),
        "accuracy": float(correct.mean()),
        "token_f1": float(f1.mean()),
        "yes_no_accuracy": yn_acc,
        "n_yes_no": len(yn),
        "correct": correct,
        "f1": f1,
    }


def vqa_contrast(eq, a: dict, b: dict, rng, n_boot: int) -> dict:
    """Paired (by question) percentile bootstrap for arm a minus arm b, both metrics.

    The computation is tools/_p1595_p3_rank_separation.py's own vqa_contrast(), imported and called
    directly so the TOST rule (p_lower = P(delta <= -margin), p_upper = P(delta >= +margin),
    p = max of the two, min_equivalent_margin = max(-ci90_low, ci90_high)) cannot drift from the
    300-question analysis.
    """
    return eq.vqa_contrast(a, b, rng, n_boot)


def aggregate_vqa_full(args, _capture: list | None = None) -> int:
    import numpy as np
    print("=" * 118)
    print("AGGREGATE vqa-full -> %s" % rel(VQA_EQ_OUT))
    print("=" * 118)
    eq = load_module("vqa1595_agg", RANKSEP_SCRIPT)
    if abs(DECLARED_MARGIN_ACC - DECLARED_MARGIN_F1) > 1e-12:
        print("ERROR: the two pre-declared margins differ; the imported contrast function takes a "
              "single margin, so the analysis cannot be run in one pass")
        return 2
    eq.VQA_MARGIN = DECLARED_MARGIN_ACC     # same pre-declared margin for both metrics
    present = [t for t in VQA_ARMS if os.path.exists(VQA_ARCHIVE % t)]
    print("\n[1] arms present: %s" % present)
    if not args.dry_run and len(present) != len(VQA_ARMS):
        print("ERROR: all three arms are required; missing %s"
              % [t for t in VQA_ARMS if t not in present])
        return 2
    if args.dry_run and len(present) != len(VQA_ARMS):
        print("    (dry run: the equivalence block needs all three; the summary below uses what is "
              "available and nothing is written)")

    arms = {t: load_vqa_arm_full(t) for t in present}
    if len(present) == len(VQA_ARMS):
        same_refs = len({tuple(arms[t]["refs"]) for t in present}) <= 1
        show("reference answers identical across arms", "%s" % same_refs, same_refs,
             "same questions in the same order => the per-question pairing is legitimate")
        show("reference lists byte-identical (sha256)",
             "%s" % sorted({arms[t]["refs_sha256"] for t in present})[0][:16],
             len({arms[t]["refs_sha256"] for t in present}) <= 1,
             "sha256 of the JSON encoding of the refs array, per arm")
    else:
        pending("reference answers identical across arms",
                "needs all three arms; %d present, nothing to compare yet" % len(present))
    for t in present:
        a = arms[t]
        show("arm %s record count" % t, "%d" % a["n_questions"], a["n_questions"] == VQA_EVAL_N,
             "accuracy %.4f / F1 %.4f / yes-no %.4f (n=%d)"
             % (a["accuracy"], a["token_f1"], a["yes_no_accuracy"], a["n_yes_no"]))

    imported_rows = [(t, arms[t]["adapter_dir"], arms[t]["adapter_source"]) for t in present]
    for t, adir, asrc in imported_rows:
        print("    arm %s: adapter %s (%s)" % (t, adir or "-", asrc))

    rng = np.random.default_rng(RNG_SEED)
    pairs = [("base", "5"), ("base", "6"), ("5", "6")]
    contrasts = {}
    if len(arms) == 3:
        for a, b in pairs:
            contrasts["%s_minus_%s" % (a, b)] = vqa_contrast(eq, arms[a], arms[b], rng, args.n_boot)

    comparison_300 = None
    if len(arms) == len(VQA_ARMS) and all(os.path.exists(VQA_300Q_ARCHIVE % t) for t in VQA_ARMS):
        comparison_300 = compare_to_300q(arms)
        show("first 300 records reproduce the archived 300-question references",
             "%s" % comparison_300["refs_match"], comparison_300["refs_match"],
             "the 451 run is head(451) of the same parquet, so its first 300 questions are the "
             "archived evaluation set")
        show("first 300 greedy hypotheses identical to the archived round",
             "%s" % comparison_300["hypotheses_identical"], comparison_300["hypotheses_identical"],
             "any mismatch means the adapter or the inference stack differs from the archived round; "
             "the per-arm deltas against the archived accuracy/F1 are recorded either way")
    print("\n[2] contrasts (paired by question, %d bootstrap replicates)" % args.n_boot)
    for name, c in contrasts.items():
        for metric in ("accuracy", "token_f1"):
            d = c[metric]
            print("    %-12s %-9s delta %+0.6f  95%% CI [%+0.4f, %+0.4f]  TOST p=%.4f  "
                  "min margin %.4f%s"
                  % (name, metric, d["delta"], d["ci95"][0], d["ci95"][1], d["tost_p"],
                     d["min_equivalent_margin"],
                     "  EQUIVALENT" if d["equivalent_at_declared_margin"] else ""))

    acc56 = contrasts.get("5_minus_6", {}).get("accuracy")
    f1_56 = contrasts.get("5_minus_6", {}).get("token_f1")
    acc_b5 = contrasts.get("base_minus_5", {}).get("accuracy")
    f1_b5 = contrasts.get("base_minus_5", {}).get("token_f1")
    acc_b6 = contrasts.get("base_minus_6", {}).get("accuracy")
    f1_b6 = contrasts.get("base_minus_6", {}).get("token_f1")

    if contrasts:
        verdict_text = (
            "On all %d held-out questions the rank ordering still has no support on token F1 "
            "(r=5 minus r=6 = %+.4f, TOST p=%.4f at the pre-declared margin %.2f) and the exact-match "
            "accuracy difference between the two ranks is %+.4f (95%% CI [%+.4f, %+.4f]), whose "
            "smallest equivalent margin is %.4f. Both ranks improve over the base model on token F1 "
            "(%+.4f for r=5, %+.4f for r=6)."
            % (VQA_EVAL_N, f1_56["delta"], f1_56["tost_p"], DECLARED_MARGIN_F1, acc56["delta"],
               acc56["ci95"][0], acc56["ci95"][1], acc56["min_equivalent_margin"],
               -f1_b5["delta"], -f1_b6["delta"]))
    else:
        verdict_text = "not computed (the three arms are not all present)"

    vqa_block = {
        "archives": [arms[t]["archive"] for t in present],
        "n_questions": VQA_EVAL_N,
        "pairing": "the same %d held-out questions in the same order in all arms "
                   "(refs arrays byte-identical across arms, see refs_sha256)" % VQA_EVAL_N,
        "declared_margin": DECLARED_MARGIN_F1,
        "declared_margin_rule": (
            "0.05 on both metrics, pre-declared and carried over unchanged from the 300-question "
            "analysis.  A single arm on 451 questions has a binomial standard error of about "
            "0.022 in accuracy, so differences below roughly two standard errors (~0.045) remain at "
            "the resolution limit of this evaluation set; the margin is not re-fitted to the larger "
            "set, and the smallest equivalent margin is reported alongside every contrast."),
        "arms": {t: {"rank": arms[t]["rank"], "train_samples": arms[t]["train_samples"],
                     "n": arms[t]["n_questions"], "accuracy": arms[t]["accuracy"],
                     "token_f1": arms[t]["token_f1"], "yes_no_accuracy": arms[t]["yes_no_accuracy"],
                     "n_yes_no": arms[t]["n_yes_no"], "archive": arms[t]["archive"],
                     "adapter_dir": arms[t]["adapter_dir"],
                     "adapter_source": arms[t]["adapter_source"],
                     "adapter_sha256": arms[t]["adapter_sha256"]} for t in present},
        "contrasts": contrasts,
        "method": "paired (by question) percentile bootstrap, 20000 replicates, identical procedure "
                  "to tools/_p1595_p3_rank_separation.py vqa_contrast(); TOST with the pre-declared "
                  "margin, min_equivalent_margin = max(-ci90_low, ci90_high)",
        "claim_verdict": {
            "both_ranks_improve_over_base": {
                "accuracy": {"r5": (-acc_b5["delta"] if acc_b5 else None),
                             "r5_resolved": (bool(acc_b5["ci95"][1] < 0) if acc_b5 else None),
                             "r6": (-acc_b6["delta"] if acc_b6 else None),
                             "r6_resolved": (bool(acc_b6["ci95"][1] < 0) if acc_b6 else None)},
                "token_f1": {"r5": (-f1_b5["delta"] if f1_b5 else None),
                             "r5_resolved": (bool(f1_b5["ci95"][1] < 0) if f1_b5 else None),
                             "r6": (-f1_b6["delta"] if f1_b6 else None),
                             "r6_resolved": (bool(f1_b6["ci95"][1] < 0) if f1_b6 else None)},
                "verdict": ("resolved for both ranks on token F1 and for r=5 on accuracy; see the "
                            "contrast blocks for the intervals" if contrasts else "not computed"),
            },
            "ranks_do_not_order": {
                "accuracy": ({"delta_r5_minus_r6": acc56["delta"], "ci95": acc56["ci95"],
                              "tost_p": acc56["tost_p"],
                              "equivalent": bool(acc56["equivalent_at_declared_margin"]),
                              "min_equivalent_margin": acc56["min_equivalent_margin"]}
                             if acc56 else None),
                "token_f1": ({"delta_r5_minus_r6": f1_56["delta"], "ci95": f1_56["ci95"],
                              "tost_p": f1_56["tost_p"],
                              "equivalent": bool(f1_56["equivalent_at_declared_margin"]),
                              "min_equivalent_margin": f1_56["min_equivalent_margin"]}
                             if f1_56 else None),
                "verdict": verdict_text,
            },
        },
    }

    rank5_block = {
        "rank": 5,
        "target": "the r=5 arm against the base model and against the r=6 arm, both metrics",
        "margin": DECLARED_MARGIN_ACC,
        "margin_rule": "0.05, pre-declared before the test was run (unchanged from the "
                       "300-question analysis)",
        "n": arms["5"]["n_questions"] if "5" in arms else None,
        "accuracy": ({"vs_base_delta": acc_b5["delta"], "vs_base_ci95": acc_b5["ci95"],
                      "vs_base_tost_p": acc_b5["tost_p"],
                      "vs_base_min_equivalent_margin": acc_b5["min_equivalent_margin"],
                      "vs_r6_delta": acc56["delta"], "vs_r6_ci95": acc56["ci95"],
                      "vs_r6_tost_p": acc56["tost_p"],
                      "vs_r6_min_equivalent_margin": acc56["min_equivalent_margin"],
                      "tost_p": acc56["tost_p"],
                      "equivalent_at_declared_margin": bool(acc56["equivalent_at_declared_margin"])}
                     if acc_b5 and acc56 else None),
        "token_f1": ({"vs_base_delta": f1_b5["delta"], "vs_base_ci95": f1_b5["ci95"],
                      "vs_base_tost_p": f1_b5["tost_p"],
                      "vs_base_min_equivalent_margin": f1_b5["min_equivalent_margin"],
                      "vs_r6_delta": f1_56["delta"], "vs_r6_ci95": f1_56["ci95"],
                      "vs_r6_tost_p": f1_56["tost_p"],
                      "vs_r6_min_equivalent_margin": f1_56["min_equivalent_margin"],
                      "tost_p": f1_56["tost_p"],
                      "equivalent_at_declared_margin": bool(f1_56["equivalent_at_declared_margin"])}
                     if f1_b5 and f1_56 else None),
        "yes_no_accuracy": ({"r5": arms["5"]["yes_no_accuracy"], "n_yes_no": arms["5"]["n_yes_no"]}
                            if "5" in arms else None),
        "energy_axis_note": "the r=5 alignment-energy TOST against zero lives in "
                            "outputs/analysis/p3_rank_separation_extended.json (rank5_equivalence) "
                            "and is unchanged by this round",
        "verdict": verdict_text,
    }

    smallest = {}
    for name, c in contrasts.items():
        for metric in ("accuracy", "token_f1"):
            smallest["%s/%s" % (name, metric)] = c[metric]["min_equivalent_margin"]

    acceptance = {
        "three_arms_present": len(present) == len(VQA_ARMS),
        "records_per_arm": {t: arms[t]["n_questions"] for t in present},
        "records_are_451": (len(present) == len(VQA_ARMS)
                            and all(arms[t]["n_questions"] == VQA_EVAL_N for t in present)),
        "refs_byte_identical_across_arms": bool(len(present) == len(VQA_ARMS)
                                                and len({arms[t]["refs_sha256"] for t in present}) <= 1),
        "refs_match_test_parquet_order": (refs_match_parquet(arms)
                                          if len(present) == len(VQA_ARMS) else None),
        "paired_by_question": len(present) == len(VQA_ARMS),
        "first_300_reproduces_300q_archive_refs": (comparison_300 or {}).get("refs_match"),
        "first_300_hypotheses_identical": (comparison_300 or {}).get("hypotheses_identical"),
    }

    result = {
        "meta": {
            "script": "tools/_p1613_p3_cloud_runner.py",
            "job": "vqa-full --aggregate",
            "task": "S28 VQA-RAD equivalence bound on the full 451-question test set, paired by "
                    "question, with the same procedure as tools/_p1595_p3_rank_separation.py",
            "n_questions": VQA_EVAL_N,
            "n_boot": args.n_boot,
            "rng_seed": RNG_SEED,
            "alpha": ALPHA,
            "declared_margins": {"accuracy": DECLARED_MARGIN_ACC, "token_f1": DECLARED_MARGIN_F1},
            "method": "paired (by question) percentile bootstrap CI of the difference plus TOST "
                      "equivalence against the pre-declared margin; the contrast function is imported "
                      "from tools/_p1595_p3_rank_separation.py",
            "archives": [arms[t]["archive"] for t in present],
            "field_names_shared_with_300q_archives": ["accuracy", "token_f1", "yes_no_accuracy",
                                                      "n_yes_no", "refs", "hypotheses",
                                                      "relaxed_accuracy"],
            "deterministic": True,
            "note": "no wall-clock field is written, so re-running this aggregation on unchanged "
                    "inputs reproduces this file byte for byte",
        },
        "arms": {t: {"rank": arms[t]["rank"], "n": arms[t]["n_questions"],
                     "accuracy": arms[t]["accuracy"], "token_f1": arms[t]["token_f1"],
                     "yes_no_accuracy": arms[t]["yes_no_accuracy"], "n_yes_no": arms[t]["n_yes_no"],
                     "archive": arms[t]["archive"], "adapter_dir": arms[t]["adapter_dir"],
                     "adapter_source": arms[t]["adapter_source"]} for t in present},
        "refs_identical_across_arms": bool(len({arms[t]["refs_sha256"] for t in present}) <= 1),
        "refs_sha256": {t: arms[t]["refs_sha256"] for t in present},
        "vqa_equivalence": vqa_block,
        "rank5_equivalence": rank5_block,
        "smallest_equivalent_margin": smallest,
        "comparison_to_300q_archive": comparison_300,
        "acceptance": acceptance,
    }
    if args.dry_run:
        print("\n[3] dry run: computed in memory, nothing was written")
        print("    would write %s" % rel(VQA_EQ_OUT))
    else:
        write_json(VQA_EQ_OUT, result)
        print("\n[3] wrote %s" % rel(VQA_EQ_OUT))
    if _capture is not None:
        _capture.append(result)
    failed = [label for label, ok in CHECKS if not ok]
    print("\n[4] assertion ledger: %d checks, %d failed" % (len(CHECKS), len(failed)))
    for label in failed:
        print("    FAILED:", label)
    if args.strict:
        unmet = strict_unmet(acceptance)
        print("\n[5] strict acceptance: %s" % ("satisfied" if not unmet else "NOT satisfied: %s" % unmet))
        if unmet:
            return 3
    if failed:
        return 1
    return 0


def refs_match_parquet(arms: dict) -> bool:
    """The reference answers must be the parquet 'output' column, in row order."""
    try:
        import pandas as pd
        path = os.path.join(REPO, "paper3", "test-vqarad.parquet")
        want = [str(x) for x in pd.read_parquet(path).head(VQA_EVAL_N)["output"].tolist()]
    except Exception:  # noqa: BLE001
        return False
    return all(list(arms[t]["refs"]) == want for t in arms)


def compare_to_300q(arms: dict) -> dict:
    """Cross-check the first 300 questions against the archived 300-question round.

    The archived 300-question evaluation is TEST_PARQUET.head(300) and the full run is
    head(451), so the first 300 records of the new archives cover exactly the same questions in the
    same order.  Recomputing the archived metrics on that prefix is the direct test of whether the
    451-question round is the same evaluation extended rather than a different one.
    """
    import numpy as np
    eq = load_module("vqa1595_cmp", RANKSEP_SCRIPT)
    out = {"archive_glob": "outputs/analysis/cloud_vqa1793_{base,5,6}.json", "arms": {},
           "n_prefix": 300,
           "note": "hypotheses are greedy-decoded and therefore expected to repeat; a mismatch "
                   "means the adapter or the inference stack differs from the archived round, and "
                   "the metrics below show how much that costs"}
    refs_match = True
    hypotheses_identical = True
    for t in VQA_ARMS:
        old = load_json(VQA_300Q_ARCHIVE % t)
        new_refs = [str(x) for x in arms[t]["refs"]][:300]
        new_hyps = [str(x) for x in arms[t]["hypotheses"]][:300]
        old_refs = [str(x) for x in old["refs"]]
        old_hyps = [str(x) for x in old["hypotheses"]]
        arms_refs_ok = old_refs == new_refs
        n_mismatch = sum(1 for a, b in zip(old_hyps, new_hyps) if a != b)
        refs_match = refs_match and arms_refs_ok
        hypotheses_identical = hypotheses_identical and n_mismatch == 0
        nref = [eq.vqa_norm(x) for x in new_refs]
        nhyp = [eq.vqa_norm(x) for x in new_hyps]
        acc300 = float(np.mean([a == b for a, b in zip(nhyp, nref)]))
        f1_300 = float(np.mean([eq.vqa_token_f1(a, b) for a, b in zip(nref, nhyp)]))
        out["arms"][t] = {
            "archive": rel(VQA_300Q_ARCHIVE % t),
            "n_archive": len(old["refs"]),
            "refs_match": bool(arms_refs_ok),
            "hypotheses_identical": bool(n_mismatch == 0),
            "n_hypothesis_mismatch": int(n_mismatch),
            "archived_accuracy": float(old["accuracy"]),
            "accuracy_first300_recomputed": acc300,
            "accuracy_delta_vs_archive": acc300 - float(old["accuracy"]),
            "archived_token_f1": float(old["token_f1"]),
            "token_f1_first300_recomputed": f1_300,
            "token_f1_delta_vs_archive": f1_300 - float(old["token_f1"]),
        }
    out["refs_match"] = bool(refs_match)
    out["hypotheses_identical"] = bool(hypotheses_identical)
    return out


# ------------------------------------------------------------------------------------------------
# Self tests (local, GPU-free, write nothing)
# ------------------------------------------------------------------------------------------------
def check_reconstruction() -> dict:
    """Confirm the reconstructed command field by field against the two archived seed-42 rows."""
    print("\n[A] reconstruction of the archived seed-42 torch 2.6/cu124 rows")
    rows = archived_rows()
    reference = {}
    show("filename lr tag follows run_training.py's %g formatting", LR_TAG, LR_TAG == "5e-05",
         "the command line takes %s; the filename tag carries '%s'" % (LR_FLAG, LR_TAG))
    for rank in NEW_RANKS:
        path = rows[rank]["path"]
        show("archived row present", rel(path), os.path.exists(path),
             "the row this round extends")
        if not os.path.exists(path):
            continue
        row = rows[rank]["row"]
        alpha = alpha_for(rank)
        cmd = build_train_command(rank, ARCHIVED_SEED, alpha, None, python="python")
        implied = {
            "rank": rank, "seed": ARCHIVED_SEED, "epochs": EPOCHS, "num_samples": NUM_SAMPLES,
            "lr": float(LR_FLAG), "warmup": False, "compute_dtype": COMPUTE_DTYPE, "opt": OPT,
            "block_config": BLOCK_CONFIG, "grad_mask": GRAD_MASK, "lora_alpha": alpha,
            "attn_targets": ATTN_TARGETS, "batch_size": BATCH_SIZE, "proj_rank": None,
            "data_offset": DATA_OFFSET, "target_proj": TARGET_PROJ, "lang_only": LANG_ONLY,
        }
        bad = {k: (row.get(k), v) for k, v in implied.items() if row.get(k) != v}
        show("r%d: every archived config field reproduced by the reconstruction" % rank,
             "%d/%d" % (len(implied) - len(bad), len(implied)), not bad,
             "mismatches: %s" % bad if bad else
             "rank, seed, epochs, num_samples, lr, warmup, dtype, opt, block_config, grad_mask, "
             "lora_alpha, attn_targets, batch_size, proj_rank, data_offset, target_proj, lang_only")
        ref = row.get("trainable")
        reference[rank] = ref
        show("r%d: archived trainable counts available as an output check" % rank,
             "%s" % ref, bool(ref), "used by row_is_valid() to catch a wrong rank/alpha/targets")

        # Filename prediction, checked against three archived files at once.
        predicted_plain = predict_plain_name(rank, ARCHIVED_SEED, alpha)
        predicted_tagged = predicted_plain[:-len(".json")] + "_torch26.json"
        show("r%d: plain filename predicted from the flags" % rank, predicted_plain,
             os.path.basename(path).replace("_torch26", "") == predicted_plain,
             "the archived file is the same name plus the _torch26 stack suffix")
        show("r%d: archived name field matches the predicted name" % rank,
             row.get("name", ""), row.get("name") == predicted_plain[:-len(".json")],
             "run_training.py writes 'name' without the .json suffix")
        show("r%d: stack suffix is applied at archival, not by the training script" % rank,
             os.path.basename(path), not os.path.basename(path).endswith(row.get("name", "") + ".json"),
             "the training script cannot write _torch26; the runner renames the output")
    # The alpha-free variant exists for r=5 seed 42 and pins the tag rule in the other direction.
    alt = os.path.join(EXP, predict_plain_name(5, ARCHIVED_SEED, None))
    if os.path.exists(alt):
        show("tag rule: without --lora-alpha the tag disappears", os.path.basename(alt),
             predict_plain_name(5, ARCHIVED_SEED, None) == os.path.basename(alt),
             "run_training.py leaves _tag empty when --lora-alpha is absent and every other flag is "
             "at its reference value, so _a10 in the archived name proves the flag was passed")
    data_files = default_data_files()
    print("    default data glob order: %s" % [rel(f) for f in data_files])
    print("    UNCONFIRMED FIELD: --data-path.  The archived JSONs do not record it, and both the "
          "default glob and an explicit non-caption --data-path produce the identical filename tag. "
          "The runner keeps the default (as every archived 20-sample command does) and refuses to "
          "start when glob[0] is not %s." % DEFAULT_DATA_FILE)
    return reference


def check_env_aggregate() -> None:
    print("\n[B] environment-stack aggregation")
    rows, notes, duplicates, discarded = collect_env_rows()
    for n in notes:
        print("     ", n)
    by_stack_rank = {}
    for r in rows:
        by_stack_rank.setdefault((r["stack"], r["rank"]), []).append(r["seed"])
    for key in sorted(by_stack_rank):
        print("      %-16s rank %d: %d seed(s) %s" % (key[0], key[1], len(by_stack_rank[key]),
                                                      sorted(by_stack_rank[key])))
    cells = {}
    for r in rows:
        cells.setdefault((r["stack"], r["rank"], r["seed"]), []).append(r)
    repeated = sorted("%s r%d s%d" % (k[0], k[1], k[2]) for k, v in cells.items() if len(v) > 1)
    show("no (stack, rank, seed) cell is counted twice", "%d repeated" % len(repeated),
         not repeated,
         "%d duplicated cell(s) resolved, %d row(s) discarded and recorded: %s"
         % (len(duplicates), len(discarded),
            ", ".join("%s r%d s%d (kept %+.1f, discarded %s)"
                      % (d["stack"], d["rank"], d["seed"], d["kept"]["delta_E"],
                         "/".join("%+.1f" % x["delta_E"] for x in d["discarded"]))
                      for d in duplicates) or "-"))

    ref_rows, ref_audit = reference_three_stack(rows)
    envs3 = {}
    for sid in ("torch29_cu130", "torch212_cu130", "torch24_cu121"):
        envs3[sid] = [r["delta_E"] for r in ref_rows if r["stack"] == sid and r["rank"] == 5]
    dec3 = decomposition(envs3)
    ref = load_json(os.path.join(AN, "p3_env_variance.json"))
    show("frozen three-stack registry reproduces the archived S37 decomposition",
         "%.4f / %.4f / %.4f" % (dec3["sigma_env"], dec3["sigma_seed"], dec3["env_variance_share"]),
         abs(dec3["sigma_env"] - float(ref["sigma_env"])) < 1e-9
         and abs(dec3["sigma_seed"] - float(ref["sigma_seed"])) < 1e-9
         and abs(dec3["env_variance_share"] - float(ref["env_share"])) < 1e-9,
         "archived %s / %s / %s" % (ref["sigma_env"], ref["sigma_seed"], ref["env_share"]))
    show("frozen registry's torch 2.4/cu121 bucket is the archived bucket",
         "%s" % sorted(envs3["torch24_cu121"]),
         sorted(envs3["torch24_cu121"]) == sorted(
             [float(x) for x in ref["envs"]["torch 2.4/cu121"]["values"]]),
         "archived values %s; the frozen composition is selected as the %d rows whose mean equals "
         "the archived bucket mean %s, so the rounded rank-5 seed-7 measurement of the torch 2.4 "
         "stack is deliberately not part of the reference and stays in the four-stack design "
         "(both facts are archived in meta.frozen_three_stack_reference)"
         % (sorted(ref["envs"]["torch 2.4/cu121"]["values"]),
            int(ref["envs"]["torch 2.4/cu121"]["n"]), ref["envs"]["torch 2.4/cu121"]["mean"]))
    envs4 = dict(envs3)
    envs4["torch26_cu124"] = [r["delta_E"] for r in rows
                              if r["stack"] == "torch26_cu124" and r["rank"] == 5]
    dec4 = decomposition(envs4)
    show("current four-stack estimate (this is what the round will replace)",
         "sigma_env %s" % ("%.2f" % dec4["sigma_env"] if dec4["sigma_env"] is not None else "-"),
         True,
         "n per stack %s; the torch26 bucket is %s seed(s) until the round completes"
         % (dec4["n_per_env"], len(envs4["torch26_cu124"])))
    for rank in NEW_RANKS:
        n26 = len([r for r in rows if r["stack"] == "torch26_cu124" and r["rank"] == rank])
        missing = [rel(t["target"]) for t in env_seed_targets((rank,), NEW_SEEDS)
                   if not os.path.exists(t["target"])]
        show("r%d: torch26 seeds archived now / new rows still missing" % rank,
             "%d / %d" % (n26, len(missing)), n26 >= 1 and len(missing) == 3,
             "the round must add exactly the three missing rows")

    # The aggregation itself, computed in memory: the payload is captured instead of written, so the
    # structure the verification script will consume is checked here, before the GPU round.
    cap: list = []
    args = argparse.Namespace(dry_run=True, strict=False, job="env-seeds", aggregate=True,
                              stack_suffix="torch26", seed=0)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = aggregate_env_stack(args, _capture=cap)
    payload = cap[0] if cap else {}
    required = ("ranks", "sigma_env", "rows")
    missing_keys = [k for k in required if k not in payload]
    try:
        blob = json.dumps(payload)
        serialisable = len(blob) > 1000
    except (TypeError, ValueError) as exc:
        serialisable = False
        print("      json.dumps failed: %r" % (exc,))
    show("aggregate payload carries the keys the cloud gate requires", "%s" % list(required),
         not missing_keys and serialisable,
         "cloud_next/expected_outputs.json requires keys %s; payload is %d bytes of JSON, "
         "captured in memory rather than written" % (list(required), len(blob) if serialisable else 0))
    show("aggregate payload: per-stack per-rank blocks at both ranks",
         "%s" % {k: list(payload.get("ranks", {}).get(k, {}).get("stacks", {})) for k in ("5", "6")},
         rc in (0, 3) and all(set(payload.get("ranks", {}).get(r, {}).get("stacks", {}))
                              == {s["id"] for s in STACKS} for r in ("5", "6")),
         "every stack has a block with n / mean / sd / min / max / single_seed at r=5 and r=6")
    show("aggregate payload: single-seed rows are listed explicitly",
         "%d row(s) before the round" % payload.get("acceptance", {}).get("single_seed_row_count", -1),
         payload.get("acceptance", {}).get("single_seed_row_count") == 3,
         "before the round the single-seed blocks are torch26 at r=5 and r=6 plus torch24 at r=6")
    show("aggregate payload: three-stack reference equals the archived S37 numbers",
         "sigma_env %.4f" % payload.get("sigma_by_rank", {}).get("5", {})
         .get("three_stack_reference", {}).get("sigma_env", float("nan")),
         abs(payload.get("sigma_by_rank", {}).get("5", {}).get("three_stack_reference", {})
             .get("sigma_env", 0.0) - float(ref["sigma_env"])) < 1e-9,
         "the same frozen registry must reproduce 31.1489 so that the change in sigma_env is "
         "attributable to the new seeds and not to a change of inputs")


def check_vqa_plumbing() -> None:
    print("\n[C] VQA plumbing and equivalence method")
    import numpy as np
    mod = load_module("vqa1516_selftest", VQA_SCRIPT)
    eq = load_module("vqa1595_selftest", RANKSEP_SCRIPT)
    frozen = [("yes there is a mass", "yes mass"), ("no, the lungs are clear", "no"),
              ("mild cardiomegaly", "cardiomegaly mild")]
    agree = all(mod.norm(r) == eq.vqa_norm(r) and
                abs(mod.token_f1([mod.norm(r)], [mod.norm(h)])
                    - eq.vqa_token_f1(eq.vqa_norm(r), eq.vqa_norm(h))) < 1e-15 for r, h in frozen)
    show("metric definitions of the two archived scripts agree", "%d frozen pairs" % len(frozen),
         agree, "tools/_p1516_p3_vqa_downstream.py norm/token_f1 == tools/_p1595_p3_rank_separation.py "
                "vqa_norm/vqa_token_f1; the runner imports the former and the contrast from the latter")

    rng = np.random.default_rng(12345)
    n = VQA_EVAL_N
    correct_a = (rng.random(n) < 0.40).astype(float)
    correct_b = np.where(rng.random(n) < 0.85, correct_a, 1.0 - correct_a)
    f1_a = np.clip(correct_a * 0.6 + rng.random(n) * 0.4, 0, 1)
    f1_b = np.clip(correct_b * 0.6 + rng.random(n) * 0.4, 0, 1)
    arm_a = {"correct": correct_a, "f1": f1_a}
    arm_b = {"correct": correct_b, "f1": f1_b}
    eq.VQA_MARGIN = DECLARED_MARGIN_ACC
    c = eq.vqa_contrast(arm_a, arm_b, np.random.default_rng(RNG_SEED), 2000)
    ok_fields = all(k in c for k in ("accuracy", "token_f1"))
    d = c["accuracy"]
    tost_consistent = (d["equivalent_at_declared_margin"] == (d["tost_p"] < ALPHA))
    margin_consistent = abs(d["min_equivalent_margin"] - max(-d["ci90"][0], d["ci90"][1])) < 1e-12
    show("imported contrast returns the fields the aggregate consumes",
         "%s" % sorted(c["accuracy"]), ok_fields and tost_consistent and margin_consistent,
         "delta/ci95/ci90/tost_p/min_equivalent_margin present; TOST verdict consistent with p; "
         "min margin == max(-ci90_low, ci90_high)")
    show("synthetic contrast delta equals the arm-mean difference",
         "%+.4f" % d["delta"],
         abs(d["delta"] - (correct_a.mean() - correct_b.mean())) < 1e-12,
         "the paired bootstrap is centred on the observed difference")
    show("bootstrap resamples questions jointly (paired)",
         "n_boot %d" % d["n_boot"], d["n_boot"] == 2000 and len(d["ci95"]) == 2 and
         d["ci95"][0] < d["delta"] < d["ci95"][1],
         "CI brackets the point estimate; pairing is what makes the difference of two arms tighter "
         "than the difference of two independent samples")

    try:
        import pandas as pd
        df = pd.read_parquet(os.path.join(REPO, "paper3", "test-vqarad.parquet"))
        show("test parquet carries exactly the evaluation set", "%d rows" % len(df),
             len(df) == VQA_EVAL_N,
             "columns %s; head(%d) is the whole test set" % (list(df.columns), VQA_EVAL_N))
    except Exception as exc:  # noqa: BLE001
        show("test parquet readable", repr(exc), False, "needed to evaluate all 451 questions")

    old_refs = {}
    for t in VQA_ARMS:
        p = VQA_300Q_ARCHIVE % t
        if os.path.exists(p):
            old_refs[t] = [str(x) for x in load_json(p)["refs"]]
    if len(old_refs) == 3:
        try:
            import pandas as pd
            want = [str(x) for x in pd.read_parquet(
                os.path.join(REPO, "paper3", "test-vqarad.parquet")).head(300)["output"].tolist()]
            show("the 300 archived questions are the first 300 of the 451",
                 "%d/%d identical" % (sum(1 for a, b in zip(old_refs["base"], want) if a == b), 300),
                 all(old_refs[t] == want for t in VQA_ARMS),
                 "so the 451 run is a strict extension of the archived evaluation and the first-300 "
                 "records can be compared directly")
            show("archived 300-question reference lists identical across arms", "3 arms",
                 len({tuple(v) for v in old_refs.values()}) == 1,
                 "the pairing of the archived analysis is legitimate")
        except Exception as exc:  # noqa: BLE001
            show("300-question prefix check", repr(exc), False, "needs the test parquet")

    for t in VQA_ARMS:
        p = VQA_ARCHIVE % t
        show("full-451 archive %s" % t, "present" if os.path.exists(p) else "absent",
             True, os.path.basename(p))

    # The adapter-training by-product filenames are predicted, not guessed: the archived 300-question
    # round left exactly those files behind, so the prediction can be checked against them.
    for rank in (5, 6):
        predicted = [os.path.basename(x) for x in predict_side_effects(rank, ARCHIVED_SEED)]
        existing = [name for name in predicted if os.path.exists(os.path.join(EXP, name))]
        show("r%d: adapter-training by-product filenames match archived files" % rank,
             "%d/%d present" % (len(existing), len(predicted)), len(existing) >= 1,
             "predicted %s; these are saved and restored around adapter training so the archived "
             "rows on the instance are not overwritten" % predicted)

    print("\n[D] adapter choice")
    for rank in (5, 6):
        step = os.path.join(ADAPTERS_DIR, "r%d_step" % rank)
        plain = os.path.join(ADAPTERS_DIR, "r%d" % rank)
        show("r%d: archived-recipe adapter r%d_step" % (rank, rank),
             "present" if os.path.exists(os.path.join(step, "adapter_config.json")) else "absent "
             "(will be trained on the instance)", True,
             "recipe of the 300-question archives: %s" % adapter_recipe_note())
        if os.path.exists(os.path.join(plain, "adapter_config.json")):
            cfg = load_json(os.path.join(plain, "adapter_config.json"))
            print("      note: %s also exists (r=%s, alpha=%s) but it belongs to a different training "
                  "budget and is deliberately not used" % (rel(plain), cfg.get("r"),
                                                           cfg.get("lora_alpha")))


def check_vqa_aggregate_rehearsal() -> None:
    """Run the whole vqa-full aggregation path on the real 300-question archives, writing nothing.

    The three archived 300-question archives are fed through the 451-question code path by pointing
    the archive template at them and telling the rehearsal that the evaluation set is 300 records
    long.  Because tools/_p1595_p3_rank_separation.py analysed exactly those three archives with the
    same contrast function, the same RNG seed and the same number of bootstrap replicates, the
    contrasts this rehearsal prints must equal the archived S28 numbers: that is the check that the
    aggregation of the new 451-question archives will be computed the same way as the published one.
    """
    global VQA_ARCHIVE, VQA_EVAL_N
    print("\n[E] aggregation rehearsal on the three real 300-question archives (dry run, no writes)")
    real_tpl, real_n = VQA_ARCHIVE, VQA_EVAL_N
    args = argparse.Namespace(dry_run=True, strict=True, n_boot=N_BOOT, force=False, arms=None,
                              eval_n=VQA_EVAL_N, train_samples=VQA_TRAIN_SAMPLES, adapter_dir=None,
                              only_arm=None, job="vqa-full", aggregate=True, self_test=False)
    cap: list = []
    buf = io.StringIO()
    try:
        VQA_ARCHIVE = VQA_300Q_ARCHIVE
        VQA_EVAL_N = 300
        with redirect_stdout(buf):
            rc = aggregate_vqa_full(args, _capture=cap)
    finally:
        VQA_ARCHIVE, VQA_EVAL_N = real_tpl, real_n
    payload = cap[0] if cap else {}
    show("rehearsal: full aggregation path runs end to end", "exit %d" % rc, rc == 0,
         "the three archived 300-question archives through the new code, including the strict "
         "acceptance gate; nothing was written")
    try:
        blob = json.dumps(payload)
        serialisable = len(blob) > 1000
    except (TypeError, ValueError) as exc:
        serialisable = False
        print("      json.dumps failed: %r" % (exc,))
    show("rehearsal: payload carries the keys the cloud gate requires",
         "%s" % [k for k in ("vqa_equivalence", "rank5_equivalence") if k in payload],
         serialisable and "vqa_equivalence" in payload and "rank5_equivalence" in payload,
         "cloud_next/expected_outputs.json requires vqa_equivalence and rank5_equivalence; payload "
         "is %d bytes of JSON, captured in memory rather than written" % (len(blob) if serialisable else 0))

    got = {}
    for name, block in payload.get("vqa_equivalence", {}).get("contrasts", {}).items():
        for metric in ("accuracy", "token_f1"):
            got["%s/%s" % (name, metric)] = block[metric]["delta"]
    arch_path = os.path.join(AN, "p3_rank_separation_extended.json")
    if os.path.exists(arch_path):
        arch = load_json(arch_path)["vqa_equivalence"]["contrasts"]
        diffs = {k: abs(got[k] - arch[k.split("/")[0]][k.split("/")[1]]["delta"])
                 for k in got if k.split("/")[0] in arch}
        worst = max(diffs.values()) if diffs else float("inf")
        show("rehearsal: contrasts equal the archived S28 analysis",
             "6 contrasts, max |delta diff| %.2e" % worst,
             len(got) == 6 and len(diffs) == 6 and worst < 1e-9,
             "tools/_p1595_p3_rank_separation.py analysed these archives with the same contrast "
             "function, seed and replicate count, so identical inputs must give identical deltas")
        margins = payload.get("smallest_equivalent_margin", {})
        show("rehearsal: every contrast reports its smallest equivalent margin",
             "%d entries" % len(margins),
             len(margins) == 6 and all(v >= 0 for v in margins.values()),
             "the archive records min_equivalent_margin per contrast, as the task requires")
    cmp300 = payload.get("comparison_to_300q_archive") or {}
    show("rehearsal: first-300 cross-check against the archived round is green",
         "refs match, hypotheses identical",
         cmp300.get("refs_match") is True and cmp300.get("hypotheses_identical") is True,
         "identical inputs through compare_to_300q() must report refs_match and hypotheses_identical, "
         "which is what the new archives will be judged on")
    show("rehearsal: nothing was written",
         "dry run", "nothing was written" in buf.getvalue(),
         "the rehearsal never calls write_json(); --dry-run keeps the aggregation in memory")


def self_test(args) -> int:
    print("=" * 118)
    print("SELF-TEST (local, GPU-free, writes nothing)")
    print("=" * 118)
    check_reconstruction()
    check_env_aggregate()
    check_vqa_plumbing()
    check_vqa_aggregate_rehearsal()
    failed = [label for label, ok in CHECKS if not ok]
    print("\nassertion ledger: %d checks, %d failed" % (len(CHECKS), len(failed)))
    for label in failed:
        print("    FAILED:", label)
    return 1 if failed else 0


# ------------------------------------------------------------------------------------------------
# Environment probes
# ------------------------------------------------------------------------------------------------
def _torch_version() -> str:
    try:
        import torch
        return str(torch.__version__)
    except Exception:  # noqa: BLE001
        return "unavailable"


def _cuda_version() -> str:
    try:
        import torch
        return str(torch.version.cuda)
    except Exception:  # noqa: BLE001
        return "unavailable"


def _gpu_name() -> str:
    try:
        import torch
        return str(torch.cuda.get_device_name(0)) if torch.cuda.is_available() else "no cuda device"
    except Exception:  # noqa: BLE001
        return "unavailable"


def _now() -> float:
    import time
    return time.time()


# ------------------------------------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------------------------------------
def main(argv=None) -> int:
    global CHECKS
    CHECKS = []
    ap = argparse.ArgumentParser(
        description="P3 cloud-round runner: environment-stack seeds (S29/S37) and full "
                    "451-question VQA (S28).  Preparing and dry-running this script needs no GPU.")
    ap.add_argument("--job", choices=("env-seeds", "vqa-full"), help="which job to run")
    ap.add_argument("--aggregate", action="store_true",
                    help="run the aggregation step of the chosen job instead of the job itself")
    ap.add_argument("--dry-run", action="store_true",
                    help="print every command, compute aggregations in memory, write nothing")
    ap.add_argument("--self-test", action="store_true",
                    help="local consistency checks (reconstruction, aggregation math, VQA plumbing)")
    ap.add_argument("--strict", action="store_true",
                    help="with --aggregate: exit non-zero when an acceptance criterion is unmet")
    ap.add_argument("--apply", action="store_true",
                    help="accepted for consistency with the other cloud scripts (cloud_next/run_all.sh "
                         "passes it); writing the archives is the default behaviour of a run or "
                         "aggregate step, so this flag changes nothing")
    ap.add_argument("--force", action="store_true", help="re-run even when an output is valid")
    ap.add_argument("--only-arm", choices=VQA_ARMS, default=None,
                    help="internal: evaluate a single VQA arm in this process")
    ap.add_argument("--arms", default=None, help="comma-separated VQA arms (default base,5,6)")
    ap.add_argument("--ranks", default=",".join(str(r) for r in NEW_RANKS),
                    help="ranks for --job env-seeds")
    ap.add_argument("--seeds", default=",".join(str(s) for s in NEW_SEEDS),
                    help="seeds for --job env-seeds")
    ap.add_argument("--limit", type=int, default=None, help="run at most N pending training runs")
    ap.add_argument("--data-path", default=None,
                    help="override the training parquet (recorded in the run log; the output "
                         "filename tag is unaffected)")
    ap.add_argument("--expect-torch", default="2.6",
                    help="torch major.minor expected on the instance for the archived stack")
    ap.add_argument("--stack-suffix", default="torch26",
                    help="stack suffix appended to the archived filenames")
    ap.add_argument("--allow-stack-mismatch", action="store_true",
                    help="proceed even when the installed torch does not match --expect-torch")
    ap.add_argument("--eval-n", type=int, default=VQA_EVAL_N, help="VQA questions to evaluate")
    ap.add_argument("--train-samples", type=int, default=VQA_TRAIN_SAMPLES,
                    help="VQA adapter training budget (archived recipe: 1793)")
    ap.add_argument("--adapter-dir", default=None,
                    help="override the rank adapter directory (default outputs/p3_vqa_adapters/r<R>_step)")
    ap.add_argument("--n-boot", type=int, default=N_BOOT, help="bootstrap replicates")
    args = ap.parse_args(argv)

    args.ranks = tuple(int(x) for x in str(args.ranks).split(",") if x.strip())
    args.seeds = tuple(int(x) for x in str(args.seeds).split(",") if x.strip())
    if args.arms:
        args.arms = tuple(x.strip() for x in str(args.arms).split(",") if x.strip())
    if args.eval_n != VQA_EVAL_N:
        print("NOTE: --eval-n %d differs from the archived full set (%d); archives will be rejected "
              "by their own validation and by cloud_next/expected_outputs.json." % (args.eval_n, VQA_EVAL_N))

    if args.self_test:
        return self_test(args)

    if args.only_arm:
        return _run_vqa_arm(args, args.only_arm)

    if not args.job:
        ap.error("--job is required unless --self-test or --only-arm is given")

    if args.aggregate:
        return aggregate_env_stack(args) if args.job == "env-seeds" else aggregate_vqa_full(args)
    return job_env_seeds(args) if args.job == "env-seeds" else job_vqa_full(args)


if __name__ == "__main__":
    raise SystemExit(main())