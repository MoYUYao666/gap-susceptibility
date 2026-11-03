# -*- coding: utf-8 -*-
r"""COCO text_only 重跑（batch 128，5 seed，含 CUDA 错误重试）（2026-10-11）。

## 背景

`tools/_p169` 的 COCO 部分**全部失败/错位**，根因是 `--out-dir` 传了基础路径：
- `r2`/`r32`/`r64` → 被"必须含 rank 标识"的校验**拒绝**（rc=1）→ 16 个失败；
- `r8` → 通过但**写进基础目录**（`OUT_DIR/text_only/`）→ 4 个错位（已改名 `.MISPLACED_*`）。

**修法**（`tools/_p172`）：`--out-dir outputs/coco_sweep_text_only/r{rank}`。

## 本驱动

**20 run** = r2/r8/r32/r64 × seed 42/123/456/789/1011，**batch 128**。
**逐 run 重试 2 次**（队列里 `r8/seed123` 曾遇 `CUDA error: unknown error`，队列无重试机制）。

**判据（以元数据为准）**：目标文件存在**且 `batch_size == 128`** → 跳过。

    python tools\_p173_coco_fix.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = sys.executable
LOG = REPO / "outputs" / "_coco_fix.log"
BASE = "outputs/coco_sweep_text_only"
RANKS = ("2", "4", "8", "16", "32", "64")
SEEDS = ("42", "123", "456", "789", "1011")
RETRY = 2


def log(m: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {m}"
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def status(rank: str, seed: str) -> str:
    f = REPO / BASE / f"r{rank}" / "text_only" / f"seed{seed}" / "results.json"
    if not f.exists():
        return "new"
    try:
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
    except Exception:
        return "bad"
    return "ok" if d.get("batch_size") == 128 else "rerun"


def stash_old(rank: str, seed: str) -> str:
    """把旧结果改名备份（脚本按文件存在性跳过，不挪走就不会真跑）。"""
    f = REPO / BASE / f"r{rank}" / "text_only" / f"seed{seed}" / "results.json"
    if not f.exists():
        return "（无旧文件）"
    try:
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        b = d.get("batch_size", "?")
    except Exception:
        b = "?"
    if b == 128:
        return f"（已是 128，不动）"
    bak = f.with_suffix(f".batch{b}.bak")
    if bak.exists():
        bak.unlink()
    f.rename(bak)
    return f"旧文件(batch={b})→{bak.name}"


def run_one(rank: str, seed: str) -> bool:
    outdir = f"{BASE}/r{rank}"
    cmd = [PY, "experiments/strict_freeze_control.py",
           "--dataset", "coco", "--data-dir", ".",
           "--out-dir", outdir, "--name", f"coco_to_r{rank}_",
           "--tags", "text_only", "--seeds", seed,
           "--epochs", "10", "--max-samples", "5000", "--batch-size", "128",
           "--skip-frozen", "--rank", rank, "--alpha-mult", "2"]
    for attempt in range(1, RETRY + 2):
        t0 = time.time()
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=4 * 3600, cwd=str(REPO))
        except subprocess.TimeoutExpired:
            log(f"      ⚠ 超时 attempt {attempt}")
            continue
        dt = time.time() - t0
        if r.returncode == 0:
            log(f"   ✅ r{rank}/seed{seed}（{dt:.0f}s）")
            return True
        err = ""
        for ln in (r.stderr or "").splitlines():
            if "Error" in ln or "error" in ln:
                err = ln.strip()[:110]
                break
        log(f"      ✗ attempt {attempt} rc={r.returncode} {err}")
        time.sleep(20)
    log(f"   ❌ r{rank}/seed{seed} 三次均失败")
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    todo = [(rk, s) for rk in RANKS for s in SEEDS if status(rk, s) != "ok"]
    print(f"=== COCO 待跑：{len(todo)} run（batch 128，逐 run 重试 {RETRY}）===")
    from collections import Counter
    for k, v in sorted(Counter(rk for rk, _ in todo).items(), key=lambda x: int(x[0])):
        print(f"  r{k:<3} {v} run")
    if not a.apply:
        print("  （预演）")
        return 0

    log("=" * 66)
    log(f"COCO text_only 重跑启动：{len(todo)} run（batch 128）")
    ok = fail = 0
    for rk, s in todo:
        log(f"▶ r{rk}/seed{s}")
        note = stash_old(rk, s)
        if note != "（已是 128，不动）":
            log(f"   {note}")
        if run_one(rk, s):
            ok += 1
        else:
            fail += 1
    log(f"完成：成功 {ok} ｜ 失败 {fail}")
    log("=" * 66)

    n128 = 0
    for rk in RANKS:
        for s in SEEDS:
            f = REPO / BASE / f"r{rk}" / "text_only" / f"seed{s}" / "results.json"
            if f.exists():
                try:
                    d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
                    if d.get("batch_size") == 128:
                        n128 += 1
                except Exception:
                    pass
    log(f"现共 {n128}/20 个 batch=128 的结果")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
