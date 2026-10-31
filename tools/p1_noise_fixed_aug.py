# -*- coding: utf-8 -*-
"""
Parameter-noise test, second control pass: fix BOTH the image set and the augmentation draw.

What the first pass (tools/p1_noise_fixed_subset.py) got wrong
-------------------------------------------------------------
It built the validation loader once, but the loader it built evaluates a *train-transformed*
dataset: create_dataloaders passes split="train" when constructing the object (src/dataset.py:401)
and then random_split()s that train object into train/val/test (src/dataset.py:422).  So the
"val" transform is get_clip_transform(is_train=True) -> RandomHorizontalFlip + ColorJitter, which
consume Python's random module on every epoch.  On top of that, num_workers defaulted to 4 with
persistent_workers=True, so the draws happen inside long-lived worker processes that main-process
seeding cannot reach.

The sigma = 0 control exposed this: it must reproduce the baseline exactly, but it returned
0.675-0.695 against a baseline of 0.695 (1.01% +/- 1.09 apparent "drop" with no noise at all).

This pass removes the confound
------------------------------
1. num_workers=0, so the transform runs in this process (a deterministic prefix slice of the
   validation annotations and shuffle=False were already fixed).
2. Before every single evaluation - baseline and all conditions alike - the augmentation RNG is
   replayed with the same constant seed, so every condition sees byte-identical images.
3. The noise draw stays condition-specific: it is taken from the global torch RNG seeded with the
   run's seed *before* the augmentation replay, and inject_noise_to_encoder consumes a fixed
   number of randn_like calls, so the augmentation replay fully overwrites the RNG state that
   follows.

sigma = 0 is again the control and must now reproduce the baseline exactly.  If it does not, this
design is still confounded and no vision-versus-text claim may be drawn from it.

Output: outputs/noise_fixed_aug.json  (does not touch outputs/noise_fixed_subset.json)
"""
import importlib.util
import io
import json
import os
import random
import sys
import time

import numpy as np

ROOT = r"D:\Realdesktop\Wan\Important\New"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ["HF_HUB_OFFLINE"] = "1"

import torch  # noqa: E402

SCRIPT = os.path.join(ROOT, "paper", "scripts", "noise_sensitivity.py")
OUT = os.path.join(ROOT, "outputs", "noise_fixed_aug.json")
SEEDS = [42, 123, 456, 789, 1024]
SIGMAS = [0.0, 0.03, 0.1]
AUG_SEED = 20240917


def replay_augmentation_rng():
    """Make the augmentation draw identical for every evaluation in this script."""
    random.seed(AUG_SEED)
    np.random.seed(AUG_SEED)
    torch.manual_seed(AUG_SEED)


