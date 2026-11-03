"""
模态差距 (Modality Gap) 度量工具集

指标说明:
1. Centroid Gap:   G_c = ||μ_I - μ_T||₂  （质心欧氏距离）
2. Distribution Gap: W₂² = ||μ_I - μ_T||² + ||σ_I - σ_T||²  （2-Wasserstein距离）
3. Cosine Stats:  正/负样本对余弦相似度分布统计
4. Positive Separation: 正样本相似度 - 最大负样本相似度的平均值
5. Per-Layer Gap: 逐层计算各指标

参考论文:
- MAAB-ER (Cheng et al., 2026, Information Fusion): 2-Wasserstein距离度量
- Understanding the Modality Gap in CLIP (Liang et al., 2022, ICLR)
- Geometry of the Modality Gap (2026)
"""

import torch
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class GapMetrics:
    """单次 Gap 度量结果"""
    epoch: int
    step: int
    centroid_gap: float                      # 质心距离
    distribution_gap: float                  # Wasserstein分布距离
    centroid_gap_norm: float                 # 归一化质心距离 (除以维度平方根)
    mean_cosine_pos: float                   # 正样本对平均余弦相似度
    mean_cosine_neg: float                   # 负样本对平均余弦相似度
    cosine_separation: float                 # 正负样本分离度 (pos - neg)
    std_cosine_pos: float                    # 正样本对余弦相似度标准差
    std_cosine_neg: float                    # 负样本对余弦相似度标准差
    per_layer: Optional[Dict[str, 'GapMetrics']] = None  # 逐层度量


class GapTracker:
    """
    模态差距跟踪器 — 贯穿训练过程记录gap变化

    用法:
        tracker = GapTracker()
        for epoch in range(num_epochs):
            ... training ...
            if epoch % gap_config.compute_every_n_epochs == 0:
                metrics = tracker.compute(image_embeds, text_embeds, epoch, step)
                tracker.record(metrics)
    """

    def __init__(self, sample_size: int = 5000, device: str = "mps"):
        self.sample_size = sample_size
        self.device = device
        self.history: List[GapMetrics] = []
        self.per_layer_history: Dict[str, List[GapMetrics]] = defaultdict(list)

    def compute(
        self,
        image_embeds: torch.Tensor,    # (N, D)
        text_embeds: torch.Tensor,      # (N, D)
        epoch: int = 0,
        step: int = 0,
        labels: Optional[torch.Tensor] = None,  # 正样本对索引 (N,)
    ) -> GapMetrics:
        """
        计算所有 gap 指标

        Args:
            image_embeds: 归一化后的图像嵌入
            text_embeds: 归一化后的文本嵌入
            labels: 如果为None，假设对角线是正样本对
        """
        # 归一化
        image_embeds = F.normalize(image_embeds, p=2, dim=-1)
        text_embeds = F.normalize(text_embeds, p=2, dim=-1)

        # 采样（数据量大时）
        if len(image_embeds) > self.sample_size:
            indices = torch.randperm(len(image_embeds))[:self.sample_size]
            image_embeds = image_embeds[indices]
            text_embeds = text_embeds[indices]

        N, D = image_embeds.shape

        # ---- 1. Centroid Gap ----
        mu_I = image_embeds.mean(dim=0)  # (D,)
        mu_T = text_embeds.mean(dim=0)    # (D,)
        centroid_gap = torch.norm(mu_I - mu_T, p=2).item()
        centroid_gap_norm = centroid_gap / np.sqrt(D)  # 除以√D归一化

        # ---- 2. Distribution Gap (2-Wasserstein) ----
        # 假设对角协方差矩阵: W₂² = ||μ_I-μ_T||² + ||σ_I-σ_T||²
        sigma_I = image_embeds.std(dim=0)  # (D,)
        sigma_T = text_embeds.std(dim=0)    # (D,)
        dist_gap = (centroid_gap ** 2 + torch.norm(sigma_I - sigma_T, p=2).item() ** 2) ** 0.5

        # ---- 3. 余弦相似度统计 ----
        # 计算所有图像-文本对的余弦相似度矩阵
        # logits: (N, N), logits[i,j] = image_i · text_j
        logits = image_embeds @ text_embeds.T  # (N, N)

        if labels is None:
            # 默认对角线是正样本
            pos_mask = torch.eye(N, device=logits.device, dtype=torch.bool)
            neg_mask = ~pos_mask
        else:
            pos_mask = torch.zeros(N, N, device=logits.device, dtype=torch.bool)
            pos_mask[torch.arange(N), labels] = True
            neg_mask = ~pos_mask

        pos_sims = logits[pos_mask]
        neg_sims = logits[neg_mask]

        mean_cosine_pos = pos_sims.mean().item()
        mean_cosine_neg = neg_sims.mean().item()
        std_cosine_pos = pos_sims.std().item()
        std_cosine_neg = neg_sims.std().item()
        cosine_separation = mean_cosine_pos - mean_cosine_neg

        return GapMetrics(
            epoch=epoch,
            step=step,
            centroid_gap=centroid_gap,
            distribution_gap=dist_gap,
            centroid_gap_norm=centroid_gap_norm,
            mean_cosine_pos=mean_cosine_pos,
            mean_cosine_neg=mean_cosine_neg,
            cosine_separation=cosine_separation,
            std_cosine_pos=std_cosine_pos,
            std_cosine_neg=std_cosine_neg,
        )

    def compute_per_layer(
        self,
        layer_image_embeds: Dict[str, torch.Tensor],
        layer_text_embeds: Dict[str, torch.Tensor],
        epoch: int = 0,
        step: int = 0,
    ) -> Dict[str, GapMetrics]:
        """逐层计算 gap 指标"""
        per_layer = {}
        for layer_name in layer_image_embeds:
            if layer_name in layer_text_embeds:
                per_layer[layer_name] = self.compute(
                    layer_image_embeds[layer_name],
                    layer_text_embeds[layer_name],
                    epoch, step,
                )
        return per_layer

    def record(self, metrics: GapMetrics):
        """记录一次度量结果"""
        self.history.append(metrics)

        if metrics.per_layer:
            for layer_name, layer_metrics in metrics.per_layer.items():
                self.per_layer_history[layer_name].append(layer_metrics)

    def get_history_dict(self) -> Dict[str, List[float]]:
        """以字典形式返回历史记录（方便pandas/matplotlib使用）"""
        return {
            "epoch": [m.epoch for m in self.history],
            "centroid_gap": [m.centroid_gap for m in self.history],
            "distribution_gap": [m.distribution_gap for m in self.history],
            "centroid_gap_norm": [m.centroid_gap_norm for m in self.history],
            "mean_cosine_pos": [m.mean_cosine_pos for m in self.history],
            "mean_cosine_neg": [m.mean_cosine_neg for m in self.history],
            "cosine_separation": [m.cosine_separation for m in self.history],
        }


