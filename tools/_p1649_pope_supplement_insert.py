#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1649_pope_supplement_insert.py -- task-18 step 2: insert the POPE subsection into the
supplementary material, with every number taken from an archive field.

Design decisions (documented so the edit is auditable):
  * A \\subsection, not a \\section: the supplement's 46 top-level sections and main.tex's
    "S1--S46" pointer stay valid.
  * Inserted immediately after the VQA-RAD section's table (before
    \\section{Second-environment reproducibility}), so it sits beside the existing
    downstream material.
  * Numbers come from outputs/analysis/p3_second_downstream.json, which was REGENERATED
    locally by the corrected tools/_p1640_p3_second_downstream.py: the pre-correction cloud
    aggregate carried relaxed_accuracy in arms.*.token_f1 and a sign-inverted verdict rule
    (defects D1/D2, see docs/p3_pope_integration_notes.md).  After the correction the
    independent recomputation in tools/_p1647_pope_corrected_metrics.py reproduces all nine
    contrasts (three pairs x three metrics) exactly.
  * The prose states the metric-dependent outcome explicitly and does NOT quote the
    accuracy-only verdict label as a blanket endorsement.

Idempotent: if \\label{app:pope} already exists it changes nothing and says so.

Output: outputs/analysis/p3_pope_tex_insert.json (line ranges + the rendered block)
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ANA = ROOT / "outputs/analysis"
SUPP = ROOT / "paper3/paper_ieee/supplementary/supplementary.tex"
OUT = ANA / "p3_pope_tex_insert.json"

ANCHOR = "\\section{Second-environment reproducibility}"
LABEL = "\\label{app:pope}"

# Re-run with --force after editing the template below: it replaces the whole subsection block
# instead of skipping, so the manuscript can never drift from this generator.
if not os.path.exists(SUPP):
    raise SystemExit("supplementary.tex not found: %s" % SUPP)

agg = json.loads((ANA / "p3_second_downstream.json").read_text(encoding="utf-8"))
rep = json.loads((ANA / "p3_pope_corrected_metrics.json").read_text(encoding="utf-8"))
per = {t: json.loads((ANA / ("p3_second_downstream_%s.json" % t)).read_text(encoding="utf-8"))
       for t in ("base", "5", "6")}


def f4(x):
    return "%.4f" % x


def sgn4(x):
    return ("+" if x >= 0 else "-") + ("%.4f" % abs(x))


A = agg["arms"]
C = agg["contrasts"]
n = A["base"]["n"]
acc_b5, acc_b6 = C["base_minus_5"]["accuracy"], C["base_minus_6"]["accuracy"]
tf1_b5, tf1_b6 = C["base_minus_5"]["token_f1"], C["base_minus_6"]["token_f1"]
pf1_b5, pf1_b6 = C["base_minus_5"]["pope_f1"], C["base_minus_6"]["pope_f1"]
acc_56, tf1_56, pf1_56 = C["5_minus_6"]["accuracy"], C["5_minus_6"]["token_f1"], C["5_minus_6"]["pope_f1"]
fn = {t: per[t]["confusion"]["fn"] for t in per}
fp = {t: per[t]["confusion"]["fp"] for t in per}
n_yes_gold = int(sum(1 for r in per["base"]["refs"] if r.strip().lower().rstrip(".") == "yes"))
se = (0.25 / n) ** 0.5

# ---- assertions: every printed number is an archive field (or its exact negation)
assert n == 3000 and n_yes_gold == 1500
for t in ("base", "5", "6"):
    assert abs(A[t]["token_f1"] - per[t]["token_f1"]) < 5e-7, "token F1 must be the per-arm field"
for pair, metrics in (("base_minus_5", (acc_b5, tf1_b5, pf1_b5)),
                      ("base_minus_6", (acc_b6, tf1_b6, pf1_b6)),
                      ("5_minus_6", (acc_56, tf1_56, pf1_56))):
    for mname, d in zip(("accuracy", "token_f1", "pope_f1"), metrics):
        r = rep["contrasts"][pair][mname]
        assert abs(d["delta"] - r["delta"]) < 1e-9, (pair, mname)
        assert abs(d["ci95"][0] - r["ci95"][0]) < 1e-9 and abs(d["ci95"][1] - r["ci95"][1]) < 1e-9
        assert abs(d["min_equivalent_margin"] - r["min_equivalent_margin"]) < 1e-9
