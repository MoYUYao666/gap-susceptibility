# -*- coding: utf-8 -*-
"""
A properly controlled version of the parameter-noise test (forward passes only).

Problem with what the paper had: the archived evaluation is a single unseeded draw taken on a
validation subset that is REDRAWN every run (sample_ratio split), so the baseline moves
between 0.685 and 0.695 and the vision/text comparison is not paired.  Three seeded re-runs on
that protocol gave vision 2.15% +/- 4.41 against text -0.01% +/- 1.93, i.e. no stable ordering.

This script removes the confound: the validation loader is built ONCE and reused for every
condition, so all measurements are on the same images, and only the Gaussian noise is seeded.
sigma = 0 is included as a control and must reproduce the baseline exactly.

If the ordering survives here at a given sigma, the paper can keep a corrected form of the
claim for that sigma; if it does not, the deletion stands.

Output: outputs/noise_fixed_subset.json
"""
import importlib.util
import io
import json
import os
import sys
import time

import numpy as np

ROOT = r"D:\Realdesktop\Wan\Important\New"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ["HF_HUB_OFFLINE"] = "1"

import torch  # noqa: E402

SCRIPT = os.path.join(ROOT, "paper", "scripts", "noise_sensitivity.py")
OUT = os.path.join(ROOT, "outputs", "noise_fixed_subset.json")
SEEDS = [42, 123, 456, 789, 1024]
SIGMAS = [0.0, 0.003, 0.01, 0.03, 0.1]


def load_module():
    spec = importlib.util.spec_from_file_location("noise_mod", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    mod = load_module()
    from transformers import CLIPModel, CLIPProcessor
    from dataset import create_dataloaders

    torch.manual_seed(0)
    np.random.seed(0)
    _, val_loader, _ = create_dataloaders("flickr30k", ".", batch_size=64, max_samples=2000)
    proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", local_files_only=True)
    print("fixed validation loader built once; device=%s" % mod.DEVICE)

    base_model = CLIPModel.from_pretrained(
        "openai/clip-vit-base-patch32", local_files_only=True).to(mod.DEVICE).eval()
    baseline = mod.compute_retrieval_metrics(base_model, proc, val_loader)["R@1"]
    del base_model
    print("baseline R@1 on the fixed subset: %.4f" % baseline)

    rows = []
    for seed in SEEDS:
        for encoder in ("vision_model", "text_model"):
            for sigma in SIGMAS:
                torch.manual_seed(seed)
                np.random.seed(seed)
                model = CLIPModel.from_pretrained(
                    "openai/clip-vit-base-patch32", local_files_only=True).to(mod.DEVICE).eval()
                n = mod.inject_noise_to_encoder(model, encoder, sigma)
                r1 = mod.compute_retrieval_metrics(model, proc, val_loader)["R@1"]
                drop = (baseline - r1) / baseline * 100
                rows.append({"seed": seed,
                             "encoder": "vision" if encoder == "vision_model" else "text",
                             "sigma": sigma, "n_injected": n,
                             "R1": round(r1, 4), "drop_pct": round(drop, 3)})
                del model
            print("  seed %d done" % seed)

    agg = {"baseline_R1_fixed_subset": baseline, "seeds": SEEDS, "sigmas": SIGMAS,
           "rows": rows, "paired": {}}
    print("\n%-8s %-18s %-18s %-10s %-12s %s" %
          ("sigma", "vision drop %", "text drop %", "ratio", "paired diff", "v>t seeds"))
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
        print("%-8.3f %-18s %-18s %-10s %-12s %d/%d" % (
            s, "%.2f +/- %.2f" % (v.mean(), v.std(ddof=1)),
            "%.2f +/- %.2f" % (t.mean(), t.std(ddof=1)),
            ("%.2fx" % ratio) if ratio else "-",
            "%+.2f +/- %.2f" % (d.mean(), d.std(ddof=1)),
            int((d > 0).sum()), len(SEEDS)))

    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(agg, fh, indent=2, ensure_ascii=False)
    print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
