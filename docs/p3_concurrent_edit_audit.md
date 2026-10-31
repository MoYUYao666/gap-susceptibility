# P3 concurrent-edit audit (started 2026-10-24 22:40)

Two remediation agents ended up editing the same P3 files at the same time. This file is the audit trail: what each
one changed, which changes are correct, and which must be reverted. It is written outside `paper3/` on purpose so
that it cannot itself collide with their writes.

## The conflict

| agent | role | first write | last write seen |
|---|---|---|---|
| remediation A (`_p1637` registry + manuscript numbers) | full unsourced-number triage | ~22:15 | 22:37 (still writing when checked) |
| remediation B (spawned because A appeared stopped) | same task, plus the three one-liners | read-only so far | - |

Both were given overlapping write scopes over `supplementary.tex`, `sections/*.tex` and
`tools/_p1637_p3_reproduce_all.py`. Neither can be stopped mid-run by the lead (subagents are not addressable), so
the plan is: **let them stop, then audit every diff against the archives and revert anything wrong.**

## Already-confirmed wrong edit (revert candidate)

`sections/conclusion.tex`: the sentence

> (ranks $\le14$ converge, two of three seeds diverge at $r=16$, all three by $r=20$)

was rewritten to

> (ranks $\le20$ converge, all three seeds diverge at $r=24$)

while the same sentence still says "places the crossing higher, between $r=14$ and $r=16$" - internally
inconsistent. The archives support the ORIGINAL wording:

* `outputs/analysis/p3_upgrade_analysis.json :: rank_sweep.critical_rank` =
  `{last_converged_rank: 14, first_majority_diverged_rank: 16, boundary_interval: [14, 16], partial_divergence_ranks: [16]}`;
* `:: rank_sweep.rows[*].n_diverged` per rank: `r<=14 -> 0`, `r=16 -> 2`, `r=20 -> 3`, `r=24 -> 3`;
* in that dense sweep "diverge" means the final energy overshoots `E0 = 3927`; at r=16 the three final energies are
  3810 / 5359 / 5464, i.e. two of three exceed E0.

So the original sentence is **sourced**, and the ledger's `UNSOURCED` verdict for the r=16/r=20 divergence counts was
a **ledger gap, not a manuscript error**. Action: keep the original wording, classify those ledger entries as
sourced (`p3_upgrade_analysis.json :: rank_sweep.*`), and reject any rewrite that borrows a different run family's
numbers (the `E0 = 3921` NaN-convention family) to describe this dense sweep.

## Audit plan once both writers stop

1. `git diff` over `paper3/paper_ieee/**` and read every hunk; classify each as (i) sourced correction,
   (ii) reclassification only, (iii) deletion of an unsourced number, (iv) **wrong - revert**.
2. Re-run `python tools/_p1637_p3_reproduce_all.py --check --quiet`; every remaining `MISMATCH` must be either
   fixed or explained in the ledger, and `UNSOURCED` may only contain entries the agents deliberately classified.
3. Re-run `audit_check.py`, `audit_pdf.py`, `_p1428_provenance_gate.py`, `paper_audit --profile p3_prl`.
4. Recompile `main.tex` and `supplementary/supplementary.tex`; confirm 10 pages / 46 sections / 22 pages (or update
   the constants and say why).
5. Record the outcome here, then hand the manuscript back to a single writer for any remaining prose fix.

## Revert checklist (grows as the diff is read)

- [ ] `sections/conclusion.tex` divergence sentence: restore `ranks <=14 converge, two of three seeds diverge at r=16, all three by r=20`. If the rewritten numbers came from the second run family, the rewrite is not a correction at all.

## Outcome (2026-10-24 23:05)

The conclusion clause was **reverted to the original wording** (`ranks <=14 converge, two of three seeds diverge at r=16, all three by r=20`). Both candidate readings are sourced, but they are two different notions of divergence in two different run families: the energy-overshoot notion (dense sweep, `outputs/analysis/p3_upgrade_analysis.json :: rank_sweep`) and the non-finite-loss notion (E2 sweep, `paper3/scripts/outputs/experiments/E2_results.json :: sweep`, first 3/3 non-finite at r=24). The conclusion sentence talks about the crossing, which is the dense-sweep family, and `experiments.tex` already reports the NaN-at-r>=24 fact where it belongs. An expanded version that labelled both notions pushed `main.pdf` to 11 pages against PRL's 10-page limit, so it was rejected for length as well.
