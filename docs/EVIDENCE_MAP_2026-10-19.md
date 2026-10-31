# Evidence map — A1 and Paper A (2026-10-19)

> One line per manuscript claim that a revision response might need: the archive that carries the number and the script
> that produced it. Paths are relative to the repository root. The frozen submission packages and their copies under
> `SUBMISSION/_frozen_submitted/` are not listed here because they are not evidence.

## A1 — `paper_a1/`

| Claim | Archive | Script |
|---|---|---|
| Matched-gap dissociation, sparse sweep (32.7 at 0.028; 52.1 at 0.05) | `outputs/analysis/a1_matched_gap_second_dataset.json` | `tools/_p1254_matched_gap_second_dataset.py` |
| Dense five-backbone sweep (50.6 / 54.4 / 48.0 / 7.7 / 62.0 at ≤0.03) | `outputs/analysis/a1_matched_gap_dense.json` | `tools/_p1300_matched_gap_dense.py` |
| Real-checkpoint pairs, archived set (6.64 at 0.0024) | `outputs/analysis/a1_real_checkpoint_pairs.json` | `tools/_p1301_lower_bound_constants.py` |
| Campaign: 18 runs, 72 checkpoints, 670 pairs, 48.5 at 0.0242 | `outputs/analysis/a1_campaign.json`, `a1_campaign_analysis.json`, `a1_campaign_correct.npz` | `tools/_p1319`, `_p1320` |
| Lower bound constants ($L=1.013$, mass 0.681/0.875) | `outputs/analysis/a1_lower_bound_constants.json` | `tools/_p1301_lower_bound_constants.py` |
| Margin mass and correlations (Bootstrap CI inputs) | `outputs/analysis/a1_margin_mass.json` | `tools/_p1299_margin_mass.py` |
| Statistic showdown (classification / retrieval / real fine-tuning) | `outputs/analysis/a1_statistic_showdown.json` | `tools/_p1308_statistic_showdown.py` |
| Williams tests | `outputs/analysis/a1_williams_tests.json` | `tools/_p1314_williams.py` |
| Selection rule (synthetic + templates) | `outputs/analysis/a1_selection_rule.json` | `tools/_p1315_selection_rule.py` |
| Half-sample, binomial interval, templates | `outputs/analysis/a1_robustness.json` | `tools/_p1309_robustness.py` |
| Prompt-template drift of CG | `outputs/analysis/a1_prompt_template_gap.json` | `tools/_p1263_prompt_template_control.py` |
| Threshold transfer | `outputs/analysis/a1_threshold_transfer.json` | `tools/_p1262_threshold_transfer.py` |
| Retrieval evidence (synthetic + real fine-tune) | `outputs/analysis/a1_retrieval_evidence.json`, `a1_retrieval_realfinetune.json` | `tools/_p1273`, `_p1332` |
| Monitoring protocol and uncertainty | `outputs/analysis/a1_monitor_protocol.json`, `a1_monitor_uncertainty.json` | `tools/_p1255`, `_p1274` |
| Margin mass under templates (P0-2) | `outputs/analysis/a1_margin_templates.json` | `tools/_p1330_margin_templates.py` |
| Cross-domain campaign (P2-11) | `outputs/analysis/a1_campaign_crossdomain.json` | `tools/_p1332_retrieval_and_crossdomain.py` |
| Within-run correlations | `outputs/analysis/a1_showdown_within_run.json` | `tools/_p1331_upgrade_analyses.py` |
| Stopping-rule limitation (campaign + interior-optimum control) | `outputs/analysis/a1_certificate_rule.json`, `a1_certificate_interior.json` | `tools/_p1331`, `_p1334` |
| Claim ledger (157 assertions) | `outputs/analysis/claim_ledger_a1.json` | `tools/_claim_ledger_a1.py` |

## Paper A — `paper合/`

| Claim | Archive | Script |
|---|---|---|
| ODE fits and parameters (96 runs) | `outputs/analysis/ode_ledger.json` | archived fits; ledger written by `_p1*` chain |
| ODE per-condition diagnostics (P0-4) | `outputs/analysis/paperA_ode_diagnostics.json` | `tools/_p1331_upgrade_analyses.py` |
| Rank × position dynamics (P0-3) | `outputs/analysis/paperA_rank_position_dynamics.json` | `tools/_p1331_upgrade_analyses.py` |
| Family comparison, LoRA vs adapter vs full FT (P1-8) | `outputs/analysis/paperA_lora_vs_fullft.json` | `tools/_p1331_upgrade_analyses.py` |
| Position table provenance and verification | `outputs/analysis/position_table_verification.json`, `tab_position_provenance.json` | archived |
| Full fine-tuning and LoRA rerun inventories | `outputs/analysis/pr_fullft_*.json`, `lora_claim_dependency.json` | archived |
| Claim ledger (76 assertions) | `outputs/analysis/claim_ledger_paperA.json` | `tools/_claim_ledger_paperA.py` |
## P3 / A23 / Commentary upgrade archives (2026-10-19 continuation)