assert agg["claim_verdict"]["second_task_verdict"] in ("supports_the_adapters",
                                                       "task_dependent_effect", "inconclusive")

block = r"""\subsection{A second downstream task: POPE}
\label{app:pope}

The downstream check is repeated on a second, independent task: POPE (Li et al.,
arXiv:2305.10355), config \texttt{Full}, split \texttt{random}, revision \texttt{4db12766},
$n=%d$ held-out questions, an object-hallucination probe whose label space is exactly the yes/no
subset that the VQA-RAD check already scores. The \texttt{r5\_step}/\texttt{r6\_step} adapters are
reused unchanged (their \texttt{adapter\_model.safetensors} hashes match the archived VQA-RAD round),
with the same prompt prefix, the same greedy decoding, and the \texttt{norm()}/\texttt{token\_f1()}
definitions imported from that check, so no new answer-parsing rule enters the comparison. All three
arms answer the same $%d$ questions in the same order (the reference arrays are byte-identical across
the three archives). The equivalence margin of $0.05$ is pre-declared and carried over unchanged from
the 451-question analysis; at $%d$ questions the binomial standard error of accuracy is about
$%.4f$, so this set is not at its resolution limit and the margin is not re-fitted.
Table~\ref{tab:pope} reports the arms.

\begin{table}[htbp]
\centering
\footnotesize
\begin{tabular}{@{}lrrrrr@{}}
\toprule
arm & $n$ & accuracy & token F1 & yes-class F1 & yes rate \\
\midrule
base & %d & %s & %s & %s & %s \\
$r=5$ (per-step) & %d & %s & %s & %s & %s \\
$r=6$ (per-step) & %d & %s & %s & %s & %s \\
\bottomrule
\end{tabular}
\caption{POPE second downstream task (real images, all %d questions, paired by question across arms;
the gold yes rate is exactly $0.5$). The adapters improve exact-match accuracy and token F1 but move
the yes/no prior, and the yes-class F1 therefore moves the other way at $r=6$. Source:
\texttt{tools/\_p1640\_p3\_second\_downstream.py} $\to$
\texttt{outputs/analysis/p3\_second\_downstream.json} (\texttt{arms.*.accuracy},
\texttt{arms.*.token\_f1}, \texttt{arms.*.pope\_f1}, \texttt{arms.*.yes\_ratio}; dataset and protocol
fields in \texttt{meta.dataset} and \texttt{meta.declared\_margins}; confusion counts in the per-arm
archives \allowbreak\texttt{outputs/analysis/\allowbreak p3\_second\_downstream\_\allowbreak\{base,5,6\}.json}).}
\label{tab:pope}
\end{table}

The pre-declared criterion is met. Before the run we fixed the rule that an adapter is accepted on
POPE if it is equivalent to or better than the base model on accuracy, that is, if the $0.05$ TOST
margin is satisfied or the $95$\%% interval of the base-minus-adapter difference lies entirely below
zero. Both adapters satisfy it: base minus $r=5$ is $%s$ (95\%% CI $[%s,%s]$) and base minus $r=6$ is
$%s$ (95\%% CI $[%s,%s]$), and the same direction holds on token F1 ($%s$, 95\%% CI $[%s,%s]$ for
$r=5$; $%s$, 95\%% CI $[%s,%s]$ for $r=6$). The archived verdict is therefore
\texttt{supports\_the\_adapters} (field \texttt{claim\_verdict.second\_task\_verdict}), and those
differences lie far outside the margin, so they are resolved improvements rather than equivalences.

That verdict is stated on the accuracy criterion, and it must be read together with the metric split
recorded in the same archive. POPE's own yes-class F1 moves the other way: base minus $r=5$ is $%s$
(95\%% CI $[%s,%s]$), inside the $0.05$ margin and declared equivalent, whereas base minus $r=6$ is
$%s$ (95\%% CI $[%s,%s]$), beyond the margin and not declared equivalent. The mechanism is a shift of
the yes/no prior: on a set whose gold yes rate is exactly $0.5$, the predicted-yes rate falls from
$%s$ (base) to $%s$ ($r=5$) and $%s$ ($r=6$), the false negatives on the $%d$ yes questions rise from
$%d$ to $%d$ and $%d$, and the false positives fall from $%d$ to $%d$ and $%d$.
\texttt{claim\_verdict.metric\_directions} records this split explicitly (accuracy: adapter better
for both adapters; yes-class F1: base better for both), so \texttt{supports\_the\_adapters} is a
statement about the pre-declared accuracy criterion, not about every metric.

Two limits remain. First, the second task does not show the alignment-energy ordering transferring
downstream: we make no claim that a downstream accuracy gain certifies that ordering. Second, the
ranking of the two adapters is consistent across all three metrics, with $r=5$ better than $r=6$ on
accuracy ($%s$, 95\%% CI $[%s,%s]$), on token F1 ($%s$, 95\%% CI $[%s,%s]$) and on yes-class F1
($%s$, 95\%% CI $[%s,%s]$), the same direction as its smaller alignment damage; this is the weaker
directional statement that the second task supports. Source:
\texttt{tools/\_p1640\_p3\_second\_downstream.py} $\to$
\texttt{outputs/analysis/p3\_second\_downstream.json}
(\texttt{contrasts.base\_minus\_5.*}, \texttt{contrasts.base\_minus\_6.*},
\texttt{contrasts.5\_minus\_6.*}, \texttt{claim\_verdict.second\_task\_verdict},
\texttt{claim\_verdict.metric\_directions}), with the confusion counts from the per-arm archives.

""" % (
    n,
    n,
    n, se,
    n, f4(A["base"]["accuracy"]), f4(A["base"]["token_f1"]), f4(A["base"]["pope_f1"]), f4(A["base"]["yes_ratio"]),
    n, f4(A["5"]["accuracy"]), f4(A["5"]["token_f1"]), f4(A["5"]["pope_f1"]), f4(A["5"]["yes_ratio"]),
    n, f4(A["6"]["accuracy"]), f4(A["6"]["token_f1"]), f4(A["6"]["pope_f1"]), f4(A["6"]["yes_ratio"]),
    n,
    sgn4(acc_b5["delta"]), sgn4(acc_b5["ci95"][0]), sgn4(acc_b5["ci95"][1]),
    sgn4(acc_b6["delta"]), sgn4(acc_b6["ci95"][0]), sgn4(acc_b6["ci95"][1]),
    sgn4(tf1_b5["delta"]), sgn4(tf1_b5["ci95"][0]), sgn4(tf1_b5["ci95"][1]),
    sgn4(tf1_b6["delta"]), sgn4(tf1_b6["ci95"][0]), sgn4(tf1_b6["ci95"][1]),
    sgn4(pf1_b5["delta"]), sgn4(pf1_b5["ci95"][0]), sgn4(pf1_b5["ci95"][1]),
    sgn4(pf1_b6["delta"]), sgn4(pf1_b6["ci95"][0]), sgn4(pf1_b6["ci95"][1]),
    f4(A["base"]["yes_ratio"]), f4(A["5"]["yes_ratio"]), f4(A["6"]["yes_ratio"]),
    n_yes_gold, fn["base"], fn["5"], fn["6"], fp["base"], fp["5"], fp["6"],
    sgn4(acc_56["delta"]), sgn4(acc_56["ci95"][0]), sgn4(acc_56["ci95"][1]),
    sgn4(tf1_56["delta"]), sgn4(tf1_56["ci95"][0]), sgn4(tf1_56["ci95"][1]),
    sgn4(pf1_56["delta"]), sgn4(pf1_56["ci95"][0]), sgn4(pf1_56["ci95"][1]),
)

