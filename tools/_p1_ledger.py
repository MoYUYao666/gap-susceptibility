# -*- coding: utf-8 -*-
r"""生成权威"实测台账"：正文所有 ODE 相关数字的**可复现值**（2026-10-07，操作者选 B）。

## 为什么

正文声称 ODE 拟合跨 **162 runs（81/数据集）**、LoRA R² = **0.985–0.986**；
`outputs/theory/` 实测只有 **96 runs**，LoRA R² = **0.949**。

操作者决定：**用实测值改正正文**。故本脚本产出**唯一权威台账**，供逐处替换引用。

## 两种拟合口径都算，并**采用与正文逐秩表一致的口径**

正文 `validation.tex:102` 写 `CLIP + Flickr30k + LoRA  0.985 ± 0.008  81`
—— `±` 说明是**跨 run 的均值±标准差** → **逐 run 拟合**口径。
故台账以**逐 run** 为主口径，种子均值作对照。

    python tools\_p1_ledger.py [--apply]
"""
from __future__ import annotations

import collections
import glob
import io
import json
import re
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "ode_ledger.json"

try:
    import numpy as np
except Exception:
    np = None


def r2(y, yh):
    y = np.asarray(y, float); yh = np.asarray(yh, float)
    ss = float(((y - y.mean()) ** 2).sum())
    return 1.0 - float(((y - yh) ** 2).sum()) / ss if ss > 0 else float("nan")


def grid_fit(t, y):
    t = np.asarray(t, float); y = np.asarray(y, float)
    dg0 = float(y[0]); r = y - dg0
    best = (float("nan"), float("nan"), float("inf"))
    for logb in np.linspace(np.log10(0.005), np.log10(20.0), 800):
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
    return float(A), float(B), r2(y, dg0 + (A / B) * (1.0 - np.exp(-B * t)))


def classify(conf: str) -> dict:
    low = conf.lower()
    fam = ("adapter" if "adapter" in low
           else "full_ft" if ("full_ft" in low or "fullft" in low) else "lora")
    site = ("text_only" if "text_only" in low else
            "vision_only" if "vision_only" in low else
            "both" if "both" in low else "other")
    m = re.search(r"_r(\d+)$|_d(\d+)$", low)
    return {"family": fam, "site": site, "rank": int(m.group(1) or m.group(2)) if m else None}


def main() -> int:
    apply = "--apply" in sys.argv
    if np is None:
        print("  ❌ 需要 numpy"); return 1

    runs, byconf = [], collections.defaultdict(list)
    for f in sorted(glob.glob(str(REPO / "outputs/theory/**/dg_star_history.json"), recursive=True)):
        rel = Path(f).relative_to(REPO / "outputs" / "theory")
        conf = "/".join(rel.parts[:-2])
        d = json.loads(io.open(f, encoding="utf-8").read())
        if len(d["epochs"]) < 5:
            continue
        A, B, R = grid_fit(d["epochs"], d["dg_star"])
        meta = classify(conf)
        rec = dict(conf=conf, top=rel.parts[0], seed=rel.parts[-2], n_epoch=len(d["epochs"]),
                   alpha=A, beta=B, R2=R, **meta)
        runs.append(rec)
        byconf[conf].append(rec)

    print(f"  === 权威台账（逐 run 口径，n={len(runs)}）===")
    print(f"  {'子集':<40} {'n':>4} {'R² 均值':>9} {'±sd':>7} {'中位':>7} {'范围':>15}")
    print("  " + "-" * 88)

    def line(name, sel):
        s = [r for r in runs if sel(r)]
        rs = [r["R2"] for r in s if r["R2"] == r["R2"]]
        if not rs:
            print(f"  {name:<40} {0:>4}  —"); return None
        sd = st.stdev(rs) if len(rs) > 1 else 0.0
        print(f"  {name:<40} {len(rs):>4} {st.mean(rs):>9.4f} {sd:>7.4f} "
              f"{st.median(rs):>7.4f} {min(rs):>6.3f}–{max(rs):<7.3f}")
        return dict(n=len(rs), mean=st.mean(rs), sd=sd, median=st.median(rs),
                    min=min(rs), max=max(rs))

    L = {}
    L["all"] = line("全部 run", lambda r: True)
    L["lora"] = line("LoRA 全部", lambda r: r["family"] == "lora")
    L["lora_flickr"] = line("LoRA + Flickr30k", lambda r: r["family"] == "lora" and r["top"] != "coco")
    L["lora_coco"] = line("LoRA + MS-COCO", lambda r: r["family"] == "lora" and r["top"] == "coco")
    L["adapter"] = line("Adapter", lambda r: r["family"] == "adapter")
    L["full_ft"] = line("full-FT", lambda r: r["family"] == "full_ft")

    print(f"\n  === 逐秩（Flickr30k, both 位, v1_trajectory, LoRA）===")
    print(f"  {'秩':>4} {'n':>4} {'R² 均值':>9} {'α 均值':>10} {'β 均值':>9}   正文 R²")
    PAPER = {1: None, 2: 0.975, 4: None, 8: None, 16: None, 32: None, 64: 0.981}
    byrank = collections.defaultdict(list)
    for r in runs:
        if (r["family"] == "lora" and r["top"] == "v1_trajectory"
                and r["site"] == "both" and r["rank"]):
            byrank[r["rank"]].append(r)
    ranks = {}
    for k in sorted(byrank):
        v = byrank[k]
        rs = [x["R2"] for x in v]
        al = [x["alpha"] for x in v]
        be = [x["beta"] for x in v]
        ranks[k] = dict(n=len(v), R2=st.mean(rs), alpha=st.mean(al), beta=st.mean(be))
        p = PAPER.get(k)
        print(f"  {k:>4} {len(v):>4} {st.mean(rs):>9.4f} {st.mean(al):>10.4f} {st.mean(be):>9.4f}"
              f"   {('%.3f' % p) if p else '—'}")

    # 种子均值口径对照
    print(f"\n  === 对照：种子均值口径 ===")
    confs = {}
    for conf, rr in byconf.items():
        n = min(x["n_epoch"] for x in rr)
        if n < 5:
            continue
        confs[conf] = rr
    print(f"  配置数: {len(confs)}")
    lorac = [c for c in confs if classify(c)["family"] == "lora"]
    print(f"  LoRA 配置数: {len(lorac)}（正文称 14 配置 × 2 数据集）")

    res = {"caliber": "per-run", "n_runs_total": len(runs), "subsets": L,
           "per_rank_flickr_both": ranks, "n_configs": len(confs),
           "n_configs_lora": len(lorac),
           "runs": [{k: v for k, v in r.items()} for r in runs]}
    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    else:
        print("\n  （预演；加 --apply 落盘）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
