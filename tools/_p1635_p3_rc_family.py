#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P3 reviewer objection: is r_c a within-family quantity, and does AdaLoRA really bound us?

Two questions, both answered only from archives that exist on disk:

  1. --refit   Re-estimate the critical rank r_c *inside each backbone family separately*,
               from the archived alignment-energy-versus-rank curves, with a paired seed
               bootstrap.  Families and strata are declared below with the exact archive
               path and the exact field path each number comes from.  No value is inferred,
               interpolated across families, or taken from the manuscript.

  2. --adalora Build the boundary-condition table: every archived cell in which AdaLoRA
               (or a published-baseline allocation rule) is compared with the Gamma-guided
               rule on the same budget, reporting the per-cell difference, its sign, and
               the regime (learning rate, rank/block configuration, loss) under which the
               ordering reverses or fails to reverse.

Outputs (both written by this script, so the numbers cannot drift apart):

  outputs/analysis/p3_rc_family_boundary.json   meta / rc_by_family / stability /
                                                adalora_boundary / conclusion
  docs/p3_rc_boundary_text.md                   LaTeX-ready draft text, every number
                                                carrying its JSON field path

Conventions and guarantees
--------------------------
* dE := E[-1] - E[0], the archived convention
  (``p3_multiseed_family.json :: meta.dE_convention``).
* r_c is estimated as the zero of the mean dE-versus-rank curve, by linear interpolation
  between the two adjacent measured ranks whose means bracket zero.  Both the bracket
  [r_lo, r_hi] and the interpolated point are reported; a family with no sign change in
  the measured range is reported as exactly that, not as a large or small r_c.
* Bootstrap resamples *seed labels jointly across ranks* (paired), because the same seed
  labels appear at every rank in the paired strata.  Fixed RNG seed => rerun-stable.
* Every number this script prints is read back out of the JSON it has just written.
* Rerun stability: no wall-clock timestamps, sorted keys, fixed bootstrap seed.  Two
  consecutive runs produce byte-identical files.

Run:  python tools/_p1635_p3_rc_family.py --dry-run
      python tools/_p1635_p3_rc_family.py --refit --adalora
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from random import Random

REPO = Path(__file__).resolve().parents[1]
EXP = "paper3/scripts/outputs/experiments"
ANA = "outputs/analysis"

OUT_JSON = ANA + "/p3_rc_family_boundary.json"
OUT_MD = "docs/p3_rc_boundary_text.md"

N_BOOT = 20000
BOOT_SEED = 20261024
OPERATING_LR = 5e-5
ADALORA_FAMILY = "qwen2-vl-2b"          # the backbone the allocation study runs on

# --------------------------------------------------------------------------------------
# archive access -- every read is recorded so that meta.sources is exhaustive
# --------------------------------------------------------------------------------------


class Archive:
    """A JSON archive plus the list of field paths actually touched."""

    def __init__(self, rel: str):
        self.rel = rel
        p = REPO / rel
        if not p.exists():
            raise SystemExit("[p1635] missing archive: %s" % rel)
        with p.open(encoding="utf-8") as fh:
            self.data = json.load(fh)
        self.fields: list[str] = []

    def f(self, path: str):
        """Read `path` and record it.

        Paths are dot-separated, list indices are allowed, and a key that itself contains a dot
        (for example `exp_beta_paper_0.137`) is matched greedily as the longest key that exists.
        """
        self.fields.append(path)
        parts = path.split(".")
        node, i = self.data, 0
        while i < len(parts):
            if isinstance(node, list):
                node = node[int(parts[i])]
                i += 1
                continue
            if not isinstance(node, dict):
                raise SystemExit("[p1635] %s: field %s walks into a scalar" % (self.rel, path))
            for j in range(len(parts), i, -1):
                key = ".".join(parts[i:j])
                if key in node:
                    node = node[key]
                    i = j
                    break
            else:
                raise SystemExit("[p1635] %s has no field %s" % (self.rel, path))
        return node

    def record(self) -> dict:
        return {"path": self.rel, "fields": sorted(set(self.fields))}


# --------------------------------------------------------------------------------------
# small statistics helpers (numpy-free, deterministic)
# --------------------------------------------------------------------------------------


def rd(x, nd: int = 6):
    """Round derived floats so the archive is byte-stable across runs."""
    if x is None:
        return None
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    return round(float(x), nd)


def mean(vals):
    vals = list(vals)
    return sum(vals) / len(vals) if vals else None


def sd_sample(vals):
    vals = list(vals)
    if len(vals) < 2:
        return None
    m = mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


# Student t two-sided 95 % critical values for the small df we actually use.
T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
       8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145,
       15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086}


def percentile(sorted_vals, q):
    """Linear-interpolation percentile; deterministic."""
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * q
    lo = int(math.floor(k))
    hi = int(math.ceil(k))
    if lo == hi:
        return sorted_vals[lo]
    return sorted_vals[lo] * (hi - k) + sorted_vals[hi] * (k - lo)


def boot_ci(values_sorted):
    return [rd(percentile(values_sorted, 0.025)), rd(percentile(values_sorted, 0.975))]


def t_ci95(vals):
    n = len(vals)
    if n < 2:
        return None
    m, s = mean(vals), sd_sample(vals)
    if s is None or n - 1 not in T95:
        return None
    half = T95[n - 1] * s / math.sqrt(n)
    return [rd(m - half), rd(m + half)]


# --------------------------------------------------------------------------------------
# the crossing estimator
# --------------------------------------------------------------------------------------


def fit_crossing(curve: dict, ranks=None, units=None) -> dict:
    """Zero crossing of the mean dE-versus-rank curve.

    curve : {unit_label: {rank: dE}}
    Returns the bracket, the interpolated point, the local-OLS point when at least three
    points are available, and the forward/reverse crossing lists.
    """
    units = sorted(curve) if units is None else list(units)
    present = [u for u in units if curve.get(u)]
    if not present:
        return {"status": "no_data"}
    all_ranks = sorted({r for u in present for r in curve[u]})
    ranks = all_ranks if ranks is None else [r for r in ranks if r in all_ranks]
    means = {}
    counts = {}
    for r in ranks:
        vals = [curve[u][r] for u in present if r in curve[u]]
        counts[r] = len(vals)
        means[r] = mean(vals)
    forward, reverse = [], []
    for a, b in zip(ranks, ranks[1:]):
        ma, mb = means[a], means[b]
        if ma < 0 <= mb:
            t = (-ma / (mb - ma)) if mb != ma else 0.0
            forward.append({"bracket": [a, b], "point": rd(a + t * (b - a)),
                            "mean_lo": rd(ma), "mean_hi": rd(mb)})
        elif ma >= 0 > mb:
            t = (ma / (ma - mb)) if ma != mb else 0.0
            reverse.append({"bracket": [a, b], "point": rd(a + t * (b - a)),
                            "mean_lo": rd(ma), "mean_hi": rd(mb)})
    signs = [("pos" if means[r] > 0 else "neg" if means[r] < 0 else "zero") for r in ranks]
    out = {
        "n_units": len(present),
        "units": present,
        "ranks": ranks,
        "mean_by_rank": {str(r): rd(means[r]) for r in ranks},
        "n_by_rank": {str(r): counts[r] for r in ranks},
        "forward_crossings": forward,
        "reverse_crossings": reverse,
        "sign_pattern_by_rank": signs,
    }
    if not forward:
        out["status"] = "no_crossing_in_range"
        out["crossing_point"] = None
        out["crossing_bracket"] = None
        out["sign_of_all_means"] = ("all_positive" if all(v > 0 for v in means.values())
                                    else "all_negative" if all(v < 0 for v in means.values())
                                    else "mixed_without_forward_step")
        out["min_rank_measured"] = ranks[0]
        out["max_rank_measured"] = ranks[-1]
        return out
    first = forward[0]
    out["status"] = "crossing" if len(forward) == 1 else "multiple_crossings"
    out["crossing_point"] = first["point"]
    out["crossing_bracket"] = list(first["bracket"])
    if len(forward) > 1:
        out["secondary_forward_crossings"] = forward[1:]
    # local OLS through the three ranks centred on the bracket, when available
    lo, hi = first["bracket"]
    idx = ranks.index(hi)
    win = ranks[max(0, idx - 2): min(len(ranks), idx + 2)]
    if len(win) >= 3:
        xs = [float(r) for r in win]
        ys = [means[r] for r in win]
        mx, my = mean(xs), mean(ys)
        den = sum((x - mx) ** 2 for x in xs)
        if den > 0:
            slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den
            if slope > 0:
                out["crossing_point_local_ols"] = rd(mx - my / slope)
                out["local_ols_window"] = win
    return out


def boot_crossing(curve: dict, unit: str, ranks, n_boot=N_BOOT, rng_seed=BOOT_SEED) -> dict:
    """Percentile CI of the crossing point, resampling units jointly across ranks."""
    units = sorted(curve)
    if len(units) < 2:
        return {"n_boot": 0, "n_boot_with_crossing": 0, "ci95": None,
                "reason": "fewer than two %ss in this stratum, so a resampling interval is undefined" % unit}
    if not all(set(curve[u]) >= set(ranks) for u in units):
        return {"n_boot": 0, "n_boot_with_crossing": 0, "ci95": None,
                "reason": "seed labels are not shared by every rank; paired resampling would not be valid"}
    rng = Random(rng_seed)
    pts = []
    for _ in range(n_boot):
        draw = [units[rng.randrange(len(units))] for _ in units]
        sub = {}
        for i, u in enumerate(draw):
            sub["%s#%d" % (u, i)] = curve[u]
        fit = fit_crossing(sub, ranks=ranks)
        if fit.get("crossing_point") is not None:
            pts.append(fit["crossing_point"])
    pts.sort()
    return {
        "n_boot": n_boot,
        "n_boot_with_crossing": len(pts),
        "ci95": boot_ci(pts) if len(pts) >= 2 else None,
        "point_bootstrap_median": rd(percentile(pts, 0.5)) if pts else None,
        "stable": bool(len(pts) >= 0.95 * n_boot),
    }


# --------------------------------------------------------------------------------------
# strata: one row per archived energy-versus-rank curve
# --------------------------------------------------------------------------------------


def _dE_from_E(E, rel, where):
    """dE = E[-1] - E[0]; non-finite entries are refused, not repaired."""
    vals = [v for v in E]
    if not vals:
        raise SystemExit("[p1635] %s %s: empty E" % (rel, where))
    if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in vals):
        return None
    return float(vals[-1]) - float(vals[0])


def s_llava_cloud10():
    """LLaVA-1.5-7B, blank-image protocol, 3 epochs, ten seeds, r=3..8."""
    ranks = [3, 4, 5, 6, 7, 8]
    seeds = [7, 17, 27, 37, 42, 123, 456, 789, 999, 1024]
    excl = ("partial", "imgs", "_e1_")
    curve, nfile, used = {}, 0, []
    for r in ranks:
        for s in seeds:
            pat = re.compile(r"^cloud_verify_r%d_s%d(?:_|\.json$)" % (r, s))
            hits = [p for p in sorted((REPO / EXP).glob("cloud_verify_r%d_s%d*.json" % (r, s)))
                    if pat.search(p.name) and not any(e in p.name for e in excl)]
            if len(hits) != 1:
                raise SystemExit("[p1635] cloud_verify r=%d s=%d matched %d files: %s"
                                 % (r, s, len(hits), [h.name for h in hits]))
            a = Archive(str(hits[0].relative_to(REPO)).replace("\\", "/"))
            E = a.f("E")
            dE = a.f("delta_E")
            got = _dE_from_E(E, a.rel, "E")
            if got is None or abs(got - dE) > 1e-6:
                raise SystemExit("[p1635] %s: delta_E %r != E[-1]-E[0] %r" % (a.rel, dE, got))
            curve.setdefault(s, {})[r] = float(dE)
            nfile += 1
            used.append(a)
    return {"id": "llava_blank3ep_cloud10", "family": "llava-1.5-7b", "unit": "seed",
            "curve": curve, "ranks": ranks,
            "protocol": "blank-image (text-only) LLaVA-1.5-7B LoRA, 3 epochs, ten seed labels, r=3..8",
            "sources": sorted({a.rel for a in used}),
            "n_records": nfile,
            "fields": ["E", "delta_E"],
            "note": "raw per-run archives; the archived aggregate p3_rank_separation_extended.json "
                    "is asserted against these means, not used as the input"}


def s_llava_rerun5():
    """LLaVA-1.5-7B, current-protocol re-run, five seeds at r=5 and r=6 (E0 = 3921.0)."""
    seeds_arch = Archive(ANA + "/p3_rerun_seeds.json")
    curve, fields = {}, []
    for key, rec in seeds_arch.f("runs").items():
        curve.setdefault(int(rec["seed"]), {})[int(rec["rank"])] = float(rec["delta_E"])
    fields.append("runs")
    rerun = Archive(ANA + "/p3_rerun_analysis.json")
    for r in ("5", "6"):
        node = rerun.f("curve.%s" % r)
        fields.append("curve.%s" % r)
        curve.setdefault(42, {})[int(r)] = float(node["dE_seed42"])
        curve.setdefault(123, {})[int(r)] = float(node["dE_other_seeds"][0])
    return {"id": "llava_rerun5", "family": "llava-1.5-7b", "unit": "seed",
            "curve": curve, "ranks": [5, 6],
            "protocol": "current run_training.py defaults (20 samples, 16 train / 4 eval, lr 5e-5, "
                        "3 epochs), E0 = 3921.0, seeds 42/123/789/999/1024",
            "sources": [seeds_arch.rel, rerun.rel], "n_records": 10,
            "fields": ["runs.<key>.delta_E", "curve.5.dE_seed42", "curve.5.dE_other_seeds",
                       "curve.6.dE_seed42", "curve.6.dE_other_seeds"],
            "note": "this is the five-seed set quoted in the manuscript's tab:seed5"}


