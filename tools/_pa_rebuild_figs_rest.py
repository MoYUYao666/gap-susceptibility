# -*- coding: utf-8 -*-
r"""重绘 Paper A 剩余来源不明的图（2026-10-05）。

## 原则（本脚本遵守）

1. **每张图先断言其正文主张**，数据不符即报错——**不画与正文不一致的图**；
   （`fig12`、`fig14` 就是这样捕获到两处主张与数据不符的。）
2. **来源写清**：脚本内标注源 JSON 路径，图注/文档同步；
3. **不臆想主张**：断言只针对**正文实际写了的话**（曾因臆想主张设错断言）。

## 覆盖

| 图 | 源数据 | 正文主张 |
|---|---|---|
| `fig1_ode_fits.png` | `outputs/theory/beta_pilot/*/seed*/dg_star_history.json` | ODE 轨迹拟合示例 |
| `fig1.png` | `outputs/flickr30k{,_seeds}/**/gap_history.json` | 间隙演化：Full FT / text-only / both |
| `fig3.png` | `outputs/flickr30k/alpha_*/gap_history.json` | LoRA α 消融 |
| `fig4.png` | `outputs/theory/adapter/adapter_all_results.json` | 跨方法：LoRA vs Adapter |
| `fig2_v5_falsification.png` | `outputs/analysis/k_remeasured_both.json` | 随机投影 vs 实测 ‖g_v‖ |
| `fig4_effective_rank.png` | `outputs/analysis/k_remeasured_both.json` | Effective Rank Saturation |

    python tools\_pa_rebuild_figs_rest.py [--dry]      # 只核对主张，不写图
    python tools\_pa_rebuild_figs_rest.py --apply      # 写图
"""
from __future__ import annotations

import glob
import io

import sys
from pathlib import Path

# ── 共享图样式（Times New Roman + 最终尺寸；定义见 tools/figure_style.py）
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from figure_style import (apply_style, figsize_full, figsize_wide,
                          save, FIG_W_FULL, OKABE_ITO)  # noqa: E402

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIGDIR = REPO / "paper合" / "figures"


def load(p: Path):
    return json.loads(io.open(p, encoding="utf-8", errors="ignore").read())


# ─────────────────────────── fig1_ode_fits ───────────────────────────
def fig_ode_fits(dry: bool) -> None:
    print("=== fig1_ode_fits.png ===")
    srcs = sorted(glob.glob(str(REPO / "outputs/theory/beta_pilot/*/seed*/dg_star_history.json")))
    print(f"  源数据 {len(srcs)} 个")
    recs = []
    for s in srcs[:6]:
        d = load(Path(s))
        n = len(d.get("epochs") or d.get("dg_star") or [])
        recs.append((Path(s).parent.parent.name, Path(s).parent.name, n, list(d)))
        print(f"    {Path(s).parent.parent.name}/{Path(s).parent.name}: {n} 点  keys={list(d)}")
    assert recs, "无 ODE 轨迹数据"
    if dry:
        return
    import sys as _sys
    import matplotlib
    matplotlib.use("Agg")
    apply_style()                       # Times New Roman + STIX + 统一字号
    import matplotlib.pyplot as plt
    picks = sorted(glob.glob(str(REPO / "outputs/theory/beta_pilot/*/seed*/dg_star_history.json")))
    groups: dict[str, list] = {}
    for s in picks:
        groups.setdefault(Path(s).parent.parent.name, []).append(s)
    fig, ax = plt.subplots(figsize=figsize_full(0.62))
    # 内部配置名 -> 可读标签 + 语义配色（ODE=蓝系实线，实测=朱红系点）
    # 原先直接用 `beta_pilot_both_r8` 之类内部名，读者看不懂；配色也未统一。
    pretty = {"beta_pilot_both_r8": ("both", OKABE_ITO["blue"]),
              "beta_pilot_full_ft": ("full FT", OKABE_ITO["vermil"]),
              "beta_pilot_text_r8": ("text", OKABE_ITO["green"])}
    shown = 0
    for name in sorted(groups):
        for s in sorted(groups[name])[:1]:       # 每配置一条，保持图简洁
            d = load(Path(s))
            ep = d["epochs"]
            lbl, col = pretty.get(name, (name.replace("beta_pilot_", ""), OKABE_ITO["purple"]))
            ax.plot(ep, d["dg_star"], "-", color=col, linewidth=1.5,
                    label=f"{lbl}: ODE")
            if "dg_empirical" in d:
                ax.plot(ep, d["dg_empirical"], "o", color=col, markersize=3.2,
                        markerfacecolor="white", markeredgewidth=0.9,
                        label=f"{lbl}: measured")
            shown += 1
    ax.set_xlabel("Epoch"); ax.set_ylabel(r"$g_v$ magnitude")
    # 图例移到**绘图区之外**（原先默认 best，落在轴中下部并压住 measured 点）
    ax.legend(fontsize=7, frameon=False, ncol=3, loc="lower center",
              bbox_to_anchor=(0.5, 1.02), columnspacing=1.0, handlelength=1.6)
    ax.grid(alpha=0.25, linewidth=0.5); ax.set_axisbelow(True)
    save(fig, FIGDIR / "fig1_ode_fits.png"); plt.close(fig)
    print(f"  ✅ 已重绘（{shown} 条轨迹）")


