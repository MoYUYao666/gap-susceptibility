"""A1 paper figures: generate the three core figures from outputs/a1_*.json → paper_a1/figures/"""
import json, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# submission requirement: text inside figures uses Times New Roman throughout (math symbols use stix to match the Times style)
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['mathtext.fontset'] = 'stix'

os.makedirs('paper_a1/figures', exist_ok=True)
full = json.load(open('outputs/a1_full_results.json', encoding='utf-8'))
sub = json.load(open('outputs/a1_subspace_results.json', encoding='utf-8'))
e2b = json.load(open('outputs/a1_e2b_e3b.json', encoding='utf-8'))

C = {'T': '#B2182B', 'O': '#D6604D', 'C': '#2166AC'}

# ---------- Fig 1: λ vs top-1 (T/O/C families) ----------
fig, ax = plt.subplots(figsize=(5.2, 3.6))
for fam, c, m in [('T', C['T'], 'o'), ('O', C['O'], 's'), ('C', C['C'], '^')]:
    xs = [r['lambda'] for r in full if r['kind'] == fam]
    ys = [r['top1'] for r in full if r['kind'] == fam]
    ax.plot(xs, ys, marker=m, color=c, linestyle='-',
            label={'T': 'gap-direction shift', 'O': 'orthogonal shift', 'C': 'centroid contraction'}[fam], ms=6)
ax.axhline(59.28, color='gray', ls='--', lw=0.8)
ax.text(2.6, 59.9, 'frozen (59.28)', fontsize=8, color='gray')
ax.set_xlabel(r'perturbation scale $\lambda$ (or $a$)')
ax.set_ylabel('ImageNet zero-shot top-1 (%)')
ax.set_title('Zero-shot degrades with perturbation, but strongly depends on direction/structure', fontsize=9)
ax.legend(fontsize=8)
ax.set_ylim(0, 75)
fig.tight_layout(); fig.savefig('paper_a1/figures/fig1_lambda.png', dpi=300); fig.savefig('paper_a1/figures/fig1_lambda.pdf'); plt.close(fig)

# ---------- Fig 2: τ vs top-1 (full spectrum + real checkpoints) ----------
# the two synthetic point sets have different sample sizes (disclosed in the caption): the 20 surgery-grid conditions are scored on the full 50k validation set,
# the rest (spectrum + per-image low rank) are scored on the 5k sample. The two are separated by different markers/colors + two legend entries.
fig, ax = plt.subplots(figsize=(5.2, 3.8))
taus50, t1s50 = [], []
for r in full:
    if r['kind'] == 'T' or r['kind'] == 'O' or r['kind'] == 'C':
        taus50.append(r['tau_top5']); t1s50.append(r['top1'])
taus5, t1s5 = [], []
for r in sub['results']:
    taus5.append(r['tau_top5']); t1s5.append(r['top1'])
for r in e2b['results']['E2b_input_dependent']:
    taus5.append(r['tau_top5']); t1s5.append(r['top1'])
ax.scatter(taus50, t1s50, s=30, alpha=0.60, marker='o', color='#555555',
           label='synthetic, 50k-image grid (n=%d)' % len(taus50))
ax.scatter(taus5, t1s5, s=36, alpha=0.85, marker='^', color='#2166AC',
           label='synthetic, 5k-image sample (n=%d)' % len(taus5))
print('fig2 point sets: 50k-grid n=%d  5k-sample n=%d' % (len(taus50), len(taus5)))
# real checkpoints: text_only/both use the retrained trajectory epoch10 (same source as §5.5/fig4), full_ft uses the three e2b seeds
traj = json.load(open('outputs/a1_tau_trajectory.json', encoding='utf-8'))
real_pts = []
for mode in ['text_only', 'both']:
    r = traj[mode][-1]
    real_pts.append((r['tau'], r['top1']))
for r in e2b['results']['E3b_real_checkpoints']:
    if r['name'].startswith('full_ft'):
        real_pts.append((r['tau_top5'], r['top1']))
rt = [p[0] for p in real_pts]; rt1 = [p[1] for p in real_pts]
ax.scatter(rt, rt1, s=90, marker='*', color='#B2182B', zorder=5,
           label='real checkpoints (text-only / both / full-FT ×3)')
ax.plot([0, 1], [0, 59.28], '--', color='gray', lw=0.7)
ax.set_xlabel(r'order preservation $\tau$ (Kendall, vs frozen)')
ax.set_ylabel('ImageNet zero-shot top-1 (%)')
ax.set_title(r'Top-1 is governed by order preservation $\tau$, not by the gap', fontsize=9)
ax.legend(fontsize=8, loc='lower right')
ax.set_xlim(-0.12, 1.05); ax.set_ylim(-5, 85)
fig.tight_layout(); fig.savefig('paper_a1/figures/fig2_tau_top1.png', dpi=300); fig.savefig('paper_a1/figures/fig2_tau_top1.pdf'); plt.close(fig)

# ---------- Fig 3: three task-sensitivity tiers (retention of each metric relative to frozen at λ=+1) ----------
base = [r for r in full if r['lambda'] == 0.0 and r['kind'] == 'T'][0]
pert = [r for r in full if r['lambda'] == 1.0 and r['kind'] == 'T'][0]
tasks = ['NCC\n(centroid class.)', 'zero-shot\ntop-1', 'retrieval\nR@1']
base_v = [base['ncc'], base['top1'], base['R1'] * 100]
pert_v = [pert['ncc'], pert['top1'], pert['R1'] * 100]
keep = [p / b * 100 for p, b in zip(pert_v, base_v)]
fig, ax = plt.subplots(figsize=(4.6, 3.4))
bars = ax.bar(tasks, keep, color=['#2166AC', '#D6604D', '#B2182B'], width=0.55)
for b, v in zip(bars, keep):
    ax.text(b.get_x() + b.get_width() / 2, v + 1.5, '%.0f%%' % v, ha='center', fontsize=9)
ax.set_ylabel('performance retained at λ=+1 (%)')
ax.set_title(r'Task-sensitivity spectrum under the same gap shift', fontsize=9)
ax.set_ylim(0, 124)
ax.axhline(100, color='gray', ls='--', lw=0.8)
# user requirement: Fig 4 (spectrum bar chart) has no legend; the task names are already given by the x-axis labels
fig.tight_layout(); fig.savefig('paper_a1/figures/fig4_spectrum.png', dpi=300); fig.savefig('paper_a1/figures/fig4_spectrum.pdf'); plt.close(fig)
print('figures done')

