# -*- coding: utf-8 -*-
r"""修正 `introduction.tex` 里残留的过度声称（2026-10-05 投稿前审核发现）。

## 问题

`introduction.tex` 的这段（**审核扫描"范围词"时发现**）：

> "Recent empirical work has revealed a striking regularity: text-only fine-tuning
> **overwhelmingly preserves cross-modal alignment better than joint-modality fine-tuning**,
> a phenomenon this paper **confirms across 117 experiments on five architectures**"

**两处与本文自身的发现冲突**：

1. **"overwhelmingly … better than joint-modality"** 是无条件声称——而本稿正文
   （`empirical.tex` 设计模式①、`validation.tex`）已明确记录 **SigLIP 上 both 更降间隙**；
2. **"117 experiments on five architectures"** —— 那 117 个实验大多在 **legacy 约定**下跑
   （`src/lora.py` 不冻结基座，text-only 臂实际训练约 1.45 亿参数），**并未隔离"适配位置"**。
   用它们支撑"位置效应"的说法，与本稿自己的 §empirical 披露相矛盾。

## 为什么之前没发现

我在本会话改过 `empirical.tex`、`validation.tex`、`conclusion.tex` 的设计模式与结论段，
**但没改 introduction 的这一句**——它用的是"Regularity"而非"design pattern"措辞，
在按关键词搜索时漏掉了。**本次审核用"范围词扫描"把它捞出来**。

    python tools\_pa_fix_intro_regularity.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "introduction.tex"

OLD = ("Recent empirical work has revealed a striking regularity: text-only fine-tuning "
       "overwhelmingly preserves cross-modal alignment better than joint-modality fine-tuning, a "
       "phenomenon this paper confirms across 117 experiments on five architectures "
       "(Section~\\ref{sec:empirical}).")

NEW = ("Recent empirical work has suggested a striking regularity: that text-only fine-tuning preserves "
       "cross-modal alignment better than joint-modality fine-tuning. This paper examines that "
       "suggestion across 117 experiments on five architectures (Section~\\ref{sec:empirical}) and finds "
       "it holds where the comparison isolates the adaptation site, but not universally: under strict "
       "freezing the ordering reverses on one of the three backbones tested, so which site is preferable "
       "has to be measured rather than assumed.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    c = t.count(OLD)
    if c != 1:
        print(f"  ⚠ 未唯一命中（{c} 次）")
        i = t.find("striking regularity")
        if i > 0:
            print("     实际: …" + t[i:i + 300].replace("\n", " ") + "…")
        return 1
    print("  ✅ 命中过度声称句")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        assert "overwhelmingly preserves cross-modal alignment better" not in t2, "旧说法仍在"
        assert "not universally" in t2 and "has to be measured rather than assumed" in t2
        print("  ✅ 已改为受限表述并断言通过")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