def s_llava_e2(section, sid):
    """LLaVA E2 batch: `extra` (multi-seed spot checks) or `sweep` (dense rank sweep)."""
    a = Archive(EXP + "/E2_results.json")
    rows = a.f(section)
    curve, seen = {}, set()
    for rec in rows:
        if not rec.get("ok") or not rec.get("E"):
            continue
        key = (int(rec["rank"]), int(rec["seed"]))
        if key in seen:
            continue
        dE = _dE_from_E(rec["E"], a.rel, "E2.%s" % section)
        if dE is None:
            continue
        seen.add(key)
        curve.setdefault(int(rec["seed"]), {})[int(rec["rank"])] = dE
    return {"id": sid, "family": "llava-1.5-7b", "unit": "seed", "curve": curve,
            "ranks": sorted({r for u in curve for r in curve[u]}),
            "protocol": "LLaVA-1.5-7B blank-image protocol, 3 epochs, E2 batch section '%s'" % section,
            "sources": [a.rel], "n_records": len(seen), "fields": ["%s" % section],
            "note": "dE computed from the archived E trajectory; runs with NaN and runs with "
                    "ok=false are excluded and counted in n_runs_excluded"}


def s_llava_sharegpt():
    """LLaVA-1.5-7B on ShareGPT, 3 seeds, 15 ranks."""
    a = Archive(EXP + "/vqa_phase_results.json")
    curve = {}
    ranks = []
    for k, node in a.data.items():
        if not re.fullmatch(r"r\d+", k):
            continue
        r = int(k[1:])
        ranks.append(r)
        a.fields.append(k)
        for i, v in enumerate(node["dE"]):
            curve.setdefault(i, {})[r] = float(v)
    return {"id": "llava_sharegpt_3seed", "family": "llava-1.5-7b", "unit": "seed",
            "curve": curve, "ranks": sorted(ranks),
            "protocol": "ShareGPT instruction data, blank-image protocol, 3 epochs, 3 seeds",
            "sources": [a.rel], "n_records": 3 * len(ranks), "fields": ["r<rank>.dE"],
            "note": "seeds are positional in the archived dE list; the archive does not name them"}


def s_llava_ers():
    """LLaVA-1.5-7B at one epoch (faster-convergence family)."""
    a = Archive(EXP + "/ers_1epoch_results.json")
    curve, ranks = {}, []
    for k, node in a.data.items():
        if not re.fullmatch(r"r\d+", k):
            continue
        r = int(k[1:])
        ranks.append(r)
        a.fields.append(k)
        for i, v in enumerate(node["dE"]):
            curve.setdefault(i, {})[r] = float(v)
    return {"id": "llava_ers_1epoch_3seed", "family": "llava-1.5-7b", "unit": "seed",
            "curve": curve, "ranks": sorted(ranks),
            "protocol": "LLaVA-1.5-7B blank-image protocol, ONE epoch, 3 seeds",
            "sources": [a.rel], "n_records": 3 * len(ranks), "fields": ["r<rank>.dE"],
            "note": "the archive contains only r=4,16,32,64, so the fit brackets the crossing "
                    "between r=32 and r=64 and cannot localise it further"}


def s_llava_samplesize():
    """LLaVA-1.5-7B sample-window ablation: one unit per training window."""
    a = Archive(EXP + "/sample_size_results.json")
    runs = a.f("runs")
    curve, seeds = {}, set()
    for rec in runs:
        if not rec.get("ok"):
            continue
        m = re.search(r"_s(\d+)$", rec["name"])
        if not m:
            raise SystemExit("[p1635] %s: cannot read a seed from %r" % (a.rel, rec["name"]))
        seeds.add(int(m.group(1)))
        dE = _dE_from_E(rec["E"], a.rel, "runs")
        if dE is None:
            continue
        curve.setdefault(int(rec["samples"]), {})[int(rec["rank"])] = dE
    if len(seeds) != 1:
        raise SystemExit("[p1635] %s: expected a single seed label, got %s" % (a.rel, sorted(seeds)))
    return {"id": "llava_samplesize_windows", "family": "llava-1.5-7b", "unit": "training window",
            "curve": curve, "ranks": sorted({r for u in curve for r in curve[u]}),
            "protocol": "LLaVA-1.5-7B blank-image protocol, 3 epochs, seed %d, training window varied"
                        % sorted(seeds)[0],
            "sources": [a.rel], "n_records": len(runs), "fields": ["runs.<i>.E", "runs.<i>.samples"],
            "note": "one seed per rank, so the resampling unit is the training window, not the seed"}


def s_qwen_cloud():
    """Qwen cloud sweep (the 45-run family quoted in the manuscript's phase table)."""
    a = Archive(EXP + "/Qwen_results.json")
    rows = a.f("sweep")
    curve = {}
    for rec in rows:
        if not rec.get("ok") or not rec.get("E"):
            continue
        dE = _dE_from_E(rec["E"], a.rel, "sweep")
        if dE is None:
            continue
        curve.setdefault(int(rec["seed"]), {})[int(rec["rank"])] = dE
    return {"id": "qwen_cloud_sweep_3seed", "family": "qwen2-vl-7b", "unit": "seed",
            "curve": curve, "ranks": sorted({r for u in curve for r in curve[u]}),
            "protocol": "cloud rank sweep, 15 ranks x 3 seeds, 3 epochs",
            "sources": [a.rel], "n_records": len(rows), "fields": ["sweep"],
            "model_label_source": "the archive stores no model field; the label 'Qwen2-VL-7B' is the "
                                  "one used by the manuscript phase table (sections/experiments.tex, "
                                  "tab:phase) and by " + ANA + "/p3_phase_boundary.json :: "
                                  "meta.archive_files.Qwen",
            "model_label_confidence": "inferred from the manuscript, not stored in the archive",
            "note": "the sweep covers r=4..64 with three seeds per rank; the archive stores no image "
                    "condition field, so this family contributes a single stratum"}


def s_qwen2b_p3d(condition, field):
    """Qwen2-VL-2B rank sweep; `condition` is real or blank, `field` dE_train or dE_eval_real."""
    a = Archive(ANA + "/p3d_qwen_ranksweep.json")
    rows = a.f("runs")
    curve = {}
    for rec in rows:
        if rec.get("condition") != condition or not rec.get("rank"):
            continue
        if field not in rec:
            raise SystemExit("[p1635] %s: run has no field %s" % (a.rel, field))
        v = rec[field]
        if v is None:
            continue
        traj = rec.get("E_train_epochs") if field == "dE_train" else rec.get("E_eval_real_epochs")
        if traj:
            got = _dE_from_E(traj, a.rel, field)
            if got is not None and abs(got - float(v)) > 1e-3:
                raise SystemExit("[p1635] %s: %s %r != trajectory delta %r" % (a.rel, field, v, got))
        curve.setdefault(int(rec["seed"]), {})[int(rec["rank"])] = float(v)
    return {"id": "qwen2b_p3d_%s_%s" % (condition, field), "family": "qwen2-vl-2b", "unit": "seed",
            "curve": curve, "ranks": sorted({r for u in curve for r in curve[u]}),
            "protocol": "Qwen2-VL-2B-Instruct, 3 epochs, lr 5e-5, LoRA qkvo, vision tower frozen, "
                        "condition = %s, energy field %s" % (condition, field),
            "sources": [a.rel], "n_records": sum(len(v) for v in curve.values()),
            "fields": ["runs.<i>.condition", "runs.<i>.rank", "runs.<i>.seed", "runs.<i>.%s" % field],
            "note": "the archive states its own model: models/Qwen2-VL-2B-Instruct"}


def s_qwen2b_blankimg():
    """Qwen2-VL-2B under the LLaVA blank-image protocol, r=5 and r=6, seed 42."""
    a = Archive(ANA + "/p3_qwen2b_crossing_fixed.json")
    runs = a.f("runs")
    curve = {}
    for rec in runs.values():
        dE = rec["delta_E"]
        got = _dE_from_E(rec["E"], a.rel, "runs")
        if got is None or abs(got - float(dE)) > 1e-6:
            raise SystemExit("[p1635] %s: delta_E %r != trajectory delta %r" % (a.rel, dE, got))
        curve.setdefault(int(rec["seed"]), {})[int(rec["rank"])] = float(dE)
    return {"id": "qwen2b_blankimg_r5_r6_seed42", "family": "qwen2-vl-2b", "unit": "seed",
            "curve": curve, "ranks": [5, 6],
            "protocol": "Qwen2-VL-2B-Instruct, blank-image protocol, seed 42, 3 epochs, adapter rank "
                        "varied through --llm-rank",
            "sources": [a.rel], "n_records": len(runs), "fields": ["runs.<key>.E", "runs.<key>.delta_E"],
            "note": "one seed per rank: no resampling interval is available from this archive alone"}


def s_clip(n_train, field):
    """CLIP ViT-B/32 text-tower LoRA rank sweep, split by training window and energy field."""
    a = Archive(ANA + "/p3d_clip_ranksweep.json")
    rows = a.f("runs")
    curve = {}
    for rec in rows:
        if rec.get("arm") != "text":
            continue
        if int(rec.get("n_train") or 0) != n_train or not rec.get("rank"):
            continue
        curve.setdefault(int(rec["seed"]), {})[int(rec["rank"])] = float(rec[field])
    return {"id": "clip_text_n%d_%s" % (n_train, field), "family": "clip-vit-base-patch32",
            "unit": "seed", "curve": curve,
            "ranks": sorted({r for u in curve for r in curve[u]}),
            "protocol": "CLIP ViT-B/32, LoRA on the text tower only, alpha = 2*rank, 3 epochs, "
                        "batch 32, Flickr30k self-split; n_train = %d; energy field %s"
                        % (n_train, field),
            "sources": [a.rel], "n_records": sum(len(v) for v in curve.values()),
            "fields": ["runs.<i>.arm", "runs.<i>.n_train", "runs.<i>.rank", "runs.<i>.seed",
                       "runs.<i>.%s" % field],
            "metric_comparable": "sign only",
            "note": "this archive's E is mean||normalize(z_I)-normalize(z_T)||^2 on a retrieval "
                    "model, a different observable and scale from the VLM alignment energy; only the "
                    "sign of dE is comparable across these two metrics"}


def s_smolvlm():
    """SmolVLM-500M, three seeds, r=5 and r=6."""
    curve, srcs = {}, []
    for s in (42, 123, 789):
        a = Archive(ANA + "/p3_smolvlm_family_s%d.json" % s)
        if int(a.f("meta.seed")) != s:
            raise SystemExit("[p1635] %s: meta.seed disagrees with the file name" % a.rel)
        for r in ("r5", "r6"):
            curve.setdefault(s, {})[int(r[1:])] = float(a.f("runs.%s.delta_E" % r))
        srcs.append(a.rel)
    return {"id": "smolvlm500m_r5_r6_3seed", "family": "smolvlm-500m", "unit": "seed",
            "curve": curve, "ranks": [5, 6],
            "protocol": "SmolVLM-500M-Instruct, 20 samples, 3 epochs, lr 5e-5, seeds 42/123/789",
            "sources": srcs, "n_records": 6, "fields": ["meta.seed", "runs.r5.delta_E",
                                                        "runs.r6.delta_E"],
            "note": "only r=5 and r=6 were run, so the fit reports the bracket and nothing finer"}


def s_llava_seed5_env():
    """The five-seed crossing set archived as aggregates only (no per-seed values)."""
    a = Archive(ANA + "/p3_robust_stats.json")
    r5 = a.f("seed5.r5.mean")
    r6 = a.f("seed5.r6.mean")
    r5n = a.f("seed5.r5.n")
    curve = {"r5": {5: float(r5)}, "r6": {6: float(r6)}}
    return {"id": "llava_seed5_aggregate_env_torch29", "family": "llava-1.5-7b",
            "unit": "aggregate", "curve": curve, "ranks": [5, 6],
            "protocol": "five seeds per rank, earlier environment stack (torch 2.9/cu130)",
            "sources": [a.rel], "n_records": int(r5n) * 2,
            "fields": ["seed5.r5.mean", "seed5.r5.n", "seed5.r6.mean"],
            "bootstrap": None,
            "bootstrap_reason": "the archive stores aggregates only (%s :: seed5.<rank>), with no "
                                "per-seed values, so no resampling interval can be built from it"
                                % a.rel,
            "note": "aggregate-only stratum: it anchors the r=5/r=6 bracket in a second environment "
                    "stack but cannot contribute a bootstrap"}


STRATUM_BUILDERS = [
    ("llava_blank3ep_cloud10", s_llava_cloud10),
    ("llava_rerun5", s_llava_rerun5),
    ("llava_e2_extra", lambda: s_llava_e2("extra", "llava_e2_extra_3seed")),
    ("llava_e2_sweep", lambda: s_llava_e2("sweep", "llava_e2_sweep_3seed")),
    ("llava_sharegpt", s_llava_sharegpt),
    ("llava_ers_1epoch", s_llava_ers),
    ("llava_samplesize_windows", s_llava_samplesize),
    ("llava_seed5_aggregate", s_llava_seed5_env),
    ("qwen_cloud_sweep", s_qwen_cloud),
    ("qwen2b_p3d_real_train", lambda: s_qwen2b_p3d("real", "dE_train")),
    ("qwen2b_p3d_blank_train", lambda: s_qwen2b_p3d("blank", "dE_train")),
    ("qwen2b_p3d_real_eval", lambda: s_qwen2b_p3d("real", "dE_eval_real")),
    ("qwen2b_p3d_blank_eval", lambda: s_qwen2b_p3d("blank", "dE_eval_real")),
    ("qwen2b_blankimg", s_qwen2b_blankimg),
    ("clip_n16_test", lambda: s_clip(16, "dE_test")),
    ("clip_n16_train", lambda: s_clip(16, "dE_train")),
    ("clip_n1024_test", lambda: s_clip(1024, "dE_test")),
    ("clip_n1024_train", lambda: s_clip(1024, "dE_train")),
    ("smolvlm_r5_r6", s_smolvlm),
]

