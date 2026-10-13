# -*- coding: utf-8 -*-
r"""补跑 COCO 的 `text_only` 缺口（让"数据集翻转"那张表两臂齐备）（2026-10-10）。

## 缺口（实测 `outputs/coco_sweep/`）

| 秩 | `both` | `text_only` |
|---|---|---|
| r1 | 3 ✅ | 3 ✅ |
| r2 | 3 ✅ | **1**（缺 2） |
| r4 | 3 ✅ | 3 ✅ |
| **r8** | 3 ✅ | **0** |
| r16 | 3 ✅ | 3 ✅ |
| **r32** | 3 ✅ | **0** |
| **r64** | 3 ✅ | **0** |

**共缺 8 个 run**（r2 的 2 个 + r8/r32/r64 各 3 个）。

## 口径（与旧 sweep 一致，除 batch）

`--dataset coco --data-dir .`｜rank 见上｜`--alpha-mult 2`｜`--seeds 42 123 456`｜
`--epochs 10 --max-samples 5000 --batch-size 64`（**128→64 为共享显存约束，已记录**）｜
`--tags text_only`｜`--skip-frozen`

**输出**：`outputs/coco_sweep_text_only/rN/`（**不覆盖旧 sweep**）

    python tools\_p94_coco_textonly.py [--apply]
"""
from __future__ import annotations

import io
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = sys.executable
LOG = REPO / "outputs" / "_coco_textonly_driver.log"

JOBS = [
    ("r8", "8", ["42", "123", "456"]),
    ("r32", "32", ["42", "123", "456"]),
    ("r64", "64", ["42", "123", "456"]),
    ("r2", "2", ["123", "456"]),        # r2 已有 seed42
]


def log(m: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {m}"
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main() -> int:
    apply = "--apply" in sys.argv
    n = sum(len(s) for _, _, s in JOBS)
    print("=== 补跑 COCO text_only ===")
    for tag, r, seeds in JOBS:
        print(f"  {tag:<6} rank {r:<3} seeds {seeds}")
    print(f"  共 {n} run ｜ 输出 outputs/coco_sweep_text_only/")
    print(f"  日志 {LOG.relative_to(REPO)}")
    if not apply:
        print("  （预演；加 --apply 实跑）")
        return 0

    log("=" * 66)
    log(f"COCO text_only 补跑启动（{n} run）")
    ok = fail = skip = 0
    for tag, rank, seeds in JOBS:
        outdir = f"outputs/coco_sweep_text_only/{tag}"
        # 幂等：已有结果的 seed 跳过
        todo = []
        for s in seeds:
            if (REPO / outdir / "text_only" / f"seed{s}" / "results.json").exists():
                skip += 1
            else:
                todo.append(s)
        if not todo:
            log(f"· {tag}: 全部已有，跳过")
            continue
        cmd = [PY, "experiments/strict_freeze_control.py",
               "--dataset", "coco", "--data-dir", ".",
               "--model", "models/clip-vit-base-patch32",
               "--out-dir", outdir, "--name", f"coco_{tag}_",
               "--rank", rank, "--alpha-mult", "2", "--tags", "text_only",
               "--seeds", *todo, "--epochs", "10", "--max-samples", "5000",
               "--batch-size", "64", "--skip-frozen"]
        log(f"▶ {tag}（rank {rank}）seeds {todo}")
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               encoding="utf-8", errors="replace",
                               timeout=6 * 3600, cwd=str(REPO))
            if r.returncode == 0:
                ok += 1
                log("   ✅ rc=0")
            else:
                fail += 1
                err = next((l for l in (r.stderr or "").splitlines()
                            if "Error" in l), "")
                log(f"   ❌ rc={r.returncode} {err[:130]}")
        except subprocess.TimeoutExpired:
            fail += 1
            log("   ⚠ 超时（6 h）")
    log(f"完成：成功 {ok} ｜ 失败 {fail} ｜ 跳过已有 {skip}")
    log("=" * 66)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
