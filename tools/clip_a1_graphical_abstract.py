"""A1 graphical abstract: 531x1328 px (PRL requirement), portrait---title on top + τ-top1 main plot in the middle + three key points below."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Submission requirement: all text inside the figure uses Times New Roman (math symbols use stix to match the Times style)
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['mathtext.fontset'] = 'stix'

fig, ax = plt.subplots(figsize=(5.31, 13.28), dpi=100)  # 531x1328 px
ax.axis('off')
# Note: text on ax uses subplot data coordinates (the default ylim 0-1 maps to canvas 0.11-0.88),
# so fig.text (figure coordinates) is required to put the title at the top of the canvas and avoid overlapping the ax2 title (fixed 2026-08-21)
fig.text(0.5, 0.975, 'The modality gap is not a universal health metric',
         ha='center', va='top', fontsize=16, fontweight='bold')
fig.text(0.5, 0.93, 'Order preservation governs zero-shot robustness',
         ha='center', va='top', fontsize=12, color='#555555')

# schematic: synthetic data showing the τ-top1 relation
rng = np.random.RandomState(0)
taus = np.linspace(-0.1, 1.0, 40)
top1 = 59.3 * (1 / (1 + np.exp(-8 * (taus - 0.25)))) + rng.randn(40) * 2.5
ax2 = fig.add_axes([0.12, 0.50, 0.76, 0.30])
ax2.scatter(taus, top1, s=12, alpha=0.6, color='#555555', label='synthetic perturbations')
# the same set of real checkpoints as Figure 2 in the main text (text-only/both take trajectory epoch-10, full-FT three seeds)
ax2.scatter([0.794, 0.748, 0.122, 0.122, -0.083], [58.7, 58.9, 7.4, 7.0, 0.1], s=60,
            marker='*', color='#B2182B', zorder=5, label='real checkpoints')
ax2.set_xlabel(r'order preservation $\tau$', fontsize=11)
ax2.set_ylabel('zero-shot top-1 (%)', fontsize=11)
ax2.set_title(r'top-1 is governed by $\tau$, not by the gap', fontsize=11)
ax2.legend(fontsize=7, loc='lower right')
ax2.set_xlim(-0.15, 1.1); ax2.set_ylim(-8, 85)

fig.text(0.06, 0.46, 'Key findings', fontsize=12, fontweight='bold', va='top')
findings = [
    ('1', 'Closing the gap by translation can destroy classification'),
    ('2', 'A first-order bias field predicts the effect (r = 1.000)'),
    ('3', 'Image-side shifts are destructive; text-side shifts are not'),
    ('4', 'tau is a zero-overhead training-time health signal'),
]
y = 0.415
for num, txt in findings:
    fig.text(0.06, y, num, fontsize=12, fontweight='bold', color='#B2182B', va='top')
    fig.text(0.12, y, txt, fontsize=10, va='top', wrap=True)
    y -= 0.043
fig.savefig('paper_a1/figures/graphical_abstract.png', dpi=100)  # no tight: exactly 531x1328 px
print('graphical abstract saved (531x1328 px)')
