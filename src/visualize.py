"""
可视化工具 — 模态差距演化图表

生成图表:
1. Gap随epoch演化曲线（不同LoRA配置对比）
2. 逐层Gap分布热力图
3. 缺失比例 vs Gap偏移的折线图
4. Gap vs Recall 散点图 + 回归线
5. t-SNE可视化（微调前后的embedding分布）
"""

import os
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 非交互后端
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from typing import Dict, List, Optional
from pathlib import Path

# 中文字体设置
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


# ============================================================
# 图1: Gap 随训练演化
# ============================================================

def plot_gap_evolution(
    gap_histories: Dict[str, List[Dict]],  # {exp_name: gap_history}
    save_path: str = "outputs/fig1_gap_evolution.png",
    figsize: tuple = (14, 10),
):
    """
    绘制不同实验的Gap演化曲线

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
    print(f"✅ 图1 已保存: {save_path}")


# ============================================================
# 图2: 逐层Gap热力图
# ============================================================

def plot_layer_gap_heatmap(
    initial_gaps: Dict[str, float],   # {layer_name: gap_value} 微调前
    final_gaps: Dict[str, float],     # {layer_name: gap_value} 微调后
    save_path: str = "outputs/fig2_layer_gap.png",
    figsize: tuple = (12, 6),
):
    """
    绘制微调前后的逐层Gap热力图对比
    """
    layers = sorted(set(list(initial_gaps.keys()) + list(final_gaps.keys())))

    # 构建矩阵
    data = np.zeros((2, len(layers)))
    for i, layer in enumerate(layers):
        data[0, i] = initial_gaps.get(layer, 0)
        data[1, i] = final_gaps.get(layer, 0)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # 热力图
    im = ax1.imshow(data, cmap='RdYlBu_r', aspect='auto')
    ax1.set_xticks(range(len(layers)))
    ax1.set_xticklabels([l.split('_')[-1] for l in layers], rotation=45, fontsize=8)
    ax1.set_yticks([0, 1])
    ax1.set_yticklabels(["Before FT", "After FT"])
    ax1.set_title("Per-Layer Centroid Gap", fontsize=12)
    plt.colorbar(im, ax=ax1)

    # 差值柱状图
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
    print(f"✅ 图2 已保存: {save_path}")


# ============================================================
# 图3: 缺失比例 vs Gap偏移
# ============================================================

def plot_missing_modality_impact(
    missing_ratios: List[float],
    gap_shifts: Dict[str, List[float]],   # {metric: [shift_values]}
    save_path: str = "outputs/fig3_missing_impact.png",
    figsize: tuple = (10, 6),
):
    """
    绘制缺失比例与Gap偏移的关系
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
    print(f"✅ 图3 已保存: {save_path}")


# ============================================================
# 图4: Gap vs Task Performance 散点图
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
    绘制 Gap vs 下游任务性能散点图 + 回归线
    """
    fig, ax = plt.subplots(figsize=figsize)

    gap_arr = np.array(gap_values)
    perf_arr = np.array(performance_values)

    # 散点
    ax.scatter(gap_arr, perf_arr, c='#3498db', alpha=0.6, s=60, edgecolors='white')

    # 线性回归
    if len(gap_arr) >= 3:
        coeffs = np.polyfit(gap_arr, perf_arr, 1)
        x_fit = np.linspace(gap_arr.min(), gap_arr.max(), 100)
        y_fit = np.polyval(coeffs, x_fit)
        ax.plot(x_fit, y_fit, '--', color='#e74c3c', linewidth=2,
               label=f'y = {coeffs[0]:.4f}x + {coeffs[1]:.4f}')

        # Pearson相关系数
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
    print(f"✅ 图4 已保存: {save_path}")


# ============================================================
# 图5: t-SNE Embedding 可视化
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
    t-SNE可视化：微调前后的embedding分布对比
    """
    from sklearn.manifold import TSNE

    # 采样
    if len(before_image_embeds) > sample_size:
        indices = np.random.choice(len(before_image_embeds), sample_size, replace=False)
        before_image_embeds = before_image_embeds[indices]
        before_text_embeds = before_text_embeds[indices]
        after_image_embeds = after_image_embeds[indices]
        after_text_embeds = after_text_embeds[indices]

    # 合并四个集合进行t-SNE（保持全局结构可比）
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
    print(f"✅ 图5 已保存: {save_path}")


# ============================================================
# 综合报告生成
# ============================================================

def generate_report(
    experiment_results: Dict,
    save_dir: str = "outputs/",
):
    """
    根据所有实验结果生成综合可视化报告
    """
    os.makedirs(save_dir, exist_ok=True)

    # 收集所有gap历史
    gap_histories = {}
    for name, result in experiment_results.items():
        if "gap_history" in result:
            gap_histories[name] = result["gap_history"]

    # 图1: Gap演化
    if gap_histories:
        plot_gap_evolution(
            gap_histories,
            save_path=os.path.join(save_dir, "fig1_gap_evolution.png"),
        )

    # 图4: Gap vs Performance
    for name, result in experiment_results.items():
        if result.get("gap_values") and result.get("performance_values"):
            plot_gap_vs_performance(
                result["gap_values"],
                result["performance_values"],
                save_path=os.path.join(save_dir, f"fig4_gap_vs_perf_{name}.png"),
            )

    print(f"\n📊 综合报告已生成: {save_dir}")
