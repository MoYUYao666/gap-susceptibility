# P3 v2 provenance

All reported numbers are derived from archived files. This note maps each figure/table and the main numerical claims
to its source; the audit appendix repeats the list in the manuscript.

| artifact / claim | source | generating script |
|---|---|---|
| Fig. 1 (PACT pilot) | `outputs/analysis/p3_pact_pilot.json` | `paper3/upgrade_v2/analysis/pact_pilot.py` |
| Table 1 (claim status) | consolidation of the audit sources below | manual from archived records |
| Table 2 (evidence blocks) | `paper3/scripts/outputs/experiments/` plus the frozen P3 supplement | manual from archived records |
| Table 3 (public benchmarks) | `outputs/analysis/p3_v2_benchmark_*.json` | `paper3/upgrade_v2/analysis/benchmark_eval.py` |
| Fig. 2 (VQA-RAD) | `outputs/analysis/p3_rank_separation_extended.json`, `outputs/analysis/p3_vqa_full_equivalence.json` | `paper3/upgrade_v2/figures/make_downstream.py` |
| Fig. 3 (r5-r6 forest) | `outputs/analysis/p3_v2_allocation_diff.json` | `paper3/upgrade_v2/analysis/allocation_diff.py` |
| Table 4 (Qwen cross-architecture) | `outputs/analysis/p3_v2_qwen_*.json` | `paper3/upgrade_v2/analysis/qwen_benchmark_eval.py`, `train_qwen_vqa.py` |
| Table 5 (allocation summary) | `paper3/scripts/outputs/experiments/all_results.json` | direct aggregate |
| Table 6 (artifact map) | this file and `paper3/upgrade_v2/` | manual |
| post-hoc multiplicity check | `outputs/analysis/p3_v2_multiplicity.json` | `paper3/upgrade_v2/analysis/multiplicity.py` |
| reference-batch PACT values and leave-one-out range | `outputs/analysis/p3_pact_pilot.json` | `pact_pilot.py` |
| environment variance share ~45% | `outputs/analysis/p3_env_stack_seeds.json` | archived field `env_variance_share` |
| VQA-RAD base/r5/r6 values | `p3_rank_separation_extended.json` / `p3_vqa_full_equivalence.json` | archived fields |
| caption/instruction checks | `p3_caption_metrics.json`, `p3_instr_downstream_{base,5,6}.json` | archived fields |
| allocation baseline values | `p3_ntk_allocation.json`, `p3_baseline_rules.json`, `p3_igu_allocation.json` | archived fields |
| 190-run archive / model families | `paper3/scripts/outputs/experiments/` and the frozen P3 supplementary | frozen P3 package |

The three figure PDFs are vector files with embedded Times/STIX CID TrueType fonts; the PNG previews are ignored by git.
The Qwen2-VL-2B rank-5 adapter is the only new training run in this draft; every other number is archived. If a number
is later changed, update this table and the manuscript source in the same commit.
