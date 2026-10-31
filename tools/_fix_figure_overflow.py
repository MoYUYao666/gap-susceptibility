# -*- coding: utf-8 -*-
r"""修重绘图的溢出：让画布宽高比与 LaTeX 的 `width=` 相容（2026-10-05）。

## 问题

`paper合/main_nc.log` 有两处 **Overfull \hbox**（图超出页面）：

| 图 | 溢出 | 原因 |
|---|---|---|
| `fig1.png` | **60.96 pt** | 画布 5.6×3.4 in（比 1.647）→ 在 `width=0.88\textwidth`（303.6 pt）下**自然高度仅 184.3 pt**，与 LaTeX 请求的 200.4 pt 不符 → 实际宽度撑到约 364 pt，**超出文本宽度** |
| `fig4_effective_rank.png` | **20.70 pt** | 同样原因（5.0×3.3 in） |

**这是重绘引入的**——原图不溢出。根因：LaTeX 的 `\includegraphics[width=0.88\textwidth]` 会按图片
**自身宽高比**算高度，而**我设的画布比例与正文预期不符**。

## 修法

把画布比例调到与正文 `figures/fig1.png` 等既有图的**预期比例**一致：
**高度/宽度 ≈ 0.66**（宽 5.6 in 时高约 3.7 in），使 `width=0.88\textwidth` 下的自然高度
接近 LaTeX 请求值，从而**不触发 Overfull**。

**并加断言**：重绘后 `pdflatex` 日志中**该图的 Overfull 必须消失**。

    python tools\_fix_figure_overflow.py [--apply]
"""
from __future__ import annotations

import io

import sys
from pathlib import Path

# ── 共享图样式（Times New Roman + 最终尺寸；定义见 tools/figure_style.py）
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from figure_style import (apply_style, figsize_full, figsize_wide,
                          save, FIG_W_FULL, OKABE_ITO)  # noqa: E402

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
PY = r"D:\Anaconda\envs\pytorch\python.exe"


def aspect(p: Path) -> tuple[int, int, float]:
    from PIL import Image
    with Image.open(p) as im:
        w, h = im.size
    return w, h, h / w


