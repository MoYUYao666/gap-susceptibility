# -*- coding: utf-8 -*-
"""Correct the stale A23 records: the margin-certificate negative control IS in the working main text."""
import io

H = "HANDOFF.md"
t = io.open(H, encoding="utf-8").read()
anchor = "> | **A23** | **跨域阈值迁移已入稿**"
assert anchor in t, "A23 hand-off row not found"

note = (
    '> \u26a0\ufe0f **2026-10-24 \u66f4\u6b63**\uff1a\u672c\u6587\u4ef6 900 \u884c\u9644\u8fd1\u201c margin '
    '\u8bc1\u4e66 \u2026 \u8bb0\u4e3a negative control\uff0c\u4e0d\u5165\u6b63\u6587 \u201d**\u5df2\u8fc7\u671f**\u2014\u2014'
    '\u8be5\u8d1f\u5bf9\u7167\u81ea 2026-10-19 18:50 \u8d77\u5c31\u5728**\u6b63\u6587**'
    '\uff08`paper_a2/ext_partII_domains.tex`\uff0cResults \u5185\uff0c`main_ieee.tex` \u7684 `\\input`\uff09\uff0c'
    '2026-10-24 \u53c8\u6309\u5f52\u6863\u91cd\u5199\u4e86\u63aa\u8f9e\uff08\u5220\u53bb\u65e0\u5f52\u6863\u652f\u6301\u7684\u201c\u7cbe\u5ea6\u592a\u4f4e\u201d'
    '\u56e0\u679c\u53e5\uff0c\u8865\u4e0a ImageNet-5k \u6709\u6548\u5de5\u4f5c\u70b9\u4e0e\u201c\u4e0d\u4e3b\u5f20\u4efb\u4f55\u4f18\u52bf\u201d\u7684\u8fb9\u754c\uff09\u3002'
    '\u5f52\u6863\u590d\u6838\u89c1 `outputs/analysis/a23_margin_negative_control.json` \u4e0e '
    '`docs/a23_margin_negative_control_paragraph.md`\u3002\n'
)
if "2026-10-24 \u66f4\u6b63" not in t:
    i = t.find(anchor)
    line_end = t.find("\n", i)
    t = t[:line_end + 1] + note + t[line_end + 1:]
    io.open(H, "w", encoding="utf-8", newline="").write(t)
    print("handoff corrected")

O = "docs/A23_REVIEWER_OBJECTIONS.md"
t = io.open(O, encoding="utf-8").read()
old = 'stale: "Recorded as a negative control; OceanCLIP weights are not present locally'
if old in t:
    t = t.replace(old, 'SUPERSEDED (2026-10-24): the adapted-encoder experiment was run and the control is in the working main text; old text was: "Recorded as a negative control; OceanCLIP weights are not present locally', 1)
    io.open(O, "w", encoding="utf-8", newline="").write(t)
    print("reviewer-objections corrected")
else:
    print("reviewer-objections pattern not found (already corrected?)")