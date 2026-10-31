"""A3 图生成: fig1 (λ 曲线: τ + top-1 保留率) / fig2 (σ_m 2×2 判别 + 域/陆地比值跨模态对照)。
数据: outputs/sonar_protocol.json
输出: paper_a3/figures/fig1_lambda.png, fig2_sigma.png @300dpi (Times New Roman)
"""
import os, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['figure.dpi'] = 300

OUTDIR = 'paper_a3/figures'
os.makedirs(OUTDIR, exist_ok=True)
D = json.load(open('outputs/sonar_protocol.json', encoding='utf-8'))
MOD = {'clip_frozen': 'CLIP (frozen)', 'sonar_ft': 'SonarCLIP (10ep)', 'clip_flickrft': 'CLIP+Flickr (10ep)'}
COL = {'clip_frozen': '#4C72B0', 'sonar_ft': '#C44E52', 'clip_flickrft': '#55A868'}

# ---------------- fig1: λ 曲线 (两面板: τ 与 top-1 保留率) ----------------
fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
ax = axes[0]
for tag, lab in MOD.items():
    rows = sorted([r for r in D[tag]['rows'] if isinstance(r['lambda'], float)], key=lambda r: r['lambda'])
    ax.plot([r['lambda'] for r in rows], [r['tau_meas'] for r in rows], 'o-', ms=3.5, lw=1.2,
            color=COL[tag], label=lab)
ax.axhline(1.0, ls=':', c='gray', lw=0.8)
ax.set_xlabel(r'$\lambda$')
ax.set_ylabel(r'$\tau$ (order preservation)')
ax.set_ylim(-0.35, 1.05)
ax.set_title('(a) Order preservation', fontsize=9)
ax = axes[1]
for tag, lab in MOD.items():
    rows = sorted([r for r in D[tag]['rows'] if isinstance(r['lambda'], float)], key=lambda r: r['lambda'])
    ax.plot([r['lambda'] for r in rows], [r['top1'] for r in rows], 'o-', ms=3.5, lw=1.2, color=COL[tag], label=lab)
ax.axhline(16.15, ls=':', c='gray', lw=0.8)
ax.set_xlabel(r'$\lambda$')
ax.set_ylabel('zero-shot top-1 (%)')
ax.set_ylim(0, 106)
ax.set_title('(b) Zero-shot top-1 (absolute)', fontsize=9)
# 共用图例（置底、三列）
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, fontsize=7, frameon=True, framealpha=0.95, loc='lower center',
           bbox_to_anchor=(0.5, -0.04), ncol=3)
fig.tight_layout(rect=[0, 0.06, 1, 1])
fig.savefig(os.path.join(OUTDIR, 'fig1_lambda.png'), bbox_inches='tight')
plt.close(fig)

# ---------------- fig2: σ_m 判别 + 跨模态比值 ----------------
fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7))
ax = axes[0]
vals = [D['clip_frozen']['sigma_m'], D['clip_flickrft']['sigma_m'], D['sonar_ft']['sigma_m']]
labels2 = ['CLIP 0ep', '+ Flickr', '+ Sonar']
ax.bar(range(3), vals, color=['#999999', '#55A868', '#C44E52'], width=0.6)
for i, v in enumerate(vals):
    ax.text(i, v + 0.0006, '%.4f' % v, ha='center', fontsize=8)
ax.set_xticks(range(3))
ax.set_xticklabels(labels2, fontsize=8)
ax.set_ylabel(r'$\sigma_m$')
ax.set_ylim(0, 0.030)
ax.set_title('(a) Sonar 2\u00d72 (8 classes, matched 10 ep)', fontsize=9)
ax = axes[1]
ax.bar([0, 1], [3.6, 3.4], color=['#4C72B0', '#C44E52'], width=0.45)
ax.text(0, 3.6 + 0.08, '3.6x', ha='center', fontsize=9)
ax.text(1, 3.4 + 0.08, '3.4x', ha='center', fontsize=9)
ax.set_xticks([0, 1])
ax.set_xticklabels(['marine (A2)', 'sonar (A3)'], fontsize=8)
ax.set_ylabel('domain/terrestrial flattening ratio')
ax.set_ylim(0, 4.2)
ax.set_title('(b) Same law, two modalities', fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'fig2_sigma.png'), bbox_inches='tight')
plt.close(fig)

print('A3 figures saved')
