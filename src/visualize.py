"""
Visualization tools — modality gap evolution charts

Generate charts:
1. Gap evolution curve over epochs (comparison of different LoRA configurations)
2. Per-layer Gap distribution heatmap
3. Line chart of missing ratio vs Gap shift
4. Gap vs Recall scatter plot + regression line
5. t-SNE visualization (embedding distribution before and after fine-tuning)
"""

import os
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from typing import Dict, List, Optional
from pathlib import Path

# CJK font settings
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


# ============================================================
# Fig 1: Gap evolution during training
# ============================================================

def plot_gap_evolution(
    gap_histories: Dict[str, List[Dict]],  # {exp_name: gap_history}
    save_path: str = "outputs/fig1_gap_evolution.png",
    figsize: tuple = (14, 10),
):
    """
    Plot the Gap evolution curves of different experiments

    gap_histories = {
        "LoRA r=4": [{"epoch": 0, "centroid_gap": 0.5, ...}, ...],
        "LoRA r=16": [...],
        ...
    }
    """
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    colors = plt.cm.viridis(np.linspace(0, 0.85, len(gap_histories)))

    metrics_plot = [
        ("centroid_gap", "Centroid Gap (||μ_I - μ_T||₂)", axes[0, 0]),
        ("distribution_gap", "Distribution Gap (W₂)", axes[0, 1]),
        ("cosine_separation", "Cosine Separation (pos - neg)", axes[1, 0]),
        ("mean_cosine_pos", "Mean Cosine Similarity (Positive)", axes[1, 1]),
    ]

    for (metric, ylabel, ax), color in zip(metrics_plot, colors):
        for (name, history), c in zip(gap_histories.items(), colors):
            epochs = [h["epoch"] for h in history]
            values = [h[metric] for h in history]
            ax.plot(epochs, values, 'o-', label=name, color=c, markersize=4, linewidth=1.5)

        ax.set_xlabel("Epoch", fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.legend(fontsize=8, loc='best')
        ax.grid(True, alpha=0.3)

    fig.suptitle("Modality Gap Evolution During LoRA Fine-tuning", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Fig 1 saved: {save_path}")


# ============================================================
# Fig 2: per-layer Gap heatmap
# ============================================================

def plot_layer_gap_heatmap(
    initial_gaps: Dict[str, float],   # {layer_name: gap_value} before fine-tuning
    final_gaps: Dict[str, float],     # {layer_name: gap_value} after fine-tuning
    save_path: str = "outputs/fig2_layer_gap.png",
    figsize: tuple = (12, 6),
):
    """
    Plot the per-layer Gap heatmap comparison before and after fine-tuning
    """
    layers = sorted(set(list(initial_gaps.keys()) + list(final_gaps.keys())))

    # build the matrix
    data = np.zeros((2, len(layers)))
    for i, layer in enumerate(layers):
        data[0, i] = initial_gaps.get(layer, 0)
        data[1, i] = final_gaps.get(layer, 0)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # heatmap
    im = ax1.imshow(data, cmap='RdYlBu_r', aspect='auto')
    ax1.set_xticks(range(len(layers)))
    ax1.set_xticklabels([l.split('_')[-1] for l in layers], rotation=45, fontsize=8)
    ax1.set_yticks([0, 1])
    ax1.set_yticklabels(["Before FT", "After FT"])
    ax1.set_title("Per-Layer Centroid Gap", fontsize=12)
    plt.colorbar(im, ax=ax1)

    # difference bar chart
    diffs = data[1] - data[0]
    colors_bar = ['#e74c3c' if d > 0 else '#3498db' for d in diffs]
    ax2.bar(range(len(layers)), diffs, color=colors_bar, alpha=0.8)
    ax2.axhline(y=0, color='black', linewidth=0.5)
    ax2.set_xticks(range(len(layers)))
    ax2.set_xticklabels([l.split('_')[-1] for l in layers], rotation=45, fontsize=8)
    ax2.set_ylabel("Δ Gap (After - Before)", fontsize=11)
    ax2.set_title("Gap Change Per Layer", fontsize=12)
    ax2.grid(True, alpha=0.3)

    fig.suptitle("Layer-wise Modality Gap Analysis", fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Fig 2 saved: {save_path}")


# ============================================================
# Fig 3: missing ratio vs Gap shift
# ============================================================

def plot_missing_modality_impact(
    missing_ratios: List[float],
    gap_shifts: Dict[str, List[float]],   # {metric: [shift_values]}
    save_path: str = "outputs/fig3_missing_impact.png",
    figsize: tuple = (10, 6),
):
    """
    Plot the relationship between missing ratio and Gap shift
    """
    fig, ax = plt.subplots(figsize=figsize)

    markers = ['o', 's', '^', 'D']
    for (metric, shifts), marker in zip(gap_shifts.items(), markers):
        ax.plot(missing_ratios, shifts, f'{marker}-', label=metric,
               markersize=8, linewidth=2)

    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax.set_xlabel("Missing Ratio", fontsize=12)
    ax.set_ylabel("Relative Gap Shift (ΔGap / Baseline)", fontsize=12)
    ax.set_title("Impact of Missing Modality on Gap Metrics", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Fig 3 saved: {save_path}")


# ============================================================
# Fig 4: Gap vs Task Performance scatter plot
# ============================================================

def plot_gap_vs_performance(
    gap_values: List[float],
    performance_values: List[float],
    gap_metric_name: str = "Distribution Gap",
    perf_metric_name: str = "Recall@1",
    save_path: str = "outputs/fig4_gap_vs_perf.png",
    figsize: tuple = (8, 6),
):
    """
    Plot the scatter plot of Gap vs downstream task performance + regression line
    """
    fig, ax = plt.subplots(figsize=figsize)

    gap_arr = np.array(gap_values)
    perf_arr = np.array(performance_values)

    # scatter
    ax.scatter(gap_arr, perf_arr, c='#3498db', alpha=0.6, s=60, edgecolors='white')

    # linear regression
    if len(gap_arr) >= 3:
        coeffs = np.polyfit(gap_arr, perf_arr, 1)
        x_fit = np.linspace(gap_arr.min(), gap_arr.max(), 100)
        y_fit = np.polyval(coeffs, x_fit)
        ax.plot(x_fit, y_fit, '--', color='#e74c3c', linewidth=2,
               label=f'y = {coeffs[0]:.4f}x + {coeffs[1]:.4f}')

        # Pearson correlation coefficient
        from scipy.stats import pearsonr
        r, p = pearsonr(gap_arr, perf_arr)
        ax.text(0.05, 0.95, f"Pearson r = {r:.3f}\np = {p:.4f}",
               transform=ax.transAxes, fontsize=11,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    ax.set_xlabel(gap_metric_name, fontsize=12)
    ax.set_ylabel(perf_metric_name, fontsize=12)
    ax.set_title(f"{gap_metric_name} vs {perf_metric_name}", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Fig 4 saved: {save_path}")


# ============================================================
# Fig 5: t-SNE Embedding visualization
# ============================================================

def plot_tsne_comparison(
    before_image_embeds: np.ndarray,    # (N, D)
    before_text_embeds: np.ndarray,      # (N, D)
    after_image_embeds: np.ndarray,      # (N, D)
    after_text_embeds: np.ndarray,       # (N, D)
    save_path: str = "outputs/fig5_tsne.png",
    figsize: tuple = (12, 5),
    sample_size: int = 1000,
):
    """
    t-SNE visualization: comparison of embedding distributions before and after fine-tuning
    """
    from sklearn.manifold import TSNE

    # sampling
    if len(before_image_embeds) > sample_size:
        indices = np.random.choice(len(before_image_embeds), sample_size, replace=False)
        before_image_embeds = before_image_embeds[indices]
        before_text_embeds = before_text_embeds[indices]
        after_image_embeds = after_image_embeds[indices]
        after_text_embeds = after_text_embeds[indices]

    # merge the four sets for t-SNE (keeping the global structure comparable)
    all_embeds = np.vstack([
        before_image_embeds, before_text_embeds,
        after_image_embeds, after_text_embeds,
    ])

    tsne = TSNE(n_components=2, perplexity=30, random_state=42, max_iter=1000)
    all_2d = tsne.fit_transform(all_embeds)

    n = len(before_image_embeds)
    bi, bt = all_2d[:n], all_2d[n:2*n]
    ai, at = all_2d[2*n:3*n], all_2d[3*n:]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Before
    ax1.scatter(bi[:, 0], bi[:, 1], c='#3498db', alpha=0.5, s=10, label='Image')
    ax1.scatter(bt[:, 0], bt[:, 1], c='#e74c3c', alpha=0.5, s=10, label='Text')
    ax1.set_title("Before Fine-tuning", fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10, markerscale=3)
    ax1.set_xticks([]); ax1.set_yticks([])

    # After
    ax2.scatter(ai[:, 0], ai[:, 1], c='#3498db', alpha=0.5, s=10, label='Image')
    ax2.scatter(at[:, 0], at[:, 1], c='#e74c3c', alpha=0.5, s=10, label='Text')
    ax2.set_title("After LoRA Fine-tuning", fontsize=13, fontweight='bold')
    ax2.legend(fontsize=10, markerscale=3)
    ax2.set_xticks([]); ax2.set_yticks([])

    fig.suptitle("t-SNE Visualization: Embedding Distribution Change", fontsize=14)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Fig 5 saved: {save_path}")


# ============================================================
# Comprehensive report generation
# ============================================================

def generate_report(
    experiment_results: Dict,
    save_dir: str = "outputs/",
):
    """
    Generate a comprehensive visualization report from all experiment results
    """
    os.makedirs(save_dir, exist_ok=True)

    # collect all gap histories
    gap_histories = {}
    for name, result in experiment_results.items():
        if "gap_history" in result:
            gap_histories[name] = result["gap_history"]

    # Fig 1: Gap evolution
    if gap_histories:
        plot_gap_evolution(
            gap_histories,
            save_path=os.path.join(save_dir, "fig1_gap_evolution.png"),
        )

    # Fig 4: Gap vs Performance
    for name, result in experiment_results.items():
        if result.get("gap_values") and result.get("performance_values"):
            plot_gap_vs_performance(
                result["gap_values"],
                result["performance_values"],
                save_path=os.path.join(save_dir, f"fig4_gap_vs_perf_{name}.png"),
            )

    print(f"\n📊 Comprehensive report generated: {save_dir}")
