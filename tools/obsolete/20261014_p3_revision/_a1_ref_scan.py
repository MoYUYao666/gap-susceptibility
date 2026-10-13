"""扫描 revision_additions.tex 的 \ref 目标：区分三类——指向正文(需存在)、指向本文件自己的块、以及悬空。"""
import io
import re
import glob

RE_LABEL = re.compile(r'\\label\{([^}]+)\}')
RE_REF = re.compile(r'\\ref\{([^}]+)\}')


def labels_of(path):
    try:
        return set(RE_LABEL.findall(io.open(path, encoding='utf-8').read()))
    except Exception:
        return set()


main_labels = labels_of('paper_a1/main.tex')
rw_labels = labels_of('paper_a1/related_work.tex')
for f in glob.glob('paper_a1/*.tex'):
    if f.endswith(('main.tex', 'revision_additions.tex', 'related_work.tex')):
        continue
    main_labels |= labels_of(f)

rev = io.open('paper_a1/revision_additions.tex', encoding='utf-8').read()
rev_labels = labels_of('paper_a1/revision_additions.tex')
refs = set(RE_REF.findall(rev))

print('main.tex 里的 label 数 = %d' % len(labels_of('paper_a1/main.tex')))
print('related_work.tex 里的 label 数 = %d' % len(rw_labels))
print('revision_additions.tex 里的 \\label 数 = %d，\\ref 目标数 = %d' % (len(rev_labels), len(refs)))
print()
dangling = sorted(r for r in refs if r not in main_labels and r not in rw_labels and r not in rev_labels)
to_main = sorted(r for r in refs if r in main_labels)
to_self = sorted(r for r in refs if r in rev_labels and r not in main_labels and r not in rw_labels)
print('→ 指向正文/相关工作的（须存在）: %d 个' % len(to_main))
for r in to_main:
    print('     %s' % r)
print('→ 仅指向本文件自身块（合并进正文后须一并带入）: %d 个' % len(to_self))
for r in to_self:
    print('     %s' % r)
print('→ 悬空（两边都没有）: %s' % (dangling if dangling else '无 ✓'))
print()
print('"lem:inversion" 是否仍被引用:', 'lem:inversion' in refs)
