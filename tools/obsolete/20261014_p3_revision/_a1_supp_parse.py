"""解析 a1_supplement.log：抽出所有 eval-only 端点/逐 epoch 结果，汇总剂量-响应。"""
import json
import os
import re
from collections import defaultdict

LOG = 'a1_supplement.log'
txt = open(LOG, encoding='utf-8', errors='replace').read()
txt = txt.replace('\r', '')

print('=== 日志规模 ===')
print(f'  {len(txt):,} 字符')
res = re.findall(r'eval-only lr([\d.]+) ep(\d+): tau=([-\d.]+) top1_50k=([\d.]+) val_loss=([\d.]+)', txt)
print(f'  抓到 {len(res)} 条 eval-only 结果')

table = defaultdict(dict)
for lam, ep, tau, top1, val in res:
    table[float(lam)][int(ep)] = (float(tau), float(top1), float(val))

print()
print('=== 各 (λ_reg, seed) 的端点（epoch 10）===')
print(f'{"λ_reg":>7} {"seed":>5} {"tau":>8} {"top1_50k":>9} {"val_loss":>9}   来源文件')
for lam in sorted(table):
    for seed in (123, 456):
        p = f'outputs/a1_class_aligned/lr{lam}/seed{seed}/eval_epoch10.json'
        if os.path.exists(p):
            d = json.load(open(p, encoding='utf-8'))
            print(f'{lam:>7} {seed:>5} {d["tau_final"]:>8.4f} {d["top1_50k"]:>9.3f} {d["val_loss"]:>9.4f}   {p}')
        else:
            print(f'{lam:>7} {seed:>5} {"(缺)":>8}')

print()
print('=== 剂量-响应汇总（含原有 seed42）===')
print(f'{"λ_reg":>7} {"n":>3} {"top1 50k (mean±sd)":>24} {"tau (mean±sd)":>20} {"val_loss (mean±sd)":>22}')
for lam in sorted(table):
    rows = []
    for seed in (42, 123, 456):
        p = f'outputs/a1_class_aligned/lr{lam}/seed{seed}/eval_epoch10.json'
        if os.path.exists(p):
            rows.append(json.load(open(p, encoding='utf-8')))
    if not rows:
        continue
    def ms(k):
        v = [r[k] for r in rows]
        m = sum(v) / len(v)
        sd = (sum((x - m) ** 2 for x in v) / len(v)) ** 0.5 if len(v) > 1 else 0.0
        return m, sd, v
    m1, s1, v1 = ms('top1_50k')
    m2, s2, v2 = ms('tau_final')
    m3, s3, v3 = ms('val_loss')
    print(f'{lam:>7} {len(rows):>3} {m1:>16.2f} ± {s1:<5.2f} {m2:>14.4f} ± {s2:<5.4f} {m3:>16.4f} ± {s3:<5.4f}')
    print(f'         top1 逐 seed {[round(x,2) for x in v1]} | val_loss {[round(x,4) for x in v3]}')

print()
print('=== λ=0 的逐 epoch（早停表补种子）===')
for seed in (42, 123, 456):
    eps = sorted(table.get(0.0, {})) if seed == 42 else []
    p = f'outputs/a1_class_aligned/lr0.0/seed{seed}'
    fs = sorted(int(m.group(1)) for f in os.listdir(p) if (m := re.match(r'eval_epoch(\d+)\.json$', f))) if os.path.isdir(p) else []
    print(f'  seed {seed}: 已评 epoch {fs}')
    for e in fs:
        d = json.load(open(f'{p}/eval_epoch{e}.json', encoding='utf-8'))
        print(f'     ep{e:>2}: tau={d["tau_final"]:.4f} top1={d["top1_50k"]:.3f} val={d["val_loss"]:.4f}')
