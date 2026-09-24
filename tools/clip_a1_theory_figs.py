"""A1 理论节图示（2026-08-22）——扩展版 §4/§11 用。
数据：outputs/a1_margins.json（τ 预测/实测、top-1 界、m 分布、逐对样本）、
outputs/a1_theory_verify.json（经验界、O 族、P 类）、outputs/a1_subspace_results.json（P 类实测）。
输出：paper_a1/figures/figT1..T6 *.png（Times New Roman + stix，300 dpi）。
"""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['axes.spines.right'] = False
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.linewidth'] = 1.0
# 图例必须白底：否则曲线穿过图例文字（2026-08-22 用户指出压字问题）
plt.rcParams['legend.frameon'] = True
plt.rcParams['legend.framealpha'] = 0.95
plt.rcParams['legend.facecolor'] = 'white'
plt.rcParams['legend.edgecolor'] = '0.85'

C = {'b': '#1B6CA8', 'g': '#2166AC', 'r': '#B2182B', 'o': '#D6604D',
     'gy': '#878787', 'd': '#333333', 'b2': '#4393C3', 'o2': '#F4A582',
     'g2': '#92C5DE', 'dk': '#1A1A1A'}
OUT = 'paper_a1/figures/'

M = json.load(open('outputs/a1_margins.json'))
V = json.load(open('outputs/a1_theory_verify.json'))
SP = json.load(open('outputs/a1_subspace_results.json'))

LN = ['-2', '-1', '-0.5', '-0.25', '0.25', '0.5', '1', '2', '4']
xpos = np.arange(len(LN))
taue = [M['predicted_tau_exact'][l] for l in LN]
taum = [M['measured_tau_5k'][l]['tau'] for l in LN]
gap_norm = M['meta']['gap_norm']
sigma_m = M['meta']['std_m']

# ---------------- T1: τ(λ) 逐点预测 vs 实测 ----------------
fig, ax = plt.subplots(figsize=(6.8, 3.6))
ax.plot(xpos, taue, 'o-', color=C['b'], lw=2, ms=6, label=r'predicted (Thm. 1, closed-form)')
ax.plot(xpos, taum, 's--', color=C['r'], lw=1.6, ms=6, label='measured (same 5k sample)')
for x, ye, ym in zip(xpos, taue, taum):
    ax.plot([x, x], [ye, ym], color=C['gy'], lw=0.8, alpha=0.7)
maxdiff = max(abs(a - b) for a, b in zip(taue, taum))
ax.set_xticks(xpos)
ax.set_xticklabels([r'$\lambda$=' + l for l in LN], fontsize=10)
ax.set_ylabel(r'order preservation $\tau$', fontsize=12)
ax.set_xlabel(r'perturbation scale $\lambda$ (gap-direction), $\|g\|=%.3f$' % gap_norm, fontsize=11)
ax.legend(fontsize=9, loc='lower left', ncol=1)
ax.set_title(r'Pointwise prediction of $\tau(\lambda)$ from frozen-model statistics', fontsize=12, pad=10)
ax.text(0.98, 0.94, 'max |diff| = %.3f (9/9 points)' % maxdiff, transform=ax.transAxes,
        ha='right', fontsize=10, color=C['d'])
fig.tight_layout(pad=1.5)
fig.savefig(OUT + 'figT1_tau_dose.png', dpi=300, bbox_inches='tight', pad_inches=0.15)
plt.close(fig)

# ---------------- T2: top-1 失守率：界链 ----------------
LP = ['0.25', '0.5', '1', '2', '4']
xp = np.arange(len(LP))
exact = [M['predicted_rank1_loss_exact'][l] for l in LP]
empf = [V['predicted_rank1_loss_emp'][l] for l in LP]
gcorr = [M['predicted_rank1_loss_corr'][l] for l in LP]
union = [min(1.0, 4 * M['predicted_rank1_loss_gauss'][l]) for l in LP]
frozon5k = 59.26
meas = [(frozon5k - M['measured_tau_5k'][l]['top1']) / frozon5k for l in LP]
fig, ax = plt.subplots(figsize=(6.8, 3.8))
ax.plot(xp, exact, 'o-', color=C['b'], lw=2, ms=6, label='exact (Thm. 3a, true $m$)')
ax.plot(xp, empf, 'D-', color=C['g'], lw=1.8, ms=5, label=r'empirical-$F_m$ bound (LOO)')
ax.plot(xp, gcorr, '^--', color=C['o'], lw=1.6, ms=6, label='Gaussian conditional bound')
ax.plot(xp, union, 'v:', color=C['gy'], lw=1.6, ms=6, label='marginal union bound (saturates)')
ax.plot(xp, meas, 's-', color=C['r'], lw=1.6, ms=6, alpha=0.85, label='measured relative drop (ref.)')
ax.set_xticks(xp)
ax.set_xticklabels([r'$\lambda$=' + l for l in LP], fontsize=10)
ax.set_ylabel(r'$P(\mathrm{rank\text{-}1\ lost})$', fontsize=12)
ax.set_xlabel(r'perturbation scale $\lambda$', fontsize=11)
ax.set_ylim(-0.02, 1.06)
ax.legend(fontsize=8.5, loc='upper center', ncol=3, bbox_to_anchor=(0.5, -0.24))
ax.set_title('Hierarchy of error bounds for the top-1 class', fontsize=12, pad=10)
ax.annotate('marginal union bound saturates\nat $\\lambda\\geq 0.5$', xy=(1.0, 1.0),
            xytext=(1.55, 0.85), fontsize=9, color=C['gy'], ha='left',
            arrowprops=dict(arrowstyle='->', color=C['gy'], lw=1.0))
