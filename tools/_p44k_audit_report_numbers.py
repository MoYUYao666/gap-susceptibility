#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p44k_audit_report_numbers.py -- extract every numeric claim in
docs/P3_STATS.md that matches a known archive value and flag any that does NOT
match the archive. Cheap sanity net, NOT a substitute for _p44a's assertions.
"""
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "outputs", "analysis")
DOC = os.path.join(ROOT, "docs", "P3_STATS.md")


def L(p):
    return json.load(open(os.path.join(A, p), encoding="utf-8"))


H = L("p3_stats_hardened.json")
B = L("p3_phase_boundary.json")
R = L("p3_reproducibility.json")
N = L("p3_nan_diagnostics.json")
M = L("p3_multiseed_family.json")
G = L("p3_gamma_batch_sensitivity.json")

# (label, value the report states, value in the archive)
# NOTE ON VOLATILE COUNTS: the version-scan counts grow every time _p446 is re-run,
# because it also scans the artefacts written by these very scripts. The report
# quotes a timestamped snapshot, so compare against the LIVE archive value here and
# treat a mismatch on these four as expected drift, not as an error.
_VOLATILE = {"file count", "json count", "key hits", "text hits"}
CHECKS = [
    ("r5 bootstrap CI lo", -51.5, H["phase_transition"]["r5"]["mean_ci"]["lo"]),
    ("r5 bootstrap CI hi", 12.5, H["phase_transition"]["r5"]["mean_ci"]["hi"]),
    ("r6 bootstrap CI lo", 30.5, H["phase_transition"]["r6"]["mean_ci"]["lo"]),
    ("r6 bootstrap CI hi", 121.5, H["phase_transition"]["r6"]["mean_ci"]["hi"]),
    ("r5 t p", 0.375, H["phase_transition"]["r5"]["t_vs_zero"]["p"]),
    ("r6 t p", 0.170, H["phase_transition"]["r6"]["t_vs_zero"]["p"]),
    ("pooled welch p", 0.0255, H["pooled_llava_tests"]["pooled_r45_vs_r67"]["welch"]["p"]),
    ("order audit binom p", 0.0078, B["r6_gt_r5_exhaustive_audit"]["exact_sign_test_all_hold"]["p_two_sided"]),
    ("MDE d", 2.95, B["power_analysis"]["n3_vs_n3"]["cohens_d_mde"]),
    ("observed d", 1.95, B["power_analysis"]["observed_effects"]["r6_vs_r5_extra_batch"]["cohens_d"]),
    ("30x ratio", 30.23, H["uncertainty_ratios"]["Theory_vs_Random_finite"]["sd_ratio_b_over_a"]),
    ("matched sd ratio", 0.98, H["uncertainty_ratios"]["Theory_vs_Random_r4_only"]["sd_ratio_b_over_a"]),
    ("matched welch p", 0.47, H["uncertainty_ratios"]["Theory_vs_Random_r4_only"]["welch"]["p"]),
    ("eta2 rank", 0.989, H["random_group_variance_decomposition"]["eta_squared_rank"]),
    ("random mean", 490.81, H["counterfactual"]["Random"]["finite_only"]["mean"]),
    ("random sd", 808.08, H["counterfactual"]["Random"]["finite_only"]["sd_sample"]),
    ("theory mean", -108.0, H["counterfactual"]["Theory"]["finite_only"]["mean"]),
    ("theory sd", 26.73, H["counterfactual"]["Theory"]["finite_only"]["sd_sample"]),
    ("median finite", -92.0, H["median_audit_random_group"]["median_finite_only"]),
    ("file count", 2066, R["exhaustive_version_record_scan"]["files_scanned"]),
    ("json count", 1816, R["exhaustive_version_record_scan"]["json_files_scanned"]),
    ("key hits", 36, len(R["exhaustive_version_record_scan"]["key_level_hits"])),
    ("text hits", 31, len(R["exhaustive_version_record_scan"]["text_level_hits"])),
    ("nan runs", 17, N["nan_vs_loss_crosstab"]["n_runs_where_E_becomes_nan"]),
    ("nan loss-finite", 17, N["nan_vs_loss_crosstab"]["n_runs_where_E_nan_BUT_loss_stays_finite"]),
    ("r5 10seed mean", -34.70, M["statistics"]["r5"]["mean"]),
    ("r6 10seed mean", 69.90, M["statistics"]["r6"]["mean"]),
    ("r5 10seed CI lo", -58.20, M["statistics"]["r5"]["mean_boot_ci95"][0]),
    ("r6 10seed CI lo", 52.25, M["statistics"]["r6"]["mean_boot_ci95"][0]),
    ("paired t", 5.569, M["paired_seed_r6_vs_r5"]["paired_t"]["t"]),
    ("paired p", 0.000348, M["paired_seed_r6_vs_r5"]["paired_t"]["p"]),
    ("paired diff", 104.60, M["paired_seed_r6_vs_r5"]["mean_diff"]),
    ("paired diff CI lo", 62.11, M["paired_seed_r6_vs_r5"]["mean_diff_ci95"][0]),
    ("paired diff CI hi", 147.09, M["paired_seed_r6_vs_r5"]["mean_diff_ci95"][1]),
    ("r5 cluster3921 mean", -49.00, M["stratified_by_E0_cluster"]["r5"]["clusters"]["3921.0"]["mean"]),
    ("r5 cluster3930 mean", -1.33, M["stratified_by_E0_cluster"]["r5"]["clusters"]["3930.5"]["mean"]),
    ("vis CV", 59.9, G["cross_batch_statistics"]["vis"]["cross_batch_cv_pct"]),
    ("vis maxmin", 5.38, G["cross_batch_statistics"]["vis"]["abs_ratio_max_over_min"]),
    ("lobo identical", 6, G["leave_one_batch_out"]["summary"]["n_order_identical"]),
    ("1s topfreq", 0.308, G["batch_size_and_choice_sensitivity"]["1b_x1s"]["top_order_freq"]),
    ("96s topfreq", 0.688, G["batch_size_and_choice_sensitivity"]["6b_x16s"]["top_order_freq"]),
]

bad = []
skipped_volatile = []
print("%-24s %-14s %-14s %s" % ("check", "report", "archive", "rel.diff"))
for label, stated, actual in CHECKS:
    if actual is None:
        bad.append((label, stated, actual, "archive None"))
        print("%-24s %-14s %-14s MISSING" % (label, stated, actual))
        continue
    rel = abs(stated - actual) / max(abs(actual), 1e-12)
    if rel > 0.005 and label in _VOLATILE:
        skipped_volatile.append((label, stated, actual))
        print("%-24s %-14s %-14s %.2e DRIFT(volatile count, expected)" % (label, stated, actual, rel))
        continue
    flag = "OK" if rel <= 0.005 else "**MISMATCH**"
    if rel > 0.005:
        bad.append((label, stated, actual, rel))
    print("%-24s %-14s %-14s %.2e %s" % (label, stated, actual, rel, flag))

print()
if skipped_volatile:
    print("volatile counts drifted (expected; report quotes a timestamped snapshot):")
    for s in skipped_volatile:
        print("   %s: report %s vs live %s" % s)
if bad:
    print("PROBLEMS: %d" % len(bad))
    for b in bad:
        print("  ", b)
else:
    print("all %d report numbers match the archive (%d volatile counts excluded)"
          % (len(CHECKS) - len(skipped_volatile), len(skipped_volatile)))

# also: does the doc still contain the retracted wrong claim?
doc = io.open(DOC, encoding="utf-8").read()
print("\n--- retraction hygiene ---")
for bad_phrase in ["median is $-111.5$", "论文 median 用了 NaN→0", "median 不一致（这是论文的一个小瑕疵）"]:
    print("  contains retracted phrase %-40s : %s" % (repr(bad_phrase), bad_phrase in doc))
