#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1660_official_igu_integration.py -- task-22: write the official-implementation comparison
into the Paper 3 supplement section `app:iguofficial`.

Idempotent. Renders the block from the archives with assertions, so the manuscript cannot drift
from `outputs/analysis/p3_official_vs_reimpl.json` /
`outputs/analysis/p3_official_igu_replicates.json`. Re-run with --force after editing this
template.

The added material is a new `\\subsection` inside the existing S41 section (so the supplement's
section count stays 46 and main.tex's S1--S46 pointer is untouched) plus one compact table.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ANA = ROOT / "outputs/analysis"
SUPP = ROOT / "paper3/paper_ieee/supplementary/supplementary.tex"
OUT = ANA / "p3_iguofficial_insert.json"

SEC_START = "\\section{Official IGU allocation stage}"
SEC_NEXT = "\\section{Instruction-family replication on Dolly-15k}"
MARKER = "\\subsection{Official implementation versus the block-level rule}"


def load(name):
    p = ANA / name
    return p, json.loads(p.read_text(encoding="utf-8"))


def sha16(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


cmp_p, CMP = load("p3_official_vs_reimpl.json")
rep_p, REP = load("p3_official_igu_replicates.json")
run_p, RUN = load("p3_official_igu_run.json")

OV = CMP["overall"]
TAD = CMP["per_configuration"]["trained_arm_delta_E"]
SENS = CMP["allocation_sensitivity_to_the_block_mapping"]
REPS = REP["summary"]
PAIRS = CMP["pairs"]

# ---- assertions: every printed value is taken from a field, and cross-checked
assert OV["mean_gap_delta_E"] == -59.5, OV["mean_gap_delta_E"]
assert OV["ci95"] == [-150.5, -8.0], OV["ci95"]
assert OV["margin"] == 196.05 and OV["margin_fraction_of_E0"] == 0.05
assert OV["allocation_l1"] == 2 and OV["allocation_within_tolerance"] is True
assert OV["verdict"] == "small" and OV["arm_verdict"] == "equivalent"
assert TAD["tost_p"] == 0.0 and TAD["equivalent_at_declared_margin"] is True
assert TAD["min_equivalent_margin"] == 107.0
assert CMP["n_pairs"] == 3 and CMP["seeds_common"] == [42, 123, 789]
assert CMP["same_stack_for_every_pair"] is True and CMP["stack_mix_warning"] is None
assert SENS["archived"]["l1"] == 2 and SENS["corrected"]["l1"] == 2
assert len(RUN["runs"]) == 6
assert REPS["n_arms"] == 6 and REPS["n_replicate_passes"] == 2
assert REPS["max_spread_across_arms"] == 132.0
assert abs(REPS["mean_spread_across_arms"] - 76.08333333333333) < 1e-9
assert abs(REPS["archived_official_minus_reimpl_gap"] - 92.5) < 1e-9
assert REP["pinned_anchors_sha256_before"] == REP["pinned_anchors_sha256_after"]
assert CMP["meta"]["margin"] == 196.05 and CMP["meta"]["allocation_l1_tolerance"] == 2
assert OV["official_config"] == "official_corrected_map"
E0 = PAIRS[0]["reimpl"]["E"][0]
assert round(OV["margin"] / OV["margin_fraction_of_E0"], 2) == E0 == 3921.0
ENV = PAIRS[0]["official"]["env"]
assert ENV["torch"] == "2.12.1+cu130" and "RTX 4080" in ENV["gpu"]

off_alloc = CMP["official_side"]["allocation"]
rei_alloc = CMP["reimpl_side"]["allocation"]


def f4(x):
    return "%+.4f" % x if abs(x) < 1 else "%+.1f" % x


def sgn(x):
    return ("+" if x >= 0 else "-") + ("%.1f" % abs(x))


BLOCK = r"""\subsection{Official implementation versus the block-level rule}
\label{app:igucompare}

To report the allocation-rule baseline from the official implementation rather than from a block-level
reimplementation, the two allocators are compared at matched budget. Both are trained under the identical
blank-image protocol (20 samples, 3 epochs, learning rate $5\times10^{-5}$, batch 1, base rank 1,
$\alpha=16$) at seeds 42, 123 and 789, giving six trained arms (\texttt{runs[]} = 6). Under the corrected
mapping the official allocator assigns $%d/%d/%d/%d$ ranks to the four blocks and our block-level
integrated-gradient rule assigns $%d/%d/%d/%d$; the block-level $L_1$ distance is $%d$ of 16, inside the
archived tolerance of $%d$, and it is also $%d$ under the archived mapping ($12/1/2/1$ against
$11/1/3/1$), so the comparison does not depend on which mapping convention is used.

Paired by seed, the official-minus-block-level gap in $\Delta E$ is $%s$ (95\%% percentile bootstrap CI
$[%s,%s]$ over 20{,}000 resamples, RNG seed 20261024). The pre-declared margin is
$196.05 = 5\%%$ of $E(0) = 3921.0$; both one-sided TOST tests pass at that margin (archived
\texttt{tost\_p} $= 0.0$, i.e.\ no resample reaches the margin; the smallest equivalent margin is
$%s$), and the arm verdict is \texttt{equivalent}. With the allocation $L_1$ inside tolerance, the
pre-declared rule returns the overall verdict \texttt{small}: the allocation-rule baseline is reported
from the official implementation. All three pairs were trained on one software and hardware stack
(torch 2.12.1+cu130, CUDA 13.0, NVIDIA RTX 4080 SUPER; \texttt{same\_stack\_for\_every\_pair} $=$
\texttt{true}, \texttt{stack\_mix\_warning} $=$ \texttt{null}), so the paired contrast is not confounded
by a stack change.

The gap must be read against run-to-run dispersion, not as a point estimate. Each of the six arms was
re-run twice with identical arguments and cache defeat (\texttt{--force}), and $\Delta E$ varies by up to
$132.0$ across the three runs of an arm (mean range $76.1$). That dispersion is the same order as the
corrected gap being judged ($59.5$) and as the gap under the archived mapping ($92.5$), so at these seeds
the two allocation rules differ by less than the run-to-run noise; we therefore frame the comparison by
the pre-declared margin and the $L_1$ distance, and we do not report a single-seed gap as a reproducible
reading. The primaries and the two pinned anchors are byte-identical before and after the replicate
passes (\texttt{pinned\_anchors\_sha256\_before} $=$ \texttt{pinned\_anchors\_sha256\_after}).

\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lr@{}}
\toprule
quantity & value \\
\midrule
paired gap, official $-$ block-level (95\%% CI) & $-59.5$ $[-150.5,-8.0]$ \\
pre-declared margin, $5\%%$ of $E(0)=3921.0$ & $196.05$ \\
TOST at that margin (archived one-sided $p$) & $0.0$ ($=$ no resample reaches the margin) \\
smallest equivalent margin & $107.0$ \\
block-level $L_1$ (corrected / archived mapping) & $2/16$ / $2/16$ (tolerance 2) \\
replicate range of per-arm $\Delta E$ & $\le 132.0$ (mean $76.1$) \\
verdict from the pre-declared rule & \texttt{small} \\
\bottomrule
\end{tabular}
\caption{Official IGU-LoRA allocator against the block-level integrated-gradient rule, trained under
the identical protocol at seeds 42, 123 and 789. The paired difference is inside the pre-declared
$5\%%$ margin and the block-level allocation distance is inside tolerance, so the verdict is
\texttt{small} and the allocation baseline is reported from the official implementation; per-arm
run-to-run dispersion of $\Delta E$ is the same order, so the comparison is framed by the margin and
the $L_1$ distance rather than by a single-seed point estimate. Source:
\texttt{tools/\_p1639\_p3\_official\_igu.py --compare} $\to$
\texttt{outputs/analysis/p3\_official\_igu\_run.json} (\texttt{runs[]}, 6 arms; fields
\texttt{config}, \texttt{seed}, \texttt{delta\_E}) and
\texttt{outputs/analysis/p3\_official\_vs\_reimpl.json} (sha256 \texttt{4698a6e7...}; fields
\texttt{overall.mean\_gap\_delta\_E}, \texttt{overall.ci95}, \texttt{overall.margin},
\texttt{meta.margin\_fraction\_of\_E0}, \texttt{pairs[].gap},
\texttt{per\_configuration.trained\_arm\_delta\_E.\allowbreak\{tost\_p,\allowbreak min\_equivalent\_margin\}},
\texttt{per\_configuration.allocation.l1},
\texttt{allocation\_sensitivity\_to\_the\_block\_mapping.\allowbreak\{archived,\allowbreak corrected\}.l1},
\texttt{same\_stack\_for\_every\_pair}, \texttt{stack\_mix\_warning},
\texttt{pairs[].official.env}); replicate dispersion from
\texttt{tools/\_p1646\_p3\_arm\_replicates.py} $\to$
\texttt{outputs/analysis/p3\_official\_igu\_replicates.json} (fields
\texttt{summary.max\_spread\_across\_arms}, \texttt{summary.mean\_spread\_across\_arms},
\texttt{summary.archived\_official\_minus\_reimpl\_gap},
\texttt{pinned\_anchors\_sha256\_before}, \texttt{pinned\_anchors\_sha256\_after}).}
\label{tab:igucompare}
\end{table*}

""" % (off_alloc["vision"], off_alloc["text_shallow"], off_alloc["text_mid"], off_alloc["text_deep"],
       rei_alloc["vision"], rei_alloc["text_shallow"], rei_alloc["text_mid"], rei_alloc["text_deep"],
       OV["allocation_l1"], CMP["meta"]["allocation_l1_tolerance"], SENS["archived"]["l1"],
       sgn(OV["mean_gap_delta_E"]), sgn(OV["ci95"][0]), sgn(OV["ci95"][1]),
       "%.1f" % TAD["min_equivalent_margin"])

text = SUPP.read_text(encoding="utf-8")
assert SEC_START in text, "S41 section not found"
if MARKER in text and "--force" not in sys.argv:
    i = text.find(MARKER)
    print("already integrated (marker at line %d) -- nothing to do (pass --force to re-render)"
          % (text[:i].count("\n") + 1))
    OUT.write_text(json.dumps({"status": "already_present",
                               "marker_line": text[:i].count("\n") + 1}, indent=1),
                   encoding="utf-8")
    raise SystemExit(0)

start = text.find(SEC_START)
end = text.find(SEC_NEXT)
assert 0 <= start < end, "cannot locate the S41 span"
# The section keeps its existing porting paragraph and allocation-stage table; the comparison block
# goes after that table (end of the section) so the two tables keep their narrative order.
old = text[start:end]
if MARKER in old:
    old = old[:old.find(MARKER)]
anchor_table_end = old.find("\\label{tab:iguofficial}")
assert anchor_table_end > 0, "allocation-stage table not found inside the section"
cut = old.find("\\end{table*}", anchor_table_end)
assert cut > 0, "cannot locate the end of the allocation-stage table"
head = old[:cut + len("\\end{table*}")] + "\n\n"
new = text[:start] + head + BLOCK + text[end:]
SUPP.write_text(new, encoding="utf-8", newline="")

rec = {
    "status": "integrated" if MARKER not in old else "replaced",
    "section": "app:iguofficial (S41)",
    "inserted_start_line": new[:start + len(head)].count("\n") + 1,
    "inserted_lines": BLOCK.count("\n"),
    "subsection_label": "app:igucompare",
    "table_label": "tab:igucompare",
    "archives": {
        "comparison": {"path": "outputs/analysis/p3_official_vs_reimpl.json",
                       "sha256_prefix": sha16(cmp_p)},
        "replicates": {"path": "outputs/analysis/p3_official_igu_replicates.json",
                       "sha256_prefix": sha16(rep_p)},
        "runs": {"path": "outputs/analysis/p3_official_igu_run.json",
                 "sha256_prefix": sha16(run_p)},
    },
    "printed_values": {
        "mean_gap_delta_E": OV["mean_gap_delta_E"],
        "ci95": OV["ci95"],
        "margin": OV["margin"],
        "margin_fraction_of_E0": OV["margin_fraction_of_E0"],
        "E0": E0,
        "tost_p": TAD["tost_p"],
        "min_equivalent_margin": TAD["min_equivalent_margin"],
        "allocation_l1": OV["allocation_l1"],
        "allocation_l1_tolerance": CMP["meta"]["allocation_l1_tolerance"],
        "l1_archived": SENS["archived"]["l1"],
        "l1_corrected": SENS["corrected"]["l1"],
        "n_pairs": CMP["n_pairs"],
        "n_runs": len(RUN["runs"]),
        "same_stack_for_every_pair": CMP["same_stack_for_every_pair"],
        "stack_mix_warning": CMP["stack_mix_warning"],
        "replicate_max_spread": REPS["max_spread_across_arms"],
        "replicate_mean_spread": REPS["mean_spread_across_arms"],
        "archived_gap": REPS["archived_official_minus_reimpl_gap"],
        "stack": {"torch": ENV["torch"], "cuda": ENV["cuda"], "gpu": ENV["gpu"]},
        "official_allocation_pdf": off_alloc,
        "reimpl_allocation_pdf": rei_alloc,
    },
}
OUT.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
print("integrated subsection app:igucompare at line %d (%d lines); table tab:igucompare"
      % (rec["inserted_start_line"], rec["inserted_lines"]))
print("section count unchanged (still a subsection inside S41); table count +1")
