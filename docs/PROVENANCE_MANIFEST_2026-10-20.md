# Provenance manifest (2026-10-20)

Rule: every table/figure that reports our own results must name its generating script and its result JSON
archive. Literature tables and schematic diagrams are exempt but listed explicitly.
Gate: `python tools/_p1428_provenance_gate.py` (must print PASS).

## P3 (paper3/paper_ieee)

| item | script | archive | status |
|---|---|---|---|
| `fig:counterfactual` | `paper3/scripts/analysis/plot_all_figures.py` | `paper3/scripts/outputs/experiments/all_results.json` | verified |
| `fig:phase_transition` | `paper3/scripts/analysis/plot_all_figures.py` | `paper3/scripts/outputs/experiments/all_results.json` | verified |
| `tab:phase` | `paper3/scripts/run_full_sweep.py` | `paper3/scripts/outputs/experiments/E2_results.json` | verified |
| `tab:sample` | `paper3/scripts/run_sample_size_sweep.py` | `paper3/scripts/outputs/experiments/sample_size_results.json` | verified |

## A1 (paper_a1)

| item | script | archive | status |
|---|---|---|---|
| `fig:campaign` | `tools/_p1333_upgrade_figures.py` | `outputs/analysis/a1_campaign_analysis.json` | verified |
| `fig:ga` | `tools/_p1276_graphical_abstract.py` | `outputs/analysis/a1_matched_gap_families.json` | verified |
| `fig:lambda` | `tools/clip_a1_figures.py` | `outputs/a1_full_results.json` | verified |
| `fig:matchedgap` | `tools/_p1210_figure_matched_gap.py` | `outputs/analysis/a1_matched_gap_families.json` | verified |
| `fig:spectrum` | `tools/clip_a1_figures.py` | `outputs/a1_subspace_results.json` | verified |
| `fig:tau` | `tools/clip_a1_figures.py` | `outputs/a1_full_results.json` | verified |
| `fig:traj` | `tools/clip_a1_fig4.py` | `outputs/a1_tau_trajectory.json` | verified |
| `tab:asym` | `tools/clip_a1_text_surgery.py` | `outputs/a1_text_surgery.json` | verified |
| `tab:benchmarks` | `tools\_claim_ledger_a1.py` | `outputs/analysis/a1_more_benchmarks.json` | verified |
| `tab:campaign` | `tools/_p1320_campaign_analysis.py` | `outputs/analysis/a1_campaign_analysis.json` | verified |
| `tab:ckpt_transfer` | `tools\_p1430_provenance_map_curated.py` | `outputs/analysis/a1_ckpt_transfer.json` | verified |
| `tab:controls` | `tools/_p1256_insert_a1_theory.py` | `outputs/analysis/a1_matched_gap_families.json` | verified |
| `tab:cross` | `tools/clip_a1_crossmodel.py` | `outputs/a1_crossmodel_results.json` | verified |
| `tab:dense` | `tools/_p1280_matched_gap_more_backbones.py` | `outputs/analysis/a1_matched_gap_dense.json` | verified |
| `tab:earlystop` | `tools\_docs_a1_fixes_done.py` | `outputs/analysis/a1_epoch_sweep_analysis.json` | verified |
| `tab:hard_k` | `tools\_claim_ledger_a1.py` | `outputs/analysis/a1_tau_k.json` | verified |
| `tab:hard_offset` | `tools/a1_h_offset.py` | `outputs/a1_h_offset.json` | verified |
| `tab:hard_seed` | `tools/a1_h_seed_summary.py` | `outputs/a1_h_seed_summary.json` | verified |
| `tab:hard_tpl` | `tools\_claim_ledger_a1.py` | `outputs/analysis/a1_prompt_template_gap.json` | verified |
| `tab:matchedgap` | `tools/_p1210_figure_matched_gap.py` | `outputs/analysis/a1_matched_gap_families.json` | verified |
| `tab:monitor_regret` | `tools/_p1408_a1_table.py` | `outputs/analysis/a1_monitor_split_diagnosis.json` | verified |
| `tab:morebench` | `tools/_p1264_more_benchmarks.py` | `outputs/analysis/a1_more_benchmarks.json` | verified |
| `tab:multiseed` | `tools/clip_a1_multiseed.py` | `outputs/a1_multiseed.json` | verified |
| `tab:pointwise` | `tools/clip_a1_margins.py` | `outputs/a1_margins.json` | verified |
| `tab:prompt` | `tools/_p1263_prompt_template_control.py` | `outputs/analysis/a1_prompt_template_gap.json` | verified |
| `tab:protocol` | `tools/_p1255_tau_monitor_protocol.py` | `outputs/analysis/a1_monitor_protocol.json` | verified |
| `tab:qwen` | `tools\ap3_a1_revision_check.py` | `outputs/a1_qwen_surgery_v3.json` | verified |
| `tab:realpairs` | `tools/_p1273_retrieval_evidence.py` | `outputs/analysis/a1_real_checkpoint_pairs.json` | verified |
| `tab:selection` | `tools/_p1316_insert_strengthen3.py` | `outputs/analysis/a1_selection_rule.json` | verified |
| `tab:showdown` | `tools/_p1310_insert_final_round.py` | `outputs/analysis/a1_statistic_showdown.json` | verified |
| `tab:spectrum` | `tools/clip_a1_baseline_metrics.py` | `outputs/a1_baseline_metrics.json` | verified |
| `tab:standard` | `-` | `-` | exempt |
| `tab:topk` | `tools\a1_h_bootstrap.py` | `outputs/a1_rr_e2_topk.json` | verified |

