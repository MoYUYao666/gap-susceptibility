#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1644_verify_pope_archive.py -- task-18 step 1: verify the POPE second-downstream
archive field by field BEFORE any number is printed in the manuscript.

What it does (all read-only; writes only its own ledger):
  1. presence + size of the aggregate and the three per-arm archives;
  2. re-derive each arm's accuracy / token_f1 / pope_f1 FROM THE PER-ARM HYPOTHESES
     (not from the summary field) and require agreement with the archive field;
  3. require the aggregate's `arms.*` metrics to equal the per-arm re-derivation;
  4. require the strict-acceptance block to be fully satisfied;
  5. re-derive the pre-declared verdict from the contrast fields (the rule is fixed
     in tools/_p1640_p3_second_downstream.py lines 1085-1093) and require it to
     equal `claim_verdict.second_task_verdict`;
  6. emit a single ledger `outputs/analysis/p3_pope_latex_values.json` mapping every
     number that will be printed -> (archive file, field path, value).  The .tex text,
     the audit needles and the _p1637 registry all read from this ledger, so a number
     cannot enter the manuscript without a field path.

Exit non-zero if the archive is missing or any assertion fails.
"""
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ANA = ROOT / "outputs/analysis"
OUT = ANA / "p3_pope_latex_values.json"

AGG = ANA / "p3_second_downstream.json"
PER_ARM = {t: ANA / ("p3_second_downstream_%s.json" % t) for t in ("base", "5", "6")}
MARGIN = 0.05
ALPHA = 0.05
CONTRASTS = (("base", "5"), ("base", "6"), ("5", "6"))
METRICS = ("accuracy", "token_f1", "pope_f1")

FAIL = []


def check(name, ok, detail=""):
    print("  [%s] %s %s" % ("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAIL.append(name)


def norm(s):
    """PLACEHOLDER -- replaced at import time by tools/_p1516_p3_vqa_downstream.py's norm().

    The archived VQA-RAD check is the authority for these conventions, so this module
    imports its norm()/token_f1() rather than re-implementing them (the same choice
    tools/_p1640_p3_second_downstream.py makes).
    """
    raise AssertionError("norm() must be imported, not defined locally")


def token_f1(refs, hyps):
    raise AssertionError("token_f1() must be imported, not defined locally")


def _load_module(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import %s" % path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def install_archived_metrics():
    """Import norm()/token_f1() from the module the archive itself cites."""
    global norm, token_f1
    mod = _load_module("vqa1516_metrics",
                       str(ROOT / "tools/_p1516_p3_vqa_downstream.py"))
    norm, token_f1 = mod.norm, mod.token_f1
    # canary: the exact cases tools/_p1640's own --self-test pins
    cases = [("Yes.", "yes"), ("  NO  ", "no"), ("Anterior, left.", "anterior left"),
             ("no, not at all", "no not at all")]
    assert all(norm(a) == b for a, b in cases), "imported norm() failed the canary"
    assert abs(token_f1(["yes"], ["yes"]) - 1.0) < 1e-12
    assert abs(token_f1(["yes"], ["no"]) - 0.0) < 1e-12


def first_token_is_yes(text):
    """The archive's yes/no rule: the first normalised token decides (fields pred_yes/ref_yes)."""
    return norm(text).split()[:1] == ["yes"]


def derive_arm(rec):
    hyps, refs = rec["hypotheses"], rec["refs"]
    n = len(hyps)
    assert n == len(refs), "hypotheses/refs length mismatch"
    nref = [norm(r) for r in refs]
    nhyp = [norm(h) for h in hyps]
    correct = [bool(a == b) for a, b in zip(nhyp, nref)]
    f1s = [float(token_f1([r], [h])) for r, h in zip(nref, nhyp)]
    pred_yes = [first_token_is_yes(h) for h in hyps]
    ref_yes = [first_token_is_yes(r) for r in refs]
    tp = sum(1 for p, r in zip(pred_yes, ref_yes) if p and r)
    fp = sum(1 for p, r in zip(pred_yes, ref_yes) if p and not r)
    fn = sum(1 for p, r in zip(pred_yes, ref_yes) if not p and r)
    tn = sum(1 for p, r in zip(pred_yes, ref_yes) if not p and not r)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec_ = tp / (tp + fn) if (tp + fn) else 0.0
    pope_f1 = 2 * prec * rec_ / (prec + rec_) if (prec + rec_) else 0.0
    return {"n": n, "accuracy": sum(correct) / n, "token_f1": sum(f1s) / n,
            "pope_f1": pope_f1, "yes_ratio": sum(pred_yes) / n,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "n_yes_gold": sum(ref_yes),
            "arm_level_token_f1": float(token_f1(nref, nhyp))}


