#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1658_audit_traceability.py -- task-21 independent number-traceability spot check.

For each number: locate the manuscript line, the Source/Archive pointer that names its
script and field, re-read the archive field, and compare with the printed value.
Exit code 0 only if every CHECKED number agrees; numbers that are archived but NOT printed
in any manuscript are reported as findings, not failures of arithmetic.

Outputs outputs/analysis/audit_traceability.json and prints a table.
"""
import json
import os
import re
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = ROOT / "outputs/analysis/audit_traceability.json"
TEX_DIRS = ["paper3/paper_ieee", "paper合", "paper_a1", "paper_a2", "paper_review_prl"]


def jload(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def dig(obj, path):
    cur = obj
    for part in path.split("."):
        m = re.match(r"^([^\[]+)\[(\d+)\]$", part)
        if m:
            cur = cur[m.group(1)][int(m.group(2))]
        else:
            cur = cur[part]
    return cur


def dig_rc(obj):
    """rc_by_family keys contain dots ('llava-1.5-7b'), so walk them explicitly."""
    fam = obj["rc_by_family"]["llava-1.5-7b"]["sensitivity_span"]
    return fam


def find_in_tex(needle):
    """Return (relative path, 1-based line, line text) for the first .tex hit."""
    for d in TEX_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for p in base.rglob("*.tex"):
            t = p.read_text(encoding="utf-8", errors="replace")
            i = t.find(needle)
            if i >= 0:
                line = t[:i].count("\n") + 1
                return str(p.relative_to(ROOT)), line, t.split("\n")[line - 1].strip()[:200]
    return None, None, None


def source_pointer(rel, line, window=60):
    """Lines around the hit that name a script (`tools/...py`) and an archive (`...json`)."""
    p = ROOT / rel
    lines = p.read_text(encoding="utf-8", errors="replace").split("\n")
    lo, hi = max(0, line - window), min(len(lines), line + window)
    chunk = "\n".join(lines[lo:hi]).replace("\\_", "_").replace("\\allowbreak", "").replace("\\", "")
    scripts = sorted(set(re.findall(r"(?:tools|paper3/scripts|exp)/[\w./-]+\.py", chunk)))
    archives = sorted(set(re.findall(r"outputs/[\w./{},\-*]+\.json", chunk)))
    return scripts, archives


CHECKS = [
    # id, printed needle as it appears in the manuscript, archive, field, formatter, expected-from-archive
    dict(id="T1_env_share_49.59", needle="49.59\\%",
         tex="paper3/paper_ieee/supplementary/supplementary.tex",
         archive="outputs/analysis/p3_env_stack_seeds.json",
         field="sigma_by_rank.5.all_rows.env_variance_share",
         fmt=lambda v: "%.2f%%" % (v * 100), printed="49.59%"),
    dict(id="T2a_sigma_env_32.46", needle="32.46",
         archive="outputs/analysis/p3_env_stack_seeds.json",
         field="sigma_by_rank.5.all_rows.sigma_env", fmt=lambda v: "%.2f" % v, printed="32.46"),
    dict(id="T2b_sigma_seed_32.72", needle="32.72",
         archive="outputs/analysis/p3_env_stack_seeds.json",
         field="sigma_by_rank.5.all_rows.sigma_seed", fmt=lambda v: "%.2f" % v, printed="32.72"),
    dict(id="T3_share_ci_35.8_74.9", needle="[35.8\\%,74.9\\%]",
         archive="outputs/analysis/p3_env_stack_seeds.json",
         field="sigma_by_rank.5.all_rows.bootstrap.share_ci95",
         fmt=lambda v: "[%.1f%%,%.1f%%]" % (v[0] * 100, v[1] * 100), printed="[35.8%,74.9%]"),
    dict(id="T4a_alloc_paired_-3570.10", needle="-3570.10",
         archive="outputs/analysis/p3_allocation_paired_stats.json",
         field="paired.capacity_matched_by_seed.mean_difference",
         fmt=lambda v: "%.2f" % v, printed="-3570.10"),
    dict(id="T4b_alloc_ci_lo", needle="-5524.16",
         archive="outputs/analysis/p3_allocation_paired_stats.json",
         field="paired.capacity_matched_by_seed.ci95_percentile[0]",
         fmt=lambda v: "%.2f" % v, printed="-5524.16"),
    dict(id="T4c_alloc_ci_hi", needle="-1850.31",
         archive="outputs/analysis/p3_allocation_paired_stats.json",
         field="paired.capacity_matched_by_seed.ci95_percentile[1]",
         fmt=lambda v: "%.2f" % v, printed="-1850.31"),
    dict(id="T5a_gamma_break_even_0.160", needle="0.160",
         archive="outputs/analysis/p3_gamma_robustness.json",
         field="noise_break_even.rho_order_flip", fmt=lambda v: "%.3f" % v, printed="0.160"),
    dict(id="T5b_gamma_rel_sd_4.227", needle="4.227",
         archive="outputs/analysis/p3_gamma_robustness.json",
         field="noise_break_even.noise_to_tolerance_ratios.worst_observed_relative_sd",
         fmt=lambda v: "%.3f" % v, printed="4.227"),
    dict(id="T5c_ratio_26.4x", needle="26.4",
         archive="outputs/analysis/p3_gamma_robustness.json",
         field="noise_break_even.noise_to_tolerance_ratios.worst_observed_relative_sd",
         fmt=lambda v: "%.1f" % (v / dig(jload("outputs/analysis/p3_gamma_robustness.json"),
                                         "noise_break_even.rho_order_flip")), printed="26.4"),
    dict(id="T6a_rc_span_lo_4.96", needle="4.96",
         archive="outputs/analysis/p3_rc_family_boundary.json",
         field="rc_by_family.llava-1.5-7b.sensitivity_span[0]", rc_idx=0,
         fmt=lambda v: "%.2f" % v, printed="4.96"),
    dict(id="T6b_rc_span_hi_46.76", needle="46.76",
         archive="outputs/analysis/p3_rc_family_boundary.json",
         field="rc_by_family.llava-1.5-7b.sensitivity_span[1]", rc_idx=1,
         fmt=lambda v: "%.2f" % v, printed="46.76"),
    dict(id="T7a_a23_scored_4940", needle="4940",
         tex="paper_a2/ext_partII_domains.tex",
         archive="outputs/analysis/a23_multiencoder_transfer.json",
         field="conclusion.n_scored_entries_cross_unit", fmt=lambda v: "%d" % v, printed="4940"),
    dict(id="T7b_a23_survivors_29", needle="$29$ keep their",
         archive="outputs/analysis/a23_multiencoder_transfer.json",
         field="conclusion.n_entries_surviving_bootstrap", fmt=lambda v: "%d" % v, printed="29"),
    dict(id="T8_pope_acc_base_r5", needle="-0.2460",
         tex="paper3/paper_ieee/supplementary/supplementary.tex",
         archive="outputs/analysis/p3_second_downstream.json",
         field="contrasts.base_minus_5.accuracy.delta", fmt=lambda v: "%.4f" % v, printed="-0.2460"),
    dict(id="T8b_pope_acc_ci", needle="[-0.2627,-0.2297]",
         archive="outputs/analysis/p3_second_downstream.json",
         field="contrasts.base_minus_5.accuracy.ci95",
         fmt=lambda v: "[%.4f,%.4f]" % (v[0], v[1]), printed="[-0.2627,-0.2297]"),
    dict(id="T9_pope_tokf1_base_r6", needle="-0.1583",
         archive="outputs/analysis/p3_second_downstream.json",
         field="contrasts.base_minus_6.token_f1.delta", fmt=lambda v: "%.4f" % v, printed="-0.1583"),
    dict(id="T10a_pope_yesf1_base_0.8849", needle="0.8849",
         archive="outputs/analysis/p3_second_downstream.json",
         field="arms.base.pope_f1", fmt=lambda v: "%.4f" % v, printed="0.8849"),
    dict(id="T10b_pope_yesf1_r5_0.8593", needle="0.8593",
         archive="outputs/analysis/p3_second_downstream.json",
         field="arms.5.pope_f1", fmt=lambda v: "%.4f" % v, printed="0.8593"),
    dict(id="T10c_pope_yesf1_r6_0.8237", needle="0.8237",
         archive="outputs/analysis/p3_second_downstream.json",
         field="arms.6.pope_f1", fmt=lambda v: "%.4f" % v, printed="0.8237"),
    dict(id="T11a_pope_yesratio_base", needle="0.4327",
         archive="outputs/analysis/p3_second_downstream.json",
         field="arms.base.yes_ratio", fmt=lambda v: "%.4f" % v, printed="0.4327"),
    dict(id="T11b_pope_yesratio_r5", needle="0.4123",
         archive="outputs/analysis/p3_second_downstream.json",
         field="arms.5.yes_ratio", fmt=lambda v: "%.4f" % v, printed="0.4123"),
    dict(id="T11c_pope_yesratio_r6", needle="0.3733",
         archive="outputs/analysis/p3_second_downstream.json",
         field="arms.6.yes_ratio", fmt=lambda v: "%.4f" % v, printed="0.3733"),
    dict(id="T12a_pope_fn_base_262", needle="$262$", tex="paper3/paper_ieee/supplementary/supplementary.tex",
         archive="outputs/analysis/p3_second_downstream_base.json",
         field="confusion.fn", fmt=lambda v: "%d" % v, printed="262"),
    dict(id="T12b_pope_fn_r5_324", needle="$324$", tex="paper3/paper_ieee/supplementary/supplementary.tex",
         archive="outputs/analysis/p3_second_downstream_5.json",
         field="confusion.fn", fmt=lambda v: "%d" % v, printed="324"),
    dict(id="T12c_pope_fn_r6_421", needle="$421$", tex="paper3/paper_ieee/supplementary/supplementary.tex",
         archive="outputs/analysis/p3_second_downstream_6.json",
         field="confusion.fn", fmt=lambda v: "%d" % v, printed="421"),
]

# numbers that are archived but must be checked for whether they are printed anywhere
ARCHIVED_ONLY = [
    dict(id="A1_official_diff_-59.5", archive="outputs/analysis/p3_official_vs_reimpl.json",
         field="overall.mean_gap_delta_E", needle=None, printed="-59.5",
         note="the only '59.5' string in the manuscript tree is supplementary.tex:532, the unrelated n=64 r=5 cell"),
    dict(id="A2_official_ci_-150.5", archive="outputs/analysis/p3_official_vs_reimpl.json",
         field="overall.ci95[0]", needle="-150.5", printed="-150.5"),
    dict(id="A3_official_ci_hi", archive="outputs/analysis/p3_official_vs_reimpl.json",
         field="overall.ci95[1]", needle=None, printed="(archived)"),
    dict(id="A4_official_margin_196.05", archive="outputs/analysis/p3_official_vs_reimpl.json",
         field="meta.margin", needle="196.05", printed="196.05"),
    dict(id="A5_replicate_max_spread_132.0", archive="outputs/analysis/p3_official_igu_replicates.json",
         field="summary.max_spread_across_arms", needle="132.0", printed="132.0"),
    dict(id="A6_replicate_mean_spread_76.1", archive="outputs/analysis/p3_official_igu_replicates.json",
         field="summary.mean_spread_across_arms", needle="76.1", printed="76.1"),
]

report = {"checked": [], "archived_only": [], "n_ok": 0, "n_fail": 0}
print("=" * 118)
print("NUMBER TRACEABILITY SPOT CHECK")
print("=" * 118)
print("%-26s %-42s %-14s %-14s %s" % ("id", "manuscript", "printed", "archive->formatted", "verdict"))
for c in CHECKS:
    rel = c.get("tex")
    if rel:
        line = None
        t = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        i = t.find(c["needle"])
        if i >= 0:
            line = t[:i].count("\n") + 1
        hit = (rel, line) if line else (rel, None)
    else:
        hit = find_in_tex(c["needle"])[:2]
    loc = "%s:%s" % (hit[0], hit[1]) if hit[1] else "NOT FOUND"
    try:
        if "rc_idx" in c:
            val = dig_rc(jload(c["archive"]))[c["rc_idx"]]
        else:
            val = dig(jload(c["archive"]), c["field"])
        formatted = c["fmt"](val)
        ok_val = (formatted == c["printed"])
    except Exception as e:
        formatted = "ERROR %s" % e
        ok_val = False
    ok = ok_val and hit[1] is not None
    scripts, archives = (source_pointer(hit[0], hit[1]) if hit[1] else ([], []))
    row = {"id": c["id"], "manuscript": loc, "printed": c["printed"],
           "archive": c["archive"], "field": c["field"], "formatted": formatted,
           "ok_value": ok_val, "ok_present": hit[1] is not None,
           "source_scripts_nearby": scripts, "source_archives_nearby": archives}
    report["checked"].append(row)
    if ok:
        report["n_ok"] += 1
    else:
        report["n_fail"] += 1
    print("%-26s %-42s %-14s %-24s %s" % (c["id"], loc, c["printed"], formatted,
                                          "OK" if ok else "**FAIL**"))

print("\n" + "=" * 118)
print("ARCHIVED-BUT-MAYBE-UNPRINTED (today's head-line results)")
print("=" * 118)
for c in ARCHIVED_ONLY:
    try:
        val = dig(jload(c["archive"]), c["field"])
    except Exception as e:
        val = "ERROR %s" % e
    found = find_in_tex(c["needle"])[:2] if c["needle"] else (None, None)
    row = {"id": c["id"], "archive": c["archive"], "field": c["field"],
           "archived_value": (val if not isinstance(val, list) else val),
           "printed_anywhere_in_manuscripts": bool(found[0]),
           "manuscript_location": ("%s:%s" % found if found[0] else None)}
    report["archived_only"].append(row)
    print("  %-30s archived=%s  in-manuscript=%s  %s"
          % (c["id"], ("%.4f" % val) if isinstance(val, float) else val,
             found[0] or "NO", ("%s:%s" % found) if found[0] else ""))

OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
print("\nOK %d / FAIL %d  -> %s" % (report["n_ok"], report["n_fail"], OUT))
raise SystemExit(1 if report["n_fail"] else 0)
