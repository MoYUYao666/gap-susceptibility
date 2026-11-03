# A3 - provenance of every reported number

Rule (repository-wide): every table or figure that reports our own results must name the script that generated it and the
result file it read. This file is that register for A3.

## Frozen inputs

| input | how it was produced | archive |
|---|---|---|
| four provenance corpora | `scripts/build_text_provenance.py` on the annotations converted by `scripts/convert_*.py` | `corpora/<dataset>/provenance_manifest.json` (counts + sha256 per file) |
| budget subsets | `scripts/match_budgets.py` | `corpora/<dataset>/budgets/budget_manifest.json` |
| dataset archives | public releases, urls + sha256 | `data/README.md` |

## Main grid (144 cells)

| item | script | result file |
|---|---|---|
| run records | `scripts/train_lora_provenance.py` via `scripts/run_full_grid.py` | `runs/full_10k/<cell>.json` (untracked; regenerable), one JSON per cell |
| aggregated statistics | `scripts/aggregate_grid.py` | `analysis/full_10k_aggregate.json` (`table` array: mean/std per dataset x arm x site) |
| Table 1 (`tab:main`) | `scripts/make_tables.py` | `analysis/full_10k_aggregate.json` |
| Figure 1 (`fig:provenance`) | `scripts/make_figures.py` | same JSON |
| in-text numbers | generated macros in `draft/numbers.tex` | same JSON |

## Scaling grid (16 cells)

| item | script | result file |
|---|---|---|
| run records | `scripts/train_lora_provenance.py` via `scripts/run_scale_grid.py` | `runs/scale_50k/<cell>.json` |
| comparison and deltas | inline analysis in `HANDOFF.md` for 2026-10-29, archived as `analysis/h2_scaling.json` and `h2_scaling.md` | those two files |
| Table 2 (`tab:scaling`) | `scripts/make_tables.py` | `analysis/h2_scaling.json` |
| Figure 2 (`fig:scaling`) | `scripts/make_figures.py` | `analysis/h2_scaling.json` + `full_10k_aggregate.json` |

## Captioning probe (H4)

| item | script | result file |
|---|---|---|
| per-arm captioning scores | `scripts/run_captioning.py --dataset rsicd --limit 8000` | `runs/captioning/rsicd/<arm>.json` (untracked) and `analysis/captioning_rsicd.json` |
| Table 4 (`tab:captioning`) | generated in the same script run, archived as `draft/table_captioning.tex` from `analysis/captioning_rsicd.json` | the analysis JSON |

## Corpora statistics

| item | script | result file |
|---|---|---|
| Table 3 (`tab:corpora`) | `scripts/make_tables.py` | `corpora/<dataset>/provenance_manifest.json` |

## Verification steps performed

- every table value is written by a script from a JSON; no number in the manuscript is typed by hand;
- `draft/numbers.tex` is generated, and its macros are the only numbers quoted in prose;
- figures use Times New Roman + STIX with CID TrueType (`pdffonts` checked);
- the bibliography has 22 entries, all with DOIs, the six new ones verified on 2026-10-29 (CrossRef for dataset DOIs,
  DataCite for the arXiv DOIs), the rest carried over from the verified survey bibliography.

## Robustness tables (added 2026-10-29)

| item | script | result file |
|---|---|---|
| Table 5 (`tab:epochs`) | `scripts/analyse_robustness.py` | `runs/epoch_ablation/*.json` -> `analysis/epoch_ablation.json` |
| Table 6 (`tab:backbones`) | `scripts/analyse_robustness.py` | `analysis/georsclip/full_10k_aggregate.json`, `analysis/l14/full_10k_aggregate.json`, `runs/humanrich_10k/*.json` |
| Table 7 (`tab:transfer`) | `scripts/run_transfer_eval.py` then `scripts/analyse_robustness.py` | `analysis/transfer_matrix.json` |
| robustness macros | `scripts/analyse_robustness.py` | `draft/rust_numbers.tex` |

All four were generated after the experiments finished; the manuscript compiles with 19 pages and no undefined
citations or references. The optional class-only metadata control was started and stopped; it is not used in any claim.

## Positioning table (added 2026-10-29, second visual pass)

| item | how it was produced |
|---|---|
| Table 1 (`tab:landscape`) | hand-compiled from the cited papers' own descriptions; every entry traces to the citation in the row (GAIA, OSM-CLIP, PMPGuard, synthetic-caption M2GARSS, LaCLIP, caption-analysis EMNLP); literature table, exempt from the our-results rule, declared here |

## Full-corpus check (added 2026-10-29)

| item | script | result file |
|---|---|---|
| Table 8 (`tab:fullcorpus`) | `scripts/analyse_fullcorpus.py` | `runs/fullcorpus/*.json` -> `analysis/fullcorpus.json` |
| full-corpus macros | `scripts/analyse_fullcorpus.py` | `draft/rust_numbers.tex` |

The full-corpus cells train on every image (all captions, at most one caption per image per batch) and evaluate with
one caption per test image, so they are comparable with the 10k cells.

## Cloud supplements (added 2026-10-29)

