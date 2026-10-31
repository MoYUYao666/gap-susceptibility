# -*- coding: utf-8 -*-
r"""记录 2026-10-05 图来源重绘阶段（含 2 处主张—数据不符的修正）。

    python tools\_docs_figure_rebuild.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENTRY = r"""> **🖼️ 2026-10-05 —— 图来源重绘：9 张全部来源明确，**并捕获 2 处主张与数据不符****
>
> 操作者要求："**把图的来源也做到明确**"。
>
> ### 起点
>
> `docs/PAPERA_FIGURE_PROVENANCE.md` 审计结论：**12 张图里只有 3 张可溯源**；
> 其余 9 张由 **2026-08-22 已不存在的脚本**产出 → **来源不明**，违反"数字必须来自真实 JSON"的要求。
>
> ### 结果：9 张全部重绘，每张都有仓库内脚本 + 明确源 JSON
>
> | 图 | 生成脚本 | 源数据 |
> |---|---|---|
> | `fig1.png` | `tools/_pa_rebuild_figs_rest.py` | `outputs/flickr30k{,_seeds}/**/gap_history.json` |
> | `fig1_ode_fits.png` | 同上 | `outputs/theory/beta_pilot/*/seed*/dg_star_history.json` |
> | `fig2_v5_falsification.png` | 同上 | `outputs/analysis/k_remeasured_both.json` |
> | `fig3.png` | 同上 | `outputs/flickr30k/alpha_*/gap_history.json` |
> | `fig4.png` | 同上 | `outputs/theory/adapter/adapter_all_results.json` |
> | `fig4_effective_rank.png` | 同上 | `outputs/analysis/k_remeasured_both.json` |
> | `fig10_layered_ft.png` | `tools/_pa_rebuild_fig10.py` | `outputs/layered_ft_results.json` |
> | `fig12_zeroshot_more.png` | `tools/_pa_rebuild_fig12.py` | `outputs/zeroshot_extra.json` |
> | `fig14_adapter_layered.png` | `tools/_pa_fix_fig14_title.py` | `outputs/adapter_layered_results.json` |
>
> **共 12/12 来源明确。** 清单已重写：`docs/PAPERA_FIGURE_PROVENANCE.md`
> （脚本 `tools/_write_figure_provenance.py`，会断言清单内脚本均存在）。
>
> ### 🎯 重绘的意外收获：2 处主张与数据不符（**这才是重绘的价值**）
>
> #### ① `fig12` 零样本：`0.8 pp` 主张不成立
>
> 正文与图注称"**all fine-tuned variants stay within 0.8 percentage points** of the frozen baseline"。
>
> | 数据集 | 变体 | 值 | Frozen | 偏差 |
> |---|---|---|---|---|
> | DTD | Text-only | 43.33 | 43.27 | +0.06 |
> | DTD | Both | 42.53 | 43.27 | +0.74 |
> | Food101 | Text-only | 80.67 | 80.60 | +0.07 |
> | **Food101** | **Both** | **79.73** | 80.60 | **+0.87** ← 超 0.8 |
>
> **已改为分变体**：text-only ≤ 0.1 pp、both-position ≤ 0.9 pp。
> （`tools/_pa_fix_zeroshot_claim.py`）——这同时暴露一个更有意义的差别：
> **text-only 的偏差比 both-position 小一个数量级**，与本文主线一致。
>
> #### ② `fig14` Adapter 分层：`frozen-level CG` 主张不成立
>
> 图注称"Training an Adapter on the text side only **reaches frozen-level CG**"，
> **图题**更写成"**Text-only Also Preserves Alignment**"。
>
> | 配置 | CG | R@1 | CG 升幅 |
> |---|---|---|---|
> | Frozen | 0.8143 | 0.6850 | — |
> | Adapter Text-only | 1.0644 | **0.0600** | **+0.250** |
> | Adapter Text+Vis | 1.3168 | 0.0050 | +0.503 |
>
> **两者 CG 都高于 frozen、R@1 都塌陷** → 谈不上"frozen-level"或"preserves alignment"。
> **已改**图注与图题（`tools/_pa_fix_fig14_caption.py`、`tools/_pa_fix_fig14_title.py`），
> 并**保留**原图注中正确的两点披露（layered-configuration 限定、
> "the aggregate cross-dimension comparison does not reproduce a text-only advantage for Adapter"）。
>
> ### 工作方式的改变（本轮最有价值的部分）
>
> **重绘不是"把旧图画一遍"，而是"用归档数据重新核对正文主张"。**
> 每个重绘脚本**先断言正文主张、再画图**——数据不符即报错，不会产出与正文不一致的图。
> 9 张里 2 张的主张经不起核对；**若原样重画或不重绘，这两处会一直留在稿子里**。
>
> **另记一条我自己的错误**：给 `fig10` 设断言时我**臆想了正文没有的主张**
> （"Text-only 崩溃"、"both 全视觉塌陷"），导致断言失败。**正文实际只说
> "Text+Vis-L1 achieves frozen-level CG"（数据 0.8143 vs 0.8137 ✅ 成立）**。
> **教训：先读正文，再设断言。**
>
> ### 编译与合规
>
> NC **43 页**（图片尺寸变化所致，原 42）、Springer **32 页**、0 错误、0 未定义引用、
> cites 44 / bib 44；页数记录已在 `tools/_pa_build_nc_package.py` 与
> `paper合/NC_submission/README.md` 同步（原为过期的"39 页"）。

"""


def main() -> int:
    apply = "--apply" in sys.argv
    p = REPO / "HANDOFF.md"
    t = io.open(p, encoding="utf-8").read()
    if "图来源重绘：9 张全部来源明确" in t:
        print("  已记录，跳过")
        return 0
    anchor = "> **🔢 2026-10-05 —— 实验计数更正"
    i = t.find(anchor)
    if i < 0:
        print("  ⚠ 未找到锚点")
        return 1
    if apply:
        io.open(p, "w", encoding="utf-8", newline="").write(t[:i] + ENTRY + t[i:])
        t2 = io.open(p, encoding="utf-8").read()
        for k in ("12/12 来源明确", "0.87", "+0.250", "先读正文，再设断言", "43 页"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