## A23 (paper_a2)

| item | script | archive | status |
|---|---|---|---|
| `fig:degrad` | `tools/clip_a2_figures.py` | `outputs/ocean_degradation.json` | verified |
| `fig:lambda` | `tools/clip_a2_figures.py` | `outputs/ocean_gap_surgery.json` | verified |
| `fig:peft` | `tools/clip_a2_figures.py` | `outputs/ocean_peft.json` | verified |
| `fig:sigma` | `tools/clip_a2_figures.py` | `outputs/ocean_margins.json` | verified |
| `fig:sonar-sigma` | `tools/clip_a2_fig7.py` | `outputs/sonar_protocol_full.json` | verified |
| `fig:sonar-tau` | `tools/clip_a2_figures.py` | `outputs/sonar_protocol_full.json` | verified |
| `fig:tau` | `tools/clip_a2_figures.py` | `outputs/ocean_margins.json` | verified |
| `tab:calib` | `tools\_p1431_provenance_map_a23.py` | `outputs/threshold_calibration.json` | verified |
| `tab:classlaw` | `tools\_p1431_provenance_map_a23.py` | `outputs/ocean_sigma_other.json` | verified |
| `tab:degmap` | `tools\_a23_verify_d1.py` | `outputs/degradation_matrix.json` | verified |
| `tab:degrad` | `tools\_a23_verify_d1.py` | `outputs/ocean_degradation.json` | verified |
| `tab:dir-op` | `tools\_p1431_provenance_map_a23.py` | `outputs/direction_operator.json` | verified |
| `tab:disc` | `tools\_p1431_provenance_map_a23.py` | `outputs/ocean_clip2x2.json` | verified |
| `tab:dynamics` | `tools\_a23_dynamics_check.py` | `outputs/dynamics_matrix.json` | verified |
| `tab:eng` | `-` | `-` | exempt |
| `tab:matrix` | `tools\_a23_verify_d1.py` | `outputs/domain_matrix.json` | verified |
| `tab:ml16k` | `tools\_p1431_provenance_map_a23.py` | `outputs/ocean_ml16k_retrieval.json` | verified |
| `tab:monitor` | `tools\_a23_dynamics_check2.py` | `outputs/ocean_tautraj.json` | verified |
| `tab:peft` | `tools\_p1431_provenance_map_a23.py` | `outputs/ocean_peft.json` | verified |
| `tab:perimage` | `tools\_p1431_provenance_map_a23.py` | `outputs/perimage_operator.json` | verified |
| `tab:portrait` | `tools\_p1431_provenance_map_a23.py` | `outputs/ocean_margins.json` | verified |
| `tab:qa-layers` | `tools\_p1431_provenance_map_a23.py` | `outputs/ml16k_qa_layers.json` | verified |
| `tab:rank1` | `tools\_a23_verify_d1.py` | `outputs/ocean_rank1_bound.json` | verified |
| `tab:replica` | `tools\_p1431_provenance_map_a23.py` | `outputs/ocean_replica.json` | verified |
| `tab:sonar-exact` | `tools\_a23_verify_d1.py` | `outputs/sonar_protocol_full.json` | verified |
| `tab:sonar-peft` | `tools\_p1431_provenance_map_a23.py` | `outputs/sonar_peft.json` | verified |
| `tab:sonar-sigma` | `tools\_a23_verify_d1.py` | `outputs/sonar_protocol_full.json` | verified |
| `tab:spectrum` | `tools\_p1351_a23_extended_transfer.py` | `outputs/ocean_spectrum.json` | verified |
| `tab:subspace` | `tools\_p1431_provenance_map_a23.py` | `outputs/direction_subspace.json` | verified |
| `tab:theory-stack` | `tools\_a23_c5_locate.py` | `outputs/a1_theory_verify.json` | verified |
| `tab:watertank` | `tools\_a23_verify_d1.py` | `outputs/sonar_protocol_full.json` | verified |

