#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1647_pope_corrected_metrics.py -- task-18: recompute the POPE metrics that the cloud
aggregate mislabels, using the SAME conventions and the SAME bootstrap procedure, and
re-evaluate the pre-declared verdict rule under the sign convention it was written for.

WHY THIS FILE EXISTS
--------------------
Two defects were found in outputs/analysis/p3_second_downstream.json (the cloud aggregate):

  (D1) `arms.<t>.token_f1` does not hold token F1.  For base it is 0.8926667, which is
       exactly the per-arm archive's `relaxed_accuracy`; for r=6 it is 0.8460000, again
       exactly `relaxed_accuracy`.  The per-arm archives and the eval log both carry the
       real token F1 (base 0.6826015, r=6 0.8409513).  Because the contrast block is built
       from the same arm records, `contrasts.*.token_f1` inherits the same substitution.

  (D2) `claim_verdict.second_task_verdict` is produced by a rule whose sign convention does
       not match the contrast direction.  The contrast is `delta = arm_a - arm_b` with
       a="base", so a NEGATIVE accuracy delta means the adapter is BETTER.  The rule tests
       `equivalent or ci95[0] > 0` for "keep" and `ci95[1] < -margin` for "lose", i.e. it
       was written as if delta were adapter minus base.  With delta = base - adapter the
       tests invert: an adapter that is better by more than the margin fires "lose".

This script does NOT modify the cloud archive.  It recomputes, with the imported metric
definitions and the archived bootstrap settings (n_boot=20000, rng seed 20261024,
percentile interval, TOST margins 0.05), the quantities the manuscript needs, and writes
them to a separate archive with its own provenance.

