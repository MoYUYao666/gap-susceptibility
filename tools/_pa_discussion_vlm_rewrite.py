# -*- coding: utf-8 -*-
r"""改写 `discussion.tex` 的 **Second** limitation（解码器 VLM）（2026-10-10）。

## 原文（站不住）

> *"…adapting the vision tower alone is **again the least effective choice**, moving the gap by
> $11\\%$ where the other two arms move it by $74\\%$ and $84\\%$ … the **both-position arm reduces
> the gap most** … This evidence is preliminary in three respects: it rests on a single model and
> a single seed, the runs use four-bit quantisation …"*

## 为什么改（操作者选 A）

**3-seed bf16 实测**（`outputs/vlm_seeds_bf16/`）：

| 臂 | $DG^*$ 相对变化（3 seed） | CG 跨度 |
|---|---|---|
| `text_only` | $+66.8\\pm6.5\\%$（59.4–71.1） | $0.205\\pm0.151$ |
| `vision_only` | $+12.4\\pm4.7\\%$（8.5–17.7） | $0.342\\pm0.064$ |
| `both` | $+85.2\\pm11.2\\%$（73.1–**95.1**） | $0.360\\pm0.235$ |

- ✅ `vision_only` **确实最弱**（CG 上 $4.9$ sd）
- ❌ **`both` 并不优于 `text_only`**（CG 上 $0.23$ sd = **无差别**）
- ❌ 原 4-bit 单 seed 的数字是**种子运气**（`both` 逐 seed 73.1% → 95.1%）
- ❌ 且 **4-bit 不可逐位复现**（同 seed 0.304 / 0.407），**bf16 可以**（0.110064 ×2）

    python tools\_pa_discussion_vlm_rewrite.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "discussion.tex"

OLD = (r"""Second, our study covers contrastive dual-encoder architectures and one decoder-based VLM. The decoder model, Qwen2-VL-2B under strict freezing, reproduces the framework's qualitative behaviour: the distribution gap follows a clear exponential decay under both the text-only and both-position arms, the position of adaptation changes the trajectory as it does in the dual-encoders, and adapting the vision tower alone is again the least effective choice, moving the gap by $11\%$ where the other two arms move it by $74\%$ and $84\%$ (Section~\ref{sec:vlm} of the supplement). What does not carry over is the identity of the best position: on this model the both-position arm reduces the gap most, whereas the three contrastively pre-trained dual-encoders place text-only first. That is the same conclusion the main text reaches from the dual-encoder comparisons --- the ordering is stable within a configuration but the preferable site is not --- now observed across an architecture family boundary. This evidence is preliminary in three respects: it rests on a single model and a single seed, the runs use four-bit quantisation for all three arms so that they remain internally comparable, and the scale is small ($400$ samples, three epochs), which is adequate for establishing the ordering but not for reporting final accuracy. Whether the framework extends to generation-oriented objectives, as distinct from decoder architectures, remains untested.""")

NEW = (r"""Second, our study covers contrastive dual-encoder architectures and one decoder-based VLM. The decoder model, Qwen2-VL-2B under strict freezing, reproduces part of the framework's qualitative behaviour: the distribution gap decays under every arm, and adapting the vision tower alone is again the weakest choice, reducing $DG^*$ by $12.4\pm4.7\%$ against $66.8\pm6.5\%$ for text-only and $85.2\pm11.2\%$ for both positions, a separation of $4.9$ pooled standard deviations on the centroid gap (Section~\ref{sec:vlm} of the supplement). What does not carry over is the ordering between the two stronger arms. On this model the both-position arm does not reduce the gap more than the text-only arm in any way we can resolve: the two differ by $0.23$ pooled standard deviations on the centroid gap, and the both-position reduction ranges from $73.1\%$ to $95.1\%$ across three seeds against $59.4\%$ to $71.1\%$ for text-only. A single seed is sufficient to manufacture an orderly ranking here, which is why we report three and why we draw no conclusion from this model about which site is preferable. Our first runs also used four-bit quantisation, which we subsequently found not to be reproducible: repeating one configuration with an identical seed changed the measured gap span from $0.304$ to $0.407$, because the quantised matrix multiplications are not deterministic. The decoder results above are therefore bfloat16, which reproduces bit for bit. Whether four-bit quantisation materially changes the ordering on the dual-encoder backbones, where the reported runs use it for the vision-side arms, is not something we have established. The remaining qualifications are the scale ($400$ samples, three epochs, one model) and the fact that whether the framework extends to generation-oriented objectives, as distinct from decoder architectures, remains untested.""")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"=== 锚点命中 {n} ===")
    if n != 1:
        return 1
    t2 = t.replace(OLD, NEW, 1)
    if not apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_vlm")
    if not bak.exists():
        io.open(bak, "w", encoding="utf-8", newline="").write(
            io.open(F, encoding="utf-8").read())
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    for k in (r"$12.4\pm4.7\%$", r"$66.8\pm6.5\%$", r"$85.2\pm11.2\%$",
              r"$4.9$ pooled standard deviations", r"$0.23$ pooled standard deviations",
              "not to be reproducible", "bfloat16, which reproduces bit for bit"):
        assert k in t3, f"断言失败：缺 {k}"
    assert "the least effective choice" not in t3, "旧主张仍在"
    assert "single model and a single seed" not in t3, "旧'单 seed'措辞仍在"
    print("  ✅ discussion 的 Second limitation 已改写")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
