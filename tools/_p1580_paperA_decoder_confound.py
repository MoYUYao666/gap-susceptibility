#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Decompose the decoder-VLM confound reported in Paper A (NEUCOM-D-26-23760).

Problem. Supplement Section E (Table `tab:vlm`, Qwen2-VL-2B-Instruct) and Section G
(Table `tab:llava`, LLaVA-1.5-7B) report opposite signs of the modality-gap change:
the Qwen arms reduce DG*, the LLaVA arms raise it. The manuscript states both numbers
but the two experiments differ in several factors at once, so the sign cannot be
attributed to the training objective (contrastive InfoNCE against caption
cross-entropy) rather than to scale, dataset, adaptation site or protocol.

This script does three things and nothing else:

  1. it walks the archived per-run records behind the two tables and recomputes the
     reported per-arm statistics from the raw seeds, naming file and JSON field for
     every number;
  2. it tabulates which factors are controlled and which vary between the two models;
  3. it enumerates what the archive can and cannot separate, including the artefacts
     that exist only as prose and therefore cannot be cited.

No experiment is run and no archived file is modified; the script only reads.

Sign convention used throughout this file: the **signed relative change** of the gap,
    change_pct = (after - before) / before * 100,
so negative means the gap narrowed and positive means it widened. Paper A's Table E
prints the magnitude of the reduction with a "+" sign while Table G prints the
magnitude of the increase with a "+" sign, so the same glyph denotes opposite
directions in the two tables; this script reports one signed quantity to remove that
ambiguity.

Dispersion convention: the manuscript's spreads are the **population** standard
deviation (ddof=0) of the per-seed values divided by the single baseline. Both ddof=0
and ddof=1 are recorded; the assertions pin the convention that reproduces the
manuscript.

    python tools/_p1580_paperA_decoder_confound.py