## paperA (paper合)

| item | script | archive | status |
|---|---|---|---|
| `fig:ablation` | `tools/_pa_rebuild_figs_rest.py` | `outputs/flickr30k/alpha_16/gap_history.json` | verified |
| `fig:adapter_layered` | `tools/_pa_fix_fig14_title.py` | `outputs/adapter_layered_results.json` | verified |
| `fig:budget` | `tools/_pa_split_appendix_figs.py` | `outputs/analysis/strict_control_summary.json` | verified |
| `fig:corr` | `tools/_pa_fig2_corr.py` | `outputs/analysis/dg_r1_reproducible.json` | verified |
| `fig:crossmethod` | `tools/_pa_rebuild_figs_rest.py` | `outputs/theory/adapter/adapter_all_results.json` | verified |
| `fig:ers` | `tools/_pa_rebuild_figs_rest.py` | `outputs/analysis/k_remeasured_both.json` | verified |
| `fig:falsification` | `tools/_pa_rebuild_figs_rest.py` | `outputs/analysis/k_remeasured_both.json` | verified |
| `fig:layered_ft` | `tools/_pa_rebuild_fig10.py` | `outputs/layered_ft_results.json` | verified |
| `fig:noise_sensitivity` | `tools/_pa_fig9_noise_rebuild.py` | `outputs/noise_fixed_aug.json` | verified |
| `fig:ode` | `tools/_pa_rebuild_figs_rest.py` | `outputs/theory/beta_pilot/beta_pilot_both_r8/seed42/beta_results.json` | verified |
| `fig:overview` | `tools/_pa_rebuild_figs_rest.py` | `outputs/flickr30k/rq2_both/gap_history.json` | verified |
| `fig:ratio` | `tools/_pa_split_appendix_figs.py` | `outputs/noise_fixed_aug.json` | verified |
| `fig:sigma0_control` | `tools/_pa_split_appendix_figs.py` | `outputs/noise_fixed_aug.json` | verified |
| `fig:site_schematic` | `tools/_p1333_upgrade_figures.py` | `-` | exempt |
| `fig:stratified` | `tools/_p860_fig_stratified.py` | `outputs/analysis/dg_r1_reproducible.json` | verified |
| `fig:vision_untouched` | `tools/_pa_fig8c.py` | `outputs/analysis/strict_control_summary.json` | verified |
| `fig:weight_svd` | `tools/_pa_fig8_rebuild.py` | `outputs/analysis/strict_control_summary.json` | verified |
| `fig:zeroshot` | `tools/_pa_rebuild_fig12.py` | `outputs/zeroshot_extra.json` | verified |
| `tab:beta_pilot` | `tools\_p1432_provenance_map_paperA.py` | `outputs/theory/beta_pilot/beta_pilot_results.json` | verified |
| `tab:config_groups` | `tools\_audit_figure_provenance.py` | `outputs/analysis/strict_control_summary.json` | verified |
| `tab:corr` | `tools\_audit_figure_provenance.py` | `outputs/analysis/dg_r1_reproducible.json` | verified |
| `tab:diagnostics` | `tools\_claim_ledger.py` | `outputs/analysis/ode_ledger.json` | verified |
| `tab:family` | `tools\_claim_ledger.py` | `outputs/analysis/ode_ledger.json` | verified |
| `tab:generalization` | `tools\_claim_ledger.py` | `outputs/analysis/ode_ledger.json` | verified |
| `tab:grad_side` | `tools\_append_k_final.py` | `outputs/analysis/k_remeasured_both.json` | verified |
| `tab:llava` | `tools\_p1145_clean_gap_measure.py` | `outputs/canonical_caption_metric.json` | verified |
| `tab:phase2` | `tools\_claim_ledger.py` | `outputs/analysis/ode_ledger.json` | verified |
| `tab:position` | `tools\_p1432_provenance_map_paperA.py` | `outputs/analysis/tab_position_provenance.json` | verified |
| `tab:position_strict` | `tools\_p1432_provenance_map_paperA.py` | `outputs/analysis/strict_table_provenance.json` | verified |
| `tab:vlm` | `tools\_p1164_verify_pull_analyze_e.py` | `outputs/vlm_clean_summary.json` | verified |

Totals: 98 floats; verified 95; exempt 3; pending 0.
| `tab:prereg` | `tools/_p1759_write_prereg_into_ms.py` | `outputs/paperA_c_prereg*/` (three batches) | verified |
| `fig:prereg` | `tools/_p1769_upgrade_a4_figures.py` | `outputs/analysis/paperA_prereg_stats.json` | verified |
| `fig:compmodels` | `tools/_p1769_upgrade_a4_figures.py` | `outputs/analysis/paperA_competing_models_cv.json` | verified |

