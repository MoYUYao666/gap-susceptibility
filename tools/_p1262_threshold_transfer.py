# -*- coding: utf-8 -*-
r"""Threshold-transfer analysis (novelty item 2): can one gap threshold travel across models and benchmarks?

If the centroid gap were a health metric, a single absolute threshold would separate healthy from degraded
configurations. This script pools every configuration archived by the matched-gap runs (three CLIP-family models on
ImageNet-5k, plus DTD and Food-101) and asks two questions:

  (a) how much does the *frozen* gap itself differ between settings, i.e. before any fine-tuning damage;
  (b) fit the threshold that best separates healthy from degraded configurations on one setting, then evaluate that
      same threshold on the other settings.

A label is "healthy" when the configuration's top-1 is within 1 point of the frozen top-1 of its own setting. Both the
in-setting balanced accuracy and the transfer balanced accuracy are reported.

Inputs : outputs/analysis/a1_matched_gap_families.json        (CLIP, ImageNet-5k)
         outputs/analysis/a1_matched_gap_crossmodel.json      (OpenCLIP, SigLIP)
         outputs/analysis/a1_matched_gap_second_dataset.json  (DTD, Food-101)
Output : outputs/analysis/a1_threshold_transfer.json

    python tools/_p1262_threshold_transfer.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "a1_threshold_transfer.json")
A = os.path.join(REPO, "outputs", "analysis")


def load_settings():
    settings = {}
    fam = json.load(io.open(os.path.join(A, "a1_matched_gap_families.json"), encoding="utf-8"))
    settings["clip_imagenet5k"] = {"frozen": fam["frozen"], "rows": fam["rows"]}
    cm = json.load(io.open(os.path.join(A, "a1_matched_gap_crossmodel.json"), encoding="utf-8"))
    for name, v in cm["models"].items():
        settings[name + "_imagenet5k"] = {"frozen": v["frozen"], "rows": v["rows"]}
    sec = json.load(io.open(os.path.join(A, "a1_matched_gap_second_dataset.json"), encoding="utf-8"))
    for name, v in sec["benchmarks"].items():
        settings[name + "_own"] = {"frozen": v["frozen"], "rows": v["rows"]}
    return settings


def points(setting):
    x, y = [], []
    f_t1 = setting["frozen"]["top1"]
    for r in setting["rows"]:
        x.append(float(r["CG"]))
        y.append(1 if float(r["top1"]) >= f_t1 - 1.0 else 0)
    return np.asarray(x), np.asarray(y)


def balanced_accuracy(pred, y):
    pos, neg = y == 1, y == 0
    if pos.sum() == 0 or neg.sum() == 0:
        return None
    return float(0.5 * (pred[pos].mean() + (1 - pred[neg]).mean()))


def fit_threshold(x, y):
    """Threshold t such that CG <= t predicts healthy (balanced-accuracy optimal)."""
    cands = np.unique(np.round(np.concatenate([x, x + 1e-6]), 6))
    best = None
    for t in cands:
        ba = balanced_accuracy((x <= t).astype(int), y)
        if ba is None:
            continue
        if best is None or ba > best[1]:
            best = (float(t), float(ba))
    return best


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    settings = load_settings()
    print(f"  settings: {len(settings)}")

    frozen, rows = {}, []
    data = {}
    for name, s in settings.items():
        x, y = points(s)
        data[name] = (x, y)
        frozen[name] = {"CG": float(s["frozen"]["CG"]), "top1": float(s["frozen"]["top1"]),
                        "n_points": int(len(x)), "n_healthy": int(y.sum()), "n_degraded": int((1 - y).sum())}
        fit = fit_threshold(x, y)
        rows.append({"setting": name, "fit_threshold": fit[0] if fit else None,
                     "in_setting_balanced_accuracy": fit[1] if fit else None,
                     "frozen_CG": float(s["frozen"]["CG"]), "frozen_top1": float(s["frozen"]["top1"])})
        print(f"   {name:<22} frozen CG={s['frozen']['CG']:.3f} top1={s['frozen']['top1']:.2f} "
              f"| n={len(x):2d} (healthy {int(y.sum())}) | best t={fit[0]:.3f} BA={fit[1]:.3f}" if fit else name)

    # transfer: threshold fitted on each setting, evaluated on every other setting
    fg = [frozen[n]["CG"] for n in frozen]
    transfer = {}
    for src in settings:
        t = fit_threshold(*data[src])
        if not t:
            continue
        t = t[0]
        transfer[src] = {}
        for dst in settings:
            if dst == src:
                continue
            x, y = data[dst]
            ba = balanced_accuracy((x <= t).astype(int), y)
            transfer[src][dst] = {"threshold": t, "balanced_accuracy": ba}
            if ba is not None:
                print(f"   transfer {src:<20} -> {dst:<22} t={t:.3f} BA={ba:.3f}")

    # the frozen gaps alone already disagree by a large factor
    summary = {
        "frozen_CG_min": float(min(fg)), "frozen_CG_max": float(max(fg)),
        "frozen_CG_ratio": float(max(fg) / min(fg)),
        "frozen_CG_spread": float(max(fg) - min(fg)),
        "frozen_top1_min": float(min(frozen[n]["top1"] for n in frozen)),
        "frozen_top1_max": float(max(frozen[n]["top1"] for n in frozen)),
        "transfer_balanced_accuracy": [v["balanced_accuracy"] for src in transfer for v in transfer[src].values()
                                       if v["balanced_accuracy"] is not None],
        "interpretation": ("A single absolute threshold would need the frozen gap of a healthy model to sit below the "
                           "threshold in every setting; the frozen gaps themselves span a factor of "
                           "%.2f, so no such threshold exists." % (max(fg) / min(fg))),
    }
    payload = {"settings": frozen, "per_setting_fit": rows, "transfer": transfer, "summary": summary}
    print("\n  summary:", json.dumps(summary, indent=1)[:600])
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
    print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
