"""(A1 后处理) 从 clip_peft_gamma_ordering.json 提炼可写入论文的结论:
  - PEFT 三种参数化之间的块序一致性(逐 E 的 Spearman);
  - 与全参数化的对比中, 只在"两边都被适配"的编码器块上比较(投影头在 PEFT 臂中未适配, Γ=0 属构造性为零);
  - 编码器块耦合的跨参数化比值(逐参数归一化后)。
输出: outputs/clip_a1_parametrization_summary.json
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
    # 1) PEFT 三者之间的排序一致性(全 4 块, 逐参数归一化)
    for m1, m2 in (('lora', 'adapter'), ('lora', 'bitfit'), ('adapter', 'bitfit')):
        v1 = [g[m1][E][b] for b in d['blocks']]
        v2 = [g[m2][E][b] for b in d['blocks']]
        rho, p = stats.spearmanr(v1, v2)
        out['per_E'][E]['%s_vs_%s' % (m1, m2)] = {'spearman': round(float(rho), 3),
                                                 'identical': v1 == v2}
    # 2) 编码器块(两边都被适配)上的排序: |Γ_text| > |Γ_vision| 是否四者一致
    enc = {m: [abs(g[m][E][b]) for b in ENC] for m in modes}
    out['encoder_ordering'][E] = {
        m: ('text>vision' if enc[m][1] > enc[m][0] else 'vision>text') for m in modes}
    out['encoder_ordering'][E]['all_agree'] = len({out['encoder_ordering'][E][m] for m in modes}) == 1
    # 3) 投影头在 PEFT 臂中是否构造性为零
    out['proj_zero_in_peft'][E] = {m: all(abs(g[m][E][b]) == 0 for b in PROJ) for m in modes}
    # 4) 编码器块耦合的跨参数化比值(相对全参数化, 逐参数归一化)
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
    'note': '投影头(visual/text_projection)在 PEFT 臂中未被适配, 其 Γ=0 属构造性为零, '
            '故跨参数化的排序比较限定在两个编码器块上(两边都被适配)。',
}
json.dump({'summary': summary, **out}, open('outputs/clip_a1_parametrization_summary.json', 'w', encoding='utf-8'),
          indent=1)
print(json.dumps(summary, indent=1, ensure_ascii=False))
for E in Es:
    print(E, 'encoder ordering:', out['encoder_ordering'][E],
          '| ratios:', json.dumps(out['ratios'][E]))
