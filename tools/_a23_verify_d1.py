"""复核 A23 表格溯源报告中最严重的几条结论（D1/D2/D3/D6/D7/D8），直接打印 JSON 实际值。
不信任报告，只信任这里打印出来的原始字段。"""
import json
import glob
import os


def L(p):
    return json.load(open(os.path.join('outputs', p), encoding='utf-8'))


print('=== D1：tab:degmap/subspace/perimage 的四个"blur"行到底是什么条件 ===')
dm = json.load(open('outputs/degradation_matrix.json', encoding='utf-8'))
print('degradation_matrix.json 顶层键:', list(dm.keys()))
for dom in dm:
    rows = dm[dom].get('rows', [])
    names = [r.get('degrade') for r in rows]
    print('  %-16s 条件名: %s' % (dom, names))
for dom in ('marine_bioclip', 'imagenet_clip'):
    if dom in dm:
        r0, r1 = dm[dom]['rows'][0], dm[dom]['rows'][1]
        print('  %s rows[0] = %s' % (dom, {k: v for k, v in r0.items() if k != 'per_class'}))
        print('  %s rows[1] = %s' % (dom, {k: v for k, v in r1.items() if k != 'per_class'}))
print('  全语料是否存在 marine/imagenet 的 blur 条件:')
anyblur = False
for f in glob.glob('outputs/**/*.json', recursive=True):
    try:
        t = open(f, encoding='utf-8').read()
    except Exception:
        continue
    if '"blur' in t:
        anyblur = True
        import re
        hits = sorted(set(re.findall(r'"(blur[a-z0-9_]*)', t)))[:6]
        print('    %s -> %s' % (f, hits))
print('    （以上为所有含 blur 字段的文件；若只有 sonar，则 marine/imagenet 的 blur 标签无据）'
      if anyblur else '    无任何 blur 字段')

print()
print('=== D1b：同名的 haze 条件在两张表里数值不同？ ===')
od = json.load(open('outputs/ocean_degradation.json', encoding='utf-8'))
print('  ocean_degradation.json bioclip rows:')
for r in od['bioclip']['rows']:
    print('    ', {k: v for k, v in r.items() if k in ('name', 'degrade', 'tau_meas', 'tau_pred')})

print()
print('=== D8：tab:rank1 的"唯一违反"是否成立 ===')
rb = json.load(open('outputs/ocean_rank1_bound.json', encoding='utf-8'))
print('  siglip.rows 键与数值:')
for k, v in rb['siglip']['rows'].items():
    print('    λ=%-5s exact=%.4f corr_gauss=%.4f  违反=%s'
          % (k, v.get('exact', float('nan')), v.get('corr_gauss', float('nan')),
             v.get('exact', 0) > v.get('corr_gauss', 0)))
print('  各模型族违反计数:')
for m in rb:
    if isinstance(rb[m], dict) and 'rows' in rb[m]:
        bad = [(k, round(v['exact'], 4), round(v['corr_gauss'], 4))
               for k, v in rb[m]['rows'].items() if v.get('exact', 0) > v.get('corr_gauss', 0)]
        print('    %-12s 违反 %d 个: %s' % (m, len(bad), bad))

print()
print('=== D2/D3：watertank 表里 UATD domainft 行 ===')
ut = json.load(open('outputs/uatd_protocol.json', encoding='utf-8'))
print('  uatd_protocol.json 顶层键:', list(ut.keys()))
for arm in ut:
    rows = ut[arm].get('rows') if isinstance(ut[arm], dict) else None
    if rows:
        print('  %s: ' % arm, [(r.get('lambda'), r.get('tau_pred'), r.get('tau_meas')) for r in rows])
print('  UATD domainft Δτ = τ(λ=2) − τ(λ=0) =',
      ut['domainft']['rows'][6]['tau_meas'] - ut['domainft']['rows'][4]['tau_meas'])

print()
print('=== D6/D7：tab:matrix 的 imagenet-1k 保留率 ===')
dom2 = json.load(open('outputs/domain_matrix.json', encoding='utf-8'))
print('  domain_matrix.json 顶层键:', list(dom2.keys()))
b = dom2['imagenet5k']['bioclip']
print('  bioclip top1_0=%.2f  rows[4].top1=%.2f  保留率=%.1f%%'
      % (b['top1_0'], b['rows'][4]['top1'], 100 * b['rows'][4]['top1'] / b['top1_0']))
c = dom2['imagenet5k']['clip_tf']
print('  clip_tf top1_0=%.2f  rows[4].top1=%.2f  保留率=%.1f%%'
      % (c['top1_0'], c['rows'][4]['top1'], 100 * c['rows'][4]['top1'] / c['top1_0']))

print()
print('=== D4/D5：tab:matrix 的 sonar 保留率 ===')
sp = json.load(open('outputs/sonar_protocol.json', encoding='utf-8'))
spf = json.load(open('outputs/sonar_protocol_full.json', encoding='utf-8'))
print('  平衡口径 clip_frozen top1_0=%.3f  rows[4].top1=%.3f'
      % (sp['clip_frozen']['top1_0'], sp['clip_frozen']['rows'][4]['top1']))
print('  全量口径 clip_frozen top1_0=%.3f  rows[4].top1=%.3f  保留率=%.1f%%'
      % (spf['clip_frozen']['top1_0'], spf['clip_frozen']['rows'][4]['top1'],
         100 * spf['clip_frozen']['rows'][4]['top1'] / spf['clip_frozen']['top1_0']))
print('  平衡 sonar_ft top1_0=%.3f rows[4].top1=%.3f ｜ 全量 sonar_ft_full top1_0=%.3f rows[4].top1=%.3f'
      % (sp['sonar_ft']['top1_0'], sp['sonar_ft']['rows'][4]['top1'],
         spf['sonar_ft_full']['top1_0'], spf['sonar_ft_full']['rows'][4]['top1']))
