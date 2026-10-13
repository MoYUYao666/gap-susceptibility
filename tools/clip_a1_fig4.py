"""A1 fig4: training-time trajectory (text_only vs both), two stacked panels.
Top: τ (left axis) + CG (right axis); bottom: top-1 (with the frozen baseline as a dashed line). Data: outputs/a1_tau_trajectory.json.
"""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Submission requirement: all in-figure text uses Times New Roman (stix for math symbols, to match the Times look)
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['mathtext.fontset'] = 'stix'

d = json.load(open('outputs/a1_tau_trajectory.json', encoding='utf-8'))
colors = {'text_only': '#2166AC', 'both': '#D6604D'}
frozen_top1 = d['frozen']['top1']          # 59.26 (frozen baseline on 5k samples)

fig, (ax, axb) = plt.subplots(2, 1, figsize=(5.0, 4.4), sharex=True)
ax2 = ax.twinx()

# ---------- top: τ (left) + CG (right) ----------
for mode, c in colors.items():
    eps = [r['epoch'] for r in d[mode]]
    tau = [r['tau'] for r in d[mode]]
    cg = [r['CG'] for r in d[mode]]
    ax.plot(eps, tau, 'o-', color=c, ms=5, label='%s: τ (left)' % mode)
    ax2.plot(eps, cg, '--', color=c, alpha=0.55, label='%s: CG (right)' % mode)
ax.set_ylabel(r'order preservation $\tau$', color='k')
ax2.set_ylabel('Centroid Gap', color='k')
ax.set_ylim(0.65, 1.05)
ax2.set_ylim(0.75, 0.95)
lines1, lab1 = ax.get_legend_handles_labels()
lines2, lab2 = ax2.get_legend_handles_labels()
ax.legend(lines1 + lines2, lab1 + lab2, fontsize=6.5, loc='upper right',
          handlelength=1.2, labelspacing=0.4, borderaxespad=0.4)

# ---------- bottom: top-1 ----------
for mode, c in colors.items():
    eps = [r['epoch'] for r in d[mode]]
    t1 = [r['top1'] for r in d[mode]]
    axb.plot(eps, t1, 's-', color=c, ms=5, label=mode)
axb.axhline(frozen_top1, color='gray', ls='--', lw=0.8, label='frozen (%.1f)' % frozen_top1)
axb.set_xlabel('training epoch')
axb.set_ylabel('zero-shot top-1 (%)')
axb.set_ylim(57.5, 60.0)
axb.legend(fontsize=6.5, loc='upper right', handlelength=1.2,
           labelspacing=0.4, borderaxespad=0.4)

ax.set_title(r'$\tau$ erodes early under both-position fine-tuning while top-1 stays flat', fontsize=8.5)
fig.tight_layout()
fig.savefig('paper_a1/figures/fig3_trajectory.png', dpi=300); fig.savefig('paper_a1/figures/fig3_trajectory.pdf')
print('fig4 done')
