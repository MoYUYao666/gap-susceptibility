# -*- coding: utf-8 -*-
r"""复核严格冻结 5-seed 结果与 ODE 的 R² 主张（论文两大主张的源数据核验）。

## 为什么单独成脚本

论文的核心因果主张现在落在**严格冻结对照**上（`outputs/analysis/strict_control_summary.json`），
而第二大主张是 ODE 的拟合优度（`R² > 0.96`）。两者都必须能逐 seed / 逐记录复算，
否则整改后的正文仍然只是"换了一套数字"，没有可复核性。

## 核验内容

1. **严格冻结 5 seeds**：`outputs/strict_freeze/{text_only,both,vision_only}/seed*/results.json`
   —— 逐 seed 计算 ΔCG = final − initial，报告均值 ± sd 与**方向一致性**；
2. **ODE R²**：全仓库收集 R² 字段，报告范围与中位数，核对"mean R² > 0.96"是否成立。

    python tools\_pa_verify_core_claims.py
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def delta_cg(p: Path) -> float | None:
    try:
        d = json.loads(io.open(p, encoding="utf-8", errors="ignore").read())
        return d["final_gap"]["centroid_gap"] - d["initial_gap"]["centroid_gap"]
    except Exception:
        return None


def main() -> int:
    print("=== ① 严格冻结 5-seed 复算（ΔCG = final − initial）===")
    per_cfg: dict[str, list[float]] = {}
    for k in ("text_only", "both", "vision_only"):
        ds = [x for x in (delta_cg(Path(p)) for p in sorted(glob.glob(
            str(REPO / "outputs" / "strict_freeze" / k / "seed*" / "results.json")))) if x is not None]
        if ds:
            per_cfg[k] = ds
            print("  %-12s n=%d  %s" % (k, len(ds), " ".join("%+.4f" % x for x in ds)))
            print("  %-12s 均值 %+.4f ± %.4f" % ("", st.mean(ds), st.stdev(ds) if len(ds) > 1 else 0.0))

    ok_dir = all(x < 0 for x in per_cfg.get("text_only", []))
    ok_order = (st.mean(per_cfg["text_only"]) < st.mean(per_cfg["both"]) < st.mean(per_cfg["vision_only"]))
    print("\n  方向一致性（text_only 全部为负）: %s" % ("✅" if ok_dir else "❌"))
    print("  排序 text_only < both < vision_only: %s" % ("✅" if ok_order else "❌"))

    print("\n=== ② CLIP 侧 ODE 拟合优度（R² > 0.96 主张）===")
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


if __name__ == "__main__":
    raise SystemExit(main())
