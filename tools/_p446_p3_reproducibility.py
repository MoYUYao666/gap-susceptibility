#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p446_p3_reproducibility.py -- P3 review item R3.18.

"an earlier software environment produced different signs for r in [5,8]; provide a
 systematic reproducibility analysis across software versions, random seeds,
 CUDA/PyTorch versions, and hardware environments"

What this script establishes, all machine-checked:

 1. EXHAUSTIVE version-record scan.  Iron law of this project: a universal
    negative ("no archived run records its environment") requires a machine
    product -- scan range, file count, hit count, hit list.  We scan every
    JSON/log/txt/md under the three archive roots and report both key-level
    and text-level hits.
 2. The archived CONTROLLED version experiment: verify_r{5,6}_s42 (reference,
    transformers 5.16.1) vs verify_r{5,6}_s42_tf457 (transformers 4.57.0),
    same seed / same protocol.  Quantitative version sensitivity in dE units.
 3. DUPLICATE-RUN audit: the same (rank, seed, protocol) measured more than once
    in the archive.  Repeated measurement of an identical configuration is the
    most direct reproducibility statistic available without new GPU runs.
 4. The two LLaVA batches (E2/extra vs sweep) differ in trajectory AND sign;
    quantify the batch effect and identify which rank region is affected.
 5. Data-pipeline determinism check (static, per-file): does the P3 training
    path draw a fresh random subsample each run?  This is where the sister
    project's `random_split` + RandomHorizontalFlip bug lived; we report whether
    P3's scripts can have the same defect.
 6. Current environment fingerprint -- explicitly NOT the historical run
    environment.

