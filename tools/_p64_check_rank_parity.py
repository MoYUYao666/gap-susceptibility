# -*- coding: utf-8 -*-
r"""查：**本地归档** strict-freeze run 的 `n_trainable_params`（确认口径）（2026-10-09）。

## 为什么要

云端结果是 rank 8（`text_only` 98,304 / `both` 245,760），
而我的驱动传的是 `--rank 4`（应为 49,152 / 122,880）。
**若本地归档也是 98,304/245,760，则"rank 4"这一说法在归档里本就不成立**，
问题就在我的理解而非云端脚本。

    python tools\_p64_check_rank_parity.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "rank_parity.json"


def main() -> int:
    apply = "--apply" in sys.argv
    rows = {}
    for label, pat in (
        ("b32_r4(b32_r4)", "outputs/strict_freeze_b32_r4/*/seed*/results.json"),
        ("b16_r4", "outputs/strict_freeze_b16/r4/*/seed*/results.json"),
        ("oclip_r4", "outputs/strict_freeze_oclip/r4/*/seed*/results.json"),
        ("b32_r8(归档)", "outputs/strict_freeze/*/seed*/results.json"),
        ("b16(归档)", "outputs/strict_freeze_b16/*/seed*/results.json"),
        ("oclip(归档)", "outputs/strict_freeze_oclip/*/seed*/results.json"),
    ):
        print(f"\n=== {label} ===")
        print(f"  {'arm':<13}{'seed':<8}{'n_trainable':>14}{'CGΔ':>11}")
        for f in sorted(glob.glob(str(REPO / pat))):
            d = json.loads(io.open(f, encoding="utf-8").read())
            arm = Path(f).parent.parent.name
            seed = Path(f).parent.name
            n = d.get("n_trainable_params")
            cg0 = d.get("initial_gap", {}).get("centroid_gap")
            cg1 = d.get("final_gap", {}).get("centroid_gap")
            dlt = (cg1 - cg0) if (cg0 is not None and cg1 is not None) else None
            rows.setdefault(label, {})[f"{arm}/{seed}"] = {
                "n_trainable_params": n, "cg_delta": dlt}
            print(f"  {arm:<13}{seed:<8}{str(n):>14}"
                  f"{(('%+.4f' % dlt) if dlt is not None else '?'):>11}")

    print("\n=== 结论 ===")
    print("  若本地 strict_freeze_b32_r4 的 n_trainable 也是 98,304/245,760，")
    print("  则该目录名里的 'r4' **与实际 rank 不符**（目录名误导，非云端脚本问题）。")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rows, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
