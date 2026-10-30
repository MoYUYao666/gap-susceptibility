# -*- coding: utf-8 -*-
r"""用容差法重查「两格是否真的无来源」（补 `_p325` 主张③ 的空列表 bug）（2026-10-12）。

    python tools\_p326_find_r1_source.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "r1_source_search.json"
TARGETS = {"CLIP_B32_r4/both": 0.679, "CLIP_B16_r4/text_only": 0.651}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    groups = defaultdict(list)
    for f in glob.glob(str(REPO / "outputs" / "**" / "results.json"), recursive=True):
        try:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        if "initial_gap" not in d or "final_gap" not in d:
            continue
        v = (d.get("final_task_metrics") or {}).get("R@1")
        if v is None:
            continue
        parts = Path(f).relative_to(REPO).parts[1:-1]
        # 归一：去掉 seed 目录，保留 到 arm 为止 的路径（与 _p319/_p322 同一粒度）
        arm_i = next((i for i, p in enumerate(parts)
                      if p in ("text_only", "both", "vision_only",
                               "text-only", "vision-only")), None)
        if arm_i is not None:
            key = "/".join(parts[:arm_i + 1])
        else:
            key = "/".join(parts[:-1]) if len(parts) > 1 else parts[0]
        groups[key].append({
            "R@1": v, "seed": d.get("seed"), "n": d.get("n_trainable_params"),
            "file": str(Path(f).relative_to(REPO)),
        })
    print(f"  扫描得到 {len(groups)} 个目录组，"
          f"其中 n>=3 的 {sum(1 for v in groups.values() if len(v) >= 3)} 个")

    rep = {}
    for name, tgt in TARGETS.items():
        print()
        print("=" * 100)
        print(f"{name}  论文 {tgt}  —— 容差扫描")
        print("=" * 100)
        rows = []
        for g, vs in groups.items():
            if len(vs) < 3:
                continue
            m = sum(x["R@1"] for x in vs) / len(vs)
            rows.append((g, m, len(vs), sorted({str(x["n"]) for x in vs}),
                         sorted({str(x["seed"]) for x in vs})))
        rows.sort(key=lambda r: abs(r[1] - tgt))
        print("  最接近的 8 个组：")
        for g, m, n, nts, seeds in rows[:8]:
            flag = "🎯" if round(m, 3) == tgt else ("≈" if abs(m - tgt) < 0.002 else " ")
            print(f"    {flag} {m:.6f}  Δ={m-tgt:+.6f}  n={n}  n_tr={nts}  "
                  f"seeds={seeds}")
            print(f"         {g}")
        exact = [r for r in rows if round(r[1], 3) == tgt]
        print(f"  → 四舍五入到 3 位小数命中 {tgt} 的组数：{len(exact)}")
        rep[name] = {"published": tgt, "n_exact_hits": len(exact),
                     "nearest": [{"dir": g, "mean": round(m, 6), "n": n,
                                  "n_train": nts, "seeds": seeds}
                                 for g, m, n, nts, seeds in rows[:8]]}

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
