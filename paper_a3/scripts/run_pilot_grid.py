# -*- coding: utf-8 -*-
r"""Run the A3 overnight pilot grid locally: RSICD at 10k pairs, four provenance arms, three adaptation sites, three seeds.

Each cell is one call to train_lora_provenance.py; finished cells are skipped, so rerunning resumes. The driver writes a
small summary CSV at the end and keeps a log line per cell.

Usage
  python run_pilot_grid.py --plan
  python run_pilot_grid.py --run
"""
import argparse
import io
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
PY = sys.executable
RUNS = os.path.join(ROOT, "runs", "pilot_rsicd_10k")
LOG = os.path.join(RUNS, "pilot_log.txt")

ARMS = ["human", "templated", "segmented", "metadata"]
SITES = ["vision", "text", "both"]
SEEDS = [0, 1, 2]
DATASET = "rsicd"
BUDGET = 10_000
EPOCHS = 2


def cells():
    for arm in ARMS:
        corpus = os.path.join(ROOT, "corpora", DATASET, "budgets", "%s_%d_pairs.jsonl" % (arm, BUDGET))
        if not os.path.exists(corpus):
            corpus = os.path.join(ROOT, "corpora", DATASET, arm + ".jsonl")
        for site in SITES:
            for seed in SEEDS:
                name = "%s_%d_%s_s%d" % (arm, BUDGET, site, seed)
                yield name, corpus, site, seed


def plan():
    print("A3 local pilot grid")
    print("  dataset %s | budget %d pairs | epochs %d | seeds %s" % (DATASET, BUDGET, EPOCHS, SEEDS))
    print("  arms %s | sites %s | cells %d" % (ARMS, SITES, len(list(cells()))))
    for name, corpus, site, seed in cells():
        print("   %-32s corpus=%s site=%s seed=%d" % (name, os.path.relpath(corpus, ROOT), site, seed))
    print("  estimated wall time: about 8-9 hours at 13-15 min per cell on the local 8 GB GPU")
    return 0


def run():
    os.makedirs(RUNS, exist_ok=True)
    if not os.path.exists(LOG):
        io.open(LOG, "w", encoding="utf-8", newline="").write("A3 pilot grid started %s\n" % time.strftime("%Y-%m-%dT%H:%M:%S"))
    todo = list(cells())
    done = 0
    for name, corpus, site, seed in todo:
        out = os.path.join(RUNS, name)
        if os.path.exists(out + ".json"):
            print("skip (done): %s" % name, flush=True)
            done += 1
            continue
        if not os.path.exists(corpus):
            line = "MISSING corpus for %s: %s" % (name, corpus)
            print(line, flush=True)
            io.open(LOG, "a", encoding="utf-8", newline="").write(line + "\n")
            continue
        cmd = [PY, os.path.join(ROOT, "scripts", "train_lora_provenance.py"),
               "--corpus", corpus, "--images-root", os.path.join(ROOT, "data", DATASET),
               "--site", site, "--seed", str(seed), "--epochs", str(EPOCHS), "--batch", "32",
               "--max-pairs", str(BUDGET), "--workers", "4", "--out-prefix", out]
        started = time.time()
        with io.open(LOG, "a", encoding="utf-8", newline="") as log:
            log.write("START %s %s\n" % (name, time.strftime("%Y-%m-%dT%H:%M:%S")))
            log.flush()
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        status = "OK" if proc.returncode == 0 and os.path.exists(out + ".json") else "FAIL"
        elapsed = time.time() - started
        line = "%s %s in %.1f min" % (status, name, elapsed / 60)
        print(line, flush=True)
        with io.open(LOG, "a", encoding="utf-8", newline="") as log:
            log.write(line + "\n")
            if status == "FAIL":
                log.write(proc.stdout.decode("utf-8", "replace")[-4000:] + "\n")
        done += 1

    rows = []
    for name, _, _, _ in todo:
        p = os.path.join(RUNS, name + ".json")
        if os.path.exists(p):
            r = json.loads(io.open(p, encoding="utf-8").read())
            rows.append({"cell": name, "arm": name.split("_")[0], "site": r["site"], "seed": r["seed"],
                         "R@1_i2t": r["metrics"].get("R@1_i2t"), "R@1_t2i": r["metrics"].get("R@1_t2i"),
                         "peak_vram_gb": r["peak_vram_gb"], "wall_min": round(r["wall_seconds"] / 60, 1)})
    summary = os.path.join(RUNS, "summary.csv")
    with io.open(summary, "w", encoding="utf-8", newline="") as f:
        f.write("cell,arm,site,seed,R@1_i2t,R@1_t2i,peak_vram_gb,wall_min\n")
        for r in rows:
            f.write("%s,%s,%s,%s,%s,%s,%s,%s\n" % (r["cell"], r["arm"], r["site"], r["seed"],
                                                   r["R@1_i2t"], r["R@1_t2i"], r["peak_vram_gb"], r["wall_min"]))
    print("cells done: %d/%d | summary: %s" % (done, len(todo), summary))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if args.plan:
        return plan()
    if args.run:
        return run()
    print("use --plan or --run", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