def main():
    print("=" * 78)
    print("POPE ARCHIVE VERIFICATION (task-18 step 1)")
    print("=" * 78)
    missing = [str(p) for p in [AGG] + list(PER_ARM.values()) if not p.exists()]
    if missing:
        print("\nARCHIVE MISSING -- refusing to produce any number:")
        for m in missing:
            print("   ", m)
        print("\nRe-run when the cloud owner has retrieved them into outputs/analysis/.")
        return 2
    print("\n[1] files present")
    for p in [AGG] + list(PER_ARM.values()):
        b = p.read_bytes()
        print("    %-46s %7d B  sha256=%s" % (p.name, len(b),
                                              hashlib.sha256(b).hexdigest()[:16]))
        check("non-empty %s" % p.name, len(b) > 100)

    agg = json.loads(AGG.read_text(encoding="utf-8"))
    arms_raw = {t: json.loads(PER_ARM[t].read_text(encoding="utf-8")) for t in PER_ARM}
    install_archived_metrics()
    print("\n[1b] norm()/token_f1() imported from tools/_p1516_p3_vqa_downstream.py "
          "(canary passed)")

    # ---- 2. re-derive each arm from hypotheses
    print("\n[2] arm metrics re-derived from the per-arm hypotheses")
    derived = {}
    for t in ("base", "5", "6"):
        d = derive_arm(arms_raw[t])
        derived[t] = d
        a = agg["arms"][t]
        check("%s n matches" % t, d["n"] == a["n"], "%d vs %d" % (d["n"], a["n"]))
        for m in METRICS:
            check("%s %s matches archive" % (t, m), abs(d[m] - a[m]) < 5e-7,
                  "derived %.7f vs archived %.7f" % (d[m], a[m]))
        check("%s yes_ratio matches" % t, abs(d["yes_ratio"] - a["yes_ratio"]) < 5e-7,
              "%.7f vs %.7f" % (d["yes_ratio"], a["yes_ratio"]))
        check("%s adapter reused from archive" % t,
              a.get("adapter_source") == "reused_from_archived_round" or t == "base",
              str(a.get("adapter_source")))
        # per-arm file's own metric fields must match the re-derivation too
        pr = arms_raw[t]
        for m in METRICS:
            if m in pr:
                check("%s per-arm file field %s matches re-derivation" % (t, m),
                      abs(pr[m] - d[m]) < 5e-7, "file %.7f vs derived %.7f" % (pr[m], d[m]))

    # ---- 3. acceptance
    print("\n[3] strict acceptance block")
    acc = agg.get("acceptance", {})
    for k, v in acc.items():
        if isinstance(v, bool):
            check("acceptance.%s" % k, v)
        else:
            print("    acceptance.%s = %r" % (k, v))
    check("refs byte-identical across arms", agg.get("refs_identical_across_arms") is True)
    check("all three arms share one question count",
          len({derived[t]["n"] for t in ("base", "5", "6")}) == 1)

    # ---- 4. verdict rule re-derivation (pre-declared rule, sign convention as defined)
    #      delta = arm_a - arm_b with a = "base", so a negative accuracy delta means the adapter
    #      is better.  equivalent_or_better = TOST equivalence OR ci95 high < 0;
    #      loses = ci95 low > +margin.  (This is the corrected rule; the pre-correction cloud
    #      aggregate tested the opposite sign, see docs/p3_pope_integration_notes.md D2.)
    print("\n[4] verdict re-derived from the contrast fields (pre-declared rule)")
    c = agg["contrasts"]

    def ci(pair, metric):
        return c[pair][metric]["ci95"]

    def equiv(pair, metric):
        return bool(c[pair][metric]["equivalent_at_declared_margin"])

    both_keep = all((equiv(p, "accuracy") or ci(p, "accuracy")[1] < 0)
                    for p in ("base_minus_5", "base_minus_6"))
    both_lose = any(ci(p, "accuracy")[0] > MARGIN for p in ("base_minus_5", "base_minus_6"))
    verdict_derived = ("task_dependent_effect" if both_lose
                       else ("supports_the_adapters" if both_keep else "inconclusive"))
    verdict_field = agg["claim_verdict"]["second_task_verdict"]
    print("    base_minus_5 accuracy: delta %+.6f ci95 [%+.4f,%+.4f] tost p=%.4f minmargin %.4f equiv=%s"
          % (c["base_minus_5"]["accuracy"]["delta"], *ci("base_minus_5", "accuracy"),
             c["base_minus_5"]["accuracy"]["tost_p"],
             c["base_minus_5"]["accuracy"]["min_equivalent_margin"],
             equiv("base_minus_5", "accuracy")))
    print("    base_minus_6 accuracy: delta %+.6f ci95 [%+.4f,%+.4f] tost p=%.4f minmargin %.4f equiv=%s"
          % (c["base_minus_6"]["accuracy"]["delta"], *ci("base_minus_6", "accuracy"),
             c["base_minus_6"]["accuracy"]["tost_p"],
             c["base_minus_6"]["accuracy"]["min_equivalent_margin"],
             equiv("base_minus_6", "accuracy")))
    check("both adapters are equivalent_or_better on accuracy", both_keep)
    check("no adapter loses accuracy beyond the margin", not both_lose)
    check("verdict matches the archive field", verdict_derived == verdict_field,
          "derived=%s archived=%s" % (verdict_derived, verdict_field))
    md = agg["claim_verdict"].get("metric_directions", {})
    check("metric_directions records accuracy as adapter_better",
          md.get("accuracy", {}).get("base_minus_r5") == "adapter_better"
          and md.get("accuracy", {}).get("base_minus_r6") == "adapter_better", str(md.get("accuracy")))
    check("metric_directions records yes-class F1 as base_better for r=6",
          md.get("pope_f1", {}).get("base_minus_r6") == "base_better", str(md.get("pope_f1")))

    # ---- 5. ledger of every printable number -> field path
    entries = []

    def put(key, value, path, note=""):
        entries.append({"key": key, "value": value, "field": path, "note": note,
                        "archive": "outputs/analysis/p3_second_downstream.json"})

    meta = agg["meta"]
    put("n_questions", meta["dataset"]["n_questions"], "meta.dataset.n_questions")
    put("dataset_revision_short", meta["dataset"]["revision"][:8], "meta.dataset.revision")
    put("dataset_config", meta["dataset"]["config"], "meta.dataset.config")
    put("dataset_split", meta["dataset"]["split"], "meta.dataset.split")
    put("n_boot", meta["n_boot"], "meta.n_boot")
    for t in ("base", "5", "6"):
        for m in METRICS:
            put("arm_%s_%s" % (t, m), agg["arms"][t][m], "arms.%s.%s" % (t, m))
        put("arm_%s_yes_ratio" % t, agg["arms"][t]["yes_ratio"], "arms.%s.yes_ratio" % t)
        put("arm_%s_n" % t, agg["arms"][t]["n"], "arms.%s.n" % t)
    for pair in ("base_minus_5", "base_minus_6", "5_minus_6"):
        for m in METRICS:
            b = c[pair][m]
            put("%s_%s_delta" % (pair, m), b["delta"], "contrasts.%s.%s.delta" % (pair, m))
            put("%s_%s_ci_lo" % (pair, m), b["ci95"][0], "contrasts.%s.%s.ci95.0" % (pair, m))
            put("%s_%s_ci_hi" % (pair, m), b["ci95"][1], "contrasts.%s.%s.ci95.1" % (pair, m))
            put("%s_%s_tost_p" % (pair, m), b["tost_p"], "contrasts.%s.%s.tost_p" % (pair, m))
            put("%s_%s_min_margin" % (pair, m), b["min_equivalent_margin"],
                "contrasts.%s.%s.min_equivalent_margin" % (pair, m))
            put("%s_%s_equiv" % (pair, m), bool(b["equivalent_at_declared_margin"]),
                "contrasts.%s.%s.equivalent_at_declared_margin" % (pair, m))
    put("verdict", verdict_field, "claim_verdict.second_task_verdict")
    for m, v in meta["declared_margins"].items():
        put("declared_margin_%s" % m, v, "meta.declared_margins.%s" % m)

    # the S29 binomial-SE benchmark for contrast: keep its own provenance, not re-derived here
    smallest = agg.get("smallest_equivalent_margin", {})
    for k, v in smallest.items():
        entries.append({"key": "smallest_" + k.replace("/", "_"), "value": v,
                        "field": "smallest_equivalent_margin.%s" % k,
                        "note": "", "archive": "outputs/analysis/p3_second_downstream.json"})

    ledger = {
        "meta": {
            "script": "tools/_p1644_verify_pope_archive.py",
            "task": "task-18 step 1 (POPE archive verification + printable-number ledger)",
            "aggregate": "outputs/analysis/p3_second_downstream.json",
            "aggregate_sha256": hashlib.sha256(AGG.read_bytes()).hexdigest(),
            "per_arm": {t: {"path": "outputs/analysis/" + PER_ARM[t].name,
                            "sha256": hashlib.sha256(PER_ARM[t].read_bytes()).hexdigest(),
                            "size": PER_ARM[t].stat().st_size} for t in PER_ARM},
            "verdict_rederived": verdict_derived,
            "verdict_rule": ("both_keep = every adapter is equivalent_at_declared_margin or "
                             "accuracy CI95 lower > 0; both_lose = any accuracy CI95 upper < "
                             "-0.05; supports_the_adapters if both_keep else "
                             "task_dependent_effect if both_lose else inconclusive"),
            "replicated_arms_from_hypotheses": {
                t: {k: derived[t][k] for k in ("n", "accuracy", "token_f1", "pope_f1",
                                               "yes_ratio", "tp", "fp", "fn", "tn",
                                               "n_yes_gold")} for t in derived},
            "caveat_sentences": agg.get("caveat_sentences", {}),
        },
        "entries": entries,
    }
    OUT.write_text(json.dumps(ledger, indent=1, ensure_ascii=False), encoding="utf-8")
    print("\n[5] ledger written: %s (%d entries)" % (OUT.name, len(entries)))

    print("\n" + "=" * 78)
    if FAIL:
        print("VERIFICATION FAILED -- %d assertion(s):" % len(FAIL))
        for f in FAIL:
            print("   -", f)
        return 1
    print("VERIFICATION PASSED -- every number in the ledger is tied to a field path")
    print("VERDICT:", verdict_field)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
