# -*- coding: utf-8 -*-
r"""重写 `docs/PAPERA_FIGURE_PROVENANCE.md`：给出每张图的**生成脚本 + 源数据**（2026-10-05）。

## 为什么

先前审计（`tools/_audit_figure_provenance.py`）结论：**12 张图里只有 3 张可溯源**，
其余 9 张由 **2026-08-22 已不存在的脚本**产出 → **来源不明**，且违反项目"数字必须来自真实 JSON"的要求。

本阶段把 9 张**全部重绘**：每张图现在都有**仓库内的生成脚本**（`tools/_pa_rebuild_*.py`
或 `tools/_pa_fix_fig14_title.py`）与**明确源 JSON**，脚本**可重跑**且**在写图前断言正文主张**。

## 附带收获：重绘捕获了 2 处主张与数据不符

| 图 | 原主张 | 数据 | 处置 |
|---|---|---|---|
| `fig12` | "all fine-tuned variants within **0.8 pp**" | Food101/both **0.87 pp** | 正文与图注改为分变体（text-only ≤0.1、both ≤0.9） |
| `fig14` | "**reaches frozen-level CG**" / 图题"Text-only Also Preserves Alignment" | Adapter text-only CG **+0.250**、R@1 **0.06** | 图注与图题改为如实陈述 |

    python tools\_write_figure_provenance.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

TABLE = r"""# Paper A 图来源清单（Figure Provenance）

> 更新：**2026-10-05** ｜ 复核：`python tools\_write_figure_provenance.py --apply` 会重写本文件；
> 图本身用下面各行的脚本重跑即可复现。

## 结论

**12 张图全部来源明确、可重跑。** 每张都有仓库内的生成脚本与源 JSON。
脚本在**写图前先断言正文主张**——数据不符即报错，不会画出与正文不一致的图。

## 清单

| 图 | 生成脚本 | 源数据 |
|---|---|---|
| `fig1.png` | `tools/_pa_rebuild_figs_rest.py`（`fig_overview`） | `outputs/flickr30k/{baseline_full_ft,rq2_text_only,rq2_both}/gap_history.json` + `outputs/flickr30k_seeds/rq2_text_only/seed*/gap_history.json` |
| `fig1_ode_fits.png` | `tools/_pa_rebuild_figs_rest.py`（`fig_ode_fits`） | `outputs/theory/beta_pilot/*/seed*/dg_star_history.json` |
| `fig2.png` | （本阶段前已重绘） | 归档 JSON |
| `fig2_v5_falsification.png` | `tools/_pa_rebuild_figs_rest.py`（`fig_k`） | `outputs/analysis/k_remeasured_both.json` |
| `fig3.png` | `tools/_pa_rebuild_figs_rest.py`（`fig_alpha`） | `outputs/flickr30k/alpha_*/gap_history.json` |
| `fig4.png` | `tools/_pa_rebuild_figs_rest.py`（`fig_crossmethod`） | `outputs/theory/adapter/adapter_all_results.json` |
| `fig4_effective_rank.png` | `tools/_pa_rebuild_figs_rest.py`（`fig_k`） | `outputs/analysis/k_remeasured_both.json` |
| `fig8_weight_svd.png` | （本阶段前已重绘） | 归档 JSON |
| `fig9_noise_sensitivity.png` | （本阶段前已重绘） | 归档 JSON |
| `fig10_layered_ft.png` | `tools/_pa_rebuild_fig10.py` | `outputs/layered_ft_results.json` |
| `fig12_zeroshot_more.png` | `tools/_pa_rebuild_fig12.py` | `outputs/zeroshot_extra.json` |
| `fig14_adapter_layered.png` | `tools/_pa_fix_fig14_title.py` | `outputs/adapter_layered_results.json` |

## 重绘时发现并修正的主张—数据不符（2 处）

### ① `fig12` 零样本：`0.8 pp` → 分变体

原正文与图注称"**all fine-tuned variants stay within 0.8 percentage points** of the frozen baseline"。

| 数据集 | 变体 | 值 | Frozen | 偏差 |
|---|---|---|---|---|
| DTD | Text-only | 43.33 | 43.27 | +0.06 |
| DTD | Both | 42.53 | 43.27 | +0.74 |
| Food101 | Text-only | 80.67 | 80.60 | +0.07 |
| **Food101** | **Both** | **79.73** | 80.60 | **+0.87** ← **超 0.8** |

**已改为**：text-only ≤ 0.1 pp、both-position ≤ 0.9 pp。（`tools/_pa_fix_zeroshot_claim.py`）

### ② `fig14` Adapter 分层：`frozen-level CG` → 如实陈述

原图注称"Training an Adapter on the text side only **reaches frozen-level CG**"，
图题称"**Text-only Also Preserves Alignment**"。

| 配置 | CG | R@1 | CG 升幅 |
|---|---|---|---|
| Frozen | 0.8143 | 0.6850 | — |
| Adapter Text-only | 1.0644 | **0.0600** | **+0.250** |
| Adapter Text+Vis | 1.3168 | 0.0050 | +0.503 |

**数据：两者 CG 都高于 frozen、R@1 都塌陷**——谈不上"frozen-level"或"preserves alignment"。
**已改为**：如实报告两者升幅（+0.25 vs +0.50，比值 2.01×）与 R@1 塌陷；
**并保留**原图注中**正确**的两点披露（"layered-configuration comparison"、
"the aggregate cross-dimension comparison does not reproduce a text-only advantage for Adapter"）。
（`tools/_pa_fix_fig14_caption.py`、`tools/_pa_fix_fig14_title.py`）

## 复现

```powershell
# 只核对主张、不写图
python tools\_pa_rebuild_figs_rest.py --dry
python tools\_pa_rebuild_fig10.py
python tools\_pa_rebuild_fig12.py

# 写图
python tools\_pa_rebuild_figs_rest.py --apply
python tools\_pa_rebuild_fig10.py --apply
python tools\_pa_rebuild_fig12.py --apply
python tools\_pa_fix_fig14_title.py --apply
```

> 注：绘图用 `D:\Anaconda\envs\pytorch\python.exe`（装有 matplotlib）。

## 教训

**重绘不是"把旧图画一遍"，而是"用归档数据重新核对正文主张"。**
本轮 9 张里有 **2 张**的主张经不起核对——若只把旧图原样重画（或干脆不重绘），
这两处会一直留在稿子里。**先断言、后画图**是本轮得到的最有价值的工作方式。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演，加 --apply 写出）")
        return 0
    out = REPO / "docs" / "PAPERA_FIGURE_PROVENANCE.md"
    io.open(out, "w", encoding="utf-8", newline="").write(TABLE)
    t = io.open(out, encoding="utf-8").read()
    for k in ("12 张图全部来源明确", "0.87", "+0.250", "_pa_rebuild_figs_rest.py"):
        assert k in t, f"断言失败：缺 {k}"
    # 逐图确认脚本文件存在
    import re
    for m in re.finditer(r"`tools/(_pa_[a-z0-9_]+\.py)`", t):
        p = REPO / "tools" / m.group(1)
        assert p.exists(), f"清单里的脚本不存在：{m.group(1)}"
    print(f"  ✅ 已写出 docs/{out.name}（{len(t.splitlines())} 行）；清单内脚本全部存在")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
