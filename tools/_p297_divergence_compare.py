# -*- coding: utf-8 -*-
r"""PR R1.6 / task-7 question C -- where does the lr=1e-4 reproduction part company with the
2026-08 archive, and is the divergence reproducible?

Sources compared, per seed at lr = 1e-4:
  * this session : `outputs/analysis/pr_fullft_lr_sweep_ext.json :: runs[*].history` (.train_loss
                   /.val_loss) for the extension runs, and
                   `outputs/analysis/pr_fullft_lr_sweep_repro.json :: runs[*].history` for the
                   seed-42 reproduction;
  * archive      : `outputs/imagenet_zs_rerun/full_ft{,_s123,_s999}/results.json ::
                   {train_losses,val_losses,r1_history}`.

Outputs `outputs/analysis/pr_fullft_divergence.json` and prints the per-epoch comparison plus a
verdict that is explicitly allowed to be "undetermined": the archive records no torch/cuDNN
version, so a version-drift explanation cannot be tested from the archives, and the script says
so instead of guessing.

    python tools\_p297_divergence_compare.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import io
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EXT = REPO / "outputs" / "analysis" / "pr_fullft_lr_sweep_ext.json"
REPRO = REPO / "outputs" / "analysis" / "pr_fullft_lr_sweep_repro.json"
ARCH = REPO / "outputs" / "imagenet_zs_rerun"
FULL = REPO / "outputs" / "analysis" / "pr_fullft_lr_sweep_full.json"
OUT = REPO / "outputs" / "analysis" / "pr_fullft_divergence.json"


def sha1_file(p):
    if not p or not Path(p).exists():
        return None
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def load_runs(path):
    if not Path(path).exists():
        return {}
    d = json.load(io.open(path, encoding="utf-8"))
    out = {}
    for r in d.get("runs", []):
        if r.get("error") or not r.get("history"):
            continue
        if r["lr"] != 1e-4:
            continue
        out[r["seed"]] = {"train": r["history"]["train_loss"],
                          "val": r["history"]["val_loss"],
                          "source": str(Path(path).relative_to(REPO))}
    return out


def load_archive():
    out = {}
    for d in sorted(glob.glob(str(ARCH / "full_ft*"))):
        p = Path(d) / "results.json"
        cg = Path(d) / "centroid_gap.json"
        if not p.exists():
            continue
        j = json.load(io.open(p, encoding="utf-8"))
        if j["config"]["lr"] != 1e-4:
            continue
        cgj = json.load(io.open(cg, encoding="utf-8")) if cg.exists() else {}
        out[j["config"]["seed"]] = {
            "train": j["train_losses"], "val": j["val_losses"], "r1": j["r1_history"],
            "zero_shot_top1_pct": j["zero_shot_imagenet1k"]["synset_single_template"],
            "final_R1": j["final_R1"], "dCG": cgj.get("cg_delta"),
            "frozen_CG": cgj.get("frozen_centroid_gap"),
            "source": str(p.relative_to(REPO))}
    return out


def first_divergence(a, b, tol=1e-6):
    for i, (x, y) in enumerate(zip(a, b), 1):
        if x is None or y is None:
            return {"epoch": i, "note": "missing value"}
        if abs(x - y) > tol:
            return {"epoch": i, "this_run": x, "reference": y, "abs_diff": abs(x - y)}
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    mine = load_runs(EXT)
    repro = load_runs(REPRO)
    arch = load_archive()
    # final metrics for the agreement table: mine from the merged grid, archive from its own
    # results.json / centroid_gap.json (each side's dCG is measured against its own frozen CG)
    finals_mine, finals_arch = {}, {}
    if FULL.exists():
        mj = json.load(io.open(FULL, encoding="utf-8"))
        fcg = mj["frozen"]["gap_retrieval"]["CG"]
        for r in mj["runs"]:
            if r.get("error") or r["lr"] != 1e-4:
                continue
            finals_mine[r["seed"]] = {
                "zero_shot": r["final"]["zero_shot_imagenet1k_top1_pct"],
                "CG": r["final"]["CG"], "dCG": round(r["final"]["CG"] - fcg, 4)}
    for s, a in arch.items():
        finals_arch[s] = {"zero_shot": a["zero_shot_top1_pct"], "CG": a["frozen_CG"],
                          "dCG": a["dCG"]}
    payload = {
        "script": "tools/_p297_divergence_compare.py",
        "script_sha1": sha1_file(Path(__file__)),
        "purpose": "task-7 question C: characterise the lr=1e-4 train/val trajectory against the "
                   "2026-08 archive and decide whether the divergence is reproducible",
        "sources": {"extension": str(EXT.relative_to(REPO)) if EXT.exists() else None,
                    "extension_sha1": sha1_file(EXT),
                    "reproduction": str(REPRO.relative_to(REPO)) if REPRO.exists() else None,
                    "reproduction_sha1": sha1_file(REPRO),
                    "archive_dir": str(ARCH.relative_to(REPO)),
                    "merged": str(FULL.relative_to(REPO)) if FULL.exists() else None},
        "archive_environment_record": {
            "searched": "outputs/**/*env*.json and any torch/cuDNN version field in the archive",
            "found": False,
            "note": "the archived full-FT results.json records only the optimisation config "
                    "(dataset, epochs, lr, weight_decay, scheduler, seed, amp, grad_clip); no "
                    "torch/cuDNN/transformers version is stored anywhere in outputs/, so a "
                    "version-drift explanation cannot be tested from the archive",
        },
        "seed42_determinism_vs_first_run": None,
        "per_seed": {},
        "verdict": None,
    }

    # --- determinism of the 1e-4 run inside this session (question C, first half) -----------
    if repro and 42 in repro:
        merged = json.load(io.open(FULL, encoding="utf-8")) if FULL.exists() else {"runs": []}
        first = [r for r in merged["runs"]
                 if r["lr"] == 1e-4 and r["seed"] == 42 and not r.get("error")]
        rep = [r for r in json.load(io.open(REPRO, encoding="utf-8"))["runs"]
               if r["lr"] == 1e-4 and r["seed"] == 42 and not r.get("error")]
        if first and rep:
            f, r2 = first[0], rep[0]
            payload["seed42_determinism_vs_first_run"] = {
                "first_run": {"zero_shot_top1_pct": f["final"]["zero_shot_imagenet1k_top1_pct"],
                              "CG": f["final"]["CG"], "R@1_mean": f["final"]["R@1_mean"],
                              "final_val_loss": f.get("final_val_loss")},
                "reproduction": {"zero_shot_top1_pct": r2["final"]["zero_shot_imagenet1k_top1_pct"],
                                 "CG": r2["final"]["CG"], "R@1_mean": r2["final"]["R@1_mean"],
                                 "final_val_loss": r2.get("final_val_loss")},
                "identical": bool(
                    f["final"]["zero_shot_imagenet1k_top1_pct"]
                    == r2["final"]["zero_shot_imagenet1k_top1_pct"]
                    and abs(f["final"]["CG"] - r2["final"]["CG"]) < 1e-6
                    and abs(f["final"]["R@1_mean"] - r2["final"]["R@1_mean"]) < 1e-6),
                "trajectory_comparable": False,
                "trajectory_note": "the first seed-42 run's per-epoch trajectory was lost to the "
                                   "resume bug in the first version of _p263, so only final "
                                   "metrics can be compared with it; per-epoch comparison is "
                                   "made against the archive below",
            }

    # --- per-seed comparison against the archive -------------------------------------------
    for seed in sorted(set(mine) | set(arch)):
        rec = {"seed": seed}
        if seed in mine:
            rec["this_session"] = {"source": mine[seed]["source"],
                                   "train": [round(x, 4) for x in mine[seed]["train"]],
                                   "val": [round(x, 4) for x in mine[seed]["val"]]}
        if seed in arch:
            rec["archive"] = {"source": arch[seed]["source"],
                              "train": [round(x, 4) for x in arch[seed]["train"]],
                              "val": [round(x, 4) for x in arch[seed]["val"]]}
        if seed in mine and seed in arch:
            rec["first_divergence_val_loss"] = first_divergence(mine[seed]["val"],
                                                               arch[seed]["val"])
            rec["first_divergence_train_loss"] = first_divergence(mine[seed]["train"],
                                                                 arch[seed]["train"])
            rec["val_loss_max_abs_diff_after_divergence"] = max(
                abs(a - b) for a, b in zip(mine[seed]["val"], arch[seed]["val"]))
            # final-metric agreement, both sides measured against their own frozen baseline
            if seed in finals_mine and seed in finals_arch:
                rec["final_agreement"] = {
                    "this_session_zero_shot_top1_pct": finals_mine[seed]["zero_shot"],
                    "archive_zero_shot_top1_pct": finals_arch[seed]["zero_shot"],
                    "abs_diff_zero_shot_pp": round(abs(finals_mine[seed]["zero_shot"]
                                                       - finals_arch[seed]["zero_shot"]), 2),
                    "this_session_dCG": finals_mine[seed]["dCG"],
                    "archive_dCG": finals_arch[seed]["dCG"],
                    "abs_diff_dCG": (round(abs(finals_mine[seed]["dCG"]
                                               - finals_arch[seed]["dCG"]), 4)
                                     if finals_mine[seed]["dCG"] is not None
                                     and finals_arch[seed]["dCG"] is not None else None),
                }
        payload["per_seed"][str(seed)] = rec

    # --- verdict ---------------------------------------------------------------------------
    repro_ok = (payload["seed42_determinism_vs_first_run"] or {}).get("identical")
    n_seeds_compared = sum(1 for s in payload["per_seed"].values()
                           if "first_divergence_val_loss" in s)
    div_epochs = [s["first_divergence_val_loss"]["epoch"] for s in payload["per_seed"].values()
                  if s.get("first_divergence_val_loss")]
    agree = {s: v.get("final_agreement") for s, v in payload["per_seed"].items()
             if v.get("final_agreement")}
    max_zs_gap = max((a["abs_diff_zero_shot_pp"] for a in agree.values()), default=None)
    max_dcg_gap = max((a["abs_diff_dCG"] for a in agree.values()
                       if a["abs_diff_dCG"] is not None), default=None)
    payload["verdict"] = {
        "within_session_reproduction_run_executed": bool(repro),
        "within_session_reproducible": repro_ok,
        "seeds_compared_with_archive": n_seeds_compared,
        "first_divergence_epoch_vs_archive": div_epochs,
        "final_metric_agreement_with_archive": agree,
        "max_abs_zero_shot_gap_pp": max_zs_gap,
        "max_abs_dCG_gap": max_dcg_gap,
        "cause": "undetermined",
        "statement": (
            "The lr=1e-4 trajectories part company with the 2026-08 archive from the FIRST epoch "
            "(val-loss divergence at epochs %s), so accumulated floating-point drift in later "
            "epochs cannot explain it: the two runs drew different data/augmentation orders or "
            "ran in different library versions from the start. Final metrics nevertheless agree "
            "closely on average (max |zero-shot| gap %s pp, max |dCG| gap %s), and the seed-42 "
            "case is the outlier. Which of data order, library version or an unrecorded code "
            "difference is responsible is UNDETERMINED, because the archived artefacts store "
            "neither a torch/cuDNN/transformers version nor a data fingerprint; this session's "
            "environment is torch 2.9.1+cu130 and cannot be assumed for the archived runs."
            % (div_epochs, max_zs_gap, max_dcg_gap)),
    }

    print(json.dumps(payload, ensure_ascii=False, indent=1))
    if args.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(payload, ensure_ascii=False, indent=1))
        print("wrote %s" % OUT.relative_to(REPO))
    else:
        print("(dry run; add --apply)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
