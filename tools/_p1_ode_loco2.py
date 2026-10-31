# -*- coding: utf-8 -*-
r"""修正 LOCO：**在同族配置内**做留一，并诊断 in-sample 分布（2026-10-07）。

## 为什么必须修正

第一版 `_p1_ode_loco.py` 把 **LoRA / Adapter / full-FT 混在一个池**里做 LOCO，
且特征只用 $DG^*_0$，得到平均 R² = −1.68、corr(α_pred, α_fit) = 0.12。

**但这个结果不能直接采信**：跨**方法**外推本来就该失败（Adapter 的 $d$ 与 LoRA 的 $r$ 不是同一量纲，
full-FT 更是另一类）。**必须先在同族内验证，再看跨族。**

## 本脚本做四件事

1. **in-sample 分布**：逐配置 R² 的直方图，找出拟合差的配置（正文称 CLIP LoRA 0.978–0.997）；
2. **同族 LOCO**：只在 **LoRA-family**（`v1_trajectory` + `beta_pilot` + `coco`）内留一；
3. **秩感知特征**：用 `(方法, 位置, 秩)` 作为配置特征，而非仅 $DG^*_0$；
4. **诚实报告**：无论结果好坏都落盘。

    python tools\_p1_ode_loco2.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import re
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "ode_loco2.json"

try:
    import numpy as np
except Exception:
    np = None


def model(t, A, B, dg0):
    return dg0 + (A / B) * (1.0 - np.exp(-B * t))


def r2(y, yhat):
    y = np.asarray(y, float); yhat = np.asarray(yhat, float)
    ss = float(((y - y.mean()) ** 2).sum())
    return 1.0 - float(((y - yhat) ** 2).sum()) / ss if ss > 0 else float("nan")


def fit(t, y):
    """网格 β + 解析幅度；返回 (α, β, R²)。"""
    t = np.asarray(t, float); y = np.asarray(y, float)
    dg0 = float(y[0]); r = y - dg0
    best = (float("nan"), float("nan"), float("inf"))
    for logb in np.linspace(np.log10(0.005), np.log10(20.0), 600):
        b = 10.0 ** logb
        u = 1.0 - np.exp(-b * t)
        den = float((u * u).sum())
        if den < 1e-12:
            continue
        a = float((u * r).sum()) / den
        resid = float(((r - a * u) ** 2).sum())
        if resid < best[2]:
            best = (a * b, b, resid)
    A, B, _ = best
    return float(A), float(B), r2(y, model(t, A, B, dg0))


def parse(conf: str) -> dict:
    """从配置路径解析 (方法族, 位置, 秩/维度)。"""
    d = {"raw": conf, "family": "?", "site": "?", "rank": None}
    low = conf.lower()
    if "adapter" in low:
        d["family"] = "adapter"
    elif "full_ft" in low or "fullft" in low:
        d["family"] = "full_ft"
    elif "lora" in low or "beta_pilot" in low or "coco" in low or "v1_" in low:
        d["family"] = "lora"
    for s in ("text_only", "both", "vision_only"):
        if s in low:
            d["site"] = s
    m = re.search(r"_r(\d+)$|_d(\d+)$", low)
    if m:
        d["rank"] = int(m.group(1) or m.group(2))
    return d


def main() -> int:
    apply = "--apply" in sys.argv
    if np is None:
        print("  ❌ 需要 numpy")
        return 1

    traj = {}
    for f in sorted(glob.glob(str(REPO / "outputs/theory/**/dg_star_history.json"), recursive=True)):
        parts = Path(f).parts
        conf = "/".join(parts[-4:-2])
        d = json.loads(io.open(f, encoding="utf-8").read())
        if len(d["epochs"]) < 5:
            continue
        traj.setdefault(conf, []).append((d["epochs"], d["dg_star"]))

    fits = {}
    for conf, runs in traj.items():
        n = min(len(y) for _, y in runs)
        y = [st.mean(r[i] for _, r in runs) for i in range(n)]
        A, B, R = fit(runs[0][0][:n], y)
        meta = parse(conf)
        fits[conf] = {"alpha": A, "beta": B, "R2": R, "y0": y[0], "t": runs[0][0][:n], "y": y, **meta}

    good = {k: v for k, v in fits.items() if v["R2"] == v["R2"]}
    rs = sorted(v["R2"] for v in good.values())
    print(f"  === ① in-sample 分布（{len(good)} 配置，种子均值轨迹）===")
    print(f"    平均 {st.mean(rs):.4f} ｜ 中位 {st.median(rs):.4f} ｜ 范围 {rs[0]:.3f}–{rs[-1]:.3f}")
    print(f"    R² ≥ 0.95 的配置: {sum(1 for r in rs if r >= 0.95)}/{len(rs)}")
    print(f"    R² < 0.5  的配置: {sum(1 for r in rs if r < 0.5)}/{len(rs)}")
    worst = sorted(good.items(), key=lambda kv: kv[1]["R2"])[:5]
    print("    最差 5 个:")
    for k, v in worst:
        print(f"      {k:<40} R²={v['R2']:+.4f}  α={v['alpha']:+.4f} β={v['beta']:.4f}")

    # ── 同族 LOCO（LoRA family，秩作为特征）
    print(f"\n  === ② 同族 LOCO（family=lora）===")
    lora = {k: v for k, v in good.items() if v["family"] == "lora"}
    print(f"    LoRA-family 配置数: {len(lora)}")
    res_loco = {}
    if len(lora) >= 4:
        keys = sorted(lora)
        for hold in keys:
            tr = [k for k in keys if k != hold]
            # 特征：DG*_0 与 秩（秩缺失填中位）
            ranks = [lora[k]["rank"] for k in tr if lora[k]["rank"]]
            rmed = st.median(ranks) if ranks else 8.0
            X = np.asarray([[lora[k]["y0"], (lora[k]["rank"] or rmed)] for k in tr], float)
            Xh = np.asarray([[lora[hold]["y0"], (lora[hold]["rank"] or rmed)]], float)
            ya = np.asarray([lora[k]["alpha"] for k in tr], float)
            yb = np.asarray([lora[k]["beta"] for k in tr], float)
            A = np.hstack([X, np.ones((len(tr), 1))])
            Ah1 = np.hstack([Xh, np.ones((1, 1))])
            try:
                ca, *_ = np.linalg.lstsq(A, ya, rcond=None)
                cb, *_ = np.linalg.lstsq(A, yb, rcond=None)
                ap = float((Ah1 @ ca)[0]); bp = float((Ah1 @ cb)[0])
            except Exception:
                ap, bp = float(ya.mean()), float(yb.mean())
            v = lora[hold]
            yh = model(np.asarray(v["t"], float), ap, bp, v["y0"])
            res_loco[hold] = {"R2": r2(v["y"], yh), "alpha_pred": ap, "alpha_fit": v["alpha"],
                              "beta_pred": bp, "beta_fit": v["beta"]}
        rl = [v["R2"] for v in res_loco.values()]
        print(f"    平均 R² = {st.mean(rl):.4f} ｜ 中位 {st.median(rl):.4f} ｜ 负值 {sum(1 for r in rl if r < 0)}/{len(rl)}")
        ka = [res_loco[k]["alpha_pred"] for k in keys]; kb = [res_loco[k]["alpha_fit"] for k in keys]
        ba = [res_loco[k]["beta_pred"] for k in keys]; bb = [res_loco[k]["beta_fit"] for k in keys]
        if np.ptp(ka) > 0 and np.ptp(kb) > 0:
            print(f"    corr(α_pred, α_fit) = {np.corrcoef(ka, kb)[0,1]:.3f}")
        if np.ptp(ba) > 0 and np.ptp(bb) > 0:
            print(f"    corr(β_pred, β_fit) = {np.corrcoef(ba, bb)[0,1]:.3f}")

    print(f"\n  === ③ 秩与 α 的关系（正文称 α 随秩变化）===")
    for fam in ("lora", "adapter"):
        sub = [(v["rank"], v["alpha"]) for v in good.values() if v["family"] == fam and v["rank"]]
        if len(sub) >= 3:
            sub.sort()
            print(f"    {fam}: " + " ｜ ".join(f"r{r}={a:+.3f}" for r, a in sub))

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"in_sample": {"mean": st.mean(rs), "median": st.median(rs), "min": rs[0], "max": rs[-1],
                           "n_ge_095": sum(1 for r in rs if r >= 0.95), "n": len(rs)},
             "per_config": {k: {kk: vv for kk, vv in v.items() if kk not in ("t", "y")}
                            for k, v in good.items()},
             "loco_lora": res_loco}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