fig.tight_layout(pad=1.5)
fig.savefig(OUT + 'figT2_top1_bounds.png', dpi=300, bbox_inches='tight', pad_inches=0.15)
plt.close(fig)

# ---------------- T3: (d, b) 联合分布与反转边界 ----------------
dd = np.array(M['pair_samples']['d'])
bb = np.array(M['pair_samples']['b'])
fig, ax = plt.subplots(figsize=(6.8, 4.4))
hb = ax.hexbin(dd, bb, gridsize=45, cmap='Blues', mincnt=1, bins='log')
for lam, cl, ls in [(1.0, C['r'], '-'), (0.5, C['o'], '--'), (2.0, C['gy'], ':')]:
    xl = np.linspace(0.001, 0.075, 50)   # 截短：不钻进右上图例框（2026-08-22）
    ax.plot(xl, xl / (lam * gap_norm), ls, color=cl, lw=1.4,
            label=r'inversion boundary $b=d/(\lambda\|g\|)$, $\lambda=%g$' % lam)
ax.set_xlim(0, 0.12)
ax.set_ylim(0, 0.22)
ax.set_xlabel(r'pairwise margin $d_{ij}$ (frozen)', fontsize=12)
ax.set_ylabel(r'bias difference $b_{ij}=m_j-m_i$', fontsize=12)
ax.set_title(r'Inversion = small margin $\times$ large bias difference ($\lambda{=}1$: above line inverts)',
             fontsize=11, pad=10)
ax.legend(fontsize=8.5, loc='upper right', bbox_to_anchor=(1.06, 1.0), borderaxespad=0)
ax.text(0.02, 0.78, 'n = 50,000 pairs\nPearson$(d,b)=0.066$\n$d$: mean 0.018 / q10 0.002',
        transform=ax.transAxes, fontsize=9, color=C['d'],
        bbox=dict(boxstyle='round,pad=0.25', facecolor='white', alpha=0.85, edgecolor=C['gy'], lw=0.6))
fig.tight_layout(pad=1.5)
fig.savefig(OUT + 'figT3_inversion_joint.png', dpi=300, bbox_inches='tight', pad_inches=0.15)
plt.close(fig)

# ---------------- T4: O 族（Corollary 1）验证 ----------------
predO = [V['predicted_tau_orthogonal'][l] for l in LN]
_lookO = {float(k): v for k, v in V['measured_tau_orthogonal'].items()}
measO = [float(_lookO.get(float(l), np.nan)) for l in LN]
sig_m = M['meta']['std_m']
sig_O = V['orthogonal']['sigma_mO']
fig, (axa, axb) = plt.subplots(1, 2, figsize=(8.6, 3.7), gridspec_kw={'width_ratios': [2.2, 1]})
axa.plot(xpos, predO, 'o-', color=C['b'], lw=2, ms=6, label='predicted (Thm. 1 with $m^O$)')
axa.plot(xpos, measO, 's--', color=C['r'], lw=1.6, ms=6, label='measured')
axa.set_xticks(xpos)
axa.set_xticklabels([r'$\lambda$=' + l for l in LN], fontsize=9)
axa.set_ylabel(r'order preservation $\tau$ (orthogonal)', fontsize=11)
axa.legend(fontsize=8.5, loc='lower left', ncol=1)
axa.set_title(r'$O$ family is the same operator, milder field', fontsize=11, pad=8)
axa.set_xlabel('perturbation scale (matched magnitude)', fontsize=10)
bars = [sig_m, sig_O]
axb.bar([0, 1], bars, color=[C['g'], C['o']], width=0.5, alpha=0.9)
for i, v in enumerate(bars):
    axb.text(i, v + 0.003, '%.4f' % v, ha='center', fontsize=9)
