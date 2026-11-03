# -*- coding: utf-8 -*-
r"""修 `fig9` 图注末尾**自相矛盾**的那句（2026-10-06）。

## 问题

`supplement.tex` 里 `fig:noise_sensitivity` 的图注**结尾**仍留着：

> "… the claim is withdrawn and the line of evidence is not used.
> **（B--C) Effective rank under frozen vs.\ fine-tuned.**"

**`(B--C)` 出现两次，第二次讲的是 "effective rank"——那是另一张图（`fig4_effective_rank`）的内容**，
属旧版图注残留。读者会以为 B/C 面板画的是 effective rank，
而实际面板是：**A** 修正探针按 σ 分组的 drop%、**B** σ=0 对照、**C** 测得比值 vs 声称的 2.6×。

（先前有个 `_pa_fix_fig9_caption.py` 只改了前半句，**没处理这个尾部残留**。）

    python tools\_pa_fix_fig9_caption_tail.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "supplement.tex"

OLD = ("(C) The measured vision-to-text ratio at $\\sigma{=}0.1$ ($0.76$), against the $2.6\\times$ "
       "claimed by that earlier probe; the claim is withdrawn and the line of evidence is not used. "
       "(B--C) Effective rank under frozen vs.\\ fine-tuned.}")

NEW = ("(C) The magnitude of the retrieval change at $\\sigma{=}0.1$ for each encoder, with the "
       "$2.6\\times$ ratio the earlier probe claimed marked as a dotted line; the measured ratio is "
       "$0.76\\times$, and that line of evidence is withdrawn and not used. Error bars are standard "
       "deviations over five seeds. Panels~A and~B use the corrected design: constant-seed augmentation "
       "replay and noise drawn from the run seed, with $\\sigma{=}0$ reproducing the baseline exactly.}")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    c = t.count(OLD)
    if c != 1:
        print(f"  ⚠ 未唯一命中（{c} 次）")
        i = t.find("(C) The measured vision-to-text ratio")
        if i > 0:
            print("   实际：")
            print("   " + repr(t[i:i + 340]))
        return 1
    print("  ✅ 命中 fig9 图注里矛盾的 (B--C) 尾句")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        assert "(B--C) Effective rank under frozen" not in t2, "旧句仍在"
        for k in ("dotted line", "0.76", "five seeds", "constant-seed augmentation"):
            assert k in t2, f"断言失败：缺 {k}"
        print("  ✅ 已改并断言通过（矛盾尾句已删，图注与实际面板逐项对应）")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
