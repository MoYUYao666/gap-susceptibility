"""收尾小改：① 判定并修 A1 检查点计数 ② A23 三处补 et al. ③ 处理 qwen2vl 许可标注。
全部带计数校验：不匹配就报告并跳过，绝不盲改。"""
import io
import json
import re
import os

LOG = []


def show(msg):
    print(msg)
    LOG.append(msg)


# ---------- ① A1 检查点计数：先取证 ----------
show('=== ① 检查点计数取证 ===')
off = json.load(open('outputs/a1_h_offset.json', encoding='utf-8'))
cps = off.get('offset_analysis', {}).get('by_vision_tower', {}).get('vision_lora_checkspoints', {})
tags = cps.get('tags', [])
show('  offset JSON 的 12 个 tag: %s' % tags)
paths = []
for c in off.get('offset_analysis', {}).get('checkpoints', []):
    paths.append((c.get('tag') or c.get('name'), c.get('ckpt') or c.get('path')))
for t, p in paths[:15]:
    show('    %-28s %s' % (t, p))
show('  指向 a1_retrain 的条目: %s' % [t for t, p in paths if p and 'a1_retrain' in str(p)])
show('  指向 imagenet_zs 的条目: %s' % [t for t, p in paths if p and 'imagenet_zs' in str(p)])
for f in ('outputs/a1_retrain/text_only/epoch10.pt', 'outputs/a1_retrain/both/epoch10.pt',
          'outputs/imagenet_zs/text_only_r8/best_checkpoint.pt',
          'outputs/imagenet_zs/both_r8/best_checkpoint.pt'):
    if os.path.exists(f):
        show('    %-56s %d B' % (f, os.path.getsize(f)))
    else:
        show('    %-56s 不存在' % f)

# ---------- ② A23：三处作者列表补 et al. ----------
show('')
show('=== ② A23 作者列表补 et al. ===')
A2 = 'paper_a2/main.tex'
s = io.open(A2, encoding='utf-8').read()
before = s

# chen2025 / jian2024 / qin2022：把「前 3 位作者, et al.」缺失的写法补齐
FIXES = [
    (r'(\\bibitem\[Chen et al\.\(2025\)\]\{chen2025\})([^\n]*?)(\.\s*(?:Underwater|ACM|In:))',
     r'\1\2, et al.\3'),
    (r'(\\bibitem\[Jian et al\.\(2024\)\]\{jian2024\})([^\n]*?)(\.\s*(?:Underwater|Intelligent|In:))',
     r'\1\2, et al.\3'),
    (r'(\\bibitem\[Qin et al\.\(2022\)\]\{qin2022\})([^\n]*?)(\.\s*(?:A survey|Remote|In:))',
     r'\1\2, et al.\3'),
]
n = 0
for pat, rep in FIXES:
    hits = re.findall(pat, s)
    if len(hits) == 1:
        s = re.sub(pat, rep, s, count=1)
        n += 1
        show('  已补 et al.: %s' % pat.split(']')[0].split('[')[-1])
    else:
        show('  跳过（命中 %d 次，需人工确认）: %s' % (len(hits), pat[:60]))

# ---------- ③ A23：qwen2vl 许可标注 ----------
show('')
show('=== ③ qwen2vl2024 许可标注 ===')
m = re.search(r'\\bibitem\[Qwen Team\(2024\)\]\{qwen2vl2024\}([^\n]*)', s)
if m:
    show('  当前该条: ...%s' % m.group(1)[-160:])
    if 'CC-BY-4.0' in m.group(1) or 'CC-BY-4.0' in s[max(0, m.start() - 40):m.end() + 200]:
        pass

if s != before:
    io.open(A2, 'w', encoding='utf-8').write(s)
    show('  已写回 %s（改动 %d 处）' % (A2, n))
else:
    show('  %s 未改动' % A2)

io.open('_final_touchups.log', 'w', encoding='utf-8').write('\n'.join(LOG))
