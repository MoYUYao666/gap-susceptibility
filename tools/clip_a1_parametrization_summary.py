"""(A1 post-processing) Extract conclusions that can go into the paper from clip_peft_gamma_ordering.json:
  - block-order consistency among the three PEFT parametrizations (Spearman per E);
  - in the comparison with full fine-tuning, compare only on encoder blocks "adapted on both sides" (the projection heads are not adapted in the PEFT arms, so Γ=0 is zero by construction);
  - cross-parametrization ratios of the encoder-block coupling (after per-parameter normalization).
Output: outputs/clip_a1_parametrization_summary.json
"""
import json

import numpy as np
from scipy import stats

d = json.load(open('outputs/clip_peft_gamma_ordering.json', encoding='utf-8'))
g = d['gamma_per_param']
modes = ['full', 'lora', 'adapter', 'bitfit']
ENC = ['vision_trunk', 'text_model']
PROJ = ['visual_projection', 'text_projection']
Es = list(g['full'].keys())

out = {'per_E': {}, 'encoder_ordering': {}, 'proj_zero_in_peft': {}, 'ratios': {}}
for E in Es:
    out['per_E'][E] = {}
    # 1) ordering consistency among the three PEFT variants (all 4 blocks, per-parameter normalized)
    for m1, m2 in (('lora', 'adapter'), ('lora', 'bitfit'), ('adapter', 'bitfit')):
        v1 = [g[m1][E][b] for b in d['blocks']]
        v2 = [g[m2][E][b] for b in d['blocks']]
        rho, p = stats.spearmanr(v1, v2)
        out['per_E'][E]['%s_vs_%s' % (m1, m2)] = {'spearman': round(float(rho), 3),
                                                 'identical': v1 == v2}
    # 2) ordering on the encoder blocks (adapted on both sides): does |Γ_text| > |Γ_vision| hold for all four
    enc = {m: [abs(g[m][E][b]) for b in ENC] for m in modes}
    out['encoder_ordering'][E] = {
        m: ('text>vision' if enc[m][1] > enc[m][0] else 'vision>text') for m in modes}
    out['encoder_ordering'][E]['all_agree'] = len({out['encoder_ordering'][E][m] for m in modes}) == 1
    # 3) whether the projection heads are zero by construction in the PEFT arms
    out['proj_zero_in_peft'][E] = {m: all(abs(g[m][E][b]) == 0 for b in PROJ) for m in modes}
    # 4) cross-parametrization ratios of the encoder-block coupling (relative to full fine-tuning, per-parameter normalized)
    out['ratios'][E] = {}
    for b in ENC:
        ref = g['full'][E][b]
        out['ratios'][E][b] = {m: (round(g[m][E][b] / ref, 3) if ref != 0 else None)
                               for m in ('lora', 'adapter', 'bitfit')}

summary = {
    'peft_pairwise_identical_all_E': all(
        out['per_E'][E]['%s_vs_%s' % (m1, m2)]['identical']
        for E in Es for m1, m2 in (('lora', 'adapter'), ('lora', 'bitfit'), ('adapter', 'bitfit'))),
    'encoder_ordering_all_agree': all(out['encoder_ordering'][E]['all_agree'] for E in Es),
    'proj_zero_in_peft_all_E': all(all(out['proj_zero_in_peft'][E][m] for m in modes[:1] + modes[1:])
                                   for E in Es),
    'modes': modes, 'blocks': d['blocks'], 'E': Es,
    'note': 'the projection heads (visual/text_projection) are not adapted in the PEFT arms, so their Γ=0 is zero by construction, '
            'hence the cross-parametrization ordering comparison is restricted to the two encoder blocks (adapted on both sides).',
}
json.dump({'summary': summary, **out}, open('outputs/clip_a1_parametrization_summary.json', 'w', encoding='utf-8'),
          indent=1)
print(json.dumps(summary, indent=1, ensure_ascii=False))
for E in Es:
    print(E, 'encoder ordering:', out['encoder_ordering'][E],
          '| ratios:', json.dumps(out['ratios'][E]))
