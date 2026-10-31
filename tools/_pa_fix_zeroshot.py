# -*- coding: utf-8 -*-
r"""Paper A 整改 · 第 2 项：`zero-shot −53.3%` → `zero-shot 56.7 pp`。

## 为什么改（源数据实测）

`outputs/imagenet1k_zs_50k_plain.json`（并有独立重跑验证 `imagenet1k_zs_50k_verify.json`，delta ≤ 0.02）：

| 项 | 值 |
|---|---|
| frozen | **59.28** |
| text_only_r8 | 58.66 |
| both_r8 | 59.67 |
| full_ft 三个种子 | 0.13 / 4.09 / 3.54 → **mean 2.5867** |

三种口径下 `−53.3%` 都不成立：
- 绝对值：`59.28 − 2.5867 = 56.69` → **56.7 pp**
- 相对降幅：`(2.5867−59.28)/59.28 = −95.6%`
- 相对均值：`(2.5867−5.5367)/5.5367 = −53.3%` ← 但 5.5367 无来源

而 `theory.tex:100` 自述 **"Section~\ref{sec:empirical} found … (CG $+24\%$, zero-shot $-53.3\%$)"**，
而 §empirical（`empirical.tex:113`）写的是 **"mean $2.6\%$, range $0.1$–$4.1\%$"** → 两处口径不一致。

`docs/PA_P3_MERGE_PLAN.md`（第九轮 ④）已把该值改为 "56.7 pp"，本项与之一致。

## 不改的相邻项

同句 `CG $+24\%$` **保留**：源数据 `0.190636/0.8186 = 23.29%`，论文写 24%，
属 1pp 内的口径差且已全文一致；改成 23.3% 反而引入新的不一致风险。

    python tools\_pa_fix_zeroshot.py            # 预演
    python tools\_pa_fix_zeroshot.py --apply
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "theory.tex"
OLD = "full fine-tuning explodes the gap (CG $+24\\%$, zero-shot $-53.3\\%$)"
NEW = "full fine-tuning explodes the gap (CG $+24\\%$, zero-shot accuracy collapsing by $56.7$ percentage points, from $59.28\\%$ to $2.6\\%$)"


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if OLD not in t:
        print("  ⚠ 未命中原文；当前该句上下文：")
        i = t.find("explodes the gap")
        print("    " + (t[max(0, i - 60):i + 140] if i >= 0 else "（未找到 'explodes the gap'）"))
        return 1
    print("  ✅ 命中")
    print("     旧: " + OLD)
    print("     新: " + NEW)
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        assert "-53.3\\%" not in t2, "断言失败：仍含 −53.3%"
        assert "56.7" in t2, "断言失败：未写入 56.7"
        print("\n✅ 已改并断言通过")
    else:
        print("\n（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
