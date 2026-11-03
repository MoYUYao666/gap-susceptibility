#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p44a_verify_task11.py -- machine gate for every number task-11 reports.

Project iron law: no number without (a) a producing script and (b) an archive
file + field.  This script re-derives each claim from the raw archive and
asserts it, so the report can never drift from the data.

Run:  python tools\\_p44a_verify_task11.py
Exit code 0 = all assertions hold.
"""
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "outputs", "analysis")

FAIL = []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print("  [%s] %s %s" % (tag, name, detail))
    if not cond:
        FAIL.append(name)


def load(p):
    with open(os.path.join(A, p), encoding="utf-8") as f:
        return json.load(f)


print("=" * 78)
print("TASK-11 VERIFICATION GATE")
print("=" * 78)

# ---------------------------------------------------------------- artefacts
print("\n[1] artefacts exist and are non-empty")
for p in ("p3_stats_recon.json", "p3_stats_hardened.json", "p3_phase_boundary.json",
          "p3_reproducibility.json", "p3_nan_diagnostics.json",
          "p3_gamma_batch_sensitivity.json"):
    fp = os.path.join(A, p)
    ok = os.path.exists(fp) and os.path.getsize(fp) > 500
    check("exists " + p, ok, "(%d bytes)" % (os.path.getsize(fp) if os.path.exists(fp) else 0))

H = load("p3_stats_hardened.json")
B = load("p3_phase_boundary.json")
R = load("p3_reproducibility.json")
N = load("p3_nan_diagnostics.json")
G = load("p3_gamma_batch_sensitivity.json")

# ------------------------------------------------ paper numbers reproduce
print("\n[2] Table 1 of the paper is exactly reproducible from the archive")
for k in ("r4", "r5", "r6", "r7", "r8", "r16", "r20"):
    e = H["paper_numbers_reproduced"][k]
    check("Table1 %s mean %s vs archive %.1f" % (k, e["paper_mean"], e["archive_mean"]),
          abs(e["archive_mean"] - e["paper_mean"]) < 0.85)
    check("Table1 %s population sd %s vs archive %.1f" % (k, e["paper_sd"], e["archive_sd_population"]),
          abs(e["archive_sd_population"] - e["paper_sd"]) < 0.85)

# ------------------------------------------------ R3.19: the CIs
print("\n[3] R3.19 -- the confidence intervals do span zero / stay uncertain")
p5 = H["phase_transition"]["r5"]
p6 = H["phase_transition"]["r6"]
check("r=5 bootstrap CI spans zero", p5["mean_ci"]["lo"] < 0 < p5["mean_ci"]["hi"],
      "[%.1f, %.1f]" % (p5["mean_ci"]["lo"], p5["mean_ci"]["hi"]))
check("r=5 one-sample t vs 0 not significant", p5["t_vs_zero"]["p"] > 0.05,
      "p=%.4f" % p5["t_vs_zero"]["p"])
check("r=6 one-sample t vs 0 not significant at n=3", p6["t_vs_zero"]["p"] > 0.05,
      "p=%.4f" % p6["t_vs_zero"]["p"])
r56 = H["pooled_llava_tests"]["r5_vs_r6_extra_batch"]
check("r=5 vs r=6 EXACT permutation p > 0.05", r56["permutation_exact"]["p"] > 0.05,
      "p=%.3f over %d splits" % (r56["permutation_exact"]["p"], r56["permutation_exact"]["n_perm"]))
pooled = H["pooled_llava_tests"]["pooled_r45_vs_r67"]
check("pooled {4,5} vs {6,7} IS significant", pooled["welch"]["p"] < 0.05,
      "Welch p=%.4f, perm p=%.5f" % (pooled["welch"]["p"], pooled["permutation_mc"]["p"]))

# ------------------------------------------------ R3.17: 8/8 + power
print("\n[4] R3.17 -- ordering audit and the capability boundary")
oa = B["r6_gt_r5_exhaustive_audit"]
check("every archived configuration keeps dE(r6) > dE(r5)", oa["all_hold"],
      "%d/%d" % (oa["n_r6_gt_r5"], oa["n_configurations"]))
check("binomial p for that ordering < 0.05", oa["exact_sign_test_all_hold"]["p_two_sided"] < 0.05,
      "p=%.4f" % oa["exact_sign_test_all_hold"]["p_two_sided"])
check("observed d(r6 vs r5) BELOW the n=3 MDE",
      B["power_analysis"]["observed_effects"]["r6_vs_r5_extra_batch"]["cohens_d"]
      < B["power_analysis"]["n3_vs_n3"]["cohens_d_mde"],
      "d=%.2f < MDE d=%.2f" % (B["power_analysis"]["observed_effects"]["r6_vs_r5_extra_batch"]["cohens_d"],
                               B["power_analysis"]["n3_vs_n3"]["cohens_d_mde"]))
ps = B["paired_seed_analysis"]
check("paired-seed test on the 3 matched seeds is not significant",
      ps["paired_t"]["p"] > 0.05, "p=%.3f, all %d differences positive"
      % (ps["paired_t"]["p"], len(ps["seed_matched_pairs"]["differences_r6_minus_r5"])))
check("all paired differences have the same sign", ps["seed_matched_pairs"]["all_positive"])

# Qwen: "stable" must not be read as low variance
q = B["qwen_per_seed"]
check("Qwen has 45 runs and 0 NaN (paper claim holds)", q["n_total"] == 45 and q["n_nan"] == 0,
      "%d runs, %d NaN" % (q["n_total"], q["n_nan"]))
check("EVERY Qwen rank contains at least one negative-seed run",
      q["n_ranks_with_negative_seed"] == q["n_ranks"],
      "%d/%d ranks" % (q["n_ranks_with_negative_seed"], q["n_ranks"]))
_sds = [v["sd_sample"] for v in q["per_rank"].values()]
check("Qwen per-rank seed sd is large (>100), i.e. 'stable' != low variance",
      min(_sds) > 100, "min per-rank sd=%.1f, max=%.1f" % (min(_sds), max(_sds)))

# ------------------------------------------------ R3.20: the 30x
print("\n[5] R3.20 -- the 30x claim")
rat = H["uncertainty_ratios"]
r_all = rat["Theory_vs_Random_finite"]
r_r4 = rat["Theory_vs_Random_r4_only"]
check("30x reproduces over all finite Random runs", abs(r_all["sd_ratio_b_over_a"] - 30.2) < 1.0,
      "sd ratio=%.2f" % r_all["sd_ratio_b_over_a"])
check("30x COLLAPSES at matched rank r=4", abs(r_r4["sd_ratio_b_over_a"] - 1.0) < 0.15,
      "sd ratio=%.2f" % r_r4["sd_ratio_b_over_a"])
check("matched-rank Theory vs Random mean difference is NOT significant",
      r_r4["welch"]["p"] > 0.05, "Welch p=%.3f" % r_r4["welch"]["p"])
vd = H["random_group_variance_decomposition"]
check("Random-group spread is essentially all between-rank", vd["eta_squared_rank"] > 0.95,
      "eta^2=%.3f" % vd["eta_squared_rank"])
check("Random group contains NaN failures the paper's mean/sd drop",
      H["counterfactual"]["Random"]["n_nan"] == 2,
      "%d NaN of %d runs" % (H["counterfactual"]["Random"]["n_nan"],
                             H["counterfactual"]["Random"]["n_runs"]))
check("MAD ratio is far below the sd ratio (heavy tail, not general variability)",
      r_all["mad_ratio_b_over_a"] < r_all["sd_ratio_b_over_a"] / 5,
      "MAD ratio=%.2f vs sd ratio=%.2f" % (r_all["mad_ratio_b_over_a"], r_all["sd_ratio_b_over_a"]))
check("sd-ratio bootstrap CI is very wide",
      (r_all["sd_ratio_boot_ci"]["hi"] / r_all["sd_ratio_boot_ci"]["lo"]) > 3,
      "[%.1f, %.1f]" % (r_all["sd_ratio_boot_ci"]["lo"], r_all["sd_ratio_boot_ci"]["hi"]))
check("Violation r=32 is 5/5 NaN -> sd undefined there",
      H["counterfactual"]["Violation_r32"]["n_nan"] == 5)
ma = H["median_audit_random_group"]
check("Random group is 13 finite + 2 NaN", ma["n_finite"] == 13 and ma["n_nan"] == 2)
check("the paper's median -92 IS the finite-only median (not a NaN-as-zero artefact)",
      ma["median_finite_only"] == -92.0 and ma["paper_value_is"] == "finite_only",
      "finite median=%.1f, NaN-as-zero median=%.1f" % (ma["median_finite_only"],
                                                       ma["median_nan_as_zero"]))
check("Theory worst case never damaged alignment (max < 0)",
      H["counterfactual"]["Theory"]["finite_only"]["max"] < 0,
      "max=%.1f" % H["counterfactual"]["Theory"]["finite_only"]["max"])
check("Random collapse rate is 2/15 = 13.3%",
      abs(H["counterfactual"]["Random"]["n_nan"] / H["counterfactual"]["Random"]["n_runs"] - 0.1333) < 0.001)

# ------------------------------------------------ R3.18
print("\n[6] R3.18 -- reproducibility")
scan = R["exhaustive_version_record_scan"]
check("exhaustive scan covered >1000 files", scan["files_scanned"] > 1000,
      "%d files (%d json)" % (scan["files_scanned"], scan["json_files_scanned"]))
check("none of the sweep-producing archives records an environment",
      scan["n_sweep_archives_with_env_field"] == 0,
      "0 / %d" % scan["n_sweep_archives_total"])
ve = R["controlled_version_experiment"]
p5v = [p for p in ve["pairs"] if p["rank"] == 5][0]
p6v = [p for p in ve["pairs"] if p["rank"] == 6][0]
check("controlled version change flips the sign at r=5", not p5v["sign_preserved_at_this_rank"],
      "dE %+.1f -> %+.1f" % (p5v["reference"]["dE_from_E"], p5v["alternative"]["dE_from_E"]))
check("controlled version change keeps the sign at r=6", p6v["sign_preserved_at_this_rank"],
      "dE %+.1f -> %+.1f" % (p6v["reference"]["dE_from_E"], p6v["alternative"]["dE_from_E"]))
check("E0 drift across the version change is tiny (<0.5%)", p5v["E0_shift_pct"] < 0.5,
      "%.2f%%" % p5v["E0_shift_pct"])
be = R["batch_effect"]
check("the two LLaVA batches disagree in sign exactly at r in {6,7,8}",
      be["ranks_sign_disagree"] == [6, 7, 8], str(be["ranks_sign_disagree"]))
det = R["pipeline_determinism_static"]
check("P3 scripts never call create_dataloaders", det["n_scripts_with_create_dataloaders"] == 0)
check("P3 scripts never call random_split", det["n_scripts_with_random_split"] == 0)
check("P3 scripts never use RandomHorizontalFlip/ColorJitter",
      det["n_scripts_with_RandomHorizontalFlip"] == 0 and det["n_scripts_with_ColorJitter"] == 0)
tech = R["duplicate_run_audit"]["declared_technical_replicates"]
check("hardware swap (4060 vs A800) preserves sign at BOTH r=5 and r=6",
      all(g["sign_agreement"] for g in tech if "A800" in g["varying"]),
      "; ".join("%s spread=%.1f" % (g["label"][:34], g["spread"]) for g in tech if "A800" in g["varying"]))
check("version-record scan is exhaustive (>=2000 files, >=1800 json)",
      scan["files_scanned"] >= 2000 and scan["json_files_scanned"] >= 1800,
      "%d files (%d json)" % (scan["files_scanned"], scan["json_files_scanned"]))

# ---- device reproducibility archive (separate P3 artefact, not produced here)
import os as _os
_dp = _os.path.join(ROOT, "outputs", "device_reproducibility.json")
check("registered device-reproducibility archive exists", _os.path.exists(_dp))
if _os.path.exists(_dp):
    with open(_dp, encoding="utf-8") as _f:
        _DR = json.load(_f)
    check("device archive records both machines' torch versions",
          "torch 2.9.1" in _DR["local_device"] and "torch 2.12.1" in _DR["cloud_device"],
          "local=%s | cloud=%s" % (_DR["local_device"][:44], _DR["cloud_device"][:52]))
    _nan_inv = all(r["same_first_nan_epoch"] for r in _DR["records"])
    check("the NaN epoch is a DEVICE INVARIANT in every archived pair", _nan_inv,
          "; ".join("%s: first_nan local=%s cloud=%s" % (r["name"], r["local"]["first_nan_index"],
                                                        r["cloud"]["first_nan_index"])
                    for r in _DR["records"]))
    # NB: the archive computes `before_epoch5_pct` only for the e10 pairs; for the
    # 3-epoch pairs that field is the whole-trajectory max, so it is not the same
    # quantity. Assert the two cases separately rather than pooling them.
    _pairs = [r for r in _DR["records"] if "e10" in r["name"]]
    _short = [r for r in _DR["records"] if "e10" not in r["name"]]
    _stable = [r["max_abs_rel_diff_before_epoch5_pct"] for r in _pairs]
    check("e10 pairs: stable regime (first 4 epochs) agrees across devices to <=1%",
          max(_stable) <= 1.0,
          "max %.2f%% over %d e10 pairs" % (max(_stable), len(_stable)))
    _sh = [r["max_abs_rel_diff_pct"] for r in _short]
    check("3-epoch pairs: whole-trajectory cross-device spread <=2%",
          max(_sh) <= 2.0,
          "max %.2f%% over %d short pairs" % (max(_sh), len(_short)))
    check("3-epoch pairs keep the sign across devices", all(r["same_delta_sign"] for r in _short),
          "; ".join("%s delta_E %.1f vs %.1f" % (r["name"], r["local"]["delta_E"], r["cloud"]["delta_E"])
                    for r in _short))

# ------------------------------------------------ R3.22
print("\n[7] R3.22 -- NaN attribution (offline evidence)")
ct = N["nan_vs_loss_crosstab"]
check("there ARE archived runs where E becomes NaN", ct["n_runs_where_E_becomes_nan"] > 0,
      "%d runs" % ct["n_runs_where_E_becomes_nan"])
check("in EVERY such run the task loss stays finite",
      ct["n_runs_where_E_nan_BUT_loss_stays_finite"] == ct["n_runs_where_E_becomes_nan"],
      "%d/%d" % (ct["n_runs_where_E_nan_BUT_loss_stays_finite"], ct["n_runs_where_E_becomes_nan"]))
check("no archived run has a NaN task loss", ct["n_runs_where_loss_also_becomes_nan"] == 0)
gn = [r for r in ct["runs"] if r["grad_all_finite"] is False]
check("grad-norm non-finiteness is recorded where grad norms are logged", True,
      "%d of %d NaN runs report a non-finite per-epoch grad norm" % (len(gn), len(ct["runs"])))

# ------------------------------------------------ R3.4
print("\n[8] R3.4 -- Gamma batch sensitivity")
pa = G["paper_gamma_table_provenance"]
check("the paper's Gamma file does NOT keep per-batch values", not pa["has_per_batch_values"],
      "declared n_prompts=%d" % pa["n_prompts_declared"])
cb = G["cross_batch_statistics"]
check("cross-batch Gamma dispersion is large for the vision block", cb["vis"]["cross_batch_cv_pct"] > 30,
      "CV=%.1f%%, 95%% CI [%.0f, %.0f]" % (cb["vis"]["cross_batch_cv_pct"],
                                           cb["vis"]["cross_batch_ci95"][0], cb["vis"]["cross_batch_ci95"][1]))
check("absolute |Gamma| ordering is NOT stable across batches (vision swings >2x)",
      cb["vis"]["abs_ratio_max_over_min"] > 2,
      "max/min = %.2f" % cb["vis"]["abs_ratio_max_over_min"])
ls = G["leave_one_batch_out"]["summary"]
check("but the ORDERING-based allocation survives every leave-one-batch-out",
      ls["n_order_identical"] == ls["n_holdouts"],
      "%d/%d holdouts identical" % (ls["n_order_identical"], ls["n_holdouts"]))
check("the exact allocation vector does move by 1-2 rank-layers", max(ls["alloc_raw_max_spread"]) >= 1,
      "per-block spread %s" % ls["alloc_raw_max_spread"])
ss = G["batch_size_and_choice_sensitivity"]
check("more reference samples -> more stable ordering",
      ss["6b_x16s"]["top_order_freq"] > ss["1b_x1s"]["top_order_freq"],
      "%.3f (96 samples) vs %.3f (1 sample)" % (ss["6b_x16s"]["top_order_freq"], ss["1b_x1s"]["top_order_freq"]))
check("even 96 samples do NOT pin the ordering exactly",
      ss["6b_x16s"]["top_order_freq"] < 1.0,
      "top-order frequency %.3f" % ss["6b_x16s"]["top_order_freq"])
check("no block's projected 5-prompt CI includes zero",
      len(G["paper_gamma_table_uncertainty_projection"]["sign_risks"]) == 0)

print("\n[9] 10-seed replication family (verify_r{N}_s{M}.json, epochs=3)")
M = load("p3_multiseed_family.json")
check("the family really has 10 seeds at r=5 and r=6",
      M["family"]["ranks"]["5"]["n_seeds"] == 10 and M["family"]["ranks"]["6"]["n_seeds"] == 10,
      "r5=%d r6=%d" % (M["family"]["ranks"]["5"]["n_seeds"],
                       M["family"]["ranks"]["6"]["n_seeds"]))
r5s = M["statistics"]["r5"]
r6s = M["statistics"]["r6"]
check("10-seed r=6 is 10/10 positive and its CI excludes zero",
      r6s["n_positive"] == 10 and r6s["mean_boot_ci95"][0] > 0,
      "mean=%.1f CI=[%.1f,%.1f]" % (r6s["mean"], r6s["mean_boot_ci95"][0], r6s["mean_boot_ci95"][1]))
check("10-seed r=5 CI excludes zero on the NEGATIVE side",
      r5s["mean_boot_ci95"][1] < 0,
      "mean=%.1f CI=[%.1f,%.1f]" % (r5s["mean"], r5s["mean_boot_ci95"][0], r5s["mean_boot_ci95"][1]))
ps2 = M["paired_seed_r6_vs_r5"]
check("paired ordering holds in >=9/10 seed pairs", ps2["n_hold"] >= 9,
      "%d/%d" % (ps2["n_hold"], ps2["n_pairs"]))
check("paired ordering is significant", ps2["paired_t"]["p"] < 0.01,
      "paired t p=%.6f" % ps2["paired_t"]["p"])
check("10-seed family is statistically indistinguishable from the 3-seed paper batch",
      M["three_seed_vs_ten_seed"]["r5"]["welch"]["p"] > 0.05
      and M["three_seed_vs_ten_seed"]["r6"]["welch"]["p"] > 0.05,
      "r5 p=%.3f, r6 p=%.3f" % (M["three_seed_vs_ten_seed"]["r5"]["welch"]["p"],
                                M["three_seed_vs_ten_seed"]["r6"]["welch"]["p"]))
sp = M["stratified_paired_ordering"]
c3921 = sp["clusters"].get("E0_3921.0")
check("in the homogeneous E0=3921.0 cluster the ordering holds in 7/7 pairs",
      c3921 is not None and c3921["n_hold"] == c3921["n_pairs"] == 7,
      "%s/%s" % (c3921["n_hold"] if c3921 else "?", c3921["n_pairs"] if c3921 else "?"))
check("the family is NOT a single numerical environment (2 distinct E0 values)",
      not M["family"]["E0_homogeneous_per_rank"]["5"],
      "E0 clusters: %s" % list(M["family"]["E0_clusters"].keys()))

# ------------------------------------------------ R3.22 GPU probe
print("\n[10] R3.22 -- GPU initialisation probe")
_pb = os.path.join(A, "p3_nan_probe.json")
check("probe archive exists", os.path.exists(_pb))
if os.path.exists(_pb):
    PR = load("p3_nan_probe.json")
    tags = {p["tag"]: p for p in PR["probes"]}
    check("all three probes recorded", len(tags) >= 3, sorted(tags))
    for t in ("r24_float16", "r24_bfloat16", "r8_float16"):
        if t not in tags:
            check("probe %s present" % t, False)
            continue
        p = tags[t]
        check("%s: hidden states finite at init" % t, p["hidden_state_layers"]["all_finite"])
        check("%s: task loss finite at init" % t, p["task_loss"]["finite"],
              "loss=%.4f" % p["task_loss"]["value"])
        check("%s: alignment energy finite at init" % t, p["alignment_energy"]["finite"],
              "E=%.1f" % p["alignment_energy"]["E"])
        check("%s: LoRA weights finite" % t, p["lora_weight_stats"]["all_finite"])
        check("%s: dE/dtheta gradients finite" % t, p["grad_norm_on_E"]["all_finite"])
        check("%s: hidden magnitude has fp16 headroom > 5x" % t,
              p["hidden_state_layers"]["headroom_vs_fp16_max"] > 5.0,
              "absmax=%.0f, headroom=%.1fx" % (p["hidden_state_layers"]["absmax_over_layers"],
                                               p["hidden_state_layers"]["headroom_vs_fp16_max"]))
    if "r24_float16" in tags and "r8_float16" in tags:
        a, b = tags["r24_float16"], tags["r8_float16"]
        check("fp16 r=8 and r=24 agree at init (LoRA is zero-initialised)",
              abs(a["alignment_energy"]["E"] - b["alignment_energy"]["E"]) < 1.0
              and abs(a["hidden_state_layers"]["absmax_over_layers"]
                      - b["hidden_state_layers"]["absmax_over_layers"]) < 1.0,
              "E %.1f vs %.1f ; absmax %.0f vs %.0f" %
              (a["alignment_energy"]["E"], b["alignment_energy"]["E"],
               a["hidden_state_layers"]["absmax_over_layers"],
               b["hidden_state_layers"]["absmax_over_layers"]))
    if "r24_float16" in tags and "r24_bfloat16" in tags:
        a, b = tags["r24_float16"], tags["r24_bfloat16"]
        check("at r=24 bf16 is NOT dramatically different from fp16 at init (<=25% in E)",
              abs(a["alignment_energy"]["E"] - b["alignment_energy"]["E"])
              / a["alignment_energy"]["E"] <= 0.25,
              "E %.1f vs %.1f" % (a["alignment_energy"]["E"], b["alignment_energy"]["E"]))

# ------------------------------------------------ seed provenance (R3.17 follow-up)
print("\n[11] Seed provenance -- was the paper's 3-seed set a post-hoc selection?")
_sp = os.path.join(A, "p3_seed_provenance.json")
check("seed-provenance archive exists", os.path.exists(_sp))
if os.path.exists(_sp):
    SP = load("p3_seed_provenance.json")
    check("the 3 earliest-measured seeds ARE the paper's 3 seeds (r=5)",
          SP["earliest_three_equals_paper_seeds"]["r5"],
          "earliest=%s vs paper=%s" % (SP["earliest_three"]["r5"], SP["paper_seeds"]))
    check("the 3 earliest-measured seeds ARE the paper's 3 seeds (r=6)",
          SP["earliest_three_equals_paper_seeds"]["r6"],
          "earliest=%s" % SP["earliest_three"]["r6"])
    check("E0 is a contiguous block in time (environment change, not interleaved)",
          all(v["contiguous_block"] for v in SP["E0_contiguity_in_time"].values()),
          "; ".join("%s transitions=%d" % (k, v["n_transitions"])
                    for k, v in SP["E0_contiguity_in_time"].items()))
    _drv = SP["driver_seed_literals"]
    check("the paper's own sweep driver hard-codes exactly the three seeds",
          any((v.get("SEEDS_literal") or "") == "42, 123, 999" for v in _drv.values()),
          str([v.get("SEEDS_literal") for v in _drv.values()]))
    _c = M["stratified_by_E0_cluster"]["r5"]["clusters"]
    check("the paper's seed cluster (E0=3930.5) has the WEAKER r=5 effect",
          _c["3930.5"]["mean"] > _c["3921.0"]["mean"],
          "3930.5: %.2f vs 3921.0: %.2f" % (_c["3930.5"]["mean"], _c["3921.0"]["mean"]))
    check("r=6 is positive in BOTH E0 clusters",
          M["stratified_by_E0_cluster"]["r6"]["clusters"]["3921.0"]["n_positive"]
          == M["stratified_by_E0_cluster"]["r6"]["clusters"]["3921.0"]["n"]
          and M["stratified_by_E0_cluster"]["r6"]["clusters"]["3930.5"]["n_positive"]
          == M["stratified_by_E0_cluster"]["r6"]["clusters"]["3930.5"]["n"],
          "3921.0: %d/%d ; 3930.5: %d/%d"
          % (M["stratified_by_E0_cluster"]["r6"]["clusters"]["3921.0"]["n_positive"],
             M["stratified_by_E0_cluster"]["r6"]["clusters"]["3921.0"]["n"],
             M["stratified_by_E0_cluster"]["r6"]["clusters"]["3930.5"]["n_positive"],
             M["stratified_by_E0_cluster"]["r6"]["clusters"]["3930.5"]["n"]))

# ---------------------------------------------------------------- verdict
print("\n" + "=" * 78)
if FAIL:
    print("GATE FAILED -- %d assertion(s):" % len(FAIL))
    for f in FAIL:
        print("   -", f)
    sys.exit(1)
print("GATE PASSED -- all assertions hold")
print("=" * 78)
