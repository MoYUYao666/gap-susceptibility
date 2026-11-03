# -*- coding: utf-8 -*-
r"""Parallel runner for the A3 cloud supplements.

Cells are the same training script as everywhere else (paper_a3/scripts/train_lora_provenance.py); this runner only
schedules them, keeps per-cell logs, resumes by skipping existing JSON records, and writes a summary.

Phases
  l14         ViT-L/14: 4 arms x 2 corpora x 3 sites x 2 seeds = 48 cells, batch 8, 10k pairs
  fullcorpus  ViT-B/32: human + metadata x 2 corpora x 3 seeds, joint site, every image
  geol14      GeoRSCLIP-L/14 human vs metadata x 2 corpora x 2 seeds, joint site (optional)

Usage (on the cloud machine, from the a3 directory that contains scripts/, data/, corpora/)
  python run_cloud_suite.py --plan
  python run_cloud_suite.py --run --workers 2 --phases l14,fullcorpus
  python run_cloud_suite.py --verify
"""
import argparse
import glob
import io
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
RUNS = os.path.join(ROOT, "runs")
LOG = os.path.join(RUNS, "cloud_suite.log")

MODELS = {
    "b32": os.path.join(ROOT, "models", "RemoteCLIP-ViT-B-32.pt"),
    "l14": os.path.join(ROOT, "models", "RemoteCLIP-ViT-L-14.pt"),
    "geol14": os.path.join(ROOT, "models", "GeoRSCLIP-ViT-L-14.pt"),
}
ARMS4 = ["human", "segmented", "templated", "metadata"]
SITES = ["vision", "text", "both"]
CORPORA = ["rsicd", "nwpu_captions"]
IMAGES = {"rsicd": "data/rsicd", "nwpu_captions": "data/nwpu_captions"}


def corpora_path(dataset, arm):
    p = os.path.join(ROOT, "corpora", dataset, arm + ".jsonl")
    return p


def cells(phases):
    out = []
    if "l14" in phases:
        for ds in CORPORA:
            for arm in ARMS4:
                for site in (SITES if ds == "rsicd" else ["both"]):
                    for seed in (0,):
                        out.append({
                            "name": "l14_%s_%s_%s_s%d" % (ds, arm, site, seed),
                            "out": os.path.join("runs", "cloud_l14", "l14_%s_%s_%s_s%d" % (ds, arm, site, seed)),
                            "corpus": corpora_path(ds, arm), "images_root": os.path.join(ROOT, IMAGES[ds]),
                            "model": MODELS["l14"], "site": site, "seed": seed, "epochs": 2, "batch": 8,
                            "max_pairs": 10000, "one_per_image": arm == "human",
                        })
    if "fullcorpus" in phases:
        for ds in CORPORA:
            for arm in ("human", "metadata"):
                for seed in (0, 1, 2):
                    out.append({
                        "name": "full_%s_%s_s%d" % (ds, arm, seed),
                        "out": os.path.join("runs", "cloud_fullcorpus", "full_%s_%s_s%d" % (ds, arm, seed)),
                        "corpus": corpora_path(ds, arm), "images_root": os.path.join(ROOT, IMAGES[ds]),
                        "model": MODELS["b32"], "site": "both", "seed": seed, "epochs": 2, "batch": 32,
                        "max_pairs": 0, "one_per_image": arm == "human",
                    })
    if "fullextra" in phases:
        for ds in CORPORA:
            for arm in ("segmented", "templated", "humanrich"):
                for seed in (0, 1, 2):
                    out.append({
                        "name": "fullextra_%s_%s_s%d" % (ds, arm, seed),
                        "out": os.path.join("runs", "cloud_fullextra", "fullextra_%s_%s_s%d" % (ds, arm, seed)),
                        "corpus": corpora_path(ds, arm), "images_root": os.path.join(ROOT, IMAGES[ds]),
                        "model": MODELS["b32"], "site": "both", "seed": seed, "epochs": 2, "batch": 32,
                        "max_pairs": 0, "one_per_image": arm == "human",
                    })
    if "l14nwpu" in phases:
        for arm in ARMS4:
            for site in ("vision", "text"):
                out.append({
                    "name": "l14_nwpu_%s_%s_s0" % (arm, site),
                    "out": os.path.join("runs", "cloud_l14_nwpu", "l14_nwpu_%s_%s_s0" % (arm, site)),
                    "corpus": corpora_path("nwpu_captions", arm),
                    "images_root": os.path.join(ROOT, IMAGES["nwpu_captions"]),
                    "model": MODELS["l14"], "site": site, "seed": 0, "epochs": 2, "batch": 8,
                    "max_pairs": 10000, "one_per_image": arm == "human",
                })
    if "geol14" in phases:
        for ds in CORPORA:
            for arm in ("human", "metadata"):
                for seed in (0, 1):
                    out.append({
                        "name": "geol14_%s_%s_s%d" % (ds, arm, seed),
                        "out": os.path.join("runs", "cloud_geol14", "geol14_%s_%s_s%d" % (ds, arm, seed)),
                        "corpus": corpora_path(ds, arm), "images_root": os.path.join(ROOT, IMAGES[ds]),
                        "model": MODELS["geol14"], "site": "both", "seed": seed, "epochs": 2, "batch": 8,
                        "max_pairs": 10000, "one_per_image": arm == "human",
                    })
    return out