| Claim | Archive | Script |
|---|---|---|
| P3 paired theory-vs-random interval (+11.5, CI [6.8,16.2]) and rank-boundary table | `outputs/analysis/p3_upgrade_analysis.json` | `tools/_p1343_p3_upgrade_analyses.py` |
| P3 AdaLoRA totals (-1468.15 / -757.30) | `outputs/analysis/_p458_adalora_lr0.0003.txt`, `_p458_adalora_lr0.001.txt` | archived runs |
| A23 adapted-encoder certificate (BioCLIP r=-0.35, OceanCLIP r=-0.56; threshold BA 0.13-0.50) | `outputs/analysis/a23_certificate_adapted.json` | `tools/_p1352_a23_certificate_adapted.py` |
| A23 generic-CLIP certificate negative control | `outputs/analysis/a23_certificate_control.json` | `tools/_p1344_a23_certificate_control.py` |
| A23 threshold transfer, 8 dense arms (BA 0.83 -> 0.25-0.67) | `outputs/analysis/a23_threshold_transfer.json` | `tools/_p1345_a23_threshold_transfer.py` |
| A23 threshold transfer, 12 arms (median 0.50) | `outputs/analysis/a23_threshold_transfer_extended.json` | `tools/_p1351_a23_extended_transfer.py` |
| Commentary reference library and checklist gate | `paper_review/refs_all.json`, `paper_review_prl/_refs_used.json` | `tools/_final_check_prl.py`, `tools/_p1349_fix_commentary_gates.py` |
| A1 interior-optimum monitoring (n=32 checkpoints, min-M regret 0.19, r(M)=-0.983) | `outputs/analysis/a1_monitor_interior.json` | `tools/_p1354_monitor_interior.py` |
| P3 local rank control (CLIP, ranks 4-64: CG 0.744-0.792, r(rank,CG) -0.43) | `outputs/analysis/p3_rank_local_control.json` | `tools/_p1358_p3_rank_control.py` |
| A1 interior-optimum v2 (2 backbones, 3 seeds, 10 epochs, sequential rules) | `outputs/analysis/a1_monitor_interior_v2.json` | `tools/_p1357_monitor_interior_v2.py` |
| P3 current-protocol re-run (r=5,6,16: ΔE −10.5/+115.0/+1235.0, E0=3921) | `outputs/analysis/p3_rerun_protocol.json` | `tools/_p1365_p3_rerun_protocol.py` |
## Round 5 local-upgrade archives (2026-10-20)

| Claim | Archive | Script |
|---|---|---|
| A1 early-stopping baselines (min-M 0.18 vs confidence 2.80-4.18, 60 checkpoints) | `outputs/analysis/a1_stopping_baselines_rules.json` | `tools/_p1369_a1_stopping_baselines.py`, `_p1375_a1_baseline_rules.py` |
| A1 per-epoch LoRA checkpoints (DTD, seed 42) | `outputs/analysis/a1_monitor_ckpt.json` + `outputs/a1_monitor_ckpt/` | `tools/_p1373_a1_ckpt_hook.py` |
| A23 order-preservation control (tau r=+0.85/+0.81 vs mass -0.35/-0.56) | `outputs/analysis/a23_tau_control.json` | `tools/_p1370_a23_tau_control.py` |
| A23 second acoustic corpus (UATD crops; out-of-distribution boundary) | `outputs/analysis/a23_uatd_domain.json` | `tools/_p1382_a23_uatd_domain.py` |
| P3 current-protocol full curve and seed check | `outputs/analysis/p3_rerun_analysis.json` | `tools/_p1378_p3_extra_analysis.py` |
| P3 extra ranks and second seed | `outputs/analysis/p3_rerun_extra.json` | `tools/_p1371_p3_extra_ranks.py` |
| P3 local Qwen2-VL-2B check (inconclusive: identical trajectories, rank not varying) | `outputs/analysis/p3_qwen2b_crossing.json` | `tools/_p1372_qwen2b_crossing.py` |
| A1 expanded monitoring set (20 runs/200 checkpoints; minM 1.70, last 1.32) | `outputs/analysis/a1_monitor_combined.json` | `tools/_p1398_a1_combined.py`, `_p1399_a1_combined_text.py` |
| A23 tau calibration (linear rescaling transfers the relation, Spearman 0.71-0.86) | `outputs/analysis/a23_tau_calibration.json` | `tools/_p1393_a23_tau_calibration.py` |
| P3 corrected Qwen2-VL-2B check (trainable 1.4/1.6M; dE -352/-288) | `outputs/analysis/p3_qwen2b_crossing_fixed.json` | `tools/_p1391_qwen2b_fixed.py` |

