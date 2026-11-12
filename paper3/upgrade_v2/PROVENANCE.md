# P3 v2 provenance

All reported numbers are derived from archived files. This note maps each figure/table and the main numerical claims
to its source; the audit appendix repeats the list in the manuscript.

| artifact / claim | source | generating script |
|---|---|---|
| Fig. 1 / Table 3 (PACT pilot) | `outputs/analysis/p3_pact_pilot.json` | `paper3/upgrade_v2/analysis/pact_pilot.py` |
| Table 6 (six public benchmarks) | `outputs/analysis/p3_v2_benchmark_*.json` | `paper3/upgrade_v2/analysis/benchmark_eval.py` |
| Table 5 (held-out caption/instruction) | `outputs/analysis/p3_v2_heldout_*.json` | `paper3/upgrade_v2/analysis/heldout_downstream.py` |
| Fig. 2 / Table 4 (VQA-RAD) | `outputs/analysis/p3_rank_separation_extended.json`, `outputs/analysis/p3_vqa_full_equivalence.json` | `paper3/upgrade_v2/figures/make_downstream.py` |
| Table 1 (claim status) | consolidation of the audit sources below | manual from archived records |
| Fig. 3 (r5-r6 forest) | `outputs/analysis/p3_v2_allocation_diff.json` | `paper3/upgrade_v2/analysis/allocation_diff.py` |
| Table 7 (Qwen cross-architecture) | `outputs/analysis/p3_v2_qwen_*.json` | `paper3/upgrade_v2/analysis/qwen_benchmark_eval.py`, `train_qwen_vqa.py` |
| Table 8 (protocol conditions) | consolidation of `p3_gamma_batch_sensitivity`, `p3_env_stack_seeds`, downstream archives | manual |
| Table 9 (allocation summary) | `paper3/scripts/outputs/experiments/all_results.json` | direct aggregate |
| 190-run archive / model families | `paper3/scripts/outputs/experiments/` and the frozen P3 supplementary | frozen P3 package |
| reference-batch PACT values | `p3_gamma_batch_sensitivity.json` | `pact_pilot.py` |
| environment variance share ~45% | `p3_env_stack_seeds.json` | archived field `env_variance_share` |
| VQA-RAD base/r5/r6 values | `p3_rank_separation_extended.json` / `p3_vqa_full_equivalence.json` | archived fields |
| caption/instruction checks | `p3_caption_metrics.json`, `p3_instr_downstream_{base,5,6}.json` | archived fields |
| allocation baseline values | `p3_ntk_allocation.json`, `p3_baseline_rules.json`, `p3_igu_allocation.json` | archived fields |

The two figure PDFs are vector files with embedded Times/STIX CID TrueType fonts; the PNG previews are ignored by git.
No new training run is introduced in this draft. If a number is later changed, update this table and the manuscript
source in the same commit.
