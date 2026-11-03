# -*- coding: utf-8 -*-
r"""检查新补 seed 的结果质量 + 排序稳定性（2026-10-09）。

## 要回答

1. 新 run 的 `R@1` 是否正常（**排除云端那种失效**，`R@1=0.002`）？
2. `n_trainable_params` 是否与同目录其它 run 一致（**排除口径漂移**）？
3. 补 seed 后**最保护臂是否仍为 `text_only`**（风险 #1 判据）？

    python tools\_p75_new_seed_check.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "new_seed_check.json"
# 本次（2026-10-09）新补的 run
NEW = [
    "outputs/strict_freeze_b16/r4/both/seed456",
    "outputs/strict_freeze_b16/r4/vision_only/seed456",
]
ARMS = ("text_only", "both", "vision_only")
CONFIGS = [("CLIP B/32 r4", "outputs/strict_freeze_b32_r4"),
           ("CLIP B/16 r4", "outputs/strict_freeze_b16/r4"),
           ("OpenCLIP r4", "outputs/strict_freeze_oclip/r4")]


def main() -> int:
    apply = "--apply" in sys.argv

    print("=== ① 本次新 run 的质量（R@1 必须远离 0）===")
    bad = []
    for rel in NEW:
        f = REPO / rel / "results.json"
        if not f.exists():
            print(f"  {rel}: ⏳ 未完成")
            continue
        d = json.loads(io.open(f, encoding="utf-8").read())
        r1 = d["final_task_metrics"]["R@1"]
        n = d["n_trainable_params"]
        loss = d["final_train_loss"]
        ok = r1 > 0.3
        if not ok:
            bad.append(rel)
        print(f"  {rel.split('/')[-2]}/{rel.split('/')[-1]:<8} R@1={r1:.4f} ｜ "
              f"loss末={loss:.4f} ｜ n_trainable={n} ｜ {'✅' if ok else '❌ 疑似失效'}")

    print("\n=== ② 同目录内 n_trainable 是否一致（防口径漂移）===")
    for label, pat in CONFIGS:
        for arm in ARMS:
            ns = set()
            for f in glob.glob(str(REPO / pat / arm / "seed*" / "results.json")):
                ns.add(json.loads(io.open(f, encoding="utf-8").read())["n_trainable_params"])
            if len(ns) > 1:
                print(f"  ❌ {label}/{arm}: {sorted(ns)} ← **口径不一致**")
            elif ns:
                print(f"  ✅ {label}/{arm}: {ns.pop()}")

    print("\n=== ③ 排序稳定性（风险 #1 判据：最保护臂不得翻转）===")
    report = {}
    for label, pat in CONFIGS:
        vals = {}
        for arm in ARMS:
            xs = []
            for f in sorted(glob.glob(str(REPO / pat / arm / "seed*" / "results.json"))):
                d = json.loads(io.open(f, encoding="utf-8").read())
                xs.append(d["final_gap"]["centroid_gap"] - d["initial_gap"]["centroid_gap"])
            if xs:
                vals[arm] = {"n": len(xs), "mean": st.mean(xs),
                             "sd": st.stdev(xs) if len(xs) > 1 else None,
                             "vals": [round(v, 4) for v in xs]}
        if not vals:
            print(f"  {label}: （无数据）")
            continue
        print(f"  ── {label}")
        for arm in ARMS:
            if arm in vals:
                v = vals[arm]
                sd = f"±{v['sd']:.4f}" if v["sd"] is not None else "（1 seed）"
                print(f"     {arm:<12} {v['mean']:+.4f} {sd:<11} n={v['n']}  {v['vals']}")
        best = min(vals, key=lambda a: vals[a]["mean"])
        same = best == "text_only"
        print(f"     → 最保护 = **{best}** {'✅ 未翻转' if same else '❌ **翻转**'}")
        report[label] = {"arms": vals, "most_protective": best, "same_as_prior": same}

    if bad:
        print(f"\n  ⚠️ 疑似失效的 run：{bad} → **需查**（可能又是环境问题）")
    else:
        print("\n  ✅ 本次新 run 的 R@1 均正常（>0.3），无云端那种失效")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"report": report, "suspect_runs": bad}, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
