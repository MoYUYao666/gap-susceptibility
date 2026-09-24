"""07_discussion.tex 第 23 行(局限段)外科修复: 删除重复片段 + 把 Sixteenth 移到 Fifteenth 之后 + 修断句。"""
import re

p = 'paper_ap3/sections/07_discussion.tex'
lines = open(p, encoding='utf-8').read().split('\n')
l = lines[22]

i16 = l.index('Sixteenth, the $\\Delta E$ signs are')
i15 = l.index('Fifteenth, the counterfactual experiments')
end16 = l.index('not modeled).') + len('not modeled).')
assert i16 < end16 < i15, (i16, end16, i15)

sixteenth = l[i16:end16]
duplicate = l[end16:i15]
fifteenth = l[i15:]
print('duplicate fragment (to delete), len=%d:' % len(duplicate))
print('   ', duplicate[:150].replace('\n', ' '), '...')
print('   ...', duplicate[-120:].replace('\n', ' '))

new_l = l[:i16] + fifteenth + ' ' + sixteenth

# 断句修复
new_l = new_l.replace('is undetermined Eighth, the two pipelines', 'is undetermined. Eighth, the two pipelines')
new_l = new_l.replace('(Section~\\ref{sec:crossarch}). the reported 1-epoch', '(Section~\\ref{sec:crossarch}). The reported 1-epoch')

# 校验: 重复片段不应再出现; 序数顺序应为 ...Fifteenth...Sixteenth...
assert 'Sixteenth' in new_l and 'Fifteenth' in new_l
assert new_l.index('Fifteenth,') < new_l.index('Sixteenth,')
assert 'undetermined. Eighth' in new_l
assert '. The reported 1-epoch' in new_l

lines[22] = new_l
open(p, 'w', encoding='utf-8').write('\n'.join(lines))
print()
print('OK: line 23 now %d chars (was %d)' % (len(new_l), len(l)))
print('ordinal order check: Fifteenth @%d < Sixteenth @%d' % (new_l.index('Fifteenth,'), new_l.index('Sixteenth,')))
print('remaining "at rank 6" occurrences:', len(re.findall(r'at rank 6', new_l)))