FAMILY_META = {
    "llava-1.5-7b": {
        "backbone": "LLaVA-1.5-7B (llava-hf)",
        "metric": "E = mean ||h_vis - h_lang||^2 on the last hidden state, blank-image protocol",
        "primary_stratum": "llava_blank3ep_cloud10",
        "primary_stratum_why": "ten paired seeds per rank, the richest rank coverage at the crossing, "
                               "and the family the manuscript's r_c in [5,6] was measured on",
    },
    "qwen2-vl-7b": {
        "backbone": "Qwen2-VL-7B (label inferred, see stratum model_label_source)",
        "metric": "same alignment-energy convention, cloud rank sweep",
        "primary_stratum": "qwen_cloud_sweep",
        "primary_stratum_why": "the only archived rank curve for this checkpoint",
    },
    "qwen2-vl-2b": {
        "backbone": "Qwen2-VL-2B-Instruct (stated inside the archives)",
        "metric": "same alignment-energy convention; the p3d sweep reports train and held-out fields",
        "primary_stratum": "qwen2b_p3d_real_train",
        "primary_stratum_why": "the widest rank range (r=1..16) with three paired seeds",
    },
    "clip-vit-base-patch32": {
        "backbone": "CLIP ViT-B/32, LoRA on the text tower",
        "metric": "mean ||normalize(z_I) - normalize(z_T)||^2 (retrieval), sign-comparable only",
        "primary_stratum": "clip_n1024_test",
        "primary_stratum_why": "the widest training window and the held-out energy field",
    },
    "smolvlm-500m": {
        "backbone": "SmolVLM-500M-Instruct",
        "metric": "same alignment-energy convention",
        "primary_stratum": "smolvlm_r5_r6",
        "primary_stratum_why": "the only archived curve for this backbone",
    },
}


def build_rc_by_family():
    strata, provenance = {}, []
    for _sid, fn in STRATUM_BUILDERS:
        st = fn()
        st["id"] = _sid          # the registry name is the canonical stratum id
        fit = fit_crossing(st["curve"], ranks=st["ranks"])
        if st.get("bootstrap", "auto") is None:
            boot = {"n_boot": 0, "n_boot_with_crossing": 0, "ci95": None,
                    "reason": st["bootstrap_reason"]}
        else:
            boot = boot_crossing(st["curve"], st["unit"], st["ranks"])
            if fit.get("status") == "no_crossing_in_range":
                # a handful of resampled draws can stumble into a negative mean at one rank and
                # so manufacture a crossing the point estimate does not have; say so instead of
                # quoting an interval built from those draws
                boot["bootstrap_crossings_are_incidental"] = True
                boot["reason"] = ("the stratum itself has no sign crossing, so the %d of %d "
                                  "resampled draws that produced one are incidental; no interval "
                                  "is quoted"
                                  % (boot["n_boot_with_crossing"], boot["n_boot"]))
                boot["ci95"] = None
                boot["point_bootstrap_median"] = None
                boot["stable"] = False
        rec = {
            "family": st["family"],
            "protocol": st["protocol"],
            "unit": st["unit"],
            "n_units": fit.get("n_units"),
            "ranks": st["ranks"],
            "mean_dE_by_rank": fit.get("mean_by_rank"),
            "n_by_rank": fit.get("n_by_rank"),
            "sign_pattern_by_rank": fit.get("sign_pattern_by_rank"),
            "status": fit.get("status"),
            "crossing_bracket": fit.get("crossing_bracket"),
            "crossing_point": fit.get("crossing_point"),
            "crossing_point_local_ols": fit.get("crossing_point_local_ols"),
            "forward_crossings": fit.get("forward_crossings"),
            "reverse_crossings": fit.get("reverse_crossings"),
            "secondary_forward_crossings": fit.get("secondary_forward_crossings"),
            "sign_of_all_means": fit.get("sign_of_all_means"),
            "min_rank_measured": fit.get("min_rank_measured"),
            "max_rank_measured": fit.get("max_rank_measured"),
            "bootstrap": boot,
            "sources": st["sources"],
            "fields": st["fields"],
            "n_records": st["n_records"],
            "note": st["note"],
            "model_label_source": st.get("model_label_source"),
        }
        if st.get("metric_comparable"):
            rec["metric_comparable_across_families"] = st["metric_comparable"]
        strata[st["id"]] = rec
        provenance.append({"stratum": st["id"], "paths": st["sources"], "fields": st["fields"],
                           "n_records": st["n_records"]})

    families = {}
    for fam, meta in FAMILY_META.items():
        members = {k: v for k, v in strata.items() if v["family"] == fam}
        prim = meta["primary_stratum"]
        prow = members[prim]
        pts = {k: v["crossing_point"] for k, v in members.items() if v["crossing_point"] is not None}
        pci = prow["bootstrap"].get("ci95")
        # do all strata of this family agree on a common crossing interval?
        intervals = [v["bootstrap"]["ci95"] for v in members.values()
                     if v["crossing_point"] is not None and v["bootstrap"].get("ci95")]
        common = None
        if intervals:
            lo = max(i[0] for i in intervals)
            hi = min(i[1] for i in intervals)
            common = [lo, hi] if lo <= hi else None
        norm = {k: v["crossing_point"] for k, v in members.items()}
        no_cross = sorted(k for k, v in members.items() if v["status"] == "no_crossing_in_range")
        out = dict(meta)
        out.update({
            "n_strata": len(members),
            "strata": members,
            "crossing_points_by_stratum": norm,
            "strata_without_a_sign_crossing": no_cross,
            "sensitivity_span": ([min(pts.values()), max(pts.values())] if pts else None),
            "common_intersection_of_stratum_ci95": common,
            "single_rc_supported_within_family": bool(common is not None and len(pts) == len(members)),
            "why_not_single": None,
        })
        if out["single_rc_supported_within_family"]:
            out["family_estimate"] = prow["crossing_point"]
            out["family_estimate_ci95"] = pci
            out["family_estimate_bracket"] = prow["crossing_bracket"]
        else:
            out["family_estimate"] = None
            out["family_estimate_ci95"] = None
            out["family_estimate_bracket"] = None
            if no_cross:
                out["why_not_single"] = (
                    "%d of %d strata show no sign change anywhere in their measured rank range "
                    "(%s), so those strata cannot pin a crossing at all"
                    % (len(no_cross), len(members), ", ".join(no_cross)))
            else:
                out["why_not_single"] = ("stratum crossing points disagree: %s"
                                         % json.dumps(norm, sort_keys=True))
        families[fam] = out
    return families, strata, provenance


# --------------------------------------------------------------------------------------
# stability: independent observables on the same crossing
# --------------------------------------------------------------------------------------


def build_stability(families, strata):
    # (a) is the straddling sign unanimous in the primary LLaVA stratum?
    prim = strata["llava_blank3ep_cloud10"]
    sig, nby = prim["sign_pattern_by_rank"], prim["n_by_rank"]
    unanimity = {}
    for r in ("5", "6"):
        vals = prim["mean_dE_by_rank"][r]
        unanimity["r" + r] = {"mean": vals, "n": nby[r]}
    unanimity["all_runs_at_r5_negative"] = all(v == "neg" for v in sig[:3])
    unanimity["all_runs_at_r6_positive"] = all(v == "pos" for v in sig[3:])

    # (b) the fifteen-pair exact test already archived for exactly these runs
    sep = Archive(ANA + "/p3_rank_separation_extended.json")
    test = {
        "n_pairs": sep.f("conclusion.n_pairs"),
        "n_separating_raw_p05": sep.f("conclusion.n_separating_raw_p05"),
        "n_separating_holm_p05": sep.f("conclusion.n_separating_holm_p05"),
        "adjacent_rank_p_values": sep.f("conclusion.adjacent_rank_p_values"),
        "sign_split": sep.f("conclusion.sign_split"),
        "crossing_between": sep.f("conclusion.crossing_between"),
        "rank5_tost_equivalent_to_zero": sep.f("conclusion.rank5_tost_equivalent_to_zero"),
        "rank5_tost_p": sep.f("conclusion.rank5_tost_p"),
        "rank5_min_equivalent_margin": sep.f("conclusion.rank5_min_equivalent_margin"),
        "rank5_ci95_t": sep.f("rank5_equivalence.ci95_t"),
        "p_min_attainable": sep.f("separation.p_min_attainable"),
        "n_splits": sep.f("separation.n_splits"),
    }
    # assert our refit reproduces the archived means the test was run on
    for r in ("3", "4", "5", "6", "7", "8"):
        mine = prim["mean_dE_by_rank"][r]
        theirs = sep.f("ranks.%s.mean" % r)
        if abs(mine - theirs) > 1e-6:
            raise SystemExit("[p1635] refit mean at r=%s (%r) != archived mean (%r)"
                             % (r, mine, theirs))
    test["refit_reproduces_archived_means"] = True

    # (c) environment share of the r=5 variance
    env = Archive(ANA + "/p3_env_variance.json")
    environment = {
        "env_share": env.f("env_share"),
        "share_ci95": env.f("bootstrap.share_ci95"),
        "sigma_env": env.f("sigma_env"),
        "sigma_seed": env.f("sigma_seed"),
        "stack_means_at_r5": {k: v["mean"] for k, v in env.f("envs").items()},
    }

    # (d) the curvature observable, an independent rank-indexed quantity
    curvature = {"by_rank": {}, "primary_seed": 42}
    probes = sorted((REPO / ANA).glob("p3_hessian_probe_r*.json"))
    for p in probes:
        if "qwen" in p.name:
            continue
        a = Archive(str(p.relative_to(REPO)).replace("\\", "/"))
        runs = a.f("runs")
        eps = a.f("meta.eps")
        rank = int(runs[0]["rank"])
        rec = {"model": a.f("meta.model"), "n_batches": len(runs), "eps": eps,
               "source": a.rel, "fields": ["meta.model", "meta.eps", "runs.<i>.rank",
                                           "runs.<i>.second_order_over_first_order.<eps>"]}
        # the seed is only in the file name; records it so the primary line can be isolated
        m = re.search(r"_s(\d+)\.json$", p.name)
        rec["seed"] = int(m.group(1)) if m else 42
        rec["seed_source"] = ("file name suffix" if m else
                              "no suffix in the file name, so the archive default seed")
        for e in eps:
            vals = [r["second_order_over_first_order"][str(e)] for r in runs]
            a.fields.append("runs.<i>.second_order_over_first_order.%s" % e)
            rec["share_mean_eps_%g" % e] = rd(mean(vals))
            rec["share_sd_eps_%g" % e] = rd(sd_sample(vals))
            rec["share_all_negative_eps_%g" % e] = all(v < 0 for v in vals)
            rec["share_at_operating_lr_from_eps_%g" % e] = rd(
                mean(vals) * OPERATING_LR / float(e))
        curvature["by_rank"][str(rank)] = rec
    curvature["probe_eps_levels"] = sorted({e for r in curvature["by_rank"].values()
                                            for e in r["eps"]})
    curvature["ranks_measured"] = sorted(int(k) for k in curvature["by_rank"])
    curvature["primary_seed_curve_share_by_rank"] = {}
    for e in curvature["probe_eps_levels"]:
        line = {k: r["share_mean_eps_%g" % e] for k, r in curvature["by_rank"].items()
                if r["seed"] == curvature["primary_seed"]}
        rk = sorted(line, key=int)
        curvature["primary_seed_curve_share_by_rank"]["eps_%g" % e] = {
            "values_by_rank": {k: line[k] for k in rk},
            "all_negative": all(v < 0 for v in line.values()),
            "monotone_rising_toward_zero": all(
                line[rk[i]] < line[rk[i + 1]] for i in range(len(rk) - 1)),
        }
    curvature["no_zero_crossing_on_the_primary_seed_curve"] = all(
        v["all_negative"]
        for v in curvature["primary_seed_curve_share_by_rank"].values())
    curvature["significant_flips"] = [
        {"source": r["source"], "seed": r["seed"], "eps": e}
        for r in curvature["by_rank"].values() for e in r["eps"]
        if not r["share_all_negative_eps_%g" % e]]
    curvature["sign_unanimous_across_batches_and_seeds"] = not curvature["significant_flips"]
    curvature["check_against_manuscript_claim_row"] = (
        "the manuscript's claim table already marks 'curvature sign stable across ranks, seeds "
        "and stacks' as not supported; the archived flips listed in significant_flips are the "
        "evidence for that row")
    # cross-check the manuscript's tab:hessian shares against the archive
    gap = Archive(ANA + "/p3_gapfill_summary.json")
    curvature["manuscript_tab_hessian_check"] = {
        "archive_r5_mean_share_at_lr": gap.f("curvature.5.mean_share_at_lr"),
        "archive_r6_mean_share_at_lr": gap.f("curvature.6.mean_share_at_lr"),
        "recomputed_r5_mean_share_at_lr": curvature["by_rank"]["5"]["share_at_operating_lr_from_eps_0.001"],
        "recomputed_r6_mean_share_at_lr": curvature["by_rank"]["6"]["share_at_operating_lr_from_eps_0.001"],
    }
    chk = curvature["manuscript_tab_hessian_check"]
    chk["reproduces_manuscript_to_4dp"] = bool(
        rd(chk["archive_r5_mean_share_at_lr"], 4) == rd(chk["recomputed_r5_mean_share_at_lr"], 4)
        and rd(chk["archive_r6_mean_share_at_lr"], 4) == rd(chk["recomputed_r6_mean_share_at_lr"], 4))

    # (e) what the manuscript currently says, and whether the archives agree
    checks = []
    supp = read_text("paper3/paper_ieee/supplementary/supplementary.tex")
    sharegpt_means = strata["llava_sharegpt"]["mean_dE_by_rank"]
    checks.append({
        "claim": "the ShareGPT stratum is described as flipping sign between r=5 and r=6",
        "manuscript_anchor": "paper3/paper_ieee/supplementary/supplementary.tex, caption of tab:sharegpt",
        "archive_means": {"r4": sharegpt_means["4"], "r5": sharegpt_means["5"],
                          "r6": sharegpt_means["6"]},
        "archive_crossing_point": strata["llava_sharegpt"]["crossing_point"],
        "agrees": bool(sharegpt_means["5"] < 0 <= sharegpt_means["6"]),
        "reading": "does the manuscript's stated bracket match its own archived means? No: the "
                   "archived means cross zero between r=4 and r=5, not between r=5 and r=6",
    })
    ers_caption = "earlier than the 3-epoch critical rank"
    checks.append({
        "claim": "the one-epoch stratum is described in its figure caption as flipping 'earlier' than "
                 "the 3-epoch crossing",
        "manuscript_anchor": "paper3/paper_ieee/supplementary/supplementary.tex, caption of fig:ers",
        "caption_present": ers_caption in supp,
        "archive_crossing_point": strata["llava_ers_1epoch"]["crossing_point"],
        "archive_bracket": strata["llava_ers_1epoch"]["crossing_bracket"],
        "agrees": bool(strata["llava_ers_1epoch"]["crossing_point"] is not None
                       and strata["llava_ers_1epoch"]["crossing_point"] < 6),
        "reading": "the archived one-epoch crossing is at a much higher rank than the 3-epoch "
                   "bracket, so 'earlier' reads as a wording inconsistency rather than a number",
    })

    return {
        "primary_stratum_sign_unanimity": unanimity,
        "archived_exact_tests_on_the_same_runs": test,
        "environment_share_of_r5_variance": environment,
        "curvature_observable": curvature,
        "manuscript_consistency_checks": checks,
    }


