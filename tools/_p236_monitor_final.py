# -*- coding: utf-8 -*-
r"""监控决策实验的**最终分析**：τ 早停 vs val_loss 早停 vs top-1 早停（2026-10-12）。

## 数据

`outputs/a1_class_aligned/lr0.0/seed{42,123,456}/eval_epoch{1..10}.json`
（由 `tools/_p235_monitor_queue.py` 生成；每个文件含
`tau_final` / `top1_50k` / `val_loss`）。

**λ_reg=0 → 纯 LoRA**（论文协议，非 class-alignment）。

## 决策准则（逐 epoch，只看**训练期可见**的量）

| 准则 | 依据 | 是否需要标签 |
|---|---|---|
| **τ 最大** | `tau_final` | ❌ 不需要（只用冻结 top-k 集） |
| **val_loss 最小** | `val_loss` | ❌ 不需要 |
| 固定 epoch N | 无信号 | ❌ |
| **top-1 最大** | `top1_50k` | ✅ **需要**（oracle 上界） |
| 训到 epoch 10 | 无 | ❌ |

**判据**：选中检查点的 top-1（越高越好）。
**若 τ 不优于 val_loss / 固定 epoch → "监控器"主张不成立（如实报告）。**

    python tools\_p236_monitor_final.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "outputs" / "a1_class_aligned"
OUT = REPO / "outputs" / "analysis" / "a1_monitor_final.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    runs = defaultdict(dict)
    for f in sorted(glob.glob(str(ROOT / "lr0.0" / "seed*" / "eval_epoch*.json"))):
        p = Path(f)
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        seed = p.parent.name
        ep = d.get("eval_epoch")
        runs[seed][ep] = {
            "tau": d.get("tau_final"), "top1": d.get("top1_50k"),
            "val_loss": d.get("val_loss"), "source": str(p.relative_to(REPO)),
        }
    complete = {s: v for s, v in runs.items() if len(v) == 10}
    print("=" * 92)
    print("① 数据完整度（lr0.0 = 纯 LoRA 协议）")
    print("=" * 92)
    for s in sorted(runs):
        eps = sorted(runs[s])
        print(f"  {s:<10} {len(eps)}/10 epoch  {eps}")
    if not complete:
        print("\n  🔴 无完整 run（需 10 个 epoch）——等队列跑完再运行")
        return 1
    print(f"\n  完整 run: {sorted(complete)}")

    print()
    print("=" * 92)
    print("② 逐 run 的逐 epoch 三元组")
    print("=" * 92)
    for s in sorted(complete):
        print(f"\n  ── {s} ──")
        print(f"    {'ep':>3} {'τ':>9} {'top1_50k':>10} {'val_loss':>10}")
        for ep in sorted(complete[s]):
            r = complete[s][ep]
            print(f"    {ep:>3} {r['tau']:>9.4f} {r['top1']:>10.2f} {r['val_loss']:>10.4f}")

    # 准则
    def pick(s, crit):
        v = complete[s]
        if crit == "tau_max":
            return max(v, key=lambda e: v[e]["tau"])
        if crit == "vloss_min":
            return min(v, key=lambda e: v[e]["val_loss"])
        if crit == "top1_max":
            return max(v, key=lambda e: v[e]["top1"])
        if crit.startswith("fixed"):
            k = int(crit.split(":")[1])
            return k if k in v else None
        if crit == "ep10":
            return max(v)
        return None

    CRITS = [("tau_max", "★ τ 最大（本方法）"), ("vloss_min", "val_loss 最小"),
             ("fixed:1", "固定 epoch 1"), ("fixed:2", "固定 epoch 2"),
             ("fixed:3", "固定 epoch 3"), ("top1_max", "top1 最大（oracle）"),
             ("ep10", "训到 epoch 10")]

    print()
    print("=" * 92)
    print("③ 各准则选中的 epoch 与 top-1（逐 run）")
    print("=" * 92)
    print(f"  {'run':<10}" + "".join(f"{c[0][:9]:>11}" for c in CRITS))
    sel = {c[0]: {} for c in CRITS}
    for s in sorted(complete):
        line = f"  {s:<10}"
        for cid, _ in CRITS:
            ep = pick(s, cid)
            t1 = complete[s][ep]["top1"] if ep else None
            sel[cid][s] = {"epoch": ep, "top1": t1}
            line += f"{str(ep) + ':' + (f'{t1:.2f}' if t1 else '-'):>11}"
        print(line)

    print()
    print("=" * 92)
    print("④ 汇总：平均 top-1 / 平均停止 epoch / 相对 oracle 的损失")
    print("=" * 92)
    oracle = {s: max(complete[s][e]["top1"] for e in complete[s]) for s in complete}
    orc_mean = st.mean(oracle.values())
    print(f"  oracle 平均 top-1 = {orc_mean:.2f}（每个 run 各自最优）")
    print()
    print(f"  {'准则':<26}{'平均top1':>11}{'损失':>9}{'平均停ep':>10}{'省ep':>7}")
    summary = {}
    for cid, label in CRITS:
        t1s = [sel[cid][s]["top1"] for s in sel[cid] if sel[cid][s]["top1"] is not None]
        eps = [sel[cid][s]["epoch"] for s in sel[cid] if sel[cid][s]["epoch"]]
        loss = st.mean([oracle[s] - sel[cid][s]["top1"] for s in sel[cid]
                        if sel[cid][s]["top1"] is not None])
        summary[cid] = {"label": label, "mean_top1": round(st.mean(t1s), 4),
                        "mean_loss": round(loss, 4),
                        "mean_stop_epoch": round(st.mean(eps), 2),
                        "epochs_saved": round(10 - st.mean(eps), 2)}
        print(f"  {label:<26}{st.mean(t1s):>11.2f}{loss:>+9.3f}"
              f"{st.mean(eps):>10.2f}{10 - st.mean(eps):>7.2f}")

    print()
    print("=" * 92)
    print("⑤ 判定")
    print("=" * 92)
    tau_loss = summary["tau_max"]["mean_loss"]
    vl_loss = summary["vloss_min"]["mean_loss"]
    best_fixed = min(("fixed:1", "fixed:2", "fixed:3"),
                     key=lambda c: summary[c]["mean_loss"])
    print(f"  τ 最大：损失 {tau_loss:+.3f}，平均停在 epoch "
          f"{summary['tau_max']['mean_stop_epoch']:.1f}")
    print(f"  val_loss 最小：损失 {vl_loss:+.3f}，平均停在 epoch "
          f"{summary['vloss_min']['mean_stop_epoch']:.1f}")
    print(f"  最好的固定基线（{summary[best_fixed]['label']}）：损失 "
          f"{summary[best_fixed]['mean_loss']:+.3f}")
    print()
    if vl_loss < tau_loss - 0.1:
        print(f"  🔴 **val_loss 早停优于 τ**（{vl_loss:+.3f} vs {tau_loss:+.3f}）"
              f"→ τ 作为停止准则不占优")
    elif tau_loss < vl_loss - 0.1:
        print(f"  ✅ **τ 早停优于 val_loss**（{tau_loss:+.3f} vs {vl_loss:+.3f}）")
    else:
        print(f"  ⚠️ τ 与 val_loss 无实质差别（{tau_loss:+.3f} vs {vl_loss:+.3f}）")
    if tau_loss < summary[best_fixed]["mean_loss"] - 0.1:
        print(f"  ✅ τ 优于固定 epoch 基线")
    else:
        print(f"  🔴 τ 不优于固定 epoch 基线（{tau_loss:+.3f} vs "
              f"{summary[best_fixed]['mean_loss']:+.3f}）→ 监控器主张不成立")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"source": "outputs/a1_class_aligned/lr0.0/seed*/eval_epoch*.json",
             "runs": {s: {str(e): v for e, v in complete[s].items()} for s in complete},
             "oracle_mean_top1": round(orc_mean, 4),
             "selected": sel, "summary": summary,
             "verdict": ("tau_better" if tau_loss < vl_loss - 0.1 else
                         ("vloss_better" if vl_loss < tau_loss - 0.1 else "no_difference")),
             "tau_beats_fixed": tau_loss < summary[best_fixed]["mean_loss"] - 0.1},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
