# -*- coding: utf-8 -*-
r"""分析 SigLIP 严格冻结对照的结果（text-only 5 seeds 已有；both 待补跑）。

## 对照关系

同一种子下、同协议（5000 样本 / 10 epochs / batch 64），**唯一差别是适配器注入位置**：

| 臂 | LoRA 注入 | 严格冻结后可训参数 | 视觉侧可训 |
|---|---|---|---|
| `s4_siglip_lora_text_only` | 仅文本 | **294,912** | **0**（视觉侧完全不动） |
| `s4_siglip_lora_both` | 文本 + 视觉 | **589,824** | 294,912（仅 LoRA，基座冻结） |

**这正是 CLIP 上无法做、而本实验能做到的对照**：legacy 约定下 text-only 反而训练 189M 参数
（含整个视觉塔），两者都动视觉侧，故不可解读为"位置选择"。

## 与归档 run 的关系

归档 `outputs/siglip/s4_siglip_lora_text_only`（legacy 约定，可训 189,276,674）给出 CGΔ = +0.0673；
本次严格冻结（可训 294,912）给出同种子的 CGΔ。**两者种子同为 42 时可直接比**，
差异即"是否冻结基座"的效应。

    python tools\_analyze_siglip_strict.py
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "outputs" / "siglip_strict"
ARCH = REPO / "outputs" / "siglip"


def load(p: Path) -> dict | None:
    try:
        return json.loads(io.open(p, encoding="utf-8", errors="ignore").read())
    except Exception:
        return None


def dcg(d: dict) -> float | None:
    ig, fg = d.get("initial_gap") or {}, d.get("final_gap") or {}
    if ig.get("centroid_gap") is None or fg.get("centroid_gap") is None:
        return None
    return fg["centroid_gap"] - ig["centroid_gap"]


def r1(d: dict) -> float | None:
    """优先用 final_task_metrics（与主脚本日志、归档 run 的口径一致）；
    注意 test_metrics 是另一个划分上的值，两者不同（实测 seed42: 0.434 vs 0.460），混用会误导。"""
    for k in ("final_task_metrics", "test_metrics"):
        v = (d.get(k) or {}).get("R@1")
        if v is not None:
            return float(v)
    return None


def main() -> int:
    print("=== 严格冻结结果（本次）===")
    summary: dict[str, list[tuple[int, float, float]]] = {}
    for arm in ("text_only", "both"):
        rows = []
        for p in sorted(glob.glob(str(ROOT / "seed*" / f"s4_siglip_lora_{arm}" / "results.json"))):
            d = load(Path(p))
            if not d:
                continue
            seed = int(Path(p).parts[-3].replace("seed", ""))
            v, r = dcg(d), r1(d)
            if v is not None:
                rows.append((seed, v, r if r is not None else float("nan")))
        summary[arm] = rows
        if rows:
            vs = [x[1] for x in rows]
            print("  %-10s n=%d  %s" % (arm, len(rows), "  ".join("s%d:%+.4f" % (s, v) for s, v, _ in rows)))
            print("  %-10s 均值 %+.4f ± %.4f ｜ R@1 %.3f" % ("", st.mean(vs), st.stdev(vs) if len(vs) > 1 else 0,
                                                            st.mean([x[2] for x in rows])))
        else:
            print("  %-10s 尚无结果" % arm)

    print("\n=== 与归档（legacy 约定）对比 ===")
    print("  ⚠ 注意：归档 run 的 `max_samples`/`epochs` **未记录在 results.json 中**，")
    print("     且其 gap_history 只有 4 个记录点，而本次为 7 个 → **两者训练预算不同，")
    print("     故归档值与本次值【不可直接相减】做效应估计**。")
    print("     本实验唯一干净的对照是 **同预算下的 text_only vs both**。")
    for arm in ("text_only", "both"):
        p = ARCH / f"s4_siglip_lora_{arm}" / "results.json"
        d = load(p)
        if d:
            print("  归档 %-10s CGΔ=%+.4f  n_trainable=%s（预算未知，仅供参考）"
                  % (arm, dcg(d) or float("nan"), d.get("n_trainable_params")))

    print("\n=== 判定：text-only 是否优于 both（严格冻结下）===")
    if summary["text_only"] and summary["both"]:
        a, b = st.mean([x[1] for x in summary["text_only"]]), st.mean([x[1] for x in summary["both"]])
        print("  text_only %+.4f  vs  both %+.4f  →  %s" % (
            a, b, "text-only 更小（优势成立）" if a < b else "text-only 不更小（优势不成立）"))
        pairs = {s: v for s, v, _ in summary["text_only"]}
        for s, v, _ in summary["both"]:
            if s in pairs:
                print("    seed %-5d text_only %+.4f  vs  both %+.4f  → %s"
                      % (s, pairs[s], v, "text-only 更小" if pairs[s] < v else "both 更小/持平"))
    else:
        print("  ⏳ both 臂结果未到齐，暂不判定")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