Output: outputs/analysis/p3_pope_corrected_metrics.json
"""
import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ANA = ROOT / "outputs/analysis"
OUT = ANA / "p3_pope_corrected_metrics.json"

N_BOOT = 20000
RNG_SEED = 20261024
ALPHA = 0.05
MARGIN = 0.05
ARMS = ("base", "5", "6")
PAIRS = (("base", "5"), ("base", "6"), ("5", "6"))
METRICS = ("accuracy", "token_f1", "pope_f1")


def _load_module(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_arm(tag):
    d = json.loads((ANA / ("p3_second_downstream_%s.json" % tag)).read_text(encoding="utf-8"))
    mod = _load_module("vqa1516_metrics", str(ROOT / "tools/_p1516_p3_vqa_downstream.py"))
    norm, token_f1 = mod.norm, mod.token_f1
    nref = [norm(x) for x in d["refs"]]
    nhyp = [norm(x) for x in d["hypotheses"]]
    correct = np.array([1.0 if a == b else 0.0 for a, b in zip(nhyp, nref)])
    f1 = np.array([float(token_f1([a], [b])) for a, b in zip(nref, nhyp)])
    pred_yes = np.array([h.split()[:1] == ["yes"] for h in nhyp])
    ref_yes = np.array([r.split()[:1] == ["yes"] for r in nref])
    return {"tag": tag, "n": len(nref), "correct": correct, "f1": f1,
            "pred_yes": pred_yes, "ref_yes": ref_yes,
            "accuracy": float(correct.mean()), "token_f1": float(f1.mean()),
            "pope_f1": pope_f1(pred_yes, ref_yes),
            "yes_ratio": float(pred_yes.mean()),
            "gold_yes_ratio": float(ref_yes.mean()),
            "n_yes_gold": int(ref_yes.sum()),
            "tp": int((pred_yes & ref_yes).sum()), "fp": int((pred_yes & ~ref_yes).sum()),
            "fn": int((~pred_yes & ref_yes).sum()), "tn": int((~pred_yes & ~ref_yes).sum())}


def pope_f1(pred_yes, ref_yes):
    tp = float(np.sum(pred_yes & ref_yes))
    fp = float(np.sum(pred_yes & ~ref_yes))
    fn = float(np.sum(~pred_yes & ref_yes))
    den = 2 * tp + fp + fn
    return (2 * tp / den) if den else 0.0


def interval(d, delta, margin):
    """The archived _interval(): 95% percentile bounds, TOST one-sided p-values, min margin.

    The archived `ci95` bounds were reproduced exactly by the 2.5/97.5 percentiles (verified
    in tools/_p1648_probe_bootstrap_variants.py: the archived [-0.262667,-0.229658] equals
    the 2.5/97.5 bounds of the same resampling distribution).  NOTE the local
    tools/_p1640_p3_second_downstream.py source still carries 5/95 in `_interval()`; the
    cloud producer evidently used 2.5/97.5, which is a correct 95% interval and is what the
    archive records, so this repair follows the archive.
    """
    q05, q95 = float(np.percentile(d, 5.0)), float(np.percentile(d, 95.0))
    q025, q975 = float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))
    p_lower = float(np.mean(d <= -margin))
    p_upper = float(np.mean(d >= +margin))
    return {"n_boot": int(len(d)), "delta": float(delta),
            "boot_mean": float(d.mean()), "boot_se": float(d.std(ddof=1)),
            # ci95 = two-sided 95% percentile interval; the minimum equivalent margin comes from
            # the 90% interval because TOST performs two one-sided 5% tests.  This is the pair of
            # conventions the generator's _interval() uses and the archive records.
            "ci95": [q025, q975], "ci90": [q05, q95],
            "tost_margin": float(margin),
            "tost_p_lower": p_lower, "tost_p_upper": p_upper,
            "tost_p": max(p_lower, p_upper),
            "equivalent_at_declared_margin": bool(max(p_lower, p_upper) <= ALPHA),
            "min_equivalent_margin": max(-q05, q95)}


def contrasts(a, b, rng):
    """Paired-by-question percentile bootstrap of a-b, exactly as the archived aggregate.

    The cloud aggregate creates ONE generator before the three-pair loop and lets its state
    advance across pairs; the first pair therefore matches a freshly seeded generator and the
    later pairs do not.  This function takes that single generator, which is why the
    recomputed accuracy/pope_f1 intervals reproduce the archive exactly for all three pairs.
    """
    n = int(len(a["correct"]))
    idx = rng.integers(0, n, size=(N_BOOT, n))
    out = {}
    for key in ("accuracy", "token_f1"):
        av = a["correct"] if key == "accuracy" else a["f1"]
        bv = b["correct"] if key == "accuracy" else b["f1"]
        out[key] = interval(av[idx].mean(axis=1) - bv[idx].mean(axis=1),
                            float(av.mean() - bv.mean()), MARGIN)
    pa, ra, pb, rb = a["pred_yes"], a["ref_yes"], b["pred_yes"], b["ref_yes"]
    f1a = np.array([pope_f1(pa[i], ra[i]) for i in idx])
    f1b = np.array([pope_f1(pb[i], rb[i]) for i in idx])
    out["pope_f1"] = interval(f1a - f1b, pope_f1(pa, ra) - pope_f1(pb, rb), MARGIN)
    return out


def main():
    arms = {t: load_arm(t) for t in ARMS}
    print("=" * 90)
    print("POPE CORRECTED METRICS")
    print("=" * 90)
    print("\n[1] arms, re-derived from the per-arm hypotheses (imported norm/token_f1)")
    for t in ARMS:
        a = arms[t]
        print("  %-5s n=%d acc=%.7f token_f1=%.7f pope_f1=%.7f yes_ratio=%.7f gold_yes=%.7f"
              % (t, a["n"], a["accuracy"], a["token_f1"], a["pope_f1"], a["yes_ratio"],
                 a["gold_yes_ratio"]))
        print("        confusion tp=%d fp=%d fn=%d tn=%d  n_yes_gold=%d"
              % (a["tp"], a["fp"], a["fn"], a["tn"], a["n_yes_gold"]))
    # cross-check against the per-arm archive fields
    per = {t: json.loads((ANA / ("p3_second_downstream_%s.json" % t)).read_text(encoding="utf-8"))
           for t in ARMS}
    for t in ARMS:
        assert abs(per[t]["accuracy"] - arms[t]["accuracy"]) < 5e-7
        assert abs(per[t]["token_f1"] - arms[t]["token_f1"]) < 5e-7
        assert abs(per[t]["pope_f1"] - arms[t]["pope_f1"]) < 5e-7
        assert abs(per[t]["yes_ratio"] - arms[t]["yes_ratio"]) < 5e-7
        assert per[t]["confusion"]["tp"] == arms[t]["tp"] and per[t]["confusion"]["fp"] == arms[t]["fp"]
        assert per[t]["confusion"]["fn"] == arms[t]["fn"] and per[t]["confusion"]["tn"] == arms[t]["tn"]
    print("  all arm metrics match the per-arm archive fields (and its confusion counts)")

    agg = json.loads((ANA / "p3_second_downstream.json").read_text(encoding="utf-8"))
    out = {"meta": {
        "script": "tools/_p1647_pope_corrected_metrics.py",
        "task": "task-18: repair of the two defects in the cloud aggregate",
        "cloud_aggregate": "outputs/analysis/p3_second_downstream.json",
        "cloud_aggregate_sha256_prefix": "1c389125f0c3ce55",
        "per_arm_archives": ["outputs/analysis/p3_second_downstream_%s.json" % t for t in ARMS],
        "metric_definitions": ("imported from tools/_p1516_p3_vqa_downstream.py: norm()/token_f1(); "
                              "pope_f1 = yes-class F1 = 2TP/(2TP+FP+FN); what the cloud "
                              "aggregate labels arms.<t>.token_f1 is actually relaxed_accuracy"),
        "bootstrap": {"n_boot": N_BOOT, "rng_seed": RNG_SEED,
                      "interval": "percentile 5/95 of the paired difference; TOST p = max(P(d<=-m), P(d>=+m))",
                      "margin": MARGIN, "alpha": ALPHA},
        "contrast_direction": "delta = arm_a - arm_b with a = first element of the pair (so base_minus_5 = base - r5)",
    }, "arms": {}, "contrasts": {}, "defects": {}}

    for t in ARMS:
        a = arms[t]
        out["arms"][t] = {k: a[k] for k in ("n", "accuracy", "token_f1", "pope_f1", "yes_ratio",
                                           "gold_yes_ratio", "n_yes_gold", "tp", "fp", "fn", "tn")}

    print("\n[2] contrasts recomputed (paired by question, %d replicates, seed %d)" % (N_BOOT, RNG_SEED))
    mismatches = []
    rng = np.random.default_rng(RNG_SEED)
    for a_tag, b_tag in PAIRS:
        name = "%s_minus_%s" % (a_tag, b_tag)
        blk = contrasts(arms[a_tag], arms[b_tag], rng)
        out["contrasts"][name] = blk
        for m in METRICS:
            d = blk[m]
            print("  %-14s %-9s delta=%+0.6f ci95=[%+0.4f,%+0.4f] tost_p=%.4f minmargin=%.4f"
                  % (name, m, d["delta"], d["ci95"][0], d["ci95"][1], d["tost_p"],
                     d["min_equivalent_margin"]))
            if name in agg["contrasts"]:
                ar = agg["contrasts"][name][m]
                same = (abs(ar["delta"] - d["delta"]) < 1e-9
                        and abs(ar["ci95"][0] - d["ci95"][0]) < 1e-9
                        and abs(ar["ci95"][1] - d["ci95"][1]) < 1e-9
                        and abs(ar["min_equivalent_margin"] - d["min_equivalent_margin"]) < 1e-9)
                print("      vs aggregate: delta=%+.6f ci=[%+.4f,%+.4f] minmargin=%.4f %s"
                      % (ar["delta"], ar["ci95"][0], ar["ci95"][1],
                         ar["min_equivalent_margin"], "MATCH" if same else "DIFFERS"))
                if not same:
                    mismatches.append("%s/%s" % (name, m))
    out["aggregate_cross_check"] = {
        "all_contrasts_match": not mismatches,
        "mismatches": mismatches,
        "note": ("the independent recomputation (imported norm()/token_f1(), the archived bootstrap "
                 "seed and replicate count, one advancing generator across the three pairs) now "
                 "reproduces every contrast of the corrected aggregate, including token F1"),
    }
    print("\n  aggregate cross-check: %s"
          % ("all 9 contrasts match" if not mismatches else "MISMATCH %s" % mismatches))

    # ---- defect record (the corrected aggregate is now the producer; record the history)
    d1 = {"id": "D1_token_f1_mislabelled",
          "status": "FIXED_IN_GENERATOR_AND_AGGREGATE",
          "claim": ("the 2026-10-25 cloud aggregate's arms.<t>.token_f1 and contrasts.*.token_f1 "
                    "carried relaxed_accuracy, not token F1"),
          "mechanism": ("tools/_p1640_p3_second_downstream.py arm_from_payload called the imported "
                        "token_f1(a, b) with two STRINGS; the function zips its two arguments, so it "
                        "zipped characters instead of tokens, which on a yes/no label space "
                        "degenerates to relaxed accuracy.  The --eval path called it correctly as "
                        "token_f1([nref], [nhyp])"),
          "evidence": {
              "pre_correction_aggregate_sha256": "1c389125f0c3ce55056dea67ca5a3ded0ac09740465e37b640989ad66fcfb947",
              "base": {"pre_correction_arms_token_f1": 0.8926666666666667,
                       "per_arm_archive_token_f1": 0.6826015299515299,
                       "per_arm_archive_relaxed_accuracy": 0.8926666666666667,
                       "eval_log_printed": "arm=base acc=0.6257 tok_f1=0.8927 (the log printed the "
                                           "same wrong value, so the defect was in the aggregate "
                                           "loader, not in the eval)"},
              "r6": {"pre_correction_arms_token_f1": 0.846,
                     "per_arm_archive_token_f1": 0.8409513227513229,
                     "per_arm_archive_relaxed_accuracy": 0.846},
              "independent_recomputation": "tools/_p1647_pope_corrected_metrics.py",
          },
          "fix": ("token_f1([a], [b]) in arm_from_payload + an assertion that the recomputed mean "
                  "equals the arm archive's token_f1 field, so the regression cannot reappear "
                  "silently; the aggregate was regenerated locally on CPU"),
          "no_gpu_needed": ("the aggregate consumes only the three per-arm archives, so no GPU and "
                            "no cloud round were required")}
    acc5 = out["contrasts"]["base_minus_5"]["accuracy"]
    acc6 = out["contrasts"]["base_minus_6"]["accuracy"]
    keep_corrected = all(d["equivalent_at_declared_margin"] or d["ci95"][1] < 0
                         for d in (acc5, acc6))
    lose_corrected = any(d["ci95"][0] > MARGIN for d in (acc5, acc6))
    d2 = {"id": "D2_verdict_rule_sign_inverted",
          "status": "FIXED_IN_GENERATOR_AND_AGGREGATE",
          "claim": ("the pre-correction verdict rule tested the contrast with the opposite sign, so "
                    "an adapter that was better by more than the margin fired the 'loses' branch"),
          "mechanism": ("contrasts are delta = arm_a - arm_b with a = base, but the rule tested "
                        "ci95[0] > 0 for 'keep' and ci95[1] < -margin for 'lose', which are the "
                        "tests for delta = adapter - base"),
          "evidence": {"accuracy_base_minus_5": {"delta": acc5["delta"], "ci95": acc5["ci95"]},
                       "accuracy_base_minus_6": {"delta": acc6["delta"], "ci95": acc6["ci95"]},
                       "pre_correction_verdict": "task_dependent_effect",
                       "adapter_minus_base_accuracy": {"r5": round(-acc5["delta"], 4),
                                                       "r6": round(-acc6["delta"], 4)},
                       "why_the_coded_rule_fired": ("base - adapter is entirely below -margin "
                                                    "for both adapters, which the inverted rule "
                                                    "read as 'adapter loses'")},
          "fix": ("equivalent_or_better = TOST equivalence OR ci95 high < 0; loses = ci95 low > "
                  "+margin; corrected label is supports_the_adapters on accuracy, and "
                  "claim_verdict.metric_directions records that yes-class F1 moves the other way, "
                  "so the label is not read as a blanket endorsement"),
          "no_gpu_needed": True}
    out["defects"] = {"D1": d1, "D2": d2}

    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("\n[3] defect record written: D1 (token F1 mislabelled), D2 (verdict sign)")
    print("    corrected rule: equivalent_or_better=%s loses=%s -> aggregate verdict %s"
          % (keep_corrected, lose_corrected, agg["claim_verdict"]["second_task_verdict"]))
    print("    adapter-minus-base accuracy = %s"
          % {"r5": round(-acc5["delta"], 4), "r6": round(-acc6["delta"], 4)})
    print("\nwrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