def read_text(rel):
    p = REPO / rel
    if not p.exists():
        raise SystemExit("[p1635] missing text file: %s" % rel)
    return p.read_text(encoding="utf-8")


# --------------------------------------------------------------------------------------
# the AdaLoRA / published-baseline boundary table
# --------------------------------------------------------------------------------------


def _run_cells(rel, plan_key, lr=None):
    a = Archive(rel)
    runs = a.f("runs")
    out = {}
    for name, rec in runs.items():
        if plan_key not in name:
            continue
        dE = rec["delta_E"]
        out[int(rec["seed"])] = {
            "delta_E": float(dE),
            "delta_E_sd_within_cell": rec.get("delta_E_per_sample_sd"),
            "loss_first": rec.get("loss_first"),
            "loss_last": rec.get("loss_last"),
            "lr": rec.get("lr", lr),
            "epochs": rec.get("epochs"),
            "E0": rec.get("E0"),
            "source": rel,
        }
    a.fields.append("runs.<name>.delta_E")
    return out, a


def build_adalora_boundary():
    adalora, ad_srcs = {}, []
    for rel, lr in ((ANA + "/p3_alloc_runs/adalora_summary.json", 5e-5),
                    (ANA + "/p3_alloc_runs/adalora_lr0.0003/adalora_summary.json", 3e-4),
                    (ANA + "/p3_alloc_runs/adalora_lr0.001/adalora_summary.json", 1e-3)):
        got, a = _run_cells(rel, "adalora__")
        for s, rec in got.items():
            rec["lr"] = lr
            adalora[(lr, s)] = rec
        ad_srcs.append(a)

    gamma, uni = {}, {}
    for rel, lr in ((ANA + "/p3_alloc_runs/main/summary.json", 5e-5),
                    (ANA + "/p3_alloc_runs/exp_lr0.0003/summary.json", 3e-4),
                    (ANA + "/p3_alloc_runs/exp_lr0.001/summary.json", 1e-3)):
        got, a = _run_cells(rel, "exp_beta_paper_0.137__")
        for s, rec in got.items():
            rec["lr"] = lr
            gamma[(lr, s)] = rec
        ad_srcs.append(a)
    for rel, lr in ((ANA + "/p3_alloc_runs/main/summary.json", 5e-5),
                    (ANA + "/p3_alloc_runs/uniform_lr0.0003/summary.json", 3e-4),
                    (ANA + "/p3_alloc_runs/uniform_lr0.001/summary.json", 1e-3)):
        got, a = _run_cells(rel, "uniform__")
        for s, rec in got.items():
            rec["lr"] = lr
            uni[(lr, s)] = rec
        ad_srcs.append(a)

    # the block configuration of the AdaLoRA arm, and the plane it is compared against
    cfg = Archive(ANA + "/p3_alloc_adalora_config.json")
    adalora_cfg = {
        "n_modules": cfg.f("n_modules"),
        "rank_distribution": cfg.f("rank_distribution"),
        "sum_rank_cost": cfg.f("sum_rank_cost"),
        "target_budget_params": cfg.f("target_budget_params"),
        "budget_exact_match_by_cost_model": cfg.f("budget_exact_match_by_cost_model"),
        "per_block_params_by_cost_model": cfg.f("per_block_params_by_cost_model"),
        "n_trainable_measured": cfg.f("n_trainable_measured"),
        "measured_matches_budget": cfg.f("measured_matches_budget"),
        "peft_version": cfg.f("peft_version"),
        "source": cfg.rel,
    }
    up = Archive(ANA + "/p3_alloc_runs/main/uniform__seed42.json")
    uni_plan = {"ranks": up.f("ranks"), "per_block_params": up.f("per_block_params"),
                "n_trainable_params_measured": up.f("n_trainable_params_measured"),
                "source": up.rel}
    gp = Archive(ANA + "/p3_alloc_runs/main/exp_beta_paper_0.137__seed42.json")
    gamma_plan = {"ranks": gp.f("ranks"), "per_block_params": gp.f("per_block_params"),
                  "n_trainable_params_measured": gp.f("n_trainable_params_measured"),
                  "source": gp.rel}
    # the two configurations must be the *same* allocation for the confound to be real
    ad_rank = sorted(adalora_cfg["rank_distribution"])
    same_alloc = (len(ad_rank) == 1 and int(ad_rank[0]) == 4
                  and uni_plan["ranks"] == {"vision": 4, "llm_shallow": 4,
                                            "llm_mid": 4, "llm_deep": 4}
                  and adalora_cfg["per_block_params_by_cost_model"] == uni_plan["per_block_params"])
    if not same_alloc:
        raise SystemExit("[p1635] the AdaLoRA rank_pattern no longer equals the uniform plan")

    matched = []
    for key in sorted(set(adalora) & set(gamma), key=lambda k: (k[0], k[1])):
        lr, seed = key
        a, g = adalora[key], gamma[key]
        diff = a["delta_E"] - g["delta_E"]
        row = {
            "lr": lr,
            "seed": seed,
            "adalora_delta_E": rd(a["delta_E"]),
            "gamma_delta_E": rd(g["delta_E"]),
            "difference_adalora_minus_gamma": rd(diff),
            "sign": "adalora_lower_delta_E" if diff < 0 else
                    "gamma_lower_delta_E" if diff > 0 else "tie",
            "adalora_loss_first": rd(a["loss_first"]),
            "adalora_loss_last": rd(a["loss_last"]),
            "adalora_loss_change": rd(a["loss_last"] - a["loss_first"]),
            "gamma_loss_first": rd(g["loss_first"]),
            "gamma_loss_last": rd(g["loss_last"]),
            "gamma_loss_change": rd(g["loss_last"] - g["loss_first"]),
            "same_E0": bool(a["E0"] == g["E0"]),
            "within_cell_sd": a.get("delta_E_sd_within_cell"),
            "ci95": None,
            "ci95_reason": "delta_E is deterministic within a cell "
                           "(delta_E_per_sample_sd = 0.0), so no within-cell interval exists",
            "sources": [a["source"], g["source"]],
            "fields": ["runs.<name>.delta_E", "runs.<name>.loss_first", "runs.<name>.loss_last",
                       "runs.<name>.E0"],
        }
        row["gamma_vs_uniform_difference"] = (
            rd(g["delta_E"] - uni[key]["delta_E"]) if key in uni else None)
        row["gamma_vs_uniform_sign"] = (
            ("gamma_lower" if g["delta_E"] < uni[key]["delta_E"] else "uniform_lower")
            if key in uni else None)
        matched.append(row)

    diffs = [r["difference_adalora_minus_gamma"] for r in matched]
    n_neg = sum(1 for d in diffs if d < 0)
    n = len(diffs)
    summary = {
        "n_matched_cells": n,
        "n_cells_adalora_lower": n_neg,
        "mean_difference": rd(mean(diffs)),
        "sd_difference": rd(sd_sample(diffs)),
        "ci95_t": t_ci95(diffs),
        "exact_sign_test_two_sided_p": rd(2 / (2 ** n)),
        "exact_sign_test_min_attainable_p": rd(2 / (2 ** n)),
        "exact_sign_test_reaches_p05": bool(2 / (2 ** n) < 0.05),
        "n_cells_where_gamma_is_lower": n - n_neg,
        "cell_lrs": sorted({r["lr"] for r in matched}),
        "cell_seeds": sorted({r["seed"] for r in matched}),
        "adalora_archived_at_lrs": sorted({k[0] for k in adalora}),
        "gamma_archived_at_lrs": sorted({k[0] for k in gamma}),
        "unmatched_adalora_cells": sorted([list(k) for k in set(adalora) - set(gamma)]),
        "unmatched_gamma_cells_count": len(set(gamma) - set(adalora)),
    }
    summary["reverses_on_the_delta_E_axis"] = bool(n_neg != n and n_neg > 0)

    # the regime in which the Gamma rule itself loses to plain uniform rank
    reversals = []
    for key in sorted(set(gamma) & set(uni), key=lambda k: (k[0], k[1])):
        lr, seed = key
        g, u = gamma[key], uni[key]
        d = g["delta_E"] - u["delta_E"]
        reversals.append({
            "lr": lr, "seed": seed,
            "gamma_delta_E": rd(g["delta_E"]), "uniform_delta_E": rd(u["delta_E"]),
            "difference_gamma_minus_uniform": rd(d),
            "sign": "uniform_lower" if d > 0 else "gamma_lower" if d < 0 else "tie",
            "sources": [g["source"], u["source"]],
        })
    rev_cells = [r for r in reversals if r["sign"] == "uniform_lower"]

    # published-baseline allocation rules at the base-rank-1 arm
    arms = Archive(ANA + "/p3_robust_stats.json")
    arm_tab = arms.f("allocation_arms.arms")
    name2rule = {
        "verify_r1_s42_bcexplicit_v2_s4_m6_d4.json": "HALoRA-style (our block-level reimplementation)",
        "verify_r1_s42_bcexplicit_v11_s1_m3_d1.json": "IGU-LoRA-style (our block-level reimplementation)",
        "verify_r1_s42_bcexplicit_v10_s2_m3_d1.json": "ShapLoRA-style (our block-level reimplementation)",
        "verify_r1_s42_bcexplicit_v5_s5_m4_d2.json": "Gamma-guided rule (same base-rank-1 arm)",
    }
    rules = Archive(ANA + "/p3_baseline_arms.json")
    rule_delta = {}
    for rule in ("halora", "igu", "shap"):
        line = rules.f("%s.delta_line" % rule)
        rule_delta[rule] = float(re.search(r"([+-]?\d+\.\d+)", line).group(1))
    ntk = Archive(EXP + "/verify_r1_s42_ntk_arm.json")
    igu = Archive(EXP + "/verify_r1_s42_bcexplicit_v12_s1_m2_d1.json")
    baseline_rows = []
    for fname, label in sorted(name2rule.items()):
        rec = arm_tab[fname]
        arms.fields.append("allocation_arms.arms.%s.delta_E" % fname)
        baseline_rows.append({"rule": label, "arm_file": EXP + "/" + fname,
                              "delta_E": rd(rec["delta_E"]), "E": rec["E"]})
    baseline_rows.append({"rule": "NTK-diagonal rule (CLIP-derived, our arm)",
                          "arm_file": ntk.rel, "delta_E": rd(ntk.f("delta_E")), "E": ntk.f("E")})
    baseline_rows.append({"rule": "official IGU-LoRA code, name-proxy adapter",
                          "arm_file": igu.rel, "delta_E": rd(igu.f("delta_E")), "E": igu.f("E")})
    gamma_arm = [r for r in baseline_rows if r["rule"].startswith("Gamma-guided")][0]
    for r in baseline_rows:
        r["difference_vs_gamma_arm"] = rd(r["delta_E"] - gamma_arm["delta_E"])
        r["sign_vs_gamma_arm"] = ("gamma_lower" if r["difference_vs_gamma_arm"] > 0
                                 else "rule_lower" if r["difference_vs_gamma_arm"] < 0 else "tie")
        r["matched_setting"] = ("LLaVA-1.5-7B blank-image protocol, 20 samples, 3 epochs, seed 42, "
                                "base rank 1, alpha 16 (not parameter-matched to the uniform "
                                "r=5/r=6 arms)")
    # the archived rule tables must agree with the arm archives
    for rule, fname in (("halora", "verify_r1_s42_bcexplicit_v2_s4_m6_d4.json"),
                        ("igu", "verify_r1_s42_bcexplicit_v11_s1_m3_d1.json"),
                        ("shap", "verify_r1_s42_bcexplicit_v10_s2_m3_d1.json")):
        if abs(rule_delta[rule] - arm_tab[fname]["delta_E"]) > 1e-6:
            raise SystemExit("[p1635] %s: delta_line %r != arm %r"
                             % (rule, rule_delta[rule], arm_tab[fname]["delta_E"]))

    # how many of *our own* plans beat the Gamma rule at the operating lr
    alloc = Archive(ANA + "/p3_alloc_results.json")
    rank_among = alloc.f("comparisons.exp_beta_paper_0.137.rank_among_plans")
    plan_means = {k: alloc.f("per_plan.%s.delta_E.mean" % k)
                  for k in sorted(alloc.f("per_plan").keys() if False else alloc.data["per_plan"])}
    alloc.fields.append("per_plan.<plan>.delta_E.mean")

    e0_values = sorted({g["E0"] for g in gamma.values()} | {a["E0"] for a in adalora.values()})
    confounds = [
        "The AdaLoRA arm and the uniform arm share one block configuration: the archived "
        "rank_pattern puts rank 4 on all %d modules with the same per-block parameter counts "
        "(%s), so 'AdaLoRA' and 'uniform allocation' are the same rank plan and the comparison "
        "against the Gamma plan varies method and configuration at once."
        % (adalora_cfg["n_modules"], json.dumps(adalora_cfg["per_block_params_by_cost_model"],
                                                sort_keys=True)),
        "Every archived cell on this plane shares one pre-training energy, E0 = %s, so both arms "
        "see the same reference data and the same evaluation samples."
        % json.dumps(e0_values),
        "AdaLoRA's trainable-parameter count is not exactly the budget "
        "(measured %d against %d, %.4f%% high), so the arms are matched only under the cost model."
        % (adalora_cfg["n_trainable_measured"], adalora_cfg["target_budget_params"],
           100.0 * (adalora_cfg["n_trainable_measured"] - adalora_cfg["target_budget_params"])
           / adalora_cfg["target_budget_params"]),
        "The two scripts do not start from the same first-epoch loss at seed 42 "
        "(AdaLoRA %.4f against Gamma %.4f at lr 5e-5), so the CE-loss axes are not matched "
        "across scripts and no matched-loss claim is made here."
        % (adalora[(5e-5, 42)]["loss_first"], gamma[(5e-5, 42)]["loss_first"]),
        "tools/_p451_baseline_adalora.py sets orth_reg_weight=0.5 in the peft config (line 161) "
        "but back-propagates the manually computed cross-entropy (lines 303-304); whether peft "
        "applied the orthogonality regulariser is not recorded in any archive, so it is left "
        "unasserted.",
    ]

    return {
        "comparison_plane": {
            "backbone": "Qwen2-VL-2B-Instruct",
            "n_train": 32, "n_eval": 32, "epochs": 4,
            "budget_params": adalora_cfg["target_budget_params"],
            "E0_shared_by_every_cell_on_this_plane": e0_values,
            "adalora_config": adalora_cfg,
            "uniform_plan": uni_plan,
            "gamma_plan": gamma_plan,
            "adalora_and_uniform_share_one_rank_plan": True,
            "why_the_backbone_matters": "the allocation study runs on %s, where the archived rank "
                                        "sweeps show no alignment-energy sign change in r=1..16; "
                                        "the manuscript's r_c in [5,6] is a LLaVA-1.5-7B number"
                                        % ADALORA_FAMILY,
        },
        "matched_cells": matched,
        "summary": summary,
        "gamma_vs_uniform_cells": reversals,
        "reversal_regime": {
            "n_cells_where_plain_uniform_beats_the_gamma_rule": len(rev_cells),
            "cells": rev_cells,
            "regime": ("learning rate 3e-4 (both archived seeds) and 1e-3 at seed 123; at the "
                       "operating rate 5e-5 the Gamma rule is lower in both seeds"
                       if rev_cells else "no archived cell in which plain uniform beats the rule"),
        },
        "published_baseline_rules": {
            "setting": "LLaVA-1.5-7B blank-image protocol, 20 samples, 3 epochs, seed 42, base rank 1",
            "rows": baseline_rows,
            "gamma_arm_delta_E": gamma_arm["delta_E"],
            "n_rules_above_the_gamma_arm": sum(1 for r in baseline_rows
                                               if r["sign_vs_gamma_arm"] == "gamma_lower"),
            "n_rules_below_the_gamma_arm": sum(1 for r in baseline_rows
                                               if r["sign_vs_gamma_arm"] == "rule_lower"),
            "caveat": "these arms are not parameter-matched to the uniform r=5/r=6 arms; the "
                      "archive calls the comparison directional",
        },
        "gamma_rule_within_our_own_plans": {
            "n_plans_compared": rank_among["n_plans_compared"],
            "n_plans_with_lower_mean_delta_E": rank_among["n_plans_with_lower_mean_delta_E"],
            "fraction_better": rank_among["fraction_better"],
            "plan_means_at_the_operating_lr": {k: rd(v) for k, v in sorted(plan_means.items())},
            "source": alloc.rel,
            "fields": ["comparisons.exp_beta_paper_0.137.rank_among_plans", "per_plan.<plan>.delta_E.mean"],
        },
        "confounds": confounds,
        "sources": [a.rel for a in ad_srcs] + [cfg.rel, up.rel, gp.rel, arms.rel, rules.rel,
                                              ntk.rel, igu.rel, alloc.rel],
    }


