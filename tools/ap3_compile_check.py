"""paper_ap3 编译审计：从 main.log 提取错误/未定义引用/重复标签/Overfull 盒，并报告页数。

用法（先跑完 pdflatex ×3 + bibtex）：
    python tools/ap3_compile_check.py            # 默认 paper_ap3
    python tools/ap3_compile_check.py paper_ap3
退出码：0 = 全部通过（无 error / 无 undefined / 无 multiply-defined / 无 Overfull>20pt）
"""
import os
import re
import subprocess
import sys

DIR = sys.argv[1] if len(sys.argv) > 1 else 'paper_ap3'
LOG = os.path.join(DIR, 'main.log')
PDF = os.path.join(DIR, 'main.pdf')

if not os.path.exists(LOG):
    print(f'FATAL: 找不到 {LOG}（先编译）')
    sys.exit(2)

log = open(LOG, encoding='utf-8', errors='replace').read()

errors = re.findall(r'(?m)^!(.*)$', log)
undef_refs = sorted(set(re.findall(r"Reference `([^']+)' on page", log)))
undef_cites = sorted(set(re.findall(r"Citation `([^']+)' on page", log)))
multi = sorted(set(re.findall(r"Label `([^']+)' multiply-defined", log)))
overfull = [float(m) for m in re.findall(r'Overfull \\hbox \((\d+\.\d+)pt', log)]
over20 = [v for v in overfull if v > 20]
underfull = len(re.findall(r'Underfull \\hbox', log))

pages = None
try:
    out = subprocess.run(['pdfinfo', PDF], capture_output=True, text=True, timeout=60).stdout
    m = re.search(r'Pages:\s+(\d+)', out)
    if m:
        pages = int(m.group(1))
except Exception as exc:  # noqa: BLE001
    print(f'(pdfinfo 不可用: {exc!r})')

print(f'== {DIR} 编译审计 ==')
print(f'  页数              : {pages}')
print(f'  errors (!)        : {len(errors)}')
for e in errors[:5]:
    print(f'      {e.strip()[:110]}')
print(f'  undefined refs    : {len(undef_refs)} {undef_refs[:5]}')
print(f'  undefined cites   : {len(undef_cites)} {undef_cites[:5]}')
print(f'  multiply-defined  : {len(multi)} {multi[:5]}')
print(f'  Overfull >20pt    : {len(over20)}')
print(f'  Overfull max      : {max(overfull) if overfull else 0:.5f} pt')
print(f'  Underfull hbox    : {underfull}')

ok = not errors and not undef_refs and not undef_cites and not multi and not over20
print(f'  判定              : {"PASS" if ok else "FAIL"}')
sys.exit(0 if ok else 1)
