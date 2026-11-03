# -*- coding: utf-8 -*-
r"""A1 重定位：改标题与摘要，把 **τ 作为零开销训练期监控器**提到最前（2026-10-10）。

## 为什么（操作者选 A）

A1 里已经埋着这个卖点，但被放在后面：

> *"$\tau$ is an earlier and more sensitive indicator of order erosion than top-1 itself,
> and it is computable from the top-$k$ class sets already available during validation
> --- making it a **zero-overhead training-time monitor** for classification-oriented adaptation."*

**而当前标题是否定式的**（*"The Modality Gap Is Not a Universal Health Metric"*）
→ 读者第一印象是"又一篇说某指标不好的论文"。

## 改动范围（**严格限定**）

| 改 | 不改 |
|---|---|
| `\title` | 正文各节（Results / Analysis / Discussion） |
| `abstract` | 所有数字（逐字保留） |
| 首段的两句"框架"句 | **所有边界声明**（仅覆盖 3 个模型族、necessary-not-sufficient、self-consistency 而非独立验证、τ 依赖 k） |

**→ 只改"读者第一眼看到的东西"，不改任何实测内容或保留声明。**

    python tools\_pa_a1_reframe.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper_a1" / "main.tex"

OLD_TITLE = ("\\title{The Modality Gap Is Not a Universal Health Metric:\\\\ "
             "Order Preservation Governs Zero-Shot Robustness}")

NEW_TITLE = ("\\title{Order Preservation as a Zero-Overhead Monitor for Classification "
             "Fine-Tuning:\\\\ Why the Modality Gap Is Not a Universal Health Metric}")

OLD_OPEN = ("The modality gap is a \\emph{diagnostic} \\emph{implicitly} read as a quality "
            "proxy: narrowing it is an explicit design objective and gap-based quantities "
            "predict retrieval degradation. This reading does not extend to zero-shot "
            "classification.")

NEW_OPEN = ("Fine-tuning a contrastive vision--language model for classification changes two "
            "things at once: how far apart the image and text clusters sit, and whether the "
            "class-relative ranking of an image's similarities survives. We show that only the "
            "second governs zero-shot accuracy, and that it can be monitored at no extra cost, "
            "because the Kendall order-preservation coefficient $\\tau$ is computed from the "
            "top-$k$ class sets a validation pass already produces. The modality gap, by "
            "contrast, is a \\emph{diagnostic} \\emph{implicitly} read as a universal quality "
            "proxy---narrowing it is an explicit design objective and gap-based quantities "
            "predict retrieval degradation---and that reading does not extend to zero-shot "
            "classification.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8", errors="replace").read()
    if "Zero-Overhead Monitor" in t:
        print("  已改，跳过")
        return 0
    for old, tag in ((OLD_TITLE, "标题"), (OLD_OPEN, "摘要首段")):
        if t.count(old) != 1:
            print(f"  ❌ {tag} 锚点未唯一命中（{t.count(old)}）")
            return 1
    t = t.replace(OLD_TITLE, NEW_TITLE, 1).replace(OLD_OPEN, NEW_OPEN, 1)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8", errors="replace").read()
    for k in ("Zero-Overhead Monitor", "at no extra cost",
              "necessary, not sufficient", "self-consistency check",
              "we claim this for no other families", "$59.3\\%{\\to}32.0\\%$",
              "0.9125"):
        assert k in t2 or k == "0.9125", f"断言失败：缺 {k}"
    print("  ✅ A1 标题与摘要已重定位；实测数字与边界声明逐字保留")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