# --------------------------------------------------------------------------------------
# conclusion
# --------------------------------------------------------------------------------------


def _family_classes(families):
    """Three different questions, three different lists.  Do not conflate them."""
    crossing_anywhere = sorted(k for k, v in families.items()
                               if any(s["crossing_point"] is not None
                                      for s in v["strata"].values()))
    none_anywhere = sorted(k for k, v in families.items()
                           if all(s["status"] == "no_crossing_in_range"
                                  for s in v["strata"].values()))
    single_rc = sorted(k for k, v in families.items()
                       if v["single_rc_supported_within_family"])
    return crossing_anywhere, none_anywhere, single_rc


def build_conclusion(families, strata, stability, adalora):
    llava = families["llava-1.5-7b"]
    prim = strata["llava_blank3ep_cloud10"]
    q2 = families["qwen2-vl-2b"]
    clip = families["clip-vit-base-patch32"]
    crossing_anywhere, none_anywhere, single_rc = _family_classes(families)
    q2_blank_eval = q2["strata"]["qwen2b_p3d_blank_eval"]
    curv = stability["curvature_observable"]
    per_family_ok = ("LLaVA-1.5-7B is the one family in which a crossing can be bracketed under a "
                     "named protocol, and even there the stratum spread runs from %.2f to %.2f, so "
                     "no single r_c holds inside the family"
                     % (llava["sensitivity_span"][0], llava["sensitivity_span"][1]))
    return {
        "what_may_be_claimed_about_rc": [
            "Within the LLaVA-1.5-7B blank-image protocol at the archived operating point, the "
            "sign of dE changes between r=%d and r=%d; the ten-seed fit puts the crossing at "
            "%.3f (95%% bootstrap CI %s), bracketed by those two ranks and not localised to one."
            % (prim["crossing_bracket"][0], prim["crossing_bracket"][1], prim["crossing_point"],
               json.dumps(prim["bootstrap"]["ci95"])),
            "The sign split at the bracket is complete in that stratum: %s."
            % json.dumps(stability["primary_stratum_sign_unanimity"], sort_keys=True),
            "The re-run family (five seeds, current script defaults) places the crossing at "
            "%.3f, inside the same bracket."
            % strata["llava_rerun5"]["crossing_point"],
            "Outside that protocol the crossing moves: %s"
            % ", ".join("%s -> %s" % (k, json.dumps(v))
                        for k, v in sorted(llava["crossing_points_by_stratum"].items())),
        ],
        "what_may_not_be_claimed_about_rc": [
            "r_c is not a single number across backbones. Of the %d families, %d contain at least "
            "one stratum with a sign crossing (%s), %d contain none anywhere in their measured "
            "rank range (%s), and only %d yields one well-defined crossing (%s). %s."
            % (len(families), len(crossing_anywhere), json.dumps(crossing_anywhere),
               len(none_anywhere), json.dumps(none_anywhere), len(single_rc),
               json.dumps(single_rc), per_family_ok),
            "Qwen2-VL-2B: in the training-energy field the sign of dE is set by the image "
            "condition, not by the rank - every rank r=1..16 is positive with real images and "
            "negative with blank ones, so no crossing exists there. The held-out energy field "
            "does contain one crossing, at %.3f, but it sits in a single bracket %s whose "
            "bootstrap CI %s spans more than a rank, so it does not localise r_c either."
            % (q2_blank_eval["crossing_point"], json.dumps(q2_blank_eval["crossing_bracket"]),
               json.dumps(q2_blank_eval["bootstrap"]["ci95"])),
            "The CLIP ViT-B/32 retrieval arm never crosses in any of its four strata: the sign of its "
            "energy change is set by the training window and by which energy is read (training "
            "energy positive at 16 pairs and negative at 1024; held-out energy negative at both), "
            "never by the rank, so it cannot corroborate any rank threshold.",
            "The curvature observable on the same LLaVA backbone does not corroborate a rank "
            "threshold either: on the primary seed line the second-order share is negative at "
            "every archived rank in %s and rises monotonically toward zero without crossing it "
            "(%s), and the manuscript's own claim table already records that the sign is not "
            "stable across seeds at this step."
            % (json.dumps(curv["ranks_measured"]),
               "monotone rising toward zero: %s"
               % json.dumps(curv["primary_seed_curve_share_by_rank"]["eps_0.001"]
                            ["monotone_rising_toward_zero"])),
            "r_c is not even stable inside LLaVA: the five-seed stratum means at r=5 are not a "
            "cross-environment constant (stack means %s; software-stack share of the r=5 variance "
            "%.2f, 95%% CI %s)."
            % (json.dumps(stability["environment_share_of_r5_variance"]["stack_means_at_r5"],
                          sort_keys=True),
               stability["environment_share_of_r5_variance"]["env_share"],
               json.dumps(stability["environment_share_of_r5_variance"]["share_ci95"])),
        ],
        "what_may_be_claimed_about_adalora": [
            "In every archived cell where AdaLoRA and the Gamma-guided rule share budget, "
            "learning rate and seed (%d cells), AdaLoRA reaches the lower alignment energy: the "
            "per-cell difference runs %s, mean %.1f, 95%% t CI %s."
            % (adalora["summary"]["n_matched_cells"],
               json.dumps([r["difference_adalora_minus_gamma"] for r in adalora["matched_cells"]]),
               adalora["summary"]["mean_difference"], json.dumps(adalora["summary"]["ci95_t"])),
            "The direction is consistent but the archived comparison is under-powered: with %d "
            "matched cells the exact two-sided sign test bottoms out at p=%.3f, so the AdaLoRA advantage "
            "is reported as a consistent direction, not as a significant one."
            % (adalora["summary"]["n_matched_cells"],
               adalora["summary"]["exact_sign_test_two_sided_p"]),
            "The Gamma-guided rule does beat the published non-adaptive allocation rules at the "
            "shared base-rank-1 arm: its arm is %s against %s."
            % (adalora["published_baseline_rules"]["gamma_arm_delta_E"],
               json.dumps([(r["rule"], r["delta_E"])
                           for r in adalora["published_baseline_rules"]["rows"]
                           if not r["rule"].startswith("Gamma-guided")])),
        ],
        "what_may_not_be_claimed_about_adalora": [
            "The comparison is confounded: the AdaLoRA arm runs the uniform rank-4 plan on all "
            "%d modules, the same rank plan as the plain uniform control, so it does not isolate "
            "adaptive rank allocation from block configuration."
            % adalora["comparison_plane"]["adalora_config"]["n_modules"],
            "It does not reverse on the energy axis at any archived learning rate or seed, but it "
            "does reverse in the neighbouring comparison: plain uniform rank beats the Gamma rule "
            "in %d archived cells (%s)."
            % (adalora["reversal_regime"]
               ["n_cells_where_plain_uniform_beats_the_gamma_rule"],
               json.dumps([[c["lr"], c["seed"]] for c in adalora["reversal_regime"]["cells"]])),
            "No matched-loss claim is available: the two scripts do not start from the same "
            "first-epoch loss, so the loss ordering between them is not comparable.",
            "The AdaLoRA arm is not exactly on budget under measurement (%.4f%% above the cost "
            "model), so budget matching holds only in the cost model."
            % (100.0 * (adalora["comparison_plane"]["adalora_config"]["n_trainable_measured"]
                        - adalora["comparison_plane"]["adalora_config"]["target_budget_params"])
               / adalora["comparison_plane"]["adalora_config"]["target_budget_params"]),
        ],
        "families_with_a_crossing_in_at_least_one_stratum": crossing_anywhere,
        "families_with_no_crossing_anywhere": none_anywhere,
        "families_with_one_well_defined_rc": single_rc,
        "families_agree": bool(len(single_rc) == len(families)),
        "single_rc_across_families_supported": False,
    }


# --------------------------------------------------------------------------------------
# insertion points in the live manuscript (read-only)
# --------------------------------------------------------------------------------------


ANCHORS = [
    {"key": "main_text_finding1", "file": "paper3/paper_ieee/sections/experiments.tex",
     "label": "sec:experiments, subsection 'Alignment Phase Transition', paragraph 'Finding 1'",
     "start": r"\\textbf\{Finding 1:",
     "end": r"belongs to the measurement protocol rather than to the model\.",
     "role": "the sentence that already says the crossing belongs to the protocol; the family "
             "boundary belongs immediately after it"},
    {"key": "main_text_adalora", "file": "paper3/paper_ieee/sections/experiments.tex",
     "label": "sec:experiments, paragraph 'An adaptive baseline is better on this metric'",
     "start": r"\\textbf\{An adaptive baseline is better on this metric",
     "end": r"run decreases monotonically\.",
     "role": "the AdaLoRA concession; the confound and the uniform reversal belong inside it"},
    {"key": "supp_claim_table", "file": "paper3/paper_ieee/supplementary/supplementary.tex",
     "label": "app:claims, table tab:claims",
     "start": r"AdaLoRA is worse than our arms",
     "end": r"AdaLoRA is worse than our arms",
     "role": "the existing claim row; the family-boundary rows join this table"},
    {"key": "supp_crossing10_end", "file": "paper3/paper_ieee/supplementary/supplementary.tex",
     "label": "end of app:crossing10 / start of app:highrank",
     "start": r"\\section\{Curvature at high rank\}",
     "end": r"\\section\{Curvature at high rank\}",
     "role": "insertion point for a new Section app:rc-boundary, immediately after the ten-seed "
             "crossing section and before the curvature section"},
    {"key": "supp_sharegpt_caption", "file": "paper3/paper_ieee/supplementary/supplementary.tex",
     "label": "app:sharegpt, caption of tab:sharegpt",
     "start": r"Phase transition on ShareGPT",
     "end": r"reproducing the Alpaca critical rank",
     "role": "the caption that states a flip between r=5 and r=6 while its own means flip between "
             "r=4 and r=5"},
    {"key": "supp_clip_control", "file": "paper3/paper_ieee/supplementary/supplementary.tex",
     "label": "sec:supp-rank-control, opening sentence",
     "start": r"The main text reports a critical rank for LLaVA-1.5-7B under the blank-image protocol",
     "end": r"we ran the",
     "role": "the CLIP control; the zero-crossing absence over r=1..16 is its quantitative form"},
    {"key": "discussion_limitations", "file": "paper3/paper_ieee/sections/discussion.tex",
     "label": "discussion, limitations paragraph item (6)",
     "start": r"Several limitations delineate",
     "end": r"rather than a universal constant\.",
     "role": "the environment-sensitivity admission; the family-sensitivity admission joins it"},
    {"key": "appendix_critical_threshold", "file": "paper3/paper_ieee/sections/appendix.tex",
     "label": "appendix, counterfactual allocation paragraph",
     "start": r"the largest rank safely below the critical",
     "end": r"threshold \$r_c \\in \[5,6\]\$\.",
     "role": "where the allocation is justified by 'below the critical threshold'; that phrase "
             "must carry the family qualifier"},
    {"key": "abstract_line", "file": "paper3/paper_ieee/main.tex",
     "label": "abstract, AdaLoRA sentence",
     "start": r"AdaLoRA, swept over the same rates",
     "end": r"AdaLoRA, swept over the same rates",
     "role": "abstract scope; leave untouched unless the boundary table is promoted to the letter"},
]


