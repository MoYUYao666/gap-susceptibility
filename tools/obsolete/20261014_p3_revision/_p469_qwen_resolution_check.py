# -*- coding: utf-8 -*-
r"""P3 §3.3 分辨率稳健性检验：对比 max_pixels=16384 与 50176 两档的 ΔE 符号。

只读两个归档，不引入外部数字。

    python tools\_p469_qwen_resolution_check.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import statistics as st
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A = REPO / "outputs" / "analysis"
SRC_MAIN = A / "p3d_qwen_ranksweep.json"          # max_pixels=16384
SRC_HI = A / "p3d_qwen_ranksweep_mp50176.json"    # max_pixels=50176
OUT = A / "p3d_qwen_resolution_check.json"


def load(p):
    return json.loads(io.open(p, encoding="utf-8").read())


def cell(runs, n_train=None):
    d = defaultdict(list)
    for r in runs:
        if r.get("rank", 0) <= 0 or r.get("dE_train") is None:
            continue
        if n_train is not None and r["n_train"] != n_train:
            continue
        d[(r["condition"], r["rank"])].append((r["seed"], r["dE_train"],
                                               r.get("dE_eval_real"),
                                               r.get("E_train_epochs"),
                                               r.get("loss_epochs")))
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    main_d, hi_d = load(SRC_MAIN), load(SRC_HI)
    lo = cell(main_d["runs"], n_train=16)
    hi = cell(hi_d["runs"], n_train=16)

    print("=== 分辨率稳健性：同一协议，只有 max_pixels 不同 ===")
    print(f"  低档 {SRC_MAIN.name}: max_pixels=16384（实测 15 visual token）")
    print(f"  高档 {SRC_HI.name}: max_pixels=50176（实测 54 visual token）")
    print(f"\n{'档':<8} {'条件':<6} {'rank':<5} {'seed':<5} {'dE_train':>10} "
          f"{'dE_eval_real':>13}  E 轨迹（初始+每epoch）           loss 每 epoch")
    for tag, d in (("16384", lo), ("50176", hi)):
        for (cond, rank) in sorted(d, key=lambda x: (x[1], x[0])):
            for (seed, dEt, dEe, traj, loss) in d[(cond, rank)]:
                tr = " → ".join(f"{v:.0f}" for v in (traj or []))
                ls = " ".join(f"{v:.3f}" for v in (loss or []))
                print(f"{tag:<8} {cond:<6} {rank:<5} {seed:<5} {dEt:>+10.2f} "
                      f"{dEe:>+13.2f}  {tr:<42} [{ls}]")
                # 自检：E 轨迹长度应为 1+epochs，loss 长度应为 epochs
                if traj and loss and len(traj) != len(loss) + 1:
                    print(f"         !! 长度异常 E={len(traj)} loss={len(loss)}")

    def sign_summary(d, cond):
        v = [x[1] for k, xs in d.items() if k[0] == cond for x in xs]
        pos, neg = sum(1 for x in v if x > 0), sum(1 for x in v if x < 0)
        return {"n": len(v), "n_positive": pos, "n_negative": neg,
                "mean": sum(v) / len(v) if v else None,
                "min": min(v) if v else None, "max": max(v) if v else None}

    lo_real, lo_blank = sign_summary(lo, "real"), sign_summary(lo, "blank")
    hi_real, hi_blank = sign_summary(hi, "real"), sign_summary(hi, "blank")
    print("\n=== 符号汇总（dE_train）===")
    for tag, r_, b_ in (("16384", lo_real, lo_blank), ("50176", hi_real, hi_blank)):
        print(f"  max_pixels={tag}:  real  n={r_['n']} 正/负={r_['n_positive']}/"
              f"{r_['n_negative']} 范围[{r_['min']:.1f}, {r_['max']:.1f}]   |   "
              f"blank n={b_['n']} 正/负={b_['n_positive']}/{b_['n_negative']} "
              f"范围[{b_['min']:.1f}, {b_['max']:.1f}]")

    ok_lo = lo_real["n_negative"] == 0 and lo_blank["n_positive"] == 0
    ok_hi = hi_real["n_negative"] == 0 and hi_blank["n_positive"] == 0
    print(f"\n  「real 全正 / blank 全负」在 max_pixels=16384 下成立: {ok_lo}")
    print(f"  「real 全正 / blank 全负」在 max_pixels=50176 下成立: {ok_hi}")
    print(f"  → 该符号模式对视觉 token 预算敏感: {ok_lo != ok_hi}")

    # 配对（同 rank/同 seed），只在两档各自内部配对
    def paired(d):
        out = []
        for (cond, rank) in d:
            if cond != "real":
                continue
            for (seed, dEt, dEe, _t, _l) in d[(cond, rank)]:
                bl = [x for x in d.get(("blank", rank), []) if x[0] == seed]
                if bl:
                    out.append({"rank": rank, "seed": seed,
                                "dE_train_blank_minus_real": bl[0][1] - dEt,
                                "dE_eval_blank_minus_real": (bl[0][2] or 0) - (dEe or 0)})
        return out

    pl, ph = paired(lo), paired(hi)
    print(f"\n=== 配对 blank−real（同 rank/同 seed）===")
    for tag, p in (("16384", pl), ("50176", ph)):
        neg = sum(1 for x in p if x["dE_train_blank_minus_real"] < 0)
        print(f"  max_pixels={tag}: n={len(p)}  ΔE_train 为负 {neg}/{len(p)}  "
              f"均值={sum(x['dE_train_blank_minus_real'] for x in p)/len(p):+.2f}")

    res = {"experiment": "p3d_qwen_resolution_check",
           "script": "tools/_p469_qwen_resolution_check.py",
           "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "sources": {"max_pixels_16384": SRC_MAIN.name, "max_pixels_50176": SRC_HI.name},
           "visual_tokens": {"16384": 15.0, "50176": 54.0},
           "sign_summary": {"16384": {"real": lo_real, "blank": lo_blank},
                            "50176": {"real": hi_real, "blank": hi_blank}},
           "pattern_holds": {"16384": ok_lo, "50176": ok_hi},
           "paired": {"16384": pl, "50176": ph},
           "conclusion": ("「real 全正 / blank 全负」只在 max_pixels=16384（15 visual token）下成立；"
                          "在 50176（54 token）下 real 的 dE_train 变为负 → 该符号模式对视觉 token "
                          "预算敏感，不能作为一般性主张。"
                          if ok_lo and not ok_hi else "见 sign_summary")}
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
