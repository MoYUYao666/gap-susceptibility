"""A2 图 1-4 生成脚本（数字全部来自 outputs/ocean_*.json）。
fig1: λ 曲线族（τ + top-1，图像侧；插图文本侧 τ）
fig2: σ_m 结构（4 模型 + 2×2 判别双家族 + 饱和点）
fig3: Theorem 1 预测 vs 实测（全部条件散点 + y=x）
fig4: PEFT 保护（任务 R@1 vs 零样本相对保持，误差棒 3-seed sd）
输出 paper_a2/figures/*.png @300dpi
"""
import os, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['figure.dpi'] = 300
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8

OUTDIR = 'paper_a2/figures'
os.makedirs(OUTDIR, exist_ok=True)


def load(f):
    return json.load(open(f, encoding='utf-8'))


GS = load('outputs/ocean_gap_surgery.json')
MA = load('outputs/ocean_margins.json')
NS = load('outputs/ocean_nsweep.json')
SO = load('outputs/ocean_sigma_other.json')
FS = load('outputs/ocean_flickrft_sigma.json')
MS = load('outputs/ocean_marineft10_sigma.json')
C2 = load('outputs/ocean_clip2x2.json')
MX = load('outputs/ocean_margins_x.json')
FA = load('outputs/ocean_fauna_margins.json')
IW = load('outputs/ocean_inat_wild.json')
PT = load('outputs/ocean_peft_ms.json')
TL = load('outputs/ocean_multitemplate.json')
MSD = load('outputs/ocean_multiseed.json')

MODELS = ['bioclip', 'oceanclip', 'openclip_tf', 'siglip']
LBL = {'bioclip': 'BioCLIP', 'oceanclip': 'OceanCLIP', 'openclip_tf': 'OpenCLIP', 'siglip': 'SigLIP'}
COL = {'bioclip': '#4C72B0', 'oceanclip': '#C44E52', 'openclip_tf': '#55A868', 'siglip': '#8172B3'}

# ---------------- fig1: λ 曲线族（三面板, 无内嵌插图） ----------------
fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.9),
                         gridspec_kw={'width_ratios': [1, 1, 0.78]})
ax = axes[0]
for m in MODELS:
    rows = [r for r in GS if r['model'] == m and r['side'] == 'image']
    rows = sorted(rows, key=lambda r: r['lam'])
    ax.plot([r['lam'] for r in rows], [r['tau'] for r in rows], 'o-', ms=3.5, lw=1.2, color=COL[m], label=LBL[m])
ax.axhline(1.0, ls=':', c='gray', lw=0.8)
ax.set_xlabel(r'$\lambda$')
ax.set_ylabel(r'$\tau$ (order preservation)')
ax.set_ylim(-0.15, 1.05)
ax.legend(fontsize=7, frameon=True, framealpha=0.95, loc='lower left')
ax.set_title('(a) Order preservation, image side', fontsize=9)
ax = axes[1]
for m in MODELS:
    rows = [r for r in GS if r['model'] == m and r['side'] == 'image']
    rows = sorted(rows, key=lambda r: r['lam'])
    b = [r for r in GS if r['model'] == m and r['side'] == 'image' and r['lam'] == 0][0]['top1']
    ax.plot([r['lam'] for r in rows], [100 * r['top1'] / b for r in rows], 'o-', ms=3.5, lw=1.2, color=COL[m])
ax.axhline(100, ls=':', c='gray', lw=0.8)
ax.set_xlabel(r'$\lambda$')
ax.set_ylabel('% of frozen zero-shot top-1')
ax.set_ylim(8, 106)
ax.set_title('(b) Zero-shot retention', fontsize=9)
ax = axes[2]
for m in ['bioclip', 'oceanclip']:
    rows = [r for r in GS if r['model'] == m and r['side'] == 'text']
    ax.plot([r['lam'] for r in rows], [r['tau'] for r in rows], 's--', ms=3.5, lw=1.2, color=COL[m], label=LBL[m])
ax.axhline(1.0, ls=':', c='gray', lw=0.8)
ax.set_xlabel(r'$\lambda$')
ax.set_ylabel(r'$\tau$')
ax.set_ylim(0.4, 1.02)
ax.set_xlim(0, 2.05)
ax.legend(fontsize=7, frameon=True, framealpha=0.95, loc='lower left')
ax.set_title('(c) Text side', fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'fig1_lambda.png'), bbox_inches='tight')
plt.close(fig)

