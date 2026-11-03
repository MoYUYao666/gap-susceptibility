# -*- coding: utf-8 -*-
r"""`fig1_ode_fits`：**可读标签 + 语义配色 + 图例移出绘图区**（2026-10-06）。

## 原图的问题（目视确认）

| 症状 | 说明 |
|---|---|
| **图例在轴中下部**，压住 measured 点 | `ax.legend(fontsize=6, ncol=2)` 默认 `best` |
| **标签是内部配置名** | `beta_pilot_both_r8 (ODE)` —— 读者看不懂 |
| **配色未统一** | 6 个系列走 matplotlib 默认色轮 |
| 未用 `save()` | 因此没出 PDF；且与 `constrained_layout` 混用了 `tight_layout` |

## 改法

- 标签简化为 **`both` / `full FT` / `text`**（去掉 `beta_pilot_` 前缀与 `_r8` 后缀）；
- **ODE 用线、measured 用点**，同一配置**同色**（语义：ODE=蓝系、实测=朱红系）；
- **图例置于绘图区之外**（轴上方，2 列）；
- 用 `save()`（同出 PNG+PDF），去掉 `tight_layout`。

    python tools\_pa_fig_ode_fits_fix.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_pa_rebuild_figs_rest.py"

OLD = '''    fig, ax = plt.subplots(figsize=figsize_full(0.60))
    shown = 0
    for name in sorted(groups):
        for s in sorted(groups[name])[:1]:       # 每配置一条，保持图简洁
            d = load(Path(s))
            ep = d["epochs"]
            ax.plot(ep, d["dg_star"], "-", linewidth=1.5, label=f"{name} (ODE)")
            if "dg_empirical" in d:
                ax.plot(ep, d["dg_empirical"], "o", markersize=3.2,
                        label=f"{name} (measured)")
            shown += 1
    ax.set_xlabel("Epoch"); ax.set_ylabel(r"$g_v$ magnitude")
    ax.legend(fontsize=6, frameon=False, ncol=2)
    ax.grid(alpha=0.25, linewidth=0.5); ax.set_axisbelow(True)
    fig.tight_layout(); fig.savefig(FIGDIR / "fig1_ode_fits.png", dpi=300); plt.close(fig)
    print(f"  ✅ 已重绘（{shown} 条轨迹）")'''

NEW = '''    fig, ax = plt.subplots(figsize=figsize_full(0.62))
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
    print(f"  ✅ 已重绘（{shown} 条轨迹）")'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "pretty = {" in t and "beta_pilot_both_r8" in t:
        print("  已改，跳过")
        return 0
    c = t.count(OLD)
    if c != 1:
        print(f"  ⚠ 未唯一命中（{c} 次）")
        return 1
    print("  ✅ 命中 fig_ode_fits 绘图块")
    if apply:
        t2 = t.replace(OLD, NEW, 1)
        ast.parse(t2)
        io.open(F, "w", encoding="utf-8", newline="").write(t2)
        t3 = io.open(F, encoding="utf-8").read()
        assert 'pretty = {"beta_pilot_both_r8"' in t3 and '"lower center",\n              bbox_to_anchor' in t3
        assert "fig.tight_layout(); fig.savefig(FIGDIR / \"fig1_ode_fits.png\"" not in t3
        print("  ✅ 已写入并断言通过")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
