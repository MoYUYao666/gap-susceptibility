# -*- coding: utf-8 -*-
r"""修正两处与 ODE 拟合优度有关的问题（2026-10-02）。

## 问题一：我的验证脚本查错了数据源

`tools/_pa_verify_core_claims.py` 按键名 `R2/r2/R^2` 全仓搜索，报"median R² 0.9718 ✅"。
但那 13 处记录**全部来自 `outputs/llava_*`（解码器实验）**，与正文的主张
（"across all tested LoRA configurations"）**无关**。

CLIP 侧 ODE 拟合的 R² 存在**另一个键名**下：`outputs/theory/**/beta_results.json`
→ `exponential_fit.r_squared`。实测（`tools/_pa_clip_ode_r2.py`）：

| 配置 | n | mean | min |
|---|---|---|---|
| `beta_pilot_both_r8` | 3 | 0.9880 | 0.9838 |
| `beta_pilot_text_r8` | 3 | 0.9829 | 0.9777 |
| **`beta_pilot_full_ft`** | 3 | **0.9223** | **0.8629** |
| 全部 9 条 | 9 | **0.9644** | 0.8629 |
| **仅 LoRA（6 条）** | 6 | **0.9855** | 0.9777 |

→ 正文写"across all tested **LoRA** configurations"时，**应按 LoRA 子集报 0.9855**；
把 full_ft 混进去才是 0.9644（勉强 >0.96）。**口径要与措辞一致**。

## 问题二：验证脚本必须改用正确来源

把 `_pa_verify_core_claims.py` 的 R² 部分改为读 `beta_results.json` 的 `r_squared`，
并**区分 LoRA 与 full_ft**，避免再用无关来源"验证"。

    python tools\_pa_fix_r2_source.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VERIFY = REPO / "tools" / "_pa_verify_core_claims.py"
SEC = REPO / "paper合" / "sections"

NEW_R2_BLOCK = '''    print("\\n=== ② CLIP 侧 ODE 拟合优度（R² > 0.96 主张）===")
    # 注意来源：CLIP 的 ODE 拟合 R² 存在 outputs/theory/**/beta_results.json 的
    # exponential_fit.r_squared 键下。**不要**用全仓 R2/r2 搜索——那会抓到 llava（解码器）
    # 的无关数字，本脚本先前正是这样误报过一次。
    fits: list[tuple[str, float]] = []
    for p in sorted((REPO / "outputs").rglob("beta_results.json")):
        try:
            d = json.loads(io.open(p, encoding="utf-8", errors="ignore").read())
        except Exception:
            continue
        r2 = (d.get("exponential_fit") or {}).get("r_squared")
        if isinstance(r2, (int, float)):
            fits.append(((d.get("config") or {}).get("name", "?"), float(r2)))
    if not fits:
        print("  ❌ 未找到 beta_results.json 的 r_squared")
        return 1
    lo = [v for n, v in fits if "full_ft" not in n]
    alle = [v for _, v in fits]
    print("  全部 %d 条: mean %.4f ｜ median %.4f ｜ min %.4f"
          % (len(alle), st.mean(alle), st.median(alle), min(alle)))
    print("  仅 LoRA %d 条: mean %.4f ｜ median %.4f ｜ min %.4f"
          % (len(lo), st.mean(lo), st.median(lo), min(lo)))
    print("  → 'mean R² > 0.96 across all tested LoRA configurations': %s"
          % ("✅" if st.mean(lo) > 0.96 else "❌"))
    print("  → 若误把 full_ft 计入: mean %.4f（%s）"
          % (st.mean(alle), "仍 >0.96 但勉强" if st.mean(alle) > 0.96 else "不足 0.96"))
    return 0
'''


def lo_ft_stats() -> tuple[float, float, float, int]:
    """从 beta_results.json 取 LoRA 子集与 full_ft 的 R² 均值/最小/计数（不硬编码）。"""
    import json
    lo: list[float] = []
    ft: list[float] = []
    for p in (REPO / "outputs").rglob("beta_results.json"):
        try:
            d = json.loads(io.open(p, encoding="utf-8", errors="ignore").read())
        except Exception:
            continue
        r2 = (d.get("exponential_fit") or {}).get("r_squared")
        if not isinstance(r2, (int, float)):
            continue
        nm = (d.get("config") or {}).get("name", "")
        (ft if "full_ft" in nm else lo).append(float(r2))
    return (sum(lo) / len(lo), min(lo), sum(ft) / len(ft), len(lo))


def main() -> int:
    apply = "--apply" in sys.argv
    n = 0
    lo_mean, lo_min, ft_mean, lo_n = lo_ft_stats()
    print(f"  实测 LoRA 子集: n={lo_n} mean={lo_mean:.4f} min={lo_min:.4f} ｜ full_ft mean={ft_mean:.4f}")

    # ① 改验证脚本
    t = io.open(VERIFY, encoding="utf-8").read()
    i = t.find('    print("\\n=== ② ODE 拟合优度')
    if i < 0:
        i = t.find('=== ②')
    if i > 0:
        t2 = t[:i] + NEW_R2_BLOCK
        print("  ✅ 验证脚本：R² 段落改为读 beta_results.json")
        if apply:
            io.open(VERIFY, "w", encoding="utf-8", newline="").write(t2)
        n += 1
    else:
        print("  ⚠ 验证脚本：未定位到 R² 段落")

    # ② 正文口径与措辞对齐（数值由实测生成）
    new_text = ("mean $R^2 = %.3f$ over the LoRA configurations (the full-fine-tuning pilot is lower, at "
                "$%.3f$, and is reported separately below)" % (lo_mean, ft_mean))
    edits = [("validation.tex", "mean $R^2 > 0.96$", new_text)]
    for fname, old, new in edits:
        p = SEC / fname
        s = io.open(p, encoding="utf-8").read()
        c = s.count(old)
        if c >= 1:
            print(f"  ✅ {fname}: 命中 {c} 处旧表述")
            if apply:
                io.open(p, "w", encoding="utf-8", newline="").write(s.replace(old, new))
            n += 1
        else:
            print(f"  ⚠ {fname}: 未命中")

    print(f"\n{n} 项{'已改' if apply else '可改'}")
    if apply:
        s = io.open(VERIFY, encoding="utf-8").read()
        assert "beta_results.json" in s, "断言失败：验证脚本未改来源"
        print("  ✅ 断言通过")
    else:
        print("（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