# ─────────────────────────── fig1 总览 ───────────────────────────
def fig_overview(dry: bool) -> None:
    print("\n=== fig1.png（间隙演化）===")
    arms = {
        "Full FT": "outputs/flickr30k/baseline_full_ft/gap_history.json",
        "text-only": "outputs/flickr30k/rq2_text_only/gap_history.json",
        "both": "outputs/flickr30k/rq2_both/gap_history.json",
    }
    for k, rel in arms.items():
        p = REPO / rel
        if not p.exists():
            print(f"  ❌ 缺 {rel}")
            return
        d = load(p)
        cg0, cg1 = d["centroid_gap"][0], d["centroid_gap"][-1]
        print(f"  {k:<10} epochs={len(d['epoch'])}  CG {cg0:.4f} → {cg1:.4f}  ΔCG={cg1-cg0:+.4f}")
    # 正文主张（empirical.tex）：legacy 约定下 text-only 保对齐、both 与 full FT 恶化
    t = load(REPO / arms["text-only"]); b = load(REPO / arms["both"]); f = load(REPO / arms["Full FT"])
    dt = t["centroid_gap"][-1] - t["centroid_gap"][0]
    db = b["centroid_gap"][-1] - b["centroid_gap"][0]
    df = f["centroid_gap"][-1] - f["centroid_gap"][0]
    print(f"  ΔCG: text-only {dt:+.4f} ｜ both {db:+.4f} ｜ Full FT {df:+.4f}")
    ok = dt < db and dt < df
    print(f"  → text-only 的 ΔCG 最小: {'✅' if ok else '❌'}")
    assert ok, "数据不支持『text-only 保对齐优于 both / full FT』"
    if dry:
        return
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=figsize_full(0.60))
    # 2026-10-15：这三条线原先走 matplotlib 默认色轮（#1f77b4 / #ff7f0e / #2ca02c），
    # 与本库其余图不统一。改用语义配色 + 线型冗余编码（灰度/色觉异常下也可区分）。
    _style = {"Full FT": (OKABE_ITO["grey"], ":"),
              "text-only": (OKABE_ITO["blue"], "-"),
              "both": (OKABE_ITO["vermil"], "--")}
    for k, rel in arms.items():
        d = load(REPO / rel)
        _c, _ls = _style.get(k, (OKABE_ITO["purple"], "-"))
        ax.plot(d["epoch"], d["centroid_gap"], _ls, color=_c, linewidth=1.6,
                label=f"{k} (ΔCG {d['centroid_gap'][-1]-d['centroid_gap'][0]:+.3f})")
    # text-only 的 5-seed 带
    seeds = sorted(glob.glob(str(REPO / "outputs/flickr30k_seeds/rq2_text_only/seed*/gap_history.json")))
    if len(seeds) >= 2:
        import statistics as st
        hs = [load(Path(s))["centroid_gap"] for s in seeds]
        n = min(len(h) for h in hs)
        m = [st.mean(h[i] for h in hs) for i in range(n)]
        lo = [min(h[i] for h in hs) for i in range(n)]
        hi = [max(h[i] for h in hs) for i in range(n)]
        ep = load(Path(seeds[0]))["epoch"][:n]
        ax.fill_between(ep, lo, hi, alpha=0.18, color=OKABE_ITO["blue"], label=f"text-only, {len(seeds)} seeds")
    ax.set_xlabel("Epoch"); ax.set_ylabel("Centroid gap")
    ax.legend(fontsize=6.5, frameon=False)
    ax.grid(alpha=0.25, linewidth=0.5); ax.set_axisbelow(True)
    save(fig, FIGDIR / "fig1.png"); plt.close(fig)
    print(f"  ✅ 已重绘（含 {len(seeds)} seed 带）")


