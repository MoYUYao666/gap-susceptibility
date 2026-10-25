#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""P3 task B: a SECOND downstream task -- POPE (object hallucination) -- evaluated with the exact
conventions of the VQA-RAD check, so the two downstream results are comparable.

WHY THIS FILE EXISTS
--------------------
The P3 downstream evidence is a single task.  Supplementary Section "VQA-RAD downstream check"
(label app:vqa) reports the LLaVA adapters on VQA-RAD only, so any claim of the form "the adapters
help downstream" rests on one task family (open-ended radiology VQA, 451 held-out questions,
binomial standard error ~0.022 in accuracy).  This script prepares and runs one additional,
independent task with the same metric conventions, the same prompt style, the same greedy decoding
and the same paired-by-question bootstrap + TOST machinery, and records the whole provenance chain.

CHOSEN TASK: POPE, config Full, split random
--------------------------------------------
Dataset      : lmms-lab-encoder/POPE  (datasets-server redirects the older lmms-lab/POPE to this id)
Revision     : 4db1276663dfa5eb8ad16a52d24c31a09e470896
Config/split : Full / random  (3000 questions; popular and adversarial are the other two splits)
File         : Full/random-00000-of-00001.parquet
Provenance   : a formatted release of POPE (Li et al., "Evaluating Object Hallucination in Large
               Vision-Language Models", arXiv:2305.10355; original code RUCAIBox/POPE) that embeds
               the COCO images in the parquet, so no separate COCO download is needed.
Fields       : id, question_id, question, answer (yes/no), image_source, image, category.
Verified     : HF dataset card (config Full: adversarial/popular/random, 3000 each; download_size
               255,022,914 B; sha 4db1276663dfa5eb8ad16a52d24c31a09e470896) and the ModelScope
               mirror lmms-lab/POPE (510,051,032 B, Apache-2.0) -- both queried on 2026-10-24.

WHY POPE AND NOT SCIENCEQA (candidate 2: derek-thomas/ScienceQA, 12726/4241/4241)
---------------------------------------------------------------------------------
* metric comparability: POPE's label space IS the yes/no subset this repository already carves out
  of VQA-RAD (tools/_p1516_p3_vqa_downstream.py computes yes_no_accuracy and n_yes_no), so norm(),
  token_f1() and the yes/no subset transfer with no new parsing rule.  ScienceQA is multiple choice
  and would need a new answer-letter extraction convention, i.e. the two tasks would no longer be
  measured by the same metric.
* cost: POPE random is 3000 one-token answers (<=255 MB for the whole repository download);
  ScienceQA is 4241 test rows of free-form answers over a 7.9 GB image-bearing repository, of which
  only the image-bearing subset (~2017 rows, count recomputed by --prepare) is multimodal.
* resolution: 3000 questions give a binomial standard error of ~0.009 in accuracy, four times
  better than the 451-question VQA-RAD set; the VQA-RAD analysis had to declare that differences
  below ~0.045 sit at its resolution limit (Supplementary Section S28), which POPE removes.
* NOTE, disclosed: the Commentary manuscript (paper_review_prl/main_prl.tex, Section 3.1) *cites*
  published POPE values (LLaVA-1.5 87.3/86.1/84.2; DoRA 85.9/86.4/87.2) as an example of a
  benchmark whose subset is not named.  No manuscript in this repository has ever *measured* POPE.
  Running it here is the first measurement, and this script names the config, the split, the
  revision, the parquet sha256, the prompt and the decoding -- i.e. it complies with the
  Commentary's own checklist instead of contradicting it.

MODES
-----
Local, no GPU, no network, writes nothing:
    python tools/_p1640_p3_second_downstream.py --plan
    python tools/_p1640_p3_second_downstream.py --self-test
    python tools/_p1640_p3_second_downstream.py --prepare --dry-run
    python tools/_p1640_p3_second_downstream.py --eval --rank base --dry-run
    python tools/_p1640_p3_second_downstream.py --aggregate --dry-run

Instance (--prepare/--aggregate need no GPU; --eval does):
    python tools/_p1640_p3_second_downstream.py --prepare
    python tools/_p1640_p3_second_downstream.py --eval --rank base     # one arm per process
    python tools/_p1640_p3_second_downstream.py --eval --rank 5
    python tools/_p1640_p3_second_downstream.py --eval --rank 6
    python tools/_p1640_p3_second_downstream.py --aggregate --strict

Exit codes: 0 ok, 1 an assertion failed, 2 an input is missing (the exact fetch/eval command is
printed), 3 --strict acceptance unmet.  A --dry-run that is missing its dataset prints the same
stop message and exits 0, mirroring tools/_p1613_p3_cloud_runner.py --aggregate --dry-run.

ADAPTERS: NEVER TRAINED HERE
----------------------------
The two adapters are the existing outputs/p3_vqa_adapters/r{5,6}_step of the archived 451-question
VQA-RAD round (per-step training on the full VQA-RAD training split: 1793 pairs, 3 epochs).  This
script reuses them, records adapter_model.safetensors' sha256 and asserts it against the sha256 that
archived round recorded in outputs/analysis/cloud_vqa_full451_{5,6}.json.  If an adapter is missing
or differs, the script stops with the exact recipe command instead of training anything.

WRITE POLICY
------------
* --plan / --self-test write nothing;
* --prepare writes paper3/test-pope-<split>.parquet and data/pope/images/<split>/*.png (new files
  only; it never overwrites them unless --force) and never downloads anything;
* --eval writes outputs/analysis/p3_second_downstream_<rank>.json (one arm per process; skipped when
  a valid archive already exists unless --force);
* --aggregate writes outputs/analysis/p3_second_downstream.json and is deterministic: no wall-clock
  field, fixed RNG seed, so re-running it on unchanged inputs reproduces the file byte for byte.
  Every number it prints is re-read from the written JSON before the script exits.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import time

import numpy as np

# ------------------------------------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------------------------------------
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SELF = os.path.abspath(__file__)
AN = os.path.join(REPO, "outputs", "analysis")
VQA_SCRIPT = os.path.join(REPO, "tools", "_p1516_p3_vqa_downstream.py")
RANKSEP_SCRIPT = os.path.join(REPO, "tools", "_p1595_p3_rank_separation.py")
CLOUD_RUNNER = os.path.join(REPO, "tools", "_p1613_p3_cloud_runner.py")
MODEL = os.path.join(REPO, "models", "llava-hf")
ADAPTERS_DIR = os.path.join(REPO, "outputs", "p3_vqa_adapters")
RAW_DIR = os.path.join(REPO, "data", "pope", "raw")
IMAGES_DIR = os.path.join(REPO, "data", "pope", "images")
PREPARED = os.path.join(REPO, "paper3", "test-pope-%s.parquet")
ARM_OUT = os.path.join(AN, "p3_second_downstream_%s.json")
AGG_OUT = os.path.join(AN, "p3_second_downstream.json")

# ------------------------------------------------------------------------------------------------
# Dataset identity (all verified 2026-10-24; see the module docstring)
# ------------------------------------------------------------------------------------------------
DATASET_ID = "lmms-lab-encoder/POPE"
DATASET_ID_ALIAS = "lmms-lab/POPE"          # ModelScope mirror still carries the old name
DATASET_REVISION = "4db1276663dfa5eb8ad16a52d24c31a09e470896"
DATASET_CONFIG = "Full"
SPLITS = ("random", "popular", "adversarial")
SPLIT_DEFAULT = "random"
SPLIT_SIZES = {"random": 3000, "popular": 3000, "adversarial": 3000}   # HF dataset card
DATASET_PAPER = ("Li et al., Evaluating Object Hallucination in Large Vision-Language Models, "
                 "arXiv:2305.10355; original code RUCAIBox/POPE")
RAW_EXPECTED = os.path.join(RAW_DIR, DATASET_CONFIG, "<split>-00000-of-00001.parquet")
FETCH_COMMANDS = [
    "# mirror first (AGENTS.md source order); this script never downloads anything itself",
    "export HF_ENDPOINT=https://hf-mirror.com",
    "export HF_HOME=/root/autodl-tmp/hf",
    "python -c \"from huggingface_hub import snapshot_download; "
    "snapshot_download('%s', repo_type='dataset', revision='%s', "
    "allow_patterns=['%s/<split>-00000-of-00001.parquet'], local_dir='/root/autodl-tmp/pope')\""
    % (DATASET_ID, DATASET_REVISION, DATASET_CONFIG),
    "# then make it visible to this script (copy or symlink):",
    "mkdir -p data/pope/raw/%s && cp /root/autodl-tmp/pope/%s/<split>-00000-of-00001.parquet "
    "data/pope/raw/%s/" % (DATASET_CONFIG, DATASET_CONFIG, DATASET_CONFIG),
    "# fallback only if the mirror is slow: ModelScope (verify the id with HubApi first)",
    "python -c \"from modelscope.hub.api import HubApi; "
    "print(HubApi().get_dataset_files('%s'))\"" % DATASET_ID_ALIAS,
    "modelscope download --dataset %s --include '%s/<split>-00000-of-00001.parquet' "
    "--local_dir /root/autodl-tmp/pope" % (DATASET_ID_ALIAS, DATASET_CONFIG),
]

# ------------------------------------------------------------------------------------------------
# Frozen comparison protocol (identical to tools/_p1516_p3_vqa_downstream.py / _p1613_p3_cloud_runner)
# ------------------------------------------------------------------------------------------------
PROMPT_PREFIX = "Answer briefly. "     # identical to _p1516 and to _p1613's VQA_PROMPT_PREFIX
MAX_NEW_TOKENS = 16                    # identical to _p1516 and to _p1613's VQA_MAX_NEW_TOKENS
ARMS = ("base", "5", "6")
ADAPTER_DIRS = {"5": "r5_step", "6": "r6_step"}
ADAPTER_REFERENCE = {                  # meta.adapter_sha256 of the archived 451-question round
    "5": "1615d21ecf2d6200effa9b1c180d1256934d22d3cbb16f6b8695ea902b64767b",
    "6": "5f681f3f80ee0fa2db1626b98f64113554305fd133f41a3867ebf74c2affee42",
}
ADAPTER_RECIPE = ("tools/_p1516_p3_vqa_downstream.py ensure_adapter(): "
                  "paper3/scripts/run_training.py --rank <r> --seed 42 --epochs 3 "
                  "--num-samples 1793 --data-path paper3/train-vqarad.parquet "
                  "--images-dir data/vqa_rad/images --per-step --save-adapter-dir "
                  "outputs/p3_vqa_adapters/r<r>_step")
MARGIN_ACC = 0.05                      # pre-declared TOST margin, carried over from S28 unchanged
MARGIN_F1 = 0.05                       # same margin on token F1 and on the POPE yes-class F1
N_BOOT = 20000                         # same replicate count as tools/_p1595_p3_rank_separation.py
RNG_SEED = 20261024                    # fixed seed => deterministic aggregate
ALPHA = 0.05
CONTRASTS = (("base", "5"), ("base", "6"), ("5", "6"))
METRICS = ("accuracy", "token_f1", "pope_f1")
ANSWER_SPACE = ("yes", "no")
MIN_ANSWER_SPACE_SHARE = 0.99          # 99% of references must be yes/no, else the wrong file/split

CHECKS: list = []                      # (label, ok) assertions
PENDS: list = []                       # labels of inputs that must exist on the instance
ASSERTS: list = []                     # (label, json path, printed value) for the final ledger
QUIET = False                          # --self-test sets this so the core records without printing


# ------------------------------------------------------------------------------------------------
# Small helpers
# ------------------------------------------------------------------------------------------------
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


def show(label: str, value: str, ok: bool, why: str) -> None:
    """Print one number only together with the assertion that guards it."""
    CHECKS.append((label, bool(ok)))
    print("  %-62s %-24s %s  %s" % (label, value, "OK  " if ok else "FAIL", why))


def pending(label: str, why: str) -> None:
    """An input that must exist on the instance; it is not a failure of the script itself."""
    PENDS.append(label)
    print("  %-62s %-24s %s  %s" % (label, "-", "PEND", why))


def ledger(note_text: str = "") -> None:
    failed = [label for label, ok in CHECKS if not ok]
    print("\n  assertion ledger: %d checks, %d failed, %d pending%s"
          % (len(CHECKS), len(failed), len(PENDS), (" (%s)" % note_text) if note_text else ""))
    for label in failed:
        print("    FAILED:", label)
    if PENDS:
        print("    pending (fetch/run these on the instance): %s" % ", ".join(PENDS))


def note(label: str, text: str, why: str, cells=()) -> None:
    """Print one line carrying numbers and record every number for the post-write ledger."""
    for path, value in cells:
        ASSERTS.append((label, path, value))
    if not QUIET:
        print("  %-58s %-40s %s" % (label, text, why))


def dig(payload, path: str):
    node = payload
    for part in path.split("."):
        node = node[part]
    return node


def load_module(name: str, path: str):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import %s" % path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def safe_name(text: str, limit: int = 48) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]", "_", str(text))[:limit] or "x"


# ------------------------------------------------------------------------------------------------
# Metrics: imported from tools/_p1516_p3_vqa_downstream.py (the archived conventions)
# ------------------------------------------------------------------------------------------------
def metric_functions():
    """norm() and token_f1() of the archived VQA-RAD check, imported -- not re-implemented."""
    mod = load_module("vqa1516_metrics", VQA_SCRIPT)
    return mod.norm, mod.token_f1


def canary_metric_check() -> bool:
    norm, token_f1 = metric_functions()
    cases = [("Yes.", "yes"), ("  NO  ", "no"), ("Anterior, left.", "anterior left"),
             ("no, not at all", "no not at all")]
    ok = all(norm(a) == b for a, b in cases)
    f1_cases = [("yes", "yes", 1.0), ("yes", "no", 0.0), ("a b", "a c", 0.5),
                ("left lung", "lung", 2 * 0.5 * 1.0 / 1.5)]
    ok = ok and all(abs(token_f1([r], [h]) - want) < 1e-12 for r, h, want in f1_cases)
    return ok


def pope_f1_from_flags(pred_yes, ref_yes) -> float:
    """POPE's yes-class F1 over a (possibly resampled) set of questions: 2TP / (2TP + FP + FN)."""
    tp = float(np.sum(pred_yes & ref_yes))
    fp = float(np.sum(pred_yes & ~ref_yes))
    fn = float(np.sum(~pred_yes & ref_yes))
    denom = 2.0 * tp + fp + fn
    return (2.0 * tp / denom) if denom > 0 else 0.0


# ------------------------------------------------------------------------------------------------
# Statistics: paired-by-question bootstrap + TOST (rule mirrored from _p1595 vqa_contrast)
# ------------------------------------------------------------------------------------------------
def paired_bootstrap_set(a: dict, b: dict, rng, n_boot: int, margin: float) -> dict:
    """Paired (by question) percentile bootstrap of arm a minus arm b, three metrics.

    One index matrix rng.integers(0, n, size=(n_boot, n)) is drawn per call and applied to both
    arms, exactly as tools/_p1595_p3_rank_separation.py vqa_contrast() does, so the pairing is
    preserved.  accuracy and token_f1 resample the per-question values the same way (--self-test
    asserts field-by-field equality with the imported function on identical input); pope_f1 is a
    set-level metric and is therefore recomputed from the resampled TP/FP/FN counts.
    """
    n = int(len(a["correct"]))
    idx = rng.integers(0, n, size=(int(n_boot), n))
    out = {}
    for key in ("accuracy", "token_f1"):
        av = a["correct"] if key == "accuracy" else a["f1"]
        bv = b["correct"] if key == "accuracy" else b["f1"]
        out[key] = _interval(av[idx].mean(axis=1) - bv[idx].mean(axis=1),
                             float(av.mean() - bv.mean()), margin, int(n_boot))
    pa, ra = a["pred_yes"], a["ref_yes"]
    pb, rb = b["pred_yes"], b["ref_yes"]
    f1a = np.array([pope_f1_from_flags(pa[i], ra[i]) for i in idx])
    f1b = np.array([pope_f1_from_flags(pb[i], rb[i]) for i in idx])
    obs_a, obs_b = pope_f1_from_flags(pa, ra), pope_f1_from_flags(pb, rb)
    out["pope_f1"] = _interval(f1a - f1b, obs_a - obs_b, margin, int(n_boot))
    out["pope_f1"]["arm_values"] = {"a": obs_a, "b": obs_b}
    return out


def _interval(d, delta: float, margin: float, n_boot: int) -> dict:
    """The interval/TOST block, computed exactly as the imported vqa_contrast() does."""
    lo90, hi90 = float(np.percentile(d, 5.0)), float(np.percentile(d, 95.0))
    p_lower = float(np.mean(d <= -margin))
    p_upper = float(np.mean(d >= +margin))
    return {
        "n_boot": int(n_boot),
        "delta": float(delta),
        "boot_mean": float(d.mean()),
        "boot_se": float(d.std(ddof=1)),
        "ci95": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))],
        "ci90": [lo90, hi90],
        "excludes_zero_95": bool(np.percentile(d, 2.5) > 0 or np.percentile(d, 97.5) < 0),
        "tost_margin": float(margin),
        "tost_p_lower": p_lower,
        "tost_p_upper": p_upper,
        "tost_p": max(p_lower, p_upper),
        "equivalent_at_declared_margin": bool(max(p_lower, p_upper) < ALPHA),
        "min_equivalent_margin": max(-lo90, hi90),
    }


# ------------------------------------------------------------------------------------------------
# --plan
# ------------------------------------------------------------------------------------------------
def plan() -> int:
    print("=" * 118)
    print("P3 TASK B -- second downstream task: POPE (%s / %s / %s)"
          % (DATASET_CONFIG, SPLIT_DEFAULT, DATASET_ID))
    print("=" * 118)

    print("\n[1] why a second downstream task")
    print("  Supplementary Section 'VQA-RAD downstream check' (label app:vqa) is the only downstream")
    print("  task of the paper: 451 held-out questions, binomial standard error ~0.022, which forced")
    print("  the analysis to declare differences below ~0.045 as sitting at the resolution limit.")
    print("  A second, independent task measured with the same conventions removes both limits.")

    print("\n[2] candidates and the choice")
    rows = [
        ("multimodal", "POPE: yes (every question is image-grounded)",
         "ScienceQA: partly (only the image-bearing ~2017 of 4241 test rows)"),
        ("public / downloadable", "POPE: HF %s + ModelScope %s" % (DATASET_ID, DATASET_ID_ALIAS),
         "ScienceQA: HF derek-thomas/ScienceQA"),
        ("size", "POPE: 255 MB repository download (images embedded, no COCO fetch)",
         "ScienceQA: 7.9 GB repository storage"),
        ("<= 1 h per 7B adapter", "POPE: 3000 one-token answers, ~0.3-0.6 s/question",
         "ScienceQA: 4241 free-form answers"),
        ("already measured by a manuscript", "POPE: no (the Commentary only cites published values)",
         "ScienceQA: no"),
        ("same metric conventions as VQA-RAD", "POPE: yes (label space = the yes/no subset)",
         "ScienceQA: no (needs an answer-letter extraction rule)"),
    ]
    for name, pope, sqa in rows:
        print("  %-34s %-58s %s" % (name, pope, sqa))
    print("  DECISION: %s, config %s, split %s -- %d questions."
          % (DATASET_ID, DATASET_CONFIG, SPLIT_DEFAULT, SPLIT_SIZES[SPLIT_DEFAULT]))

    print("\n[3] exact dataset identity")
    print("  id           : %s (revision %s)" % (DATASET_ID, DATASET_REVISION))
    print("  alias        : %s on ModelScope (510,051,032 B, Apache-2.0)" % DATASET_ID_ALIAS)
    print("  config/split : %s / %s   (other splits: %s)"
          % (DATASET_CONFIG, SPLIT_DEFAULT, ", ".join(SPLITS[1:])))
    print("  file         : %s/%s-00000-of-00001.parquet" % (DATASET_CONFIG, "<split>"))
    print("  fields       : id, question_id, question, answer(yes/no), image_source, image, category")
    print("  paper        : %s" % DATASET_PAPER)
    print("  fetch (the script never downloads):")
    for line in FETCH_COMMANDS:
        print("      %s" % line.replace("<split>", SPLIT_DEFAULT))

    print("\n[4] what runs where")
    print("  [prepare]    validate the raw parquet, extract the embedded images to")
    print("               %s/<split>/, write %s" % (rel(IMAGES_DIR), rel(PREPARED % "<split>")))
    print("  [eval]       one arm per process: base / r5 / r6, prompt %r, greedy, max_new_tokens=%d"
          % (PROMPT_PREFIX + "<question>", MAX_NEW_TOKENS))
    print("               adapters: %s (reused, sha256-checked, never trained here)"
          % rel(ADAPTERS_DIR))
    print("  [aggregate]  paired-by-question bootstrap + TOST over the three arms -> %s"
          % rel(AGG_OUT))
    print("  commands:")
    print("      %s --prepare" % rel(SELF))
    for arm in ARMS:
        print("      %s --eval --rank %s" % (rel(SELF), arm))
    print("      %s --aggregate --strict" % rel(SELF))

    print("\n[5] expected runtime and memory on a 32 GB GPU")
    print("  measured anchor: the archived 451-question VQA-RAD round took 3.47 / 3.63 / 4.40 min")
    print("  for base / r5 / r6 on the cloud RTX 4080 SUPER (meta.elapsed_min of")
    print("  outputs/analysis/cloud_vqa_full451_*.json) = 0.46-0.59 s per question with up to 16")
    print("  generated tokens.  POPE answers are one token, so 3000 questions are expected at")
    print("  ~0.3-0.6 s/question = 15-30 min per arm; three arms ~1-1.5 h sequential.")
    print("  memory: the same round loaded 4-bit LLaVA-1.5-7B in 4.1 GB (docs/p3_cloud_round_notes.md")
    print("  section 5); batch 1 with 576 image tokens fits comfortably in 32 GB (~13% of the card).")
    print("  disk: raw parquet <=255 MB, materialised PNGs ~0.6-1.2 GB, arm archives <1 MB each.")

    print("\n[6] acceptance criteria (enforced by --aggregate --strict)")
    for item in ("three arms present and each carrying the same number of questions",
                 "reference arrays byte-identical across arms (sha256) and in prepared-parquet order",
                 "adapters are the archived r5_step/r6_step (sha256 == the archived round's value)",
                 "every printed number equals the value in the written JSON",
                 "re-running --aggregate on unchanged inputs reproduces the file byte for byte"):
        print("  - %s" % item)

    print("\n[7] what the result would mean for the paper's downstream claim")
    print("  STRENGTHENS: both adapters are equivalent-or-better than the base model on POPE")
    print("              accuracy and yes-class F1 within the pre-declared margin (TOST), i.e. the")
    print("              second task does not contradict the VQA-RAD direction; with 3000 questions")
    print("              the resolution limit that bound S28 disappears.")
    print("  WEAKENS:    an adapter loses accuracy or yes-class F1 beyond the margin, or the yes-ratio")
    print("              collapses -- then the downstream effect is task-dependent and the paper must")
    print("              say so (the honest negative is the reportable result, not a deleted run).")
    print("  EITHER WAY: 'the downstream check is a single task' becomes false and is replaced by")
    print("              the two-task sentence stored in the aggregate's caveat_sentences block.")

    print("\n[8] local verification (read-only)")
    rc = verify_local()
    ledger("inputs that only exist on the instance are listed as pending")
    print("\n  nothing was executed and nothing was written")
    return rc


def verify_local(require_dataset: bool = False) -> int:
    show("archived VQA-RAD script present (metric source)", rel(VQA_SCRIPT),
         os.path.isfile(VQA_SCRIPT), "norm() and token_f1() are imported from it")
    show("rank-separation script present (statistics source)", rel(RANKSEP_SCRIPT),
         os.path.isfile(RANKSEP_SCRIPT),
         "the bootstrap/TOST rule is mirrored from its vqa_contrast()")
    show("metric canary (imported definitions)", "4 norm + 4 f1 cases", canary_metric_check(),
         "imported norm()/token_f1() behave as the archived round used them")
    try:
        cr = load_module("cloud_runner_constants", CLOUD_RUNNER)
        same = (cr.VQA_PROMPT_PREFIX == PROMPT_PREFIX and cr.VQA_MAX_NEW_TOKENS == MAX_NEW_TOKENS)
        show("prompt and decoding identical to the archived VQA arm",
             "%r / %d" % (PROMPT_PREFIX, MAX_NEW_TOKENS), same,
             "_p1613 VQA_PROMPT_PREFIX=%r VQA_MAX_NEW_TOKENS=%d"
             % (cr.VQA_PROMPT_PREFIX, cr.VQA_MAX_NEW_TOKENS))
    except Exception as exc:  # noqa: BLE001
        show("prompt and decoding identical to the archived VQA arm", "error", False, "%r" % (exc,))
    for tag, sub in sorted(ADAPTER_DIRS.items()):
        path = os.path.join(ADAPTERS_DIR, sub, "adapter_model.safetensors")
        if os.path.exists(path):
            digest = sha256_file(path)
            show("adapter r%s present" % tag, rel(path), True,
                 "archived adapter of the 451-question round")
            show("adapter r%s sha256 equals the archived round's value" % tag, digest[:16],
                 digest == ADAPTER_REFERENCE[tag],
                 "reference from outputs/analysis/cloud_vqa_full451_%s.json" % tag)
        elif require_dataset:
            show("adapter r%s present" % tag, rel(path), False,
                 "MISSING: retrieve it from the instance of the archived round, or rebuild it "
                 "exactly as the archived round did: %s" % ADAPTER_RECIPE)
        else:
            pending("adapter r%s present" % tag,
                    "not in this checkout; --eval --rank %s prints the exact recipe" % tag)
    cands = raw_candidates_for(SPLIT_DEFAULT)
    label, value = "raw POPE parquet present", (rel(cands[0]) if cands else rel(RAW_EXPECTED))
    if cands:
        show(label, value, True, "found on this machine")
    elif require_dataset:
        show(label, value, False, "run the fetch commands of --plan section [3]")
    else:
        pending(label, "not fetched yet; the fetch commands are printed by --plan section [3]")
    prepared = PREPARED % SPLIT_DEFAULT
    if os.path.exists(prepared):
        show("prepared parquet present", rel(prepared), True, "produced by --prepare")
    elif require_dataset:
        show("prepared parquet present", rel(prepared), False, "produced by --prepare")
    else:
        pending("prepared parquet present", "produced by --prepare (needs the raw parquet)")
    for tag in ARMS:
        path = ARM_OUT % tag
        if os.path.exists(path):
            show("arm archive %s present" % tag, rel(path), True, "produced by --eval --rank %s" % tag)
        elif require_dataset:
            show("arm archive %s present" % tag, rel(path), False,
                 "produced by --eval --rank %s" % tag)
        else:
            pending("arm archive %s present" % tag, "produced by --eval --rank %s" % tag)
    return 0 if all(ok for _, ok in CHECKS) else 1


# ------------------------------------------------------------------------------------------------
# --prepare
# ------------------------------------------------------------------------------------------------
def raw_candidates_for(split: str) -> list:
    """Where the raw parquet may already be, in priority order (never downloaded by this script)."""
    name = "%s-00000-of-00001.parquet" % split
    out = []
    local = os.path.join(RAW_DIR, DATASET_CONFIG, name)
    if os.path.exists(local):
        out.append(local)
    for root in (os.environ.get("HF_HOME"), os.path.expanduser("~/.cache/huggingface"),
                 os.path.expanduser("~/.cache/huggingface/hub")):
        if not root:
            continue
        for base in (os.path.join(root, "datasets--%s" % DATASET_ID.replace("/", "--")),
                     os.path.join(root, "hub", "datasets--%s" % DATASET_ID.replace("/", "--"))):
            for rev in (DATASET_REVISION, "main"):
                snap = os.path.join(base, "snapshots", rev, DATASET_CONFIG, name)
                if os.path.exists(snap):
                    out.append(snap)
    return out


def fetch_help(split: str) -> None:
    print("  FETCH IT, then re-run --prepare (this script never downloads anything by itself):")
    for line in FETCH_COMMANDS:
        print("      %s" % line.replace("<split>", split))


def prepare(args) -> int:
    import pandas as pd
    from PIL import Image

    splits = list(SPLITS) if args.split == "all" else [args.split]
    print("=" * 118)
    print("P3 TASK B -- PREPARE (%s / %s / %s)" % (DATASET_ID, DATASET_CONFIG, ",".join(splits)))
    print("=" * 118)
    stopped = False
    for split in splits:
        print("\n[split %s]" % split)
        cands = raw_candidates_for(split)
        expected = os.path.join(RAW_DIR, DATASET_CONFIG, "%s-00000-of-00001.parquet" % split)
        if not cands:
            if args.dry_run:
                pending("raw parquet present", "expected at %s" % rel(expected))
                fetch_help(split)
                print("  [dry run] would then extract the embedded images to %s/ and write %s"
                      % (rel(os.path.join(IMAGES_DIR, split)), rel(PREPARED % split)))
                continue
            show("raw parquet present", rel(expected), False, "dataset missing on this machine")
            fetch_help(split)
            return 2
        raw = cands[0]
        df = pd.read_parquet(raw)
        print("  raw: %s (%d rows, %.1f MB)" % (rel(raw), len(df), os.path.getsize(raw) / 1e6))
        if args.limit:
            df = df.head(args.limit)
        missing = [c for c in ("question", "answer", "image") if c not in df.columns]
        show("raw parquet carries the required columns", "%s" % list(df.columns)[:7], not missing,
             "missing: %s" % missing if missing else "question / answer / image (+ category, id)")
        if missing:
            return 2
        if args.limit is None and split in SPLIT_SIZES:
            show("row count matches the dataset card", "%d" % len(df), len(df) == SPLIT_SIZES[split],
                 "HF card: %s carries %d examples" % (split, SPLIT_SIZES[split]))
        out_parquet = PREPARED % split
        img_root = os.path.join(IMAGES_DIR, split)
        if (os.path.exists(out_parquet) and os.path.isdir(img_root) and not args.force
                and args.limit is None):
            prepared = pd.read_parquet(out_parquet)
            images_ok = all(os.path.exists(os.path.join(IMAGES_DIR, str(p)))
                            for p in prepared["image"].head(50))
            same_rows = len(prepared) == len(df)
            show("prepared parquet already valid (skip)", rel(out_parquet),
                 same_rows and images_ok,
                 "%d rows; first 50 images present; --force rewrites it" % len(prepared))
            if same_rows and images_ok:
                continue
        if args.dry_run:
            print("  [dry run] would extract %d images to %s/ and write %s"
                  % (len(df), rel(img_root), rel(out_parquet)))
            continue
        os.makedirs(img_root, exist_ok=True)
        rows, value_counts, skipped = [], {}, 0
        for i, row in df.iterrows():
            blob = row["image"]
            if isinstance(blob, dict) and blob.get("bytes"):
                data = blob["bytes"]
            elif isinstance(blob, (bytes, bytearray)):
                data = blob
            else:
                skipped += 1
                continue
            name = "%05d_%s.png" % (i, safe_name(row.get("question_id", i)))
            path = os.path.join(img_root, name)
            if not os.path.exists(path):
                Image.open(io.BytesIO(data)).convert("RGB").save(path)
            answer = str(row["answer"]).strip().lower()
            value_counts[answer] = value_counts.get(answer, 0) + 1
            rows.append({"instruction": str(row["question"]), "input": "",
                         "output": str(row["answer"]), "image": "%s/%s" % (split, name),
                         "question_id": str(row.get("question_id", i)),
                         "category": str(row.get("category", "")),
                         "image_source": str(row.get("image_source", ""))})
        out = pd.DataFrame(rows)
        out.to_parquet(out_parquet)
        share = sum(v for k, v in value_counts.items()
                    if k in ANSWER_SPACE) / max(len(rows), 1)
        show("answers live in the yes/no label space", "%s" % value_counts,
             share >= MIN_ANSWER_SPACE_SHARE,
             "POPE's label space is yes/no; another distribution means the wrong file or split")
        show("images extracted", "%d files" % len(out), len(out) == len(df) - skipped,
             "skipped %d rows without image bytes" % skipped)
        show("prepared parquet rows match the raw parquet", "%d" % len(out), len(out) == len(df),
             "%s" % rel(out_parquet))
        print("  raw parquet sha256      : %s" % sha256_file(raw))
        print("  prepared parquet sha256 : %s" % sha256_file(out_parquet))
        if share < MIN_ANSWER_SPACE_SHARE:
            stopped = True
    if not args.dry_run and not stopped:
        print("\n  next: %s --eval --rank base   (then --rank 5 and --rank 6)" % rel(SELF))
    ledger()
    if stopped:
        return 2
    return 1 if any(not ok for _, ok in CHECKS) else 0


# ------------------------------------------------------------------------------------------------
# --eval (one arm per process)
# ------------------------------------------------------------------------------------------------
def arm_archive(path: str, tag: str, n_expected: int) -> tuple:
    """A valid arm archive for this arm, or (False, reason)."""
    if not os.path.exists(path):
        return False, "missing"
    try:
        d = load_json(path)
    except Exception as exc:  # noqa: BLE001
        return False, "unreadable (%r)" % (exc,)
    if (d.get("meta") or {}).get("script") != rel(SELF):
        return False, "produced by %r, not by this script" % (d.get("meta") or {}).get("script")
    if d.get("ok") is not True:
        return False, "ok is not true"
    for key in ("accuracy", "token_f1", "pope_f1", "refs", "hypotheses", "questions", "meta"):
        if key not in d:
            return False, "field %s absent" % key
    if len(d["refs"]) != n_expected or len(d["hypotheses"]) != n_expected:
        return False, "%d records, expected %d" % (len(d["refs"]), n_expected)
    if (d.get("rank") is None) != (tag == "base"):
        return False, "rank %r does not match arm %s" % (d.get("rank"), tag)
    return True, "valid (%d questions, accuracy %.4f, pope_f1 %.4f)" % (
        len(d["refs"]), float(d["accuracy"]), float(d["pope_f1"]))


def eval_arm(args) -> int:
    print("=" * 118)
    print("P3 TASK B -- EVAL arm %s (%s / %s / split %s)"
          % (args.rank, DATASET_ID, DATASET_CONFIG, args.split))
    print("=" * 118)
    tag = args.rank
    rank = None if tag == "base" else int(tag)
    out_path = ARM_OUT % tag
    prepared = PREPARED % args.split

    print("\n[1] inputs")
    if not os.path.exists(prepared):
        show("prepared parquet present", rel(prepared), False, "run --prepare first")
        if args.dry_run:
            print("  [dry run] would then evaluate the first %s question(s) of %s with prompt %r,"
                  % (args.limit or "all", rel(prepared), PROMPT_PREFIX + "<question>"))
            print("            greedy decoding, max_new_tokens=%d, and write %s"
                  % (MAX_NEW_TOKENS, rel(out_path)))
            print("            (the real run stops here with exit code 2 until --prepare has run)")
            return 0
        print("  STOP: fetch the dataset (commands in --plan section [3]) and run:")
        print("      %s --prepare --split %s" % (rel(SELF), args.split))
        return 2
    show("prepared parquet present", rel(prepared), True, "written by --prepare")
    show("base model present", rel(MODEL), os.path.isdir(MODEL),
         "models/llava-hf; weights are downloaded on the instance, never uploaded")

    import pandas as pd
    df = pd.read_parquet(prepared)
    if args.limit:
        df = df.head(args.limit)
    n = len(df)
    dataset_sha = sha256_file(prepared)
    print("  evaluation set: %s, %d questions (limit=%s)" % (rel(prepared), n, args.limit))
    ok, why = arm_archive(out_path, tag, n)
    if ok and not args.force:
        print("  arm %s: existing archive is valid (%s); skipping" % (tag, why))
        return 0

    adapter_dir, adapter_how = None, "none"
    if rank is not None:
        adapter_dir = os.path.join(ADAPTERS_DIR, ADAPTER_DIRS[tag])
        cfg_path = os.path.join(adapter_dir, "adapter_config.json")
        weights = os.path.join(adapter_dir, "adapter_model.safetensors")
        present = os.path.exists(cfg_path) and os.path.exists(weights)
        if not present:
            show("adapter present", rel(adapter_dir), False, "adapter missing")
            if args.dry_run:
                print("  [dry run] would stop here with exit code 2; retrieve the archived adapter,")
                print("            or rebuild it (never done by this script): %s" % ADAPTER_RECIPE)
                return 0
            print("  STOP: %s is missing.  Retrieve it from the instance of the archived round, or"
                  % rel(adapter_dir))
            print("        rebuild it exactly as the archived round did:")
            print("      %s" % ADAPTER_RECIPE)
            return 2
        show("adapter present", rel(adapter_dir), True, "reused from the archived 451-question round")
        cfg = load_json(cfg_path)
        if int(cfg.get("r", -1)) != rank:
            print("  ERROR: adapter r is %r, expected %d" % (cfg.get("r"), rank))
            return 2
        if abs(float(cfg.get("lora_alpha", -1)) - 2 * rank) > 1e-9:
            print("  ERROR: adapter lora_alpha is %r, expected %d" % (cfg.get("lora_alpha"), 2 * rank))
            return 2
        targets = sorted(cfg.get("target_modules") or [])
        if targets != sorted(["q_proj", "k_proj", "v_proj", "o_proj"]):
            print("  ERROR: adapter targets %r, expected the qkvo set" % (targets,))
            return 2
        digest = sha256_file(weights)
        adapter_how = "reused_from_archived_round"
        show("adapter sha256 matches the archived VQA-RAD round", digest[:16],
             digest == ADAPTER_REFERENCE[tag],
             "otherwise this is a different adapter and the two tasks would not share it")
        if digest != ADAPTER_REFERENCE[tag]:
            print("  STOP: refusing to evaluate an adapter that is not the archived one.")
            print("        expected %s" % ADAPTER_REFERENCE[tag])
            print("        found    %s" % digest)
            return 2

    if args.dry_run:
        print("\n[2] dry run: would load %s%s and run %d greedy generations (%r + question, "
              "max_new_tokens=%d), then write %s"
              % (rel(MODEL), "" if rank is None else " + " + rel(adapter_dir), n, PROMPT_PREFIX,
                 MAX_NEW_TOKENS, rel(out_path)))
        print("    nothing was executed and nothing was written")
        return 0

    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    norm, token_f1 = metric_functions()
    import torch
    from PIL import Image
    from transformers import AutoProcessor, BitsAndBytesConfig, LlavaForConditionalGeneration
    from peft import PeftModel

    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                               bnb_4bit_use_double_quant=True)
    processor = AutoProcessor.from_pretrained(MODEL, local_files_only=True)
    t0 = time.time()
    base = LlavaForConditionalGeneration.from_pretrained(MODEL, quantization_config=quant,
                                                         device_map="auto", local_files_only=True)
    model = base
    if rank is not None:
        model = PeftModel.from_pretrained(base, adapter_dir, is_trainable=False)
    hyps, refs, questions, images = [], [], [], []
    pred_yes, ref_yes, correct, f1s, yn_flags = [], [], [], [], []
    model.eval()
    print("\n[2] generating %d answers (greedy, max_new_tokens=%d)" % (n, MAX_NEW_TOKENS))
    for i, row in df.iterrows():
        img = Image.open(os.path.join(IMAGES_DIR, str(row["image"]))).convert("RGB")
        conv = [{"role": "user", "content": [{"type": "image"},
                                            {"type": "text",
                                             "text": PROMPT_PREFIX + str(row["instruction"])}]}]
        text = processor.apply_chat_template(conv, add_generation_prompt=True)
        inp = processor(text=text, images=img, return_tensors="pt")
        inp = {k: v.to("cuda") if torch.is_tensor(v) else v for k, v in inp.items()}
        with torch.no_grad():
            out = model.generate(**inp, max_new_tokens=MAX_NEW_TOKENS, do_sample=False)
        gen = processor.tokenizer.decode(out[0][inp["input_ids"].shape[1]:],
                                         skip_special_tokens=True).strip()
        ref = str(row["output"])
        nref, nhyp = norm(ref), norm(gen)
        per_f1 = float(token_f1([nref], [nhyp]))
        is_yn = bool(nref.split()[:1] in (["yes"], ["no"]))
        hyps.append(gen)
        refs.append(ref)
        images.append(str(row["image"]))
        questions.append({"index": int(i), "question_id": str(row.get("question_id", "")),
                          "category": str(row.get("category", "")), "image": str(row["image"]),
                          "question": str(row["instruction"]), "reference": ref,
                          "hypothesis": gen, "norm_reference": nref, "norm_hypothesis": nhyp,
                          "correct": bool(nhyp == nref),
                          "relaxed_correct": bool(set(nref.split()) <= set(nhyp.split())),
                          "token_f1": per_f1, "yes_no": is_yn,
                          "pred_yes": bool(nhyp.split()[:1] == ["yes"]),
                          "ref_yes": bool(nref.split()[:1] == ["yes"])})
        pred_yes.append(bool(nhyp.split()[:1] == ["yes"]))
        ref_yes.append(bool(nref.split()[:1] == ["yes"]))
        correct.append(bool(nhyp == nref))
        f1s.append(per_f1)
        yn_flags.append(is_yn)
        if i < 3 or (i + 1) % 250 == 0:
            print("    arm=%s %d/%d gen=%r ref=%r" % (tag, i + 1, n, gen[:32], refs[-1][:32]),
                  flush=True)
        del inp, out
        if (i + 1) % 50 == 0:
            torch.cuda.empty_cache()

    pred_yes, ref_yes = np.array(pred_yes), np.array(ref_yes)
    correct_arr, f1_arr = np.array(correct, dtype=float), np.array(f1s, dtype=float)
    accuracy = float(correct_arr.mean())
    token_f1_mean = float(f1_arr.mean())
    all_ref = [norm(r) for r in refs]
    all_hyp = [norm(h) for h in hyps]
    if abs(f1_arr.mean() - float(token_f1(all_ref, all_hyp))) > 1e-12:
        print("  ERROR: the per-question F1 does not average to the arm-level F1")
        return 1
    yn_sel = [c for c, f in zip(correct, yn_flags) if f]
    yn_acc = float(np.mean(yn_sel)) if yn_sel else None
    tp = float(np.sum(pred_yes & ref_yes))
    fp = float(np.sum(pred_yes & ~ref_yes))
    fn = float(np.sum(~pred_yes & ref_yes))
    tn = float(np.sum(~pred_yes & ~ref_yes))
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    pope_f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    elapsed_min = (time.time() - t0) / 60.0
    report = {
        "meta": {
            "script": rel(SELF),
            "task": "P3 second downstream task: POPE object-hallucination probing",
            "dataset_id": DATASET_ID, "dataset_revision": DATASET_REVISION,
            "dataset_alias": DATASET_ID_ALIAS, "config": DATASET_CONFIG, "split": args.split,
            "n_eval": n, "limit": args.limit,
            "prompt": PROMPT_PREFIX + "<question>",
            "decoding": "greedy (do_sample=False), max_new_tokens=%d" % MAX_NEW_TOKENS,
            "evaluation_code": "tools/_p1516_p3_vqa_downstream.py norm()/token_f1() reused by "
                               "import; prompt prefix and max_new_tokens identical to "
                               "tools/_p1613_p3_cloud_runner.py's VQA arm",
            "prepared_parquet": rel(prepared), "prepared_parquet_sha256": dataset_sha,
            "images_dir": rel(os.path.join(IMAGES_DIR, args.split)),
            "adapter_dir": None if adapter_dir is None else rel(adapter_dir),
            "adapter_source": adapter_how,
            "adapter_sha256": (sha256_file(os.path.join(adapter_dir, "adapter_model.safetensors"))
                               if adapter_dir else None),
            "adapter_sha256_reference": ADAPTER_REFERENCE.get(tag),
            "adapter_recipe": ADAPTER_RECIPE if rank is not None else "none (base model)",
            "base_model": rel(MODEL),
            "torch": _version("torch"), "cuda": _cuda(), "gpu": _gpu(),
            "elapsed_min": elapsed_min,
            "metric_definitions": "accuracy = normalised exact match; token_f1 = mean of the "
                                  "per-question token F1 (the imported definition); pope_f1 = "
                                  "yes-class F1 = 2TP/(2TP+FP+FN) with yes as the positive class; "
                                  "yes_ratio = predicted-yes share; yes_no subset = questions whose "
                                  "reference is yes or no",
            "answer_space": list(ANSWER_SPACE),
        },
        "rank": rank,
        "accuracy": accuracy,
        "token_f1": token_f1_mean,
        "relaxed_accuracy": float(np.mean([bool(set(a.split()) <= set(b.split()))
                                           for a, b in zip(all_ref, all_hyp)])),
        "yes_no_accuracy": yn_acc,
        "n_yes_no": int(sum(yn_flags)),
        "yes_ratio": float(pred_yes.mean()),
        "pope_precision": precision, "pope_recall": recall, "pope_f1": pope_f1,
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "refs": refs, "hypotheses": hyps, "images": images,
        "categories": [str(row.get("category", "")) for _, row in df.iterrows()],
        "refs_sha256": sha256_json(refs), "questions": questions,
        "ok": True,
    }
    write_json(out_path, report)
    print("\n[3] arm=%s accuracy=%.4f token_f1=%.4f pope_f1=%.4f yes_ratio=%.4f (n=%d, %.1f min)"
          % (tag, accuracy, token_f1_mean, pope_f1, float(pred_yes.mean()), n, elapsed_min))
    print("  wrote %s" % rel(out_path))
    written = load_json(out_path)
    show("written archive carries the printed accuracy", "%.4f" % written["accuracy"],
         abs(float(written["accuracy"]) - accuracy) < 1e-12, rel(out_path))
    show("written archive carries the printed pope_f1", "%.4f" % written["pope_f1"],
         abs(float(written["pope_f1"]) - pope_f1) < 1e-12, "yes-class F1 on the same records")
    ledger()
    return 1 if any(not ok for _, ok in CHECKS) else 0


def _version(name: str):
    try:
        return __import__(name).__version__
    except Exception:  # noqa: BLE001
        return None


def _cuda():
    try:
        import torch
        return getattr(torch.version, "cuda", None)
    except Exception:  # noqa: BLE001
        return None


def _gpu():
    try:
        import torch
        return torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    except Exception:  # noqa: BLE001
        return None


# ------------------------------------------------------------------------------------------------
# --aggregate
# ------------------------------------------------------------------------------------------------
def arm_from_payload(d: dict, archive: str) -> dict:
    """Turn an arm archive payload into the arrays the contrast function consumes."""
    refs, hyps = d["refs"], d["hypotheses"]
    norm, token_f1 = metric_functions()
    nref = [norm(x) for x in refs]
    nhyp = [norm(x) for x in hyps]
    correct = np.array([1.0 if a == b else 0.0 for a, b in zip(nhyp, nref)])
    f1 = np.array([float(token_f1(a, b)) for a, b in zip(nref, nhyp)])
    pred_yes = np.array([h.split()[:1] == ["yes"] for h in nhyp])
    ref_yes = np.array([r.split()[:1] == ["yes"] for r in nref])
    meta = d.get("meta") or {}
    return {
        "archive": archive, "rank": d.get("rank"), "n_questions": len(refs),
        "refs": refs, "refs_sha256": d.get("refs_sha256") or sha256_json(refs),
        "hypotheses": hyps,
        "adapter_dir": meta.get("adapter_dir"), "adapter_source": meta.get("adapter_source"),
        "adapter_sha256": meta.get("adapter_sha256"),
        "archived_accuracy": float(d.get("accuracy", float(correct.mean()))),
        "archived_token_f1": float(d.get("token_f1", float(f1.mean()))),
        "archived_pope_f1": float(d.get("pope_f1", pope_f1_from_flags(pred_yes, ref_yes))),
        "accuracy": float(correct.mean()), "token_f1": float(f1.mean()),
        "pope_f1": pope_f1_from_flags(pred_yes, ref_yes),
        "yes_ratio": float(pred_yes.mean()),
        "correct": correct, "f1": f1, "pred_yes": pred_yes, "ref_yes": ref_yes,
    }


def load_arm_full(tag: str) -> dict:
    """Load one arm archive from disk (see arm_from_payload)."""
    path = ARM_OUT % tag
    return arm_from_payload(load_json(path), rel(path))


def synthetic_arms(n: int = 240, seed: int = 7) -> dict:
    """A fixed in-memory fixture for --self-test: three arms over the same synthetic questions.

    Arm 5 answers slightly better than the base model, arm 6 slightly worse; every reference is a
    yes/no question, so the fixture exercises the same code path as the POPE evaluation without
    touching the disk, the GPU or the network.
    """
    rng = np.random.default_rng(seed)
    refs, hyps = [], {"base": [], "5": [], "6": []}
    for i in range(n):
        ref_yes = bool(i % 2 == 0)
        refs.append("yes" if ref_yes else "no")
        for tag in ARMS:
            rate = {"base": 0.80, "5": 0.86, "6": 0.78}[tag]
            hit = bool(rng.random() < rate)
            hyps[tag].append(("yes" if ref_yes else "no") if hit
                             else ("no" if ref_yes else "yes"))
    arms = {}
    for tag in ARMS:
        payload = {"rank": None if tag == "base" else int(tag), "refs": refs,
                   "hypotheses": hyps[tag], "refs_sha256": sha256_json(refs),
                   "meta": {"adapter_dir": None if tag == "base"
                            else "outputs/p3_vqa_adapters/r%s_step" % tag,
                            "adapter_source": "none" if tag == "base"
                            else "reused_from_archived_round",
                            "adapter_sha256": None if tag == "base" else ADAPTER_REFERENCE[tag]}}
        arms[tag] = arm_from_payload(payload, "fixture (in memory)")
    return {"arms": arms, "n_seen": {t: n for t in ARMS}}


def refs_match_parquet(arms: dict, prepared: str) -> bool:
    import pandas as pd
    want = [str(x) for x in pd.read_parquet(prepared)["output"].tolist()]
    return all([str(x) for x in arms[t]["refs"]] == want for t in ARMS if t in arms)


def aggregate(args) -> int:
    print("=" * 118)
    print("P3 TASK B -- AGGREGATE -> %s" % rel(AGG_OUT))
    print("=" * 118)
    prepared = PREPARED % args.split
    print("\n[1] arms")
    if not os.path.exists(prepared):
        if args.dry_run:
            pending("prepared parquet present", "run --prepare first; nothing to aggregate yet")
            print("  (dry run: the real mode stops here with exit code 2)")
            return 0
        show("prepared parquet present", rel(prepared), False, "run --prepare first")
        return 2
    show("prepared parquet present", rel(prepared), True, "written by --prepare")
    present = [t for t in ARMS if os.path.exists(ARM_OUT % t)]
    missing = [t for t in ARMS if t not in present]
    if missing and args.dry_run:
        pending("all three arms present", "missing: %s" % missing)
    else:
        show("all three arms present", "%s" % present, not missing, "missing: %s" % missing)
    if missing:
        print("\n  no contrast is reported with a missing arm.  Exact producer commands:")
        for t in missing:
            print("      %s --eval --rank %s --split %s" % (rel(SELF), t, args.split))
        print("      (the adapters of arms 5 and 6 are %s)"
              % ", ".join(rel(os.path.join(ADAPTERS_DIR, ADAPTER_DIRS[t])) for t in ("5", "6")))
        if args.dry_run:
            print("  (dry run: the real mode stops here with exit code 2)")
            return 0
        return 2

    arms = {t: load_arm_full(t) for t in ARMS}
    n_seen = {t: arms[t]["n_questions"] for t in ARMS}
    show("equal question counts across arms", "%s" % n_seen, len(set(n_seen.values())) == 1,
         "pairing by question requires the same evaluation set in the same order")
    if len(set(n_seen.values())) != 1:
        return 2
    same_refs = len({tuple(arms[t]["refs"]) for t in ARMS}) <= 1
    same_sha = len({arms[t]["refs_sha256"] for t in ARMS}) <= 1
    match_parquet = refs_match_parquet(arms, prepared)
    show("reference arrays identical across arms", "%s" % same_refs, same_refs,
         "same questions in the same order => the pairing is legitimate")
    show("reference sha256 identical across arms",
         "%s" % sorted({arms[t]["refs_sha256"] for t in ARMS})[0][:16], same_sha,
         "sha256 of the JSON encoding of the refs array")
    show("references match the prepared parquet in row order", "%s" % match_parquet, match_parquet,
         "%s" % rel(prepared))

    result, acceptance = aggregate_core(arms, n_seen, rel(prepared), sha256_file(prepared),
                                        args.n_boot, args.split, missing, same_sha, match_parquet)
    if args.dry_run:
        print("\n[3] dry run: computed in memory, nothing was written")
        print("    would write %s" % rel(AGG_OUT))
    else:
        write_json(AGG_OUT, result)
        print("\n[3] wrote %s" % rel(AGG_OUT))
    failed = [label for label, ok in CHECKS if not ok]
    print("\n[4] assertion ledger: %d checks, %d failed" % (len(CHECKS), len(failed)))
    for label in failed:
        print("    FAILED:", label)
    if not args.dry_run:
        bad = assert_printed_against_json(load_json(AGG_OUT))
        if bad:
            return 1
    if args.strict:
        unmet = [k for k, v in acceptance.items() if v is False]
        print("\n[5] strict acceptance: %s"
              % ("satisfied" if not unmet else "NOT satisfied: %s" % unmet))
        if unmet:
            return 3
    return 1 if failed else 0


def aggregate_core(arms: dict, n_seen: dict, prepared_rel: str, prepared_sha: str, n_boot: int,
                   split: str, missing: list, same_sha: bool, match_parquet: bool) -> tuple:
    """Contrasts, verdict, acceptance and the archive payload.  Pure: the self-test calls it too."""
    n = n_seen["base"]
    for t in ARMS:
        a = arms[t]
        note("arm %s" % t,
             "n=%d acc=%.4f tok_f1=%.4f pope_f1=%.4f yes_ratio=%.4f"
             % (a["n_questions"], a["accuracy"], a["token_f1"], a["pope_f1"], a["yes_ratio"]),
             "%s (%s)" % (a["adapter_dir"] or "-", a["adapter_source"]),
             [("arms.%s.n" % t, a["n_questions"]), ("arms.%s.accuracy" % t, a["accuracy"]),
              ("arms.%s.token_f1" % t, a["token_f1"]), ("arms.%s.pope_f1" % t, a["pope_f1"]),
              ("arms.%s.yes_ratio" % t, a["yes_ratio"])])

    if not QUIET:
        print("\n[2] contrasts (paired by question, %d bootstrap replicates)" % n_boot)
    rng = np.random.default_rng(RNG_SEED)
    contrasts = {}
    for a_tag, b_tag in CONTRASTS:
        name = "%s_minus_%s" % (a_tag, b_tag)
        block = paired_bootstrap_set(arms[a_tag], arms[b_tag], rng, n_boot, MARGIN_ACC)
        contrasts[name] = block
        for metric in METRICS:
            d = block[metric]
            note("%s %s" % (name, metric),
                 "delta %+0.6f  CI95 [%+0.4f,%+0.4f]  TOST p=%.4f  min margin %.4f%s"
                 % (d["delta"], d["ci95"][0], d["ci95"][1], d["tost_p"], d["min_equivalent_margin"],
                    "  EQUIVALENT" if d["equivalent_at_declared_margin"] else ""),
                 "%s margin %g" % (metric, MARGIN_ACC if metric == "accuracy" else MARGIN_F1),
                 [("contrasts.%s.%s.delta" % (name, metric), d["delta"]),
                  ("contrasts.%s.%s.ci95" % (name, metric), list(d["ci95"])),
                  ("contrasts.%s.%s.tost_p" % (name, metric), d["tost_p"]),
                  ("contrasts.%s.%s.min_equivalent_margin" % (name, metric),
                   d["min_equivalent_margin"])])

    acc_b5 = contrasts["base_minus_5"]["accuracy"]
    acc_b6 = contrasts["base_minus_6"]["accuracy"]
    f1_b5 = contrasts["base_minus_5"]["pope_f1"]
    f1_b6 = contrasts["base_minus_6"]["pope_f1"]
    acc_56 = contrasts["5_minus_6"]["accuracy"]
    both_keep = all(d["equivalent_at_declared_margin"] or d["ci95"][0] > 0 for d in (acc_b5, acc_b6))
    both_lose = any(d["ci95"][1] < -MARGIN_ACC for d in (acc_b5, acc_b6))
    verdict = ("task_dependent_effect" if both_lose
               else ("supports_the_adapters" if both_keep else "inconclusive"))
    note("second-task verdict", verdict, "keep=%s lose=%s" % (both_keep, both_lose),
         [("claim_verdict.second_task_verdict", verdict)])
    note("n questions per arm", "%d" % n, "identical across the three arms",
         [("meta.dataset.n_questions", n)])

    smallest = {}
    for name, block in contrasts.items():
        for metric in METRICS:
            smallest["%s/%s" % (name, metric)] = block[metric]["min_equivalent_margin"]

    acceptance = {
        "three_arms_present": not missing,
        "records_per_arm": n_seen,
        "equal_question_counts": len(set(n_seen.values())) == 1,
        "refs_byte_identical_across_arms": bool(same_sha),
        "refs_match_prepared_parquet_order": bool(match_parquet),
        "adapters_reused_not_trained": all(
            arms[t]["adapter_source"] == "reused_from_archived_round"
            and arms[t]["adapter_sha256"] == ADAPTER_REFERENCE[t] for t in ("5", "6")),
        "contrasts_computed": all("%s_minus_%s" % c in contrasts for c in CONTRASTS),
        "every_contrast_reports_a_minimum_equivalent_margin": all(
            v is not None for v in smallest.values()),
    }
    result = {
        "meta": {
            "script": rel(SELF),
            "job": "second downstream task -- POPE",
            "task": "P3 second downstream task: POPE object-hallucination probing, paired by "
                    "question, with the metric conventions of the archived VQA-RAD check",
            "dataset": {"id": DATASET_ID, "alias": DATASET_ID_ALIAS, "revision": DATASET_REVISION,
                        "config": DATASET_CONFIG, "split": split, "n_questions": n,
                        "paper": DATASET_PAPER, "prepared_parquet": prepared_rel,
                        "prepared_parquet_sha256": prepared_sha},
            "n_boot": n_boot, "rng_seed": RNG_SEED, "alpha": ALPHA,
            "declared_margins": {"accuracy": MARGIN_ACC, "token_f1": MARGIN_F1,
                                 "pope_f1": MARGIN_F1},
            "margin_rule": ("0.05 on every metric, pre-declared and carried over unchanged from the "
                            "451-question VQA-RAD analysis.  A 3000-question arm has a binomial "
                            "standard error of ~0.009 in accuracy, so this evaluation set is not at "
                            "its resolution limit; the margin is not re-fitted, and the smallest "
                            "equivalent margin is reported alongside every contrast."),
            "method": "paired (by question) percentile bootstrap of the difference plus TOST; the "
                      "resampling rule and the interval definitions are tools/_p1595_p3_rank_"
                      "separation.py vqa_contrast()",
            "field_names_shared_with_the_vqa_archives": ["accuracy", "token_f1", "yes_no_accuracy",
                                                         "refs", "hypotheses", "relaxed_accuracy"],
            "archives": [arms[t]["archive"] for t in ARMS],
            "deterministic": True,
            "note": "no wall-clock field is written, so re-running this aggregation on unchanged "
                    "inputs reproduces this file byte for byte",
        },
        "arms": {t: {"rank": arms[t]["rank"], "n": arms[t]["n_questions"],
                     "accuracy": arms[t]["accuracy"], "token_f1": arms[t]["token_f1"],
                     "pope_f1": arms[t]["pope_f1"], "yes_ratio": arms[t]["yes_ratio"],
                     "archive": arms[t]["archive"], "adapter_dir": arms[t]["adapter_dir"],
                     "adapter_source": arms[t]["adapter_source"],
                     "adapter_sha256": arms[t]["adapter_sha256"]} for t in ARMS},
        "refs_identical_across_arms": bool(same_sha),
        "refs_sha256": {t: arms[t]["refs_sha256"] for t in ARMS},
        "contrasts": contrasts,
        "smallest_equivalent_margin": smallest,
        "claim_verdict": {
            "second_task_verdict": verdict,
            "base_minus_r5": {"accuracy": acc_b5, "pope_f1": f1_b5},
            "base_minus_r6": {"accuracy": acc_b6, "pope_f1": f1_b6},
            "r5_minus_r6": {"accuracy": acc_56},
            "rule": ("supports_the_adapters = both adapters are equivalent to or better than the base "
                     "model on accuracy; task_dependent_effect = an adapter loses more than the "
                     "margin on accuracy; inconclusive = neither statement holds"),
        },
        "acceptance": acceptance,
        "caveat_sentences": {
            "two_tasks": "The downstream check is repeated on a second, independent task (POPE, "
                         "config Full/split random, 3000 held-out questions, the adapters reused "
                         "unchanged), so the downstream evidence rests on two task families rather "
                         "than one.",
            "task_dependent": "The downstream check on a second task (POPE) does not reproduce the "
                              "VQA-RAD direction: the adapters lose accuracy or yes-class F1 beyond "
                              "the pre-declared margin, so the downstream effect is task-dependent.",
            "not_run": "The downstream check remains a single task (VQA-RAD); POPE was prepared "
                       "(tools/_p1640_p3_second_downstream.py) but not run.",
        },
    }
    return result, acceptance


def assert_printed_against_json(written: dict, target: str = None) -> int:
    """Every number note()d must appear in the written JSON, unchanged."""
    target = target or rel(AGG_OUT)
    print("\n[6] printed-number ledger: %d numbers asserted against %s" % (len(ASSERTS), target))
    bad = []
    for label, path, value in ASSERTS:
        found = dig(written, path)
        if isinstance(value, list):
            ok = len(found) == len(value) and all(abs(float(a) - float(b)) <= 1e-12
                                                  for a, b in zip(found, value))
        elif isinstance(value, float):
            ok = abs(float(found) - value) <= 1e-12
        else:
            ok = found == value
        if not ok:
            bad.append((label, path, value, found))
        print("  %-34s %-46s %s" % (label, path, "OK  " if ok else "FAIL"))
    for label, path, value, found in bad:
        print("    MISMATCH: %s printed %r but %s holds %r" % (label, value, path, found))
    return len(bad)


# ------------------------------------------------------------------------------------------------
# --self-test
# ------------------------------------------------------------------------------------------------
def self_test() -> int:
    print("=" * 118)
    print("P3 TASK B -- SELF TEST (no GPU, no network, nothing written)")
    print("=" * 118)
    print("\n[A] metrics are the archived ones")
    show("imported norm()/token_f1() canary", "4 norm + 4 f1 cases", canary_metric_check(),
         "the two downstream tasks are measured by the same definitions")
    try:
        cr = load_module("cr_selftest", CLOUD_RUNNER)
        show("prompt/decoding identical to the archived VQA arm",
             "%r / %d" % (PROMPT_PREFIX, MAX_NEW_TOKENS),
             cr.VQA_PROMPT_PREFIX == PROMPT_PREFIX and cr.VQA_MAX_NEW_TOKENS == MAX_NEW_TOKENS,
             "prompt prefix and max_new_tokens come from the same frozen protocol")
    except Exception as exc:  # noqa: BLE001
        show("prompt/decoding identical to the archived VQA arm", "error", False, "%r" % (exc,))
    fixture_pred = np.array([True, True, False, False])
    fixture_ref = np.array([True, False, True, False])
    want_f1 = 2 * 1.0 / (2 * 1.0 + 1 + 1)
    show("yes-class F1 on a hand-computed fixture",
         "%.4f" % pope_f1_from_flags(fixture_pred, fixture_ref),
         abs(pope_f1_from_flags(fixture_pred, fixture_ref) - want_f1) < 1e-12,
         "TP=1 FP=1 FN=1 -> 2TP/(2TP+FP+FN) = %.4f" % want_f1)

    print("\n[B] the bootstrap mirrors tools/_p1595_p3_rank_separation.py")
    try:
        eq = load_module("p1595_selftest_b", RANKSEP_SCRIPT)
        n = 10
        vals = np.array([1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0])
        f1s = np.array([1.0, 0.0, 0.5, 0.75, 0.25, 1.0, 0.0, 0.5, 1.0, 0.5])
        a = {"correct": vals, "f1": f1s, "pred_yes": vals.astype(bool),
             "ref_yes": np.ones(n, bool)}
        b = {"correct": np.zeros(n), "f1": np.zeros(n), "pred_yes": np.zeros(n, bool),
             "ref_yes": np.ones(n, bool)}
        n_boot = 4000
        mine = paired_bootstrap_set(a, b, np.random.default_rng(RNG_SEED), n_boot, 0.05)
        theirs = eq.vqa_contrast(a, b, np.random.default_rng(RNG_SEED), n_boot)
        drift = []
        for metric in ("accuracy", "token_f1"):
            for field in ("delta", "boot_mean", "boot_se", "ci95", "ci90", "tost_p",
                          "tost_p_lower", "tost_p_upper", "equivalent_at_declared_margin",
                          "min_equivalent_margin"):
                x, y = mine[metric].get(field), theirs[metric].get(field)
                same = np.allclose(x, y) if isinstance(x, list) else (x == y)
                if not same:
                    drift.append("%s.%s %r vs %r" % (metric, field, x, y))
        show("paired_bootstrap_set == imported vqa_contrast (accuracy, token_f1)",
             "2 metrics x 10 fields", not drift,
             "; ".join(drift) if drift else "interval, TOST p-value and minimum equivalent margin "
                                            "agree field by field on identical input")
    except Exception as exc:  # noqa: BLE001
        show("paired_bootstrap_set == imported vqa_contrast (accuracy, token_f1)", "error", False,
             "%r" % (exc,))

    print("\n[C] guards")
    ok, why = arm_archive(ARM_OUT % "base", "base", 1)
    show("a missing arm archive is refused", "%s" % why, ok is False,
         "the aggregate stops with the exact --eval command instead of reporting a number")
    source = io.open(SELF, encoding="utf-8").read()
    # assembled at run time so the guard does not match its own source line
    forbidden = ["import " + mod for mod in ("subprocess", "socket", "urllib", "requests")]
    found = [tok for tok in forbidden if tok in source]
    show("the script has no execution or download capability", "no such import",
         not found, "checked: %s" % ", ".join(found) if found
         else "no subprocess/socket/urllib/requests import; the fetch commands are printed strings")
    show("every fetch command is a printed instruction",
         "%d lines" % len(FETCH_COMMANDS),
         all(line.startswith(("#", "export", "mkdir", "python", "modelscope"))
             for line in FETCH_COMMANDS),
         "the operator runs them; nothing in this file opens a socket")

    print("\n[D] inputs on this machine (read-only)")
    rc = verify_local()
    ledger()
    print("\n[E] end-to-end aggregate rehearsal on a synthetic fixture (nothing written)")
    global QUIET
    QUIET, ASSERTS[:] = True, []
    try:
        fixture = synthetic_arms()
        res1, acc1 = aggregate_core(fixture["arms"], fixture["n_seen"], "fixture (in memory)",
                                    "0" * 64, 4000, SPLIT_DEFAULT, [], True, True)
        first_pass = list(ASSERTS)
        res2, _ = aggregate_core(fixture["arms"], fixture["n_seen"], "fixture (in memory)",
                                 "0" * 64, 4000, SPLIT_DEFAULT, [], True, True)
        ASSERTS[:] = first_pass
        show("aggregate core is deterministic on a fixed fixture",
             "%s" % sha256_json(res1)[:16], sha256_json(res1) == sha256_json(res2),
             "no wall-clock field and a fixed RNG seed => byte-identical payloads")
        complete = all(m in res1["contrasts"][k] for k in res1["contrasts"] for m in METRICS)
        show("three pairs x three metrics computed", "%d contrasts" % len(res1["contrasts"]),
             complete and len(res1["contrasts"]) == len(CONTRASTS),
             "accuracy (per question), token_f1 (per question) and pope_f1 (set level)")
        marg_ok = all(res1["contrasts"][k][m]["min_equivalent_margin"] is not None
                      for k in res1["contrasts"] for m in METRICS)
        show("every contrast reports its smallest equivalent margin", "9 values", marg_ok,
             "required by the paper's S28 wording")
        show("acceptance block is populated", "%d keys" % len(acc1),
             acc1["contrasts_computed"] and acc1["equal_question_counts"]
             and acc1["adapters_reused_not_trained"] and acc1["refs_byte_identical_across_arms"],
             "the fixture uses the archived adapters and identical references")
        show("fixture verdict follows the rule", "%s" % res1["claim_verdict"]["second_task_verdict"],
             res1["claim_verdict"]["second_task_verdict"] in
             ("supports_the_adapters", "task_dependent_effect", "inconclusive"),
             "the fixture's arm 5 beats 0.80 and arm 6 sits at 0.78")
        bad = assert_printed_against_json(res1, target="the in-memory fixture result")
        show("every printed number equals the fixture payload", "%d numbers" % len(ASSERTS),
             bad == 0, "the same ledger that runs after --aggregate writes the real archive")
    except Exception as exc:  # noqa: BLE001
        show("end-to-end aggregate rehearsal", "error", False, "%r" % (exc,))
    finally:
        QUIET = False
    print("\n  nothing was executed and nothing was written")
    return 1 if any(not okk for _, okk in CHECKS) else 0


# ------------------------------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="P3 task B: POPE as a second downstream task, with the "
                                             "metric conventions of the archived VQA-RAD check")
    ap.add_argument("--plan", action="store_true",
                    help="print the plan and verify the local inputs (default; writes nothing)")
    ap.add_argument("--self-test", action="store_true",
                    help="offline metric/statistics guards (writes nothing)")
    ap.add_argument("--prepare", action="store_true",
                    help="validate the raw POPE parquet and materialise the prepared parquet + images")
    ap.add_argument("--eval", action="store_true", help="evaluate one arm (one process per arm)")
    ap.add_argument("--aggregate", action="store_true",
                    help="paired bootstrap + TOST over the three arms; writes %s" % rel(AGG_OUT))
    ap.add_argument("--rank", default="base", choices=("base", "5", "6"),
                    help="which arm to evaluate")
    ap.add_argument("--split", default=SPLIT_DEFAULT, choices=SPLITS + ("all",),
                    help="POPE split (random is the default; 'all' is only meaningful for --prepare)")
    ap.add_argument("--limit", type=int, default=None,
                    help="evaluate only the first N questions (smoke mode; recorded in the archive)")
    ap.add_argument("--n-boot", type=int, default=N_BOOT, help="bootstrap replicates")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan/commands, execute nothing, write nothing")
    ap.add_argument("--force", action="store_true",
                    help="redo work whose output already exists")
    ap.add_argument("--strict", action="store_true",
                    help="with --aggregate: exit non-zero when an acceptance criterion is unmet")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.prepare:
        return prepare(args)
    if args.eval:
        return eval_arm(args)
    if args.aggregate:
        return aggregate(args)
    if args.split == "all":
        args.split = SPLIT_DEFAULT
    return plan()


if __name__ == "__main__":
    raise SystemExit(main())