"""在核验报告顶部加两处已知错误的批注，防止下游代理照着它把正确数字改错；
并收紧 _a1_fail_scan.py 里几处会误报的正则。"""
import io
import re

# ---------- 1) 核验报告加批注 ----------
P = 'docs/A1_HARDENING_VERIFY.md'
s = io.open(P, encoding='utf-8').read()

BANNER = """
> **⚠ 本文件含两处已知错误——下游请勿照此修改（2026-09-15 由残量修正代理证明）**
>
> 1. **V-4 是误报。** 报告称 12 检查点的超出量区间应为 "+3.06 … +6.06"、并称存储聚合值
>    `excess_stats.min` 有缺陷。**均不成立**：`outputs/a1_h_offset.json →
>    offset_analysis.by_vision_tower.vision_lora_checkspoints.tags` 恰好 12 个 tag 且**包含**
>    取值 +0.54 的 `flickr30k_retrain_both_ep10`；这 12 个值的 mean 3.616667 / sd 1.407456 /
>    min 0.54 / max 6.06 与存储值逐位一致。被排除的第 13 个是 `flickr30k_text_only_r8`
>    （`vision_lora=false`，+0.48），不是 +0.54。且**+3.06 对 12 元素子集算术上不可能**
>    （13 个值里只有 10 个 ≥3.06）。→ 按本报告去改会把正确数字改错。
>
> 2. **V-5 的 "27 个子集里 16 个 τ=+0.50" 是错的。** 重算为 **6/27**（top1_50k 列）或
>    9/27（5k 列）；21 个子集给 +1.00。"16" 对不上任何定义。
>
> 另注：V-11 的 0.006336 归属应为**九个受控种子检查点**，而非报告所写的"12 个视觉 LoRA"。
> 其余各条经复核成立，尤其 §①（τ@k=10 = 0.9262，连 p 值 17 位有效数字精确复现）与
> "无任何数组被重启截断"。

"""

if '本文件含两处已知错误' in s:
    print('批注已存在，跳过')
else:
    lines = s.split('\n')
    # 插在首个标题行之后（若有），否则置顶
    idx = 1 if lines and lines[0].lstrip().startswith('#') else 0
    out = '\n'.join(lines[:idx]) + '\n' + BANNER + '\n'.join(lines[idx:])
    io.open(P, 'w', encoding='utf-8').write(out)
    print('已在 %s 顶部插入批注（%d → %d 字节）' % (P, len(s.encode('utf-8')), len(out.encode('utf-8'))))

# ---------- 2) 收紧扫描器正则 ----------
Q = 'tools/_a1_fail_scan.py'
t = io.open(Q, encoding='utf-8').read()
FIX = [
    (r"r'accuracy.{0,25}improving'", r"r'accuracy[^.]{0,25}improving intervention'"),
    (r"r'\b0\.6\b.{0,20}point'", r"r'0\.0072|\b0\.6\b[^.]{0,15}points? residual'"),
    (r"r'orders? of magnitude[^.]{0,30}small'", r"r'orders? of magnitude[^.]{0,30}[^a-z]small[^a-z]'"),
    (r"r'byte-identic'", r"r'byte-identic(?!ally correct)'"),
]
n = 0
for a, b in FIX:
    if a in t:
        t = t.replace(a, b)
        n += 1
if n:
    io.open(Q, 'w', encoding='utf-8').write(t)
    print('已收紧 %d 处正则（%s）' % (n, Q))
else:
    print('扫描器正则未变（可能此前已收紧）')
