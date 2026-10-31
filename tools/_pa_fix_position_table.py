# -*- coding: utf-8 -*-
r"""Paper A 整改 · `tab:position`：数据来源核实 + 表注纠正 + 协议披露。

## 核实（数值全部溯源成功）

| 表行 | 源 run | 实测 CGΔ | 可训参数 |
|---|---|---|---|
| Flickr30k text-only | `outputs/flickr30k/rq2_text_only` | **−0.0635** → 表内 −0.064 ✅ | **145,170,177** |
| Flickr30k both | `outputs/flickr30k/rq2_both` | **−0.0324** → −0.032 ✅ | 131,290,881 |
| COCO text-only | `outputs/coco/rq2_text_only_coco` | −0.0405 → −0.041 ✅ | 145,170,177 |
| COCO both | `outputs/coco/rq2_both_coco` | **−0.0524** → −0.052 ✅ | 131,290,881 |

→ **表内数值用的是 legacy（非严格冻结）协议**。

## 两个问题（均已修）

1. **表注过强**：`"Text-only consistently produces the smallest gap increase."`
   而 **COCO 行 both(−0.052) 优于 text-only(−0.041)** —— "consistently" **被本表自己的数据推翻**。
   → 改为按数据集描述，并点明 COCO 为例外。
2. **协议未披露**：该表与随后引用的严格冻结 5-seed 值**是两套协议**，同段混用会误导。
   → 在表注中写明 legacy 约定及其含义。

    python tools\_pa_fix_position_table.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

OLD = ("\\caption{Effect of LoRA position on CG$\\Delta$. Text-only consistently produces the smallest gap "
       "increase.}")
NEW = ("\\caption{Effect of LoRA position on CG$\\Delta$ under the earlier adaptation convention, in which the "
       "LoRA backbone was not frozen (Section~\\ref{sec:empirical} states the consequence: these arms differ in "
       "which adapters are injected, not in which encoders receive updates, so the comparison does not isolate "
       "a siting choice). Text-only gives the smaller gap increase on Flickr30k, BLIP-1 and ViT-L, while MS-COCO "
       "reverses that ordering.}")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if OLD not in t:
        print("  ⚠ 未命中表注；当前：")
        i = t.find("Effect of LoRA position")
        print("    " + (t[i - 20:i + 200].replace("\n", " ") if i >= 0 else "（未找到）"))
        return 1
    print("  ✅ 命中 tab:position 表注")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        assert "consistently produces the smallest" not in t2, "断言失败：过强表述仍在"
        assert "not isolate " in t2, "断言失败：未写入协议披露"
        print("  ✅ 已改并断言通过")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