def _anchor_re(pat: str):
    """Anchor patterns are literal prose plus a few regex escapes; a space may be a newline."""
    return re.compile(pat.replace(" ", r"\s+"))


def _line_of(text: str, off: int) -> int:
    return text.count("\n", 0, off) + 1


def locate_anchors():
    out = []
    for a in ANCHORS:
        text = read_text(a["file"])
        ms = _anchor_re(a["start"]).search(text)
        if ms is None:
            raise SystemExit("[p1635] anchor %s: start pattern not found in %s"
                             % (a["key"], a["file"]))
        me = _anchor_re(a["end"]).search(text, ms.start())
        if me is None:
            raise SystemExit("[p1635] anchor %s: end pattern not found after start in %s"
                             % (a["key"], a["file"]))
        s = _line_of(text, ms.start())
        e = _line_of(text, me.end() - 1)
        if e < s:
            e = s
        out.append({"key": a["key"], "file": a["file"], "label": a["label"],
                    "line_range": [s, e], "role": a["role"],
                    "insertion": ("after line %d (end of the anchored block)" % e
                                  if s != e else "at line %d" % s)})
    return out


# --------------------------------------------------------------------------------------
# planning, printing and writing
# --------------------------------------------------------------------------------------


def plan_lines():
    out = []
    out.append("PLAN -- tools/_p1635_p3_rc_family.py")
    out.append("")
    out.append("1. --refit  re-estimate r_c inside each backbone family")
    out.append("   estimator : zero of the mean dE-versus-rank curve, linear interpolation")
    out.append("               between the two adjacent measured ranks that bracket zero")
    out.append("   dE        : E[-1] - E[0]")
    out.append("   bootstrap : %d draws, paired resampling of the stratum's unit, RNG seed %d"
               % (N_BOOT, BOOT_SEED))
    out.append("   strata    : %d declared, %d backbones" % (len(STRATUM_BUILDERS),
                                                             len(FAMILY_META)))
    for sid, _fn in STRATUM_BUILDERS:
        out.append("               - %s" % sid)
    out.append("")
    out.append("2. --adalora  build the boundary-condition table")
    out.append("   matched cells : (learning rate, seed) present for BOTH the AdaLoRA archive")
    out.append("                   and the Gamma-guided archive, same budget and same E0")
    out.append("   sources       : %s" % ", ".join(sorted({
        ANA + "/p3_alloc_runs/adalora_summary.json",
        ANA + "/p3_alloc_runs/adalora_lr0.0003/adalora_summary.json",
        ANA + "/p3_alloc_runs/adalora_lr0.001/adalora_summary.json",
        ANA + "/p3_alloc_runs/main/summary.json",
        ANA + "/p3_alloc_runs/exp_lr0.0003/summary.json",
        ANA + "/p3_alloc_runs/exp_lr0.001/summary.json",
        ANA + "/p3_alloc_runs/uniform_lr0.0003/summary.json",
        ANA + "/p3_alloc_runs/uniform_lr0.001/summary.json",
        ANA + "/p3_alloc_adalora_config.json",
        ANA + "/p3_baseline_arms.json",
        ANA + "/p3_robust_stats.json",
        EXP + "/verify_r1_s42_ntk_arm.json",
        EXP + "/verify_r1_s42_bcexplicit_v12_s1_m2_d1.json",
    })))
    out.append("")
    out.append("3. --stability  independent observables on the same crossing")
    out.append("   sources       : %s" % ", ".join(sorted({
        ANA + "/p3_rank_separation_extended.json",
        ANA + "/p3_env_variance.json",
        ANA + "/p3_gapfill_summary.json",
        ANA + "/p3_hessian_probe_r*.json",
    })))
    out.append("")
    out.append("4. writes")
    out.append("   json : %s" % OUT_JSON)
    out.append("   md   : %s" % OUT_MD)
    out.append("")
    out.append("insertion-point anchors to be located in the live manuscript:")
    for a in ANCHORS:
        exists = "ok" if (REPO / a["file"]).exists() else "MISSING"
        out.append("   [%s] %-52s %s" % (exists, a["key"], a["file"]))
    out.append("")
    out.append("archive existence pre-check:")
    for rel in sorted({ANA + "/p3_alloc_results.json",
                       ANA + "/p3_multiseed_family.json",
                       EXP + "/E2_results.json",
                       EXP + "/ers_1epoch_results.json",
                       ANA + "/p3_hessian_probe_r24.json",
                       ANA + "/p3_hessian_probe_r64_s42.json",
                       ANA + "/p3_adalora_verified.json"}):
        state = "ok" if (REPO / rel).exists() else "MISSING"
        out.append("   [%s] %s" % (state, rel))
    out.append("")
    out.append("note: the task brief named two paths that do not exist; both are recorded in")
    out.append("      meta.path_discrepancies_in_the_task_brief:")
    out.append("        ers_1epoch_results.json                    -> " + EXP +
               "/ers_1epoch_results.json")
    out.append("        outputs/analysis/p3_hessian_probe_r64.json -> " + ANA +
               "/p3_hessian_probe_r64_s42.json")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refit", action="store_true",
                    help="re-estimate r_c inside each family (always written to the JSON)")
    ap.add_argument("--adalora", action="store_true",
                    help="build the AdaLoRA boundary table (always written to the JSON)")
    ap.add_argument("--dry-run", action="store_true", help="print the plan and exit")
    args = ap.parse_args(argv)

    if args.dry_run:
        for ln in plan_lines():
            print(ln)
        return 0
    if not (args.refit or args.adalora):
        print("[p1635] nothing selected: pass --refit and/or --adalora (or --dry-run)")
        return 2

    families, strata, provenance = build_rc_by_family()
    stability = build_stability(families, strata)
    adalora = build_adalora_boundary()
    conclusion = build_conclusion(families, strata, stability, adalora)
    anchors = locate_anchors()

    sources = []
    seen = set()
    for a in _ALL_ARCHIVES:
        r = a.record()
        if r["path"] in seen:
            continue
        seen.add(r["path"])
        sources.append(r)
    sources.sort(key=lambda r: r["path"])

    doc = {
        "meta": {
            "script": "tools/_p1635_p3_rc_family.py",
            "task": "P3 reviewer objection: the critical rank may come from another family, and "
                    "AdaLoRA reaches lower alignment energy than the Gamma-guided allocation",
            "scope": "archives only; no manuscript file is modified",
            "dE_convention": "dE = E[-1] - E[0]",
            "estimator": {
                "name": "piecewise-linear zero of the mean dE-versus-rank curve",
                "point": "r_lo + (0 - m_lo) / (m_hi - m_lo) * (r_hi - r_lo) for the first adjacent "
                         "pair with m_lo < 0 <= m_hi",
                "bracket": "[r_lo, r_hi]",
                "reporting_rule": "a stratum whose means never change sign is reported as "
                                  "'no_crossing_in_range' with the measured rank range; its r_c is "
                                  "not estimated and not bounded",
                "reverse_crossings": "positive-to-negative steps are recorded separately and are "
                                     "not used as r_c",
            },
            "bootstrap": {"n_boot": N_BOOT, "rng_seed": BOOT_SEED,
                          "unit": "the stratum's declared unit (seed label or training window), "
                                  "resampled jointly across ranks so the pairing survives",
                          "interval": "percentile 2.5 / 97.5"},
            "operating_lr_for_curvature_rescaling": OPERATING_LR,
            "allocation_study_backbone": ADALORA_FAMILY,
            "not_sourced": [
                {"item": "whether peft applied the orthogonality regulariser",
                 "detail": "tools/_p451_baseline_adalora.py configures orth_reg_weight=0.5 in the "
                           "peft AdaLoraConfig but back-propagates the manually computed "
                           "cross-entropy only; no archive records whether the regulariser reached "
                           "the loss, so the AdaLoRA arm is described as configured, not as "
                           "regularised",
                 "status": "not asserted"},
                {"item": "seed labels of the ShareGPT and one-epoch strata",
                 "detail": ANA + "/vqa_phase_results.json and " + EXP +
                           "/ers_1epoch_results.json store dE as positional lists under r<rank>, "
                           "with no seed field; the refit uses the list index as the unit label and "
                           "the pairing is positional",
                 "status": "unit labels are positional, not archived"},
                {"item": "the model label of the cloud Qwen sweep",
                 "detail": ANA + "/Qwen_results.json has no model field; 'Qwen2-VL-7B' comes from "
                           "the manuscript phase table and " + ANA +
                           "/p3_phase_boundary.json :: meta.archive_files.Qwen",
                 "status": "inferred"},
                {"item": "a matched-loss comparison between AdaLoRA and the Gamma rule",
                 "detail": "the two scripts do not start from the same first-epoch loss at the "
                           "same seed, so no matched-loss statement is available from the archives",
                 "status": "not available"},
                {"item": "whether the three published-rule arms are parameter-matched",
                 "detail": ANA + "/p3_baseline_arms.json and the manuscript both call the base-"
                           "rank-1 arm comparison directional; the archives carry no parameter "
                           "count for those arms",
                 "status": "not available"},
            ],
            "sources": sources,
            "provenance": provenance,
            "path_discrepancies_in_the_task_brief": [
                {"named": "ers_1epoch_results.json", "actual": EXP + "/ers_1epoch_results.json",
                 "note": "the file is under the experiments directory, not at the repository root"},
                {"named": "outputs/analysis/p3_hessian_probe_r64.json",
                 "actual": ANA + "/p3_hessian_probe_r64_s42.json",
                 "note": "the r=64 probe archive carries a seed suffix; the unsuffixed name does "
                         "not exist"},
            ],
            "task_brief_archives_verified": [
                {"path": EXP + "/E2_results.json", "exists": True},
                {"path": EXP + "/ers_1epoch_results.json", "exists": True},
                {"path": EXP + "/cloud_verify_r*.json",
                 "exists": True,
                 "n_files": len(list((REPO / EXP).glob("cloud_verify_r*_s*.json")))},
                {"path": ANA + "/p3_alloc_results.json", "exists": True},
                {"path": ANA + "/p3_alloc_runs/*/summary.json",
                 "exists": True,
                 "n_files": len(list((REPO / ANA).glob("p3_alloc_runs/*/summary.json")))},
                {"path": ANA + "/p3_hessian_probe_r24.json", "exists": True},
                {"path": ANA + "/p3_hessian_probe_r64_s42.json", "exists": True},
            ],
            "rerun_stable": "no timestamps, sorted keys, fixed bootstrap RNG seed",
        },
        "family_list": sorted(families),
        "rc_by_family": families,
        "stability": stability,
        "adalora_boundary": adalora,
        "conclusion": conclusion,
        "insertion_points": anchors,
    }

    out_path = REPO / OUT_JSON
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")

    md = render_markdown(doc)
    md_path = REPO / OUT_MD
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with md_path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(md)

    # ---- read the JSON back and print only from it ------------------------------------
    with out_path.open(encoding="utf-8") as fh:
        back = json.load(fh)
    if back != doc:
        raise SystemExit("[p1635] JSON round-trip mismatch")
    verify_printed_numbers(back)
    print_report(back, args)
    print("[p1635] wrote %s (%d bytes)" % (OUT_JSON, out_path.stat().st_size))
    print("[p1635] wrote %s (%d bytes)" % (OUT_MD, md_path.stat().st_size))
    print("[p1635] self-check: every printed number was read back out of %s" % OUT_JSON)
    return 0


# every Archive that gets constructed is registered here so meta.sources is complete
_ALL_ARCHIVES: list[Archive] = []
_ORIG_INIT = Archive.__init__


def _register_init(self, rel):
    _ORIG_INIT(self, rel)
    _ALL_ARCHIVES.append(self)


Archive.__init__ = _register_init


# --------------------------------------------------------------------------------------
# console report -- numbers come from the JSON document, never recomputed
# --------------------------------------------------------------------------------------


