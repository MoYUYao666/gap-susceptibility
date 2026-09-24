"""A2 图 7（声呐偏置场结构）重生成脚本。
修复：右侧面板旧版只有两根粗柱（3.6x/3.4x），观感像图例且数值过时
（正文已修正为 平衡 3.8×/全量 1.8×，陆地 1.1×）。
新版：(a) 分组柱——平衡 650 / 全量 2,617 两口径 × (冻结/+Flickr/+Sonar) 的 σ_m；
      (b) 压平比（σ_m 冻结/σ_m 微调）——sonar 平衡 3.8× / sonar 全量 1.8× / 陆地 1.1×。
数字全部实时从 outputs/sonar_protocol.json + sonar_protocol_full.json 计算。
输出 paper_a2/figures/fig7_sonar_sigma.png @300dpi
"""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['figure.dpi'] = 300
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8

BAL = json.load(open('outputs/sonar_protocol.json', encoding='utf-8'))
FUL = json.load(open('outputs/sonar_protocol_full.json', encoding='utf-8'))

# σ_m 取值（平衡口径 / 全量口径）
frozen = [BAL['clip_frozen']['sigma_m'], FUL['clip_frozen']['sigma_m']]
flickr = [BAL['clip_flickrft']['sigma_m'], FUL['clip_flickrft']['sigma_m']]
sonar = [BAL['sonar_ft']['sigma_m'], FUL['sonar_ft_full']['sigma_m']]

# 压平比 = σ_m(冻结) / σ_m(微调)
ratio_bal = BAL['clip_frozen']['sigma_m'] / BAL['sonar_ft']['sigma_m']        # 平衡口径
ratio_ful = FUL['clip_frozen']['sigma_m'] / FUL['sonar_ft_full']['sigma_m']    # 全量口径
ratio_ter = FUL['clip_frozen']['sigma_m'] / FUL['clip_flickrft']['sigma_m']    # 陆地对照

fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.3))
ax = axes[0]

# ---- (a) 分组柱状 ----
groups = ['balanced 650', 'full 2,617']
# '+ Flickr' 不是多余条目：它就是 (b) 面板里的陆地对照 (CLIP + Flickr FT)，图例写明，
# 以免读者以为它是一条与正文无关的曲线（正文 0.0239→0.0063 vs 0.0216 即此序列）。
series = [('CLIP frozen', frozen, '#8C8C8C'), ('+ Flickr FT (terrestrial control)', flickr, '#57A860'),
          ('+ Sonar', sonar, '#C44E52')]
x = np.arange(len(groups))
w = 0.26
for k, (name, vals, col) in enumerate(series):
    xi = x + (k - 1) * w
    bars = ax.bar(xi, vals, width=w, color=col, edgecolor='#333333',
                  linewidth=0.6, label=name, zorder=3)
    for xi_, v in zip(xi, vals):
        ax.text(xi_, v + 0.0006, f'{v:.4f}', ha='center', va='bottom', fontsize=8.5)
ax.set_xticks(x)
ax.set_xticklabels(groups, fontsize=9)
ax.set_yticks(np.arange(0, 0.0301, 0.005))
ax.set_ylim(0, 0.028)
ax.set_ylabel(r'$\sigma_m$', fontsize=10)
ax.set_title(r'(a) $\sigma_m$: frozen vs adapted (balanced / full protocols)', fontsize=10)
ax.tick_params(axis='both', labelsize=8.5)
ax.grid(axis='y', color='#DDDDDD', linewidth=0.6, zorder=0)
ax.legend(loc='upper center', frameon=False, fontsize=8.5, ncol=3,
          bbox_to_anchor=(0.5, -0.30))

# ---- (b) 压平比 ----
ax2 = axes[1]
names = ['sonar\nbalanced 650', 'sonar\nfull 2,617', 'terrestrial\n(full 2,617)']
vals = [ratio_bal, ratio_ful, ratio_ter]
cols = ['#C44E52', '#C44E52', '#8C8C8C']
labs = [f'{v:.1f}$\\times$' for v in vals]
bb = ax2.bar(np.arange(3), vals, width=0.5, color=cols, edgecolor='#333333',
             linewidth=0.6, zorder=3)
for i, (v, l) in enumerate(zip(vals, labs)):
    ax2.text(i, v + 0.09, l, ha='center', va='bottom', fontsize=10)
ax2.set_xticks(np.arange(3))
ax2.set_xticklabels(names, fontsize=8.5)
ax2.set_ylim(0, 4.4)
ax2.set_yticks(np.arange(0, 4.5, 1.0))
ax2.set_ylabel(r'flattening ratio  ($\sigma_m$ frozen / $\sigma_m$ fine-tuned)',
               fontsize=9)
ax2.set_title(r'(b) Matched-scale discrimination', fontsize=10)
ax2.tick_params(axis='both', labelsize=8.5)
ax2.grid(axis='y', color='#DDDDDD', linewidth=0.6, zorder=0)

fig.tight_layout()
fig.savefig('paper_a2/figures/fig7_sonar_sigma.png', dpi=300, bbox_inches='tight')
print(f'fig7 written | balanced {ratio_bal:.2f}x  full {ratio_ful:.2f}x  terrestrial {ratio_ter:.2f}x')
