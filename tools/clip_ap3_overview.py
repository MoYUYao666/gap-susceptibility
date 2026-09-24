# -*- coding: utf-8 -*-
"""合并稿提升#2: 框架概念总览图(Γ→表示定理→GFAP→实验)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(12.5, 3.6), dpi=300)
ax.axis('off')

boxes = [
    (0.005, 0.62, 0.20, 0.30, 'Problem\nblock-allocation\n(budget C, blocks M_k)'),
    (0.235, 0.62, 0.20, 0.30, 'Requirements R1-R5\ncomputable · invariant\nadditive · directed · 1st-order'),
    (0.465, 0.62, 0.20, 0.30, 'Representation Thm\nΓ_k = ⟨∇_{M_k}E, u_{M_k}⟩\nunique up to scaling'),
    (0.695, 0.62, 0.20, 0.30, 'GFAP (C1-C4)\nΔE→ Γ dominates\nrank_k ∝ exp(-β|Γ_k|)'),
    (0.925, 0.62, 0.07, 0.30, 'Empirics\n278 dual-enc.\n190 decoder\n468 runs'),
    (0.235, 0.06, 0.20, 0.30, 'Specialization (C5)\nEq. d(DG^*)/dt = α - β(DG^*-DG_0)\nR²>0.96 · ERS k=0.043'),
    (0.465, 0.06, 0.20, 0.30, 'Predictions\nr_c ∈ [5,6] (LLaVA)\nabsent (Qwen2-VL)\nzero-shot transfer'),
    (0.695, 0.06, 0.20, 0.30, 'Checks\ncounterfactuals 30×\nordering p=2⁻⁵\nA1 linearity R²=0.961'),
]
for x, y, w, h, txt in boxes:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.006',
                                linewidth=1.2, edgecolor='#2b4c7e', facecolor='#eef3fa'))
    ax.text(x + w / 2, y + h / 2, txt, ha='center', va='center', fontsize=8.2, linespacing=1.45)

arrows = [
    ((0.21, 0.77), (0.228, 0.77)),
    ((0.44, 0.77), (0.458, 0.77)),
    ((0.67, 0.77), (0.688, 0.77)),
    ((0.80, 0.62), (0.80, 0.40)),
    ((0.90, 0.36), (0.92, 0.36)),
    ((0.36, 0.36), (0.36, 0.18)),
    ((0.67, 0.36), (0.688, 0.36)),
    ((0.57, 0.36), (0.57, 0.40)),
]
for (x1, y1), (x2, y2) in arrows:
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>',
                                 mutation_scale=12, linewidth=1.2, color='#2b4c7e'))

ax.text(0.012, 0.47, 'allocation\nproblem', fontsize=7, color='#7a7a7a', ha='left')
ax.text(0.465, 0.47, 'forced, not proposed', fontsize=7, color='#7a7a7a', ha='center')
ax.text(0.695, 0.47, 'laws', fontsize=7, color='#7a7a7a', ha='center')
ax.text(0.30, 0.02, 'dynamical theory', fontsize=7, color='#7a7a7a', ha='center')

plt.tight_layout()
plt.savefig('paper_ap3/figures/fig_diagram.png', dpi=300, bbox_inches='tight')
print('saved paper_ap3/figures/fig_diagram.png')
