# -*- coding: utf-8 -*-
r"""通用 COCO 补跑驱动（多臂、多秩、5 seed、batch 128）（2026-10-11）。

## 为什么再写一个

`_p173` 只支持 `text_only` 单臂。但**严格冻结的对照**里 `both` 臂也需要补 seed：
- `coco_sweep/r16/both`（现 3 seed）、`coco_sweep/r64/both`（现 3 seed）
- `coco_sweep/r4/both`（现 3 seed）

**目标**：论文"数据集翻转"用到的秩，**两臂都 5 seed**。

## 判据（元数据为准）

目标 `results.json` 存在**且 `batch_size == 128`** 且 **seed 已够** → 跳过。
若需重跑，**先把旧文件改名**（`.batchN.bak`）——脚本"存在即跳过"，不挪走就不会真跑。

    python tools\_p183_coco_general.py [--list] [--apply]
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
LOG = REPO / "outputs" / "_coco_general.log"
SEEDS = ("42", "123", "456", "789", "1011")
RETRY = 2

# (组, 秩, 臂)
JOBS = [
    ("outputs/coco_sweep_text_only", "4", "text_only"),
    ("outputs/coco_sweep_text_only", "16", "text_only"),
    ("outputs/coco_sweep_text_only", "64", "text_only"),
    ("outputs/coco_sweep", "4", "both"),
    ("outputs/coco_sweep", "16", "both"),
    ("outputs/coco_sweep", "64", "both"),
]


def log(m: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {m}"
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def path_of(outdir: str, rank: str, arm: str, seed: str) -> Path:
    return REPO / outdir / f"r{rank}" / arm / f"seed{seed}" / "results.json"


def status(outdir: str, rank: str, arm: str, seed: str) -> str:
    f = path_of(outdir, rank, arm, seed)
    if not f.exists():
        return "new"
    try:
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
    except Exception:
        return "bad"
    return "ok" if d.get("batch_size") == 128 else "rerun"


def stash(outdir: str, rank: str, arm: str, seed: str) -> str:
    f = path_of(outdir, rank, arm, seed)
    if not f.exists():
        return "（无旧文件）"
    try:
        b = json.loads(io.open(f, encoding="utf-8", errors="replace").read()).get(
            "batch_size", "?")
    except Exception:
        b = "?"
    if b == 128:
        return "（已是 128）"
    bak = f.with_suffix(f".batch{b}.bak")
    if bak.exists():
        bak.unlink()
    f.rename(bak)
    return f"旧(batch={b})→{bak.name}"


def run_one(outdir: str, rank: str, arm: str, seed: str) -> bool:
    cmd = [PY, "experiments/strict_freeze_control.py",
           "--dataset", "coco", "--data-dir", ".",
           "--out-dir", f"{outdir}/r{rank}", "--name", f"coco_{arm}_r{rank}_",
           "--tags", arm, "--seeds", seed,
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
            log(f"   ✅ {outdir.split('/')[-1]}/r{rank}/{arm}/seed{seed}（{dt:.0f}s）")
            return True
        err = next((l.strip() for l in (r.stderr or "").splitlines()
                    if "Error" in l or "error" in l), "")
        log(f"      ✗ attempt {attempt} rc={r.returncode} {err[:100]}")
        time.sleep(20)
    log(f"   ❌ {outdir.split('/')[-1]}/r{rank}/{arm}/seed{seed} 三次均失败")
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    todo = []
    for outdir, rank, arm in JOBS:
        for seed in SEEDS:
            st = status(outdir, rank, arm, seed)
            if st != "ok":
                todo.append((st, outdir, rank, arm, seed))

    from collections import Counter
    print(f"=== COCO 通用队列：{len(todo)} run ===")
    print(f"  新建 {sum(1 for t in todo if t[0]=='new')} ｜ "
          f"重跑 {sum(1 for t in todo if t[0]=='rerun')}")
    for k, v in sorted(Counter(f"{t[1].split('/')[-1]}/r{t[2]}/{t[3]}" for t in todo).items()):
        print(f"  {k:<38} {v} run")
    if a.list:
        for t in todo:
            print(f"   [{t[0]:<5}] {t[1].split('/')[-1]:<22} r{t[2]:<4} {t[3]:<12} seed{t[4]}")
        return 0
    if not a.apply:
        print("  （预演）")
        return 0

    log("=" * 72)
    log(f"COCO 通用补跑启动：{len(todo)} run（batch 128）")
    ok = fail = 0
    for st, outdir, rank, arm, seed in todo:
        log(f"▶ [{st}] {outdir.split('/')[-1]}/r{rank}/{arm}/seed{seed}")
        note = stash(outdir, rank, arm, seed)
        if note not in ("（无旧文件）", "（已是 128）"):
            log(f"   {note}")
        if run_one(outdir, rank, arm, seed):
            ok += 1
        else:
            fail += 1
    log(f"完成：成功 {ok} ｜ 失败 {fail}")
    log("=" * 72)

    for outdir, rank, arm in JOBS:
        n = sum(1 for s in SEEDS if status(outdir, rank, arm, s) == "ok")
        log(f"  {outdir.split('/')[-1]}/r{rank}/{arm}: {n}/5 seed 已达 batch 128")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
