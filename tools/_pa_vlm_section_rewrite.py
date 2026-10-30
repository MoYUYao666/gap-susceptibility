# -*- coding: utf-8 -*-
r"""改写 `paper合/sections/supplement.tex` 的 E 节（解码器 VLM）（2026-10-10）。

## 为什么改（操作者选 A）

**论文原主张**（`discussion.tex`）：*"adapting the vision tower alone is **again the least
effective choice**, moving the gap by $11\%$ where the other two arms move it by $74\%$ and
$84\%$ … the **both-position arm reduces the gap most**"* —— **依据 `tab:vlm` 的单 seed 4-bit 结果**。

**3-seed bf16 实测**（`outputs/vlm_seeds_bf16/`，9 run）：

| 臂 | n | $DG^*$ 相对变化 | CG 跨度 |
|---|---|---|---|
| `text_only` | 3 | **+66.8 ± 6.5%** | 0.2053 ± 0.1505 |
| `vision_only` | 3 | **+12.4 ± 4.7%** | 0.3421 ± 0.0644 |
| `both` | 3 | **+85.2 ± 11.2%** | 0.3595 ± 0.2352 |

**（逐 seed）**
- `text_only`：59.4 / 70.0 / 71.1 %
- `vision_only`：17.7 / 11.0 / 8.5 %
- `both`：73.1 / 87.5 / **95.1 %** ← 单 seed 时看到的 73.1% 是最低值

## 三个结论（都可核）

1. **`vision_only` 确实最弱**：`text_only` vs `vision_only` = **4.9 sd**（CG 尺度）→ 显著；
2. **但 `both` 并不比 `text_only` 好**：−0.23 sd（CG）→ **不显著**（论文说 `both` 最好，**错**）；
3. **原 4-bit 单 seed 的数字是种子运气**：`both` 逐 seed 从 73.1% 到 **95.1%**。

## 另加

**4-bit 不可复现**（`bitsandbytes`）：同 seed 两次 `cg_span` = 0.3041 / 0.4073；
**bf16 逐位相同**（0.110064 / 0.110064）。→ 新表用 bf16 **3 seed**。

## 改动

1. 协议段：改为 bf16、batch 2、3 seed；**删掉"bf16 不可行"的不准确表述**（实测可行）
2. `tab:vlm`：换为 3-seed 均值 ± sd
3. 加一段：4-bit 不可复现的说明 + 为什么改 bf16

    python tools\_pa_vlm_section_rewrite.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "supplement.tex"

# ① 协议段整体替换
OLD_PROTO = ("""The protocol is $400$ samples for three epochs at batch $4$, rank $8$ and learning rate $10^{-4}$. All three
arms use four-bit quantisation. That choice was forced rather than preferred: at bfloat16 the vision-only
arm had not completed a single epoch after $27$ minutes, against $2.4$ minutes per epoch for text-only,
whereas at four-bit the same arm completes three epochs in $5.4$ minutes. Applying the same setting to all
three arms keeps them comparable to one another, which is what the comparison requires.""")

NEW_PROTO = ("""The protocol is $400$ samples for three epochs at batch $2$, rank $8$ and learning rate $10^{-4}$, and
every configuration is run at three seeds; we report means with the spread across seeds. Precision is an
issue we had to settle before the comparison could be made. Our first runs used four-bit quantisation,
which is not reproducible: repeating one configuration with an identical seed changes the measured gap
span from $0.304$ to $0.407$, because the quantised matrix multiplications are not deterministic. The same
configuration in bfloat16 reproduces bit for bit ($0.110\,064$ on both of two repeated runs). All results
below are therefore bfloat16. At batch $2$ this fits the single available accelerator, and the vision-only
arm, which had not completed an epoch at batch $4$ in bfloat16, completes its three epochs in $3.3$ to
$5.0$ minutes.""")

# ② 表 + 表注整体替换
OLD_TAB = r"""\begin{table}[h]
\centering
\caption{Adaptation site on a decoder-based VLM under strict freezing. Qwen2-VL-2B-Instruct, $400$
samples, three epochs, batch $4$, rank $8$, four-bit quantisation, one seed. $DG^*$ is the paired squared
distance after normalisation; the relative change is quoted because the arms begin from different values.}
\label{tab:vlm}
\footnotesize
\begin{tabular}{lccc}
\toprule
Arm & Trainable & $DG^*_0 \to DG^*_3$ & Relative change \\
\midrule
Both-position   & $14{,}494{,}912$ & $0.636 \to 0.103$ & $\mathbf{-83.8\%}$ \\
Text-only       & $9{,}232{,}384$  & $0.710 \to 0.185$ & $-73.9\%$ \\
Vision-only     & $5{,}262{,}528$  & $2.176 \to 1.937$ & $-11.0\%$ \\
\bottomrule
\end{tabular}
\end{table}"""

NEW_TAB = r"""\begin{table}[h]
\centering
\caption{Adaptation site on a decoder-based VLM under strict freezing. Qwen2-VL-2B-Instruct, $400$
samples, three epochs, batch $2$, rank $8$, bfloat16, three seeds. $DG^*$ is the paired squared distance
after normalisation. The reduction in $DG^*$ is quoted as a percentage of the arm's own starting value
because vision-only starts $3.7$ to $8.8$ times higher than the other two arms; the centroid gap starts at
comparable values ($1.34$--$1.37$ for vision-only against $0.20$--$0.70$), and we quote its span alongside
so that the comparison does not rest on the normalisation alone.}
\label{tab:vlm}
\footnotesize
\begin{tabular}{lcccc}
\toprule
Arm & Trainable & $DG^*$ reduction & Seed range & CG span \\
\midrule
Both-position   & $14{,}494{,}912$ & $+85.2\pm11.2\%$ & $73.1$--$95.1$ & $0.360\pm0.235$ \\
Text-only       & $9{,}232{,}384$  & $+66.8\pm6.5\%$  & $59.4$--$71.1$ & $0.205\pm0.151$ \\
Vision-only     & $5{,}262{,}528$  & $+12.4\pm4.7\%$  & $8.5$--$17.7$  & $0.342\pm0.064$ \\
\bottomrule
\end{tabular}
\end{table}

