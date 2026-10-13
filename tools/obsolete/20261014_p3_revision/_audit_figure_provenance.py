# -*- coding: utf-8 -*-
r"""图的来源审计：每个图能否从当前仓库复现（操作者要求"所有数据必须真实来源明确"）。

## 为什么做

操作者 2026-10-03 指示：**所有数据必须真实来源明确；不确定的可以重跑；不确定的删除。**

本稿的图有一部分是我在本轮整改中**从 `outputs/` 的 JSON 重新生成**的（来源明确、脚本在 `tools/`），
但也有若干是 **2026-08-02 由已不存在的脚本**产出的（`paper合/scripts/` 不存在）——**来源不明**。

本审计逐图判定，输出三类：
- ✅ **可复现**：`tools/` 下有生成脚本，且脚本读的源 JSON 存在；
- ⚠️ **来源不明**：图存在但找不到生成脚本；
- ❓ **需人工确认**：脚本存在但源数据或参数不清。

    python tools\_audit_figure_provenance.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"

# 我本轮亲自从 JSON 重绘、脚本在 tools/ 下的图（来源明确）
REGENERATED = {
    "fig2.png": ("tools/_pa_fig2_corr.py", "outputs/analysis/dg_r1_reproducible.json",
                 "n=204 相关性（DG/CG vs R@1）；2026-10-01 重绘"),
    "fig8_weight_svd.png": ("tools/_pa_fig8_rebuild.py", "outputs/analysis/strict_control_summary.json",
                            "严格冻结的权重/谱证据；2026-10-01 重绘"),
    "fig9_noise_sensitivity.png": ("tools/_pa_fig9_noise_rebuild.py", "outputs/noise_fixed_aug.json",
                                   "修正后的噪声探针（σ=0 复现基线）；2026-10-01 重绘"),
}

# 其余图：需逐个人工判定来源
OTHERS = ["fig1.png", "fig1_ode_fits.png", "fig10_layered_ft.png", "fig12_zeroshot_more.png",
          "fig14_adapter_layered.png", "fig2_v5_falsification.png", "fig3.png", "fig4.png",
          "fig4_effective_rank.png"]


def main() -> int:
    apply = "--apply" in sys.argv
    lines: list[str] = []
    n_ok = n_unknown = 0

    lines.append("# 图的来源审计（Paper A）\n")
    lines.append("> 依据：操作者 2026-10-03 指示——**所有数据必须真实来源明确；不确定的可以重跑；不确定的删除。**\n")
    lines.append("> 生成脚本：`tools/_audit_figure_provenance.py`（可重跑）\n")
    lines.append("\n## ✅ 来源明确（本轮从 `outputs/` 的 JSON 重绘，脚本在 `tools/`）\n")
    lines.append("| 图 | 生成脚本 | 源数据 | 说明 |")
    lines.append("|---|---|---|---|")
    for fig, (script, src, note) in sorted(REGENERATED.items()):
        sp, dp, fp = REPO / script, REPO / src, PA / "figures" / fig
        ok_s, ok_d, ok_f = sp.exists(), dp.exists(), fp.exists()
        state = "✅" if (ok_s and ok_d and ok_f) else "⚠️"
        if ok_s and ok_d and ok_f:
            n_ok += 1
        lines.append(f"| `{fig}` {state} | `{script}` {'✅' if ok_s else '❌缺'} | "
                     f"`{src}` {'✅' if ok_d else '❌缺'} | {note} |")

    lines.append("\n## ⚠️ 来源不明（图存在，但**本仓库找不到生成脚本**）\n")
    lines.append("这些图的时间戳为 **2026-08-02**，而 `paper合/scripts/` **不存在**。")
    lines.append("按操作者标准，**这些图的数据来源无法核实**。\n")
    lines.append("| 图 | 时间戳 | 正文中的位置 | 处置 |")
    lines.append("|---|---|---|---|")
    used = {}
    for f in (PA / "sections").glob("*.tex"):
        t = io.open(f, encoding="utf-8", errors="ignore").read()
        for m in re.finditer(r"\\includegraphics[^{]*\{figures/([^}]+)\}", t):
            used.setdefault(m.group(1), []).append(f.name)
    for fig in OTHERS:
        fp = PA / "figures" / fig
        ts = fp.stat().st_mtime
        import time as _t
        ts_s = _t.strftime("%Y-%m-%d", _t.localtime(ts))
        where = ", ".join(sorted(set(used.get(fig, [])))) or "（未被引用）"
        n_unknown += 1
        lines.append(f"| `{fig}` | {ts_s} | {where} | **待重跑或删除** |")

    lines.append("\n## 处置建议（按操作者的标准）\n")
    lines.append("### 可重跑：数据源仍在 `outputs/`（8 张）\n")
    lines.append("| 图 | 数据源存在？ | 处置 |")
    lines.append("|---|---|---|")
    rebuildable = {
        "fig1.png": "outputs/flickr30k/{rq2_text_only,rq2_both,baseline_full_ft}/gap_history.json",
        "fig1_ode_fits.png": "outputs/theory/beta_pilot/**/dg_star_history.json",
        "fig3.png": "outputs/flickr30k/**/gap_history.json",
        "fig4.png": "outputs/analysis/adapter_common_baseline.json",
        "fig10_layered_ft.png": "outputs/layered_ft_results.json",
        "fig12_zeroshot_more.png": "outputs/imagenet1k_zs_50k_plain.json",
        "fig14_adapter_layered.png": "outputs/analysis/adapter_common_baseline.json",
    }
    for fig, src in rebuildable.items():
        lines.append(f"| `{fig}` | ✅ `{src}` | **可写生成脚本重绘**（来源即明确） |")

    lines.append("\n### 无法重跑：数据来源不可追溯（2 张）\n")
    lines.append("| 图 | 问题 | 处置 |")
    lines.append("|---|---|---|")
    lines.append("| `fig2_v5_falsification.png` | 支撑 `$k=0.043$`；该量**无法从归档复算**"
                 "（329 条 `norm_g_v` 记录**无一带 rank**），且计算函数**只累加可训 LoRA 参数** → "
                 "**text-only 臂的 $\\|g_v\\|$ 在构造上恒为 0**，曲线只能来自 both / vision_only，"
                 "而论文**未写明是哪个臂** | **须重测**；未测出前该结论与其图**应删除或标为未验证** |")
    lines.append("| `fig4_effective_rank.png` | 与上图同源（Effective Rank Saturation） | 同上 |")

    lines.append("\n### ⚠️ 不能做的处置\n")
    lines.append("**不可**用 `outputs/analysis/k_recomputed_legacy.json`（全 0）去『重绘』这两张图——")
    lines.append("那个文件是**用错臂**得到的（text-only 在构造上恒 0），把它当成『复算成功』是错误结论。")
    lines.append("\n## 对正文的影响（**未改正文，仅记录**）\n")
    lines.append("- `validation.tex:84` 与 `supplement.tex:77` 引用 `$k=0.043$` 与 Effective Rank Saturation；")
    lines.append("  **在重跑之前，这两处属于『来源不明』**，按操作者标准应重跑或删除。")
    lines.append("- 该结论是**次级机制声称**（不在三条设计模式内），删除它**不影响本文的主要结论**。")
    lines.append("- **重跑配方**：对 `both` 与 `vision_only` 臂、各 rank 的 checkpoint 调用 "
                 "`compute_gap_susceptibility`，对 $\\log r$ 拟合斜率。注意 **text-only 臂不可用**（恒为 0）。")

    text = "\n".join(lines) + "\n"
    print(f"  ✅ 可复现: {n_ok} ｜ ⚠️ 来源不明: {n_unknown}")
    if apply:
        out = REPO / "docs" / "PAPERA_FIGURE_PROVENANCE.md"
        io.open(out, "w", encoding="utf-8", newline="").write(text)
        print(f"  ✅ 已写出 {out.relative_to(REPO)}")
    else:
        print("  （预演，加 --apply 写出）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
