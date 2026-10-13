"""
Modality Gap measurement toolkit

Metric descriptions:
1. Centroid Gap:   G_c = ||μ_I - μ_T||₂  (centroid Euclidean distance)
2. Distribution Gap: W₂² = ||μ_I - μ_T||² + ||σ_I - σ_T||²  (2-Wasserstein distance)
3. Cosine Stats:  statistics of the cosine similarity distribution for positive/negative sample pairs
4. Positive Separation: mean of (positive sample similarity - largest negative sample similarity)
5. Per-Layer Gap: compute each metric layer by layer

Reference papers:
- MAAB-ER (Cheng et al., 2026, Information Fusion): 2-Wasserstein distance metric
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
    """Result of a single Gap measurement"""
    epoch: int
    step: int
    centroid_gap: float                      # centroid distance
    distribution_gap: float                  # Wasserstein distribution distance
    centroid_gap_norm: float                 # normalized centroid distance (divided by sqrt of dimension)
    mean_cosine_pos: float                   # mean cosine similarity of positive sample pairs
    mean_cosine_neg: float                   # mean cosine similarity of negative sample pairs
    cosine_separation: float                 # positive-negative sample separation (pos - neg)
    std_cosine_pos: float                    # std of cosine similarity of positive sample pairs
    std_cosine_neg: float                    # std of cosine similarity of negative sample pairs
    per_layer: Optional[Dict[str, 'GapMetrics']] = None  # per-layer measurements


class GapTracker:
    """
    Modality gap tracker — records gap changes throughout the training process

    Usage:
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
        labels: Optional[torch.Tensor] = None,  # positive sample pair indices (N,)
    ) -> GapMetrics:
        """
        Compute all gap metrics

        Args:
            image_embeds: normalized image embeddings
            text_embeds: normalized text embeddings
            labels: if None, assume the diagonal holds the positive sample pairs
        """
        # normalize
        image_embeds = F.normalize(image_embeds, p=2, dim=-1)
        text_embeds = F.normalize(text_embeds, p=2, dim=-1)

        # sampling (when the data volume is large)
        if len(image_embeds) > self.sample_size:
            indices = torch.randperm(len(image_embeds))[:self.sample_size]
            image_embeds = image_embeds[indices]
            text_embeds = text_embeds[indices]

        N, D = image_embeds.shape

        # ---- 1. Centroid Gap ----
        mu_I = image_embeds.mean(dim=0)  # (D,)
        mu_T = text_embeds.mean(dim=0)    # (D,)
        centroid_gap = torch.norm(mu_I - mu_T, p=2).item()
        centroid_gap_norm = centroid_gap / np.sqrt(D)  # normalize by dividing by √D

        # ---- 2. Distribution Gap (2-Wasserstein) ----
        # assume a diagonal covariance matrix: W₂² = ||μ_I-μ_T||² + ||σ_I-σ_T||²
        sigma_I = image_embeds.std(dim=0)  # (D,)
        sigma_T = text_embeds.std(dim=0)    # (D,)
        dist_gap = (centroid_gap ** 2 + torch.norm(sigma_I - sigma_T, p=2).item() ** 2) ** 0.5

        # ---- 3. Cosine similarity statistics ----
        # compute the cosine similarity matrix over all image-text pairs
        # logits: (N, N), logits[i,j] = image_i · text_j
        logits = image_embeds @ text_embeds.T  # (N, N)

        if labels is None:
            # by default the diagonal holds the positive samples
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
        """Compute gap metrics layer by layer"""
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
        """Record one measurement result"""
        self.history.append(metrics)

        if metrics.per_layer:
            for layer_name, layer_metrics in metrics.per_layer.items():
                self.per_layer_history[layer_name].append(layer_metrics)

    def get_history_dict(self) -> Dict[str, List[float]]:
        """Return the history as a dict (convenient for pandas/matplotlib)"""
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
# Batch analysis tools
# ============================================================

def gap_correlation_analysis(
    gap_history: List[GapMetrics],
    task_performance: List[float],  # Recall@K corresponding to each epoch
) -> Dict[str, float]:
    """
    Analyze the correlation between gap metrics and downstream task performance

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
        if len(values) >= 5:  # at least 5 data points are required
            r, p = pearsonr(values, task_performance)
            correlations[key] = r
            correlations[f"{key}_pvalue"] = p

    return correlations


def gap_shift_analysis(
    baseline_metrics: GapMetrics,
    missing_metrics: GapMetrics,
) -> Dict[str, float]:
    """
    Analyze the gap shift under missing modalities

    Returns:
        {metric_name: relative_shift}  (relative change with respect to baseline)
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
