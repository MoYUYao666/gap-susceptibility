# -*- coding: utf-8 -*-
r"""落账：**更正** E-A 的 Simpson 结论（n=3 假象，n=30 推翻）（2026-10-12）。

## 必须更正的原因

我在 HANDOFF 里写过"E-A 留出检验出结果（**推翻性**）"，结论是
"τ 的池化相关由数据集身份承载，组内反向 → Simpson 悖论 → 推翻核心主张"。

**该结论基于 n=3（每数据集 3 个 seed），是噪声假象。**
补评 100 个逐 epoch 检查点后（`tools/_p218`）：

| 检验 | n=3（错） | **n=30（对）** |
|---|---|---|
| 组内 Spearman(τ, top1) | **−0.268** | **+0.8401**（4/4 正） |
| 池化 vs 组内差 | +1.02 | **−0.08（无悖论）** |
| 去数据集均值后 τ–top1 | +0.039 | **+0.7883** |
| 单 seed 轨迹 | — | **+0.9451（10/10 正）** |

**必须写明：错的一方是我（以及方法学审稿人），不是论文。**

    python tools\_docs_correct_expA.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **⚠️⚠️ 2026-10-12 —— **更正**：E-A 的 "Simpson 悖论" 结论是 **n=3 的噪声假象**，已被 n=30 推翻**
>
> ### 更正什么
>
> 本文件上一条目（"E-A 留出检验出结果（推翻性）"）声称：
> *"τ 的池化相关由数据集身份承载，组内反向（−0.27）→ Simpson 悖论 → 推翻核心主张"*。
>
> **该结论错误。** 它基于 **每数据集仅 3 个 seed（n=3）**，而 n=3 的 Spearman 只取
> {−1, −0.5, 0, +0.5, +1} 几个离散值，**信噪比极低**。
>
> ### 补做的实验（`tools/_p218_eval_all_epochs.py`）
>
> 发现 `outputs/a1_rr_ckpt/**/epoch{1..10}.pt` **共 100 个检查点全部存在且权重各不相同**
> （96/96 张量逐 epoch 变化，`tools/_p213` 验证），而论文只评了 `epoch10` 的 13 个。
> **补评 87 个（纯 forward，28 分钟，无需训练）** → 每数据集 **n=30**。
>
> ### 结果（`outputs/a1_epoch_sweep.json` + `tools/_p219`）
>
> | 检验 | n=3（**错**） | **n=30（对）** |
> |---|---|---|
> | 组内 Spearman(τ, top1) | **−0.268** | **+0.8401**（4/4 数据集为正） |
> | 池化 Spearman | +0.750 | +0.7599 |
> | 池化−组内（Simpson 指标） | **+1.02** | **−0.08**（无悖论） |
> | 去数据集均值后 τ–top1 | +0.039 | **+0.7883** |
> | **单 seed 轨迹**（最干净） | — | **+0.9451（10/10 为正）** |
>
> **逐数据集**：coco **+0.670**(t=4.78)｜dtd **+0.970**(t=21.2)｜flickr30k **+0.915**(t=6.42)｜
> food101 **+0.397**(t=2.29)。
>
> **交叉验证**：新评的 `epoch10` 与旧归档逐位吻合（coco seed42/43/44 = 0.5754/58.14、
> 0.5756/56.94、0.5759/57.56，与 `a1_h_offset.json` 完全一致）
> → **不是计算错误，而是采样不足。**
>
> ### 结论
>
> **论文的核心主张（order preservation governs zero-shot accuracy）在组内成立，
> 且比池化更强。** 之前的"推翻"是**我和方法学审稿人共同的过度解读**：
> 我们拿 3 个点算相关，把一个方向正确的强信号读成了反向。
>
> **仍未证伪、仍需修的问题**（这些是真的）：
> 1. `highlights.tex:14` 的 r=1.000 **未加限定**（正文已降级为自洽检查）
> 2. 摘要首句 "Only the second governs" 与自家 Table 1 冲突（Table 1 是必要的反例）
> 3. "zero-overhead" 无开销测量；"matches to four decimals" 实为三位（0.0019）
> 4. `abstract.tex` 是"改了标题没改正文"的半成品；`main_zh.tex` 仍是旧标题
> 5. `docs/A1_VENUE_DECISION.md` 仍写"在 Neurocomputing 在审"（实况 10-10 已拒）
> 6. 合成 surgery 位移 100% 沿 gap 方向，真实 LoRA 86.0–99.7% 正交 → +3.62±1.41 点偏移未解释
> 7. 论文 L473 的池化 ρ=0.786 **跨 4 个数据集** → 应改用组内统计（n=30 的 +0.84）或明确标注
> 8. 监控器缺少"用它做过决策"的演示（数据已在手，可补）
>
> **证据文件**：`outputs/a1_epoch_sweep.json`、`outputs/analysis/a1_epoch_sweep_analysis.json`、
> `tools/_p213_ckpt_verify.py`、`tools/_p218_eval_all_epochs.py`、`tools/_p219_analyze_epoch_sweep.py`
"""


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "更正：E-A" in t or "n=3 的噪声假象" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("n=3 的噪声假象", "+0.8401", "+0.9451", "不是计算错误，而是采样不足",
              "我和方法学审稿人共同的过度解读"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加更正（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
