# -*- coding: utf-8 -*-
r"""核论文里三条"监控"主张在新数据下的真伪（2026-10-12）。

## 论文的三条主张（`main.tex`）

| # | 主张 | 出处 |
|---|---|---|
| 1 | "$\tau$ is an earlier and more sensitive indicator of order erosion than top-1 itself" | L308 附近 |
| 2 | "all three monitoring signals degrade under fine-tuning, and $\tau$ degrades *fastest* in relative terms" | §tau_monitor |
| 3 | "computable from the top-$k$ class sets already available during validation" | L308 |

## 新数据

`outputs/a1_class_aligned/lr0.0/seed*/eval_epoch*.json`（逐 epoch 的 τ / top1_50k / val_loss）
+ `outputs/a1_epoch_sweep.json`（100 检查点的 τ / top1）

**判据**：逐 run 计算「首次下降的 epoch」，比较 τ vs top1 vs val_loss。

    python tools\_p240_check_monitor_claims.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "outputs" / "a1_class_aligned" / "lr0.0"
SWEEP = REPO / "outputs" / "a1_epoch_sweep.json"
OUT = REPO / "outputs" / "analysis" / "a1_monitor_claims_check.json"


def first_drop(vals, keys):
    """返回首个「比前一个小」的 keys 下标对应 epoch。"""
    for i in range(1, len(keys)):
        if vals[i] is not None and vals[i - 1] is not None and vals[i] < vals[i - 1]:
            return keys[i]
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    res = {}

    print("=" * 92)
    print("① 逐 run 的「首次下降 epoch」：τ vs top-1 vs val_loss")
    print("=" * 92)
    runs = defaultdict(dict)
    for f in sorted(glob.glob(str(ROOT / "seed*" / "eval_epoch*.json"))):
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        runs[Path(f).parent.name][d["eval_epoch"]] = d
    print(f"  {'run':<12}{'n':>4}{'τ首降':>8}{'top1首降':>10}{'val_loss首升':>12}"
          f"{'τ比top1早?':>12}")
    earlier = {"tau_vs_top1": 0, "tau_vs_vloss": 0, "total": 0}
    detail = {}
    for s in sorted(runs):
        v = runs[s]
        eps = sorted(v)
        if len(eps) < 5:
            print(f"  {s:<12}{len(eps):>4}  （不足 5 个 epoch，跳过）")
            continue
        tau = [v[e]["tau_final"] for e in eps]
        t1 = [v[e]["top1_50k"] for e in eps]
        vl = [v[e]["val_loss"] for e in eps]
        e_tau = first_drop(tau, eps)
        e_t1 = first_drop(t1, eps)
        # val_loss「首升」= 变差
        e_vl = None
        for i in range(1, len(eps)):
            if vl[i] is not None and vl[i - 1] is not None and vl[i] > vl[i - 1]:
                e_vl = eps[i]
                break
        tau_first = (e_tau is not None and (e_t1 is None or e_tau < e_t1))
        tau_vs_vl = (e_tau is not None and (e_vl is None or e_tau <= e_vl))
        earlier["tau_vs_top1"] += 1 if tau_first else 0
        earlier["tau_vs_vloss"] += 1 if tau_vs_vl else 0
        earlier["total"] += 1
        detail[s] = {"n_epochs": len(eps), "tau_first_drop": e_tau,
                     "top1_first_drop": e_t1, "val_loss_first_rise": e_vl,
                     "tau_earlier_than_top1": tau_first,
                     "tau_not_later_than_vloss": tau_vs_vl}
        print(f"  {s:<12}{len(eps):>4}{str(e_tau):>8}{str(e_t1):>10}{str(e_vl):>12}"
              f"{'✅ 是' if tau_first else '否':>12}")

    print()
    print("=" * 92)
    print("② 主张裁决")
    print("=" * 92)
    n = earlier["total"]
    r1 = earlier["tau_vs_top1"] / n if n else 0
    lib = {
        "1_earlier_than_top1": {
            "claim": "τ 是比 top-1 更早的指示器",
            "supported": earlier["tau_vs_top1"],
            "n": n,
            "verdict": ("支持" if r1 >= 0.7 else ("部分支持" if r1 >= 0.4 else "不支持")),
        },
        "2_relatively_fastest": {
            "claim": "τ 在相对意义上下降最快",
            "note": "需比较各信号的**相对降幅**（见 ③）",
        },
        "3_no_extra_forward": {
            "claim": "τ 只需验证时已有的 top-k 集合",
            "note": "代码事实（`a1_h_common.per_image_tau` 只读冻结 top-k 与当前分数）",
        },
    }
    print(f"  主张 1（τ 比 top-1 更早）：**{earlier['tau_vs_top1']}/{n}** 个 run 成立 "
          f"→ {lib['1_earlier_than_top1']['verdict']}")
    print(f"  主张 1b（τ 不晚于 val_loss 变差）：**{earlier['tau_vs_vloss']}/{n}** 个 run")

    # ③ 相对降幅
    print()
    print("=" * 92)
    print("③ 主张 2：各信号的**相对降幅**（epoch1 → 最后一个 epoch）")
    print("=" * 92)
    print(f"  {'run':<12}{'Δτ/τ₁':>12}{'Δtop1/top1₁':>15}{'Δval/val₁':>12}{'谁最快':>10}")
    fastest = {"tau": 0, "top1": 0, "val_loss": 0}
    for s in sorted(detail):
        v = runs[s]
        eps = sorted(v)
        tau = [v[e]["tau_final"] for e in eps]
        t1 = [v[e]["top1_50k"] for e in eps]
        vl = [v[e]["val_loss"] for e in eps]
        dt = (tau[0] - tau[-1]) / tau[0] if tau[0] else 0
        d1 = (t1[0] - t1[-1]) / t1[0] if t1[0] else 0
        dv = (vl[-1] - vl[0]) / vl[0] if vl[0] else 0
        who = max((("tau", dt), ("top1", d1), ("val_loss", dv)), key=lambda x: x[1])[0]
        fastest[who] += 1
        detail[s].update({"rel_drop_tau": round(dt, 4), "rel_drop_top1": round(d1, 4),
                          "rel_rise_vloss": round(dv, 4), "fastest": who})
        print(f"  {s:<12}{dt:>12.4f}{d1:>15.4f}{dv:>12.4f}{who:>10}")
    print()
    print(f"  相对降幅最大者：τ × {fastest['tau']} ｜ top-1 × {fastest['top1']} ｜ "
          f"val_loss × {fastest['val_loss']}")
    lib["2_relatively_fastest"].update({
        "fastest_counts": fastest,
        "verdict": ("支持" if fastest["tau"] >= max(fastest["top1"], fastest["val_loss"])
                    else "部分支持" if fastest["tau"] > 0 else "不支持"),
    })
    print(f"  → 主张 2：**{lib['2_relatively_fastest']['verdict']}**")

    lib["3_no_extra_forward"]["verdict"] = "支持（代码事实）"
    res = {"runs": detail, "claims": lib,
           "source": "outputs/a1_class_aligned/lr0.0/seed*/eval_epoch*.json"}
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