def print_report(doc, args):
    m, fam = doc["meta"], doc["rc_by_family"]
    print("=" * 96)
    print("P3 r_c by family, and the AdaLoRA boundary  (%s)" % m["script"])
    print("=" * 96)
    print("dE convention: %s   |   estimator: %s" % (m["dE_convention"],
                                                     m["estimator"]["name"]))
    print()
    print("-- r_c per family ---------------------------------------------------------------")
    for name in sorted(fam):
        f = fam[name]
        print("%-24s %s" % (name, f["backbone"]))
        for sid in sorted(f["strata"]):
            s = f["strata"][sid]
            ci = s["bootstrap"].get("ci95")
            print("    %-32s bracket=%-10s point=%-8s ci95=%-22s %s"
                  % (sid, s["crossing_bracket"], s["crossing_point"], ci, s["status"]))
        print("    -> family estimate: %s  ci95=%s  single r_c supported: %s"
              % (f["family_estimate"], f["family_estimate_ci95"],
                 f["single_rc_supported_within_family"]))
        if f["why_not_single"]:
            print("       why not: %s" % f["why_not_single"])
    print()
    print("-- stability --------------------------------------------------------------------")
    st = doc["stability"]
    print("primary stratum sign unanimity: %s" % json.dumps(
        st["primary_stratum_sign_unanimity"], sort_keys=True))
    t = st["archived_exact_tests_on_the_same_runs"]
    print("archived exact tests: %d/%d pairs separate (Holm %d), p_min=%.3g, refit matches "
          "archived means: %s"
          % (t["n_separating_raw_p05"], t["n_pairs"], t["n_separating_holm_p05"],
             t["p_min_attainable"], t["refit_reproduces_archived_means"]))
    env = st["environment_share_of_r5_variance"]
    print("environment share of r=5 variance: %.4f  ci95=%s"
          % (env["env_share"], json.dumps(env["share_ci95"])))
    cur = st["curvature_observable"]
    print("curvature observable: ranks %s, no zero crossing on the primary seed line: %s, "
          "sign unanimous: %s, tab:hessian reproduced: %s"
          % (json.dumps(cur["ranks_measured"]),
             cur["no_zero_crossing_on_the_primary_seed_curve"],
             cur["sign_unanimous_across_batches_and_seeds"],
             cur["manuscript_tab_hessian_check"]["reproduces_manuscript_to_4dp"]))
    for c in st["manuscript_consistency_checks"]:
        print("manuscript check: agrees=%s  %s" % (c["agrees"], c["claim"][:88]))
    print()
    print("-- AdaLoRA boundary -------------------------------------------------------------")
    ad = doc["adalora_boundary"]
    print("plane: %s  budget=%d  epochs=%d"
          % (ad["comparison_plane"]["backbone"], ad["comparison_plane"]["budget_params"],
             ad["comparison_plane"]["epochs"]))
    print("adalora and uniform share one rank plan: %s"
          % ad["comparison_plane"]["adalora_and_uniform_share_one_rank_plan"])
    for r in ad["matched_cells"]:
        print("    lr=%-8g seed=%-5d adalora=%-10.2f gamma=%-10.2f diff=%-10.2f %s (gamma-vs-"
              "uniform: %s)"
              % (r["lr"], r["seed"], r["adalora_delta_E"], r["gamma_delta_E"],
                 r["difference_adalora_minus_gamma"], r["sign"], r["gamma_vs_uniform_sign"]))
    s = ad["summary"]
    print("summary: %d/%d cells AdaLoRA lower, mean diff %.2f, ci95 %s, exact sign p=%.3f "
          "(reaches p<0.05: %s)"
          % (s["n_cells_adalora_lower"], s["n_matched_cells"], s["mean_difference"],
             json.dumps(s["ci95_t"]), s["exact_sign_test_two_sided_p"],
             s["exact_sign_test_reaches_p05"]))
    rr = ad["reversal_regime"]
    print("reversal regime (plain uniform beats the rule): %d cells %s"
          % (rr["n_cells_where_plain_uniform_beats_the_gamma_rule"],
             json.dumps([[c["lr"], c["seed"]] for c in rr["cells"]])))
    pb = ad["published_baseline_rules"]
    print("published-baseline arms vs the Gamma arm (%s): %d above, %d below"
          % (pb["gamma_arm_delta_E"], pb["n_rules_above_the_gamma_arm"],
             pb["n_rules_below_the_gamma_arm"]))
    for r in pb["rows"]:
        print("    %-56s delta_E=%-9.1f %s" % (r["rule"][:56], r["delta_E"],
                                               r["sign_vs_gamma_arm"]))
    print()
    print("-- conclusion -------------------------------------------------------------------")
    c = doc["conclusion"]
    for k in ("what_may_be_claimed_about_rc", "what_may_not_be_claimed_about_rc",
              "what_may_be_claimed_about_adalora", "what_may_not_be_claimed_about_adalora"):
        print("[%s]" % k)
        for line in c[k]:
            print("   * %s" % line)
    print("families agree: %s   single r_c across families supported: %s"
          % (c["families_agree"], c["single_rc_across_families_supported"]))
    print()
    print("-- insertion points (live manuscript, read-only) --------------------------------")
    for a in doc["insertion_points"]:
        print("    %-28s %s  lines %s  %s" % (a["key"], a["file"],
                                              a["line_range"], a["insertion"]))
    print()


def verify_printed_numbers(doc):
    """Assert the numbers the report leans on are internally consistent in the document."""
    # every stratum's crossing point must reproduce from the means it stores
    for fam, f in doc["rc_by_family"].items():
        for sid, s in f["strata"].items():
            mb = s["mean_dE_by_rank"]
            if s["crossing_point"] is None:
                if s["crossing_bracket"] is not None:
                    raise SystemExit("[p1635] %s/%s: no point but a bracket" % (fam, sid))
                if s["status"] != "no_crossing_in_range":
                    raise SystemExit("[p1635] %s/%s: unexpected status %s" % (fam, sid, s["status"]))
                if s["bootstrap"].get("ci95") is not None:
                    raise SystemExit("[p1635] %s/%s: interval quoted without a crossing"
                                     % (fam, sid))
                continue
            lo, hi = s["crossing_bracket"]
            expect = lo + (0 - mb[str(lo)]) / (mb[str(hi)] - mb[str(lo)]) * (hi - lo)
            if abs(expect - s["crossing_point"]) > 1e-6:
                raise SystemExit("[p1635] %s/%s: crossing point does not reproduce from the means"
                                 % (fam, sid))
            if not mb[str(lo)] < 0 <= mb[str(hi)]:
                raise SystemExit("[p1635] %s/%s: stored bracket does not straddle zero" % (fam, sid))
        pts = [s["crossing_point"] for s in f["strata"].values()
               if s["crossing_point"] is not None]
        if pts and f["sensitivity_span"] != [min(pts), max(pts)]:
            raise SystemExit("[p1635] %s: sensitivity span does not match the strata" % fam)
        if f["single_rc_supported_within_family"] != (f["common_intersection_of_stratum_ci95"]
                                                      is not None and len(pts) == len(f["strata"])):
            raise SystemExit("[p1635] %s: the within-family verdict does not follow" % fam)

    # the family classes must be a partition of the family list
    c = doc["conclusion"]
    a = set(c["families_with_a_crossing_in_at_least_one_stratum"])
    b = set(c["families_with_no_crossing_anywhere"])
    d = set(c["families_with_one_well_defined_rc"])
    if a & b or d - a or a | b != set(doc["family_list"]):
        raise SystemExit("[p1635] the family classes are not consistent")
    if c["single_rc_across_families_supported"] != bool(len(d) == len(doc["family_list"])):
        raise SystemExit("[p1635] the cross-family verdict does not follow from the classes")

    # the AdaLoRA table
    ad = doc["adalora_boundary"]
    for r in ad["matched_cells"]:
        if abs((r["adalora_delta_E"] - r["gamma_delta_E"])
               - r["difference_adalora_minus_gamma"]) > 1e-6:
            raise SystemExit("[p1635] matched-cell difference does not reproduce")
        want = ("adalora_lower_delta_E" if r["difference_adalora_minus_gamma"] < 0
                else "gamma_lower_delta_E" if r["difference_adalora_minus_gamma"] > 0 else "tie")
        if r["sign"] != want:
            raise SystemExit("[p1635] matched-cell sign does not follow from the difference")
        if r["same_E0"] is not True:
            raise SystemExit("[p1635] a matched cell does not share E0")
    s = ad["summary"]
    n = len(ad["matched_cells"])
    if n != s["n_matched_cells"] or abs(2 / (2 ** n) - s["exact_sign_test_two_sided_p"]) > 1e-9:
        raise SystemExit("[p1635] sign-test summary does not reproduce")
    if s["n_cells_adalora_lower"] != sum(
            1 for r in ad["matched_cells"] if r["difference_adalora_minus_gamma"] < 0):
        raise SystemExit("[p1635] the AdaLoRA-wins count does not reproduce")
    if s["reverses_on_the_delta_E_axis"] != bool(
            0 < s["n_cells_adalora_lower"] < s["n_matched_cells"]):
        raise SystemExit("[p1635] the 'reverses on the energy axis' flag does not follow")
    rr = ad["reversal_regime"]
    if rr["n_cells_where_plain_uniform_beats_the_gamma_rule"] != sum(
            1 for r in ad["gamma_vs_uniform_cells"] if r["sign"] == "uniform_lower"):
        raise SystemExit("[p1635] the reversal count does not reproduce")
    if rr["n_cells_where_plain_uniform_beats_the_gamma_rule"] != len(rr["cells"]):
        raise SystemExit("[p1635] the reversal cells do not match the reversal count")
    # the published-rule table must not silently include the Gamma row as a competitor
    pb = ad["published_baseline_rules"]
    if pb["n_rules_above_the_gamma_arm"] != sum(
            1 for r in pb["rows"] if r["sign_vs_gamma_arm"] == "gamma_lower"):
        raise SystemExit("[p1635] the published-rule count does not reproduce")

    # the curvature statement
    cur = doc["stability"]["curvature_observable"]
    line = cur["primary_seed_curve_share_by_rank"]["eps_0.001"]["values_by_rank"]
    if cur["no_zero_crossing_on_the_primary_seed_curve"] != all(v < 0 for v in line.values()):
        raise SystemExit("[p1635] the curvature no-crossing flag does not follow")
    if cur["sign_unanimous_across_batches_and_seeds"] != (not cur["significant_flips"]):
        raise SystemExit("[p1635] the curvature unanimity flag does not follow")


# --------------------------------------------------------------------------------------
# the Markdown draft
# --------------------------------------------------------------------------------------


def _cell(fam, sid, family="llava-1.5-7b"):
    return fam[family]["strata"][sid]


