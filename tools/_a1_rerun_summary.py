"""汇总 A1 λ_reg 重跑结果（修好质心索引 bug 后的正确数字）。"""
import os
import json
import glob

ROOT = 'outputs/a1_class_aligned'
rows = []
for d in sorted(glob.glob(os.path.join(ROOT, 'lr*'))):
    lam_name = os.path.basename(d)
    for sd in sorted(glob.glob(os.path.join(d, 'seed*'))):
        p = os.path.join(sd, 'results.json')
        if not os.path.exists(p):
            continue
        r = json.load(open(p, encoding='utf-8'))
        rows.append((lam_name, r.get('seed'), r.get('top1_50k'), r.get('val_loss'),
                     r.get('tau_final'), r.get('ema', True),
                     r['history'][-1].get('align_loss')))

print('=== 全部端点（results.json）===')
print('%-12s %-6s %10s %10s %10s %8s' % ('dir', 'seed', 'top1_50k', 'val_loss', 'tau_final', 'align'))
for a, b, c, d2, e, ema, al in rows:
    print('%-12s %-6s %10s %10s %10s %8.4f%s'
          % (a, b, ('%.2f' % c) if c is not None else 'None',
             '%.4f' % d2, ('%.4f' % e) if e is not None else '-', al,
             '' if ema else '  [no-EMA]'))

print()
print('=== λ 剂量-响应：三种子均值±样本sd（seed 42/123/456）===')
print('%-8s %-28s %-28s' % ('λ', 'top-1 50k (mean±sd)', 'val_loss (mean±sd)'))
for lam in ('lr0.0', 'lr0.05', 'lr0.1', 'lr0.25', 'lr0.5', 'lr1.0'):
    ts, vs = [], []
    for a, b, c, d2, e, ema, al in rows:
        if a == lam and ema and c is not None:
            ts.append(c)
            vs.append(d2)
    if not ts:
        continue
    def ms(v):
        m = sum(v) / len(v)
        sd = (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5 if len(v) > 1 else 0.0
        return m, sd
    mt, st = ms(ts)
    mv, sv = ms(vs)
    print('%-8s %-28s %-28s n=%d' % (lam, '%.2f ± %.2f' % (mt, st),
                                     '%.4f ± %.4f' % (mv, sv), len(ts)))

print()
print('=== 早停表（λ=0, seed 42, 逐 epoch eval JSON）===')
d0 = os.path.join(ROOT, 'lr0.0', 'seed42')
print('%-6s %8s %10s %10s' % ('epoch', 'tau', 'top1_50k', 'val_loss'))
for ep in (1, 2, 3, 5, 10):
    p = os.path.join(d0, 'eval_epoch%d.json' % ep)
    if os.path.exists(p):
        r = json.load(open(p, encoding='utf-8'))
        print('%-6d %8.4f %10.2f %10.4f' % (ep, r['tau_final'], r['top1_50k'], r['val_loss']))
