# -*- coding: utf-8 -*-
"""
Verification gate for docs/PR_STATS_FIX.md.

Each claim below NAMES (a) the JSON file and (b) the exact field path that carries the
number, and asserts that the number rendered from that field actually appears in the
report -- inside a local window around a named context string, NOT by a global fuzzy
search over the whole document.

Why the context window: this project has already been burned once by a fuzzy-matching
"gate" (tools/_reproducibility_gate.py) that passed 145/145 by searching 122,161
archived numbers at 0.5% tolerance -- a pure artefact.  A global `if s in doc` check
has the same defect.  Requiring the number to sit near its own named context makes the
check falsifiable.

Run:  python tools/_p261_verify_pr_stats_report.py
Exit: 0 if every claim verifies, 1 otherwise.
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, "docs", "PR_STATS_FIX.md")
A = os.path.join(ROOT, "outputs", "analysis")

FILES = {
    "hardened": os.path.join(A, "pr_stats_hardened.json"),
    "within": os.path.join(A, "pr_stats_within_group.json"),
    "mixed": os.path.join(A, "pr_stats_mixed_effects.json"),
    "boot": os.path.join(A, "pr_stats_cluster_bootstrap.json"),
    "holdout": os.path.join(A, "pr_stats_holdout.json"),
}
WINDOW = 800


def get(obj, path):
    """Dotted path with [i] indices."""
    cur = obj
    for tok in path.split("."):
        m = re.match(r"^([^\[]*)((?:\[\d+\])*)$", tok)
        name, idxs = m.group(1), m.group(2)
        if name:
            cur = cur[name]
        for i in re.findall(r"\[(\d+)\]", idxs):
            cur = cur[int(i)]
    return cur


# (label, file_key, field path, format spec, context string that must sit near it)
CLAIMS = [
    # ---- provenance / reproduction -----------------------------------------
    ("pooled r reproduces the manuscript value", "hardened", "verdict.pooled_r", ".4f", "汇合（稿件现值）"),
    ("pooled R^2", "hardened", "verdict.pooled_r2", ".4f", "样本内（对照）"),
    ("naive Fisher CI lower", "hardened", "verdict.pooled_naive_ci[0]", ".4f", "汇合（稿件现值）"),
    ("naive Fisher CI upper", "hardened", "verdict.pooled_naive_ci[1]", ".4f", "汇合（稿件现值）"),
    ("n rows", "hardened", "n_rows", "d", "n = 204"),
    ("recheck: 204 rows, 0 mismatches", "hardened", "provenance.recheck", "mismatches0", "独立重推校验"),

    # ---- 1.3 design cells ---------------------------------------------------
    ("largest design cell share", "hardened", "verdict.largest_cell_share", ".3f", "84.8"),
    ("n design cells", "hardened", "verdict.n_design_cells", "d", "设计单元（dataset | model）"),
    ("flickr30k|CLIP n", "hardened", "label_evidence.flickr30k|CLIP ViT-B/32.n_rows", "d", "flickr30k \\| CLIP ViT-B/32"),
    ("coco|CLIP n", "hardened", "label_evidence.coco|CLIP ViT-B/32.n_rows", "d", "coco \\| CLIP ViT-B/32"),
    ("flickr30k|BLIP n", "hardened", "label_evidence.flickr30k|BLIP.n_rows", "d", "flickr30k \\| BLIP"),
    ("flickr30k|SigLIP n", "hardened", "label_evidence.flickr30k|SigLIP.n_rows", "d", "flickr30k \\| SigLIP"),
    ("DISPUTED|CLIP n", "hardened", "label_evidence.DISPUTED|CLIP ViT-B/32.n_rows", "d", "DISPUTED \\| CLIP ViT-B/32"),
    ("UNDOCUMENTED|ViT-L n", "hardened", "label_evidence.UNDOCUMENTED|ViT-L.n_rows", "d", "UNDOCUMENTED \\| ViT-L"),

    # ---- 2.1 within-group ---------------------------------------------------
    ("within-family pooled r", "hardened", "verdict.within_family_r", ".4f", "组内汇聚（族内"),
    ("within-cell pooled r", "hardened", "verdict.within_cell_r", ".4f", "组内汇聚（设计单元内"),
    ("within-dataset pooled r", "within", "pooled_within_dataset.r_within", ".4f", "组内汇聚（数据集内"),
    ("within-model pooled r", "within", "pooled_within_model.r_within", ".4f", "组内汇聚（模型内"),
    ("within-family n_groups", "within", "pooled_within_family.n_groups", "d", "族内，11 组"),
    ("within-cell n_groups", "within", "pooled_within_design_cell.n_groups", "d", "设计单元内，5 单元"),
    ("flickr30k within-dataset r", "within", "by_dataset.flickr30k.r", "+.4f", "dataset = flickr30k"),
    ("coco within-dataset r", "within", "by_dataset.coco.r", "+.4f", "dataset = coco"),
    ("coco within-dataset p", "within", "by_dataset.coco.p", ".5f", "dataset = coco"),
    ("coco within-dataset CI lo", "within", "by_dataset.coco.ci95[0]", ".4f", "dataset = coco"),
    ("coco within-dataset CI hi", "within", "by_dataset.coco.ci95[1]", ".4f", "dataset = coco"),
    ("flickr30k within-dataset n", "within", "by_dataset.flickr30k.n", "d", "dataset = flickr30k"),
    ("CLIP within-model r", "within", "by_model.CLIP ViT-B/32.r", "+.4f", "model = **CLIP ViT-B/32**"),
    ("CLIP within-model n", "within", "by_model.CLIP ViT-B/32.n", "d", "model = **CLIP ViT-B/32**"),
    ("CLIP within-model CI lo", "within", "by_model.CLIP ViT-B/32.ci95[0]", ".4f", "model = **CLIP ViT-B/32**"),
    ("CLIP within-model CI hi", "within", "by_model.CLIP ViT-B/32.ci95[1]", ".4f", "model = **CLIP ViT-B/32**"),
    ("BLIP within-model r", "within", "by_model.BLIP.r", "+.4f", "model = BLIP"),
    ("BLIP within-model p", "within", "by_model.BLIP.p", ".4f", "model = BLIP"),
    ("SigLIP within-model r", "within", "by_model.SigLIP.r", "+.4f", "model = **SigLIP**"),
    ("SigLIP within-model p", "within", "by_model.SigLIP.p", ".4f", "model = **SigLIP**"),
    ("SigLIP within-model CI lo", "within", "by_model.SigLIP.ci95[0]", ".4f", "model = **SigLIP**"),
    ("SigLIP within-model CI hi", "within", "by_model.SigLIP.ci95[1]", ".4f", "model = **SigLIP**"),
    ("family route_c r", "within", "by_family.route_c.r", "+.4f", "`route_c`"),
    ("family blip2 r", "within", "by_family.blip2.r", "+.4f", "`blip2`"),
    ("family phase1 r", "within", "by_family.phase1.r", "+.4f", "`phase1`"),
    ("family theory r", "within", "by_family.theory.r", "+.4f", "`theory`"),
    ("family flickr30k_seeds r", "within", "by_family.flickr30k_seeds.r", "+.4f", "`flickr30k_seeds`"),
    ("family flickr30k r", "within", "by_family.flickr30k.r", "+.4f", "`flickr30k`"),
    ("family coco r", "within", "by_family.coco.r", "+.4f", "`coco`"),
    ("family route_d r", "within", "by_family.route_d.r", "+.4f", "`route_d`"),
    ("family route_e r", "within", "by_family.route_e.r", "+.4f", "`route_e`"),
    ("family siglip r", "within", "by_family.siglip.r", "+.4f", "`siglip`"),
    ("family imagenet_zs r", "within", "by_family.imagenet_zs.r", "+.4f", "`imagenet_zs`"),
    ("coco dataset nested: family coco r", "within", "by_family_within_dataset.coco.by_family.coco.r", "+.4f", "其内部"),
    ("coco dataset nested: theory r", "within", "by_family_within_dataset.coco.by_family.theory.r", "+.4f", "theory/coco` 族"),
    ("coco dataset nested: dataset r", "within", "by_family_within_dataset.coco.dataset_r", "+.4f", "coco 是最干净的例证"),

    # ---- 2.2 mixed effects + self test -------------------------------------
    ("REML self-test slope", "mixed", "self_test_reml.beta_slope", ".3f", "斜率复原"),
    ("REML self-test n", "mixed", "self_test_reml.n", "d", "自检设定：n=400"),
    ("REML self-test tau_ratio[0]", "mixed", "self_test_reml.tau_ratio[0]", ".3f", "比值 **["),
    ("REML self-test tau_ratio[1]", "mixed", "self_test_reml.tau_ratio[1]", ".3f", "比值 **["),
    ("REML self-test tau_ratio[2]", "mixed", "self_test_reml.tau_ratio[2]", ".3f", "比值 **["),
    ("REML self-test total ratio", "mixed", "self_test_reml.tau_total_ratio", ".3f", "总和比 **0.656**"),
    ("M1 beta", "mixed", "M1_random_intercept_config.beta_DG", "+.4f", "| M1 |"),
    ("M1 se", "mixed", "M1_random_intercept_config.se_DG", ".4f", "| M1 |"),
    ("M1 z", "mixed", "M1_random_intercept_config.z", ".3f", "| M1 |"),
    ("M1 p", "mixed", "M1_random_intercept_config.p_wald", ".2g", "| M1 |"),
    ("M1 icc", "mixed", "M1_random_intercept_config.icc_total_random", ".4f", "| M1 |"),
    ("M2 beta", "mixed", "M2_random_intercepts_family_config.beta_DG", "+.4f", "| M2 |"),
    ("M2 se", "mixed", "M2_random_intercepts_family_config.se_DG", ".4f", "| M2 |"),
    ("M2 z", "mixed", "M2_random_intercepts_family_config.z", ".3f", "| M2 |"),
    ("M2 p", "mixed", "M2_random_intercepts_family_config.p_wald", ".2g", "| M2 |"),
    ("M2 icc", "mixed", "M2_random_intercepts_family_config.icc_total_random", ".4f", "| M2 |"),
    ("M2 icc family", "mixed", "M2_random_intercepts_family_config.icc.levels[0]", ".4f", "| M2 |"),
    ("M2 icc config", "mixed", "M2_random_intercepts_family_config.icc.levels[1]", ".4f", "| M2 |"),
    ("M3 beta", "mixed", "M3_random_intercepts_dataset_model.beta_DG", "+.4f", "| M3 |"),
    ("M3 se", "mixed", "M3_random_intercepts_dataset_model.se_DG", ".4f", "| M3 |"),
    ("M3 z", "mixed", "M3_random_intercepts_dataset_model.z", ".3f", "| M3 |"),
    ("M3 p", "mixed", "M3_random_intercepts_dataset_model.p_wald", ".2g", "| M3 |"),
    ("M3 icc", "mixed", "M3_random_intercepts_dataset_model.icc_total_random", ".4f", "| M3 |"),
    ("M4 beta", "mixed", "M4_random_intercepts_dataset_model_config.beta_DG", "+.4f", "M4（任务指定）"),
    ("M4 se", "mixed", "M4_random_intercepts_dataset_model_config.se_DG", ".4f", "M4（任务指定）"),
    ("M4 z", "mixed", "M4_random_intercepts_dataset_model_config.z", ".3f", "M4（任务指定）"),
    ("M4 p", "mixed", "M4_random_intercepts_dataset_model_config.p_wald", ".3g", "M4（任务指定）"),
    ("M4 icc total", "mixed", "M4_random_intercepts_dataset_model_config.icc_total_random", ".4f", "M4（任务指定）"),
    ("M4 icc dataset", "mixed", "M4_random_intercepts_dataset_model_config.icc.levels[0]", ".4f", "分层 ICC"),
    ("M4 icc model", "mixed", "M4_random_intercepts_dataset_model_config.icc.levels[1]", ".4f", "分层 ICC"),
    ("M4 icc config", "mixed", "M4_random_intercepts_dataset_model_config.icc.levels[2]", ".4f", "分层 ICC"),
    ("M4 resid icc", "mixed", "M4_random_intercepts_dataset_model_config.icc.residual", ".4f", "分层 ICC"),
    ("M4 tau dataset", "mixed", "M4_random_intercepts_dataset_model_config.variance_components.levels[0]", ".4f", "M4 方差成分"),
    ("M4 tau model", "mixed", "M4_random_intercepts_dataset_model_config.variance_components.levels[1]", ".4f", "M4 方差成分"),
    ("M4 tau config", "mixed", "M4_random_intercepts_dataset_model_config.variance_components.levels[2]", ".4f", "M4 方差成分"),
    ("M4 resid var", "mixed", "M4_random_intercepts_dataset_model_config.variance_components.residual", ".4f", "M4 方差成分"),
    ("M4 intercept", "mixed", "M4_random_intercepts_dataset_model_config.beta_intercept", ".4f", "M4 方差成分"),
    ("M5 beta", "mixed", "M5_random_intercepts_dataset_model_family_config.beta_DG", "+.4f", "| M5 |"),
    ("M5 se", "mixed", "M5_random_intercepts_dataset_model_family_config.se_DG", ".4f", "| M5 |"),
    ("M5 z", "mixed", "M5_random_intercepts_dataset_model_family_config.z", ".3f", "| M5 |"),
    ("M5 p", "mixed", "M5_random_intercepts_dataset_model_family_config.p_wald", ".2g", "| M5 |"),
    ("M5 icc", "mixed", "M5_random_intercepts_dataset_model_family_config.icc_total_random", ".4f", "| M5 |"),
    ("M5 model icc is zero", "mixed", "M5_random_intercepts_dataset_model_family_config.icc.levels[1]", ".4f", "压到 0.0000"),
    ("OLS slope (all 204)", "hardened", "ols_slope_all", "+.4f", "OLS 斜率均为"),
    ("CR1 se_ols (cell)", "mixed", "cluster_robust_OLS.by_design_cell.se_ols", ".4f", "dataset × model** | **6**"),
    ("CR1 se_cr1 (cell)", "mixed", "cluster_robust_OLS.by_design_cell.se_cr1", ".4f", "dataset × model** | **6**"),
    ("CR1 inflation (cell)", "mixed", "cluster_robust_OLS.by_design_cell.se_inflation_vs_ols", ".2f", "dataset × model** | **6**"),
    ("CR1 p (cell, t5)", "mixed", "cluster_robust_OLS.by_design_cell.p_cr1_t_Gminus1", ".5f", "dataset × model** | **6**"),
    ("CR1 se_cr1 (family)", "mixed", "cluster_robust_OLS.by_family.se_cr1", ".4f", "| family | 12 |"),
    ("CR1 inflation (family)", "mixed", "cluster_robust_OLS.by_family.se_inflation_vs_ols", ".2f", "| family | 12 |"),
    ("CR1 p (family)", "mixed", "cluster_robust_OLS.by_family.p_cr1_t_Gminus1", ".6f", "| family | 12 |"),
    ("CR1 se_cr1 (config)", "mixed", "cluster_robust_OLS.by_config.se_cr1", ".4f", "| config | 125 |"),
    ("CR1 inflation (config)", "mixed", "cluster_robust_OLS.by_config.se_inflation_vs_ols", ".2f", "| config | 125 |"),
    ("CR1 p (config)", "mixed", "cluster_robust_OLS.by_config.p_cr1_t_Gminus1", ".1e", "| config | 125 |"),
    ("CR1 beta_DG", "mixed", "cluster_robust_OLS.by_design_cell.beta_DG", "+.4f", "OLS 斜率均为"),
    ("mixed sens: documented only n", "mixed", "sensitivity_subsets.documented_dataset_only.n", "d", "去掉未定论标签的 5 行"),
    ("mixed sens: documented only beta", "mixed", "sensitivity_subsets.documented_dataset_only.beta_DG", "+.4f", "去掉未定论标签的 5 行"),
    ("mixed sens: documented only se", "mixed", "sensitivity_subsets.documented_dataset_only.se_DG", ".4f", "去掉未定论标签的 5 行"),
    ("mixed sens: documented only icc", "mixed", "sensitivity_subsets.documented_dataset_only.icc_total_random", ".4f", "去掉未定论标签的 5 行"),
    ("mixed sens: drop route n", "mixed", "sensitivity_subsets.drop_route_cde.n", "d", "去掉 Route C/D/E 16 行"),
    ("mixed sens: drop route beta", "mixed", "sensitivity_subsets.drop_route_cde.beta_DG", "+.4f", "去掉 Route C/D/E 16 行"),
    ("mixed sens: drop route se", "mixed", "sensitivity_subsets.drop_route_cde.se_DG", ".4f", "去掉 Route C/D/E 16 行"),
    ("mixed sens: drop route icc", "mixed", "sensitivity_subsets.drop_route_cde.icc_total_random", ".4f", "去掉 Route C/D/E 16 行"),
    ("mixed sens: cell>=10 n", "mixed", "sensitivity_subsets.design_cells_n_ge_10.n", "d", "只留 n≥10 的设计单元"),
    ("mixed sens: cell>=10 beta", "mixed", "sensitivity_subsets.design_cells_n_ge_10.beta_DG", "+.4f", "只留 n≥10 的设计单元"),
    ("mixed sens: cell>=10 se", "mixed", "sensitivity_subsets.design_cells_n_ge_10.se_DG", ".4f", "只留 n≥10 的设计单元"),
    ("mixed sens: cell>=10 icc", "mixed", "sensitivity_subsets.design_cells_n_ge_10.icc_total_random", ".4f", "只留 n≥10 的设计单元"),

    # ---- 2.3 bootstrap ------------------------------------------------------
    ("boot seed", "boot", "seed", "d", "seed = 20261012"),
    ("boot n_boot", "boot", "n_boot", "d", "10000 次重抽"),
    ("naive boot r", "boot", "naive_row_bootstrap.r_mean", "+.4f", "朴素（按行重抽）"),
    ("naive boot n_clusters", "boot", "naive_row_bootstrap.n_clusters", "d", "朴素（按行重抽）"),
    ("naive boot CI lo", "boot", "naive_row_bootstrap.ci95[0]", ".4f", "朴素（按行重抽）"),
    ("naive boot CI hi", "boot", "naive_row_bootstrap.ci95[1]", ".4f", "朴素（按行重抽）"),
    ("naive boot width", "boot", "naive_row_bootstrap.ci_width", ".4f", "朴素（按行重抽）"),
    ("naive boot frac>=0", "boot", "naive_row_bootstrap.frac_r_ge_0", ".5f", "朴素（按行重抽）"),
    ("family boot r", "boot", "clustered_by_family.r_mean", "+.4f", "聚类（family）"),
    ("family boot n_clusters", "boot", "clustered_by_family.n_clusters", "d", "聚类（family）"),
    ("family boot CI lo", "boot", "clustered_by_family.ci95[0]", ".4f", "聚类（family）"),
    ("family boot CI hi", "boot", "clustered_by_family.ci95[1]", ".4f", "聚类（family）"),
    ("family boot width", "boot", "clustered_by_family.ci_width", ".4f", "聚类（family）"),
    ("family boot frac>=0", "boot", "clustered_by_family.frac_r_ge_0", ".5f", "聚类（family）"),
    ("cell boot r", "boot", "clustered_by_design_cell.r_mean", "+.4f", "聚类（dataset × model）"),
    ("cell boot n_clusters", "boot", "clustered_by_design_cell.n_clusters", "d", "聚类（dataset × model）"),
    ("cell boot CI lo", "boot", "clustered_by_design_cell.ci95[0]", ".4f", "聚类（dataset × model）"),
    ("cell boot CI hi", "boot", "clustered_by_design_cell.ci95[1]", ".4f", "聚类（dataset × model）"),
    ("cell boot width", "boot", "clustered_by_design_cell.ci_width", ".4f", "聚类（dataset × model）"),
    ("cell boot frac>=0", "boot", "clustered_by_design_cell.frac_r_ge_0", ".5f", "聚类（dataset × model）"),
    ("config boot r", "boot", "clustered_by_config.r_mean", "+.4f", "聚类（config）"),
    ("config boot n_clusters", "boot", "clustered_by_config.n_clusters", "d", "聚类（config）"),
    ("config boot CI lo", "boot", "clustered_by_config.ci95[0]", ".4f", "聚类（config）"),
    ("config boot CI hi", "boot", "clustered_by_config.ci95[1]", ".4f", "聚类（config）"),
    ("config boot width", "boot", "clustered_by_config.ci_width", ".4f", "聚类（config）"),
    ("config boot frac>=0", "boot", "clustered_by_config.frac_r_ge_0", ".5f", "聚类（config）"),
    ("widening cell vs naive", "boot", "widening_design_cell_vs_naive", ".2f", "聚类（dataset × model）"),
    ("widening family vs naive", "boot", "widening_family_vs_naive", ".2f", "聚类（family）"),

    # ---- 2.4 holdout --------------------------------------------------------
    ("in-sample R2", "holdout", "in_sample.r2", ".4f", "样本内（对照）"),
    ("in-sample n", "holdout", "in_sample.n", "d", "样本内（对照）"),
    ("LOFO family n_folds", "holdout", "leave_one_family_out.n_folds", "d", "留一 family"),
    ("LOFO family pooled R2", "holdout", "leave_one_family_out.r2_oos_pooled", "+.4f", "留一 family"),
    ("LOFO family median fold R2", "holdout", "leave_one_family_out.r2_oos_median_fold", "+.4f", "留一 family"),
    ("LOFO family frac positive", "holdout", "leave_one_family_out.frac_folds_r2_positive", "pct", "留一 family"),
    ("LOFO cell n_folds", "holdout", "leave_one_design_cell_out.n_folds", "d", "留一设计单元"),
    ("LOFO cell pooled R2", "holdout", "leave_one_design_cell_out.r2_oos_pooled", "+.4f", "留一设计单元"),
    ("LOFO cell median fold R2", "holdout", "leave_one_design_cell_out.r2_oos_median_fold", "+.4f", "留一设计单元"),
    ("LOFO cell frac positive", "holdout", "leave_one_design_cell_out.frac_folds_r2_positive", "pct", "留一设计单元"),
    ("LOCO config frac positive", "holdout", "leave_one_config_out.frac_folds_r2_positive", "pct", "留一 config"),
    ("LOCO config n_folds", "holdout", "leave_one_config_out.n_folds", "d", "留一 config"),
    ("LOCO config pooled R2", "holdout", "leave_one_config_out.r2_oos_pooled", "+.4f", "留一 config"),
    ("LOCO config median fold R2", "holdout", "leave_one_config_out.r2_oos_median_fold", "+.4f", "留一 config"),
    ("per-fold: flickr30k|CLIP n_test", "holdout", "leave_one_design_cell_out.folds[4].n_test", "d", "flickr30k \\| CLIP ViT-B/32 | 173"),
    ("per-fold: flickr30k|CLIP slope", "holdout", "leave_one_design_cell_out.folds[4].slope", "+.4f", "flickr30k \\| CLIP ViT-B/32 | 173"),
    ("per-fold: flickr30k|CLIP R2", "holdout", "leave_one_design_cell_out.folds[4].r2_oos", "+.4f", "flickr30k \\| CLIP ViT-B/32 | 173"),
    ("per-fold: coco|CLIP slope", "holdout", "leave_one_design_cell_out.folds[2].slope", "+.4f", "coco \\| CLIP ViT-B/32 | 16"),
    ("per-fold: coco|CLIP R2", "holdout", "leave_one_design_cell_out.folds[2].r2_oos", "+.4f", "coco \\| CLIP ViT-B/32 | 16"),
    ("per-fold: BLIP slope", "holdout", "leave_one_design_cell_out.folds[3].slope", "+.4f", "flickr30k \\| BLIP | 5"),
    ("per-fold: BLIP R2", "holdout", "leave_one_design_cell_out.folds[3].r2_oos", "+.4f", "flickr30k \\| BLIP | 5"),
    ("per-fold: SigLIP slope", "holdout", "leave_one_design_cell_out.folds[5].slope", "+.4f", "flickr30k \\| SigLIP | 5"),
    ("per-fold: SigLIP R2", "holdout", "leave_one_design_cell_out.folds[5].r2_oos", "+.3f", "flickr30k \\| SigLIP | 5"),
    ("per-fold: DISPUTED slope", "holdout", "leave_one_design_cell_out.folds[0].slope", "+.4f", "DISPUTED \\| CLIP ViT-B/32 | 3"),
    ("per-fold: DISPUTED R2", "holdout", "leave_one_design_cell_out.folds[0].r2_oos", "+.4f", "DISPUTED \\| CLIP ViT-B/32 | 3"),
    ("per-fold: ViT-L slope", "holdout", "leave_one_design_cell_out.folds[1].slope", "+.4f", "UNDOCUMENTED \\| ViT-L | 2"),
    ("per-fold: ViT-L R2", "holdout", "leave_one_design_cell_out.folds[1].r2_oos", "+.4f", "UNDOCUMENTED \\| ViT-L | 2"),

    # ---- 2.5 Mundlak --------------------------------------------------------
    ("Mundlak cell G", "hardened", "mundlak_within_between[0].n_groups", "d", "dataset × model** | 6"),
    ("Mundlak cell within beta", "hardened", "mundlak_within_between[0].beta_within", "+.4f", "dataset × model** | 6"),
    ("Mundlak cell within p", "hardened", "mundlak_within_between[0].p_within", ".4f", "dataset × model** | 6"),
    ("Mundlak cell between beta", "hardened", "mundlak_within_between[0].beta_between", "+.4f", "dataset × model** | 6"),
    ("Mundlak cell between p", "hardened", "mundlak_within_between[0].p_between", ".4f", "dataset × model** | 6"),
    ("Mundlak family G", "hardened", "mundlak_within_between[1].n_groups", "d", "| family | 12 |"),
    ("Mundlak family within beta", "hardened", "mundlak_within_between[1].beta_within", "+.4f", "| family | 12 |"),
    ("Mundlak family within p", "hardened", "mundlak_within_between[1].p_within", ".5f", "| family | 12 |"),
    ("Mundlak family between beta", "hardened", "mundlak_within_between[1].beta_between", "+.4f", "| family | 12 |"),
    ("Mundlak family between p", "hardened", "mundlak_within_between[1].p_between", ".6f", "| family | 12 |"),
    ("Mundlak config within beta", "hardened", "mundlak_within_between[2].beta_within", "+.4f", "| config | 125 |"),
    ("Mundlak config within p", "hardened", "mundlak_within_between[2].p_within", ".3f", "| config | 125 |"),
    ("Mundlak config between beta", "hardened", "mundlak_within_between[2].beta_between", "+.4f", "| config | 125 |"),
    ("Mundlak config between p", "hardened", "mundlak_within_between[2].p_between", ".2e", "| config | 125 |"),
    ("Mundlak config>=2 G", "hardened", "mundlak_within_between[5].n_groups", "d", "config（仅 n≥2 的 35 组"),
    ("Mundlak config>=2 n_rows", "hardened", "mundlak_within_between[5].n_rows", "d", "config（仅 n≥2 的 35 组"),
    ("Mundlak config>=2 within beta", "hardened", "mundlak_within_between[5].beta_within", "+.4f", "config（仅 n≥2 的 35 组"),
    ("Mundlak config>=2 within p", "hardened", "mundlak_within_between[5].p_within", ".3f", "config（仅 n≥2 的 35 组"),
    ("Mundlak config>=2 between beta", "hardened", "mundlak_within_between[5].beta_between", "+.4f", "config（仅 n≥2 的 35 组"),
    ("Mundlak config>=2 between p", "hardened", "mundlak_within_between[5].p_between", ".2e", "config（仅 n≥2 的 35 组"),

    # ---- 2.6 design effect --------------------------------------------------
    ("DE cell n_clusters", "hardened", "design_effect.design_cell.n_clusters", "d", "dataset × model** | **6**"),
    ("DE cell mean size", "hardened", "design_effect.design_cell.mean_cluster_size", ".1f", "dataset × model** | **6**"),
    ("DE cell icc_dataset", "hardened", "design_effect.design_cell.icc_dataset", ".4f", "dataset × model** | **6**"),
    ("DE cell icc_model", "hardened", "design_effect.design_cell.icc_model", ".4f", "dataset × model** | **6**"),
    ("DE cell icc_cell", "hardened", "design_effect.design_cell.icc_cell", ".4f", "dataset × model** | **6**"),
    ("DE cell design effect", "hardened", "design_effect.design_cell.design_effect", ".2f", "dataset × model** | **6**"),
    ("DE cell effective n", "hardened", "design_effect.design_cell.effective_n", ".2f", "dataset × model** | **6**"),
    ("DE family n_clusters", "hardened", "design_effect.family.n_clusters", "d", "| family | 12 |"),
    ("DE family mean size", "hardened", "design_effect.family.mean_cluster_size", ".1f", "| family | 12 |"),
    ("DE family icc", "hardened", "design_effect.family.icc_family", ".4f", "| family | 12 |"),
    ("DE family design effect", "hardened", "design_effect.family.design_effect", ".2f", "| family | 12 |"),
    ("DE family effective n", "hardened", "design_effect.family.effective_n", ".2f", "| family | 12 |"),

    # ---- 2.7 sensitivity ----------------------------------------------------
    ("S1 n", "hardened", "sensitivity.S1_all_204.n", "d", "S1 全部 204 行"),
    ("S1 r", "hardened", "sensitivity.S1_all_204.r", "+.4f", "S1 全部 204 行"),
    ("S1 CI lo", "hardened", "sensitivity.S1_all_204.fisher_ci95[0]", ".4f", "S1 全部 204 行"),
    ("S1 CI hi", "hardened", "sensitivity.S1_all_204.fisher_ci95[1]", ".4f", "S1 全部 204 行"),
    ("S1 R2", "hardened", "sensitivity.S1_all_204.r2", ".4f", "S1 全部 204 行"),
    ("S2 n", "hardened", "sensitivity.S2_drop_route_d.n", "d", "S2 剔除 Route D"),
    ("S2 r", "hardened", "sensitivity.S2_drop_route_d.r", "+.4f", "S2 剔除 Route D"),
    ("S2 CI lo", "hardened", "sensitivity.S2_drop_route_d.fisher_ci95[0]", ".4f", "S2 剔除 Route D"),
    ("S2 CI hi", "hardened", "sensitivity.S2_drop_route_d.fisher_ci95[1]", ".4f", "S2 剔除 Route D"),
    ("S2 R2", "hardened", "sensitivity.S2_drop_route_d.r2", ".4f", "S2 剔除 Route D"),
    ("S3 n", "hardened", "sensitivity.S3_drop_route_cde.n", "d", "S3 剔除 Route C/D/E"),
    ("S3 r", "hardened", "sensitivity.S3_drop_route_cde.r", "+.4f", "S3 剔除 Route C/D/E"),
    ("S3 CI lo", "hardened", "sensitivity.S3_drop_route_cde.fisher_ci95[0]", ".4f", "S3 剔除 Route C/D/E"),
    ("S3 CI hi", "hardened", "sensitivity.S3_drop_route_cde.fisher_ci95[1]", ".4f", "S3 剔除 Route C/D/E"),
    ("S3 R2", "hardened", "sensitivity.S3_drop_route_cde.r2", ".4f", "S3 剔除 Route C/D/E"),
    ("S4 n", "hardened", "sensitivity.S4_cell_ge_10.n", "d", "S4 只留 n≥10"),
    ("S4 r", "hardened", "sensitivity.S4_cell_ge_10.r", "+.4f", "S4 只留 n≥10"),
    ("S4 CI lo", "hardened", "sensitivity.S4_cell_ge_10.fisher_ci95[0]", ".4f", "S4 只留 n≥10"),
    ("S4 CI hi", "hardened", "sensitivity.S4_cell_ge_10.fisher_ci95[1]", ".4f", "S4 只留 n≥10"),
    ("S4 R2", "hardened", "sensitivity.S4_cell_ge_10.r2", ".4f", "S4 只留 n≥10"),
    ("S5 n", "hardened", "sensitivity.S5_documented_dataset_only.n", "d", "S5 剔除未定论标签"),
    ("S5 r", "hardened", "sensitivity.S5_documented_dataset_only.r", "+.4f", "S5 剔除未定论标签"),
    ("S5 CI lo", "hardened", "sensitivity.S5_documented_dataset_only.fisher_ci95[0]", ".4f", "S5 剔除未定论标签"),
    ("S5 CI hi", "hardened", "sensitivity.S5_documented_dataset_only.fisher_ci95[1]", ".4f", "S5 剔除未定论标签"),
    ("S5 R2", "hardened", "sensitivity.S5_documented_dataset_only.r2", ".4f", "S5 剔除未定论标签"),

    # ---- verdict / limitation ----------------------------------------------
    ("verdict effective n cell", "hardened", "verdict.effective_n_cell", ".2f", "有效样本量"),
    ("verdict cr1 se cell", "hardened", "verdict.cr1_se_design_cell", ".4f", "CR1 标准误"),
    ("verdict cr1 p cell", "hardened", "verdict.cr1_p_design_cell_t5", ".4f", "CR1 标准误"),
    ("verdict cr1 beta", "hardened", "verdict.cr1_beta_DG", "+.4f", "OLS 斜率均为"),
    ("verdict clustered CI family lo", "hardened", "verdict.clustered_ci_family[0]", ".3f", "family-clustered bootstrap"),
    ("verdict clustered CI family hi", "hardened", "verdict.clustered_ci_family[1]", ".3f", "family-clustered bootstrap"),
    ("verdict oos median fold cell", "hardened", "verdict.oos_r2_cell_median_fold", ".4f", "设计效应"),
    ("verdict within dataset flickr30k", "hardened", "verdict.within_dataset.flickr30k", "+.4f", "within_dataset"),
    ("verdict within model CLIP", "hardened", "verdict.within_model.CLIP ViT-B/32", "+.4f", "within_model"),
]

# narrative numbers that must appear verbatim in the limitation sentence section
NARRATIVE = [
    ("limitation: slope", "-1.05", "英文（建议直接采用）"),
    ("limitation: CR1 se", "0.29", "英文（建议直接采用）"),
    ("limitation: p", "0.016", "英文（建议直接采用）"),
    ("limitation: CI lo", "-0.887", "英文（建议直接采用）"),
    ("limitation: CI hi", "-0.615", "英文（建议直接采用）"),
    ("limitation: 173", "173", "英文（建议直接采用）"),
    ("limitation: 84.8", "84.8", "英文（建议直接采用）"),
    ("limitation: 192", "192", "英文（建议直接采用）"),
    ("limitation: 94.1", "94.1", "英文（建议直接采用）"),
    ("limitation: DE 23", "23", "英文（建议直接采用）"),
    ("limitation: effective n 9", "9", "英文（建议直接采用）"),
    ("verdict association not prediction", "association", "判决：association 还是 predictive"),
    ("statsmodels missing", "ModuleNotFoundError", "statsmodels` 在本环境不可用"),
    ("no dataset field in results.json", "没有 `dataset`、没有 `model`、没有 `config`", "归档里没有这些字段"),
    ("input producer named in doc", "p1_dg_r1_recompute.py", "1.1 数据来源链"),
]


def check_context(doc, needle, context):
    """True iff `needle` occurs within WINDOW chars of some occurrence of `context`."""
    for m in re.finditer(re.escape(context), doc):
        lo = max(0, m.start() - WINDOW)
        hi = min(len(doc), m.end() + WINDOW)
        if needle in doc[lo:hi]:
            return True
    return False


def main():
    with io.open(DOC, encoding="utf-8") as fh:
        raw = fh.read()
    # normalise the typographic minus / en-dash / nbsp that the report uses
    doc = (raw.replace("\u2212", "-").replace("\u2013", "-")
              .replace("\u2014", "-").replace("\u00a0", " "))

    data = {}
    for k, p in FILES.items():
        assert os.path.exists(p), "missing artefact %s" % p
        with io.open(p, encoding="utf-8") as fh:
            data[k] = json.load(fh)

    fails = []
    for label, key, path, spec, ctx in CLAIMS:
        try:
            val = get(data[key], path)
        except (KeyError, IndexError, TypeError) as e:
            fails.append("%-46s FIELD MISSING %s (%s)" % (label, path, e))
            continue
        try:
            if spec == "s":
                rendered = str(val)
            elif spec == "d":
                rendered = "%d" % int(val)
            elif spec == "pct":
                rendered = "%d%%" % int(round(100.0 * float(val)))
            elif spec == "mismatches0":
                s = str(val)
                assert "(0 mismatches)" in s, (
                    "provenance.recheck no longer reports zero mismatches: %r" % s)
                rendered = "0 处不符"
            else:
                rendered = format(float(val), spec)
        except (TypeError, ValueError) as e:
            fails.append("%-46s FORMAT ERROR %r (%s)" % (label, val, e))
            continue
        if rendered not in doc:
            fails.append("%-46s NUMBER NOT IN DOC: %r  (%s :: %s)"
                         % (label, rendered, key, path))
        elif not check_context(doc, rendered, ctx):
            fails.append("%-46s NUMBER NOT NEAR CONTEXT %r: %r  (%s :: %s)"
                         % (label, ctx, rendered, key, path))

    for label, needle, ctx in NARRATIVE:
        if needle not in doc:
            fails.append("%-46s NARRATIVE MISSING: %r" % (label, needle))
        elif not check_context(doc, needle, ctx):
            fails.append("%-46s NARRATIVE NOT NEAR CONTEXT %r: %r"
                         % (label, ctx, needle))

    total = len(CLAIMS) + len(NARRATIVE)
    print("checked %d claims (%d field-bound + %d narrative) against %s"
          % (total, len(CLAIMS), len(NARRATIVE), os.path.relpath(DOC, ROOT)))
    if fails:
        print("\nFAILED %d/%d:" % (len(fails), total))
        for f in fails:
            print("  " + f)
        return 1
    print("ALL %d CLAIMS VERIFIED — every number in the report is bound to a named "
          "JSON file + field." % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