# ---------------- fig2: σ_m 结构 ----------------
labels = ['BioCLIP', 'OceanCLIP', 'OpenCLIP', 'SigLIP']
sigs = [MA['bioclip']['sigma_m'], MA['oceanclip']['sigma_m'], SO['openclip_tf']['sigma_m'], SO['siglip']['sigma_m']]
fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.7))
ax = axes[0]
x = np.arange(4)
ax.bar(x, sigs, color=[COL[m] for m in MODELS], width=0.6)
for i, v in enumerate(sigs):
    ax.text(i, v + 0.0015, '%.4f' % v, ha='center', fontsize=7)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=8)
ax.set_ylabel(r'$\sigma_m$ (bias-field spread)')
ax.set_ylim(0, 0.092)
ax.set_title('(a) Frozen models on the 67-class marine set', fontsize=9)
ax = axes[1]
grp = [('bio+0ep', 0.0535), ('bio+Flickr', FS['sigma_m']), ('bio+Marine', MS['sigma_m']),
       ('CLIP+0ep', C2['clip_frozen']['sigma_m']), ('CLIP+Flickr', C2['clip_flickrft']['sigma_m']),
       ('CLIP+Marine', C2['clip_marineft']['sigma_m'])]
xx = np.arange(len(grp))
ax.bar(xx, [g[1] for g in grp], color=['#999999', '#55A868', '#2A9D8F', '#999999', '#55A868', '#2A9D8F'], width=0.65)
for i, (g, v) in enumerate(grp):
    ax.text(i, v + 0.0015, '%.4f' % v, ha='center', fontsize=6.5)
ax.set_xticks(xx)
ax.set_xticklabels([g[0] for g in grp], fontsize=7, rotation=20)
ax.set_ylabel(r'$\sigma_m$')
ax.set_ylim(0, 0.058)
ax.axhline(0.0078, ls='--', c='#C44E52', lw=0.9)
ax.plot([], [], ls='--', c='#C44E52', label='OceanCLIP (50 ep)')
ax.legend(fontsize=6.5, frameon=True, framealpha=0.95, loc='upper right')
ax.set_title('(b) Matched-scale 2\u00d72: ocean FT vs terrestrial FT', fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'fig2_sigma.png'), bbox_inches='tight')
plt.close(fig)

# ---------------- fig3: τ 预测 vs 实测 ----------------
pts = []
for tag, d in [('bioclip', MA['bioclip']), ('oceanclip', MA['oceanclip']),
               ('openclip_tf', MX['openclip_tf']), ('siglip', MX['siglip'])]:
    for l in ['-1.0', '-0.5', '-0.25', '0.25', '0.5', '1.0', '2.0']:
        pts.append((d['predicted_tau_exact'][l], d['measured'][l]['tau'], tag))
for tag, d in [('bioclip', FA['bioclip']), ('oceanclip', FA['oceanclip'])]:
    pts.append((d['predicted_tau_exact']['1.0'], d['measured']['1.0']['tau'], tag))
for tag, d in [('bioclip', IW['bioclip']), ('oceanclip', IW['oceanclip'])]:
    pts.append((d['tau_pred_1'], d['tau_meas_1'], tag))
for tag in ['bioclip', 'oceanclip']:
    for N in ['20', '40', '67']:
        pts.append((NS[tag][N]['tau_pred_1'], NS[tag][N]['tau_meas_1'], tag))
fig, ax = plt.subplots(figsize=(4.6, 4.0))
allx = [p[0] for p in pts]
ally = [p[1] for p in pts]
maxv = max(max(allx), max(ally))
ax.plot([-0.1, maxv + 0.05], [-0.1, maxv + 0.05], ls='--', c='gray', lw=0.9)
for tag in ['bioclip', 'oceanclip', 'openclip_tf', 'siglip']:
    px = [p for p in pts if p[2] == tag]
    ax.scatter([p[0] for p in px], [p[1] for p in px], s=22, color=COL.get(tag, '#333333'),
               label=LBL.get(tag, tag), alpha=0.85)
ax.set_xlabel(r'predicted $\tau$ (exact inversion condition)', fontsize=11)
ax.set_ylabel(r'measured $\tau$', fontsize=11)
ax.set_xlim(-0.12, maxv + 0.05)
ax.set_ylim(-0.12, maxv + 0.05)
ax.legend(fontsize=9, loc='upper left')
max_diff = max(abs(p[0] - p[1]) for p in pts)
ax.set_title('max |diff| = %.4f (%d conditions)' % (max_diff, len(pts)), fontsize=10)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'fig3_taupred.png'), bbox_inches='tight')
plt.close(fig)