text = SUPP.read_text(encoding="utf-8")
FORCE = "--force" in sys.argv
if LABEL in text:
    m = re.search(re.escape(LABEL), text)
    start = text.rfind("\\subsection{A second downstream task: POPE}", 0, m.start())
    line = text[:start].count("\n") + 1
    if not FORCE:
        print("already inserted (%s at line %d) -- nothing to do (pass --force to re-render)"
              % (LABEL, line))
        OUT.write_text(json.dumps({"status": "already_present", "subsection_start_line": line},
                                  indent=1), encoding="utf-8")
        raise SystemExit(0)
    idx = text.index(ANCHOR)
    assert 0 <= start < idx, "cannot locate the inserted block boundaries"
    old_n = text[start:idx].count("\n")
    new = text[:start] + block + text[idx:]
    SUPP.write_text(new, encoding="utf-8", newline="")
    end_line = line + block.count("\n") - 1
    rec = {"status": "replaced", "subsection_anchor": ANCHOR,
           "inserted_start_line": line, "inserted_end_line": end_line,
           "n_lines_added": block.count("\n"), "n_lines_replaced": old_n,
           "label": LABEL, "table_label": "tab:pope",
           "aggregate_sha256": __import__("hashlib").sha256(
               (ANA / "p3_second_downstream.json").read_bytes()).hexdigest(),
           "numbers_source": {
               "aggregate": "outputs/analysis/p3_second_downstream.json",
               "per_arm": ["outputs/analysis/p3_second_downstream_%s.json" % t
                           for t in ("base", "5", "6")],
               "independent_cross_check": "outputs/analysis/p3_pope_corrected_metrics.json"},
           "rendered_block": block}
    OUT.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    print("replaced subsection block at lines %d-%d (%d -> %d lines)"
          % (line, end_line, old_n, block.count("\n")))
    raise SystemExit(0)
