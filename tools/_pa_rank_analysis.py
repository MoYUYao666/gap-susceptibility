# -*- coding: utf-8 -*-
r"""三骨干 rank 效应的**严格分析**（2026-10-05）。

## 为什么单独成脚本

我在此问题上**已快速断言三次，三次都错**（其中一次写进了正文）。故把分析固化成脚本：
**所有数字由代码算出，不再手工读**；每个断言都由配对检验支撑。

## 数据（全部严格冻结）

| 来源 | 内容 |
|---|---|
| `outputs/strict_freeze/` | CLIP B/32 r8（5 seeds） |
| `outputs/strict_freeze_rank/r{1,4,16,32,64}/` | CLIP B/32 其他 rank（3 seeds） |
| `outputs/strict_freeze_openclip/` | OpenCLIP B/32 r8（5 seeds） |
| `outputs/strict_freeze_openclip_rank/r4/` | OpenCLIP B/32 r4（5 seeds） |
| `outputs/siglip_strict/*/s4_siglip_lora_*` | SigLIP B/16 r8（5 seeds） |
| `outputs/siglip_strict/*/s7_siglip_lora_r4_*` | SigLIP B/16 r4（5 seeds） |

    python tools\_pa_rank_analysis.py
"""
from __future__ import annotations

import json
import math
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def load(pattern: str) -> dict[int, float]:
    """返回 {seed: ΔCG}。"""
    out: dict[int, float] = {}
    for p in sorted(REPO.glob(pattern)):
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        ig, fg = d.get("initial_gap") or {}, d.get("final_gap") or {}
        if ig.get("centroid_gap") is None or fg.get("centroid_gap") is None:
            continue
        seed = d.get("seed")
        if seed is None:
            # 从路径推断（SigLIP 的结果文件不记 seed）
            m = [x for x in p.parts if x.startswith("seed")]
            seed = int(m[0][4:]) if m else 0
        out[int(seed)] = fg["centroid_gap"] - ig["centroid_gap"]
    return out


# (骨干, 臂) -> {rank: {seed: ΔCG}}
DATA: dict[tuple[str, str], dict[int, dict[int, float]]] = {
    ("CLIP B/32", "text_only"): {
        8: load("outputs/strict_freeze/text_only/seed*/results.json"),
        4: load("outputs/strict_freeze_rank/r4/text_only/seed*/results.json"),
        1: load("outputs/strict_freeze_rank/r1/text_only/seed*/results.json"),
        16: load("outputs/strict_freeze_rank/r16/text_only/seed*/results.json"),
        32: load("outputs/strict_freeze_rank/r32/text_only/seed*/results.json"),
        64: load("outputs/strict_freeze_rank/r64/text_only/seed*/results.json"),
    },
    ("CLIP B/32", "both"): {
        8: load("outputs/strict_freeze/both/seed*/results.json"),
        4: load("outputs/strict_freeze_rank/r4/both/seed*/results.json"),
        1: load("outputs/strict_freeze_rank/r1/both/seed*/results.json"),
        16: load("outputs/strict_freeze_rank/r16/both/seed*/results.json"),
        32: load("outputs/strict_freeze_rank/r32/both/seed*/results.json"),
        64: load("outputs/strict_freeze_rank/r64/both/seed*/results.json"),
    },
    ("OpenCLIP B/32", "text_only"): {
        8: load("outputs/strict_freeze_openclip/text_only/seed*/results.json"),
        4: load("outputs/strict_freeze_openclip_rank/r4/text_only/seed*/results.json"),
    },
    ("OpenCLIP B/32", "both"): {
        8: load("outputs/strict_freeze_openclip/both/seed*/results.json"),
        4: load("outputs/strict_freeze_openclip_rank/r4/both/seed*/results.json"),
    },
    ("SigLIP B/16", "text_only"): {
        8: load("outputs/siglip_strict/*/s4_siglip_lora_text_only/results.json"),
        4: load("outputs/siglip_strict/*/s7_siglip_lora_r4_text_only/results.json"),
    },
    ("SigLIP B/16", "both"): {
        8: load("outputs/siglip_strict/*/s4_siglip_lora_both/results.json"),
        4: load("outputs/siglip_strict/*/s7_siglip_lora_r4_both/results.json"),
    },
}


def paired(a: dict[int, float], b: dict[int, float]) -> tuple[float, float, float, int] | None:
    ss = sorted(set(a) & set(b))
    if len(ss) < 2:
        return None
    ds = [a[s] - b[s] for s in ss]
    m, sd = st.mean(ds), st.stdev(ds)
    t = m / (sd / math.sqrt(len(ds))) if sd else float("inf")
    return m, sd, t, len(ss)


def main() -> int:
    print("=== ① 每个（骨干, 臂）的 rank 曲线 ===")
    for (bb, arm), byrank in DATA.items():
        ks = sorted(k for k, v in byrank.items() if v)
        if not ks:
            continue
        line = "  ".join("r%d=%+.4f(n=%d)" % (k, st.mean(list(byrank[k].values())), len(byrank[k])) for k in ks)
        print("  %-16s %-10s %s" % (bb, arm, line))

    print("\n=== ② rank 方向（r4 → r8，配对检验）===")
    print("  %-16s %-10s %10s %8s %8s %s" % ("骨干", "臂", "平均差", "t", "n", "方向"))
    dirs = []
    for (bb, arm), byrank in DATA.items():
        if 4 in byrank and 8 in byrank and byrank[4] and byrank[8]:
            r = paired(byrank[8], byrank[4])   # r8 − r4
            if r:
                m, sd, t, n = r
                d = "r8 更小(间隙↓)" if m < 0 else "r8 更大(间隙↑)"
                dirs.append((bb, arm, d))
                print("  %-16s %-10s %+10.4f %+8.2f %8d %s" % (bb, arm, m, t, n, d))

    print("\n=== ③ 位置排序（每个骨干 × rank：text_only vs both 谁 ΔCG 更小）===")
    consistent = 0
    total = 0
    for bb in ("CLIP B/32", "OpenCLIP B/32", "SigLIP B/16"):
        t_arm = DATA.get((bb, "text_only"), {})
        b_arm = DATA.get((bb, "both"), {})
        for rk in sorted(set(t_arm) & set(b_arm)):
            if not t_arm[rk] or not b_arm[rk]:
                continue
            tv, bv = st.mean(list(t_arm[rk].values())), st.mean(list(b_arm[rk].values()))
            who = "text_only" if tv < bv else "both"
            total += 1
            if who == "text_only":
                consistent += 1
            print("  %-16s r%-3d text_only %+.4f vs both %+.4f → %s 更小" % (bb, rk, tv, bv, who))
    print("\n  → text_only 更小的组合: %d/%d" % (consistent, total))

    print("\n=== ④ 结论 ===")
    uniq = {d for _, _, d in dirs}
    print("  rank 方向取值: %s  → %s" % (sorted(uniq),
          "**方向不一致**（跨骨干或跨臂存在相反）" if len(uniq) > 1 else "方向一致"))
    print("  位置排序一致性: %d/%d" % (consistent, total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
