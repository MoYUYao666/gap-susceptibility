#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""P3 task A: run the OFFICIAL IGU-LoRA allocator under the block-level comparison protocol and
quantify the gap between the official code and our block-level reimplementation.

WHY THIS FILE EXISTS
--------------------
Supplementary Section "Allocation-rule baselines" (paper3/paper_ieee/supplementary/supplementary.tex)
states, verbatim:

    "Several limitations ... These are our block-level reimplementations, not the official
     implementations."

That sentence is the caveat this round closes.  The IGU-LoRA case is the one where the official code
IS obtainable (github.com/withyou12/igulora, vendored at external/igulora), so the caveat can be
retired for it by running the official allocator under exactly the protocol our block-level arm used
and reporting the measured gap -- including the case where the gap is large.

WHAT IS OFFICIAL AND WHAT IS ADAPTED
------------------------------------
Official, unmodified (pinned by sha256 below):
  * external/igulora/iglora/rank_allocator.py  -- RankAllocator: EMA/SNR scoring, AdaLoRA budget
    schedule, mask-to-target-rank ("the algorithm").
  * external/igulora/iglora/lora_module.py     -- SVDLoRAModule: the module the allocator scores.
Adapted glue (this repository's code, NOT the official repo):
  * the name proxy that presents CLIP attention projections to RankAllocator under LLM-style
    parameter names (RankAllocator hard-codes "model.layers.<n>.self_attn.<proj>.lora_*");
  * the aggregation of surviving per-module ranks into the four blocks of the comparison.

The released pipeline itself (iglora/run_pruning_sft.py + script/benchmark/sst2/*.sh) is a text-LLM
SVD-LoRA pipeline (Llama2-7B / SST2) and cannot be dropped into 4-bit LLaVA; the plan therefore
runs the official *allocation algorithm* on CLIP and trains the resulting LLaVA arm with
paper3/scripts/run_training.py, which is the same training path the block-level arm used.

TWO BLOCK MAPPINGS (read this before quoting a number)
------------------------------------------------------
The published official arm (Supplementary Section S39 / Table tab:iguofficial) aggregated the
surviving ranks with a glue whose test ``prefix.startswith("model.layers.1")`` also captures the
CLIP *text* layers 1, 10 and 11 (they share the "1" prefix with the vision-tower proxy indices
100-111).  Recomputing the archived per-module ranks with the corrected mapping gives a different
allocation:

    mapping      vision  shallow  mid  deep   shares (v/s/m/d)              allocation (budget 16)
    archived     309     23       45   7      0.8047/0.0599/0.1172/0.0182   12/1/2/1  (published)
    corrected    270     30       45   39     0.7031/0.0781/0.1172/0.1016   11/1/2/2

Both are computable from the same official run, so --stage allocate records both and asserts each
against the value above.  --compare takes --official-config, and 'auto' prefers the corrected one.

MODES
-----
Local, no GPU, no network, writes nothing:
    python tools/_p1639_p3_official_igu.py --plan
    python tools/_p1639_p3_official_igu.py --self-test
    python tools/_p1639_p3_official_igu.py --compare --dry-run     # computes in memory only

Instance only (GPU).  Never downloads anything: every asset is a local path, and every run mode
sets HF_HUB_OFFLINE / TRANSFORMERS_OFFLINE before importing transformers.
    python tools/_p1639_p3_official_igu.py --run-official --stage all --dry-run   # prints commands
    python tools/_p1639_p3_official_igu.py --run-official --stage allocate
    python tools/_p1639_p3_official_igu.py --run-official --stage train \
        --config official_corrected_map,reimpl_igu_style --seeds 42,123,789
    python tools/_p1639_p3_official_igu.py --compare

WRITE POLICY
------------
* --plan / --self-test write nothing;
* --run-official writes outputs/analysis/p3_official_igu_run.json and lets run_training.py write its
  own verify_*.json; any pre-existing archive that the training script would overwrite is saved and
  restored, and its sha256 is recorded (see _restore_owned);
* --compare writes outputs/analysis/p3_official_vs_reimpl.json and is deterministic: no wall-clock
  field is written, all randomness is seeded, so re-running it on unchanged inputs reproduces the
  file byte for byte;
* no mode ever modifies a pre-existing archive owned by another round.
"""
from __future__ import annotations

import argparse
import hashlib
import glob
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

# ------------------------------------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------------------------------------
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(REPO, "outputs", "analysis")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")
TRAIN_SCRIPT = os.path.join(REPO, "paper3", "scripts", "run_training.py")
OFFICIAL_DIR = os.path.join(REPO, "external", "igulora")
CLIP_MODEL = os.path.join(REPO, "models", "clip-vit-base-patch32")
CAPTIONS_DIR = os.path.join(REPO, "data", "marine_captions")
CAPTIONS_JSON = os.path.join(CAPTIONS_DIR, "captions.json")
DATA_FILE = os.path.join(REPO, "paper3", "train-00000-of-00001-a09b74b3ef9c3b56.parquet")

ARCHIVE_ALLOC_OFFICIAL = os.path.join(AN, "p3_official_igu_clip.json")
ARCHIVE_RULES_REIMPL = os.path.join(AN, "p3_baseline_rules.json")
ARCHIVE_ARM_OFFICIAL = os.path.join(EXP, "verify_r1_s42_bcexplicit_v12_s1_m2_d1.json")
ARCHIVE_ARM_REIMPL = os.path.join(EXP, "verify_r1_s42_bcexplicit_v11_s1_m3_d1.json")
RUN_ARCHIVE = os.path.join(AN, "p3_official_igu_run.json")
COMPARE_OUT = os.path.join(AN, "p3_official_vs_reimpl.json")

# ------------------------------------------------------------------------------------------------
# Official implementation identity (pinned; --plan fails loudly on any drift)
# ------------------------------------------------------------------------------------------------
OFFICIAL_URL = "https://github.com/withyou12/igulora.git"
OFFICIAL_COMMIT = "3f5ba10a6646c81c557e4669b14b072f76822085"
OFFICIAL_COMMIT_DATE = "2026-02-26 07:45:36 +0000"
OFFICIAL_PAPER = ("IGU-LoRA: Adaptive Rank Allocation via Integrated Gradients and Uncertainty-Aware "
                  "Scoring; ICLR 2026 (Fourteenth International Conference on Learning "
                  "Representations); OpenReview MnToYQx9My; repo README bib key Cui2026igulora")
OFFICIAL_FILES = {
    "iglora/rank_allocator.py": "6ba699ebecd6bf2ee6e699a2bd0647dc5af0e401c8e66dc7e7cea0dd57573424",
    "iglora/lora_module.py": "63ff9a981d9a7af169c83ff7c7c1979f91c7c9c3f5c336dc5b9bb164bc7ccc5c",
    "iglora/calc_gen_scores.py": "228f8d2c2b8231803d1d065b220ef8df1ffa5bee793a395e4f77003918519094",
    "iglora/io_utils.py": "6a7c69fa42001f57ef9b4499cd98fbf8bb277f47b3a822447472a64cad0477a0",
    "iglora/run_pruning_sft.py": "4d5c9539552b9e9e9f87c47474f6ef305b991767be5423a18f67382576cba2c9",
    "iglora/run_final_sft.py": "cd29128eecb3b0d994ed229fe8e8ef3cedd60b7b85b94d0851afeab9fb98d492",
    "script/benchmark/sst2/llama2_7b_sst2_prune.sh":
        "260fed057f8c62a82d8db1b4b2809fdc3bb1d5623e7d7bf0ed27c0b35e3873a6",
    "script/benchmark/sst2/llama2_7b_sst2_final.sh":
        "ff2af0df0aa97270b2420c594891df7b80cbd50535a347257bd07bd4c1e71f5d",
    "README.md": "7e9fe11920b0a9abac05801af456db6d5911b5bc7bd282e261d463d3f4f48a21",
}
CLONE_COMMAND = ("git clone %s external/igulora && git -C external/igulora checkout %s"
                 % (OFFICIAL_URL, OFFICIAL_COMMIT))

# ------------------------------------------------------------------------------------------------
# Frozen protocol of the comparison (every value is read back from the archives by --plan)
# ------------------------------------------------------------------------------------------------
BLOCKS = ("vision", "text_shallow", "text_mid", "text_deep")
BUDGET = 16                 # rank-layers of the comparison budget
NUM_SAMPLES = 20            # archived "num_samples": 20 (16 train / 4 eval, blank-image protocol)
EPOCHS = 3                  # archived "epochs": 3
LR = 5e-5                   # archived "lr": 5e-05
BASE_RANK = 1               # archived "rank": 1
LORA_ALPHA = 16.0           # archived "lora_alpha": 16
SEEDS_DEFAULT = (42, 123, 789)
E0_ARCHIVED = 3921.0        # archived E(0) of every bcexplicit arm (asserted, not assumed)
ARCHIVED_DELTA_OFFICIAL = 240.5     # verify_r1_s42_bcexplicit_v12_s1_m2_d1.json
ARCHIVED_DELTA_REIMPL = 333.0       # verify_r1_s42_bcexplicit_v11_s1_m3_d1.json
DATA_SHA256 = "06391b656a06fd3fb9d213160ef2398796c3b7f3dc75ef1e3ced30d461517073"

# The official allocation stage (identical knobs to tools/_p1557_official_igu_clip.py, which
# produced the archived p3_official_igu_clip.json: 30 contrastive steps on 4 marine captions/step).
ALLOC_MODULE_RANK = 16
ALLOC_MODULE_ALPHA = 32
ALLOC_TARGET_RANK = 4
ALLOC_INIT_WARMUP = 5
ALLOC_FINAL_WARMUP = 5
ALLOC_MASK_INTERVAL = 10
ALLOC_BETA1 = 0.85
ALLOC_BETA2 = 0.99
ALLOC_STEPS = 30
ALLOC_BATCH = 4
ALLOC_LR = 1e-3
ALLOC_SEED = 42
ARCHIVED_MODULE_SUMS = {"archived": {"vision": 309.0, "text_shallow": 23.0, "text_mid": 45.0,
                                     "text_deep": 7.0},
                        "corrected": {"vision": 270.0, "text_shallow": 30.0, "text_mid": 45.0,
                                      "text_deep": 39.0}}
ARCHIVED_ALLOCATIONS = {"archived": {"vision": 12, "text_shallow": 1, "text_mid": 2, "text_deep": 1},
                        "corrected": {"vision": 11, "text_shallow": 1, "text_mid": 2, "text_deep": 2}}
REIMPL_ALLOCATION = {"vision": 11, "text_shallow": 1, "text_mid": 3, "text_deep": 1}

CONFIGS = {
    "official_archived_map": {"side": "official", "block_map": "archived",
                              "allocation": ARCHIVED_ALLOCATIONS["archived"]},
    "official_corrected_map": {"side": "official", "block_map": "corrected",
                               "allocation": ARCHIVED_ALLOCATIONS["corrected"]},
    "reimpl_igu_style": {"side": "reimpl", "block_map": None, "allocation": REIMPL_ALLOCATION},
}
DEFAULT_CONFIGS = ("official_corrected_map", "reimpl_igu_style")

# Pre-declared decision rule (declared BEFORE the run; see docs/P3_OFFICIAL_IGU_PLAN.md)
MARGIN_FRACTION = 0.05      # equivalence margin on delta_E, as a fraction of the archived E(0)
MARGIN_ABS = MARGIN_FRACTION * E0_ARCHIVED      # = 196.05
ALLOC_L1_TOLERANCE = 2      # rank-layers of 16 (12.5% of the budget)
N_BOOT = 20000              # bootstrap replicates, same count as tools/_p1595_p3_rank_separation.py
RNG_SEED = 20261024         # fixed seed => deterministic analysis archive
ALPHA = 0.05

ENV_KEYS = ("python", "torch", "cuda", "gpu", "transformers", "peft", "numpy")

CHECKS: list = []


# ------------------------------------------------------------------------------------------------
# Small helpers
# ------------------------------------------------------------------------------------------------
def rel(path: str) -> str:
    """Repo-relative POSIX path for display.

    2026-10-25 portability defect: os.path.relpath raises
    `ValueError: path is on mount 'C:', start on mount 'D:'` when the two locations are on different
    Windows drives (e.g. a tempfile.mkdtemp() that lands on C: while the repo is on D:). Display must
    never crash a run, so fall back to the absolute path.
    """
    try:
        return os.path.relpath(path, REPO).replace(os.sep, "/")
    except ValueError:
        return os.path.abspath(path).replace(os.sep, "/")


def load_json(path: str) -> dict:
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: str, payload: dict) -> None:
    """Deterministic writer: fixed indent, ASCII, LF, trailing newline."""
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


def show(label: str, value: str, ok: bool, why: str) -> None:
    """Print one number only together with the assertion that guards it."""
    CHECKS.append((label, bool(ok)))
    print("  %-60s %-24s %s  %s" % (label, value, "OK  " if ok else "FAIL", why))


def pending(label: str, why: str) -> None:
    print("  %-60s %-24s %s  %s" % (label, "-", "PEND", why))


def printable_command(cmd) -> str:
    parts = []
    for i, tok in enumerate(cmd):
        if i == 0:
            parts.append("python")
        elif isinstance(tok, str) and os.path.isabs(tok) and tok.startswith(REPO):
            parts.append(rel(tok))
        else:
            parts.append(str(tok))
    return " ".join(parts)


def fmt_alpha(value: float) -> str:
    return "%g" % value


def load_module(name: str, path: str):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import %s" % path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def env_fingerprint() -> dict:
    """Environment of the machine that produced a run (called only inside run modes)."""
    import platform
    out = {"python": platform.python_version(), "numpy": np.__version__}
    try:
        import torch
        out["torch"] = torch.__version__
        out["cuda"] = getattr(torch.version, "cuda", None)
        out["gpu"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    except Exception as exc:  # noqa: BLE001
        out["torch"] = "unavailable (%s)" % type(exc).__name__
    try:
        import transformers
        out["transformers"] = transformers.__version__
    except Exception:  # noqa: BLE001
        out["transformers"] = None
    try:
        import peft
        out["peft"] = peft.__version__
    except Exception:  # noqa: BLE001
        out["peft"] = None
    return out


# ------------------------------------------------------------------------------------------------
# Archive readers (all read-only)
# ------------------------------------------------------------------------------------------------
def read_archived_official() -> dict:
    """The archived official allocation stage: p3_official_igu_clip.json."""
    if not os.path.exists(ARCHIVE_ALLOC_OFFICIAL):
        return {}
    d = load_json(ARCHIVE_ALLOC_OFFICIAL)
    return {
        "path": rel(ARCHIVE_ALLOC_OFFICIAL),
        "sha256": sha256_file(ARCHIVE_ALLOC_OFFICIAL),
        "module_ranks": d.get("module_ranks") or {},
        "block_rank_sum": d.get("block_rank_sum") or {},
        "share": d.get("share") or {},
        "allocation": d.get("allocation") or {},
        "meta": d.get("meta") or {},
    }


def read_archived_rules() -> dict:
    """The archived block-level reimplementation: p3_baseline_rules.json."""
    if not os.path.exists(ARCHIVE_RULES_REIMPL):
        return {}
    d = load_json(ARCHIVE_RULES_REIMPL)
    return {
        "path": rel(ARCHIVE_RULES_REIMPL),
        "sha256": sha256_file(ARCHIVE_RULES_REIMPL),
        "allocation": (d.get("allocation") or {}).get("igu") or {},
        "igu_raw": d.get("igu_raw") or {},
        "meta": d.get("meta") or {},
    }


def read_arm(path: str) -> dict:
    """One archived trained arm (paper3/scripts/outputs/experiments/verify_*.json)."""
    if not os.path.exists(path):
        return {}
    d = load_json(path)
    energy = d.get("E") or []
    return {
        "path": rel(path),
        "sha256": sha256_file(path),
        "rank": d.get("rank"),
        "seed": d.get("seed"),
        "lora_alpha": d.get("lora_alpha"),
        "epochs": d.get("epochs"),
        "num_samples": d.get("num_samples"),
        "E": energy,
        "E0": float(energy[0]) if energy else None,
        "delta_E": d.get("delta_E"),
        "trainable": d.get("trainable"),
        "ok": d.get("ok"),
    }


def read_run_archive() -> dict:
    if not os.path.exists(RUN_ARCHIVE):
        return {}
    d = load_json(RUN_ARCHIVE)
    d["path"] = rel(RUN_ARCHIVE)
    d["sha256"] = sha256_file(RUN_ARCHIVE)
    return d


# ------------------------------------------------------------------------------------------------
# Allocation arithmetic
# ------------------------------------------------------------------------------------------------
def allocate_from_sums(sums: dict, budget: int = BUDGET) -> dict:
    """Share-proportional integer allocation with the repo's rounding rule (see _p1557/_p1514)."""
    w = np.array([float(sums[b]) for b in BLOCKS], dtype=float)
    share = w / w.sum() if w.sum() > 0 else np.ones_like(w) / len(w)
    ranks = np.maximum(1, np.round(share * budget)).astype(int)
    guard = 0
    while ranks.sum() > budget and guard < 1000:
        i = int(np.argmax(ranks))
        if ranks[i] > 1:
            ranks[i] -= 1
        else:
            break
        guard += 1
    guard = 0
    while ranks.sum() < budget and guard < 1000:
        i = int(np.argmin(share * budget - ranks))
        ranks[i] += 1
        guard += 1
    return {b: int(r) for b, r in zip(BLOCKS, ranks)}


def block_map_of(prefix: str, mapping: str) -> str:
    """The two block mappings of the raw name proxy (see the module docstring).

    'archived' reproduces the published glue: the prefix test also captures text layers 1/10/11.
    'corrected' assigns by the real layer index: >=100 is the vision tower, 0-2/3-8/9-11 are the
    text shallow/mid/deep blocks (the 3/6/3 analogue of LLaVA's 8/16/8).
    """
    if mapping == "archived" and prefix.startswith("model.layers.1"):
        return "vision"
    idx = int(prefix.split(".")[2])
    if idx >= 100:
        return "vision"
    return "text_shallow" if idx <= 2 else ("text_mid" if idx <= 8 else "text_deep")


def block_sums(module_ranks: dict, mapping: str) -> dict:
    out = {b: 0.0 for b in BLOCKS}
    for prefix, rank in module_ranks.items():
        out[block_map_of(prefix, mapping)] += float(rank)
    return out


def l1_gap(a: dict, b: dict) -> int:
    return int(sum(abs(int(a.get(k, 0)) - int(b.get(k, 0))) for k in BLOCKS))


def share_l1(a: dict, b: dict, budget: int = BUDGET) -> float:
    return float(sum(abs((int(a.get(k, 0)) - int(b.get(k, 0))) / float(budget)) for k in BLOCKS))


# ------------------------------------------------------------------------------------------------
# Statistics: paired percentile bootstrap + TOST (same rule as tools/_p1595_p3_rank_separation.py)
# ------------------------------------------------------------------------------------------------
def paired_bootstrap(diffs, margin: float, rng, n_boot: int) -> dict:
    """Percentile bootstrap of the mean paired difference, plus a two-sided TOST against +/-margin.

    The RNG is consumed exactly as tools/_p1595_p3_rank_separation.py vqa_contrast() does
    (rng.integers(0, n, size=(n_boot, n)) and percentile 2.5/5/95/97.5), which --self-test asserts
    by calling that function on the same numbers.
    """
    vals = np.asarray([float(v) for v in diffs], dtype=float)
    n = int(vals.size)
    out = {"n_pairs": n, "mean_gap": float(vals.mean()) if n else None, "n_boot": int(n_boot),
           "margin": float(margin),
           "method": "paired (by seed) percentile bootstrap of the mean difference + TOST; the "
                     "resampling rule is tools/_p1595_p3_rank_separation.py vqa_contrast()"}
    if n == 0:
        out.update({"boot_mean": None, "boot_se": None, "ci95": None, "ci90": None, "tost_p": None,
                    "tost_p_lower": None, "tost_p_upper": None,
                    "equivalent_at_declared_margin": None, "min_equivalent_margin": None,
                    "unavailable_reason": "no paired seed"})
        return out
    if n == 1:
        # One pair carries no interval.  A number is NOT reported in place of the interval.
        out.update({"boot_mean": None, "boot_se": None, "ci95": None, "ci90": None, "tost_p": None,
                    "tost_p_lower": None, "tost_p_upper": None,
                    "equivalent_at_declared_margin": None, "min_equivalent_margin": None,
                    "unavailable_reason": "a single paired seed carries no bootstrap interval or "
                                          "TOST p-value; run more seeds (--seeds) to obtain one"})
        return out
    idx = rng.integers(0, n, size=(int(n_boot), n))
    d = vals[idx].mean(axis=1)
    lo90, hi90 = float(np.percentile(d, 5.0)), float(np.percentile(d, 95.0))
    p_lower = float(np.mean(d <= -margin))
    p_upper = float(np.mean(d >= +margin))
    out.update({
        "boot_mean": float(d.mean()),
        "boot_se": float(d.std(ddof=1)),
        "ci95": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))],
        "ci90": [lo90, hi90],
        "excludes_zero_95": bool(np.percentile(d, 2.5) > 0 or np.percentile(d, 97.5) < 0),
        "tost_p_lower": p_lower,
        "tost_p_upper": p_upper,
        "tost_p": max(p_lower, p_upper),
        "equivalent_at_declared_margin": bool(max(p_lower, p_upper) < ALPHA),
        "min_equivalent_margin": max(-lo90, hi90),
        "unavailable_reason": None,
    })
    return out


def arm_equivalence_verdict(stat: dict) -> str:
    """'equivalent' | 'within_margin_unconfirmed' | 'different' (rule declared in the plan doc)."""
    mean = stat.get("mean_gap")
    if mean is None:
        return "no_data"
    margin = float(stat.get("margin") or MARGIN_ABS)
    if abs(mean) > margin:
        return "different"
    if stat.get("ci95") is None:
        return "within_margin_unconfirmed"
    return "equivalent" if stat.get("equivalent_at_declared_margin") else "different"


# ------------------------------------------------------------------------------------------------
# --plan
# ------------------------------------------------------------------------------------------------
def plan() -> int:
    print("=" * 118)
    print("P3 TASK A -- official IGU-LoRA allocation under the block-level comparison protocol")
    print("=" * 118)

    print("\n[1] what the caveat says today")
    print("  paper3/paper_ieee/supplementary/supplementary.tex, Section 'Allocation-rule baselines'")
    print("  (label app:rules, Table tab:rules / tab:rulearms):")
    print("    \"Block-level reimplementations in the spirit of three published allocation rules ...\"")
    print("    \"These are our block-level reimplementations, not the official implementations.\"")
    print("  Supplementary Section 'Official IGU allocation stage' (label app:iguofficial, Table")
    print("  tab:iguofficial) already reports the official allocator through a name-only adapter, so")
    print("  the remaining gap is not 'no official code' but 'no like-for-like comparison': the")
    print("  official stage and the block-level stage were run under different allocation protocols.")

    print("\n[2] official implementation")
    print("  origin      : %s" % OFFICIAL_URL)
    print("  commit      : %s (%s)" % (OFFICIAL_COMMIT, OFFICIAL_COMMIT_DATE))
    print("  vendored at : %s" % rel(OFFICIAL_DIR))
    print("  paper       : %s" % OFFICIAL_PAPER)
    print("  official files used (rank_allocator, lora_module) and the released text-LLM pipeline:")
    for name in sorted(OFFICIAL_FILES):
        print("      %-52s %s" % (name, OFFICIAL_FILES[name][:16]))
    print("  NOT official, provided by this repository: the name proxy and the block aggregation.")
    print("  NOTE: external/ is gitignored (.gitignore), so the clone is NOT in the repository; the")
    print("  instance must fetch it.  --plan verifies the local clone and --run-official verifies it")
    print("  again on the instance before importing anything from it.")

    print("\n[3] environment the official run needs")
    print("  runtime      : the instance python that already runs paper3/scripts/run_training.py")
    print("                 (torch + transformers + peft + bitsandbytes + numpy + pandas + pillow).")
    print("  extra pip    : none.  The allocation stage imports only external/igulora's")
    print("                 iglora.rank_allocator and iglora.lora_module, which need torch only.")
    print("                 The released text-LLM pipeline would additionally need accelerate,")
    print("                 datasets, tensorboardX and tqdm; it is NOT part of this comparison and is")
    print("                 not needed to close the caveat.")
    print("  assets       : %s (CLIP backbone of the allocation stage)" % rel(CLIP_MODEL))
    print("                 %s (marine captions, %d contrastive steps)"
          % (rel(CAPTIONS_DIR), ALLOC_STEPS))
    print("                 %s (blank-image training shard)" % rel(DATA_FILE))
    print("                 models/llava-hf (4-bit base model of the trained arms)")
    print("  no downloads : if an asset is missing, fetch it with the mirror-first rule and rerun;")
    print("                 this script never downloads anything (HF_HUB_OFFLINE=1 is set by every")
    print("                 run mode).")
    print("  clone        : %s" % CLONE_COMMAND)
    print("  pip (only if the instance python lacks a package):")
    print("                 pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <package>")
    print("                 export HF_ENDPOINT=https://hf-mirror.com; export HF_HOME=/root/autodl-tmp/hf")

    print("\n[4] commands that would run it (instance only, GPU)")
    print("  %s --run-official --stage all --dry-run" % rel(os.path.abspath(__file__)))
    print("  %s --run-official --stage allocate" % rel(os.path.abspath(__file__)))
    print("  %s --run-official --stage train --config %s --seeds 42,123,789"
          % (rel(os.path.abspath(__file__)), ",".join(DEFAULT_CONFIGS)))
    print("  %s --compare" % rel(os.path.abspath(__file__)))
    print("  [allocate] official RankAllocator + SVDLoRAModule on CLIP, %d steps x %d captions, seed %d"
          % (ALLOC_STEPS, ALLOC_BATCH, ALLOC_SEED))
    print("  [train]    paper3/scripts/run_training.py per (config, seed): --rank 1 --rank-vision V")
    print("             --rank-shallow S --rank-mid M --rank-deep D --seed <s> --epochs 3")
    print("             --num-samples 20 --lora-alpha 16 --data-path <%s>" % rel(DATA_FILE))

    print("\n[5] fair-comparison checklist (only the allocation rule may differ)")
    rows = [
        ("data", "20 samples of %s (16 train / 4 eval, blank-image protocol)"
                 % os.path.basename(DATA_FILE), "identical"),
        ("epochs", "%d" % EPOCHS, "identical"),
        ("optimiser / lr / batch", "AdamW, lr %g, batch 1" % LR, "identical"),
        ("rank budget", "%d rank-layers, base rank %d, alpha %g, targets qkvo"
                        % (BUDGET, BASE_RANK, LORA_ALPHA), "identical"),
        ("seeds", "%s" % ",".join(str(s) for s in SEEDS_DEFAULT), "identical"),
        ("base model", "models/llava-hf, 4-bit nf4 double quant, float16 compute", "identical"),
        ("evaluation", "run_training.py compute_E on the same 4 held-out samples, dE = E(3) - E(0)",
         "identical"),
        ("allocation", "official RankAllocator+name proxy vs block-level integrated gradients",
         "STUDY VARIABLE"),
        ("input of the allocation stage",
         "CLIP contrastive batches (official, online pruning schedule) vs a probe LLaVA adapter "
         "(block-level, post-hoc IG)", "DECLARED, not removable"),
    ]
    for name, value, status in rows:
        print("  %-30s %-72s %s" % (name, value, status))

    print("\n[6] expected cost (measured evidence, not an estimate)")
    print("  * trained arm 20 samples / 3 epochs / batch 1: outputs/run_*.log report "
          "'Training time: 1253-1968 s'")
    print("    (21-33 min) on the RTX 4060 Laptop; docs/p3_cloud_round_notes.md budgets ~25 min per")
    print("    run on a laptop-class GPU, faster on a datacenter card.")
    print("  * allocation stage: %d CLIP-base steps (~2-5 min on a GPU)." % ALLOC_STEPS)
    print("  * budget for 3 official + 3 reimplementation arms: ~2.5-3.5 h GPU on a laptop-class")
    print("    card, less on a datacenter card; disk: no new download (all assets are in the repo),")
    print("    ~30 MB per arm archive.")
    print("  * shutdown after retrieval: sync && (shutdown -h now || poweroff), then verify the")
    print("    port is unreachable and record the time.")

    print("\n[7] pre-declared decision rule (declared before the run; %s)" % rel(COMPARE_OUT))
    print("  margin       : %g x E(0) = %.2f on delta_E (the paper's own 5%% equivalence margin)"
          % (MARGIN_FRACTION, MARGIN_ABS))
    print("  allocation   : L1 distance of the block ranks <= %d of %d" % (ALLOC_L1_TOLERANCE, BUDGET))
    print("  verdicts     : small  = arm equivalent AND allocation within L1 tolerance")
    print("                 mixed  = one of the two holds")
    print("                 large  = the arm gap exceeds the margin (or its CI excludes equivalence)")

    print("\n[8] local verification of the inputs")
    rc = verify_inputs()
    print("\n  assertion ledger: %d checks, %d failed" % (len(CHECKS), sum(1 for _, ok in CHECKS if not ok)))
    for label, ok in CHECKS:
        if not ok:
            print("    FAILED:", label)
    print("\n  nothing was executed and nothing was written")
    return rc


def verify_inputs(require_gpu_assets: bool = False) -> int:
    """Every input --plan depends on, asserted (read-only)."""
    ok_official = os.path.isdir(os.path.join(OFFICIAL_DIR, ".git"))
    show("official clone present", rel(OFFICIAL_DIR), ok_official,
         "clone with: %s" % CLONE_COMMAND)
    if ok_official:
        head = subprocess.run(["git", "-C", OFFICIAL_DIR, "rev-parse", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
        show("official clone at the pinned commit", head[:16], head == OFFICIAL_COMMIT,
             "expected %s" % OFFICIAL_COMMIT[:16])
        drift = []
        for name, want in sorted(OFFICIAL_FILES.items()):
            path = os.path.join(OFFICIAL_DIR, name)
            if not os.path.exists(path):
                drift.append("%s missing" % name)
            elif sha256_file(path) != want:
                drift.append("%s sha256" % name)
        show("official files match the pinned sha256", "%d files" % len(OFFICIAL_FILES),
             not drift, "; ".join(drift) if drift else "rank_allocator + lora_module + pipeline")

    arch_off = read_archived_official()
    show("archived official allocation archive", rel(ARCHIVE_ALLOC_OFFICIAL), bool(arch_off),
         "%s" % (arch_off.get("meta", {}).get("script") if arch_off else
                 "missing; produced by tools/_p1557_official_igu_clip.py"))
    if arch_off:
        mr = arch_off.get("module_ranks") or {}
        show("archived per-module ranks non-empty", "%d modules" % len(mr), len(mr) >= 96,
             "12 text + 12 vision CLIP layers x 4 projections")
        for mapping in ("archived", "corrected"):
            sums = block_sums(mr, mapping)
            want_sums = ARCHIVED_MODULE_SUMS[mapping]
            alloc = allocate_from_sums(sums)
            same_sums = all(abs(sums[b] - want_sums[b]) < 1e-9 for b in BLOCKS)
            same_alloc = alloc == ARCHIVED_ALLOCATIONS[mapping]
            show("%s block mapping reproduces the recorded sums" % mapping,
                 "%s" % [int(sums[b]) for b in BLOCKS], same_sums,
                 "expected %s" % [int(want_sums[b]) for b in BLOCKS])
            show("%s block mapping reproduces the allocation" % mapping,
                 "%s" % [alloc[b] for b in BLOCKS], same_alloc,
                 "budget %d; %s" % (BUDGET, "published 12/1/2/1" if mapping == "archived"
                                    else "corrected 11/1/2/2 (differs from the published arm)"))
        show("budget is respected by both mappings",
             "%s" % [sum(ARCHIVED_ALLOCATIONS[m].values()) for m in ("archived", "corrected")],
             all(sum(ARCHIVED_ALLOCATIONS[m].values()) == BUDGET for m in ("archived", "corrected")),
             "every allocation must sum to %d rank-layers" % BUDGET)

    arch_rules = read_archived_rules()
    show("archived block-level rules archive", rel(ARCHIVE_RULES_REIMPL), bool(arch_rules),
         "allocation.igu of p3_baseline_rules.json")
    if arch_rules:
        show("reimplementation allocation equals %s" % [REIMPL_ALLOCATION[b] for b in BLOCKS],
             "%s" % [arch_rules["allocation"].get(b) for b in BLOCKS],
             arch_rules["allocation"] == REIMPL_ALLOCATION,
             "tools/_p1514_p3_baseline_rules.py (integrated gradients along zero -> probe)")

    arm_off = read_arm(ARCHIVE_ARM_OFFICIAL)
    show("archived official trained arm", os.path.basename(ARCHIVE_ARM_OFFICIAL), bool(arm_off),
         "Delta E = %s (published S39 number)" % ARCHIVED_DELTA_OFFICIAL)
    if arm_off:
        show("archived official arm delta_E", "%+0.1f" % float(arm_off["delta_E"]),
             abs(float(arm_off["delta_E"]) - ARCHIVED_DELTA_OFFICIAL) < 1e-9,
             "the published number this comparison is anchored to")
        show("archived official arm E(0)", "%0.1f" % float(arm_off["E0"]),
             abs(float(arm_off["E0"]) - E0_ARCHIVED) < 1e-9,
             "same E(0) for every arm of the protocol")
    arm_re = read_arm(ARCHIVE_ARM_REIMPL)
    show("archived reimplementation trained arm", os.path.basename(ARCHIVE_ARM_REIMPL), bool(arm_re),
         "Delta E = %s (S27 number)" % ARCHIVED_DELTA_REIMPL)
    if arm_re:
        show("archived reimplementation arm delta_E", "%+0.1f" % float(arm_re["delta_E"]),
             abs(float(arm_re["delta_E"]) - ARCHIVED_DELTA_REIMPL) < 1e-9,
             "the published number this comparison is anchored to")

    ok_data = os.path.exists(DATA_FILE)
    show("training shard present", rel(DATA_FILE), ok_data, "blank-image protocol shard")
    if ok_data:
        digest = sha256_file(DATA_FILE)
        show("training shard sha256", digest[:16], digest == DATA_SHA256,
             "pinned; a different shard silently changes the training set")
    globbed = sorted(glob.glob(os.path.join(REPO, "paper3", "train-*.parquet")))
    show("run_training.py's default glob still resolves to that shard",
         os.path.basename(globbed[0]) if globbed else "-",
         bool(globbed) and globbed[0] == DATA_FILE,
         "otherwise the archived commands would train on a different file")

    show("training entry point present", rel(TRAIN_SCRIPT), os.path.isfile(TRAIN_SCRIPT),
         "the only training path of this comparison")
    for name, path in (("CLIP backbone", CLIP_MODEL), ("marine captions", CAPTIONS_JSON)):
        present = os.path.exists(path)
        show("%s present" % name, rel(path), present or not require_gpu_assets,
             "needed by the allocation stage" if present else
             "MISSING on the instance: fetch it with the mirror-first rule before --stage allocate")
    if os.path.exists(CAPTIONS_JSON):
        caps = load_json(CAPTIONS_JSON).get("captions") or []
        show("marine captions non-empty", "%d captions" % len(caps), len(caps) >= ALLOC_BATCH,
             "the allocation stage draws %d per step" % ALLOC_BATCH)

    if os.path.exists(COMPARE_OUT):
        try:
            owner = (load_json(COMPARE_OUT).get("meta") or {}).get("script")
        except Exception:  # noqa: BLE001
            owner = "unreadable"
        show("existing compare output is owned by this script", rel(COMPARE_OUT),
             owner == rel(os.path.abspath(__file__)),
             "meta.script = %r; a foreign file at this path would be overwritten by --compare"
             % owner)
    else:
        show("compare output path is free", rel(COMPARE_OUT), True,
             "--compare will create it; --dry-run never writes it")
    return 0 if all(ok for _, ok in CHECKS) else 1


# ------------------------------------------------------------------------------------------------
# --run-official
# ------------------------------------------------------------------------------------------------
def read_captions(n: int):
    from PIL import Image
    caps = load_json(CAPTIONS_JSON)["captions"]
    if len(caps) < n:
        raise RuntimeError("%s carries %d captions" % (rel(CAPTIONS_JSON), len(caps)))
    return caps


def run_allocation_stage(dry_run: bool) -> dict:
    """Run the official allocator on CLIP and return {module_ranks, mappings, env, ...}."""
    if dry_run:
        print("  [dry run] would load %s, replace 96 attention projections with the official" %
              rel(CLIP_MODEL))
        print("            SVDLoRAModule(r=%d, alpha=%d), feed the official RankAllocator the name" %
              (ALLOC_MODULE_RANK, ALLOC_MODULE_ALPHA))
        print("            proxy, run %d contrastive steps x %d captions (seed %d, AdamW lr %g)," %
              (ALLOC_STEPS, ALLOC_BATCH, ALLOC_SEED, ALLOC_LR))
        print("            then aggregate the surviving ranks under both block mappings.")
        return {}
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    import torch
    import torch.nn as nn
    from PIL import Image
    from transformers import CLIPModel, CLIPProcessor

    sys.path.insert(0, OFFICIAL_DIR)
    from iglora.lora_module import SVDLoRAModule          # official, unmodified
    from iglora.rank_allocator import RankAllocator       # official, unmodified

    torch.manual_seed(ALLOC_SEED)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CLIPModel.from_pretrained(CLIP_MODEL, local_files_only=True).float().to(device)
    proc = CLIPProcessor.from_pretrained(CLIP_MODEL, local_files_only=True)

    proj_map = {"q_proj": "q_proj", "k_proj": "k_proj", "v_proj": "v_proj", "out_proj": "o_proj"}
    mapping, targets = {}, []
    modules = dict(model.named_modules())
    for name, mod in list(modules.items()):
        if not isinstance(mod, nn.Linear) or ".self_attn." not in name:
            continue
        proj = name.rsplit(".", 1)[-1]
        if proj not in proj_map:
            continue
        if "text_model.encoder.layers." in name:
            idx = int(name.split("text_model.encoder.layers.")[1].split(".")[0])
            llm_idx = idx
        elif "vision_model.encoder.layers." in name:
            idx = int(name.split("vision_model.encoder.layers.")[1].split(".")[0])
            llm_idx = 100 + idx
        else:
            continue
        parent = modules[name.rsplit(".", 1)[0]]
        new_mod = SVDLoRAModule(mod, mod.in_features, mod.out_features,
                                r=ALLOC_MODULE_RANK, lora_alpha=ALLOC_MODULE_ALPHA)
        setattr(parent, proj, new_mod)
        prefix = "model.layers.%d.self_attn.%s" % (llm_idx, proj_map[proj])
        mapping[prefix + ".lora_A"] = new_mod.lora_A
        mapping[prefix + ".lora_B"] = new_mod.lora_B
        mapping[prefix + ".lora_E"] = new_mod.lora_E
        targets.append((llm_idx, proj, prefix))

    class _NameProxy(nn.Module):
        """Presents the adapted CLIP modules under LLM-style names to the official allocator."""

        def __init__(self, mp):
            super().__init__()
            self._mp = mp

        def named_parameters(self, *args, **kwargs):
            return iter(self._mp.items())

    proxy = _NameProxy(mapping)
    params = [p for n, p in model.named_parameters() if "lora_" in n and p.requires_grad]
    allocator = RankAllocator(proxy, lora_r=ALLOC_MODULE_RANK, target_rank=ALLOC_TARGET_RANK,
                              init_warmup=ALLOC_INIT_WARMUP, final_warmup=ALLOC_FINAL_WARMUP,
                              mask_interval=ALLOC_MASK_INTERVAL, beta1=ALLOC_BETA1,
                              beta2=ALLOC_BETA2, total_step=ALLOC_STEPS)
    opt = torch.optim.AdamW(params, lr=ALLOC_LR)
    caps = read_captions(ALLOC_BATCH)
    n = len(caps)
    print("  official allocator: %d adapted modules, %d trainable tensors, %d steps"
          % (len(targets), len(params), ALLOC_STEPS))
    losses = []
    for step in range(ALLOC_STEPS):
        picks = [int((step * ALLOC_BATCH + k) % n) for k in range(ALLOC_BATCH)]
        images = [Image.open(os.path.join(CAPTIONS_DIR, "%04d.jpg" % i)).convert("RGB")
                  for i in picks]
        inp = proc(text=[caps[i] for i in picks], images=images, return_tensors="pt",
                   padding=True, truncation=True)
        inp = {k: v.to(device) for k, v in inp.items()}
        out = model(**inp, return_loss=True)
        opt.zero_grad(set_to_none=True)
        out.loss.backward()
        opt.step()
        allocator.update_and_mask(proxy, step)
        losses.append(float(out.loss))
        if step % 5 == 0 or step == ALLOC_STEPS - 1:
            print("    step %2d/%d loss %.4f" % (step + 1, ALLOC_STEPS, losses[-1]), flush=True)

    module_ranks = {}
    for llm_idx, proj, prefix in targets:
        e = mapping[prefix + ".lora_E"]
        module_ranks[prefix] = int((e.abs().sum(dim=1) > 0).sum().item())
    out = {"module_ranks": module_ranks, "env": env_fingerprint(),
           "loss_first": losses[0] if losses else None, "loss_last": losses[-1] if losses else None,
           "steps": ALLOC_STEPS, "seed": ALLOC_SEED,
           "module_rank": ALLOC_MODULE_RANK, "module_alpha": ALLOC_MODULE_ALPHA,
           "target_rank": ALLOC_TARGET_RANK, "init_warmup": ALLOC_INIT_WARMUP,
           "final_warmup": ALLOC_FINAL_WARMUP, "mask_interval": ALLOC_MASK_INTERVAL,
           "beta1": ALLOC_BETA1, "beta2": ALLOC_BETA2, "lr": ALLOC_LR, "batch": ALLOC_BATCH,
           "clip_model": rel(CLIP_MODEL), "captions": rel(CAPTIONS_JSON)}
    for name in ("archived", "corrected"):
        sums = block_sums(module_ranks, name)
        out[name] = {"block_rank_sum": sums, "allocation": allocate_from_sums(sums),
                     "matches_archive": all(abs(sums[b] - ARCHIVED_MODULE_SUMS[name][b]) < 1e-9
                                            for b in BLOCKS)}
    return out


def predict_side_effects(seed: int, allocation: dict) -> list:
    """Files paper3/scripts/run_training.py writes when a block-config arm runs.

    With --rank-vision/--rank-shallow/--rank-mid/--rank-deep the tag is fully replaced by
    '_bcexplicit_v<V>_s<S>_m<M>_d<D>' (see the script's tag logic), and the per-epoch partial file
    is 'verify_r<rank>_s<seed>_b1_partial.json' (no block tag).
    """
    tag = "_bcexplicit_v%d_s%d_m%d_d%d" % (allocation["vision"], allocation["text_shallow"],
                                           allocation["text_mid"], allocation["text_deep"])
    return [os.path.join(EXP, "verify_r%d_s%d%s.json" % (BASE_RANK, seed, tag)),
            os.path.join(EXP, "verify_r%d_s%d_b1_partial.json" % (BASE_RANK, seed))]


def restore_owned(label: str, path: str, prev) -> None:
    """Undo the training script's overwrite of a file this round does not own."""
    if prev is None:
        if os.path.exists(path):
            os.remove(path)
            print("      removed the transient %s %s" % (label, rel(path)))
    else:
        with open(path, "wb") as fh:
            fh.write(prev)
        print("      restored the pre-existing %s %s" % (label, rel(path)))


def restore_side_effects(expected: list, saved: dict) -> None:
    """Undo run_training.py's side effects on the files this round does NOT own.

    `expected` is predict_side_effects(): [target arm archive, per-epoch partial by-product].
    The FIRST entry is this round's product and must NEVER be restored or removed.

    2026-10-25 defect: the pre-fix code applied restore_owned() to *every* entry, so when the
    target arm was a new filename (prev is None) it was deleted immediately after training, and
    run_one_arm then failed with "no usable archive ... after training". The restore belongs to
    the by-products only; that is what this helper isolates (and what --self-test now exercises).
    """
    if not expected:
        return
    for path in expected[1:]:
        restore_owned("training by-product", path, saved.get(path))


def train_command(allocation: dict, seed: int, python: str) -> list:
    """The exact argv of one arm: identical to the archived bcexplicit arm except the allocation."""
    return [python, TRAIN_SCRIPT,
            "--rank", str(BASE_RANK),
            "--rank-vision", str(allocation["vision"]),
            "--rank-shallow", str(allocation["text_shallow"]),
            "--rank-mid", str(allocation["text_mid"]),
            "--rank-deep", str(allocation["text_deep"]),
            "--seed", str(seed),
            "--epochs", str(EPOCHS),
            "--num-samples", str(NUM_SAMPLES),
            "--lora-alpha", fmt_alpha(LORA_ALPHA),
            "--data-path", DATA_FILE]


def run_one_arm(config: str, allocation: dict, seed: int, python: str, force: bool) -> dict:
    """Train one arm, keep the archive, and return its record (no wall-clock field)."""
    expected = predict_side_effects(seed, allocation)
    target = expected[0]
    if os.path.exists(target) and not force:
        arm = read_arm(target)
        if (arm.get("rank") == BASE_RANK and arm.get("seed") == seed
                and arm.get("lora_alpha") is not None
                and abs(float(arm["lora_alpha"]) - LORA_ALPHA) < 1e-9
                and arm.get("epochs") == EPOCHS and arm.get("num_samples") == NUM_SAMPLES
                and arm.get("ok") is True and arm.get("delta_E") is not None):
            print("    seed %s: existing arm archive is valid; skipping (--force to re-run)" % seed)
            return {"config": config, "side": CONFIGS[config]["side"], "seed": seed,
                    "allocation": dict(allocation), "from_cache": True, **arm,
                    "archive_preserved": False}

    saved = {}
    for path in expected:
        if os.path.exists(path):
            with open(path, "rb") as fh:
                saved[path] = fh.read()
            print("      preserving the pre-existing %s (run_training.py rewrites it)" % rel(path))
    cmd = train_command(allocation, seed, python)
    print("      %s" % printable_command(cmd))
    proc = subprocess.run(cmd, cwd=REPO)
    # Only the by-products are restored; the target arm archive is this round's product.
    restore_side_effects(expected, saved)
    if proc.returncode != 0:
        raise RuntimeError("run_training.py exited %d for config=%s seed=%d"
                           % (proc.returncode, config, seed))
    # Regression guard (2026-10-25 defect): the target must exist AND parse before it is
    # interpreted. Without this, a restore-logic regression silently deletes a finished arm.
    if not os.path.exists(target):
        raise RuntimeError("training finished but the target archive %s is missing; the "
                           "side-effect restore must never touch it" % rel(target))
    arm = read_arm(target)
    if arm.get("delta_E") is None:
        raise RuntimeError("target archive %s did not parse into a usable arm after training"
                           % rel(target))
    if not arm or arm.get("delta_E") is None:
        raise RuntimeError("no usable archive at %s after training" % rel(target))
    if arm.get("seed") != seed or arm.get("epochs") != EPOCHS or arm.get("num_samples") != NUM_SAMPLES:
        raise RuntimeError("archive %s does not match the requested protocol" % rel(target))
    return {"config": config, "side": CONFIGS[config]["side"], "seed": seed,
            "allocation": dict(allocation), "from_cache": False, **arm,
            "archive_preserved": bool(saved.get(target))}


def merge_block_maps(run: dict, payload: dict) -> dict:
    """Preserve/refresh the per-block maps when --stage train rewrites the run archive.

    2026-10-25 defect #2: this used to read `run["module_ranks"]` only. The allocate stage stores
    the ranks under `allocation_stage.module_ranks`, so the lookup returned {} -> block_sums was
    all zeros -> allocate_from_sums(zeros) wrote a uniform [4,4,4,4] over the correct
    [11,1,2,2]; the next --stage train then refused with "corrected allocation differs from the
    pinned". The fixed precedence is: explicit top-level maps, else module_ranks (either
    location), else keep whatever the payload already carries (never overwrite with zeros).
    """
    payload["block_maps"] = payload.get("block_maps") or {}
    for name in ("archived", "corrected"):
        src = run.get(name) if run else None
        if src:
            payload["block_maps"][name] = {"block_rank_sum": src["block_rank_sum"],
                                           "allocation": src["allocation"],
                                           "matches_archive": src["matches_archive"]}
            continue
        ranks = (run.get("module_ranks")
                 or (run.get("allocation_stage") or {}).get("module_ranks") or {}) if run else {}
        if ranks:
            sums = block_sums(ranks, name)
            payload["block_maps"][name] = {"block_rank_sum": sums,
                                           "allocation": allocate_from_sums(sums)}
        # else: nothing authoritative to refresh from -> keep payload["block_maps"][name] as-is
    return payload


def stage_train(configs, seeds, python: str, dry_run: bool, force: bool) -> int:
    run = read_run_archive()
    allocations = {m: (run.get("block_maps", {}).get(m, {}).get("allocation")
                       or ARCHIVED_ALLOCATIONS.get(m)) for m in ("archived", "corrected")}
    rules = read_archived_rules()
    if rules.get("allocation"):
        allocations["reimpl"] = rules["allocation"]
    records = list(run.get("runs") or [])
    done = {(r.get("config"), r.get("seed")) for r in records}
    print("\n[2] training %d config(s) x %d seed(s) = %d arm(s)"
          % (len(configs), len(seeds), len(configs) * len(seeds)))
    for config in configs:
        if config not in CONFIGS:
            print("  ERROR: unknown --config %r; known: %s" % (config, sorted(CONFIGS)))
            return 2
        spec = CONFIGS[config]
        if spec["side"] == "reimpl":
            alloc = allocations.get("reimpl")
        else:
            alloc = allocations.get(spec["block_map"])
        if not alloc:
            print("  ERROR: no allocation available for %s; run --stage allocate first" % config)
            return 2
        if spec["side"] == "official" and alloc != spec["allocation"]:
            print("  ERROR: the run archive's %s allocation %s differs from the pinned %s"
                  % (spec["block_map"], alloc, spec["allocation"]))
            return 2
        print("  config %-24s side=%-8s allocation(v/s/m/d)=%s" %
              (config, spec["side"], [alloc[b] for b in BLOCKS]))
        for seed in seeds:
            if (config, seed) in done and not force:
                print("    seed %s: already recorded in %s; skipping" % (seed, rel(RUN_ARCHIVE)))
                continue
            if dry_run:
                print("    seed %s: %s" % (seed, printable_command(train_command(alloc, seed, python))))
                for extra in (predict_side_effects(seed, alloc)[1],):
                    print("             (also writes %s)" % rel(extra))
                continue
            record = run_one_arm(config, alloc, seed, python, force)
            archived = (ARCHIVED_DELTA_OFFICIAL if config == "official_archived_map"
                        else (ARCHIVED_DELTA_REIMPL if config == "reimpl_igu_style" else None))
            if archived is not None and seed == 42:
                record["reproduction"] = {"archived_delta_E": archived,
                                          "delta": float(record["delta_E"]) - archived,
                                          "equal": abs(float(record["delta_E"]) - archived) < 1e-9}
                print("      reproduction check: %+0.1f vs archived %+0.1f (%s)"
                      % (float(record["delta_E"]), archived,
                         "identical" if record["reproduction"]["equal"]
                         else "DIFFERENT environment or protocol"))
            record["command"] = train_command(alloc, seed, python)
            record["env"] = env_fingerprint()
            records = [r for r in records if not (r.get("config") == config and r.get("seed") == seed)]
            records.append(record)
            done.add((config, seed))
    if dry_run:
        print("\n  dry run: nothing was executed and nothing was written")
        return 0
    payload = run or {"meta": {}, "block_maps": {}, "runs": []}
    payload["meta"] = {
        "script": rel(os.path.abspath(__file__)),
        "task": "P3 task A: official IGU-LoRA allocator vs the block-level reimplementation",
        "protocol": ("paper3/scripts/run_training.py, blank-image protocol, %d samples, %d epochs, "
                     "lr %g, batch 1, base rank %d, alpha %g, qkvo targets"
                     % (NUM_SAMPLES, EPOCHS, LR, BASE_RANK, LORA_ALPHA)),
        "official_code": {"url": OFFICIAL_URL, "commit": OFFICIAL_COMMIT, "paper": OFFICIAL_PAPER,
                          "vendored_at": rel(OFFICIAL_DIR)},
        "fair_comparison": ("data / epochs / lr / batch / rank budget / seeds / evaluation identical "
                            "across configs; only the allocation rule differs"),
        "deterministic": True,
        "note": "no wall-clock field is written; re-running --stage train on unchanged inputs "
                "reproduces this file byte for byte",
    }
    merge_block_maps(run, payload)
    payload["runs"] = sorted(records, key=lambda r: (str(r.get("config")), int(r.get("seed", -1))))
    payload["runs_sha256"] = sha256_json(payload["runs"])
    write_json(RUN_ARCHIVE, payload)
    print("\n  wrote %s (%d runs)" % (rel(RUN_ARCHIVE), len(payload["runs"])))
    return 0


def run_official(args) -> int:
    print("=" * 118)
    print("P3 TASK A -- INSTANCE RUN (GPU).  Nothing is downloaded; every asset is a local path.")
    print("=" * 118)
    rc = verify_inputs(require_gpu_assets=not args.dry_run)
    print("\n  input ledger: %d checks, %d failed"
          % (len(CHECKS), sum(1 for _, ok in CHECKS if not ok)))
    if rc != 0 and not args.dry_run:
        print("  refusing to run: fix the inputs above first")
        return 2
    if not args.dry_run and not os.path.isdir(os.path.join(OFFICIAL_DIR, ".git")):
        print("  ERROR: the official clone is missing.  On the instance run:")
        print("      %s" % CLONE_COMMAND)
        return 2

    if args.stage in ("allocate", "all"):
        print("\n[1] official allocation stage")
        if not args.dry_run:
            stage = run_allocation_stage(False)
            payload = read_run_archive() or {"meta": {}, "block_maps": {}, "runs": []}
            payload["allocation_stage"] = stage
            for name in ("archived", "corrected"):
                payload["block_maps"][name] = {
                    "block_rank_sum": stage[name]["block_rank_sum"],
                    "allocation": stage[name]["allocation"],
                    "matches_archive": stage[name]["matches_archive"],
                    "source": "official RankAllocator run of %s" % rel(RUN_ARCHIVE)}
            payload.setdefault("meta", {})["script"] = rel(os.path.abspath(__file__))
            payload["runs"] = sorted(payload.get("runs") or [],
                                     key=lambda r: (str(r.get("config")), int(r.get("seed", -1))))
            write_json(RUN_ARCHIVE, payload)
            for name in ("archived", "corrected"):
                ok = stage[name]["matches_archive"]
                show("allocator reproduces the %s block sums" % name,
                     "%s" % [int(stage[name]["block_rank_sum"][b]) for b in BLOCKS], ok,
                     "expected %s; allocation %s"
                     % ([int(ARCHIVED_MODULE_SUMS[name][b]) for b in BLOCKS],
                        [stage[name]["allocation"][b] for b in BLOCKS]))
            print("  wrote %s (allocation stage)" % rel(RUN_ARCHIVE))
            if not all(stage[m]["matches_archive"] for m in ("archived", "corrected")):
                print("  STOP: the allocator did not reproduce the archived per-module ranks.")
                print("        Do not train arms from it; report the drift instead.")
                return 3
        else:
            run_allocation_stage(True)

    if args.stage in ("train", "all"):
        configs = [c for c in (args.config or "").split(",") if c]
        seeds = [int(s) for s in (args.seeds or "").split(",") if s]
        rc = stage_train(configs, seeds, args.python or sys.executable, args.dry_run, args.force)
        if rc != 0:
            return rc
    print("\n  next: %s --compare%s" % (rel(os.path.abspath(__file__)),
                                        " --dry-run" if args.dry_run else ""))
    return 0


# ------------------------------------------------------------------------------------------------
# --compare
# ------------------------------------------------------------------------------------------------
def gather_official(run: dict, config: str) -> dict:
    """Official side: the round's runs for the selected config (or the archived arm for seed 42)."""
    if not config:
        for candidate in ("official_corrected_map", "official_archived_map"):
            if any(r.get("config") == candidate for r in (run.get("runs") or [])):
                config = candidate
                break
        else:
            config = "official_archived_map"
    runs = [r for r in (run.get("runs") or []) if r.get("config") == config]
    alloc, alloc_src = None, None
    for r in runs:
        alloc, alloc_src = r.get("allocation"), rel(RUN_ARCHIVE)
        break
    if alloc is None:
        maps = (run.get("block_maps") or {})
        for name in ("archived", "corrected"):
            entry = maps.get(name) or {}
            if entry.get("allocation") and (
                    (name == "archived" and config == "official_archived_map")
                    or (name == "corrected" and config == "official_corrected_map")):
                alloc, alloc_src = entry["allocation"], rel(RUN_ARCHIVE)
                break
    if alloc is None and config == "official_archived_map":
        arch = read_archived_official()
        if arch.get("allocation"):
            alloc, alloc_src = arch["allocation"], arch["path"]
    if not runs and config == "official_archived_map":
        arm = read_arm(ARCHIVE_ARM_OFFICIAL)
        if arm:
            runs = [{"config": config, "side": "official", "seed": int(arm["seed"]),
                     "allocation": alloc, "delta_E": arm["delta_E"], "E": arm["E"],
                     "E0": arm["E0"], "archive": arm["path"], "archive_sha256": arm["sha256"],
                     "env": {}, "from_archive": True, "reproduction": None}]
    return {"config": config, "allocation": alloc, "allocation_source": alloc_src,
            "runs": sorted(runs, key=lambda r: int(r.get("seed", -1)))}


def gather_reimpl(run: dict) -> dict:
    """Reimplementation side: the round's runs, plus the archived seed-42 arm when it is missing."""
    runs = [r for r in (run.get("runs") or []) if r.get("config") == "reimpl_igu_style"]
    rules = read_archived_rules()
    alloc = (runs[0].get("allocation") if runs else None) or rules.get("allocation")
    seeds = {int(r.get("seed")) for r in runs}
    if 42 not in seeds:
        arm = read_arm(ARCHIVE_ARM_REIMPL)
        if arm:
            runs = list(runs) + [{"config": "reimpl_igu_style", "side": "reimpl", "seed": 42,
                                  "allocation": alloc, "delta_E": arm["delta_E"], "E": arm["E"],
                                  "E0": arm["E0"], "archive": arm["path"],
                                  "archive_sha256": arm["sha256"], "env": {},
                                  "from_archive": True, "reproduction": None}]
    return {"config": "reimpl_igu_style", "allocation": alloc,
            "allocation_source": (rel(RUN_ARCHIVE) if any(
                r.get("config") == "reimpl_igu_style" for r in (run.get("runs") or []))
                else rules.get("path")),
            "runs": sorted(runs, key=lambda r: int(r.get("seed", -1)))}


def compare_core(official: dict, reimpl: dict, n_boot: int) -> dict:
    """The quantitative gap, per configuration and overall (pure function; --self-test uses it)."""
    o_runs = {int(r["seed"]): r for r in official["runs"]}
    r_runs = {int(r["seed"]): r for r in reimpl["runs"]}
    common = sorted(set(o_runs) & set(r_runs))
    pairs, diffs, mixed_stack = [], [], False
    for seed in common:
        o, r = o_runs[seed], r_runs[seed]
        o_env, r_env = (o.get("env") or {}), (r.get("env") or {})
        same_stack = bool(o_env) and bool(r_env) and all(
            o_env.get(k) == r_env.get(k) for k in ("torch", "cuda", "gpu"))
        if o.get("from_archive") or r.get("from_archive"):
            same_stack = False
        if not same_stack:
            mixed_stack = True
        diffs.append(float(o["delta_E"]) - float(r["delta_E"]))
        pairs.append({"seed": seed,
                      "official": {"delta_E": float(o["delta_E"]), "E": o.get("E"),
                                   "archive": o.get("archive"), "from_archive":
                                       bool(o.get("from_archive")), "env": o_env},
                      "reimpl": {"delta_E": float(r["delta_E"]), "E": r.get("E"),
                                 "archive": r.get("archive"), "from_archive":
                                     bool(r.get("from_archive")), "env": r_env},
                      "gap": float(o["delta_E"]) - float(r["delta_E"]),
                      "same_stack": same_stack})

    rng = np.random.default_rng(RNG_SEED)
    stat = paired_bootstrap(diffs, MARGIN_ABS, rng, n_boot)
    alloc_gap = {}
    if official.get("allocation") and reimpl.get("allocation"):
        oa, ra = official["allocation"], reimpl["allocation"]
        alloc_gap = {"per_block": {b: {"official": int(oa.get(b, 0)), "reimpl": int(ra.get(b, 0)),
                                       "gap": int(oa.get(b, 0)) - int(ra.get(b, 0)),
                                       "abs_gap": abs(int(oa.get(b, 0)) - int(ra.get(b, 0)))}
                                   for b in BLOCKS},
                     "l1": l1_gap(oa, ra), "share_l1": share_l1(oa, ra),
                     "tolerance": ALLOC_L1_TOLERANCE,
                     "within_tolerance": l1_gap(oa, ra) <= ALLOC_L1_TOLERANCE,
                     "same_budget": (sum(int(oa.get(b, 0)) for b in BLOCKS) == BUDGET
                                     and sum(int(ra.get(b, 0)) for b in BLOCKS) == BUDGET),
                     "exact_match": all(int(oa.get(b, 0)) == int(ra.get(b, 0)) for b in BLOCKS)}

    sensitivity = {}
    for name in ("archived", "corrected"):
        archived = ARCHIVED_ALLOCATIONS.get(name)
        if archived and reimpl.get("allocation"):
            sensitivity[name] = {"official": archived, "reimpl": reimpl["allocation"],
                                 "l1": l1_gap(archived, reimpl["allocation"]),
                                 "within_tolerance":
                                     l1_gap(archived, reimpl["allocation"]) <= ALLOC_L1_TOLERANCE}

    arm_verdict = arm_equivalence_verdict(stat)
    alloc_ok = bool(alloc_gap.get("within_tolerance"))
    if arm_verdict == "equivalent" and alloc_ok:
        overall = "small"
    elif arm_verdict == "different":
        overall = "large"
    else:
        overall = "mixed"

    traj = []
    for pair in pairs:
        o_e, r_e = pair["official"]["E"] or [], pair["reimpl"]["E"] or []
        if len(o_e) == len(r_e) and o_e:
            traj.append({"seed": pair["seed"],
                         "gap_per_epoch": [float(a) - float(b) for a, b in zip(o_e, r_e)],
                         "note": "descriptive only: epochs inside a seed are not independent"})
    return {
        "pairing": "paired by seed; the same seed value is used on both sides",
        "seeds_common": common, "n_pairs": len(common),
        "same_stack_for_every_pair": (bool(pairs) and not mixed_stack),
        "stack_mix_warning": ("at least one pair mixes a fresh run with an archived arm or mixes "
                              "environments; the paired difference is still taken on the same seed, "
                              "but the interval must not be read as a same-stack interval"
                              if mixed_stack else None),
        "pairs": pairs,
        "per_configuration": {
            "allocation": alloc_gap,
            "trained_arm_delta_E": stat,
            "arm_verdict": arm_verdict,
            "trajectory_gap": traj,
        },
        "allocation_sensitivity_to_the_block_mapping": sensitivity,
        "overall": {
            "official_config": official["config"],
            "official_allocation_source": official.get("allocation_source"),
            "reimpl_allocation_source": reimpl.get("allocation_source"),
            "mean_gap_delta_E": stat.get("mean_gap"),
            "ci95": stat.get("ci95"),
            "margin": MARGIN_ABS,
            "margin_fraction_of_E0": MARGIN_FRACTION,
            "allocation_l1": alloc_gap.get("l1"),
            "allocation_within_tolerance": alloc_ok,
            "arm_verdict": arm_verdict,
            "verdict": overall,
            "rule": ("small = arm equivalent (|mean gap| <= %g x E0 and TOST equivalent) AND "
                     "allocation L1 <= %d; large = the arm gap exceeds the margin or its CI "
                     "excludes equivalence; mixed = exactly one of the two holds"
                     % (MARGIN_FRACTION, ALLOC_L1_TOLERANCE)),
            "ci_unavailable_reason": stat.get("unavailable_reason"),
        },
    }


def compare(args) -> int:
    print("=" * 118)
    print("P3 TASK A -- OFFICIAL vs BLOCK-LEVEL REIMPLEMENTATION: %s" % rel(COMPARE_OUT))
    print("=" * 118)
    run = read_run_archive()
    official = gather_official(run, args.official_config)
    reimpl = gather_reimpl(run)
    print("\n[1] inputs")
    print("  official config        : %s" % official["config"])
    print("  official allocation    : %s (%s)"
          % (official["allocation"], official.get("allocation_source") or "-"))
    print("  official arms          : %s"
          % [(r["seed"], float(r["delta_E"]), "archive" if r.get("from_archive") else "run")
             for r in official["runs"]])
    print("  reimplementation alloc : %s (%s)"
          % (reimpl["allocation"], reimpl.get("allocation_source") or "-"))
    print("  reimplementation arms  : %s"
          % [(r["seed"], float(r["delta_E"]), "archive" if r.get("from_archive") else "run")
             for r in reimpl["runs"]])
    show("official side present", "%d arm(s)" % len(official["runs"]), bool(official["runs"]),
         "produce it with --run-official --stage train --config %s" % official["config"])
    show("reimplementation side present", "%d arm(s)" % len(reimpl["runs"]), bool(reimpl["runs"]),
         "produce it with --run-official --stage train --config reimpl_igu_style, or restore %s"
         % rel(ARCHIVE_ARM_REIMPL))
    if not official["runs"] or not reimpl["runs"]:
        print("\n  STOP: one side is missing, so no gap is reported.  Exact producer commands:")
        if not official["runs"]:
            print("      %s --run-official --stage all" % rel(os.path.abspath(__file__)))
            print("      (the archived fallback needs %s)" % rel(ARCHIVE_ARM_OFFICIAL))
        if not reimpl["runs"]:
            print("      %s --run-official --stage train --config reimpl_igu_style --seeds 42"
                  % rel(os.path.abspath(__file__)))
            print("      (the archived fallback needs %s)" % rel(ARCHIVE_ARM_REIMPL))
        return 2

    payload = compare_core(official, reimpl, args.n_boot)
    print("\n[2] allocation gap")
    ag = payload["per_configuration"]["allocation"]
    if ag:
        for block in BLOCKS:
            e = ag["per_block"][block]
            print("    %-14s official %2d  reimpl %2d  gap %+d" % (block, e["official"], e["reimpl"],
                                                                   e["gap"]))
        print("    L1 = %d of %d (tolerance %d, within=%s); share L1 = %.4f; same budget=%s; exact=%s"
              % (ag["l1"], BUDGET, ALLOC_L1_TOLERANCE, ag["within_tolerance"], ag["share_l1"],
                 ag["same_budget"], ag["exact_match"]))
    print("\n[3] trained-arm gap (paired by seed, %d bootstrap replicates)" % args.n_boot)
    stat = payload["per_configuration"]["trained_arm_delta_E"]
    for pair in payload["pairs"]:
        print("    seed %-5s official %+8.2f  reimpl %+8.2f  gap %+8.2f  same_stack=%s%s"
              % (pair["seed"], pair["official"]["delta_E"], pair["reimpl"]["delta_E"], pair["gap"],
                 pair["same_stack"], "  (archived)" if pair["official"]["from_archive"]
                 or pair["reimpl"]["from_archive"] else ""))
    if stat.get("ci95"):
        print("    mean gap %+0.4f  95%% CI [%+0.4f, %+0.4f]  TOST p=%.4f  min equivalent margin %.4f"
              % (stat["mean_gap"], stat["ci95"][0], stat["ci95"][1], stat["tost_p"],
                 stat["min_equivalent_margin"]))
    else:
        print("    mean gap %+0.4f  (no interval: %s)" % (stat["mean_gap"],
                                                         stat.get("unavailable_reason")))
    print("    arm verdict: %s" % payload["per_configuration"]["arm_verdict"])

    print("\n[4] allocation sensitivity to the block mapping (which mapping the official side used)")
    for name, block in (payload["allocation_sensitivity_to_the_block_mapping"] or {}).items():
        print("    %-10s official %s vs reimpl %s -> L1 %d (within tolerance=%s)"
              % (name, [block["official"][b] for b in BLOCKS],
                 [block["reimpl"][b] for b in BLOCKS], block["l1"], block["within_tolerance"]))

    print("\n[5] overall verdict: %s" % payload["overall"]["verdict"].upper())
    print("    %s" % payload["overall"]["rule"])
    output = {
        "meta": {
            "script": rel(os.path.abspath(__file__)),
            "task": "P3 task A: official IGU-LoRA allocator vs the block-level reimplementation",
            "official_code": {"url": OFFICIAL_URL, "commit": OFFICIAL_COMMIT,
                              "paper": OFFICIAL_PAPER, "vendored_at": rel(OFFICIAL_DIR)},
            "n_boot": args.n_boot, "rng_seed": RNG_SEED, "alpha": ALPHA,
            "margin": MARGIN_ABS, "margin_fraction_of_E0": MARGIN_FRACTION,
            "allocation_l1_tolerance": ALLOC_L1_TOLERANCE,
            "protocol": ("blank-image protocol: %d samples, %d epochs, lr %g, batch 1, base rank %d, "
                         "alpha %g, seeds %s" % (NUM_SAMPLES, EPOCHS, LR, BASE_RANK, LORA_ALPHA,
                                                 ",".join(str(s) for s in SEEDS_DEFAULT))),
            "method": "paired (by seed) percentile bootstrap of the mean delta_E difference plus "
                      "TOST against the pre-declared margin; identical resampling rule to "
                      "tools/_p1595_p3_rank_separation.py vqa_contrast()",
            "inputs": {"run_archive": run.get("path"), "run_archive_sha256": run.get("sha256"),
                       "archived_official_allocation": read_archived_official().get("path"),
                       "archived_reimpl_allocation": read_archived_rules().get("path"),
                       "archived_official_arm": rel(ARCHIVE_ARM_OFFICIAL),
                       "archived_reimpl_arm": rel(ARCHIVE_ARM_REIMPL)},
            "deterministic": True,
            "note": "no wall-clock field is written, so re-running this comparison on unchanged "
                    "inputs reproduces this file byte for byte",
        },
        "official_side": {"config": official["config"], "allocation": official["allocation"],
                          "allocation_source": official.get("allocation_source"),
                          "runs": [{k: v for k, v in r.items() if k != "env"}
                                   for r in official["runs"]]},
        "reimpl_side": {"config": reimpl["config"], "allocation": reimpl["allocation"],
                        "allocation_source": reimpl.get("allocation_source"),
                        "runs": [{k: v for k, v in r.items() if k != "env"}
                                 for r in reimpl["runs"]]},
        **payload,
        "caveat_sentences": {
            "small": "The official IGU-LoRA allocator and our block-level reimplementation were "
                     "trained under the identical protocol and their alignment-energy changes differ "
                     "by less than the pre-declared 5% margin, so the allocation-rule baseline is "
                     "reported from the official implementation.",
            "mixed": "The official IGU-LoRA allocator and our block-level reimplementation agree on "
                     "the trained-arm outcome within the pre-declared margin but disagree on the "
                     "block ranks, so the baseline is reported from the official implementation and "
                     "the rank difference is stated explicitly.",
            "large": "The official IGU-LoRA allocator and our block-level reimplementation differ by "
                     "more than the pre-declared 5% margin on the identical protocol, so the "
                     "block-level numbers are not a substitute for the official implementation and "
                     "are reported as a separate, clearly labelled arm.",
        },
    }
    if args.dry_run:
        print("\n[6] dry run: computed in memory, nothing was written")
        print("    would write %s" % rel(COMPARE_OUT))
    else:
        write_json(COMPARE_OUT, output)
        print("\n[6] wrote %s" % rel(COMPARE_OUT))
        written = load_json(COMPARE_OUT)
        exact = written.get("overall", {}).get("mean_gap_delta_E") == payload["overall"]["mean_gap_delta_E"]
        show("written file carries the printed overall gap",
             "%s" % written.get("overall", {}).get("mean_gap_delta_E"), exact,
             "every printed number is re-read from the archive before it is reported")
        show("written file carries the printed L1 gap", "%s" % written["per_configuration"]
             ["allocation"].get("l1"), written["per_configuration"]["allocation"].get("l1")
             == ag.get("l1"), "printed L1 must equal the archived L1")
        show("written file carries the printed verdict", "%s" % written["overall"]["verdict"],
             written["overall"]["verdict"] == payload["overall"]["verdict"],
             "the sentence used in the paper follows this verdict")
    failed = [label for label, ok in CHECKS if not ok]
    print("\n[7] assertion ledger: %d checks, %d failed" % (len(CHECKS), len(failed)))
    for label in failed:
        print("    FAILED:", label)
    return 1 if failed else 0


# ------------------------------------------------------------------------------------------------
# --self-test (offline; writes nothing; exercises the statistics on fixtures)
# ------------------------------------------------------------------------------------------------
def self_test() -> int:
    print("=" * 118)
    print("P3 TASK A -- SELF TEST (no GPU, no network, nothing written)")
    print("=" * 118)
    print("\n[A] the resampling rule mirrors tools/_p1595_p3_rank_separation.py")
    try:
        eq = load_module("p1595_selftest", os.path.join(REPO, "tools",
                                                        "_p1595_p3_rank_separation.py"))
        vals = np.array([12.0, -48.5, 33.25, 7.0, -19.5], dtype=float)
        n_boot = 4000
        mine = paired_bootstrap(vals, 0.05, np.random.default_rng(RNG_SEED), n_boot)
        a = {"correct": vals, "f1": vals}
        b = {"correct": np.zeros_like(vals), "f1": np.zeros_like(vals)}
        theirs = eq.vqa_contrast(a, b, np.random.default_rng(RNG_SEED), n_boot)["accuracy"]
        # field-by-field: the imported function names the mean difference 'delta'
        same_names = (("mean_gap", "delta"), ("boot_mean", "boot_mean"), ("boot_se", "boot_se"),
                      ("ci95", "ci95"), ("ci90", "ci90"), ("tost_p", "tost_p"),
                      ("tost_p_lower", "tost_p_lower"), ("tost_p_upper", "tost_p_upper"),
                      ("equivalent_at_declared_margin", "equivalent_at_declared_margin"),
                      ("min_equivalent_margin", "min_equivalent_margin"),
                      ("excludes_zero_95", "excludes_zero_95"))
        drift = []
        for ours, imported in same_names:
            x, y = mine.get(ours), theirs.get(imported)
            if isinstance(x, list):
                ok = np.allclose(x, y)
            else:
                ok = (x == y)
            if not ok:
                drift.append("%s=%r vs %s=%r" % (ours, x, imported, y))
        show("paired_bootstrap == imported vqa_contrast on identical input", "%d fields"
             % len(same_names), not drift,
             "; ".join(drift) if drift else "interval, TOST p-value, verdict and minimum equivalent "
                                            "margin all agree (same RNG consumption order)")
    except Exception as exc:  # noqa: BLE001
        show("paired_bootstrap == imported vqa_contrast on identical input", "error", False,
             "%r" % (exc,))

    print("\n[B] the decision rule")
    fixture = {
        "official": {"config": "official_corrected_map",
                     "allocation": {"vision": 11, "text_shallow": 1, "text_mid": 2, "text_deep": 2},
                     "allocation_source": "fixture",
                     "runs": [{"seed": s, "delta_E": d, "E": [3921.0, 3900.0, 3800.0, 3921.0 + d],
                               "env": {"torch": "t", "cuda": "c", "gpu": "g"}, "archive": "fixture",
                               "from_archive": False} for s, d in ((42, 240.0), (123, 260.0),
                                                                   (789, 250.0))]},
        "reimpl": {"config": "reimpl_igu_style",
                   "allocation": {"vision": 11, "text_shallow": 1, "text_mid": 3, "text_deep": 1},
                   "allocation_source": "fixture",
                   "runs": [{"seed": s, "delta_E": d, "E": [3921.0, 3900.0, 3800.0, 3921.0 + d],
                             "env": {"torch": "t", "cuda": "c", "gpu": "g"}, "archive": "fixture",
                             "from_archive": False} for s, d in ((42, 333.0), (123, 340.0),
                                                                 (789, 335.0))]},
    }
    small = compare_core(fixture["official"], fixture["reimpl"], 4000)
    show("allocation L1 of 11/1/2/2 vs 11/1/3/1", "%d" % small["per_configuration"]["allocation"]["l1"],
         small["per_configuration"]["allocation"]["l1"] == 2,
         "within the tolerance of %d, so the allocation clause holds" % ALLOC_L1_TOLERANCE)
    show("fixture verdict (gaps of ~-85 within the margin)", small["overall"]["verdict"],
         small["overall"]["verdict"] == "small", "arm equivalent and allocation within tolerance")
    far = {"official": dict(fixture["official"]), "reimpl": dict(fixture["reimpl"])}
    far["official"] = dict(fixture["official"])
    far["official"]["runs"] = [dict(r, delta_E=float(r["delta_E"]) + 900.0)
                               for r in fixture["official"]["runs"]]
    big = compare_core(far["official"], far["reimpl"], 4000)
    show("fixture verdict when the arm gap exceeds the margin", big["overall"]["verdict"],
         big["overall"]["verdict"] == "large", "the large-gap sentence would be used")
    one = {"official": dict(fixture["official"]),
           "reimpl": dict(fixture["reimpl"])}
    one["official"]["runs"] = fixture["official"]["runs"][:1]
    one["reimpl"]["runs"] = fixture["reimpl"]["runs"][:1]
    single = compare_core(one["official"], one["reimpl"], 4000)
    stat = single["per_configuration"]["trained_arm_delta_E"]
    show("one paired seed yields no interval", "ci95=%s" % stat["ci95"], stat["ci95"] is None,
         "the script reports the reason instead of a number: %s" % stat["unavailable_reason"])

    print("\n[C] the training side-effect restore logic (2026-10-25 defect regression test)")
    tmp = tempfile.mkdtemp(prefix="p1639_selftest_", dir=REPO)
    try:
        def old_restore_side_effects(expected, saved):  # the pre-fix behaviour, for the contrast
            for p in expected:
                restore_owned("training by-product", p, saved.get(p))

        def scenario(fn):
            """Return (target_survives, byproduct_state) for one restore implementation."""
            d = tempfile.mkdtemp(prefix="case_", dir=tmp)
            target = os.path.join(d, "verify_r1_s42_bcexplicit_v11_s1_m2_d2.json")
            byprod = os.path.join(d, "verify_r1_s42_b1_partial.json")
            with open(target, "w", encoding="utf-8") as fh:
                fh.write('{"delta_E": 250.5, "ok": true}')          # fresh arm just trained
            with open(byprod, "w", encoding="utf-8") as fh:
                fh.write("OVERWRITTEN-BY-TRAINING")                 # training rewrote it
            saved = {byprod: b'{"transient": "pre-existing"}'}      # it pre-existed this round
            fn([target, byprod], saved)
            survives = os.path.exists(target)
            with open(byprod, "rb") as fh:
                restored = fh.read()
            return survives, restored

        new_survives, new_byprod = scenario(restore_side_effects)
        old_survives, old_byprod = scenario(old_restore_side_effects)
        show("restore keeps the freshly trained target arm", "exists" if new_survives else "deleted",
             new_survives, "the target is this round's product and must never be restored away")
        show("pre-fix logic would delete that same target arm (the defect)",
             "deleted" if not old_survives else "exists", not old_survives,
             "reproducing the 2026-10-25 failure: fresh target removed -> 'no usable archive'")
        show("restore still reverts the pre-existing by-product after training",
             "reverted" if new_byprod == b'{"transient": "pre-existing"}' else "NOT reverted",
             new_byprod == b'{"transient": "pre-existing"}',
             "the fix narrows the loop to expected[1:]; by-product handling is unchanged")
        show("by-product handling identical between the fixed and the pre-fix logic",
             "same" if new_byprod == old_byprod else "differs", new_byprod == old_byprod,
             "only the target-arm behaviour changed")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n[D] the run-archive block_maps merge logic (2026-10-25 defect #2 regression test)")
    good_maps = {"archived": {"block_rank_sum": ARCHIVED_MODULE_SUMS["archived"],
                              "allocation": ARCHIVED_ALLOCATIONS["archived"]},
                 "corrected": {"block_rank_sum": ARCHIVED_MODULE_SUMS["corrected"],
                               "allocation": ARCHIVED_ALLOCATIONS["corrected"]}}
    # Shape of the archive as --stage allocate leaves it: no top-level module_ranks, and an empty
    # allocation_stage.module_ranks (worst case). The pre-fix code recomputed all-zero sums here
    # and wrote a uniform [4,4,4,4]; the fixed code must keep the payload's correct maps.
    archive_no_ranks = {"allocation_stage": {"module_ranks": {}}}
    merged = merge_block_maps(archive_no_ranks, {"block_maps": dict(good_maps), "runs": []})
    c = merged["block_maps"]["corrected"]["allocation"]
    a = merged["block_maps"]["archived"]["allocation"]
    show("block_maps survive a --stage train rewrite (no zero-sum overwrite)",
         "corrected=%s" % [c[b] for b in BLOCKS], c == ARCHIVED_ALLOCATIONS["corrected"],
         "pre-fix code read run['module_ranks'] (absent here) -> all-zero sums -> [4,4,4,4]")
    show("archived block map also preserved", "archived=%s" % [a[b] for b in BLOCKS],
         a == ARCHIVED_ALLOCATIONS["archived"],
         "both maps are written back, not just the research-variable one")
    # Explicit top-level maps take precedence when present.
    merged2 = merge_block_maps({"archived": dict(good_maps["archived"], matches_archive=True),
                                "corrected": dict(good_maps["corrected"], matches_archive=True)},
                               {"block_maps": {}, "runs": []})
    show("explicit top-level maps take precedence",
         "corrected=%s" % [merged2["block_maps"]["corrected"]["allocation"][b] for b in BLOCKS],
         merged2["block_maps"]["corrected"]["allocation"] == ARCHIVED_ALLOCATIONS["corrected"],
         "a --stage allocate rewrite still wins over a stale payload copy")

    print("\n[E] inputs on this machine (read-only)")
    rc = verify_inputs()
    print("\n  assertion ledger: %d checks, %d failed"
          % (len(CHECKS), sum(1 for _, ok in CHECKS if not ok)))
    failed = [label for label, ok in CHECKS if not ok]
    for label in failed:
        print("    FAILED:", label)
    print("\n  nothing was executed and nothing was written")
    return 1 if failed else 0


# ------------------------------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="P3 task A: official IGU-LoRA allocator vs the "
                                             "block-level reimplementation")
    ap.add_argument("--plan", action="store_true", help="print the plan and verify the inputs "
                                                       "(default; writes nothing)")
    ap.add_argument("--self-test", action="store_true", help="offline checks of the statistics and "
                                                            "of the local inputs (writes nothing)")
    ap.add_argument("--run-official", action="store_true", help="INSTANCE ONLY: run the official "
                                                                "allocation stage and/or the arms")
    ap.add_argument("--stage", choices=("allocate", "train", "all"), default="all",
                    help="with --run-official: which stage to execute")
    ap.add_argument("--config", default=",".join(DEFAULT_CONFIGS),
                    help="with --stage train: comma-separated configs from %s" % sorted(CONFIGS))
    ap.add_argument("--seeds", default=",".join(str(s) for s in SEEDS_DEFAULT),
                    help="with --stage train: comma-separated seeds")
    ap.add_argument("--compare", action="store_true", help="compute the gap and write %s"
                                                           % rel(COMPARE_OUT))
    ap.add_argument("--official-config", default="auto",
                    choices=("auto", "official_corrected_map", "official_archived_map"),
                    help="which official run to compare (auto prefers the corrected block mapping)")
    ap.add_argument("--n-boot", type=int, default=N_BOOT, help="bootstrap replicates")
    ap.add_argument("--dry-run", action="store_true", help="print every command, execute nothing, "
                                                           "write nothing")
    ap.add_argument("--force", action="store_true", help="re-run arms whose archive already exists")
    ap.add_argument("--python", default=None, help="interpreter used for the training subprocess")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.run_official:
        return run_official(args)
    if args.compare:
        if args.official_config == "auto":
            args.official_config = None
        return compare(args)
    return plan()


if __name__ == "__main__":
    raise SystemExit(main())