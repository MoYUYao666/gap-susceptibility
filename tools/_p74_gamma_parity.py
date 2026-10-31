# -*- coding: utf-8 -*-
r"""核对：云端 `Γ_m` 数值是否可信、与本地归档的 `Γ_m` 对照（2026-10-09）。

## 为什么

云端训练**失效**（`R@1=0.002`），但 `Γ_m` 是**单批前向 + 反传**的量，
**不依赖训练收敛** → 理论上仍可信。**但必须实测核对，不能凭"理论上"。**

## 对照基准

`outputs/theory/encoder_side/encoder_side.json`（本地归档的 `norm_g_vision`/`norm_g_text`）。

**判据**：
- 若云端的 `‖∇_tDG*‖`/`‖∇_vDG*‖` 与本地归档**同量级** → 云端 `Γ_m` 可用；
- 若差一个量级 → 云端的前向/反传也有问题 → **`Γ_m` 也不可用**。

    python tools\_p74_gamma_parity.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "gamma_parity.json"

# 云端 Γ_m（从驱动日志提取，2026-10-09）
CLOUD = {
    "text_only":   {"norm_grad_text": 26.0692, "cos_text": 0.9608, "Gamma_text": 25.0481,
                    "norm_grad_vision": 0.0, "cos_vision": None, "Gamma_vision": 0.0},
    "vision_only": {"norm_grad_vision": 5.2054, "cos_vision": 0.1918, "Gamma_vision": 0.9983,
                    "norm_grad_text": 0.0, "cos_text": None, "Gamma_text": 0.0},
    "both":        {"norm_grad_vision": 5.2988, "cos_vision": 0.1915, "Gamma_vision": 1.0148,
                    "norm_grad_text": 26.5986, "cos_text": 0.9617, "Gamma_text": 25.5793},
}


def main() -> int:
    apply = "--apply" in sys.argv
    es = REPO / "outputs/theory/encoder_side/encoder_side.json"
    if not es.exists():
        print(f"  ❌ 缺 {es.relative_to(REPO)}")
        return 1
    local = json.loads(io.open(es, encoding="utf-8").read())["summary"]

    print("=== 云端 vs 本地归档：∇DG* 的范数 ===")
    print(f"  {'臂':<13}{'量':<18}{'本地':>12}{'云端':>12}{'比值':>9}  判定")
    rows = []
    for arm in ("text_only", "vision_only", "both"):
        L, C = local.get(arm, {}), CLOUD.get(arm, {})
        for key, lk, ck in (("‖∇_vDG*‖", "norm_g_vision", "norm_grad_vision"),
                            ("‖∇_tDG*‖", "norm_g_text", "norm_grad_text")):
            lv, cv = L.get(lk), C.get(ck)
            if lv is None or cv is None:
                continue
            if lv == 0.0 and cv == 0.0:
                print(f"  {arm:<13}{key:<18}{lv:>12.4f}{cv:>12.4f}{'—':>9}  ✅ 都为零")
                rows.append({"arm": arm, "qty": key, "local": lv, "cloud": cv,
                             "ratio": None})
                continue
            ratio = (cv / lv) if lv else float("inf")
            ok = 0.5 <= ratio <= 2.0
            print(f"  {arm:<13}{key:<18}{lv:>12.4f}{cv:>12.4f}{ratio:>9.4f}  "
                  f"{'✅ 同量级' if ok else '❌ 差量级'}")
            rows.append({"arm": arm, "qty": key, "local": lv, "cloud": cv,
                         "ratio": ratio, "same_order": ok})

    print("\n=== 云端 Γ_m（完整量，含 cos）===")
    for arm, d in CLOUD.items():
        gv = d.get("Gamma_vision"); gt = d.get("Gamma_text")
        print(f"  {arm:<13} Γ_v={gv:>8.4f} ｜ Γ_t={gt:>8.4f}")

    print("\n=== 判读 ===")
    ratios = [r["ratio"] for r in rows if r.get("ratio")]
    if ratios and all(0.5 <= x <= 2.0 for x in ratios):
        print("  ✅ 云端 ‖∇DG*‖ 与本地归档**同量级** →")
        print("     `Γ_m` 是**单批前向+反传**量，不依赖训练收敛 → **云端 Γ_m 可用**")
        usable = True
    else:
        print("  ❌ 云端 ‖∇DG*‖ 与本地差量级 → **Γ_m 也不可用**")
        usable = False

    print("\n=== 但要标注的限制 ===")
    print("  1. 云端 `Γ_m` 为**7 批平均**（本地 `_p58` 为 8 批），机制相同；")
    print("  2. 云端跑在**不同的环境**（torch 2.12 vs 2.9），绝对值可能有系统偏移；")
    print("  3. **不得**用云端 `Γ_m` 去替换本地归档的同名量——只能作为**独立一组**报告。")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps({
            "cloud_gamma": CLOUD, "comparison": rows, "usable": usable,
            "caveats": ["cloud averaged 7 batches vs local 8",
                        "different torch version",
                        "report as an independent set, do not merge"],
        }, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