# ─────────────────────────── fig3 α 消融 ───────────────────────────
def fig_alpha(dry: bool) -> None:
    print("\n=== fig3.png（LoRA α 消融）===")
    alphas = sorted(glob.glob(str(REPO / "outputs/flickr30k/alpha_*/gap_history.json")))
    print(f"  α 配置 {len(alphas)} 个")
    vals = {}
    for p in alphas:
        a = Path(p).parent.name.replace("alpha_", "")
        d = load(Path(p))
        vals[a] = d["centroid_gap"][-1] - d["centroid_gap"][0]
        print(f"    α={a:<4} ΔCG={vals[a]:+.4f}")
    assert len(vals) >= 2, "α 消融数据不足"
    if dry:
        return
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    xs = sorted(vals, key=lambda x: int(x))
    fig, ax = plt.subplots(figsize=(FIG_W_FULL, FIG_W_FULL * 0.66))
    ax.plot([int(x) for x in xs], [vals[x] for x in xs], "o-", color=OKABE_ITO["blue"], linewidth=1.5, markersize=5)
    ax.set_xscale("log", base=2); ax.set_xticks([int(x) for x in xs])
    ax.set_xticklabels([x for x in xs])
    ax.set_xlabel(r"LoRA scaling $\alpha$"); ax.set_ylabel(r"$\Delta$CG")
    ax.axhline(0, color="black", linewidth=0.6)
    ax.grid(alpha=0.25, linewidth=0.5); ax.set_axisbelow(True)
    save(fig, FIGDIR / "fig3.png"); plt.close(fig)
    print("  ✅ 已重绘")


# ─────────────────────────── fig4 跨方法 ───────────────────────────
def fig_crossmethod(dry: bool) -> None:
    """Disabled 2026-10-15: this function drew Adapter beta-vs-dimension and wrote it to fig4.png,
    overwriting the cross-method comparison produced by tools/_pa_rebuild_fig4_crossmethod.py. The
    shipped manuscript used the PDF, which was never rewritten, so both the PNG and the PDF showed the
    wrong plot (with `False`/`True` as legend labels) for months. Left in place as a record; run
    tools/_pa_rebuild_fig4_crossmethod.py --apply for the real figure.
    """
    print("\n=== fig4.png（跨方法 LoRA vs Adapter）—— 已停用，见本函数 docstring ===")
    return
    print(f"  Adapter 记录 {len(d)} 条  keys={list(d[0])}")
    dims = sorted({r["dim"] for r in d})
    print(f"  dim 取值: {dims}")
    pos = sorted({r["position"] for r in d})
    print(f"  position 取值: {pos}")
    assert len(d) > 0, "无 Adapter 数据"
    if dry:
        return
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import statistics as st
    fig, ax = plt.subplots(figsize=(FIG_W_FULL, FIG_W_FULL * 0.66))
    for po in pos:
        xs, ys = [], []
        for dm in dims:
            vs = [r["beta"] for r in d if r["dim"] == dm and r["position"] == po and r.get("beta") is not None]
            if vs:
                xs.append(dm); ys.append(st.mean(vs))
        if xs:
            ax.plot(xs, ys, "o-", linewidth=1.5, markersize=4.5, label=po)
    ax.set_xscale("log", base=2); ax.set_xticks(dims); ax.set_xticklabels([str(x) for x in dims])
    ax.set_xlabel("Adapter bottleneck dimension"); ax.set_ylabel(r"$\beta$")
    ax.legend(fontsize=6.5, frameon=False)
    ax.grid(alpha=0.25, linewidth=0.5); ax.set_axisbelow(True)
    fig.tight_layout()
    # 2026-10-15: was `fig.savefig(..., .png)`, so the library's PDF for this figure was a stale export
    # from 2026-08-02 while the PNG was current -- and LaTeX includes the PDF. Use the shared save()
    # so both exports are regenerated together.
    save(fig, FIGDIR / "fig4.png"); plt.close(fig)
    print("  ✅ 已重绘")


