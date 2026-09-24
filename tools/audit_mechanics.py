"""机械核查: (1) 硬编码 Equation/Table/Figure/Section 编号 vs .aux 实际编号; (2) 浮动体/公式引用完整性。"""
import re
import glob

AUX = 'paper_ap3/main.aux'
aux = open(AUX, encoding='utf-8', errors='ignore').read()
raw = re.findall(r'\\newlabel\{([^}]+)\}\{\{([^}]*)\}\{(\d+)\}', aux)
num_of = {k: page for k, _t, page in raw}
for k, t, _p in raw:
    if '{' not in t:
        num_of[k] = t  # 部分标签第二字段即编号

print('=== 1) 硬编码编号引用 ===')
pat = re.compile(r'(Equation|Eq\.|Table|Figure|Fig\.|Section|Sec\.|Appendix|Corollary|Theorem|Lemma)\s*~?\s*\(?(\d+|[A-Z])\)?')
hits = []
for f in sorted(glob.glob('paper_ap3/sections/*.tex')) + ['paper_ap3/main.tex']:
    for i, line in enumerate(open(f, encoding='utf-8'), 1):
        for m in pat.finditer(line):
            kind, val = m.group(1), m.group(2)
            # 排除 \ref 形式与数学符号
            seg = line[max(0, m.start() - 12):m.start()]
            if '\\ref' in seg or '\\eqref' in seg or '\\label' in seg:
                continue
            if kind in ('Corollary', 'Theorem', 'Lemma') and val.isdigit():
                pass  # 定理编号另核
            hits.append((f.replace('paper_ap3/sections/', ''), i, kind, val, line.strip()[:110]))
for h in hits:
    print('   %-22s:%-4d %s %s | %s' % h)

print()
print('=== 2) 关键标签的真实编号(.aux) ===')
for lab in ['eq:allocation', 'eq:gradflow', 'eq:ode_main', 'thm:repr', 'thm:ode', 'thm:proj',
            'tab:phase', 'tab:sens', 'tab:policy', 'tab:2x2', 'tab:langonly', 'tab:alloc',
            'tab:generalization', 'tab:phase2', 'tab:layergamma', 'tab:gamma_rank',
            'fig:framework', 'fig:ode', 'fig:ers', 'fig:p3ers', 'sec:special', 'sec:crossarch',
            'sec:sens_sched', 'sec:sens_10ep', 'sec:sens_2x2', 'sec:sens_langonly', 'sec:conclusion']:
    print('   %-22s -> %s' % (lab, num_of.get(lab, 'MISSING')))

print()
print('=== 3) 未被引用的 label(公式/表/图/定理) ===')
tex = ''.join(open(f, encoding='utf-8').read() for f in glob.glob('paper_ap3/sections/*.tex') + ['paper_ap3/main.tex'])
all_labels = re.findall(r'\\label\{([^}]+)\}', tex)
refs = set(re.findall(r'\\(?:ref|eqref)\{([^}]+)\}', tex))
unused = [l for l in all_labels if l not in refs]
print('   unused labels:', unused if unused else 'none')
missing = [r for r in refs if r not in all_labels]
print('   refs without label:', missing if missing else 'none')
