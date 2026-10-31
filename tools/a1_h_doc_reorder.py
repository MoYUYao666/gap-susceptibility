"""One-off: reorder docs/A1_HARDENING.md so the sections run 1,2,3,4,5, then append section 6.

The five items were appended as they completed, which put section 4 before section 3. This script
moves the blocks by their headings and never edits their contents.
"""
import io
import os

P = 'docs/A1_HARDENING.md'
S3 = '## ③ Prompt-template sensitivity'
S4 = '## ④ Bootstrap confidence intervals for τ'
S5 = '## ⑤ Explaining the systematic offset'

with io.open(P, encoding='utf-8') as f:
    txt = f.read()

i3, i4, i5 = txt.index(S3), txt.index(S4), txt.index(S5)
assert i4 < i3 < i5, 'unexpected order: %d %d %d' % (i3, i4, i5)

head = txt[:i4]
block4 = txt[i4:i3]
block3 = txt[i3:i5]
tail = txt[i5:]

out = head + block3 + block4 + tail
out = out.rstrip('\n') + '\n'

with io.open(P, 'w', encoding='utf-8') as f:
    f.write(out)

# report the new heading order
order = [ln for ln in out.splitlines() if ln.startswith('## ')]
print('heading order:')
for o in order:
    print('  ' + o)
print('bytes:', len(out.encode('utf-8')))