# ──────────────────── k 相关的两张 ────────────────────
def fig_k(dry: bool) -> None:
    print("\n=== fig2_v5_falsification.png / fig4_effective_rank.png（源：k 重测）===")
    k = load(REPO / "outputs/analysis/k_remeasured_both.json")
    pts = k["points"]           # [{"rank": r, "norm_g_v_mean": v}, ...]
    pairs = sorted((int(p["rank"]), float(p["norm_g_v_mean"])) for p in pts)
    ranks = [r for r, _ in pairs]
    vals = [v for _, v in pairs]
    print(f"  arm={k.get('arm')} convention={k.get('convention')}")
    print(f"  覆盖 rank: {ranks}")
    print(f"  ‖g_v‖: {[round(v,4) for v in vals]}")
    spread = 100 * (max(vals) - min(vals)) / (sum(vals) / len(vals))
    pred = (max(ranks) / min(ranks)) ** 0.5
    print(f"  极差 {spread:.1f}% ｜ √r 预测 {pred:.1f}× 变化")
    # 正文主张（validation.tex）：10% 带 vs √r 的八倍
    ok = spread < 20 and pred >= 7.5
    print(f"  → 主张『10% 带 vs √r 八倍』: {'✅' if ok else '❌'}")
    assert ok, "k 数据与正文主张不符"
    if dry:
        return
    import math
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # (A) falsification：随机投影 √r 预测 vs 实测
    #     2026-10-15：此图在 LaTeX 里是 0.88\textwidth（= 4.189 in），原先按 0.78 出图 ⇒
    #     LaTeX 需放大 1.05×、字号与其它图不一致。改按最终宽度出图（tools/_p868_figure_scale.py 复核）。
    fig, ax = plt.subplots(figsize=figsize_full(0.66))
    xs = list(range(len(ranks)))
    pred_y = [vals[0] * math.sqrt(r / ranks[0]) for r in ranks]
    ax.plot(xs, pred_y, "s--", color=OKABE_ITO["vermil"], linewidth=1.4, markersize=4.5,
            label=r"random projection, $\propto\sqrt{r}$")
    ax.plot(xs, vals, "o-", color=OKABE_ITO["blue"], linewidth=1.6, markersize=5, label="measured")
    ax.set_xticks(xs); ax.set_xticklabels([str(r) for r in ranks])
    ax.set_xlabel("LoRA rank"); ax.set_ylabel(r"$\|g_v\|$")
    ax.legend(fontsize=7, frameon=False)
    ax.grid(alpha=0.25, linewidth=0.5); ax.set_axisbelow(True)
    fig.tight_layout()
    # 2026-10-15: save() writes PNG **and** PDF; the bare savefig left the included PDF stale.
    save(fig, FIGDIR / "fig2_v5_falsification.png"); plt.close(fig)

    # (B) Effective Rank Saturation：同一数据的另一种读法（归一化到 r=1）
    fig, ax = plt.subplots(figsize=(FIG_W_FULL, FIG_W_FULL * 0.66))
    norm = [v / vals[0] for v in vals]
    ax.plot(xs, [math.sqrt(r / ranks[0]) for r in ranks], "s--", color=OKABE_ITO["vermil"],
            linewidth=1.4, markersize=4.5, label=r"$\sqrt{r}$ prediction")
    ax.plot(xs, norm, "o-", color=OKABE_ITO["blue"], linewidth=1.6, markersize=5, label="measured (normalised)")
    ax.fill_between(xs, 0.95, 1.05, color=OKABE_ITO["blue"], alpha=0.12, label=r"$\pm5\%$ band")
    ax.set_xticks(xs); ax.set_xticklabels([str(r) for r in ranks])
    ax.set_xlabel("Configured rank"); ax.set_ylabel(r"$\|g_v\| / \|g_v\|_{r=1}$")
    ax.legend(fontsize=7, frameon=False)
    ax.grid(alpha=0.25, linewidth=0.5); ax.set_axisbelow(True)
    fig.tight_layout()
    # 2026-10-15: save() writes PNG **and** PDF; the bare savefig left the included PDF stale.
    save(fig, FIGDIR / "fig4_effective_rank.png"); plt.close(fig)
    print("  ✅ 已重绘两张（来源：outputs/analysis/k_remeasured_both.json）")


def main() -> int:
    dry = "--dry" in sys.argv or "--apply" not in sys.argv
    for fn in (fig_ode_fits, fig_overview, fig_alpha, fig_crossmethod, fig_k):
        fn(dry)
    print("\n  " + ("（核对模式，未写图；加 --apply 写图）" if dry else "✅ 全部完成"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