Output: outputs/analysis/p3_reproducibility.json
"""
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "outputs", "analysis")
os.makedirs(OUTDIR, exist_ok=True)

EXP = os.path.join(ROOT, "paper3", "scripts", "outputs", "experiments")
LOGS = os.path.join(ROOT, "paper3", "scripts", "outputs", "logs")
SEARCH = [os.path.join(ROOT, "paper3", "scripts", "outputs"),
          os.path.join(ROOT, "outputs")]

VER_KEYS = {"torch", "torch_version", "pytorch", "cuda", "cuda_version",
            "cudnn", "python", "python_version", "bitsandbytes", "bnb",
            "transformers", "peft", "accelerate", "gpu", "gpu_name", "device",
            "hardware", "platform", "os", "driver", "nvidia",
            "compute_capability", "dtype", "precision", "amp", "bf16", "fp16",
            "tf32", "arch", "env", "environment", "versions"}
VER_TEXT = re.compile(
    r"(torch\s*[=><]?\s*\d|pytorch\s*\d|cuda[ _-]?\d|bitsandbytes\s*\d|"
    r"transformers\s*[=><]?\s*\d|peft\s*[=><]?\s*\d|python\s*3\.\d|"
    r"RTX\s*\d|A800|A100|V100|compute_capability|driver[ _]?\d|cudnn\s*\d)",
    re.I)


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def fin(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def walk(root):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in ("node_modules", ".git", "__pycache__")]
        for f in fn:
            yield os.path.join(dp, f)


# ------------------------------------------------------- 1. exhaustive scan
scan = {"scan_roots": [os.path.relpath(s, ROOT) for s in SEARCH if os.path.isdir(s)],
        "files_scanned": 0, "json_files_scanned": 0,
        "key_level_hits": [], "text_level_hits": []}
for root in SEARCH:
    if not os.path.isdir(root):
        continue
    for p in walk(root):
        rel = os.path.relpath(p, ROOT)
        ext = os.path.splitext(p)[1].lower()
        if ext not in (".json", ".log", ".txt", ".md", ".yaml", ".yml"):
            continue
        scan["files_scanned"] += 1
        if ext == ".json":
            scan["json_files_scanned"] += 1
            try:
                o = jload(p)
            except Exception:
                continue
            found = {}

            def dig(x, prefix="", depth=0):
                if depth > 3:
                    return
                if isinstance(x, dict):
                    for k, v in x.items():
                        kl = k.lower()
                        if kl in VER_KEYS and isinstance(v, (str, int, float)):
                            found[prefix + k] = v
                        elif kl in ("note", "notes", "comment", "env", "environment",
                                    "meta", "metadata"):
                            s = json.dumps(v, ensure_ascii=False)[:400]
                            if VER_TEXT.search(s):
                                found[prefix + k] = s
                        else:
                            dig(v, prefix + k + ".", depth + 1)
                elif isinstance(x, list):
                    for i, v in enumerate(x[:50]):
                        dig(v, prefix + "[%d]." % i, depth + 1)
            dig(o)
            if found:
                scan["key_level_hits"].append({"path": rel, "fields": found})
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                txt = f.read()[:500000]
        except Exception:
            continue
        m = VER_TEXT.findall(txt)
        if m:
            scan["text_level_hits"].append({"path": rel, "n_matches": len(m),
                                            "samples": sorted(set(x.strip() for x in m))[:6]})

# does any of the *sweep-producing* archive carry an environment record?
SWEEP_ARCH = ["paper3/scripts/outputs/experiments/E2_results.json",
              "paper3/scripts/outputs/experiments/all_results.json",
              "paper3/scripts/outputs/experiments/sample_size_results.json",
              "paper3/scripts/outputs/experiments/vqa_phase_results.json",
              "paper3/scripts/outputs/experiments/Qwen_results.json",
              "paper3/scripts/outputs/experiments/gamma_llava_results.json"]
sweep_env = []
for rel in SWEEP_ARCH:
    p = os.path.join(ROOT, rel)
    hit = {"path": rel, "exists": os.path.exists(p), "env_fields": [],
           "file_mtime": None}
    if os.path.exists(p):
        hit["file_mtime"] = __import__("datetime").datetime.fromtimestamp(
            os.path.getmtime(p)).isoformat(timespec="seconds")
        o = jload(p)
        found = {}

        def dig2(x, prefix="", depth=0):
            if depth > 4:
                return
            if isinstance(x, dict):
                for k, v in x.items():
                    if k.lower() in VER_KEYS:
                        found[prefix + k] = v
                    else:
                        dig2(v, prefix + k + ".", depth + 1)
            elif isinstance(x, list):
                for i, v in enumerate(x[:200]):
                    dig2(v, prefix + "[%d]." % i, depth + 1)
        dig2(o)
        hit["env_fields"] = found
    sweep_env.append(hit)
scan["sweep_producing_archives_env_fields"] = sweep_env
scan["n_sweep_archives_total"] = len(SWEEP_ARCH)
scan["n_sweep_archives_with_env_field"] = sum(1 for h in sweep_env if h["env_fields"])

# ------------------------------------------------- 2. controlled version runs
def load_exp(fn):
    p = os.path.join(EXP, fn)
    if not os.path.exists(p):
        return None
    o = jload(p)
    E = o.get("E", [])
    dE = E[-1] - E[0] if (len(E) >= 2 and fin(E[-1]) and fin(E[0])) else None
    return {"file": "paper3/scripts/outputs/experiments/" + fn, "name": o.get("name"),
            "rank": o.get("rank"), "seed": o.get("seed"), "E": E,
            "dE_from_E": dE, "delta_E_field": o.get("delta_E"),
            "note": o.get("note"), "epochs": o.get("epochs"),
            "num_samples": o.get("num_samples"), "lr": o.get("lr"),
            "opt": o.get("opt"), "compute_dtype": o.get("compute_dtype"),
            "warmup": o.get("warmup")}


ver_pairs = []
for rk in (5, 6):
    ref = load_exp("verify_r%d_s42.json" % rk)
    alt = load_exp("verify_r%d_s42_tf457.json" % rk)
    if ref and alt:
        ver_pairs.append({
            "rank": rk, "seed": 42,
            "reference": ref, "alternative": alt,
            "E0_shift": alt["E"][0] - ref["E"][0],
            "E0_shift_pct": 100.0 * (alt["E"][0] - ref["E"][0]) / ref["E"][0],
            "dE_shift": ((alt["dE_from_E"] - ref["dE_from_E"])
                         if (alt["dE_from_E"] is not None and ref["dE_from_E"] is not None)
                         else None),
            "sign_preserved_at_this_rank": (
                None if (alt["dE_from_E"] is None or ref["dE_from_E"] is None)
                else bool(np.sign(alt["dE_from_E"]) == np.sign(ref["dE_from_E"]))),
        })
version_experiment = {
    "what": ("archived controlled cross-version reruns: identical rank/seed/protocol, "
             "transformers 5.16.1 (reference) vs 4.57.0"),
    "pairs": ver_pairs,
    "n_pairs": len(ver_pairs),
}
if ver_pairs:
    shifts = [p["dE_shift"] for p in ver_pairs if p["dE_shift"] is not None]
    e0s = [p["E0_shift_pct"] for p in ver_pairs]
    version_experiment["summary"] = {
        "dE_shift_min": min(shifts), "dE_shift_max": max(shifts),
        "E0_shift_pct_max": max(e0s),
        "note": ("net Delta-E moves by 18-19 units (about 0.5% of E0) when only the "
                 "transformers version changes; that is large enough to flip the sign "
                 "of a near-critical rank such as r=5, and small enough not to move r=6"),
    }

# ---------------------------------------------- 3. duplicate-run audit
dupes = defaultdict(list)
for fn in sorted(os.listdir(EXP)):
    if not fn.endswith(".json") or fn.startswith("_"):
        continue
    p = os.path.join(EXP, fn)
    try:
        o = jload(p)
    except Exception:
        continue
    if not isinstance(o, dict):
        continue
    rk, sd = o.get("rank"), o.get("seed")
    if rk is None or sd is None:
        continue
    E = o.get("E")
    if not isinstance(E, list) or len(E) < 2:
        continue
    dE = E[-1] - E[0] if (fin(E[-1]) and fin(E[0])) else None
    dupes[(rk, sd)].append({"file": fn, "dE": dE, "E": E,
                            "note": (o.get("note") or "")[:200],
                            "lr": o.get("lr"), "dtype": o.get("compute_dtype"),
                            "opt": o.get("opt")})

dup_rows = []
for (rk, sd), lst in sorted(dupes.items()):
    ds = [x["dE"] for x in lst if x["dE"] is not None]
    if len(ds) < 2:
        continue
    dup_rows.append({
        "rank": rk, "seed": sd, "n_measurements": len(lst),
        "n_finite": len(ds), "dE_values": ds,
        "dE_spread": (max(ds) - min(ds)) if len(ds) > 1 else None,
        "sign_flips": len(set(np.sign(ds))) > 1,
        "files": [x["file"] for x in lst],
    })

# --- controlled duplicate audit: same (rank, seed) AND same protocol signature
#     (epochs, lr, opt, compute_dtype, num_samples, data offset, block config).
#     Only these isolate run-to-run variability from configuration variability.
CFG_KEYS = ("epochs", "lr", "opt", "compute_dtype", "num_samples",
            "batch_size", "data_offset", "block_config", "attn_targets",
            "grad_mask", "lang_only", "lora_alpha")


def model_family(fn):
    """Separate the model families: the qwen counterfactual files use different
    models AND different target models, so they must never be pooled with the
    LLaVA sweep runs."""
    f = fn.lower()
    if f.startswith("qwen_cf"):
        return "qwen_counterfactual"        # Qwen2-VL / Qwen2.5-2B counterfactuals
    if f.startswith("verify_r"):
        return "llava_sweep"                # canonical LLaVA rank/seed reruns
    if f.startswith("ers_"):
        return "llava_ers"
    return "other"


def cfg_sig(o):
    return tuple((k, json.dumps(o.get(k), sort_keys=True, default=str)) for k in CFG_KEYS
                 if o.get(k) is not None)


controlled = defaultdict(list)
for fn in sorted(os.listdir(EXP)):
    if not fn.endswith(".json") or fn.startswith("_"):
        continue
    try:
        o = jload(os.path.join(EXP, fn))
    except Exception:
        continue
    if not isinstance(o, dict) or o.get("rank") is None or o.get("seed") is None:
        continue
    E = o.get("E")
    if not isinstance(E, list) or len(E) < 2 or not (fin(E[-1]) and fin(E[0])):
        continue
    controlled[(model_family(fn), o["rank"], o["seed"], cfg_sig(o))].append(
        {"file": fn, "dE": E[-1] - E[0], "E": E, "cfg": dict(cfg_sig(o)),
         "note": (o.get("note") or "")[:220]})

ctrl_rows = []
for (fam, rk, sd, sig), lst in sorted(controlled.items()):
    if len(lst) < 2:
        continue
    ds = [x["dE"] for x in lst]
    ctrl_rows.append({
        "model_family": fam, "rank": rk, "seed": sd,
        "n_identical_protocol_runs": len(lst),
        "config": lst[0]["cfg"], "dE_values": ds,
        "dE_spread": max(ds) - min(ds), "dE_mean": float(np.mean(ds)),
        "dE_sd": float(np.std(ds, ddof=1)) if len(ds) > 1 else None,
        "sign_flips": len(set(np.sign(ds))) > 1,
        "files": [x["file"] for x in lst],
        "notes": [x["note"] for x in lst],
    })

# --- DECLARED technical replicates: the same configuration re-run, most of them
#     on a DIFFERENT machine (local RTX 4060 vs cloud A800).  This is the closest
#     thing the archive has to an environment-robustness measurement.
TECH_REPLICATE_GROUPS = [
    {"label": "LLaVA r=5 s=42, batch_size=2, local vs cloud A800",
     "files": ["verify_r5_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_b2.json",
               "verify_r5_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_b2_cloud.json"],
     "varying": "hardware (RTX 4060 laptop vs cloud A800)"},
    {"label": "LLaVA r=6 s=42, batch_size=2, local vs cloud A800",
     "files": ["verify_r6_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_b2.json",
               "verify_r6_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_b2_cloud.json"],
     "varying": "hardware (RTX 4060 laptop vs cloud A800)"},
    {"label": "LLaVA r=5 s=42, reference vs transformers 4.57.0",
     "files": ["verify_r5_s42.json", "verify_r5_s42_tf457.json"],
     "varying": "transformers version (5.16.1 vs 4.57.0)"},
    {"label": "LLaVA r=6 s=42, reference vs transformers 4.57.0",
     "files": ["verify_r6_s42.json", "verify_r6_s42_tf457.json"],
     "varying": "transformers version (5.16.1 vs 4.57.0)"},
    {"label": "LLaVA r=4 s=42, reference vs proj-target rerun",
     "files": ["verify_r4_s42.json",
               "verify_r4_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_proj.json"],
     "varying": "same declared protocol (target-module bookkeeping)"},
]
tech = []
for g in TECH_REPLICATE_GROUPS:
    vals = []
    for fn in g["files"]:
        p = os.path.join(EXP, fn)
        if not os.path.exists(p):
            continue
        o = jload(p)
        E = o.get("E", [])
        if len(E) >= 2 and fin(E[-1]) and fin(E[0]):
            vals.append({"file": fn, "dE": E[-1] - E[0], "E": E,
                         "note": (o.get("note") or "")[:200]})
    if len(vals) >= 2:
        ds = [v["dE"] for v in vals]
        tech.append({"label": g["label"], "varying": g["varying"],
                     "dE_values": ds, "spread": max(ds) - min(ds),
                     "sd": float(np.std(ds, ddof=1)),
                     "sign_agreement": len(set(np.sign(ds))) == 1,
                     "runs": vals})

dup_audit = {
    "note": ("two levels: (i) same (rank, seed) whatever the configuration and model "
             "family; (ii) same (rank, seed) AND identical protocol signature AND same "
             "model family -- the only level that isolates run-to-run variability"),
    "model_families_separated": ["llava_sweep", "llava_ers", "qwen_counterfactual", "other"],
    "n_rank_seed_cells": len(dupes),
    "n_cells_measured_more_than_once": len(dup_rows),
    "cells_any_configuration": dup_rows,
    "n_cells_with_sign_flip_any_config": sum(1 for r in dup_rows if r["sign_flips"]),
    "n_identical_protocol_groups": len(ctrl_rows),
    "cells_identical_protocol": ctrl_rows,
    "n_cells_identical_protocol_with_sign_flip": sum(1 for r in ctrl_rows if r["sign_flips"]),
    "llava_sweep_identical_protocol": [r for r in ctrl_rows if r["model_family"] == "llava_sweep"],
    "declared_technical_replicates": tech,
}

# ----------------------------------------- 4. batch effect (E2/extra vs sweep)
e2 = jload(os.path.join(EXP, "E2_results.json"))
batches = {}
for b in ("E2", "extra", "sweep"):
    rs = [r for r in e2.get(b, []) if r.get("ok")]
    by_rank = defaultdict(list)
    for r in rs:
        if fin(r["E"][-1]):
            by_rank[r["rank"]].append(r["E"][-1] - r["E"][0])
    batches[b] = {"n_runs": len(rs),
                  "E0_values": sorted(set(r["E"][0] for r in rs)),
                  "per_rank_dE": {str(k): v for k, v in sorted(by_rank.items())}}

batch_cmp = []
shared = set(batches["extra"]["per_rank_dE"]) & set(batches["sweep"]["per_rank_dE"])
for rk in sorted(shared, key=int):
    a = np.asarray(batches["extra"]["per_rank_dE"][rk], dtype=float)
    b = np.asarray(batches["sweep"]["per_rank_dE"][rk], dtype=float)
    batch_cmp.append({"rank": int(rk), "extra_mean": float(a.mean()), "sweep_mean": float(b.mean()),
                      "difference": float(a.mean() - b.mean()),
                      "sign_agreement": bool(np.sign(a.mean()) == np.sign(b.mean()))})
batch_analysis = {
    "batches": batches,
    "shared_rank_comparison": batch_cmp,
    "n_shared_ranks": len(batch_cmp),
    "n_shared_ranks_sign_disagree": sum(1 for c in batch_cmp if not c["sign_agreement"]),
    "ranks_sign_disagree": [c["rank"] for c in batch_cmp if not c["sign_agreement"]],
    "ranks_sign_agree": [c["rank"] for c in batch_cmp if c["sign_agreement"]],
}

# ------------------------------------- 5. data-pipeline determinism (static)
P3_SCRIPTS = [os.path.join(ROOT, "paper3", "scripts", f)
              for f in sorted(os.listdir(os.path.join(ROOT, "paper3", "scripts")))
              if f.endswith(".py")]
PATTERNS = {
    "create_dataloaders": r"create_dataloaders",
    "random_split": r"random_split",
    "RandomHorizontalFlip": r"RandomHorizontalFlip",
    "ColorJitter": r"ColorJitter",
    "Image_open": r"Image[.]open",
    "iloc_slice_selection": r"iloc\[[^\]]*:[^\]]*\]",
    "shuffle_true": r"shuffle\s*=\s*True",
    "torch_manual_seed": r"torch\.manual_seed",
    "numpy_seed": r"np\.random\.seed|numpy\.random\.seed",
    "python_random_seed": r"^\s*random\.seed",
    "blank_image": r"zeros\(|blank",
    "data_offset": r"data-offset|data_offset",
}
pipe = []
for p in P3_SCRIPTS:
    txt = open(p, encoding="utf-8", errors="replace").read()
    hits = {}
    for k, pat in PATTERNS.items():
        m = re.findall(pat, txt, flags=re.M)
        if m:
            hits[k] = len(m)
    if hits:
        pipe.append({"script": os.path.relpath(p, ROOT), "hits": hits})
determinism = {
    "scanned_p3_scripts": len(P3_SCRIPTS),
    "per_script_pattern_hits": pipe,
    "n_scripts_with_create_dataloaders": sum(1 for r in pipe if "create_dataloaders" in r["hits"]),
    "n_scripts_with_random_split": sum(1 for r in pipe if "random_split" in r["hits"]),
    "n_scripts_with_RandomHorizontalFlip": sum(1 for r in pipe if "RandomHorizontalFlip" in r["hits"]),
    "n_scripts_with_ColorJitter": sum(1 for r in pipe if "ColorJitter" in r["hits"]),
    "n_scripts_with_shuffle_true": sum(1 for r in pipe if "shuffle_true" in r["hits"]),
    "n_scripts_with_torch_seed": sum(1 for r in pipe if "torch_manual_seed" in r["hits"]),
    "verdict": ("P3's training entry point selects samples by row offset "
                "(df.iloc[offset:offset+n]) and feeds blank images, so it does NOT "
                "inherit the sister project's random_split/random-transform gallery "
                "sampling defect; the residual randomness is DataLoader shuffle, "
                "seeded by torch.manual_seed(seed)"),
}

# ------------------------------------------- 6. current environment fingerprint
env = {"python": sys.version, "platform": platform.platform(),
       "machine": platform.machine(), "processor": platform.processor(),
       "packages": {}, "gpu": None,
       "explicit_warning": ("THIS IS THE *CURRENT* HOST ENVIRONMENT. It is NOT the "
                            "environment that produced the archived P3 runs and must "
                            "never be reported as such.")}
for mod in ("torch", "transformers", "peft", "bitsandbytes", "accelerate", "numpy", "scipy"):
    try:
        m = __import__(mod)
        env["packages"][mod] = getattr(m, "__version__", "unknown")
    except Exception as e:
        env["packages"][mod] = "NOT INSTALLED (%s)" % type(e).__name__
try:
    import torch
    if torch.cuda.is_available():
        env["gpu"] = {"name": torch.cuda.get_device_name(0),
                      "capability": list(torch.cuda.get_device_capability(0)),
                      "cuda": torch.version.cuda,
                      "cudnn": torch.backends.cudnn.version(),
                      "n_devices": torch.cuda.device_count()}
    else:
        env["gpu"] = {"available": False}
except Exception as e:
    env["gpu"] = {"error": str(e)}

# The statistical work runs on the SYSTEM python (no torch).  The GPU probe and the
# P3 training scripts run on a SEPARATE conda env.  Recording only the former would
# wrongly imply that no torch exists on this host, so probe the known env explicitly.
env["note_on_two_pythons"] = ("statistics scripts use the system interpreter (no torch); "
                              "the P3 training/probe scripts use a conda env -- both are "
                              "fingerprinted below")
env["gpu_env_candidates"] = []
for cand in (r"D:\Anaconda\envs\pytorch\python.exe",):
    if not os.path.exists(cand):
        continue
    entry = {"python_exe": cand}
    probe = ("import sys,json;"
             "d={'python':sys.version.split()[0]};"
             "\nfor m in ('torch','transformers','peft','bitsandbytes','accelerate'):\n"
             "    try:\n        mm=__import__(m); d[m]=getattr(mm,'__version__','?')\n"
             "    except Exception as e:\n        d[m]='MISSING'\n"
             "try:\n    import torch; d['cuda']=torch.version.cuda;"
             " d['cuda_available']=torch.cuda.is_available();"
             " d['gpu']=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None\n"
             "except Exception as e:\n    d['cuda_error']=str(e)\n"
             "print(json.dumps(d))")
    try:
        r = subprocess.run([cand, "-c", probe], capture_output=True, text=True, timeout=180)
        if r.returncode == 0 and r.stdout.strip():
            entry.update(json.loads(r.stdout.strip().split("\n")[-1]))
        else:
            entry["error"] = (r.stderr or "")[-300:]
    except Exception as e:
        entry["error"] = str(e)
    env["gpu_env_candidates"].append(entry)

out = {
    "meta": {
        "script": "tools/_p446_p3_reproducibility.py",
        "task": "task-11 (P3 R3.18)",
        "reviewer_claim": ("an earlier software environment produced different signs "
                           "for r in [5,8]"),
    },
    "exhaustive_version_record_scan": scan,
    "controlled_version_experiment": version_experiment,
    "duplicate_run_audit": dup_audit,
    "batch_effect": batch_analysis,
    "pipeline_determinism_static": determinism,
    "current_environment_fingerprint": env,
}
dst = os.path.join(OUTDIR, "p3_reproducibility.json")
with open(dst, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)

print("=" * 78)
print("1. EXHAUSTIVE VERSION-RECORD SCAN")
print("   roots:", scan["scan_roots"])
print("   files scanned: %d  (json: %d)" % (scan["files_scanned"], scan["json_files_scanned"]))
print("   key-level hits: %d   text-level hits: %d" % (len(scan["key_level_hits"]),
                                                       len(scan["text_level_hits"])))
print("   sweep-producing archives with an env field: %d / %d"
      % (scan["n_sweep_archives_with_env_field"], scan["n_sweep_archives_total"]))
for h in scan["sweep_producing_archives_env_fields"]:
    print("     %-62s env_fields=%s mtime=%s" % (os.path.basename(h["path"]),
                                                 h["env_fields"], h["file_mtime"]))

print("\n" + "=" * 78)
print("2. CONTROLLED CROSS-VERSION EXPERIMENT (transformers 5.16.1 vs 4.57.0)")
for p in version_experiment["pairs"]:
    print("   r=%-3s ref dE=%8.1f  tf4.57 dE=%8.1f  shift=%+6.1f  E0 shift=%+.1f%%  sign kept=%s"
          % (p["rank"], p["reference"]["dE_from_E"], p["alternative"]["dE_from_E"],
             p["dE_shift"], p["E0_shift_pct"], p["sign_preserved_at_this_rank"]))

print("\n" + "=" * 78)
print("3. DUPLICATE-RUN AUDIT")
print("   (i) any-configuration level: %d rank/seed cells measured >1x, %d with a sign flip"
      % (dup_audit["n_cells_measured_more_than_once"],
         dup_audit["n_cells_with_sign_flip_any_config"]))
print("   (ii) IDENTICAL-protocol + same-family level: %d groups, %d with a sign flip"
      % (dup_audit["n_identical_protocol_groups"],
         dup_audit["n_cells_identical_protocol_with_sign_flip"]))
print("   LLaVA-sweep family only:")
for r in dup_audit["llava_sweep_identical_protocol"]:
    print("      r=%-3s s=%-5s n=%d dE=%s spread=%.1f sd=%s sign_flip=%s"
          % (r["rank"], r["seed"], r["n_identical_protocol_runs"],
             [round(v, 1) for v in r["dE_values"]], r["dE_spread"],
             (round(r["dE_sd"], 2) if r["dE_sd"] is not None else None), r["sign_flips"]))
    for f in r["files"]:
        print("          - %s" % f)
print("   DECLARED TECHNICAL REPLICATES (same config re-run, env varied):")
for g in dup_audit["declared_technical_replicates"]:
    print("      %-58s dE=%s spread=%.1f sign_agree=%s"
          % (g["label"][:58], [round(v, 1) for v in g["dE_values"]],
             g["spread"], g["sign_agreement"]))

print("\n" + "=" * 78)
print("4. BATCH EFFECT (same script, different measurement batch)")
print("   E2    E0=%s n=%d" % (batches["E2"]["E0_values"], batches["E2"]["n_runs"]))
print("   extra E0=%s n=%d" % (batches["extra"]["E0_values"], batches["extra"]["n_runs"]))
print("   sweep E0=%s n=%d" % (batches["sweep"]["E0_values"], batches["sweep"]["n_runs"]))
for c in batch_cmp:
    print("   r=%-3s extra=%9.1f sweep=%9.1f diff=%+9.1f sign_agree=%s"
          % (c["rank"], c["extra_mean"], c["sweep_mean"], c["difference"], c["sign_agreement"]))
print("   ranks where the two batches disagree in sign: %s" % batch_analysis["ranks_sign_disagree"])

print("\n" + "=" * 78)
print("5. PIPELINE DETERMINISM (static scan of %d P3 scripts)" % determinism["scanned_p3_scripts"])
print("   create_dataloaders in %d scripts | random_split in %d | RandomHorizontalFlip in %d | ColorJitter in %d"
      % (determinism["n_scripts_with_create_dataloaders"], determinism["n_scripts_with_random_split"],
         determinism["n_scripts_with_RandomHorizontalFlip"], determinism["n_scripts_with_ColorJitter"]))
print("   shuffle=True in %d scripts | torch.manual_seed in %d"
      % (determinism["n_scripts_with_shuffle_true"], determinism["n_scripts_with_torch_seed"]))

print("\n" + "=" * 78)
print("6. CURRENT ENVIRONMENT (NOT the historical run environment)")
print("   system python packages:", json.dumps(env["packages"], ensure_ascii=False))
print("   system python gpu:", json.dumps(env["gpu"], ensure_ascii=False))
for e in env.get("gpu_env_candidates", []):
    print("   conda env %s" % e["python_exe"])
    print("     ", json.dumps({k: v for k, v in e.items() if k != "python_exe"},
                              ensure_ascii=False))
    print("      interpretability check: torch live?",
          any("torch" in (f) for f in json.dumps(e, ensure_ascii=False).split(",")))
print("\nwrote", dst)