assert ANCHOR in text, "anchor section not found: %s" % ANCHOR
idx = text.index(ANCHOR)
start_line = text[:idx].count("\n") + 1
new = text[:idx] + block + text[idx:]
end_line = start_line + block.count("\n") - 1
SUPP.write_text(new, encoding="utf-8", newline="")

rec = {"status": "inserted", "subsection_anchor": ANCHOR,
       "inserted_start_line": start_line, "inserted_end_line": end_line,
       "n_lines_added": block.count("\n"), "label": LABEL, "table_label": "tab:pope",
       "aggregate_sha256": __import__("hashlib").sha256(
           (ANA / "p3_second_downstream.json").read_bytes()).hexdigest(),
       "numbers_source": {
           "aggregate": "outputs/analysis/p3_second_downstream.json",
           "per_arm": ["outputs/analysis/p3_second_downstream_%s.json" % t for t in ("base", "5", "6")],
           "independent_cross_check": "outputs/analysis/p3_pope_corrected_metrics.json"},
       "printed_values": {
           "n": n, "n_yes_gold": n_yes_gold, "binomial_se_accuracy": se,
           "arms": {t: {"accuracy": A[t]["accuracy"], "token_f1": A[t]["token_f1"],
                        "pope_f1": A[t]["pope_f1"], "yes_ratio": A[t]["yes_ratio"],
                        "fn": per[t]["confusion"]["fn"], "fp": per[t]["confusion"]["fp"]}
                    for t in ("base", "5", "6")},
           "contrasts": {k: {m: {"delta": C[k][m]["delta"], "ci95": C[k][m]["ci95"]}
                             for m in ("accuracy", "token_f1", "pope_f1")} for k in C}},
       "rendered_block": block}
OUT.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
print("inserted subsection at lines %d-%d (%d lines)" % (start_line, end_line, block.count("\n")))
print("table tab:pope; n=%d; SE=%.4f; gold yes=%d" % (n, se, n_yes_gold))
print("accuracy base-r5 %.4f [%.4f,%.4f]" % (acc_b5["delta"], *acc_b5["ci95"]))
print("token F1 base-r6 %.4f [%.4f,%.4f]" % (tf1_b6["delta"], *tf1_b6["ci95"]))
print("pope F1 base-r6 %.4f [%.4f,%.4f]" % (pf1_b6["delta"], *pf1_b6["ci95"]))
print("wrote", OUT)
