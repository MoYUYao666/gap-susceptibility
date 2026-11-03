#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p440_p3_recon.py -- P3 (I group) reconnaissance: locate every archived run
that carries a per-seed Delta-E for the LLaVA / Qwen rank sweeps, plus every
gamma / NaN / version-metadata artefact.

Output: outputs/analysis/p3_stats_recon.json  (inventory + parsed per-seed table)

RULE (project iron law): every number later reported must name (a) the producing
script and (b) the archive file + field.  This script is the provenance layer.
"""
import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs", "analysis")
os.makedirs(OUT, exist_ok=True)

SEARCH_DIRS = [
    os.path.join(ROOT, "paper3", "scripts", "outputs"),
    os.path.join(ROOT, "paper3", "paper_ieee", "outputs"),
    os.path.join(ROOT, "outputs"),
]

SKIP_DIR_PARTS = (
    os.sep + "node_modules" + os.sep,
    os.sep + ".git" + os.sep,
    os.sep + ".worktrees" + os.sep,
    os.sep + "backups" + os.sep,
    os.sep + "publish_clean" + os.sep,
)

NAME_HINT = re.compile(
    r"(phase|sweep|rank|sample_size|E2|gamma|counterfactual|e4|repro|seed|"
    r"version|env|cuda|torch|stability|nan|collapse|sharegpt|qwen)",
    re.I,
)


def walk_files():
    for d in SEARCH_DIRS:
        if not os.path.isdir(d):
            continue
        for dirpath, dirnames, filenames in os.walk(d):
            if any(p in dirpath + os.sep for p in SKIP_DIR_PARTS):
                continue
            dirnames[:] = [x for x in dirnames if x not in
                           ("node_modules", ".git", "__pycache__")]
            for fn in filenames:
                yield os.path.join(dirpath, fn)


def load_json(p):
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# ---------------------------------------------------------------- inventory
inventory = []
for p in sorted(walk_files()):
    rel = os.path.relpath(p, ROOT)
    try:
        size = os.path.getsize(p)
    except OSError:
        continue
    rec = {"path": rel, "size": size}
    if p.lower().endswith(".json"):
        obj = load_json(p)
        if obj is None:
            rec["json"] = "PARSE_FAIL"
        else:
            rec["json"] = "ok"
            if isinstance(obj, dict):
                rec["top_keys"] = sorted(list(obj.keys()))[:40]
            elif isinstance(obj, list):
                rec["top_keys"] = ["<list len=%d>" % len(obj)]
        inventory.append(rec)
    elif NAME_HINT.search(os.path.basename(p)):
        inventory.append(rec)

# ------------------------------------------- exhaustive version-record scan
# Iron law: any universal negative ("no run records its software version")
# needs a machine-exhaustive product: scan range + hit count + hit list.
VERSION_KEYS = [
    "torch_version", "torch", "pytorch", "cuda", "cuda_version", "python",
    "python_version", "bitsandbytes", "bnb", "transformers", "peft",
    "accelerate", "gpu", "device", "hardware", "platform", "os",
    "driver", "nvidia", "arch", "env", "environment", "versions",
    "compute_capability", "gpu_name", "hostname", "dtype", "precision",
    "amp", "bf16", "fp16", "tf32",
]
VER_PAT = re.compile(
    r"(torch\s*[=><]?\s*\d|pytorch|cuda[ _-]?\d|bitsandbytes|"
    r"transformers\s*[=><]?\s*\d|\bpeft\s*[=><]?\s*\d|"
    r"python\s*3\.\d|RTX\s*\d|A800|V100|A100|compute_capability|"
    r"driver[ _]?version|cudnn|nvidia-smi)",
    re.I,
)

ver_scan = {"scanned_json_files": 0, "scanned_files_total": 0,
            "key_hits": [], "text_hits": [], "scan_dirs": []}
for d in SEARCH_DIRS:
    ver_scan["scan_dirs"].append(os.path.relpath(d, ROOT) if os.path.exists(d) else d + " (MISSING)")
for p in sorted(walk_files()):
    ver_scan["scanned_files_total"] += 1
    low = p.lower()
    if not (low.endswith(".json") or low.endswith(".log") or low.endswith(".txt")
            or low.endswith(".yaml") or low.endswith(".yml") or low.endswith(".md")):
        continue
    if low.endswith(".json"):
        ver_scan["scanned_json_files"] += 1
    rel = os.path.relpath(p, ROOT)
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            txt = f.read()
    except Exception:
        continue
    if low.endswith(".json"):
        obj = load_json(p)
        if isinstance(obj, dict):
            found = [k for k in obj.keys() if k.lower() in VERSION_KEYS]
            if found:
                sub = {k: obj[k] for k in found}
                ver_scan["key_hits"].append({"path": rel, "keys": sub})
        elif isinstance(obj, list):
            for it in obj[:500]:
                if isinstance(it, dict):
                    found = [k for k in it.keys() if k.lower() in VERSION_KEYS]
                    if found:
                        ver_scan["key_hits"].append(
                            {"path": rel, "keys": {k: it[k] for k in found}})
                        break
    # text-level scan (first occurrence per file, capped)
    hits = VER_PAT.findall(txt[:400000])
    if hits:
        uniq = sorted(set(h.strip() for h in hits))[:8]
        ver_scan["text_hits"].append({"path": rel, "n_matches": len(hits),
                                      "samples": uniq})

# ------------------------------------------------ per-seed Delta-E extraction
# Delta-E convention (project archive):  dE = E[-1] - E[0]
runs = []


def note(name, rank, seed, E, src, batch, exp=""):
    if not isinstance(E, list) or not E:
        return
    first, last = E[0], E[-1]
    finite = all(isinstance(v, (int, float)) and v == v for v in E)
    rec = {"name": name, "rank": rank, "seed": seed, "E": E,
           "E0": first, "Efinal": last, "src_file": src, "batch": batch,
           "exp": exp, "all_finite": finite,
           "dE": (last - first) if finite else None,
           "nan_epochs": [i for i, v in enumerate(E)
                          if not (isinstance(v, (int, float)) and v == v)]}
    runs.append(rec)


# E2_results.json  (E2 / extra / sweep)
p = os.path.join(ROOT, "paper3", "scripts", "outputs", "experiments", "E2_results.json")
obj = load_json(p)
if isinstance(obj, dict):
    for batch in ("E2", "extra", "sweep"):
        for it in obj.get(batch, []):
            if not it.get("ok", False):
                continue
            note(it.get("name", ""), it.get("rank"), it.get("seed"),
                 it.get("E", []), "paper3/scripts/outputs/experiments/E2_results.json",
                 "E2_results." + batch, it.get("exp", ""))

# all_results.json
p = os.path.join(ROOT, "paper3", "scripts", "outputs", "experiments", "all_results.json")
obj = load_json(p)
if isinstance(obj, dict):
    def rec_walk(o, path):
        if isinstance(o, dict):
            if "E" in o and isinstance(o.get("E"), list):
                note(o.get("name", path), o.get("rank"), o.get("seed"),
                     o["E"], "paper3/scripts/outputs/experiments/all_results.json",
                     "all_results:" + path, o.get("exp", ""))
            for k, v in o.items():
                rec_walk(v, path + "/" + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                rec_walk(v, path + "[%d]" % i)
    rec_walk(obj, "")

# sample_size_results.json
p = os.path.join(ROOT, "paper3", "scripts", "outputs", "experiments", "sample_size_results.json")
obj = load_json(p)
if obj is not None:
    rec_walk_local = None
    def rec_walk_local(o, path):
        if isinstance(o, dict):
            if "E" in o and isinstance(o.get("E"), list):
                note(o.get("name", path), o.get("rank"), o.get("seed"), o["E"],
                     "paper3/scripts/outputs/experiments/sample_size_results.json",
                     "sample_size:" + path, o.get("exp", ""))
            for k, v in o.items():
                rec_walk_local(v, path + "/" + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                rec_walk_local(v, path + "[%d]" % i)
    rec_walk_local(obj, "")

# Qwen_results.json
p = os.path.join(ROOT, "paper3", "scripts", "outputs", "experiments", "Qwen_results.json")
obj = load_json(p)
if obj is not None:
    def rec_walk_q(o, path):
        if isinstance(o, dict):
            if "E" in o and isinstance(o.get("E"), list):
                note(o.get("name", path), o.get("rank"), o.get("seed"), o["E"],
                     "paper3/scripts/outputs/experiments/Qwen_results.json",
                     "qwen:" + path, o.get("exp", ""))
            for k, v in o.items():
                rec_walk_q(v, path + "/" + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                rec_walk_q(v, path + "[%d]" % i)
    rec_walk_q(obj, "")

# ------------------------------------------------------------ gamma artefacts
gamma_files = []
for p in sorted(walk_files()):
    b = os.path.basename(p).lower()
    if "gamma" in b and p.lower().endswith(".json"):
        gamma_files.append(os.path.relpath(p, ROOT))

out = {
    "meta": {
        "script": "tools/_p440_p3_recon.py",
        "purpose": "P3 I-group reconnaissance (task-11)",
        "dE_convention": "dE = E[-1] - E[0]  (final epoch minus pre-training baseline)",
        "search_dirs": [os.path.relpath(d, ROOT) for d in SEARCH_DIRS],
    },
    "n_runs_parsed": len(runs),
    "runs": runs,
    "gamma_artefacts": gamma_files,
    "version_record_scan": ver_scan,
    "inventory_size": len(inventory),
    "inventory": inventory,
}

dst = os.path.join(OUT, "p3_stats_recon.json")
with open(dst, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)

# console summary
print("runs parsed:", len(runs))
by = defaultdict(list)
for r in runs:
    by[(r["src_file"], r["batch"])].append(r)
for k in sorted(by):
    rr = by[k]
    print("  %-60s %-28s n=%d" % (k[0].split("/")[-1], k[1], len(rr)))
print("\nversion-record scan: json files scanned =", ver_scan["scanned_json_files"])
print("  key-level hits  =", len(ver_scan["key_hits"]))
print("  text-level hits =", len(ver_scan["text_hits"]))
print("\nwrote", dst)
