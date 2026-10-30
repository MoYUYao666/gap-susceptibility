# -*- coding: utf-8 -*-
r"""task-9 自检 + 修复：**配置错标**（"静默覆盖类缺陷"第 ③ 类，最危险的一类）。

## 背景（Lead 2026-10-13 机器穷举 161 个脚本的结论）

全仓库只有**一处真 bug**：`tools/_p434_alloc_train.py` 的汇总归档曾写模块级常量
`"lr": LR`（恒 5e-5），而逐 run 归档与优化器用的是 `args.lr`。
⇒ 在 lr 扫描时会出现**自相矛盾**：文件名写 `lr0.001`、逐 run 写 `1e-3`、**汇总写 `5e-5`**。

**危害分级**（本文件作者与 Lead 共同确认）：

| 级别 | 现象 | 可见性 |
|---|---|---|
| **重写** | 聚合产物每次被重写，丢掉未参与本次调用的方案 | 可见（"少了一个"） |
| **覆盖** | 参数/tag 缺失导致多配置写同一文件 | 可见（"少了一个"） |
| **错标** | **所有产物都在、数字都真实，只是标签与内容不符** | **不可见** —— 任何下游推断都会错，且没有迹象提示去查 |

## 本脚本做两件事

1. **检测**：对每个 `<tag>/summary.json`，比较其顶层 `lr` 与其中 **逐 run** 的 `lr`；
2. **`--fix`**：若不一致，以**逐 run 的 `lr` 为准**（逐 run 是"只增不改"的权威来源）
   重写汇总归档的 `lr` 字段，并把**修复前后**的值与依据一并打印、追加到修复台账。

**为什么要以逐 run 为准**：逐 run 文件在训练时写一次、之后不再改；
而汇总文件会被后续调用重写。⇒ **逐 run 是权威来源**（同 `docs/P3_EXPERIMENTS.md §8.0`）。

    python tools\_p461_check_config_mislabel.py            # 只检测
    python tools\_p461_check_config_mislabel.py --fix      # 检测并修复
"""
from __future__ import annotations

import argparse
import datetime as _dt
import glob
import io
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNDIR = REPO / "outputs" / "analysis" / "p3_alloc_runs"
LEDGER = REPO / "outputs" / "analysis" / "p3_config_mislabel_fixes.json"

# 需检查的键（后续可扩展：任何"会改变结果且应落到归档"的配置）
KEYS = ("lr", "epochs", "batch", "tag")


def check_one(summary_path: Path) -> dict:
    """比较汇总归档的顶层键与其中逐 run 的对应键。返回检测记录。"""
    j = json.loads(io.open(summary_path, encoding="utf-8").read())
    runs = j.get("runs", {}) or {}
    rec = {"summary": str(summary_path.relative_to(REPO)), "mismatches": {}}
    for k in KEYS:
        top = j.get(k)
        vals = sorted({r.get(k) for r in runs.values() if r.get(k) is not None})
        if top is None or not vals:
            continue
        if top not in vals:
            rec["mismatches"][k] = {"summary_value": top, "run_values": vals}
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true", help="按逐 run 值修复汇总归档")
    args = ap.parse_args()

    files = sorted(glob.glob(str(RUNDIR / "*" / "summary.json"))) + \
        sorted(glob.glob(str(RUNDIR / "*" / "adalora_summary.json")))
    if not files:
        print(f"[SKIP] 未找到汇总归档于 {RUNDIR.relative_to(REPO)}")
        return 0

    print("=== 配置错标检测（汇总顶层 vs 逐 run）===")
    bad, checked = [], 0
    for f in files:
        r = check_one(Path(f))
        checked += 1
        tag = Path(f).parent.name
        if r["mismatches"]:
            bad.append(r)
            for k, v in r["mismatches"].items():
                print(f"  ❌ {tag:<22} {k}: 汇总={v['summary_value']!r} "
                      f"逐run={v['run_values']!r}")
        else:
            print(f"  OK {tag:<22} 无错标")
    print(f"\n检查 {checked} 个汇总归档，发现 {len(bad)} 个错标")

    if not bad:
        return 0
    if not args.fix:
        print("\n（加 --fix 按逐 run 值修复）")
        return 1

    # ---- 修复：以逐 run 值为准 ----
    fixes = []
    for r in bad:
        p = REPO / r["summary"]
        j = json.loads(io.open(p, encoding="utf-8").read())
        for k, v in r["mismatches"].items():
            vals = v["run_values"]
            new = vals[0] if len(vals) == 1 else None
            if new is None:
                print(f"  [warn] {p.name}:{k} 逐 run 值不唯一 {vals} —— 跳过，需人工处理")
                continue
            old = j.get(k)
            j[k] = new
            fixes.append({"file": r["summary"], "key": k, "old": old, "new": new,
                          "basis": "逐 run 归档（只增不改，权威来源）"})
            print(f"  ✅ {p.parent.name}:{k} {old!r} -> {new!r}")
        io.open(p, "w", encoding="utf-8", newline="").write(
            json.dumps(j, ensure_ascii=False, indent=1))

    # ---- 修复台账（可复核）----
    ledger = []
    if LEDGER.exists():
        try:
            ledger = json.loads(io.open(LEDGER, encoding="utf-8").read()).get("fixes", [])
        except Exception:  # noqa: BLE001
            ledger = []
    ledger += [dict(f, fixed_at_utc=_dt.datetime.utcnow().isoformat(timespec="seconds"))
               for f in fixes]
    io.open(LEDGER, "w", encoding="utf-8", newline="").write(
        json.dumps({"script": "tools/_p461_check_config_mislabel.py",
                    "rule": "汇总归档的配置键必须等于其中逐 run 的对应键；"
                            "不一致时以**逐 run**为准（只增不改）",
                    "hazard_ranking": ["错标（不可见，最危险）", "覆盖", "重写"],
                    "fixes": ledger}, ensure_ascii=False, indent=1))
    print(f"\n已修复 {len(fixes)} 处 → 台账 {LEDGER.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
