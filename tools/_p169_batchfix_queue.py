# -*- coding: utf-8 -*-
r"""批次修正 + 5-seed 升级总队列（**统一 batch 128**）（2026-10-10 晚）。

## 操作者指令

> **"A，统一 128"**（先让 9-seed VLM 跑完，再修批次）

## 为什么必须重跑而不是统计补救

`tools/_p168` 查出 **19 个 run 用了 batch 64**，而同组其它 run 用 128 →
**臂间/seed 间比较被批次混淆**。**同一目录里混两套配置，均值不可用。**

## 队列（**串行**，单卡铁律）

| 阶段 | 内容 | run |
|---|---|---|
| **P1** | OCLIP r4 三臂：seed 123/456 重跑（128）+ 补 789/1011 | 6 + 6 |
| **P2** | B/16 r4 both/vision：seed 456 重跑（128）+ 三臂补 789/1011 | 2 + 6 |
| **P3** | COCO text_only：r2/r8/r32/r64 重跑（128）+ 各补 789/1011 | 11 + 8（r2 只需 2） |
| **P4** | B/32 r4 三臂：补 789/1011 | 6 |

**判"是否需要跑"的规则（幂等且**以元数据为准**）**：
- 目标 `results.json` **不存在** → 跑
- 存在但 `batch_size != 128` → **重跑**（覆盖）
- 存在且 `batch_size == 128` → 跳过

    python tools\_p169_batchfix_queue.py [--list] [--apply]
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
LOG = REPO / "outputs" / "_batchfix.log"
TARGET_BATCH = 128
SEEDS_5 = ["42", "123", "456", "789", "1011"]

# (标签, 输出目录, 模型, 数据集, rank, 额外参数, [(臂, [seeds])])
PLAN = [
    # ── P1: OCLIP r4（seed 42 已是 128）──
    ("oclip_r4", "outputs/strict_freeze_oclip/r4", "models/openclip", "flickr30k", "4", [],
     [("text_only", ["123", "456", "789", "1011"]),
      ("vision_only", ["123", "456", "789", "1011"]),
      ("both", ["123", "456", "789", "1011"])]),
    # ── P2: B/16 r4 ──
    ("b16_r4", "outputs/strict_freeze_b16/r4", "models/clip-vit-base-patch16", "flickr30k", "4", [],
     [("text_only", ["789", "1011"]),
      ("vision_only", ["456", "789", "1011"]),
      ("both", ["456", "789", "1011"])]),
    # ── P3: COCO text_only ──
    ("coco_to", "outputs/coco_sweep_text_only/r2", None, "coco", "2", ["--alpha-mult", "2"],
     [("text_only", ["42", "123", "456", "789", "1011"])]),
    ("coco_to", "outputs/coco_sweep_text_only/r8", None, "coco", "8", ["--alpha-mult", "2"],
     [("text_only", ["42", "123", "456", "789", "1011"])]),
    ("coco_to", "outputs/coco_sweep_text_only/r32", None, "coco", "32", ["--alpha-mult", "2"],
     [("text_only", ["42", "123", "456", "789", "1011"])]),
    ("coco_to", "outputs/coco_sweep_text_only/r64", None, "coco", "64", ["--alpha-mult", "2"],
     [("text_only", ["42", "123", "456", "789", "1011"])]),
    # ── P4: B/32 r4（全部已是 128，只补 seed）──
    ("b32_r4", "outputs/strict_freeze_b32_r4", "models/clip-vit-base-patch32", "flickr30k", "4", [],
     [("text_only", ["789", "1011"]), ("vision_only", ["789", "1011"]),
      ("both", ["789", "1011"])]),
]


def log(m: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {m}"
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def need_run(outdir: str, arm: str, seed: str) -> str:
    """返回 'skip' / 'new' / 'rerun'。"""
    f = REPO / outdir / arm / f"seed{seed}" / "results.json"
    if not f.exists():
        return "new"
    try:
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
    except Exception:
        return "rerun"
    return "skip" if d.get("batch_size") == TARGET_BATCH else "rerun"


def stash_old(outdir: str, arm: str, seed: str) -> str:
    """把旧结果改名备份（脚本按文件存在性跳过，不挪走就不会真跑）。

    返回说明字符串。
    """
    f = REPO / outdir / arm / f"seed{seed}" / "results.json"
    if not f.exists():
        return "（无旧文件）"
    try:
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        b = d.get("batch_size", "?")
    except Exception:
        b = "?"
    bak = f.with_suffix(f".batch{b}.bak")
    if bak.exists():
        bak.unlink()
    f.rename(bak)
    return f"旧文件(batch={b})→{bak.name}"


def run_one(tag, outdir, model, dataset, rank, extra, arm, seed) -> bool:
    cmd = [PY, "experiments/strict_freeze_control.py",
           "--dataset", dataset, "--data-dir", ".",
           "--out-dir", outdir, "--name", f"{tag}_r{rank}_",
           "--tags", arm, "--seeds", seed,
           "--epochs", "10", "--max-samples", "5000",
           "--batch-size", str(TARGET_BATCH), "--skip-frozen",
           "--rank", rank, *extra]
    if model:
        cmd += ["--model", model]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=8 * 3600, cwd=str(REPO))
    dt = time.time() - t0
    if r.returncode == 0:
        log(f"   ✅ {tag}/r{rank}/{arm}/seed{seed}（{dt:.0f}s）")
        return True
    err = next((l.strip() for l in (r.stderr or "").splitlines()
                if "Error" in l or "error" in l), "")
    log(f"   ❌ {tag}/r{rank}/{arm}/seed{seed} rc={r.returncode} {err[:110]}")
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    todo = []
    for tag, outdir, model, dataset, rank, extra, spec in PLAN:
        for arm, seeds in spec:
            for seed in seeds:
                st = need_run(outdir, arm, seed)
                if st != "skip":
                    todo.append((st, tag, outdir, model, dataset, rank, extra, arm, seed))

    from collections import Counter
    print(f"=== 队列：{len(todo)} run ===")
    print(f"  新建 {sum(1 for t in todo if t[0]=='new')} ｜ "
          f"重跑（批次<128）{sum(1 for t in todo if t[0]=='rerun')}")
    for k, v in sorted(Counter(f"{t[1]}/r{t[5]}" for t in todo).items()):
        print(f"  {k:<20} {v} run")
    if a.list:
        for t in todo:
            print(f"   [{t[0]:<5}] {t[1]:<10} r{t[5]:<4} {t[7]:<12} seed{t[8]}")
        return 0
    if not a.apply:
        print("  （预演；--apply 实跑）")
        return 0

    log("=" * 70)
    log(f"批次修正 + 5-seed 队列启动：{len(todo)} run（目标 batch {TARGET_BATCH}）")
    ok = fail = 0
    for t in todo:
        st, tag, outdir, model, dataset, rank, extra, arm, seed = t
        log(f"▶ [{st}] {tag}/r{rank}/{arm}/seed{seed}")
        if st == "rerun":
            note = stash_old(outdir, arm, seed)
            log(f"   {note}")
        if run_one(tag, outdir, model, dataset, rank, extra, arm, seed):
            ok += 1
        else:
            fail += 1
    log(f"完成：成功 {ok} ｜ 失败 {fail}")
    log("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
