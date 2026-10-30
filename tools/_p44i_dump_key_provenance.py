#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p44i_dump_key_provenance.py -- dump the exact provenance values the report
cites, read straight from the archives (used to hard-code the verification gate)."""
import json, os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "outputs", "analysis")


def L(p):
    return json.load(open(os.path.join(A, p), encoding="utf-8"))


H = L("p3_stats_hardened.json")
R = L("p3_reproducibility.json")
N = L("p3_nan_diagnostics.json")
M = L("p3_multiseed_family.json")
G = L("p3_gamma_batch_sensitivity.json")

print("### R3.20 / uncertainty ratios")
r = H["uncertainty_ratios"]["Theory_vs_Random_finite"]
print("  full sd ratio            = %.2f" % r["sd_ratio_b_over_a"])
print("  full mad ratio           = %.2f" % r["mad_ratio_b_over_a"])
print("  full welch p             = %.4f" % r["welch"]["p"])
print("  full permutation p       = %.5f" % r["permutation"]["p"])
print("  full sd-ratio boot CI    = [%.2f, %.2f]" % (r["sd_ratio_boot_ci"]["lo"], r["sd_ratio_boot_ci"]["hi"]))
r4 = H["uncertainty_ratios"]["Theory_vs_Random_r4_only"]
print("  matched-rank sd ratio    = %.4f" % r4["sd_ratio_b_over_a"])
print("  matched-rank welch p     = %.4f" % r4["welch"]["p"])
print("  matched-rank perm p      = %.5f" % r4["permutation"]["p"])
print("  matched-rank boot CI     = [%.2f, %.2f]" % (r4["sd_ratio_boot_ci"]["lo"], r4["sd_ratio_boot_ci"]["hi"]))
print("  eta^2(rank)              = %.4f" % H["random_group_variance_decomposition"]["eta_squared_rank"])
th = H["counterfactual"]["Theory"]["finite_only"]
rd = H["counterfactual"]["Random"]["finite_only"]
print("  Theory   mean=%.2f sd=%.2f CI=[%.1f,%.1f] max=%.1f" % (th["mean"], th["sd_sample"], th["mean_ci"]["lo"], th["mean_ci"]["hi"], th["max"]))
print("  Random   mean=%.2f sd=%.2f CI=[%.1f,%.1f] max=%.1f" % (rd["mean"], rd["sd_sample"], rd["mean_ci"]["lo"], rd["mean_ci"]["hi"], rd["max"]))
vi = H["counterfactual"]["Violation_r16"]["finite_only"]
print("  Viol16   mean=%.2f sd=%.2f CI=[%.1f,%.1f] max=%.1f" % (vi["mean"], vi["sd_sample"], vi["mean_ci"]["lo"], vi["mean_ci"]["hi"], vi["max"]))

print("\n### R3.17 order audit")
oa = H and json.load(open(os.path.join(A, "p3_phase_boundary.json"), encoding="utf-8"))["r6_gt_r5_exhaustive_audit"]
print("  %d/%d hold, binomial p=%.5f" % (oa["n_r6_gt_r5"], oa["n_configurations"],
                                           oa["exact_sign_test_all_hold"]["p_two_sided"]))
B = json.load(open(os.path.join(A, "p3_phase_boundary.json"), encoding="utf-8"))
print("  MDE n3 d=%.2f ; observed d=%.2f" % (B["power_analysis"]["n3_vs_n3"]["cohens_d_mde"],
                                            B["power_analysis"]["observed_effects"]["r6_vs_r5_extra_batch"]["cohens_d"]))
ex = H["pooled_llava_tests"]["r5_vs_r6_extra_batch"]["permutation_exact"]
print("  r5vs6 exact perm p=%.4f over %d splits" % (ex["p"], ex["n_perm"]))
po = H["pooled_llava_tests"]["pooled_r45_vs_r67"]
print("  pooled welch p=%.5f perm p=%.5f" % (po["welch"]["p"], po["permutation_mc"]["p"]))

print("\n### R3.17 10-seed family")
for k in ("r5", "r6"):
    s = M["statistics"][k]
    print("  %s n=%d mean=%.2f sd=%.2f CI=[%.2f,%.2f] pos=%d/%d p_vs0=%.5f" %
          (k, s["n"], s["mean"], s["sd_sample"], s["mean_boot_ci95"][0], s["mean_boot_ci95"][1],
           s["n_positive"], s["n"], s["t_vs_zero"]["p"]))
ps = M["paired_seed_r6_vs_r5"]
print("  paired %d/%d hold; t=%.3f p=%.6f; perm p=%.4f; diff=%.2f CI=[%.2f,%.2f]" %
      (ps["n_hold"], ps["n_pairs"], ps["paired_t"]["t"], ps["paired_t"]["p"],
       ps["exact_signflip_permutation"]["p_two_sided"], ps["mean_diff"],
       ps["mean_diff_ci95"][0], ps["mean_diff_ci95"][1]))
print("  welch p=%.6f ; sign_test ordering p=%.5f" % (ps["welch"]["p"], ps["sign_test_ordering"]["p_two_sided"]))
for k, v in M["three_seed_vs_ten_seed"].items():
    print("  %s 3-seed mean=%.1f vs 10-seed mean=%.1f welch p=%.4f" %
          (k, v["paper_batch_mean"], v["verify_family_mean"], v["welch"]["p"]))
for k, v in M["stratified_by_E0_cluster"].items():
    for e0, s in v["clusters"].items():
        print("  %s E0=%s n=%d mean=%.2f CI=[%.2f,%.2f] pos=%d/%d" %
              (k, e0, s["n"], s["mean"], s["mean_boot_ci95"][0], s["mean_boot_ci95"][1],
               s["n_positive"], s["n"]))
for k, v in M["stratified_paired_ordering"]["clusters"].items():
    print("  pairs %s: %d/%d hold, r5=%.1f r6=%.1f" % (k, v["n_hold"], v["n_pairs"], v["r5_mean"], v["r6_mean"]))

print("\n### R3.22 offline")
ct = N["nan_vs_loss_crosstab"]
print("  E->NaN runs=%d ; loss-stays-finite=%d ; loss-also-NaN=%d" %
      (ct["n_runs_where_E_becomes_nan"], ct["n_runs_where_E_nan_BUT_loss_stays_finite"],
       ct["n_runs_where_loss_also_becomes_nan"]))
c3 = json.load(open(os.path.join(ROOT, "outputs/device_reproducibility.json"), encoding="utf-8"))
print("  device_repro: local=%s" % c3["local_device"])
print("  device_repro: cloud=%s" % c3["cloud_device"])
for rec in c3["records"]:
    print("    %-14s nan local=%s cloud=%s same=%s maxrel%%=%.2f" %
          (rec["name"], rec["local"]["first_nan_index"], rec["cloud"]["first_nan_index"],
           rec["same_first_nan_epoch"], rec["max_abs_rel_diff_pct"]))

print("\n### R3.4 gamma")
cb = G["cross_batch_statistics"]["vis"]
print("  vis CV=%.1f%% CI=[%.0f,%.0f] max/min=%.2f" % (cb["cross_batch_cv_pct"], cb["cross_batch_ci95"][0],
                                                       cb["cross_batch_ci95"][1], cb["abs_ratio_max_over_min"]))
ls = G["leave_one_batch_out"]["summary"]
print("  LOBO order identical %d/%d ; alloc spread %s" % (ls["n_order_identical"], ls["n_holdouts"],
                                                          ls["alloc_raw_max_spread"]))
ss = G["batch_size_and_choice_sensitivity"]
print("  1b_x1s top freq=%.3f ; 6b_x16s top freq=%.3f" % (ss["1b_x1s"]["top_order_freq"], ss["6b_x16s"]["top_order_freq"]))
print("  sign risks (projected CI includes 0): %d" % len(G["paper_gamma_table_uncertainty_projection"]["sign_risks"]))

print("\n### R3.18 version scan")
sc = R["exhaustive_version_record_scan"]
print("  files=%d json=%d key_hits=%d text_hits=%d sweep_env=%d/%d" %
      (sc["files_scanned"], sc["json_files_scanned"], len(sc["key_level_hits"]),
       len(sc["text_level_hits"]), sc["n_sweep_archives_with_env_field"], sc["n_sweep_archives_total"]))
be = R["batch_effect"]
print("  ranks sign disagree: %s" % be["ranks_sign_disagree"])
det = R["pipeline_determinism_static"]
print("  P3 scripts: create_dataloaders=%d random_split=%d RHF=%d CJ=%d" %
      (det["n_scripts_with_create_dataloaders"], det["n_scripts_with_random_split"],
       det["n_scripts_with_RandomHorizontalFlip"], det["n_scripts_with_ColorJitter"]))