def main() -> int:
    apply = "--apply" in sys.argv
    figs = PA / "figures"

    print("=== 现各图宽高比（h/w）===")
    targets = ["fig1.png", "fig4_effective_rank.png", "fig2_v5_falsification.png",
               "fig10_layered_ft.png", "fig12_zeroshot_more.png", "fig14_adapter_layered.png",
               "fig1_ode_fits.png", "fig3.png", "fig4.png"]
    for t in targets:
        p = figs / t
        if p.exists():
            w, h, r = aspect(p)
            flag = "⚠ 偏宽" if r < 0.62 else ("⚠ 偏高" if r > 0.78 else "✅")
            print(f"  {t:<32} {w}×{h}  h/w={r:.3f}  {flag}")

    if not apply:
        print("\n  （预演；加 --apply 重绘 fig1 与 fig4_effective_rank 为 h/w≈0.66）")
        return 0

    # ── 重绘：把画布调为宽 5.6 in、高 3.7 in（h/w≈0.661）
    # ── Okabe-Ito 色盲友好调色板（2026-10-06 统一；定义见 tools/figure_style.py）
    import sys as _sys
    import matplotlib
    matplotlib.use("Agg")
    apply_style()                      # Times New Roman + STIX + 统一字号
    import matplotlib.pyplot as plt
    import glob
    import json
    import math

    # (A) fig1：间隙演化
    arms = {
        "Full FT": "outputs/flickr30k/baseline_full_ft/gap_history.json",
        "text-only": "outputs/flickr30k/rq2_text_only/gap_history.json",
        "both": "outputs/flickr30k/rq2_both/gap_history.json",
    }
    fig, ax = plt.subplots(figsize=figsize_full(0.66))
    # 语义配色 + **线型冗余编码**（灰度/色觉异常下仍可区分）
    _style = {"Full FT": (OKABE_ITO["grey"], ":"),
              "text-only": (OKABE_ITO["blue"], "-"),
              "both": (OKABE_ITO["vermil"], "--")}
    for k, rel in arms.items():
        d = json.loads(io.open(REPO / rel, encoding="utf-8").read())
        dcg = d["centroid_gap"][-1] - d["centroid_gap"][0]
        _c, _ls = _style.get(k, (OKABE_ITO["purple"], "-"))
        ax.plot(d["epoch"], d["centroid_gap"], _ls, color=_c, linewidth=1.6,
                label=f"{k} (ΔCG {dcg:+.3f})")
    seeds = sorted(glob.glob(str(REPO / "outputs/flickr30k_seeds/rq2_text_only/seed*/gap_history.json")))
    if len(seeds) >= 2:
        import statistics as st
        hs = [json.loads(io.open(s, encoding="utf-8").read())["centroid_gap"] for s in seeds]
        n = min(len(h) for h in hs)
        lo = [min(h[i] for h in hs) for i in range(n)]
        hi = [max(h[i] for h in hs) for i in range(n)]
        ep = json.loads(io.open(seeds[0], encoding="utf-8").read())["epoch"][:n]
        ax.fill_between(ep, lo, hi, alpha=0.18, color=OKABE_ITO["blue"], label=f"text-only, {len(seeds)} seeds")
    ax.set_xlabel("Epoch"); ax.set_ylabel("Centroid gap")
    ax.legend(fontsize=6.5, frameon=False)
    ax.grid(alpha=0.25, linewidth=0.5); ax.set_axisbelow(True)
    save(fig, figs / "fig1.png"); plt.close(fig)
    print("\n  ✅ 已重绘 fig1.png")

    # (B) fig4_effective_rank：由 k 数据
    k = json.loads(io.open(REPO / "outputs/analysis/k_remeasured_both.json", encoding="utf-8").read())
    pairs = sorted((int(p["rank"]), float(p["norm_g_v_mean"])) for p in k["points"])
    ranks = [r for r, _ in pairs]; vals = [v for _, v in pairs]
    xs = list(range(len(ranks)))
    fig, ax = plt.subplots(figsize=figsize_full(0.66))
    ax.plot(xs, [math.sqrt(r / ranks[0]) for r in ranks], "s--", color=OKABE_ITO["vermil"],
            linewidth=1.4, markersize=4.5, label=r"$\sqrt{r}$ prediction")
    ax.plot(xs, [v / vals[0] for v in vals], "o-", color=OKABE_ITO["blue"],
            linewidth=1.6, markersize=5, label="measured (normalised)")
    ax.fill_between(xs, 0.95, 1.05, color=OKABE_ITO["blue"], alpha=0.12, label=r"$\pm5\%$ band")
    ax.set_xticks(xs); ax.set_xticklabels([str(r) for r in ranks])
    ax.set_xlabel("Configured rank"); ax.set_ylabel(r"$\|g_v\| / \|g_v\|_{r=1}$")
    ax.legend(fontsize=7, frameon=False)
    ax.grid(alpha=0.25, linewidth=0.5); ax.set_axisbelow(True)
    fig.tight_layout(); fig.savefig(figs / "fig4_effective_rank.png", dpi=300); plt.close(fig)
    print("  ✅ 已重绘 fig4_effective_rank.png")

    # ── 重新编译并断言 Overfull 消失
    for ext in ("aux", "bbl", "blg", "log", "out"):
        (PA / f"main_nc.{ext}").unlink(missing_ok=True)
    for cmd in (["pdflatex", "-interaction=nonstopmode", "main_nc.tex"],
                ["bibtex", "main_nc"],
                ["pdflatex", "-interaction=nonstopmode", "main_nc.tex"],
                ["pdflatex", "-interaction=nonstopmode", "main_nc.tex"]):
        subprocess.run(cmd, cwd=PA, capture_output=True)
    log = (PA / "main_nc.log").read_text(encoding="utf-8", errors="ignore")
    ov = re.findall(r"Overfull \\hbox \(([\d.]+)pt too wide\)", log)
    print(f"\n  Overfull \\hbox: {len(ov)} 处 {ov}")
    assert not ov, f"Overfull 仍在：{ov}"
    print("  ✅ Overfull 已消除")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
