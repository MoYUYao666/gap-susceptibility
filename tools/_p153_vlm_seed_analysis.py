# -*- coding: utf-8 -*-
r"""解码器 VLM 三臂多 seed 分析（C3 缺口）（2026-10-10）。

## 要回答

1. 三臂的 `cg_span` / `dg_span` **mean ± sd**（现只 1 seed，值几乎贴在一起：
   0.2761 / 0.2778 / 0.3056）
2. **`text_only` vs `both` 的排序是否显著**（三臂贴太近，必须看 sd）
3. 复跑 seed 42 是否与归档**逐位一致**（验证 `--seed` 改动无副作用）
4. 4-bit 统一后，`text_only` 是否与归档的 **bf16** 值差异明显（量化 C5）

    python tools\_p153_vlm_seed_analysis.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "vlm_seed_verdict.json"
ARMS = ("text_only", "both", "vision_only")


def load(pattern: str):
    out = {}
    for f in sorted(glob.glob(str(REPO / pattern), recursive=True)):
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        if "arm" not in d:
            continue
        arm = d["arm"]
        out.setdefault(arm, []).append({
            "file": str(Path(f).relative_to(REPO)), "seed": d.get("seed"),
            "cg_span": d.get("cg_span"), "dg_span": d.get("dg_span"),
            "4bit": d.get("4bit"), "n_epochs": len(d.get("cg") or []),
            "elapsed": d.get("elapsed_sec"),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    new = load("outputs/vlm_seeds/*.json")
    arch = load("outputs/vlm_strictfreeze/4bit/*_seed42.json")
    arch2 = load("outputs/vlm_strictfreeze/*_seed42.json")
    repro = load("outputs/vlm_seeds_repro/*.json")

    print("=" * 74)
    print("① 新的多 seed 结果（4-bit 统一）")
    print("=" * 74)
    res = {}
    for arm in ARMS:
        xs = new.get(arm, [])
        if not xs:
            print(f"  {arm:<12} —— 无数据")
            continue
        cg = [x["cg_span"] for x in xs if x["cg_span"] is not None]
        dg = [x["dg_span"] for x in xs if x["dg_span"] is not None]
        seeds = sorted(str(x["seed"]) for x in xs)
        m, s = st.mean(cg), (st.stdev(cg) if len(cg) > 1 else None)
        md, sd = st.mean(dg), (st.stdev(dg) if len(dg) > 1 else None)
        res[arm] = {"n": len(cg), "seeds": seeds,
                    "cg_mean": round(m, 5), "cg_sd": round(s, 5) if s else None,
                    "dg_mean": round(md, 5), "dg_sd": round(sd, 5) if sd else None,
                    "cg_all": [round(v, 5) for v in cg]}
        print(f"  {arm:<12} n={len(cg)} seeds={seeds}")
        print(f"      CG 跨度 {m:.4f}" + (f" ± {s:.4f}" if s else "")
              + f"   ｜ DG* 跨度 {md:.4f}" + (f" ± {sd:.4f}" if sd else ""))
        print(f"      CG 逐 seed: {[round(v,4) for v in cg]}")

    print()
    print("=" * 74)
    print("② 排序是否显著（CG 跨度越大 = 保护越弱）")
    print("=" * 74)
    if len(res) >= 2:
        order = sorted(res, key=lambda k: res[k]["cg_mean"])
        print("  由保护强到弱：" + " < ".join(
            f"{k}({res[k]['cg_mean']:.4f})" for k in order))
        # 相邻差异 vs 合并 sd
        for i in range(len(order) - 1):
            a1, a2 = order[i], order[i + 1]
            d = abs(res[a1]["cg_mean"] - res[a2]["cg_mean"])
            s1, s2 = res[a1]["cg_sd"], res[a2]["cg_sd"]
            if s1 and s2:
                psd = (s1 ** 2 + s2 ** 2) ** 0.5
                k = d / psd if psd else float("nan")
                verdict = ("✅ 显著" if k >= 2 else
                           ("⚠️ 边缘" if k >= 1 else "🔴 **不显著**"))
                print(f"    {a1} vs {a2}: |Δ|={d:.4f}  pooled_sd={psd:.4f} → "
                      f"**{k:.2f} sd**  {verdict}")
            else:
                print(f"    {a1} vs {a2}: |Δ|={d:.4f}（sd 不足，无法判）")

    print()
    print("=" * 74)
    print("③ 复跑 seed 42 vs 归档（验证 --seed 改动无副作用）")
    print("=" * 74)
    for arm in ("both", "vision_only"):
        a1 = (arch.get(arm) or arch2.get(arm) or [{}])[0]
        r1 = (repro.get(arm) or [{}])[0]
        if not a1.get("cg_span") or not r1.get("cg_span"):
            print(f"  {arm:<12} 数据不全")
            continue
        same = (abs(a1["cg_span"] - r1["cg_span"]) < 1e-9
                and abs(a1["dg_span"] - r1["dg_span"]) < 1e-9)
        print(f"  {arm:<12} 归档 cg={a1['cg_span']:.6f} → 复跑 cg={r1['cg_span']:.6f}  "
              f"{'✅ 逐位一致' if same else '⚠️ 有差异'}")
        print(f"  {'':<12} 归档 dg={a1['dg_span']:.6f} → 复跑 dg={r1['dg_span']:.6f}")

    print()
    print("=" * 74)
    print("④ 4-bit 统一 vs 归档的 text_only（bf16）—— 量化 C5")
    print("=" * 74)
    to_bf16 = (arch2.get("text_only") or [{}])[0]
    if to_bf16.get("cg_span") and res.get("text_only"):
        print(f"  text_only 归档（**bf16**，400/3ep）: cg_span={to_bf16['cg_span']:.4f} "
              f"dg_span={to_bf16['dg_span']:.4f}")
        print(f"  text_only 新跑（**4-bit**，n={res['text_only']['n']}）: "
              f"cg_span={res['text_only']['cg_mean']:.4f} ± "
              f"{res['text_only']['cg_sd']}  dg_span={res['text_only']['dg_mean']:.4f}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"per_arm": res,
             "archived_textonly_bf16": {"cg_span": to_bf16.get("cg_span"),
                                        "dg_span": to_bf16.get("dg_span")},
             "repro": {k: v[0] if v else None for k, v in repro.items()}},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
