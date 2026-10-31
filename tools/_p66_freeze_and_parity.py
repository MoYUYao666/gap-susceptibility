# -*- coding: utf-8 -*-
r"""查：本地归档里的**冻结校验字段**与**训练循环来源**（2026-10-09）。

## 待答

1. 本地归档 `results.json` 里有没有"视觉侧非零张量 = 0"这类**冻结校验**？
2. 云端 `strict_freeze_control.py` 与本地是否**同一版本**（我上传的是 `cloud_pack`，
   而 `cloud_pack/tools/` 只含 `audit/` + 3 个脚本 —— **`experiments/` 是整体复制的**）？
3. 最关键：**两边 `strict_freeze_control.py` 是否逐字节相同**？

    python tools\_p66_freeze_and_parity.py [--apply]
"""
from __future__ import annotations

import glob
import hashlib
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "freeze_parity.json"


def main() -> int:
    apply = "--apply" in sys.argv

    print("=== ① 本地归档的完整字段（B/32 both seed42）===")
    f = REPO / "outputs/strict_freeze_b32_r4/both/seed42/results.json"
    if f.exists():
        d = json.loads(io.open(f, encoding="utf-8").read())
        for k in sorted(d):
            v = d[k]
            s = json.dumps(v, ensure_ascii=False)
            print(f"  {k:<34} {s[:110]}")
    else:
        print("  ❌ 缺")

    print("\n=== ② 本地脚本指纹 ===")
    for rel in ("experiments/strict_freeze_control.py", "src/trainer.py",
                "src/dataset.py", "src/config.py"):
        p = REPO / rel
        if p.exists():
            h = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
            print(f"  {rel:<40} sha256={h} ｜ {p.stat().st_size} B")

    print("\n=== ③ cloud_pack 里是否有同一份脚本 ===")
    cp = REPO / "cloud_pack/experiments/strict_freeze_control.py"
    if cp.exists():
        h1 = hashlib.sha256(cp.read_bytes()).hexdigest()[:16]
        h2 = hashlib.sha256((REPO / "experiments/strict_freeze_control.py").read_bytes()).hexdigest()[:16]
        print(f"  cloud_pack 版本 sha256={h1}")
        print(f"  本地版本      sha256={h2}")
        print(f"  {'✅ 一致' if h1 == h2 else '❌ **不一致**'}")
    else:
        print("  ❌ cloud_pack 里没有该脚本")

    print("\n=== ④ 归档里的 CGΔ 分布（看是否有负/正两组）===")
    rows = []
    for f2 in sorted(glob.glob(str(REPO / "outputs/strict_freeze_b32_r4/*/seed*/results.json"))):
        d = json.loads(io.open(f2, encoding="utf-8").read())
        arm = Path(f2).parent.parent.name
        seed = Path(f2).parent.name
        cg0 = d["initial_gap"]["centroid_gap"]; cg1 = d["final_gap"]["centroid_gap"]
        rows.append((arm, seed, cg0, cg1, cg1 - cg0))
    print(f"  {'arm':<13}{'seed':<9}{'CG0':>9}{'CG1':>9}{'CGΔ':>10}")
    for r in rows:
        print(f"  {r[0]:<13}{r[1]:<9}{r[2]:>9.4f}{r[3]:>9.4f}{r[4]:>+10.4f}")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps({
            "archive_fields": sorted(json.loads(io.open(
                REPO / "outputs/strict_freeze_b32_r4/both/seed42/results.json",
                encoding="utf-8").read()).keys()),
            "script_hashes": {rel: hashlib.sha256((REPO / rel).read_bytes()).hexdigest()
                              for rel in ("experiments/strict_freeze_control.py",
                                          "src/trainer.py", "src/dataset.py")
                              if (REPO / rel).exists()},
            "rows": [{"arm": a, "seed": s, "cg0": c0, "cg1": c1, "delta": d}
                     for a, s, c0, c1, d in rows],
        }, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
