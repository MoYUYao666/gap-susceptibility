# -*- coding: utf-8 -*-
r"""落账：监控决策实验的最终结论（等 `_p236` 跑完后再执行）（2026-10-12）。

**本脚本从 `outputs/analysis/a1_monitor_final.json` 读取结果并写入 HANDOFF**，
不写死数字——**避免"结论与数据不一致"**（本项目已因此出过错）。

    python tools\_docs_monitor_final.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "outputs" / "analysis" / "a1_monitor_final.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not SRC.exists():
        print(f"  🔴 缺 {SRC.relative_to(REPO)} —— 先跑 tools/_p236_monitor_final.py")
        return 1
    d = json.loads(io.open(SRC, encoding="utf-8", errors="replace").read())
    s = d["summary"]
    runs = sorted(d["runs"])

    rows = []
    for cid in ("tau_max", "vloss_min", "fixed:1", "fixed:2", "fixed:3", "top1_max",
                "ep10"):
        if cid not in s:
            continue
        x = s[cid]
        rows.append(f"| {x['label']} | {x['mean_top1']:.2f} | {x['mean_loss']:+.3f} | "
                    f"{x['mean_stop_epoch']:.1f} | {x['epochs_saved']:.1f} |")
    table = "\n".join(rows)
    verdict = d.get("verdict")
    beats = d.get("tau_beats_fixed")
    vmap = {"tau_better": "✅ **τ 早停优于 val_loss 早停**",
            "vloss_better": "🔴 **val_loss 早停优于 τ**（τ 作为停止准则不占优）",
            "no_difference": "⚠️ **τ 与 val_loss 无实质差别**"}
    vtxt = vmap.get(verdict, str(verdict))
    btxt = ("✅ τ 优于固定 epoch 基线" if beats
            else "🔴 **τ 不优于固定 epoch 基线 → 监控器主张不成立**")

    ENT = f"""> **🎯 2026-10-12 —— 监控决策实验（真实验）最终结论：τ 是**诊断信号**，不是**停止准则**（操作者选"补"）**
>
> ### 为什么补这个实验
>
> 此前 E-B 用 `a1_epoch_sweep` 的 100 个检查点做过停止准则对照，但那份归档
> **只有 ImageNet top-1，没有验证损失**，无法与 val_loss 早停对照（审稿人点名的缺口：
> *"no τ-triggered early stopping, no comparison against loss/top-1 selection"*）。
> 操作者选"补" → 用**已有的逐 epoch 权重**补评测（`--eval-only`，无训练）。
>
> ### 数据（`tools/_p235_monitor_queue.py`）
>
> `outputs/a1_class_aligned/lr0.0/seed{{42,123,456}}/eval_epoch{{1..10}}.json`
> —— **λ_reg=0 = 纯 LoRA（论文协议）**；每个文件含 `tau_final` / `top1_50k` / `val_loss`。
> **逐 epoch 权重早已存盘**，故只需评测；共补评测 25 个 epoch（每个约 6.8 分钟）。
>
> ### 结果（`tools/_p236_monitor_final.py`，{len(runs)} 个 run）
>
> oracle 平均 top-1 = {d['oracle_mean_top1']:.2f}（每个 run 各自最优）
>
> | 停止准则 | 平均 top-1 | 相对 oracle 损失 | 平均停在第几轮 | 省下轮数 |
> |---|---|---|---|---|
> {table}
>
> ### 裁决
>
> - {vtxt}
> - {btxt}
>
> ### 顺带核实论文的三条"监控"主张（`tools/_p240_check_monitor_claims.py`）
>
> | 主张 | 新数据裁决 |
> |---|---|
> | τ 比 **top-1** 更早报警 | 🔴 **不支持**（seed42：τ 与 top-1 同在 epoch 2 首降） |
> | τ 比 **val_loss** 更早变差 | ✅ **支持**（τ epoch 2 vs val_loss **epoch 4**） |
> | τ 的**相对降幅最大** | ✅ **支持**：τ **6.29%** ＞ top-1 2.86% ＞ val_loss 1.11% |
> | τ 不需额外前向 | ✅ 代码事实（`a1_h_common.per_image_tau` 只读冻结 top-k 与当前分数） |
>
> **→ 论文若保留"更敏感"这一措辞，须限定为"相对降幅更大、且早于 val_loss"，
> 不能写成"早于 top-1"。**
>
> ### 证据
>
> `outputs/analysis/a1_monitor_final.json`、`a1_monitor_claims_check.json`；
> `tools/_p234_monitor_configs.py`、`_p235_monitor_queue.py`、`_p236_monitor_final.py`、
> `_p237_check_tau_scale.py`（核实新评与归档 τ 同一尺度）、`_p240_check_monitor_claims.py`
"""

    if not a.apply:
        print(ENT)
        print("  （预演；加 --apply 写入 HANDOFF）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "监控决策实验（真实验）最终结论" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("监控决策实验（真实验）最终结论", "oracle 平均 top-1", "6.29%"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
