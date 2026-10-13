"""ZH 镜像同步：main_zh.tex 里那个头部相关系数仍是 top-10 口径的 0.926，须与 EN 一致改为 top-5 的 0.9125。"""
import io
import re

P = 'paper_a1/main_zh.tex'
s = io.open(P, encoding='utf-8').read()

hits = [m.start() for m in re.finditer(r'0\.926', s)]
print('main_zh.tex 中 "0.926" 出现 %d 次' % len(hits))
for h in hits:
    ln = s[:h].count('\n') + 1
    print('  行 %d: ...%s...' % (ln, s[max(0, h - 70):h + 60].replace('\n', ' ')))

new = s
# 1) τ 相关值：0.926 -> 0.9125
new = new.replace('$\\tau$ $0.926$', '$\\tau$ $0.9125$')
# 2) 相应 p 值：10^{-11} -> 8.5\times10^{-11}（k=5 口径）
new = new.replace('$p{=}10^{-11}$', '$p{=}8.5\\times10^{-11}$')

if new != s:
    io.open(P, 'w', encoding='utf-8').write(new)
    print('已写回；τ 值替换 %d 处，p 值替换 %d 处'
          % (s.count('$\\tau$ $0.926$'), s.count('$p{=}10^{-11}$')))
else:
    print('未发生替换（模式未命中，需人工确认）')

chk = io.open(P, encoding='utf-8').read()
print('复查：仍含 0.926 =', '0.926' in chk, '｜ 含 0.9125 =', '0.9125' in chk)
