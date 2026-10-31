# -*- coding: utf-8 -*-
r"""取 bf16 3-seed 的完整轨迹数据（供改写 `tab:vlm` 与 `discussion.tex`）（2026-10-10）。

    python tools\_p158_vlm_bf16_detail.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "vlm_bf16_detail.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    rows = {}
    for f in sorted(glob.glob(str(REPO / "outputs/vlm_seeds_bf16/*_seed*.json"))):
        d = json.loads(io.open(f, encoding="utf-8").read())
        rows.setdefault(d["arm"], {})[str(d["seed"])] = d

    print("=" * 78)
    print("逐 seed 完整数据（bf16, 400 样本 / 3 epoch / batch 2）")
    print("=" * 78)
    out = {}
    for arm in ("text_only", "vision_only", "both"):
        if arm not in rows:
            continue
        print(f"\n── {arm} ──")
        out[arm] = {}
        for seed in sorted(rows[arm], key=int):
            d = rows[arm][seed]
            dg = d["dg_star"]; cg = d["cg"]
            dg_rel = (dg[0] - dg[-1]) / dg[0] * 100.0
            out[arm][seed] = {
                "dg_star": dg, "cg": cg, "loss": d["loss"],
                "dg_rel_pct": round(dg_rel, 2),
                "cg_span": d["cg_span"], "dg_span": d["dg_span"],
                "n_trainable": d["n_trainable"],
                "elapsed": d["elapsed_sec"],
            }
            print(f"  seed {seed:<4} n_trainable={d['n_trainable']:>10,}")
            print(f"      DG* {dg[0]:.4f} → {dg[-1]:.4f}  相对变化 {dg_rel:+.1f}%")
            print(f"      CG  {cg[0]:.4f} → {cg[-1]:.4f}  跨度 {d['cg_span']:.4f}")
            print(f"      loss {[round(x, 4) for x in d['loss']]}  耗时 {d['elapsed_sec']}s")

    print()
    print("=" * 78)
    print("汇总")
    print("=" * 78)
    summary = {}
    for arm in ("text_only", "vision_only", "both"):
        if arm not in out:
            continue
        rels = [v["dg_rel_pct"] for v in out[arm].values()]
        cgs = [v["cg_span"] for v in out[arm].values()]
        n = len(rels)
        summary[arm] = {
            "n": n, "n_trainable": out[arm][sorted(out[arm], key=int)[0]]["n_trainable"],
            "dg_rel": [round(x, 2) for x in rels],
            "dg_rel_mean": round(st.mean(rels), 2),
            "dg_rel_sd": round(st.stdev(rels), 2) if n > 1 else None,
            "cg_span": [round(x, 4) for x in cgs],
            "cg_mean": round(st.mean(cgs), 4),
            "cg_sd": round(st.stdev(cgs), 4) if n > 1 else None,
        }
        print(f"  {arm:<12} n={n}  DG* 相对变化 {summary[arm]['dg_rel_mean']:+.1f}%"
              + (f" ± {summary[arm]['dg_rel_sd']:.1f}" if summary[arm]['dg_rel_sd'] else "")
              + f"   逐 seed {summary[arm]['dg_rel']}")
        print(f"  {'':<12}      CG 跨度 {summary[arm]['cg_mean']:.4f}"
              + (f" ± {summary[arm]['cg_sd']:.4f}" if summary[arm]['cg_sd'] else "")
              + f"  逐 seed {summary[arm]['cg_span']}")

    # 两两比较
    print()
    print("=== 两两比较（CG 跨度差 / 合并 sd）===")
    arms = [k for k in ("text_only", "vision_only", "both") if k in summary]
    for i in range(len(arms)):
        for j in range(i + 1, len(arms)):
            a1, a2 = arms[i], arms[j]
            d = abs(summary[a1]["cg_mean"] - summary[a2]["cg_mean"])
            s1, s2 = summary[a1]["cg_sd"], summary[a2]["cg_sd"]
            if s1 and s2:
                psd = (s1 ** 2 + s2 ** 2) ** 0.5
                k = d / psd if psd else float("nan")
                print(f"  {a1:<12} vs {a2:<12} |Δ|={d:.4f} pooled_sd={psd:.4f} → "
                      f"**{k:.2f} sd** " + ("显著" if k >= 2 else
                                            ("边缘" if k >= 1 else "**不显著**")))

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"per_run": out, "summary": summary,
             "config": "400 samples / 3 epochs / batch 2 / bf16",
             "note": "CG 跨度越小越保护；DG* 相对变化按 (dg0-dg3)/dg0 计"},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