def plan(phases):
    cs = cells(phases)
    print("phases: %s | cells: %d" % (list(phases), len(cs)))
    for c in cs[:6]:
        print("   " + c["name"])
    if len(cs) > 6:
        print("   ... (%d more)" % (len(cs) - 6))
    print("estimated wall time with 2 workers: %.0f-%.0f min" % (len(cs) * 5 / 2, len(cs) * 9 / 2))
    return 0


def run(phases, workers):
    os.makedirs(LOG and os.path.dirname(LOG), exist_ok=True)
    todo = [c for c in cells(phases) if not os.path.exists(os.path.join(ROOT, c["out"] + ".json"))]
    print("cells to run: %d (of %d)" % (len(todo), len(cells(phases))), flush=True)
    if not todo:
        return 0
    running, done, failed = [], [], []
    queue = list(todo)
    while queue or running:
        while queue and len(running) < workers:
            c = queue.pop(0)
            cmd = [PY, "-u", os.path.join(ROOT, "scripts", "train_lora_provenance.py")]
            # spawn through a shell-free Popen
            args = cmd + ["--corpus", c["corpus"], "--images-root", c["images_root"], "--model", c["model"],
                          "--site", c["site"], "--seed", str(c["seed"]), "--epochs", str(c["epochs"]),
                          "--batch", str(c["batch"]), "--max-pairs", str(c["max_pairs"]),
                          "--workers", "16", "--out-prefix", os.path.join(ROOT, c["out"])]
            if c["one_per_image"]:
                args.append("--one-per-image")
            args.append("--cache-images")
            os.makedirs(os.path.dirname(os.path.join(ROOT, c["out"])), exist_ok=True)
            log_path = os.path.join(ROOT, "runs", "logs", c["name"] + ".log")
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            fh = io.open(log_path, "wb")
            proc = subprocess.Popen(args, stdout=fh, stderr=subprocess.STDOUT, cwd=ROOT)
            running.append({"cell": c, "proc": proc, "fh": fh, "t0": time.time()})
            print("start %s (running %d)" % (c["name"], len(running)), flush=True)
            with io.open(LOG, "a", encoding="utf-8", newline="") as f:
                f.write("START %s %s\n" % (c["name"], time.strftime("%H:%M:%S")))
        time.sleep(15)
        still = []
        for r in running:
            if r["proc"].poll() is None:
                still.append(r)
                continue
            ok = r["proc"].returncode == 0 and os.path.exists(os.path.join(ROOT, r["cell"]["out"] + ".json"))
            elapsed = (time.time() - r["t0"]) / 60
            print("%s %s in %.1f min" % ("OK" if ok else "FAIL", r["cell"]["name"], elapsed), flush=True)
            with io.open(LOG, "a", encoding="utf-8", newline="") as f:
                f.write("%s %s %.1f min\n" % ("OK" if ok else "FAIL", r["cell"]["name"], elapsed))
            (done if ok else failed).append(r["cell"]["name"])
            r["fh"].close()
        running = still
    print("done: %d | failed: %d" % (len(done), len(failed)), flush=True)
    return 0 if not failed else 1


def verify():
    problems = []
    for phase_dir in ("cloud_l14", "cloud_fullcorpus", "cloud_geol14"):
        d = os.path.join(ROOT, "runs", phase_dir)
        js = glob.glob(os.path.join(d, "*.json"))
        print("%-16s %d records" % (phase_dir, len(js)))
        for p in js:
            try:
                r = json.loads(io.open(p, encoding="utf-8").read())
                assert r["metrics"].get("R@1_i2t") is not None
                assert r["peak_vram_gb"] and r["peak_vram_gb"] > 0
            except Exception as e:
                problems.append((p, str(e)[:80]))
    if problems:
        print("PROBLEMS:", problems)
        return 1
    print("all records carry metrics and VRAM; safe to copy back")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--phases", default="l14,fullcorpus")
    args = ap.parse_args()
    phases = [p.strip() for p in args.phases.split(",") if p.strip()]
    if args.plan:
        return plan(phases)
    if args.run:
        return run(phases, args.workers)
    if args.verify:
        return verify()
    print("use --plan / --run / --verify", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