def render_markdown(doc):
    J = "outputs/analysis/p3_rc_family_boundary.json"
    fam = doc["rc_by_family"]
    prim = _cell(fam, "llava_blank3ep_cloud10")
    rerun = _cell(fam, "llava_rerun5")
    ad = doc["adalora_boundary"]
    st = doc["stability"]
    c = doc["conclusion"]
    e0 = ad["comparison_plane"]["E0_shared_by_every_cell_on_this_plane"]
    ident = ("E0 = %g" % e0[0]) if len(e0) == 1 else ("E0 in %s" % json.dumps(e0))

    L = []
    A = L.append
    A("# P3 — critical rank by family, and the AdaLoRA boundary")
    A("")
    A("English draft text for the supplement, generated by `%s`." % doc["meta"]["script"])
    A("Every number carries the field path of `%s` that holds it." % J)
    A("No manuscript file is modified by this document or by that script.")
    A("")
    A("## 1. LaTeX-ready paragraph (supplement)")
    A("")
    A("> **Draft sentence, ready to paste.** The critical rank is not a single number, and the "
      "archive says so in two independent ways. Inside LLaVA-1.5-7B, the ten-seed refit places the "
      "sign change of $\\Delta E$ at $r_c=%.3f$ (95\\%% paired-seed bootstrap CI $%s$), bracketed by "
      "$r=%d$ and $r=%d$ (`rc_by_family.llava-1.5-7b.strata.llava_blank3ep_cloud10.crossing_point`, "
      "`.crossing_bracket`, `.bootstrap.ci95`); the five-seed re-run on the current script defaults "
      "gives $%.3f$ inside the same bracket (`.strata.llava_rerun5.crossing_point`). Outside that "
      "one protocol the crossing moves, from $%.2f$ on the ShareGPT stratum to $%.2f$ on the "
      "one-epoch stratum "
      "(`rc_by_family.llava-1.5-7b.sensitivity_span`), so what the data support is a bracketed "
      "crossing under a named protocol, not a model constant. Across backbones it is weaker "
      "still: of the %d families examined, %d contain a crossing in at least one stratum, %d "
      "contain none anywhere in their measured rank range (%s), and only %d yields a single "
      "well-defined crossing "
      "(`conclusion.families_with_a_crossing_in_at_least_one_stratum`, "
      "`.families_with_no_crossing_anywhere`, `.families_with_one_well_defined_rc`). On "
      "Qwen2-VL-2B the sign of $\\Delta E$ is set by the image condition rather than by the rank — "
      "in the training-energy field every rank $r=1..16$ is positive with real images and negative "
      "with blank ones "
      "(`rc_by_family.qwen2-vl-2b.strata.qwen2b_p3d_real_train.sign_of_all_means`, "
      "`.strata.qwen2b_p3d_blank_train.sign_of_all_means`) — and the CLIP ViT-B/32 retrieval arm "
      "likewise shows no zero crossing over $r=1..16$ in any of its four strata, its sign being set "
      "by the training window and by which energy is read rather than by the rank "
      "(`rc_by_family.clip-vit-base-patch32.strata.*.sign_of_all_means`). We therefore restrict $r_c\\in[%d,%d]$ to the LLaVA "
      "configuration and protocol under which it was measured. On the adaptive baseline, the "
      "archived comparison does not reverse on the energy axis: in all %d cells where AdaLoRA and "
      "the $\\Gamma$-guided rule share budget, learning rate and seed, AdaLoRA reaches the lower "
      "alignment energy (per-cell differences $%s$, mean $%.1f$, 95\\%% $t$ CI $%s$; "
      "`adalora_boundary.matched_cells[*].difference_adalora_minus_gamma`, `.summary.mean_difference`, "
      "`.summary.ci95_t`). That comparison is under-powered — with $n=%d$ cells the exact two-sided "
      "sign test bottoms out at $p=%.3f$ — and it is confounded, because the AdaLoRA arm runs the "
      "uniform rank-4 plan on all %d modules, the same rank plan as our plain uniform control "
      "(`adalora_boundary.comparison_plane.adalora_and_uniform_share_one_rank_plan`). In the "
      "neighbouring comparison the ordering does reverse: plain uniform rank beats the "
      "$\\Gamma$-guided rule in %d archived cells, %s "
      "(`adalora_boundary.reversal_regime.cells`, `.reversal_regime.regime`). Against the published "
      "non-adaptive allocation rules at the shared base-rank-1 arm the $\\Gamma$ arm is the lowest "
      "of the set "
      "(`adalora_boundary.published_baseline_rules.rows[*].delta_E`)."
      % (prim["crossing_point"], json.dumps(prim["bootstrap"]["ci95"]),
         prim["crossing_bracket"][0], prim["crossing_bracket"][1],
         rerun["crossing_point"],
         fam["llava-1.5-7b"]["sensitivity_span"][0], fam["llava-1.5-7b"]["sensitivity_span"][1],
         len(fam), len(c["families_with_a_crossing_in_at_least_one_stratum"]),
         len(c["families_with_no_crossing_anywhere"]),
         " and ".join("\\texttt{%s}" % f for f in c["families_with_no_crossing_anywhere"]),
         len(c["families_with_one_well_defined_rc"]),
         prim["crossing_bracket"][0], prim["crossing_bracket"][1],
         ad["summary"]["n_matched_cells"],
         json.dumps([r["difference_adalora_minus_gamma"] for r in ad["matched_cells"]]),
         ad["summary"]["mean_difference"], json.dumps(ad["summary"]["ci95_t"]),
         ad["summary"]["n_matched_cells"], ad["summary"]["exact_sign_test_two_sided_p"],
         ad["comparison_plane"]["adalora_config"]["n_modules"],
         ad["reversal_regime"]["n_cells_where_plain_uniform_beats_the_gamma_rule"],
         _regime_latex(ad["reversal_regime"]["cells"])))
    A("")
    A("## 2. Compact boundary table (LaTeX)")
    A("")
    A("%d useful rows — the matched AdaLoRA-versus-$\\Gamma$ cells, which are what the objection "
      "is about, so the table stays inside the six-row budget. The %d cells in which plain "
      "uniform rank reverses the ordering against the rule are given in the sentence below the "
      "table rather than as further rows. `%s`."
      % (len(ad["matched_cells"]),
         ad["reversal_regime"]["n_cells_where_plain_uniform_beats_the_gamma_rule"], J))
    A("")
    A("```latex")
    A("\\begin{table}[t]")
    A("\\centering\\footnotesize")
    A("\\begin{tabular}{@{}llrrl@{}}")
    A("\\toprule")
    A("$\\eta$ & seed & $\\Delta E_{\\rm AdaLoRA}$ & $\\Delta E_{\\Gamma}$ & sign \\\\")
    A("\\midrule")
    for r in ad["matched_cells"]:
        A("$%s$ & %d & $%+.0f$ & $%+.0f$ & AdaLoRA lower \\\\"
          % (_eta(r["lr"]), r["seed"], r["adalora_delta_E"], r["gamma_delta_E"]))
    A("\\bottomrule")
    A("\\end{tabular}")
    A("\\caption{AdaLoRA against the $\\Gamma$-guided rule at matched budget (%s trainable "
      "parameters), matched learning rate, matched seed and matched reference data; the AdaLoRA "
      "arm runs the same rank plan as the plain uniform control (rank 4 on all %d modules). "
      "Source: \\texttt{tools/\\_p1635\\_p3\\_rc\\_family.py} $\\to$ "
      "\\texttt{outputs/analysis/p3\\_rc\\_family\\_boundary.json} "
      "(\\texttt{adalora\\_boundary.matched\\_cells}; confound in "
      "\\texttt{adalora\\_boundary.confounds}).}"
      % ("{:,}".format(ad["comparison_plane"]["budget_params"]).replace(",", "{,}"),
         ad["comparison_plane"]["adalora_config"]["n_modules"]))
    A("\\label{tab:rc-boundary}")
    A("\\end{table}")
    A("```")
    A("")
    A("The reversal, stated outside the table so that it is not averaged away: plain uniform rank "
      "at the same budget beats the $\\Gamma$-guided rule in %d archived cells — %s "
      "(`adalora_boundary.reversal_regime.cells`). The largest of those differences is %.1f "
      "energy units in favour of uniform "
      "(`adalora_boundary.reversal_regime.cells[*].difference_gamma_minus_uniform`)."
      % (ad["reversal_regime"]["n_cells_where_plain_uniform_beats_the_gamma_rule"],
         " ; ".join("$\\eta=%s$, seed %d: uniform $%+.0f$ against $\\Gamma$ $%+.0f$"
                    % (_eta(c["lr"]), c["seed"], c["uniform_delta_E"], c["gamma_delta_E"])
                    for c in ad["reversal_regime"]["cells"]),
         max(c["difference_gamma_minus_uniform"]
             for c in ad["reversal_regime"]["cells"])))
    A("")
    A("## 3. Insertion points (file, label, line range)")
    A("")
    A("Line numbers are located in the live sources by `%s` and re-located on every run."
      % doc["meta"]["script"])
    A("")
    for a in doc["insertion_points"]:
        A("- `%s` — **%s**, lines **%d–%d** (`%s`). %s"
          % (a["file"], a["label"], a["line_range"][0], a["line_range"][1], a["key"],
             a["role"]))
    A("")
    A("Proposed new anchors if the boundary is promoted out of the comment: a supplementary "
      "section `\\label{app:rc-boundary}` inserted immediately before `\\section{Curvature at high "
      "rank}` in `paper3/paper_ieee/supplementary/supplementary.tex`, and one new row in "
      "`tab:claims` (`app:claims`) reading *crossing transfers across backbones* — status "
      "*not supported*.")
    A("")
    A("## 4. Caveats that must survive editing")
    A("")
    A("1. **Family coverage.** %d backbones were searched and all %d have a rank curve. %d contain a "
      "crossing in at least one stratum, %d contain none anywhere in the measured range (`%s`) so "
      "for them $r_c$ is neither localised nor bounded, and only %d yields a single well-defined "
      "crossing (`conclusion.families_with_a_crossing_in_at_least_one_stratum`, "
      "`.families_with_no_crossing_anywhere`, `.families_with_one_well_defined_rc`). One family's "
      "label is not stored inside its archive: `qwen2-vl-7b` is inherited from the manuscript phase "
      "table (`rc_by_family.qwen2-vl-7b.strata.qwen_cloud_sweep.model_label_source`, "
      "`.model_label_confidence`)."
      % (len(fam), len(fam),
         len(c["families_with_a_crossing_in_at_least_one_stratum"]),
         len(c["families_with_no_crossing_anywhere"]),
         "` and `".join(c["families_with_no_crossing_anywhere"]),
         len(c["families_with_one_well_defined_rc"])))
    A("2. **Seed counts.** The primary LLaVA stratum has %d paired seeds; the re-run stratum %d; "
      "the E2 batches %d; the sample-window stratum %d unit (the training window) at a single "
      "seed; SmolVLM %d. The five-seed environment stratum is archived as aggregates only and "
      "carries no resampling interval "
      "(`rc_by_family.llava-1.5-7b.strata.llava_seed5_aggregate.bootstrap.reason`)."
      % (prim["n_units"], rerun["n_units"],
         _cell(fam, "llava_e2_sweep")["n_units"],
         _cell(fam, "llava_samplesize_windows")["n_units"],
         _cell(fam, "smolvlm_r5_r6", "smolvlm-500m")["n_units"]))
    A("3. **Environment.** The software stack accounts for %.2f of the $r=5$ variance (95\\%% CI "
      "$%s$), and the three archived stack means at $r=5$ are `%s` — one of them positive "
      "(`stability.environment_share_of_r5_variance`). Any cross-family sentence about $r_c$ must "
      "carry this."
      % (st["environment_share_of_r5_variance"]["env_share"],
         json.dumps(st["environment_share_of_r5_variance"]["share_ci95"]),
         json.dumps(st["environment_share_of_r5_variance"]["stack_means_at_r5"], sort_keys=True)))
    A("4. **Two manuscript statements disagree with the archives and should be reconciled, not "
      "copied.** (a) The `tab:sharegpt` caption states the sign flip occurs between $r=5$ and "
      "$r=6$, while its own archived means are $r=4:%s$, $r=5:%s$, $r=6:%s$ — a zero crossing "
      "between $r=4$ and $r=5$, fitted at $%s$ "
      "(`rc_by_family.llava-1.5-7b.strata.llava_sharegpt.mean_dE_by_rank`, `.crossing_point`). "
      "(b) The `fig:ers` caption calls the one-epoch flip *earlier* than the three-epoch bracket, "
      "while the archived one-epoch crossing sits at $%s$, far above it "
      "(`...strata.llava_ers_1epoch.crossing_point`)."
      % (_cell(fam, "llava_sharegpt")["mean_dE_by_rank"]["4"],
         _cell(fam, "llava_sharegpt")["mean_dE_by_rank"]["5"],
         _cell(fam, "llava_sharegpt")["mean_dE_by_rank"]["6"],
         _cell(fam, "llava_sharegpt")["crossing_point"],
         _cell(fam, "llava_ers_1epoch")["crossing_point"]))
    A("5. **AdaLoRA: what is and is not matched.** Matched: budget, learning rate, seed, reference "
      "data ($%s$). Not matched: the block configuration relative to the $\\Gamma$ plan, and the "
      "cross-entropy axis — the two scripts do not start from the same first-epoch loss, so no "
      "matched-loss statement is available (`adalora_boundary.confounds`). The AdaLoRA arm also "
      "sits %.4f\\%% above the budget under measurement, so budget matching holds in the cost model "
      "only (`adalora_boundary.summary` and `.comparison_plane.adalora_config`)."
      % (ident, 100.0 * (ad["comparison_plane"]["adalora_config"]["n_trainable_measured"]
                         - ad["comparison_plane"]["adalora_config"]["target_budget_params"])
         / ad["comparison_plane"]["adalora_config"]["target_budget_params"]))
    A("6. **Under-powered, and reported as such.** $n=%d$ matched cells give an exact two-sided "
      "sign-test floor of $p=%.3f$; the direction is unanimous but cannot reach significance at "
      "this cell count (`adalora_boundary.summary.exact_sign_test_two_sided_p`, "
      "`.exact_sign_test_reaches_p05`)."
      % (ad["summary"]["n_matched_cells"], ad["summary"]["exact_sign_test_two_sided_p"]))
    A("7. **Not sourced, therefore not asserted.** (i) Whether peft applied the orthogonality "
      "regulariser configured as `orth_reg_weight=0.5` in `tools/_p451_baseline_adalora.py`: no "
      "archive records it. (ii) The seed labels of the ShareGPT and one-epoch strata, which the "
      "archives store as positional lists. (iii) A $\\Gamma$ arm trained at the same base-rank-1 "
      "configuration is available, but the three published-rule arms are not parameter-matched to "
      "the uniform $r=5$/$r=6$ arms, which the manuscript already calls a directional comparison.")
    A("8. **Metric comparability.** The CLIP stratum's energy is a normalised-embedding retrieval "
      "gap on a different scale from the VLM alignment energy, so only the *sign* of its "
      "$\\Delta E$ is comparable across families "
      "(`rc_by_family.clip-vit-base-patch32.strata.clip_n16_test.metric_comparable_across_families`). "
      "Its four strata are sign-constant along the rank axis: training energy is $%+.6f$ at 16 "
      "pairs and $%+.6f$ at 1024, held-out energy is $%+.6f$ and $%+.6f$ "
      "(`...strata.clip_n16_train.mean_dE_by_rank`, `.clip_n1024_train`, `.clip_n16_test`, "
      "`.clip_n1024_test`)."
      % (_cell(fam, "clip_n16_train", "clip-vit-base-patch32")["mean_dE_by_rank"]["16"],
         _cell(fam, "clip_n1024_train", "clip-vit-base-patch32")["mean_dE_by_rank"]["16"],
         _cell(fam, "clip_n16_test", "clip-vit-base-patch32")["mean_dE_by_rank"]["16"],
         _cell(fam, "clip_n1024_test", "clip-vit-base-patch32")["mean_dE_by_rank"]["16"]))
    A("9. **One stratum reports more than one crossing, and it is the ShareGPT one.** Its curve "
      "crosses zero three times (up between $r=4$ and $r=5$ at $%.3f$, down between $r=32$ and "
      "$r=48$, up again between $r=48$ and $r=64$ at $%.3f$); the primary entry is the first "
      "forward crossing and the others are kept in "
      "`rc_by_family.llava-1.5-7b.strata.llava_sharegpt.forward_crossings` and "
      "`.reverse_crossings`. A 'critical rank' read off this stratum alone would be ill-defined, "
      "which is part of why the family has no single $r_c$."
      % (_cell(fam, "llava_sharegpt")["forward_crossings"][0]["point"],
         _cell(fam, "llava_sharegpt")["forward_crossings"][1]["point"]))
    A("")
    A("## 5. Independent check on the same runs")
    A("")
    A("The refit reproduces the archived per-rank means of the ten-seed family exactly "
      "(`stability.archived_exact_tests_on_the_same_runs.refit_reproduces_archived_means`), and the "
      "already-archived exact test on those same runs separates %d of %d rank pairs after "
      "Holm--Bonferroni (`...n_separating_holm_p05`). The curvature observable, which is "
      "rank-indexed on the same backbone, does not corroborate a rank threshold: along its primary "
      "seed line the second-order share is negative at every archived rank in $%s$ and rises "
      "monotonically toward zero without crossing it "
      "(`stability.curvature_observable.ranks_measured`, "
      "`.primary_seed_curve_share_by_rank`); its rescaled share at the operating rate reproduces "
      "the manuscript's `tab:hessian` values to four decimals "
      "(`...manuscript_tab_hessian_check.reproduces_manuscript_to_4dp`). The sign is not unanimous "
      "across seeds and probe steps (%s, "
      "`.significant_flips`), which is what the manuscript's own claim table already records."
      % (st["archived_exact_tests_on_the_same_runs"]["n_separating_holm_p05"],
         st["archived_exact_tests_on_the_same_runs"]["n_pairs"],
         json.dumps(st["curvature_observable"]["ranks_measured"]),
         _plural(len(st["curvature_observable"]["significant_flips"]),
                 "archived sign flip", "archived sign flips")))
    A("")
    A("## 6. One-line answers to the two objections")
    A("")
    A("- *The critical rank was taken from another family.* It was not taken from another "
      "backbone — its archive is LLaVA-1.5-7B throughout — but it does belong to one protocol: "
      "inside LLaVA the stratum crossings run from $%.2f$ to $%.2f$, %d of the %d backbones "
      "contain no crossing anywhere in their measured range, and none of the LLaVA strata is a "
      "cross-environment constant."
      % (fam["llava-1.5-7b"]["sensitivity_span"][0], fam["llava-1.5-7b"]["sensitivity_span"][1],
         len(c["families_with_no_crossing_anywhere"]), len(fam)))
    A("- *AdaLoRA is a counterexample.* On the energy axis it is not a counterexample but a "
      "consistent winner in every matched cell (%d of %d), which the manuscript already concedes; "
      "what the boundary table adds is that the win is under-powered ($p\\ge%.3f$ at this cell "
      "count) and confounded with the uniform rank plan, and that the ordering *does* reverse "
      "against plain uniform rank in %d archived cells."
      % (ad["summary"]["n_cells_adalora_lower"], ad["summary"]["n_matched_cells"],
         ad["summary"]["exact_sign_test_two_sided_p"],
         ad["reversal_regime"]["n_cells_where_plain_uniform_beats_the_gamma_rule"]))
    A("")
    return "\n".join(L) + "\n"


def _plural(n, one, many):
    return "%d %s" % (n, one if n == 1 else many)


def _regime_latex(cells):
    """Group the reversal cells by learning rate, in LaTeX, from the archived rows."""
    by_lr = {}
    for c in cells:
        by_lr.setdefault(c["lr"], []).append(c["seed"])
    parts = ["$\\eta=%s$ at seed%s %s" % (_eta(lr), "s" if len(s) > 1 else "",
                                          " and ".join(str(x) for x in sorted(s)))
             for lr, s in sorted(by_lr.items())]
    return "; ".join(parts)


def _eta(lr):
    return {5e-5: "5\\times10^{-5}", 3e-4: "3\\times10^{-4}", 1e-3: "10^{-3}"}.get(
        lr, ("%g" % lr))


if __name__ == "__main__":
    sys.exit(main())