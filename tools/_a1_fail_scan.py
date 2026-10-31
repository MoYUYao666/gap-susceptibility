"""判定核验的 18 条 FAIL 在两个文件里是否已修：逐条按特征串检索。"""
import io
import re

TARGETS = [
    ('V-14 λ=-0.5 误称为提升精度', [r'accuracy[^.]{0,25}improving intervention', r'提升精度的干预']),
    ('V-5 "survives and strengthens"', [r'survive[ds]?[^.]{0,40}strengthen', r'加强']),
    ('V-2 E3 残差界 0.0072/0.6', [r'0\.0072', r'0\.0072|\b0\.6\b[^.]{0,15}points? residual']),
    ('V-8 默认模板"第三"', [r'third of five', r'第三']),
    ('V-7 界 ±0.05', [r'\\?p?m\\?0\.05', r'±0\.05']),
    ('V-10 比值 6-25x', [r'6\s*[-–]\s*25\\?times', r'6--25']),
    ('V-4 偏移下界 +0.54', [r'\+0\.54']),
    ('V-11 "orders of magnitude too small"', [r'orders? of magnitude[^.]{0,30}[^a-z]small[^a-z]', r'数量级']),
    ('V-1 运行时长 147.7', [r'147\.7']),
    ('V-3 CG -0.2150', [r'-0\.2150']),
    ('V-6 收缩区间 0.58-0.68', [r'0\.58[^0-9]{0,6}0\.68']),
    ('V-12a "byte-identically"', [r'byte-identic(?!ally correct)', r'字节完全一致']),
    ('V-12b "re-measures everything"', [r're-?measures? everything', r'重新测量一切']),
    ('V-12c CUDA 崩溃声明', [r'illegal memory access', r'CUDA.{0,15}crash']),
    ('V-15 精度变动 1.0-1.2', [r'1\.0[^0-9]{0,6}1\.2\s*points']),
]

FILES = [('docs/A1_HARDENING.md', '报告'), ('paper_a1/revision_additions.tex', '稿件块19')]

for path, tag in FILES:
    try:
        s = io.open(path, encoding='utf-8').read()
    except Exception as e:
        print('%s 读取失败: %s' % (path, e))
        continue
    print('=' * 70)
    print('%s（%s） 行数 %d，字节 %d' % (path, tag, s.count('\n') + 1, len(s.encode('utf-8'))))
    if path.endswith('.tex'):
        nb, ne = len(re.findall(r'\\begin\{', s)), len(re.findall(r'\\end\{', s))
        print('  结构: \\begin %d / \\end %d  %s' % (nb, ne, 'OK' if nb == ne else '!! 不匹配'))
        print('  \\label %d 个；含 sec:hardening: %s' % (len(re.findall(r'\\label\{', s)), 'sec:hardening' in s))
        print('  末尾: %s' % s.rstrip().split('\n')[-1][:90])
    print('  --- 残留的 FAIL 特征 ---')
    hits = 0
    for name, pats in TARGETS:
        found = []
        for p in pats:
            for m in re.finditer(p, s, re.I):
                ln = s[:m.start()].count('\n') + 1
                found.append(ln)
        if found:
            hits += 1
            print('    [未修] %-38s 行 %s' % (name, sorted(set(found))[:6]))
    if hits == 0:
        print('    （无残留特征 → 该文件应已全部修正）')
    print('  合计残留类别: %d' % hits)
