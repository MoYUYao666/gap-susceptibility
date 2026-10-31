# -*- coding: utf-8 -*-
r"""汇总实验 ③ 的结果：patch-size 规律在新增骨干上是否复现（2026-10-07）。

## 检验什么

论文的规律（`empirical.tex`）：
> "every patch-32 backbone has the **text-only** arm at the smallest gap change and
> every patch-16 backbone has the **both**-position arm there, without exception"

**新增骨干**：
- **③a OpenCLIP B/32**（patch-32）→ 期望 **text-only 的 CGΔ 最负**
- **③b CLIP B/16**（patch-16）→ 期望 **both 的 CGΔ 最负**

**这是对"patch size 决定排序"的关键检验**：CLIP B/16 与 CLIP B/32 **同族、同预训练目标，仅 patch size 不同**，
是唯一能把 patch size 与模型身份分开的对照。

    python tools\_p9_patchsize_verdict.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "patchsize_verdict.json"

ARMS = ("text_only", "both", "vision_only")


def load(d: Path) -> dict:
    """取三臂的 CGΔ（末态−初态）。"""
    res = {}
    for f in sorted(glob.glob(str(d / "*" / "seed*" / "results.json"))):
        j = json.loads(io.open(f, encoding="utf-8").read())
        arm = f.replace("\\", "/").split("/")[-3]
        cg0, cg1 = j.get("cg_initial"), j.get("cg_final")
        if cg0 is None or cg1 is None:
            for k in ("initial_gap", "final_gap"):
                pass
            g0 = j.get("initial_gap", {}).get("centroid_gap") if isinstance(j.get("initial_gap"), dict) else None
            g1 = j.get("final_gap", {}).get("centroid_gap") if isinstance(j.get("final_gap"), dict) else None
            cg0, cg1 = g0, g1
        if cg0 is not None and cg1 is not None:
            res[arm] = cg1 - cg0
    return res


def main() -> int:
    apply = "--apply" in sys.argv
    targets = {
        "OpenCLIP B/32 (r4)": (REPO / "outputs/strict_freeze_oclip/r4", 32, "text_only"),
        "CLIP B/16 (r4)":     (REPO / "outputs/strict_freeze_b16/r4", 16, "both"),
    }
    verdict = {}
    for name, (d, patch, expect) in targets.items():
        if not d.exists():
            print(f"  ⏳ {name}: 目录不存在（未跑）")
            continue
        cg = load(d)
        if not cg:
            print(f"  ⏳ {name}: 尚无 results.json")
            continue
        print(f"\n  === {name}（patch={patch}，预期最保护臂={expect}）===")
        for a in ARMS:
            if a in cg:
                print(f"    {a:<12} CGΔ = {cg[a]:+.4f}")
        best = min(cg, key=lambda a: cg[a])
        ok = best == expect
        verdict[name] = {"patch": patch, "cg_delta": cg, "most_protective": best,
                         "expected": expect, "consistent": bool(ok)}
        print(f"    → 最保护臂 = **{best}**　{'✅ 与预期一致' if ok else '❌ 与预期不符'}")

    if not verdict:
        print("\n  尚无可判定的结果（队列仍在跑）")
        return 0

    print(f"\n  === 规律检验 ===")
    for name, v in verdict.items():
        print(f"    {name:<20} 最保护={v['most_protective']:<12} "
              f"{'✅' if v['consistent'] else '❌'}")
    allok = all(v["consistent"] for v in verdict.values())
    print(f"\n  {'✅ 规律在新增骨干上复现' if allok else '⚠ 存在不符 → 规律需收窄表述'}")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(verdict, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
