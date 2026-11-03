# -*- coding: utf-8 -*-
r"""把 `fig8` 与 `fig9` **由 1×3 面板拆成各自独立的单面板图**（2026-10-06，操作者建议）。

## 为什么

操作者："**可以分成三个图片啊，没必要挤在一起**"。

**对**。原先 1×3 面板挤在 **3.713 in 宽**的画布里 → 每面板仅 **1.24 in 宽**，
标题/轴标签/图例必然重叠（这正是 `fig8`、`fig9` 坏掉的原因）。
拆开后每张占满栏宽（**3.713 in**），单面板高 2.67 in，**只占版心高 31%**，一页绰绰有余。

## 产出

| 原图 | 拆成 | 内容 |
|---|---|---|
| `fig8_weight_svd` | `fig8a_rank_delta.png` | A：严格冻结下视觉/文本侧**有效秩变化** |
| | `fig8b_budget.png` | B：**可训参数预算**（严格 vs 旧协议，log 轴） |
| | `fig8c_vision_untouched.png` | C：**收到更新的视觉张量数** |
| `fig9_noise_sensitivity` | `fig9a_noise_sweep.png` | A：修正探针，按 σ 分组的 R@1 变化 |
| | `fig9b_sigma0_control.png` | B：σ=0 对照（必须精确为 0） |
| | `fig9c_ratio.png` | C：测得比值 vs 旧文声称的 2.6× |

**同时修正 `fig8` 图注的两处错误**：原写 "**A/B--D**"（四个面板，实际三个）、
且描述为 "Mean $\|\Delta W\|_F$ … SVD"（**与实际内容完全不符**）。

    python tools\_pa_split_appendix_figs.py [--apply]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from figure_style import apply_style, figsize_wide, save, OKABE_ITO  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
apply_style()
import matplotlib.pyplot as plt     # noqa: E402
import numpy as np                  # noqa: E402

FIGDIR = ROOT / "paper合" / "figures"
CV, CT = OKABE_ITO["blue"], OKABE_ITO["vermil"]
CG, CGR = OKABE_ITO["green"], OKABE_ITO["grey"]


def _one() -> tuple:
    """单面板：占满 0.78\\textwidth，h/w = 0.72。"""
    return plt.subplots(figsize=figsize_wide(0.72))


def fig8() -> None:
    d = json.loads((ROOT / "outputs" / "analysis" / "strict_control_summary.json")
                   .read_text(encoding="utf-8"))
    cfgs, names = d["configs"], ["text_only", "both", "vision_only"]
    lab = {"text_only": "text", "both": "both", "vision_only": "vision"}
    ntr = [cfgs[k]["n_trainable_params"] for k in names]
    dvis = [cfgs[k]["vision_rank_delta_mean"] for k in names]
    dtext = [cfgs[k]["text_rank_delta_mean"] for k in names]
    legacy = d["legacy"]["legacy text-only (single)"]["n_trainable_params"]
    nz = [cfgs[k]["vision_nonzero_tensors"][0] for k in names]
    ntot = d["frozen"]["tensors"]
    x = np.arange(3)

    # A
    fig, ax = _one()
    ax.bar(x - 0.2, dvis, 0.4, color=CV, edgecolor="black", linewidth=0.4, label="Vision side")
    ax.bar(x + 0.2, dtext, 0.4, color=CT, edgecolor="black", linewidth=0.4,
           hatch="//", label="Text side")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels([lab[k] for k in names])
    ax.set_ylabel(r"$\Delta$ effective rank (mean over layers)")
    ax.legend(frameon=False, ncol=2, loc="upper right", handlelength=1.2)
    save(fig, FIGDIR / "fig8a_rank_delta.png"); plt.close(fig)

    # B
    fig, ax = _one()
    ax.bar([0, 1, 2], ntr, 0.55, color=CV, edgecolor="black", linewidth=0.4)
    ax.bar([3], [legacy], 0.55, color=CGR, edgecolor="black", linewidth=0.4)
    ax.set_yscale("log")
    ax.set_xticks([0, 1, 2, 3])
    ax.set_xticklabels(["text", "both", "vision", "text\n(legacy)"])
    ax.set_ylabel("Trainable parameters")
    ax.text(1, max(ntr) * 2.2, "strict freezing", ha="center", fontsize=7.5, color=CV)
    ax.text(3, legacy * 2.2, "not used as evidence", ha="center", fontsize=7.5, color=CGR)
    save(fig, FIGDIR / "fig8b_budget.png"); plt.close(fig)

    # C
    fig, ax = _one()
    ax.bar(x, nz, 0.5, color=CG, edgecolor="black", linewidth=0.4)
    ax.axhline(ntot, color=CGR, ls="--", lw=1.0)
    ax.set_xticks(x); ax.set_xticklabels([lab[k] for k in names])
    ax.set_ylabel("Vision tensors receiving an update")
    ax.set_ylim(0, ntot * 1.45)
    ax.text(0.96, 0.88, f"frozen total = {ntot}", transform=ax.transAxes,
            ha="right", va="top", fontsize=7.5, color=CGR)
    save(fig, FIGDIR / "fig8c_vision_untouched.png"); plt.close(fig)
    print("  ✅ fig8 → fig8a / fig8b / fig8c")
    assert nz[0] == 0, "text-only 的 vision_nonzero 应为 0"


def fig9() -> None:
    d = json.loads((ROOT / "outputs" / "noise_fixed_aug.json").read_text(encoding="utf-8"))
    rows = d["rows"]
    sigs = sorted({round(r["sigma"], 3) for r in rows})
    vis = {s: [r["drop_pct"] for r in rows if r["encoder"] == "vision" and abs(r["sigma"] - s) < 1e-9] for s in sigs}
    txt = {s: [r["drop_pct"] for r in rows if r["encoder"] == "text" and abs(r["sigma"] - s) < 1e-9] for s in sigs}
    v01, t01 = float(np.mean(vis[0.1])), float(np.mean(txt[0.1]))
    ratio = abs(v01 / t01)

    # A
    fig, ax = _one()
    x, w = np.arange(len(sigs)), 0.34
    ax.bar(x - w / 2, [np.mean(vis[s]) for s in sigs], w,
           yerr=[np.std(vis[s], ddof=1) for s in sigs], capsize=3,
           color=CV, edgecolor="black", linewidth=0.4, label="Vision")
    ax.bar(x + w / 2, [np.mean(txt[s]) for s in sigs], w,
           yerr=[np.std(txt[s], ddof=1) for s in sigs], capsize=3,
           color=CT, edgecolor="black", linewidth=0.4, hatch="//", label="Text")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(["0", "0.03", "0.1"])
    ax.set_xlabel(r"Noise $\sigma$"); ax.set_ylabel("R@1 change (%)")
    ax.legend(frameon=False, ncol=1, loc="upper left", handlelength=1.2)
    save(fig, FIGDIR / "fig9a_noise_sweep.png"); plt.close(fig)

    # B
    fig, ax = _one()
    zv, zt = vis[0.0], txt[0.0]
    ax.scatter(range(1, len(zv) + 1), zv, s=26, color=CV, marker="o",
               edgecolor="black", linewidth=0.4, zorder=3, label="Vision")
    ax.scatter(range(1, len(zt) + 1), zt, s=26, color=CT, marker="s",
               edgecolor="black", linewidth=0.4, zorder=3, label="Text")
    ax.axhline(0, color="black", ls="--", lw=1.0)
    ax.set_ylim(-1.0, 1.0)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_xlabel("Seed index"); ax.set_ylabel("R@1 change (%)")
    ax.legend(frameon=False, ncol=2, loc="lower center", handlelength=1.2)
    save(fig, FIGDIR / "fig9b_sigma0_control.png"); plt.close(fig)

    # C
    fig, ax = _one()
    ax.bar([0, 1], [abs(v01), abs(t01)], 0.5, color=[CV, CT],
           edgecolor="black", linewidth=0.4, hatch=[None, "//"])
    ax.errorbar([0], [abs(v01)], yerr=[np.std(vis[0.1], ddof=1)], fmt="none",
                ecolor="black", elinewidth=0.9, capsize=3)
    ax.errorbar([1], [abs(t01)], yerr=[np.std(txt[0.1], ddof=1)], fmt="none",
                ecolor="black", elinewidth=0.9, capsize=3)
    ax.axhline(2.6, color=CGR, ls=":", lw=1.2)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Vision", "Text"])
    ax.set_ylabel(r"$|$R@1 change$|$ (%) at $\sigma{=}0.1$")
    ax.set_ylim(0, 6.6)
    ax.text(0.97, 0.99, r"earlier claim: $2.6\times$", transform=ax.transAxes,
            ha="right", va="top", fontsize=7.5, color=CGR)
    save(fig, FIGDIR / "fig9c_ratio.png"); plt.close(fig)
    print("  ✅ fig9 → fig9a / fig9b / fig9c")
    assert d.get("control_sigma0_reproduces_baseline"), "σ=0 未复现基线"
    assert 0.5 < ratio < 1.2, f"比值 {ratio:.2f} 与图注 0.76 不符"


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演，加 --apply）")
        return 0
    fig8()
    fig9()
    print("\n  === 产出核对 ===")
    from PIL import Image
    for f in ("fig8a_rank_delta", "fig8b_budget", "fig8c_vision_untouched",
              "fig9a_noise_sweep", "fig9b_sigma0_control", "fig9c_ratio"):
        p = FIGDIR / f"{f}.png"
        with Image.open(p) as im:
            w, h = im.size
        print(f"    {f:<28} {w/300:.3f} × {h/300:.3f} in  {'✅' if abs(w/300 - 3.713) < 0.02 else '⚠'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
