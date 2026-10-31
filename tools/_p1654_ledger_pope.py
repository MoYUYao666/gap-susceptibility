#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1654_ledger_pope.py -- register every POPE number printed in the supplement in
tools/_p1637_p3_reproduce_all.py, so the ledger re-derives it from the archive field.

Idempotent: if the S29b marker is present it makes no change.
"""
import io
import os
import sys
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEDGER = ROOT / "tools/_p1637_p3_reproduce_all.py"
MARKER = "# --- S29b: POPE second downstream task"
ANCHOR = "# --- S29: second-environment reproducibility"

BLOCK = r'''# --- S29b: POPE second downstream task (S29 subsection, 2026-10-25) -------------------
# Every value is a field of outputs/analysis/p3_second_downstream.json, regenerated locally by
# the corrected tools/_p1640_p3_second_downstream.py (defects D1/D2 fixed; see
# docs/p3_pope_integration_notes.md).  The pre-correction cloud aggregate
# (sha256 1c389125f0c3ce55...) carried relaxed_accuracy in arms.*.token_f1 and a sign-inverted
# verdict rule, and is superseded: outputs/analysis/p3_second_downstream_pre_correction.json.
_POPE = ANA + "/p3_second_downstream.json"
_POPE_ARM = ANA + "/p3_second_downstream_%s.json"
add("s29b-n", "S29", "supplementary.tex Table tab:pope n (all three arms)",
    "%d" % dig(_load(_POPE), "meta.dataset.n_questions"), _POPE, "meta.dataset.n_questions",
    "archived POPE evaluation size", float(dig(_load(_POPE), "meta.dataset.n_questions")),
    tol=T_ABS)
for _arm in ("base", "5", "6"):
    for _metric in ("accuracy", "token_f1", "pope_f1", "yes_ratio"):
        add("s29b-%s-%s" % (_arm, _metric), "S29",
            "supplementary.tex Table tab:pope arm %s %s" % (_arm, _metric),
            "%.4f" % dig(_load(_POPE), "arms.%s.%s" % (_arm, _metric)),
            _POPE, "arms.%s.%s" % (_arm, _metric),
            "archived POPE arm metric",
            dig(_load(_POPE), "arms.%s.%s" % (_arm, _metric)), tol=T_R4)
for _pair in ("base_minus_5", "base_minus_6", "5_minus_6"):
    for _metric in ("accuracy", "token_f1", "pope_f1"):
        add("s29b-%s-%s-delta" % (_pair, _metric), "S29",
            "supplementary.tex: POPE contrast %s %s delta" % (_pair, _metric),
            "%+.4f" % dig(_load(_POPE), "contrasts.%s.%s.delta" % (_pair, _metric)),
            _POPE, "contrasts.%s.%s.delta" % (_pair, _metric),
            "archived paired-bootstrap delta",
            dig(_load(_POPE), "contrasts.%s.%s.delta" % (_pair, _metric)), tol=T_R4)
        add("s29b-%s-%s-ci-lo" % (_pair, _metric), "S29",
            "supplementary.tex: POPE contrast %s %s 95%% CI lower" % (_pair, _metric),
            "%+.4f" % dig(_load(_POPE), "contrasts.%s.%s.ci95.0" % (_pair, _metric)),
            _POPE, "contrasts.%s.%s.ci95.0" % (_pair, _metric),
            "archived 2.5th bootstrap percentile",
            dig(_load(_POPE), "contrasts.%s.%s.ci95.0" % (_pair, _metric)), tol=T_R4)
        add("s29b-%s-%s-ci-hi" % (_pair, _metric), "S29",
            "supplementary.tex: POPE contrast %s %s 95%% CI upper" % (_pair, _metric),
            "%+.4f" % dig(_load(_POPE), "contrasts.%s.%s.ci95.1" % (_pair, _metric)),
            _POPE, "contrasts.%s.%s.ci95.1" % (_pair, _metric),
            "archived 97.5th bootstrap percentile",
            dig(_load(_POPE), "contrasts.%s.%s.ci95.1" % (_pair, _metric)), tol=T_R4)
add("s29b-verdict", "S29", "supplementary.tex: POPE boundary is metric-dependent",
    dig(_load(_POPE), "claim_verdict.second_task_verdict"), _POPE,
    "claim_verdict.second_task_verdict",
    "accuracy-only pre-declared label; the prose states the metric-dependent boundary",
    dig(_load(_POPE), "claim_verdict.second_task_verdict"), tol=0.0)
for _metric in ("accuracy", "pope_f1"):
    for _pair in ("base_minus_r5", "base_minus_r6"):
        add("s29b-dir-%s-%s" % (_metric, _pair), "S29",
            "supplementary.tex: POPE metric direction %s %s" % (_metric, _pair),
            dig(_load(_POPE), "claim_verdict.metric_directions.%s.%s" % (_metric, _pair)),
            _POPE, "claim_verdict.metric_directions.%s.%s" % (_metric, _pair),
            "archived metric direction",
            dig(_load(_POPE), "claim_verdict.metric_directions.%s.%s" % (_metric, _pair)),
            tol=0.0)
for _arm in ("base", "5", "6"):
    add("s29b-fn-%s" % _arm, "S29",
        "supplementary.tex: POPE false negatives on yes questions, arm %s" % _arm,
        "%d" % dig(_load(_POPE_ARM % _arm), "confusion.fn"),
        _POPE_ARM % _arm, "confusion.fn",
        "archived false negatives (gold yes, predicted no)",
        float(dig(_load(_POPE_ARM % _arm), "confusion.fn")), tol=T_ABS)
    add("s29b-fp-%s" % _arm, "S29",
        "supplementary.tex: POPE false positives on no questions, arm %s" % _arm,
        "%d" % dig(_load(_POPE_ARM % _arm), "confusion.fp"),
        _POPE_ARM % _arm, "confusion.fp",
        "archived false positives (gold no, predicted yes)",
        float(dig(_load(_POPE_ARM % _arm), "confusion.fp")), tol=T_ABS)
calc("s29b-yes-gold", "S29",
     "supplementary.tex: POPE 'the gold yes rate is exactly 0.5' -> 1500 of 3000 yes questions",
     "1500", _POPE_ARM % "base", "refs (count of 'yes')",
     "counted from the reference answers",
     1500.0,
     lambda: float(sum(1 for r in _load(_POPE_ARM % "base")["refs"]
                       if r.strip().lower().rstrip(".") == "yes")), tol=T_ABS)
calc("s29b-binomial-se", "S29",
     "supplementary.tex: POPE 'binomial standard error of accuracy is about 0.0091'",
     "0.0091", _POPE, "meta.dataset.n_questions",
     "sqrt(0.25/n) with n = the archived question count", 0.0091,
     lambda: (0.25 / float(dig(_load(_POPE), "meta.dataset.n_questions"))) ** 0.5, tol=T_R4)

'''


def main():
    text = io.open(LEDGER, encoding="utf-8").read()
    if MARKER in text:
        print("S29b block already present -- nothing to do")
        return 0
    assert ANCHOR in text, "anchor not found"
    idx = text.index(ANCHOR)
    line = text[:idx].count("\n") + 1
    new = text[:idx] + BLOCK + text[idx:]
    io.open(LEDGER, "w", encoding="utf-8", newline="").write(new)
    print("inserted S29b ledger block at line %d (%d lines)" % (line, BLOCK.count("\n")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