# ============================================================
# 批量分析工具
# ============================================================

def gap_correlation_analysis(
    gap_history: List[GapMetrics],
    task_performance: List[float],  # 对应每个epoch的Recall@K
) -> Dict[str, float]:
    """
    分析 gap 指标与下游任务性能的相关性

    Returns:
        {metric_name: pearson_correlation}
    """
    from scipy.stats import pearsonr

    metrics_dict = {}
    for m in gap_history:
        if not hasattr(metrics_dict, '_initialized'):
            metrics_dict = {
                "centroid_gap": [],
                "distribution_gap": [],
                "cosine_separation": [],
                "mean_cosine_pos": [],
            }
        metrics_dict["centroid_gap"].append(m.centroid_gap)
        metrics_dict["distribution_gap"].append(m.distribution_gap)
        metrics_dict["cosine_separation"].append(m.cosine_separation)
        metrics_dict["mean_cosine_pos"].append(m.mean_cosine_pos)

    correlations = {}
    for key, values in metrics_dict.items():
        if len(values) >= 5:  # 至少需要5个数据点
            r, p = pearsonr(values, task_performance)
            correlations[key] = r
            correlations[f"{key}_pvalue"] = p

    return correlations


def gap_shift_analysis(
    baseline_metrics: GapMetrics,
    missing_metrics: GapMetrics,
) -> Dict[str, float]:
    """
    分析缺失模态下的 gap 偏移

    Returns:
        {metric_name: relative_shift}  (相对于baseline的相对变化)
    """
    shifts = {}
    for attr in ["centroid_gap", "distribution_gap", "cosine_separation"]:
        baseline_val = getattr(baseline_metrics, attr)
        missing_val = getattr(missing_metrics, attr)
        if baseline_val != 0:
            shifts[f"{attr}_shift"] = (missing_val - baseline_val) / baseline_val
        else:
            shifts[f"{attr}_shift"] = float('inf')
    return shifts