The seed spread is what the comparison turns on. Vision-only is clearly the weakest arm: its reduction in
$DG^*$ is non-overlapping with the other two, and on the centroid gap it is separated from text-only by
$4.9$ pooled standard deviations. The other pair is not resolved. Both-position reduces $DG^*$ by more than
text-only, but its values range from $73.1\%$ to $95.1\%$ across three seeds, and on the centroid gap the
two arms differ by $0.23$ pooled standard deviations, which is no difference at all. A single seed is
enough to produce the appearance of a large and orderly effect: the first seed we ran puts both-position at
$73.1\%$ against text-only at $59.4\%$, whereas the second and third put it at $87.5\%$ and $95.1\%$ against
$70.0\%$ and $71.1\%$. We therefore report the arm ordering on this model as unresolved between
both-position and text-only, and we do not use it as evidence about which adaptation site is preferable."""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n1, n2 = t.count(OLD_PROTO), t.count(OLD_TAB)
    print(f"=== 锚点：协议段 {n1} ｜ 表 {n2} ===")
    if n1 != 1 or n2 != 1:
        print("  ❌ 未唯一命中")
        return 1
    t2 = t.replace(OLD_PROTO, NEW_PROTO, 1).replace(OLD_TAB, NEW_TAB, 1)
    if not apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_vlm")
    if not bak.exists():
        io.open(bak, "w", encoding="utf-8", newline="").write(
            io.open(F, encoding="utf-8").read())
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    for k in ("$+85.2\\pm11.2\\%$", "$+66.8\\pm6.5\\%$", "$+12.4\\pm4.7\\%$",
              "0.304$ to $0.407$", "reproduces bit for bit", "$4.9$ pooled standard deviations",
              "$0.23$ pooled standard deviations", "unresolved between"):
        assert k in t3, f"断言失败：缺 {k}"
    assert "one seed" not in t3.split("\\label{tab:vlm}")[1][:400], "表注仍写 one seed"
    print("  ✅ E 节已改写：协议（bf16/3 seed）、表（均值±sd）、4-bit 不可复现说明")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