| A1 split-size diagnosis (large splits minM 0.58 vs last 0.52; small splits noise-dominated) | `outputs/analysis/a1_monitor_diagnosis.json`, `a1_monitor_split_diagnosis.json` | `tools/_p1402_a1_monitor_diagnosis.py`, `_p1404_a1_split_size.py` |
| `a1_monitor_trainmass.json` | A1 训练集 margin 监测（4 域 × 10 epoch） | `tools/_p1410_a1_trainmass.py` |
| `a1_monitor_bothtower.json` | A1 双塔 LoRA 监测（dtd/food101） | `tools/_p1411_a1_bothtower.py` |
| `a1_retrieval_monitor.json` | A1 检索监控（marine captions 400/137） | `tools/_p1412_a1_retrieval_monitor.py` |
| `a1_round1_analysis.json` | A1 Round-1 汇总（规则 regret / 省 epoch） | `tools/_p1434_a1_round1_analysis.py` |
| `a23_watertank_domain.json` | water-tank96 gap-surgery（OOD 边界） | `tools/_p1414_a23_watertank.py` |
| `a23_neval_sensitivity.json` | A23 n_eval 敏感性（32/64/128/256/all） | `tools/_p1415_a23_neval.py` |
| `paperA_ode_residuals.json` | Paper A ODE 拟合残差结构 | `tools/_p1440_paperA_ode_residuals.py` |
| `cross_paper_consistency.json` | 五稿共享数字/页数/DOI 一致性 | `tools/_p1442_cross_paper_consistency.py` |
| `staged_package_check.json` | 五个修回包独立编译 1:1 校验 | `tools/_p1444_staged_package_check.py` |
| `provenance_manifest.json` | 98 float → 脚本 → JSON 清单 | `tools/_p1428_provenance_gate.py` |
| `p3_rerun_seeds.json` / `p3_numsamples_ablation.json` | P3 补 seeds / 协议消融（进行中） | `tools/_p1416_p3_seeds.py` / `tools/_p1417_p3_numsamples.py` |
| `p3_seeds_combined.json` | P3 5-seed 合并 + 精确置换（p=0.008） | `tools/_p1448_p3_seeds_analysis.py` |
| `p3_rerun_seeds.json` | P3 新增 seed 原始记录（r5/r6 × 789/999/1024） | `tools/_p1416_p3_seeds.py` |
| `p3_numsamples_ablation.json` | P3 num-samples 消融（12/32/64） | `tools/_p1417_p3_numsamples.py` |
| `a1_monitor_bothtower.json` | A1 双塔 LoRA 逐 epoch 监控 | `tools/_p1411_a1_bothtower.py` |
| `a1_monitor_bothtower_analysis.json` | A1 双塔 regret 分析（两域均 0.0） | `tools/_p1452_a1_bothtower_analysis.py` |
| `tab:monitor_variants` | A1 附录：三类任务 × 四条选择规则 regret | `tools/_p1463_a1_monitoring_appendix.py` |
| `tab:watertank96` / `tab:neval` | A23 附录：water-tank96 OOD 探测 + 评测集大小 sweep | `tools/_p1461_a23_probes_appendix.py` |
| `tab:odefit` | Paper A 附录：按 family/site 的 ODE 拟合质量 | `tools/_p1462_paperA_ode_appendix.py` |
| Commentary ref `sun2026reading` | Commentary §3.2 评测伪影引用（arXiv:2603.09095）| `tools/_p1464_commentary_freshness.py` |
| `a23_neval_sensitivity.json`（v2） | A23 评测集分层重跑（67/134/268/536/1608） | `tools/_p1415_a23_neval.py` |
| 包修复脚本 | `--zip-exclude` / `--supplementary` / 清空重建 | `tools/_p1336_build_venue_package.py`, `tools/_p1445_rebuild_packages.py` |
| P3 补材修复 | longtable→table* + S14/S15 引用 | `tools/_p1470_p3_supp_fix.py` |
| `a1_monitor_frontier.json` | A1 risk–compute frontier（ε 网格） | `tools/_p1480_a1_frontier.py` |
| `a23_calib_lodo.json` | A23 leave-one-domain-out 校准 | `tools/_p1478_a23_lodo_calibration.py` |
| `p3_protocol_shift.json` | P3 r=5 在 n=12 的协议移动测量 | `tools/_p1476_p3_protocol_shift.py` |
| `docs/NEW_PAPER_IDEAS_2026-10-21.md` | 新论文提案 A–E（仅记录） | — |
| `docs/P3_RESUBMISSION_PLAN_2026-10-21.md` | P3 拒稿后改投方案（PRL 新投稿 + 备选 SCI） | — |
| S17 `tab:claims` | P3 claim-status 表（支持/不支持/边界） | `docs/P3_SOUNDNESS_HARDENING_2026-10-21.md`（计划）|