| item | script | records |
|---|---|---|
| Table 8 (`tab:l14grid`): RemoteCLIP ViT-L/14, 4 arms x 2 corpora x 3 sites, seed 0 | `cloud/analyse_cloud_runs.py` | `runs/cloud_l14/*.json` (16) + `runs/cloud_l14_nwpu/*.json` (8) -> `analysis/cloud_summary.json` |
| Table 10 (`tab:cloudfull`): every image, four arms + human-rich, three seeds | `cloud/analyse_cloud_runs.py` | `runs/cloud_fullcorpus/*.json` (12) + `runs/cloud_fullextra/*.json` (18) |
| run-record archive | - | `docs/cloud_runs_2026-10-29.tgz`, sha256 `36f32f86cf3bd0ba06db5710ac6643ad76e1868feae0b26375c78ce35efd1767` |

Training used the same script as every other cell (`scripts/train_lora_provenance.py`), with `--one-per-image` for
multi-caption human corpora and `--cache-images` to remove slow block storage from the training loop. The cloud machine
was a single 32 GB vGPU; 56 cells were completed and verified before the records were copied back.

## Length control (added 2026-10-29, mock-review response)

| item | script | records |
|---|---|---|
| Human caption repeated five times (same length as the human-rich arm, no new content), 10k pairs, 3 seeds, both corpora | `scripts/make_repeated_corpus.py` -> `scripts/run_repeated_grid.py` -> `scripts/analyse_repeated.py` | `runs/repeated_10k/*.json` -> `analysis/repeated.json` |

Result: RSICD 0.127 +- 0.007, NWPU-Captions 0.217 +- 0.007, against human 0.148/0.165 and human-rich 0.196/0.340; the
sentence in Section 5.3 uses the generated macros from `draft/repeated_numbers.tex`.

## LLM-caption arm (added 2026-10-29, mock-review response R2)

| item | script | records |
|---|---|---|
| Qwen3-VL-8B captions for 3,000 RSICD images (1.44 s/img, local LM Studio server) | `scripts/make_llm_caption_corpus.py` | `corpora/rsicd/llmcaption.jsonl` |
| matched 3,000-image subset for every arm | `scripts/make_llm_subset_corpora.py` | `corpora/rsicd/subset3000_<arm>.jsonl` |
| four arms x two seeds, same adapter and schedule | `scripts/run_llmarm_grid2.py` | `runs/llmarm_3k/*.json` -> `analysis/llm_arm.json` |
| table and macros | `scripts/analyse_llmarm.py` | `draft/table_llmarm.tex`, `draft/llmarm_numbers.tex` |

Result: human 0.117 +- 0.004, LLM 0.104 +- 0.004, templated 0.037 +- 0.003, metadata 0.008 +- 0.001
(matched 3,000-image RSICD subset, seeds 0-1). The generator is Qwen3-VL-8B Q4_K_M, run locally.

## NWPU-Captions LLM arm and classification probe (added 2026-10-30)

| item | script | records |
|---|---|---|
| 968 NWPU-Captions images captioned with Qwen3-VL-8B (1.54 s/img) | `scripts/make_llm_caption_corpus.py` | `corpora/nwpu_captions/llmcaption.jsonl` |
| matched 968-image subsets on the five-arm intersection | `scripts/make_llm_subset_corpora.py --intersect` | `corpora/nwpu_captions/subset968_<arm>.jsonl` |
| four arms x two seeds, same adapter and schedule | `scripts/run_llmarm_grid_nwpu968.py` | `runs/llmarm_968_nwpu/*.json` |
| second-task classification probe on the exported adapters | `scripts/probe_classification.py` -> `scripts/analyse_probe.py` | `runs/classification_probe/*.json` -> `draft/probe_numbers.tex` |

Result: RSICD subset human 0.117 > LLM 0.104; NWPU-Captions subset LLM 0.233 > human 0.151; classification probe
saturates at 0.964-0.969 for all arms (RSICD test split, 2,054 images, 30 classes).

## Full-scale LLM arms, two generators (added 2026-10-30)

| item | script | records |
|---|---|---|
| Qwen3-VL-8B captions for all 10,921 RSICD images | `scripts/make_llm_caption_corpus.py` | `corpora/rsicd/llmcaption.jsonl` |
| MiniCPM-V-2.6 captions for all 10,921 RSICD images | same script, `--model minicpm-v-2_6` | `corpora/rsicd/llmcaption2.jsonl` |
| full-corpus matched corpora (six arms, one text per image) | `scripts/make_full_matched_corpora.py` | `corpora/rsicd/full_<arm>.jsonl` |
| full-corpus arm grids (2 seeds each) | `scripts/run_fullarm_grid.py` -> `scripts/analyse_fullarm.py` | `runs/fullarm_rsicd_rsicd_llm*` -> `analysis/fullarm.json` |

Result (RSICD, all images, joint site): Qwen3-VL-8B 0.262 +- 0.010, human-rich 0.202 +- 0.002, MiniCPM-V-2.6
0.159 +- 0.004, human 0.127 +- 0.002, templated 0.077 +- 0.007, metadata 0.053 +- 0.010.
