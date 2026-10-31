# -*- coding: utf-8 -*-
r"""Run the A3 main grid locally: four datasets x four provenance arms x three adaptation sites x three seeds.

Each cell is one call to train_lora_provenance.py on the frozen 10k-pair budget subset, with the modality diagnostics
included in the run JSON. Finished cells are skipped, so rerunning resumes.

Usage
  python run_full_grid.py --plan
  python run_full_grid.py --run [--datasets rsicd,rsitmd,nwpu_captions,dior_rsvg]
"""
import argparse
import io
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
RUNS = os.path.join(ROOT, "runs", "epoch_ablation")
LOG = os.path.join(RUNS, "grid_log.txt")

DATASETS = {
    "rsicd": "data/rsicd",
    "nwpu_captions": "data/nwpu_captions",
}
ARMS = ["human", "templated", "metadata"]
SITES = ["both"]
SEEDS = [0]
BUDGET = 10_000
EPOCHS = 6


def cells(datasets):
    for ds in datasets:
        images_root = os.path.join(ROOT, DATASETS[ds])
        for arm in ARMS:
            corpus = os.path.join(ROOT, "corpora", ds, "budgets", "%s_%d_pairs.jsonl" % (arm, BUDGET))
            if not os.path.exists(corpus):
                corpus = os.path.join(ROOT, "corpora", ds, arm + ".jsonl")
            for site in SITES:
                for seed in SEEDS:
                    yield "%s_%s_%d_%s_s%d" % (ds, arm, BUDGET, site, seed), corpus, images_root, site, seed


def plan(datasets):
    print("A3 epoch-ablation grid (6 epochs, two datasets, two arms x human)")
    print("  datasets %s | budget %d | epochs %d | seeds %s" % (datasets, BUDGET, EPOCHS, SEEDS))
    total = len(list(cells(datasets)))
    print("  cells %d | estimated wall time about %.1f hours at 2.3 min per cell" % (total, total * 2.3 / 60))
    return 0


def run(datasets):
    os.makedirs(RUNS, exist_ok=True)
    if not os.path.exists(LOG):
        io.open(LOG, "w", encoding="utf-8", newline="").write("A3 main grid started %s\n" % time.strftime("%Y-%m-%dT%H:%M:%S"))
    todo = list(cells(datasets))
    done = 0
    for name, corpus, images_root, site, seed in todo:
        out = os.path.join(RUNS, name)
        if os.path.exists(out + ".json"):
            done += 1
            continue
        if not os.path.exists(corpus):
            line = "MISSING corpus for %s: %s" % (name, corpus)
            print(line, flush=True)
            io.open(LOG, "a", encoding="utf-8", newline="").write(line + "\n")
            continue
        ds = name.split("_")[0] if name.startswith("rsicd") else name.split("_10")[0].rsplit("_", 0)[0]
        cmd = [PY, "-u", os.path.join(ROOT, "scripts", "train_lora_provenance.py"),
               "--corpus", corpus, "--images-root", images_root,
               "--site", site, "--seed", str(seed), "--epochs", str(EPOCHS), "--batch", "32",
               "--max-pairs", str(BUDGET), "--workers", "4", "--out-prefix", out]
        started = time.time()
        child_log = os.path.join(RUNS, "child_%s.log" % name)
        with io.open(LOG, "a", encoding="utf-8", newline="") as log:
            log.write("START %s %s\n" % (name, time.strftime("%Y-%m-%dT%H:%M:%S")))
            log.flush()
        with io.open(child_log, "wb") as child_out:
            proc = subprocess.run(cmd, stdout=child_out, stderr=subprocess.STDOUT)
        ok = proc.returncode == 0 and os.path.exists(out + ".json")
        line = "%s %s in %.1f min" % ("OK" if ok else "FAIL", name, (time.time() - started) / 60)
        print(line, flush=True)
        with io.open(LOG, "a", encoding="utf-8", newline="") as log:
            log.write(line + "\n")
            if not ok:
                log.write(proc.stdout.decode("utf-8", "replace")[-3000:] + "\n")
        done += 1

    rows = []
    for name, _, _, site, seed in todo:
        p = os.path.join(RUNS, name + ".json")
        if not os.path.exists(p):
            continue
        r = json.loads(io.open(p, encoding="utf-8").read())
        arm = name.split("_")[1] if not name.startswith(("nwpu", "dior")) else name.split("_")[2]
        rows.append({"cell": name, "site": r["site"], "seed": r["seed"],
                     "R@1_i2t": r["metrics"].get("R@1_i2t"), "R@1_t2i": r["metrics"].get("R@1_t2i"),
                     "R@5_i2t": r["metrics"].get("R@5_i2t"),
                     "modality_gap": r["metrics"].get("modality_gap"),
                     "peak_vram_gb": r["peak_vram_gb"], "wall_min": round(r["wall_seconds"] / 60, 2)})
    with io.open(os.path.join(RUNS, "summary.csv"), "w", encoding="utf-8", newline="") as f:
        cols = ["cell", "site", "seed", "R@1_i2t", "R@1_t2i", "R@5_i2t", "modality_gap", "peak_vram_gb", "wall_min"]
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join(str(r[c]) for c in cols) + "\n")
    print("cells done %d/%d | summary written" % (done, len(todo)))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--datasets", default="rsicd,nwpu_captions")
    args = ap.parse_args()
    datasets = [d.strip() for d in args.datasets.split(",") if d.strip()]
    if args.plan:
        return plan(datasets)
    if args.run:
        return run(datasets)
    print("use --plan or --run", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