# ---------------- fig4: PEFT ----------------
import collections
g = collections.defaultdict(list)
for k, v in PT.items():
    tag, method, seed = k.split('__')
    g[(tag, method)].append(v)
base = {'bioclip': 21.70, 'oceanclip': 24.19}
fig, ax = plt.subplots(figsize=(4.6, 3.4))
for (tag, method), rows in sorted(g.items()):
    r1 = np.mean([r['flickr_R1'] for r in rows])
    t1 = np.mean([r['marine_top1'] for r in rows])
    sd = np.std([r['marine_top1'] for r in rows])
    keep = 100 * t1 / base[tag]
    ax.errorbar(r1, keep, yerr=100 * sd / base[tag], fmt='o', ms=5,
                color=COL[tag], capsize=3)
    if keep > 100:
        dx, dy, ha = 6, 6, 'left'
    elif keep > 88:
        dx, dy, ha = 6, -13, 'left'
    else:
        dx, dy, ha = 6, 6, 'left'
    if r1 > 0.55:            # 右侧点: 标签放点左侧同高, 避免互相堆叠/超出右边
        dx, dy, ha = -8, 0, 'right'
    ax.annotate('%s/%s' % (tag[:3], method.replace('_', ' ')), (r1, keep),
                textcoords='offset points', xytext=(dx, dy), fontsize=7,
                ha=ha, va='center')
ax.axhline(100, ls=':', c='gray', lw=0.8)
ax.set_ylim(18, 118)
ax.set_xlim(0.06, 0.66)
ax.set_xlabel('Flickr30k retrieval R@1 (task performance)')
ax.set_ylabel('zero-shot retention (% of frozen)')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'fig4_peft.png'), bbox_inches='tight', pad_inches=0.15)
plt.close(fig)

# ---------------- fig5: 退化-手术边界 ----------------
DG = load('outputs/ocean_degradation.json')
fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8))
ax = axes[0]
conds = ['haze_t0.60', 'haze_t0.30', 'uw_cast']
xx = np.arange(3)
for k, tag in enumerate(['bioclip', 'oceanclip']):
    vals = [next(r for r in DG[tag]['rows'] if r['degrade'] == c)['tau_meas'] for c in conds]
    ax.bar(xx + (k - 0.5) * 0.4, vals, width=0.38, color=COL[tag], label=LBL[tag])
    for i, v in enumerate(vals):
        ax.text(xx[i] + (k - 0.5) * 0.4, v + 0.015, '%.2f' % v, ha='center', fontsize=7)
ax.set_xticks(xx)
ax.set_xticklabels(conds, fontsize=7)
ax.set_ylabel(r'$\tau$ under degradation')
ax.set_ylim(0, 1.15)
ax.legend(fontsize=7, loc='upper right')
ax.set_title('(a) Ordering damage from real degradation', fontsize=9)
ax = axes[1]
cshort = {'haze_t0.60': 'h0.6', 'haze_t0.30': 'h0.3', 'uw_cast': 'cast'}
for tag in ['bioclip', 'oceanclip']:
    pts = [(r['tau_pred'], r['tau_meas'], cshort[r['degrade']])
           for r in DG[tag]['rows'] if r['degrade'] != 'clean']
    ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=32, color=COL[tag],
               label=LBL[tag], edgecolor='#333333', linewidth=0.5, zorder=3)
    for x, y, cs in pts:
        ax.text(x + 0.015, y + 0.018, cs, fontsize=5.5, color=COL[tag],
                va='bottom', ha='left', zorder=3)
ax.plot([0, 1], [0, 1], ls='--', c='gray', lw=0.9, zorder=2)
ax.set_xlabel(r'predicted $\tau$ (gap-axis $\lambda_{\rm eff}$)')
ax.set_ylabel(r'measured $\tau$ (degradation)')
ax.set_xlim(-0.05, 1.16)
ax.set_ylim(0.1, 1.05)
ax.grid(color='#DDDDDD', linewidth=0.5, zorder=0)
ax.legend(fontsize=7, loc='lower right', markerscale=0.9)
ax.set_title('(b) Off-axis boundary of the exact predictor', fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'fig5_degradation.png'), bbox_inches='tight')
plt.close(fig)

print('figures saved to', OUTDIR)