axb.set_xticks([0, 1])
axb.set_xticklabels([r'$\sigma_m$', r'$\tilde\sigma_O$'], fontsize=10)
axb.set_ylabel('field dispersion', fontsize=11)
axb.set_ylim(0, 0.085)
axb.text(0.98, 0.88, r'$\tilde\sigma_O = %.3f\,\sigma_m$' % V['orthogonal']['ratio_sigmaO_over_sigmaM'],
         transform=axb.transAxes, ha='right', fontsize=10, color=C['d'])
axb.set_title('orthogonal projection', fontsize=11, pad=8)
fig.tight_layout(pad=1.4)
fig.savefig(OUT + 'figT4_orthogonal.png', dpi=300, bbox_inches='tight', pad_inches=0.15)
plt.close(fig)

# ---------------- T5: P 类（Theorem 5）验证 ----------------
pc = V['class_contraction']
measP = pc['measured']
fig, (axa, axb) = plt.subplots(1, 2, figsize=(8.6, 3.6))
as_ = [0.25, 0.5]
top1_p = [pc['%g' % a]['predicted_top1'] for a in as_]
top1_m = [measP['%g' % a]['top1'] for a in as_]
tau_p = [pc['%g' % a]['predicted_tau'] for a in as_]
tau_m = [measP['%g' % a]['tau'] for a in as_]
axa.plot(as_, top1_p, 'o-', color=C['b'], lw=2, ms=7, label='predicted (affine, exact)')
axa.plot(as_, top1_m, 'x-', color=C['r'], lw=1.6, ms=8, label='measured', alpha=0.85)
axa.set_xlabel(r'contraction strength $a$', fontsize=11)
axa.set_ylabel('ImageNet zero-shot top-1 (%)', fontsize=11)
axa.set_ylim(55, 85)
axa.legend(fontsize=9, loc='lower right')
axa.set_title('Theorem 5: class-aligned contraction', fontsize=11, pad=8)
axb.plot(as_, tau_p, 'o-', color=C['b'], lw=2, ms=7, label='predicted')
axb.plot(as_, tau_m, 'x-', color=C['r'], lw=1.6, ms=8, label='measured', alpha=0.85)
axb.set_xlabel(r'contraction strength $a$', fontsize=11)
axb.set_ylabel(r'$\tau$ (vs frozen)', fontsize=11)
axb.legend(fontsize=9, loc='lower left')
axb.set_title(r'$\tau$ drops while top-1 rises (two-field)', fontsize=11, pad=8)
for axx, vals in [(axa, top1_p), (axb, tau_p)]:
    for a, v in zip(as_, vals):
        axx.annotate('%.2f' % v if v > 1 else '%.3f' % v, (a, v), textcoords='offset points',
                     xytext=(0, 8), ha='center', fontsize=8.5)
fig.suptitle('Prediction = measured (exact overlap); self-field mean $+0.0435\\pm0.029$',
             fontsize=11, y=1.0)
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(OUT + 'figT5_class_contraction.png', dpi=300, bbox_inches='tight', pad_inches=0.15)
plt.close(fig)

# ---------------- T6: m 分布 ----------------
mv = np.array(M['m_values'])
mean_m = M['meta']['mean_m']
fig, ax = plt.subplots(figsize=(6.0, 3.4))
ax.hist(mv, bins=25, color=C['g'], alpha=0.8, edgecolor='white')
xx = np.linspace(mv.min() - 0.02, mv.max() + 0.02, 300)
yy = 1000 * 0.02 * (1 / (np.sqrt(2 * np.pi) * sigma_m)) * np.exp(-0.5 * ((xx - mean_m) / sigma_m) ** 2)
ax.plot(xx, yy, '--', color=C['r'], lw=1.6, label=r'Gaussian fit ($\sigma_m=%.4f$)' % sigma_m)
ax.axvline(mean_m, color=C['d'], ls=':', lw=1.2)
ax.text(mean_m - 0.022, ax.get_ylim()[1] * 0.88, r'$\mu_m=%.3f$ (biased!)' % mean_m, fontsize=9,
        ha='right',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.9,
                  edgecolor=C['gy'], lw=0.6))
ax.set_xlabel(r'class bias field $m_c=\hat d\cdot t_c$', fontsize=11)
ax.set_ylabel('count (1000 classes)', fontsize=11)
ax.legend(fontsize=9)
ax.set_title(r'$m$ is class-imbalanced-positive; differences $b_{ij}$ are zero-mean',
             fontsize=11, pad=10)
fig.tight_layout(pad=1.5)
fig.savefig(OUT + 'figT6_m_distribution.png', dpi=300, bbox_inches='tight', pad_inches=0.15)
plt.close(fig)

print('saved:', ['figT%d' % k for k in range(1, 7)])
