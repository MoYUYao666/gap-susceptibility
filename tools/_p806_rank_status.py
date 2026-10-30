# -*- coding: utf-8 -*-
r"""One-line status report for the Paper A rank-ablation rerun.

Prints a single sentence: which ranks have finished, which rank is running, elapsed time and the
estimated remaining time. Designed to be called by an hourly reminder.

    python tools/_p806_rank_status.py
"""
from __future__ import annotations

import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "outputs" / "rank_rerun"
LOG = REPO / "outputs" / "analysis" / "_p805.log"
ERR = REPO / "outputs" / "analysis" / "_p805.err"
TOTAL_RANKS = [2, 4, 8, 16, 32, 64]


def running_pids() -> list:
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Process python -EA SilentlyContinue | "
             "Where-Object { $_.StartTime -gt (Get-Date).AddHours(-12) } | "
             "Select-Object -ExpandProperty Id"],
            capture_output=True, timeout=30)
        return [int(x) for x in r.stdout.decode("utf-8", "replace").split() if x.strip().isdigit()]
    except Exception:
        return []


def main() -> int:
    done = sorted(OUT_DIR.glob("*.json")) if OUT_DIR.exists() else []
    finished = []
    for p in done:
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
            if d.get("R@1") is not None:
                finished.append(d)
        except Exception:
            pass
    done_ranks = sorted({d["rank"] for d in finished})
    remaining = [r for r in TOTAL_RANKS if r not in done_ranks]

    current = None
    if LOG.exists():
        t = LOG.read_text(encoding="utf-8", errors="replace")
        m = re.findall(r"(rank\d+_text_only_s\d+)", t)
        if m:
            current = m[-1]

    epoch_txt = ""
    if ERR.exists():
        lines = [l for l in ERR.read_text(encoding="utf-8", errors="replace").splitlines()
                 if "Epoch" in l and "/10" in l]
        if lines:
            m = re.search(r"Epoch\s+(\d+)/10", lines[-1])
            if m:
                epoch_txt = f"，当前 rank 第 {m.group(1)}/10 epoch"

    pids = running_pids()
    if not remaining:
        print(f"【rank 消融】全部 {len(TOTAL_RANKS)} 个 rank 已完成："
              + "，".join(f"r{r} R@1={next(d['R@1'] for d in finished if d['rank'] == r):.4f}"
                          for r in done_ranks))
        return 0
    if pids:
        # per-rank cost measured on this machine: rank 2 with 5,000 images and 10 epochs took 1,753 s
        per_rank_min = 29.0
        print(f"【rank 消融】{len(done_ranks)}/{len(TOTAL_RANKS)} 个 rank 完成"
              + (f"（{', '.join('r' + str(r) for r in done_ranks)}）" if done_ranks else "")
              + f"，正在跑 {current or remaining[0]}{epoch_txt}，剩 {len(remaining)} 个、约 "
              + f"{len(remaining) * per_rank_min / 60:.1f} 小时")
    else:
        print(f"【rank 消融】🔴 进程已停止：{len(done_ranks)}/{len(TOTAL_RANKS)} 个 rank 完成，"
              f"剩 {', '.join('r' + str(r) for r in remaining)} 未跑 —— 需要重新启动")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