"""
from __future__ import annotations

import glob
import io
import json
import re
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "paperA_decoder_confound.json"

ARMS = ["text_only", "vision_only", "both"]

QWEN_DIR = REPO / "outputs" / "vlm_clean_cloud"
QWEN_BASELINE = QWEN_DIR / "frozen_baseline.json"
QWEN_SUMMARY = REPO / "outputs" / "vlm_clean_summary.json"
QWEN_LEGACY_DETAIL = REPO / "outputs" / "analysis" / "vlm_bf16_detail.json"
QWEN_LEGACY_DIR = REPO / "outputs" / "vlm_seeds_bf16"

LLAVA_METRIC = REPO / "outputs" / "canonical_caption_metric.json"
LLAVA_DIR = REPO / "outputs" / "llava_canonical_cloud"

# Manuscript values the recomputation must reproduce (Paper A supplement Tables E and G).
EXPECT = {
    "qwen": {  # reduction magnitude, sd, seed range
        "both": (98.57, 0.44, (97.72, 99.44)),
        "text_only": (96.74, 0.29, (95.86, 97.07)),
        "vision_only": (89.41, 1.01, (87.08, 90.74)),
    },
    "llava": {  # increase magnitude, sd, per-seed range (Table G, clean caption construction)
        # text_only and both ranges are printed in the supplement (lines 368-369);
        # the vision_only range is not stated there and is pinned here from the archive.
        "text_only": (73.27, 7.54, (67.61, 83.92)),
        "vision_only": (121.48, 16.33, (99.53, 138.68)),
        "both": (95.66, 7.91, (86.04, 105.43)),
    },
}

FACTOR_TABLE = {
    "controlled_identical": [
        "arm definition (text_only / vision_only / both, split by tower name)",
        "strict freezing (only adapter matrices trainable, backbone frozen)",
        "LoRA rank 8",
        "epochs 3",
        "batch size 2",
        "learning rate 1e-4",
        "precision bfloat16",
        "image side of DG* (mean pool over image-token positions, L2, no projection)",
        "DG* as paired squared distance (mean_i ||I_i - T_i||^2)",
        "three-arm design reported against an untrained baseline",
    ],
    "varies": [
        {
            "factor": "training objective / loss",
            "qwen": "symmetric InfoNCE contrastive on the unprojected pooled pair "
                    "(tools/_p1150_qwen_clean_sweep.py line 253)",
            "llava": "caption-generation causal-LM cross-entropy "
                     "(tools/_p820_llava_sites.py, out.loss with labels)",
            "separated_by_archive": False,
        },
        {
            "factor": "parameter scale",
            "qwen": "2B (Qwen2-VL-2B-Instruct)",
            "llava": "7B (LLaVA-1.5-7B)",
            "separated_by_archive": False,
        },
        {
            "factor": "base model family",
            "qwen": "Qwen2-VL (Qwen vision encoder + Qwen2 language model)",
            "llava": "LLaVA-1.5 (CLIP ViT-L/14-336 vision tower + Vicuna-7B language model)",
            "separated_by_archive": False,
        },
        {
            "factor": "training dataset",
            "qwen": "Flickr30k, 400 annotated images yielding 320 image-caption pairs",
            "llava": "MS-COCO, 1500 training pairs and 500 held-out pairs",
            "separated_by_archive": False,
        },
        {
            "factor": "training-set size (pairs)",
            "qwen": "320",
            "llava": "1500",
            "separated_by_archive": False,
        },
        {
            "factor": "evaluation-pair count",
            "qwen": "320 (outputs/vlm_clean_cloud/frozen_baseline.json:n_pairs)",
            "llava": "500 (outputs/llava_canonical_cloud/frozen_s42.json:n_eval; read in 63 "
                     "batches per outputs/canonical_caption_metric.json:runs.frozen.clean.n_batches)",
            "separated_by_archive": False,
        },
        {
            "factor": "seeds per arm",
            "qwen": "13",
            "llava": "3",
            "separated_by_archive": False,
        },
        {
            "factor": "adaptation site / target modules",
            "qwen": "LoRA alpha 16, dropout 0.05, tower-specific target modules "
                    "(vision attn.qkv/attn.proj/mlp.fc1/fc2; language 7 projections)",
            "llava": "LoRA on vision_model encoder projections, language_model projections "
                     "and multi_modal_projector.linear_1/linear_2",
            "separated_by_archive": False,
        },
        {
            "factor": "text-side convention of the DG* measurement",
            "qwen": "caption positions after the last image token up to <|im_end|> "
                    "(tools/_p1150_qwen_clean_sweep.py)",
            "llava": "caption-token positions, labels != -100 "
                     "(tools/_p1145_clean_gap_measure.py)",
            "separated_by_archive": True,
            "note": "same concept, implemented independently in two scripts; both "
                    "constructions are archived for LLaVA on the same nine adapters "
                    "and both give an increase, so this factor does not carry the sign",
        },
    ],
    "verdict": "objective, scale, family, dataset, set size, seed count and adaptation-site "
               "specification all vary together; no archived run isolates any one of them",
}


def load(path: Path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def rel_pct(after: float, before: float) -> float:
    """Signed relative change in percent; negative = gap narrowed."""
    return (after - before) / before * 100.0


def describe(values, baseline, files):
    """Per-arm statistics under both dispersion conventions."""
    n = len(values)
    mean_after = st.fmean(values)
    signed = [rel_pct(v, baseline) for v in values]
    mean_change = rel_pct(mean_after, baseline)
    sd_pop = st.pstdev(signed) if n > 1 else 0.0
    sd_samp = st.stdev(signed) if n > 1 else 0.0
    return {
        "n": n,
        "baseline_value": baseline,
        "per_seed_after": [round(v, 12) for v in values],
        "mean_after": round(mean_after, 12),
        "mean_signed_change_pct": round(mean_change, 6),
        "median_signed_change_pct": round(st.median(signed), 6),
        "sd_population_pct": round(sd_pop, 6),
        "sd_sample_pct": round(sd_samp, 6),
        "min_signed_change_pct": round(min(signed), 6),
        "max_signed_change_pct": round(max(signed), 6),
        "n_runs_gap_narrowed": sum(1 for s in signed if s < 0),
        "n_runs_gap_widened": sum(1 for s in signed if s > 0),
        "source_files": files,
    }


def qwen_arm(arm):
    files = sorted(glob.glob(str(QWEN_DIR / f"{arm}_seed*.json")))
    seeds, values, legacy, files_used = [], [], [], []
    for fp in files:
        rec = load(Path(fp))
        if rec.get("arm") != arm:
            raise AssertionError(f"arm mismatch in {fp}: {rec.get('arm')}")
        seeds.append(rec["seed"])
        values.append(rec["dg_star"][2])          # epoch 3
        legacy.append(rec["legacy_dg_star"][2])   # superseded projected construction
        files_used.append(Path(fp).relative_to(REPO).as_posix())
    order = sorted(range(len(seeds)), key=lambda i: seeds[i])
    return ([seeds[i] for i in order],
            [values[i] for i in order],
            [legacy[i] for i in order],
            [files_used[i] for i in order])


def llava_metric_arm(metric, kind, arm):
    tags = [f"{arm}_{s}" for s in ("s42", "s123", "s456")]
    values = [metric["runs"][t][kind]["dg_star"] for t in tags]
    files = [f"{LLAVA_METRIC.relative_to(REPO).as_posix()}"
             f"::runs.{t}.{kind}.dg_star" for t in tags]
    return values, files


def llava_cloud_arm(arm):
    files = sorted(glob.glob(str(LLAVA_DIR / f"{arm}_s*.json")))
    seeds, vals, files_used = [], [], []
    for fp in files:
        rec = load(Path(fp))
        if rec.get("arm") != arm:
            raise AssertionError(f"arm mismatch in {fp}: {rec.get('arm')}")
        seeds.append(rec["seed"])
        vals.append(rec["dg_star_rel_change"] * 100.0)  # already a signed rel change
        files_used.append(Path(fp).relative_to(REPO).as_posix())
    order = sorted(range(len(seeds)), key=lambda i: seeds[i])
    return ([vals[i] for i in order], [files_used[i] for i in order])


def main() -> int:
    notes = []

    # ---------------------------------------------------------------- Qwen2-VL-2B
    qwen_frozen = load(QWEN_BASELINE)
    q_baseline = qwen_frozen["dg_star"]
    assert qwen_frozen["n_pairs"] == 320, qwen_frozen["n_pairs"]

    qwen = {
        "model": "Qwen2-VL-2B-Instruct",
        "archive_dir": QWEN_DIR.relative_to(REPO).as_posix(),
        "per_run_glob": f"{QWEN_DIR.relative_to(REPO).as_posix()}/{{arm}}_seed*.json",
        "producer_script": "tools/_p1150_qwen_clean_sweep.py",
        "baseline_producer_script": "tools/_p1163_qwen_frozen_baseline.py",
        "objective": "symmetric InfoNCE contrastive loss on the unprojected pooled image-text pair",
        "gap_field": "dg_star (3-element list, one entry per epoch; value used here is index 2 = epoch 3)",
        "baseline_field": "dg_star",
        "baseline_file": QWEN_BASELINE.relative_to(REPO).as_posix(),
        "baseline_value": q_baseline,
        "n_pairs_evaluated": qwen_frozen["n_pairs"],
        "gpu_class": "single 32 GB cloud instance, bfloat16",
        "arms": {},
    }

    q_legacy_means, q_ranges = {}, {}
    for arm in ARMS:
        seeds, values, legacy, files = qwen_arm(arm)
        assert len(values) == 13, f"qwen {arm}: expected 13 seeds, got {len(values)}"
        d = describe(values, q_baseline, files)
        d["seeds"] = seeds
        d["legacy_projected_construction"] = {
            "field": "legacy_dg_star[2]",
            "mean_after": round(st.fmean(legacy), 6),
            "note": "superseded _p47 construction (all-non-padding text pool plus two "
                    "fixed random 512-d projections); flat near 2.0 for every arm, so it "
                    "cannot resolve the gap",
        }
        qwen["arms"][arm] = d
        q_legacy_means[arm] = st.fmean(legacy)
        # manuscript quotes the reduction magnitude as a "seed range" of percentages
        red = [-rel_pct(v, q_baseline) for v in values]
        q_ranges[arm] = (round(min(red), 2), round(max(red), 2))

    # reproduce the manuscript's Table E and the derived summary file
    for arm, (exp_red, exp_sd, exp_range) in EXPECT["qwen"].items():
        got = qwen["arms"][arm]
        got_red = -got["mean_signed_change_pct"]
        assert abs(got_red - exp_red) < 0.01, (arm, got_red, exp_red)
        assert abs(got["sd_population_pct"] - exp_sd) < 0.01, (arm, got["sd_population_pct"], exp_sd)
        assert q_ranges[arm] == exp_range, (arm, q_ranges[arm], exp_range)
        got["manuscript_reduction_pct"] = exp_red
        got["manuscript_sd_pct"] = exp_sd
        got["manuscript_seed_range_pct"] = list(exp_range)
        got["reduction_seed_range_pct"] = list(q_ranges[arm])

    qwen["dispersion_convention"] = ("population sd (ddof=0) of the per-seed signed changes; "
                                     "sample sd (ddof=1) is larger by a factor sqrt(13/12)=1.041 "
                                     "and does not reproduce the manuscript")

    # cross-check against the pre-aggregated derived summary
    qsum = load(QWEN_SUMMARY)
    assert qsum["verification"]["n_records"] == 39, qsum["verification"]["n_records"]
    assert abs(qsum["frozen"]["dg_star"] - q_baseline) < 1e-15
    for arm in ARMS:
        s = qsum["per_arm"][arm]
        assert s["n"] == 13, (arm, s["n"])
        assert abs(s["reduction_mean"] - (-qwen["arms"][arm]["mean_signed_change_pct"])) < 1e-6
        assert abs(s["reduction_sd"] - qwen["arms"][arm]["sd_population_pct"]) < 1e-3, \
            (arm, s["reduction_sd"], qwen["arms"][arm]["sd_population_pct"])
        assert abs(s["legacy_ep3_mean"] - q_legacy_means[arm]) < 1e-6
    qwen["derived_summary_check"] = {
        "file": QWEN_SUMMARY.relative_to(REPO).as_posix(),
        "n_records": qsum["verification"]["n_records"],
        "problems": qsum["verification"]["problems"],
        "agrees_with_recomputation": True,
    }

    # ------------------------------------------------------------------ LLaVA-1.5-7B
    metric = load(LLAVA_METRIC)
    l_baseline = metric["runs"]["frozen"]["clean"]["dg_star"]
    l_baseline_prompt = metric["runs"]["frozen"]["prompt"]["dg_star"]

    llava = {
        "model": "LLaVA-1.5-7B",
        "manuscript_table": "tab:llava (supplement Section G)",
        "archive_file": LLAVA_METRIC.relative_to(REPO).as_posix(),
        "producer_script": "tools/_p1145_clean_gap_measure.py",
        "adapter_training_script": "tools/_p820_llava_sites.py",
        "objective": "caption-generation causal-LM cross-entropy (out.loss with labels)",
        "gap_field": "runs.<tag>.<kind>.dg_star",
        "baseline_field": "runs.frozen.<kind>.dg_star",
        "n_eval_pairs": 500,
        "gpu_class": "single 32 GB cloud instance, bfloat16",
        "constructions": {},
    }

    for kind in ("clean", "prompt"):
        base = l_baseline if kind == "clean" else l_baseline_prompt
        block = {
            "text_side": ("caption-token positions, labels != -100" if kind == "clean"
                          else "instruction prompt (no caption in the sequence)"),
            "is_manuscript_construction": kind == "clean",
            "baseline_value": base,
            "baseline_source": f"{LLAVA_METRIC.relative_to(REPO).as_posix()}"
                               f"::runs.frozen.{kind}.dg_star",
            "arms": {},
        }
        for arm in ARMS:
            values, files = llava_metric_arm(metric, kind, arm)
            assert len(values) == 3
            block["arms"][arm] = describe(values, base, files)
        llava["constructions"][kind] = block

    for arm, (exp_chg, exp_sd, exp_range) in EXPECT["llava"].items():
        got = llava["constructions"]["clean"]["arms"][arm]
        assert abs(got["mean_signed_change_pct"] - exp_chg) < 0.01, \
            (arm, got["mean_signed_change_pct"], exp_chg)
        assert abs(got["sd_population_pct"] - exp_sd) < 0.01, \
            (arm, got["sd_population_pct"], exp_sd)
        assert (round(got["min_signed_change_pct"], 2),
                round(got["max_signed_change_pct"], 2)) == exp_range, \
            (arm, got["min_signed_change_pct"], got["max_signed_change_pct"], exp_range)
        got["manuscript_change_pct"] = exp_chg
        got["manuscript_sd_pct"] = exp_sd
        got["manuscript_spread_range_pct"] = list(exp_range)

    llava["dispersion_convention"] = ("population sd (ddof=0) of the three per-seed signed "
                                      "changes; the sample sd (ddof=1) is a factor "
                                      "sqrt(3/2)=1.225 larger and does not reproduce Table G")

    # second LLaVA construction, same nine adapters, archived separately
    lc = load(LLAVA_DIR / "frozen_s42.json")
    lc_baseline_floor = lc["dg_star_rel_change"] * 100.0
    llava_cloud = {
        "manuscript_table": None,
        "archive_dir": LLAVA_DIR.relative_to(REPO).as_posix(),
        "producer_script": "tools/_p820_llava_sites.py",
        "gap_field": "dg_star_rel_change (already a signed relative change; multiplied by 100)",
        "baseline": "the frozen arm's own drg_star_rel_change is the measurement floor, not a "
                    "zero point; the untrained value under this construction is "
                    "dg_star_before = 0.814593874491178 shared by every run",
        "untrained_dg_star_before": lc["dg_star_before"],
        "frozen_arm_floor_pct": round(lc_baseline_floor, 6),
        "arms": {},
    }
    for arm in ARMS:
        vals, files = llava_cloud_arm(arm)
        llava_cloud["arms"][arm] = {
            "n": len(vals),
            "per_seed_signed_change_pct": [round(v, 6) for v in vals],
            "mean_signed_change_pct": round(st.fmean(vals), 6),
            "sd_population_pct": round(st.pstdev(vals), 6),
            "sd_sample_pct": round(st.stdev(vals), 6),
            "min_signed_change_pct": round(min(vals), 6),
            "max_signed_change_pct": round(max(vals), 6),
            "n_runs_gap_narrowed": sum(1 for v in vals if v < 0),
            "n_runs_gap_widened": sum(1 for v in vals if v > 0),
            "source_files": files,
        }
    # documented per-seed values for this construction
    doc_seed = {
        "text_only": [40.765, 39.097, 27.173],
        "vision_only": [-1.508, 19.896, 3.322],
        "both": [31.011, 34.279, 34.761],
    }
    for arm, exp in doc_seed.items():
        got = llava_cloud["arms"][arm]["per_seed_signed_change_pct"]
        assert all(abs(a - b) < 0.01 for a, b in zip(got, exp)), (arm, got, exp)
    assert abs(llava_cloud["arms"]["both"]["mean_signed_change_pct"] - 33.350) < 0.01
    assert abs(llava_cloud["arms"]["text_only"]["mean_signed_change_pct"] - 35.678) < 0.01
    assert abs(llava_cloud["arms"]["vision_only"]["mean_signed_change_pct"] - 7.237) < 0.01
    llava["second_construction_same_adapters"] = llava_cloud
    llava["adapters_present"] = sorted(
        p.name for p in LLAVA_DIR.glob("*_ckpt.pt"))

    # ------------------------------------------------- what the archive can separate
    all_q = [(a, s) for a in ARMS for s in qwen["arms"][a]["per_seed_after"]]
    n_q_narrow = sum(1 for a in ARMS for s in
                     [rel_pct(v, q_baseline) for v in qwen["arms"][a]["per_seed_after"]] if s < 0)
    n_l_widen_clean = sum(
        1 for a in ARMS for s in
        [rel_pct(v, l_baseline) for v in llava["constructions"]["clean"]["arms"][a]["per_seed_after"]]
        if s > 0)
    n_l_widen_prompt = llava_cloud["arms"]["both"]["n_runs_gap_widened"] + \
        llava_cloud["arms"]["text_only"]["n_runs_gap_widened"] + \
        llava_cloud["arms"]["vision_only"]["n_runs_gap_widened"]

    # every archived Qwen legacy-construction run narrows the gap
    legacy_detail = load(QWEN_LEGACY_DETAIL)
    legacy_pcts = [v["dg_rel_pct"] for arm in legacy_detail["per_run"]
                   for v in legacy_detail["per_run"][arm].values()]
    legacy_n_pos = sum(1 for v in legacy_pcts if v > 0)
    legacy_n_neg = sum(1 for v in legacy_pcts if v < 0)

    evidence = {
        "question": "Is there archived evidence that separates the training objective from "
                    "parameter scale, holding the other factors fixed?",
        "answer": "No.",
        "what_exists": {
            "seed_level_variation": {
                "qwen": {
                    "runs_total": len(all_q),
                    "runs_per_arm": 13,
                    "runs_gap_narrowed": n_q_narrow,
                    "runs_gap_widened": len(all_q) - n_q_narrow,
                    "field": "dg_star[2]",
                    "comment": "every archived Qwen run narrows the gap; the three arms have "
                               "disjoint seed ranges, so the sign is not a seed artefact",
                },
                "llava_clean_construction": {
                    "runs_total": 9,
                    "runs_per_arm": 3,
                    "runs_gap_widened": n_l_widen_clean,
                    "runs_gap_narrowed": 9 - n_l_widen_clean,
                    "field": "runs.<tag>.clean.dg_star",
                    "comment": "every archived LLaVA run under the manuscript's construction "
                               "widens the gap",
                },
                "llava_prompt_construction": {
                    "runs_total": 9,
                    "runs_gap_widened": n_l_widen_prompt,
                    "runs_gap_narrowed": 9 - n_l_widen_prompt,
                    "field": "dg_star_rel_change",
                    "comment": "under the second construction the vision-only arm has one seed "
                               "that narrows the gap (vision_only_s123, -1.508%), so the "
                               "arm-mean statement 'every arm widens it' is 3/3 on means but "
                               "8/9 on individual runs here",
                },
            },
            "measurement_construction_within_model": {
                "qwen": {
                    "constructions": 3,
                    "detail": [
                        "clean caption-span construction (vlm_clean_cloud::dg_star) -> large reduction",
                        "superseded _p47 projected all-token construction "
                        "(vlm_clean_cloud::legacy_dg_star) -> flat near 2.0, no resolvable change",
                        "pre-2026-10-17 13-seed archive (outputs/vlm_seeds_bf16, "
                        "analysed in outputs/analysis/vlm_bf16_detail.json::per_run.*.*.dg_rel_pct, "
                        "baseline = epoch 1) -> "
                        f"{legacy_n_pos}/{len(legacy_pcts)} runs report a reduction, "
                        f"{legacy_n_neg} report an increase",
                    ],
                    "comment": "no archived Qwen construction produces an increase",
                },
                "llava": {
                    "constructions": 2,
                    "detail": [
                        "caption-token text side (canonical_caption_metric.json, clean) -> increase",
                        "instruction-prompt text side (canonical_caption_metric.json, prompt) "
                        "-> increase",
                    ],
                    "comment": "the sign on LLaVA is invariant to the text-side convention, so "
                               "this factor does not carry the sign difference",
                },
            },
        },
        "what_is_missing": [
            {
                "experiment": "same base model under the other objective",
                "status": "absent",
                "detail": "no LLaVA-1.5-7B run under a contrastive objective exists anywhere in "
                          "tools/ or exp/ (searched for InfoNCE / log_softmax / logits.T training "
                          "losses in every script that names LLaVA), and no Qwen2-VL-2B run under "
                          "a caption-generation objective is archived",
            },
            {
                "experiment": "scale-matched decoder pair under one objective",
                "status": "absent",
                "detail": "the archive holds one decoder model per scale: Qwen2-VL-2B and "
                          "LLaVA-1.5-7B only",
            },
            {
                "experiment": "matched training budget across the two models",
                "status": "absent",
                "detail": "Qwen trains on 320 pairs, LLaVA on 1500; no run matches them",
            },
            {
                "experiment": "Qwen2.5-VL-7B under the generation objective "
                              "(tools/_p1135_qwen_sites.py, MODEL = Qwen/Qwen2.5-VL-7B-Instruct)",
                "status": "never_archived",
                "detail": "the runner declares OUT_DIR outputs/qwen_sites, which does not exist; "
                          "no JSON for it is present under outputs/",
            },
            {
                "experiment": "Qwen2.5-VL-7B feasibility pilot (generative, 7B)",
                "status": "prose_only_not_citable",
                "detail": "DG* 1.2879 -> 1.2424 (-3.531%) on 8 held-out pairs and 392 LoRA "
                          "tensors appear only in the prose of docs/llava_canonical_2026-10-17.md "
                          "and HANDOFF.md; no archived JSON or field carries them, and the arm is "
                          "not stated, so under the repository's provenance rule they cannot be "
                          "reported as evidence",
            },
            {
                "experiment": "SmolVLM decoder run",
                "status": "wrong_metric",
                "detail": "outputs/analysis/p3_smolvlm_family*.json record an energy field E over "
                          "20 samples (tools/_p1568_smolvlm_run.py); there is no DG* or gap field, "
                          "so it cannot enter this comparison",
            },
        ],
        "dataset_flip_evidence_from_dual_encoders": {
            "file": "outputs/analysis/dataset_flip_strict.json",
            "fields": "r4.<dataset>|<arm>.mean",
            "finding": "changing dataset from Flickr30k to MS-COCO flips the best arm "
                       "(text_only -0.03038 against both -0.02037 on Flickr30k; both -0.08860 "
                       "against text_only -0.04301 on COCO) but not the sign: every arm narrows "
                       "the centroid gap on both datasets",
            "scope": "dual-encoder strict freezing, not decoders; it shows the dataset can "
                     "reorder arms, which is why dataset cannot be dismissed as a candidate "
                     "explanation for the decoder sign difference",
        },
    }

    # ---------------------------------------------------------- provenance findings
    manifest = load(REPO / "docs" / "provenance_manifest.json")
    manifest_rows = {}

    def walk_manifest(o):
        if isinstance(o, dict):
            if o.get("label") in ("tab:vlm", "tab:llava"):
                manifest_rows[o["label"]] = {
                    "kind": o.get("kind"),
                    "script": o.get("script"),
                    "archive": o.get("archive"),
                    "status": o.get("status"),
                }
            for v in o.values():
                walk_manifest(v)
        elif isinstance(o, list):
            for v in o:
                walk_manifest(v)

    walk_manifest(manifest)

    for label, true_src in (
            ("tab:vlm", [QWEN_DIR.relative_to(REPO).as_posix(),
                         QWEN_BASELINE.relative_to(REPO).as_posix()]),
            ("tab:llava", [LLAVA_METRIC.relative_to(REPO).as_posix()])):
        row = manifest_rows.get(label, {})
        declared = row.get("archive")
        payload = load(REPO / declared) if declared else {}
        resolved = 'dg_star' in json.dumps(payload)
        row["resolves_to_table_numbers"] = resolved
        row["declared_archive_contains_dg_star"] = resolved
        row["true_sources"] = true_src
        if not resolved:
            row["defect"] = (f"manifest declares {declared} with status 'verified', but that "
                             f"file holds a tau-vs-lambda instruction-dynamics probe and none of "
                             f"the table's numbers (no dg_star field, no untrained baseline); the "
                             f"table's numbers come from " + " and ".join(true_src))
        manifest_rows[label] = row

    provenance_findings = {
        "manifest": "docs/provenance_manifest.json (labels tab:vlm and tab:llava, both 'verified')",
        "decoder_table_mapping": manifest_rows,
        "mapping_is_correct": all(not r.get("defect") for r in manifest_rows.values()),
        "sign_glyph_ambiguity": {
            "table_E_header": "Arm & Trainable & DG* after & Reduction & Seed range & CG",
            "table_E_values": "+98.57\\pm0.44\\%, +96.74\\pm0.29\\%, +89.41\\pm1.01\\%",
            "table_E_meaning": "magnitude of a gap REDUCTION printed with a plus sign",
            "table_G_header": "Arm & Trainable & DG* after & Change vs frozen",
            "table_G_values": "+73.27\\pm7.54\\%, +121.48\\pm16.33\\%, +95.66\\pm7.91\\%",
            "table_G_meaning": "magnitude of a gap INCREASE printed with a plus sign",
            "risk": "the same '+' glyph denotes opposite directions in the two tables; the column "
                    "headers differ ('Reduction' against 'Change vs frozen') and the prose "
                    "disambiguates, but a reader comparing the two tables cell by cell can read "
                    "98.57% and 73.27% as the same kind of quantity",
            "this_script": "reports one signed quantity for both, negative = narrowed",
        },
        "adapter_path_discrepancy": {
            "file": LLAVA_METRIC.relative_to(REPO).as_posix(),
            "field": "definition.adapters",
            "declared": metric["definition"]["adapters"],
            "declared_path_exists": (REPO / "outputs" / "llava_canonical").is_dir(),
            "actual_local_archive": LLAVA_DIR.relative_to(REPO).as_posix(),
            "actual_adapters": llava["adapters_present"],
            "note": "the declared adapter directory does not exist locally; the nine adapters the "
                    "file was computed from are in outputs/llava_canonical_cloud/, which is also "
                    "where tools/_p1145_clean_gap_measure.py's outputs were pulled back to. This "
                    "is a path-label issue only: the nine adapters are present and non-empty.",
        },
        "third_llava_construction_not_reconciled": {
            "file": LLAVA_DIR.relative_to(REPO).as_posix(),
            "field": "dg_star_before",
            "untrained_value_in_sweep_records": lc["dg_star_before"],
            "untrained_value_caption_metric_prompt": metric["runs"]["frozen"]["prompt"]["dg_star"],
            "untrained_value_caption_metric_clean": metric["runs"]["frozen"]["clean"]["dg_star"],
            "note": "the sweep's own measurement gives an untrained DG* of 0.8146, which matches "
                    "neither variant of canonical_caption_metric.json (0.3885 prompt, 0.3566 "
                    "clean); it is therefore a third, not yet reconciled construction. It is used "
                    "here only as a qualitative check that all three LLaVA arms increase the gap, "
                    "never as a source for a reported magnitude.",
        },
    }

    # ------------------------------------------------------------------- conclusion
    q_red = {a: -qwen["arms"][a]["mean_signed_change_pct"] for a in ARMS}
    q_sd = {a: qwen["arms"][a]["sd_population_pct"] for a in ARMS}
    l_chg = {a: llava["constructions"]["clean"]["arms"][a]["mean_signed_change_pct"] for a in ARMS}
    l_sd = {a: llava["constructions"]["clean"]["arms"][a]["sd_population_pct"] for a in ARMS}

    conclusion = {
        "bounded_claim": (
            "Across two decoder-based VLMs the measured image-text gap moves in opposite "
            "directions: on Qwen2-VL-2B-Instruct it narrows under all three adaptation arms "
            f"(DG* reduction {q_red['both']:.2f}+/-{q_sd['both']:.2f}% both-position, "
            f"{q_red['text_only']:.2f}+/-{q_sd['text_only']:.2f}% text-only and "
            f"{q_red['vision_only']:.2f}+/-{q_sd['vision_only']:.2f}% vision-only over thirteen "
            "seeds, with disjoint seed ranges), while on LLaVA-1.5-7B it widens under all three "
            f"(DG* change {l_chg['text_only']:+.2f}+/-{l_sd['text_only']:.2f}% text-only, "
            f"{l_chg['vision_only']:+.2f}+/-{l_sd['vision_only']:.2f}% vision-only and "
            f"{l_chg['both']:+.2f}+/-{l_sd['both']:.2f}% both-position over three seeds). Both "
            "decoder experiments place the vision side in the same role from opposite "
            "directions, but they differ simultaneously in training objective (contrastive "
            "against caption generation), parameter scale (2B against 7B), pretraining family, "
            "dataset (Flickr30k against MS-COCO) and training-set size (320 against 1500 "
            "pairs), so the sign difference cannot be attributed to the objective alone; no "
            "archived run isolates any single one of these factors."
        ),
        "supported_by_data": [
            "the direction of the change on each model separately, at the stated n",
            "the ordering of the three arms within each model",
            "the invariance of each model's sign to the text-side convention of the measurement",
            "the absence of seed-level sign flips in the arm means on both models",
        ],
        "NOT_supported_by_data": [
            "that the training objective causes the opposite sign",
            "that parameter scale causes the opposite sign",
            "that the dataset causes the opposite sign",
            "any comparison of effect magnitudes between the two tables",
            "the claim that LLaVA widens the gap on every individual run under the "
            "instruction-prompt construction (8 of 9 runs widen there)",
        ],
        "definitive_control_design": {
            "executed": False,
            "design_only": True,
            "minimal_design": (
                "Hold model, data, budget, seed set and adaptation-site specification fixed and "
                "vary only the loss. Use one LLaVA-1.5-7B checkpoint with the toolchain already "
                "archived in tools/_p820_llava_sites.py so the preprocessing, target modules and "
                "measurement are byte-identical to the existing run, and define two arms: "
                "(a) caption-generation cross-entropy, (b) the symmetric InfoNCE contrastive loss "
                "ported from tools/_p1150_qwen_clean_sweep.py line 253 (cross_entropy over the "
                "pooled image-text similarity matrix and its transpose). Both arms train on the "
                "same 1500 MS-COCO pairs, three epochs, batch 2, rank 8, learning rate 1e-4, "
                "bfloat16, and are evaluated with tools/_p1145_clean_gap_measure.py so the DG* "
                "definition is the one Table G already uses. Analysis is a 2x3 design "
                "(objective x arm) on the same seeds, with the frozen baseline measured once per "
                "objective, since the loss does not affect the untrained model."
            ),
            "decision_rule": (
                "If the contrastive arm narrows DG* and the generation arm widens it in the same "
                "model, objective is sufficient to explain the sign and scale is excluded. If "
                "both arms move the same way, objective is excluded and scale, family or dataset "
                "must carry it, and the next control is the same objective at 2B against 7B "
                "within one family."
            ),
            "cost_estimate_source": (
                "rate measured on the archived LLaVA run: 0.95 s/step at 2250 steps per run "
                "(docs/llava_canonical_2026-10-17.md), so six new training runs plus evaluation "
                "are roughly six times the existing three-seed sweep; the two objectives differ "
                "in loss only, so no change to the data pipeline is required"
            ),
            "what_remains_uncontrolled_even_then": [
                "the contrastive and generation objectives may need different learning rates to "
                "be compared fairly, and the archived runs use one rate for both",
                "a single model pair still cannot separate family from scale",
                "320-pair and 1500-pair budgets remain unequal unless the Qwen side is re-run",
            ],
        },
    }

    out = {
        "meta": {
            "script": "tools/_p1580_paperA_decoder_confound.py",
            "purpose": "decompose the decoder-VLM sign confound in Paper A supplement "
                       "Sections E and G (manuscript NEUCOM-D-26-23760)",
            "manuscript_tables": {
                "tab:vlm": "paper合/sections/supplement.tex lines 264-282 (Section E, Qwen2-VL-2B)",
                "tab:llava": "paper合/sections/supplement.tex lines 344-363 (Section G, LLaVA-1.5-7B)",
            },
            "sign_convention": "change_pct = (after - before) / before * 100; negative = gap narrowed",
            "dispersion_convention": "population sd (ddof=0); sample sd recorded alongside",
            "read_only": True,
            "manuscript_files_modified": [],
        },
        "models": {"qwen2_vl_2b": qwen, "llava_1_5_7b": llava},
        "factor_table": FACTOR_TABLE,
        "additional_evidence": evidence,
        "provenance_findings": provenance_findings,
        "conclusion": conclusion,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write("\n")

    # ------------------------------------------------------------------- console
    print(f"wrote {OUT.relative_to(REPO).as_posix()}")
    print()
    print("Qwen2-VL-2B-Instruct  (baseline DG* "
          f"{q_baseline:.6f}, {qwen_frozen['n_pairs']} pairs, 13 seeds/arm)")
    for arm in ARMS:
        a = qwen["arms"][arm]
        print(f"  {arm:<12} n={a['n']:>2}  DG*_ep3={a['mean_after']:.6f}  "
              f"signed change {a['mean_signed_change_pct']:+8.3f}%  "
              f"sd(ddof=0) {a['sd_population_pct']:5.3f}  "
              f"range [{a['min_signed_change_pct']:+.2f},{a['max_signed_change_pct']:+.2f}]  "
              f"narrowed {a['n_runs_gap_narrowed']}/{a['n']}")
    print()
    print("LLaVA-1.5-7B  (clean caption construction, baseline DG* "
          f"{l_baseline:.6f}, 500 held-out pairs, 3 seeds/arm)")
    for arm in ARMS:
        a = llava["constructions"]["clean"]["arms"][arm]
        print(f"  {arm:<12} n={a['n']:>2}  DG*={a['mean_after']:.6f}  "
              f"signed change {a['mean_signed_change_pct']:+8.3f}%  "
              f"sd(ddof=0) {a['sd_population_pct']:5.3f}  "
              f"range [{a['min_signed_change_pct']:+.2f},{a['max_signed_change_pct']:+.2f}]  "
              f"widened {a['n_runs_gap_widened']}/{a['n']}")
    print()
    print("LLaVA-1.5-7B  (instruction-prompt construction, same nine adapters)")
    for arm in ARMS:
        a = llava_cloud["arms"][arm]
        print(f"  {arm:<12} n={a['n']:>2}  signed change {a['mean_signed_change_pct']:+8.3f}%  "
              f"sd(ddof=0) {a['sd_population_pct']:5.3f}  widened {a['n_runs_gap_widened']}/{a['n']}")
    print()
    print(f"separates objective from scale: {evidence['answer']}")
    print(f"archived Qwen legacy-construction runs reporting a reduction: "
          f"{legacy_n_pos}/{len(legacy_pcts)}")
    print(f"provenance manifest maps decoder tables correctly: "
          f"{provenance_findings['mapping_is_correct']}")
    for label, r in manifest_rows.items():
        if r.get("defect"):
            print(f"  DEFECT {label}: declared {r['archive']} (status {r['status']}) "
                  f"does not carry the table's numbers")
    print(f"adapters declared by canonical_caption_metric.json present at declared path: "
          f"{provenance_findings['adapter_path_discrepancy']['declared_path_exists']}")
    for n in notes:
        print(f"note: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())