def load_module():
    spec = importlib.util.spec_from_file_location("noise_mod", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    mod = load_module()
    from transformers import CLIPModel, CLIPProcessor
    from dataset import create_dataloaders

    # num_workers=0 is the point of this pass: the transform must run in this process.
    _, val_loader, _ = create_dataloaders("flickr30k", ".", batch_size=64,
                                          max_samples=2000, num_workers=0)
    proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", local_files_only=True)
    print("loader built once, num_workers=0, augmentation seed fixed at %d" % AUG_SEED, flush=True)

    base_model = CLIPModel.from_pretrained(
        "openai/clip-vit-base-patch32", local_files_only=True).to(mod.DEVICE).eval()
    replay_augmentation_rng()
    baseline = mod.compute_retrieval_metrics(base_model, proc, val_loader)["R@1"]
    del base_model
    print("baseline R@1 on the fixed subset, fixed augmentation: %.4f" % baseline, flush=True)

    rows = []
    t0 = time.time()
    for seed in SEEDS:
        for encoder in ("vision_model", "text_model"):
            for sigma in SIGMAS:
                # 1) noise draw depends only on the run seed
                torch.manual_seed(seed)
                np.random.seed(seed)
                model = CLIPModel.from_pretrained(
                    "openai/clip-vit-base-patch32", local_files_only=True).to(mod.DEVICE).eval()
                n = mod.inject_noise_to_encoder(model, encoder, sigma)
                # 2) augmentation replayed identically for every condition
                replay_augmentation_rng()
                r1 = mod.compute_retrieval_metrics(model, proc, val_loader)["R@1"]
                drop = (baseline - r1) / baseline * 100
                rows.append({"seed": seed,
                             "encoder": "vision" if encoder == "vision_model" else "text",
                             "sigma": sigma, "n_injected": n,
                             "R1": round(r1, 4), "drop_pct": round(drop, 3)})
                del model
            print("  seed %d done  (%.1f min)" % (seed, (time.time() - t0) / 60), flush=True)

    zero = [r for r in rows if r["sigma"] == 0.0]
    # compare at the recorded precision: rows store round(R@1, 4), baseline is the raw float
    control_ok = all(abs(r["R1"] - round(baseline, 4)) < 1e-9 for r in zero)
    print("", flush=True)
    print("CONTROL (sigma=0 vs baseline %.4f): %s" % (
        baseline, "reproduced exactly on all %d runs" % len(zero) if control_ok else "FAILED"),
        flush=True)
    for r in zero:
        print("   %-7s seed %-5d R@1 %.4f" % (r["encoder"], r["seed"], r["R1"]), flush=True)

    agg = {"baseline_R1_fixed_subset": baseline, "seeds": SEEDS, "sigmas": SIGMAS,
           "aug_seed": AUG_SEED, "num_workers": 0, "rows": rows, "paired": {},
           "control_sigma0_reproduces_baseline": control_ok,
           "note": "val loader is a Subset of a train-transformed dataset (src/dataset.py:401,422); "
                   "augmentation replayed with a constant seed before every evaluation"}
    print("", flush=True)
    print("%-8s %-18s %-18s %-9s %-16s %s" % (
        "sigma", "vision drop %", "text drop %", "ratio", "paired diff", "v>t seeds"), flush=True)
    for s in SIGMAS:
        v = np.array([r["drop_pct"] for r in rows if r["encoder"] == "vision" and r["sigma"] == s])
        t = np.array([r["drop_pct"] for r in rows if r["encoder"] == "text" and r["sigma"] == s])
        d = v - t
        ratio = float(v.mean() / t.mean()) if abs(t.mean()) > 1e-9 else None
        try:
            from scipy import stats
            pval = float(stats.ttest_rel(v, t).pvalue)
        except ImportError:
            pval = None
        agg["paired"]["%.4f" % s] = {
            "vision_mean": round(float(v.mean()), 3), "vision_sd": round(float(v.std(ddof=1)), 3),
            "text_mean": round(float(t.mean()), 3), "text_sd": round(float(t.std(ddof=1)), 3),
            "ratio": round(ratio, 3) if ratio is not None else None,
            "paired_diff_mean": round(float(d.mean()), 3),
            "paired_diff_sd": round(float(d.std(ddof=1)), 3),
            "paired_t_p": round(pval, 4) if pval is not None else None,
            "n_seeds_vision_gt_text": int((d > 0).sum()),
        }
        print("%-8.3f %-18s %-18s %-9s %-16s %d/%d" % (
            s, "%.2f +/- %.2f" % (v.mean(), v.std(ddof=1)),
            "%.2f +/- %.2f" % (t.mean(), t.std(ddof=1)),
            ("%.2fx" % ratio) if ratio else "-",
            "%+.2f +/- %.2f" % (d.mean(), d.std(ddof=1)),
            int((d > 0).sum()), len(SEEDS)), flush=True)
        if pval is not None:
            print("         paired t-test p = %.4f" % pval, flush=True)

    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(agg, fh, indent=2, ensure_ascii=False)
    print("", flush=True)
    print("wrote %s" % OUT, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
