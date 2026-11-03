# -*- coding: utf-8 -*-
"""
Seed the parameter-noise-sensitivity test (forward passes only) and aggregate.

Why: outputs/noise_sensitivity.json is a single unseeded draw, and the review noted that at
sigma = 0.003 the vision/text ordering reverses, so "vision noise degrades retrieval 2.6x more
than text noise" rested on one sample.  This runs part [A] of
paper/scripts/noise_sensitivity.py several times with fixed seeds and reports mean +/- sd per
sigma plus the ratio at each sigma.

Part [B] of that script is NOT run: it retrains models and would overwrite
outputs/effective_rank_tracking.json, which is archived evidence for a different finding.

Outputs: outputs/noise_seeds/seed<SEED>.json (per-seed raw)
         outputs/noise_sensitivity_seeds.json (aggregate)
         outputs/noise_sensitivity_pre_seed.json (archive of the original single draw)
"""
import importlib.util
import io
import json
import os
import shutil
import sys
import time

import numpy as np

ROOT = r"D:\Realdesktop\Wan\Important\New"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ["HF_HUB_OFFLINE"] = "1"

import torch  # noqa: E402

SEEDS = [42, 123, 456]
SCRIPT = os.path.join(ROOT, "paper", "scripts", "noise_sensitivity.py")
RAW = os.path.join(ROOT, "outputs", "noise_sensitivity.json")
PRE = os.path.join(ROOT, "outputs", "noise_sensitivity_pre_seed.json")
PER = os.path.join(ROOT, "outputs", "noise_seeds")
AGG = os.path.join(ROOT, "outputs", "noise_sensitivity_seeds.json")


def load_module():
    spec = importlib.util.spec_from_file_location("noise_mod", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)          # top level only; main() is guarded by __name__
    return mod


def main():
    if os.path.exists(RAW) and not os.path.exists(PRE):
        shutil.copy2(RAW, PRE)
        print("archived the original single draw -> outputs/noise_sensitivity_pre_seed.json")
    os.makedirs(PER, exist_ok=True)
    mod = load_module()
    print("module loaded; device=%s" % mod.DEVICE)

    runs = []
    for seed in SEEDS:
        torch.manual_seed(seed)
        np.random.seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        t0 = time.time()
        res, base = mod.run_noise_sensitivity_test()
        shutil.copy2(RAW, os.path.join(PER, "seed%d.json" % seed))
        runs.append({"seed": seed, "baseline_R1": base,
                     "vision": res["Vision"], "text": res["Text"],
                     "elapsed_sec": round(time.time() - t0, 1)})
        print("[seed %d] baseline R@1 %.4f  (%.0f s)" % (seed, base, runs[-1]["elapsed_sec"]))

    sigmas = [row[0] for row in runs[0]["vision"]]
    agg = {"seeds": SEEDS, "sigmas": sigmas, "per_sigma": {}}
    print("\n%-8s %-22s %-22s %-10s" % ("sigma", "vision drop %", "text drop %", "ratio v/t"))
    for i, s in enumerate(sigmas):
        v = [r["vision"][i][2] for r in runs]
        t = [r["text"][i][2] for r in runs]
        vm, vd = float(np.mean(v)), float(np.std(v, ddof=1)) if len(v) > 1 else 0.0
        tm, td = float(np.mean(t)), float(np.std(t, ddof=1)) if len(t) > 1 else 0.0
        ratio = vm / tm if abs(tm) > 1e-9 else float("nan")
        agg["per_sigma"]["%.4f" % s] = {
            "vision_drop_mean": round(vm, 3), "vision_drop_sd": round(vd, 3),
            "text_drop_mean": round(tm, 3), "text_drop_sd": round(td, 3),
            "ratio": round(ratio, 3) if np.isfinite(ratio) else None,
            "n_seeds_vision_gt_text": int(sum(1 for a, b in zip(v, t) if a > b)),
        }
        print("%-8.4f %-22s %-22s %-10s" % (
            s, "%.2f +/- %.2f" % (vm, vd), "%.2f +/- %.2f" % (tm, td),
            "%.2fx" % ratio if np.isfinite(ratio) else "-"))
    agg["runs"] = runs
    with io.open(AGG, "w", encoding="utf-8") as fh:
        json.dump(agg, fh, indent=2, ensure_ascii=False)
    print("\nwrote %s" % AGG)
    return 0


if __name__ == "__main__":
    sys.exit(main())
