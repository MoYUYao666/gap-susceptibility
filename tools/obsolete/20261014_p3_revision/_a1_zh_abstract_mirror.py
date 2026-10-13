# -*- coding: utf-8 -*-
"""Mirror the English abstract edits of tools/_a1_vector_and_repo.py into the
Chinese reference master paper_a1/main_zh.tex.

main_zh.tex is a reference translation that is not submitted, but the standing rule
is that it stays faithful, so the restored task-sensitivity ordering and the four
prose trims are mirrored sentence by sentence.  Exact hit counts are asserted."""
import io, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZH = os.path.join(ROOT, 'paper_a1', 'main_zh.tex')

PAIRS = [
    ('缩小它是对齐方法中的显式设计目标', '缩小它是显式设计目标',
     'abstract: drop "in alignment methods"'),
    ('而其自带留出集上的旧训练期记录器给出', '而其自带留出集上的旧记录器给出',
     'abstract: legacy logger'),
    ('我们报告区间并注明协议，而不是取较大的那个', '我们只报区间与协议，而不取较大的那个',
     'abstract: quote the range and the protocol'),
    ('并预测——经我们证实——平移文本侧的破坏性远小于平移图像侧。',
     '并预测——经我们证实——平移文本侧的破坏性小于平移图像侧。',
     'abstract: shorten theory prediction'),
    ('鸿沟则保留给检索；我们不把这些结论外推到其他编码器家族、基准或自适应机制。',
     '鸿沟则保留给检索，并给出任务敏感度谱系（质心分类 $<$ 零样本分类 $<$ 检索）；'
     '我们不把这些结论外推到其他编码器家族、基准或机制。',
     'abstract: RESTORE task-sensitivity ordering'),
]

with io.open(ZH, encoding='utf-8') as f:
    text = f.read()

log = []
for old, new, label in PAIRS:
    n = text.count(old)
    if n != 1:
        print('ABORT: %s -- expected 1 occurrence, found %d' % (label, n))
        sys.exit(1)
    text = text.replace(old, new)
    log.append('  OK  ' + label)

with io.open(ZH, 'w', encoding='utf-8', newline='') as f:
    f.write(text)

print('applied %d mirrors into paper_a1/main_zh.tex:' % len(log))
for line in log:
    print(line)

abs_zh = text.split('\\begin{abstract}', 1)[-1].split('\\end{abstract}', 1)[0]
print('')
print('ZH abstract now contains the ordering: %s' % ('yes' if '谱系' in abs_zh else 'NO'))
