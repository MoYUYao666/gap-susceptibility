# -*- coding: utf-8 -*-
r"""等当前 rank-1 训练结束后，按顺序跑完剩余实验步骤（**串行，单 GPU**）。

## 为什么串行

本机只有一块 GPU（RTX 4060 Laptop 8 GB）。先前并行两批实验曾造成显存吃紧
（曾达 7,938 MiB / 8,188 MiB）。故本脚本**逐个等待再启动下一个**。

## 为什么拆开而不写成长链

本次会话已被**电脑重启打断两次**，长链会整条丢失。故每步是**独立命令**，
且各训练脚本都有"已存在则跳过"逻辑 → 重启后重跑同一命令即可续上。

## 步骤

| # | 步骤 | 判据（完成） |
|---|---|---|
| 1 | both r1（进行中） | `r1/both/seed*/results.json` = 3 |
| 2 | both r64 | `r64/both/seed*/results.json` = 3 |
| 3 | CLIP r1/r64 text_only | `r{1,64}/text_only/seed*/results.json` = 各 3 |
| 4 | SigLIP r4（text_only + both） | `s7_siglip_lora_r4_*` = 10 |
| 5 | OpenCLIP r4（text_only + both） | `strict_freeze_openclip_rank` = 10 |

    python tools\_run_remaining_steps.py            # 预演
    python tools\_run_remaining_steps.py --apply    # 执行
"""
from __future__ import annotations

import glob
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = r"D:\Anaconda\envs\pytorch\python.exe"
SEEDS3 = ["42", "123", "456"]
SEEDS5 = ["42", "123", "456", "789", "1024"]


def n(pat: str) -> int:
    return len(glob.glob(str(REPO / pat)))


def wait_until(pat: str, target: int, label: str, timeout_h: float = 4.0,
               max_silent_min: float = 25.0) -> bool:
    """等产物达到目标数。

    ⚠ **关键**：若产物在 `max_silent_min` 分钟内**完全没增长**，判定该步已失败并立即返回 False。
    历史教训：2026-10-03 夜 `both r64` 因断言失败，而本函数不知道命令已死，仍按 6 小时超时轮询，
    整晚浪费，后续 SigLIP / OpenCLIP 步骤全未执行。
    """
    t0 = time.time()
    last_c = n(pat)
    last_change = time.time()
    while True:
        c = n(pat)
        if c >= target:
            print("  ✅ %s 完成（%d/%d）" % (label, c, target), flush=True)
            return True
        if c > last_c:
            last_c, last_change = c, time.time()
        silent_min = (time.time() - last_change) / 60.0
        if silent_min > max_silent_min:
            print("  ❌ %s 疑似失败：%.0f 分钟内产物无增长（%d/%d）—— 跳到下一步"
                  % (label, silent_min, c, target), flush=True)
            return False
        if time.time() - t0 > timeout_h * 3600:
            print("  ⚠ %s 超时（%d/%d）" % (label, c, target), flush=True)
            return False
        print("  … %s %d/%d（静默 %.0f 分钟）" % (label, c, target, silent_min), flush=True)
        time.sleep(120)


STEPS = [
    # (标签, 等待判据, 目标数, 命令)
    ("both r1（k 起点）", "outputs/strict_freeze_rank/r1/both/seed*/results.json", 3,
     [PY, "experiments/strict_freeze_control.py", "--rank", "1", "--tags", "both", "--skip-frozen",
      "--epochs", "10", "--max-samples", "5000", "--batch-size", "128",
      "--out-dir", "outputs/strict_freeze_rank/r1", "--seeds", *SEEDS3]),
    ("both r64（k 终点）", "outputs/strict_freeze_rank/r64/both/seed*/results.json", 3,
     [PY, "experiments/strict_freeze_control.py", "--rank", "64", "--tags", "both", "--skip-frozen",
      "--epochs", "10", "--max-samples", "5000", "--batch-size", "128",
      "--out-dir", "outputs/strict_freeze_rank/r64", "--seeds", *SEEDS3]),
    ("CLIP r1 text_only", "outputs/strict_freeze_rank/r1/text_only/seed*/results.json", 3,
     [PY, "experiments/strict_freeze_control.py", "--rank", "1", "--tags", "text_only", "--skip-frozen",
      "--epochs", "10", "--max-samples", "5000", "--batch-size", "128",
      "--out-dir", "outputs/strict_freeze_rank/r1", "--seeds", *SEEDS3]),
    ("CLIP r64 text_only", "outputs/strict_freeze_rank/r64/text_only/seed*/results.json", 3,
     [PY, "experiments/strict_freeze_control.py", "--rank", "64", "--tags", "text_only", "--skip-frozen",
      "--epochs", "10", "--max-samples", "5000", "--batch-size", "128",
      "--out-dir", "outputs/strict_freeze_rank/r64", "--seeds", *SEEDS3]),
    ("SigLIP r4（text_only + both）", "outputs/siglip_strict/*/s7_siglip_lora_r4_*/results.json", 10,
     [PY, "tools/_run_siglip_r4.py"]),
    ("OpenCLIP r4（text_only + both）", "outputs/strict_freeze_openclip_rank/*/seed*/results.json", 10,
     [PY, "experiments/strict_freeze_control.py", "--model", "models/openclip", "--name", "oclip_",
      "--rank", "4", "--tags", "text_only", "both", "--skip-frozen", "--epochs", "10",
      "--max-samples", "5000", "--batch-size", "128",
      "--out-dir", "outputs/strict_freeze_openclip_rank/r4", "--seeds", *SEEDS5]),
]


def main() -> int:
    apply = "--apply" in sys.argv
    print("剩余步骤（串行，单 GPU）：")
    for label, pat, tgt, _ in STEPS:
        print("  %-28s 目标 %-3d 当前 %d" % (label, tgt, n(pat)))
    if not apply:
        print("\n（预演，加 --apply 执行）")
        return 0

    for label, pat, tgt, cmd in STEPS:
        if n(pat) >= tgt:
            print("\n▶ %s —— 已完成，跳过" % label, flush=True)
            continue
        print("\n%s\n▶ %s\n%s" % ("=" * 70, label, "=" * 70), flush=True)
        r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        for l in (r.stdout or "").splitlines():
            if any(k in l for k in ("strict]", "done]", "✅", "❌", "total ", "拒绝运行", "严格冻结")):
                print("  " + l.strip()[:150], flush=True)
        if r.returncode != 0:
            print("  ⚠ 退出码 %d" % r.returncode, flush=True)
            for l in (r.stderr or "").strip().splitlines()[-4:]:
                print("    stderr: " + l[:140], flush=True)
        if not wait_until(pat, tgt, label):
            print("  ⚠ %s 未完成，继续下一步（该步可用同一命令重跑）" % label, flush=True)
    print("\n✅ 全部步骤完成", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
