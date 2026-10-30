# -*- coding: utf-8 -*-
r"""修 `fig:vision_untouched` 图注的错误 + 微调 `fig:adapter_layered` 图注（2026-10-06）。

## `fig:vision_untouched` 原图注的两处错误

> "Vision-side tensors receiving any update. The dashed line is the total number of vision tensors in
> the frozen model. Both the text-only **and the both-position** strict arms leave the vision side at
> zero, which is the weight-level counterpart of the zero vision gradient measured directly."

| 错 | 实际 |
|---|---|
| 说"**text-only 与 both** 两臂视觉侧都为零" | **both 臂非零**（`vision_rank_delta_mean = −0.0421`） |
| 把"权重不可训"（**必然**）说成"零梯度"（**可测发现**）的证据 | **两者是两回事**：严格冻结下塔权重本就不可训，任何臂都"收到 0 次更新" |

**图已改画 `vision_rank_delta_mean`**（LoRA 对视觉侧的**实际**影响），图注随之重写。

    python tools\_pa_fix_vision_caption.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "supplement.tex"

OLD_V = r"""\caption{Vision-side tensors receiving any update. The dashed line is the total number of vision tensors
in the frozen model. Both the text-only and the both-position strict arms leave the vision side at zero,
which is the weight-level counterpart of the zero vision gradient measured directly.}"""

NEW_V = r"""\caption{What each adaptation position does to the vision side, measured as the change in effective
rank of the vision weights induced by the adapters (mean over layers). Training the text side alone leaves
this at exactly zero, which is the weight-level counterpart of the zero vision gradient measured directly
in Section~\ref{sec:validation}. The both-position and vision-only arms do move the vision side, by
$-0.042$ and $-0.059$ respectively. A count of vision tensors receiving a gradient update would read zero
for all three arms, since under strict freezing the tower's own weights are never trainable; that count
therefore carries no information and is not plotted.}"""

OLD_A = (r"\caption{Adapter layered fine-tuning. Both Adapter configurations raise the gap above the "
         r"frozen reference ($0.81$), the text-side one by $0.25$ and its text+vision counterpart by "
         r"$0.50$, and both collapse retrieval to near zero ($R@1$ $0.06$ and $0.005$); this is a "
         r"layered-configuration comparison, and the aggregate cross-dimension comparison in "
         r"Section~\ref{sec:validation} does not reproduce a text-only advantage for Adapter.}")

NEW_A = (r"\caption{Adapter layered fine-tuning, both panels sharing the epoch axis. Both Adapter "
         r"configurations raise the gap above the frozen reference of $0.81$: the text-side one by "
         r"$0.25$ and its text-plus-vision counterpart by $0.50$. Retrieval collapses in both, to $R@1$ "
         r"$0.06$ and $0.005$ against a frozen baseline of $0.69$, so neither configuration preserves "
         r"either quantity. This is a layered-configuration comparison; the aggregate cross-dimension "
         r"comparison in Section~\ref{sec:validation} does not reproduce a text-only advantage for "
         r"Adapter.}")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    n = 0
    for old, new, why in ((OLD_V, NEW_V, "fig:vision_untouched 图注（改画后重写）"),
                          (OLD_A, NEW_A, "fig:adapter_layered 图注（补 frozen baseline）")):
        c = t.count(old)
        if c == 1:
            print(f"  ✅ {why}")
            if apply:
                t = t.replace(old, new, 1)
            n += 1
        else:
            print(f"  ⚠ {why}：命中 {c} 次")
    if apply and n:
        io.open(F, "w", encoding="utf-8", newline="").write(t)
        t2 = io.open(F, encoding="utf-8").read()
        assert "and the both-position" not in t2, "旧的错误表述仍在"
        for k in ("$-0.042$", "$-0.059$", "carries no information and is not plotted",
                  "sharing the epoch axis", "frozen baseline of $0.69$"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ 已改 {n} 处并断言通过")
    else:
        print(f"\n  {n}/2（{'预演' if not apply else '部分失败'}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
