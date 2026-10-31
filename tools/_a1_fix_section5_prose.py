# -*- coding: utf-8 -*-
"""Last residual stale mention in the A1 venue record.

Section 5's intro sentence still told a reader to update the three A23 places to
"submitted to Image and Vision Computing", while the table beneath it now says
Neurocomputing.  Rewrite the sentence to point at the table instead of naming a journal,
so it cannot go stale again if the venue changes."""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, 'docs', 'A1_VENUE_DECISION.md')

OLD = ('OE 稿中有三处描述 A1 状态的文字，现均写"A1 的修订版正在准备另投他刊"；'
       '当 A1 **实际提交之后**、OE 提交**之前**，这三处必须更新为"已投稿 Image and Vision Computing"。')
NEW = ('OE 稿中有三处描述 A1 状态的文字，现均写"A1 的修订版正在准备另投他刊"；'
       '当 A1 **实际提交之后**、OE 提交**之前**，这三处必须更新为**下表"改为"列给出的文本**'
       '（刊名以表中为准，现为 Neurocomputing；A1 的最终目标刊见本文件第八节）。')

with io.open(DOC, encoding='utf-8') as f:
    text = f.read()

n = text.count(OLD)
if n != 1:
    print('ABORT: expected 1 occurrence of the intro sentence, found %d' % n)
    sys.exit(1)
text = text.replace(OLD, NEW)

if 'Image and Vision Computing' in text.split('## 五、')[1].split('## 六、')[0]:
    print('ABORT: section 5 still names Image and Vision Computing')
    sys.exit(1)

with io.open(DOC, 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)
print('OK: section 5 no longer hard-codes a journal name; it points at the table')
