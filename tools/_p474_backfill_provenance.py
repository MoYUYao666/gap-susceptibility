# -*- coding: utf-8 -*-
r"""来源加固：给已归档的逐 run 明细**回填超参**，并把"来源/派生"关系写进归档。

## 为什么（2026-10-13 流程规则：不要把聚合产物当来源）

`_p461` / `_p464` 的归档里，训练超参**只写在顶层 `protocol`**，而 `protocol` 每次调用都会被**重写**。
⇒ 一旦将来用不同超参续跑，**旧 run 会被静默误标**——字段路径还在，值是错的。

本脚本做三件事（**只增不改**）：
1. 给每条 run 回填 `protocol` 里已有的训练超参（`lr/epochs/batch/dropout/...`）——**已存在的一律不覆盖**；
2. 写入顶层 `train_spec`（超参规范化快照）与 `source_of_truth` 说明；
3. **打印并断言**：run 数不变、**原有键值逐位不变**（对原文件每个已有键做值比对）。任何一处不符 → 退出 1，不写。

    python tools\_p474_backfill_provenance.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A = REPO / "outputs" / "analysis"

ARCHIVES = [
    "p3d_clip_ranksweep.json",
    "p3d_qwen_ranksweep.json",
    "p3d_qwen_ranksweep_mp50176.json",
]
# 顶层字段 → 回填进 rows[*]（只有行里没有的才加）
ROW_ARCHIVES = {
    "p3d_e0_vs_token_budget_train_sel_n16.json": ["device"],
    "p3d_e0_vs_token_budget_test_n4.json": ["device"],
    "p3d_e0_vs_token_budget_test_n2.json": ["device"],
}
# 从 protocol 回填到每条 run 的键（只有 run 里没有的才加）
BACKFILL_KEYS = ["lr", "epochs", "batch", "dropout", "dtype",
                 "lora_targets", "lora_alpha", "min_pixels", "max_pixels",
                 "E_eval_n", "E_train_n_cap"]
SRC_NOTE = ("runs[*] —— 只增不改的逐 run 明细，且每条 run 自带超参，是**来源**；"
            "顶层 protocol/train_spec 只是说明，派生聚合（*_summary.json）会被重写，"
            "**引用请指向 runs[*] 并带 split/n**。")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    bad = 0

    for name in ARCHIVES:
        p = A / name
        if not p.exists():
            print(f"  [skip] {name} 不存在")
            continue
        d = json.loads(io.open(p, encoding="utf-8").read())
        runs = d.get("runs", [])
        proto = d.get("protocol", {}) or {}
        before = json.dumps(runs, sort_keys=True, ensure_ascii=False)   # 原始快照

        added = {}
        for r in runs:
            for k in BACKFILL_KEYS:
                if k not in r and k in proto:
                    r[k] = proto[k]
                    added[k] = added.get(k, 0) + 1

        # ---- 断言 1：run 数不变 ----
        if len(runs) != len(json.loads(before)):
            print(f"  [FAIL] {name}: run 数变了")
            bad += 1
            continue
        # ---- 断言 2：原有键值逐位不变（只允许新增键）----
        old_runs = json.loads(before)
        drift = []
        for o, n in zip(old_runs, runs):
            for k, v in o.items():
                if n.get(k) != v:
                    drift.append((k, v, n.get(k)))
        if drift:
            print(f"  [FAIL] {name}: 原有键被改动 {drift[:3]}")
            bad += 1
            continue

        d["train_spec"] = proto
        d["source_of_truth"] = SRC_NOTE
        print(f"  [OK]   {name:<38} runs={len(runs):>3}  回填字段: "
              f"{ {k: v for k, v in sorted(added.items())} or '无需回填'}")
        if a.apply:
            io.open(p, "w", encoding="utf-8", newline="").write(
                json.dumps(d, ensure_ascii=False, indent=1))

    # ---- 第二类：`_p472` 的 rows[*] 回填 device（同样只增不改 + 断言）----
    for name, top_keys in ROW_ARCHIVES.items():
        p = A / name
        if not p.exists():
            print(f"  [skip] {name} 不存在")
            continue
        d = json.loads(io.open(p, encoding="utf-8").read())
        rows = d.get("rows", [])
        before = json.dumps(rows, sort_keys=True, ensure_ascii=False)
        added = {}
        for r in rows:
            for k in top_keys:
                if k not in r and k in d:
                    r[k] = d[k]
                    added[k] = added.get(k, 0) + 1
        old_rows = json.loads(before)
        drift = [(k, v, n.get(k)) for o, n in zip(old_rows, rows)
                 for k, v in o.items() if n.get(k) != v]
        if len(rows) != len(old_rows) or drift:
            print(f"  [FAIL] {name}: 行数变了或有键被改动 {drift[:3]}")
            bad += 1
            continue
        print(f"  [OK]   {name:<38} rows={len(rows):>3}  回填: "
              f"{ {k: v for k, v in sorted(added.items())} or '无需回填'}")
        if a.apply:
            io.open(p, "w", encoding="utf-8", newline="").write(
                json.dumps(d, ensure_ascii=False, indent=1))

    print(f"\n=== 断言全部通过（run 数不变、原有键值逐位不变）===" if not bad
          else f"\n=== {bad} 个文件有问题，未写入 ===")
    print("（预演；加 --apply 才写）" if not a.apply else "已写入。")
    return 1 if bad else 0

if __name__ == "__main__":
    raise SystemExit(main())
