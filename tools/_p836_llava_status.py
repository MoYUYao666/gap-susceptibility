# -*- coding: utf-8 -*-
r"""One-line progress report for the full LLaVA adaptation-site run.

Prints which of the 36 arm-seed combinations are done, which is running, and the remaining time
estimated from the runs that have already finished.

    python tools/_p836_llava_status.py
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "outputs" / "llava_sites"
LOG = REPO / "outputs" / "analysis" / "_p835_llava_full.out"
ARMS = ["frozen", "text_only", "vision_only", "both"]
SEEDS = [42, 123, 456]


def main() -> int:
    done = {}
    if OUT_DIR.exists():
        for p in sorted(OUT_DIR.glob("*.json")):
            m = re.match(r"(.+)_s(\d+)\.json$", p.name)
            if not m:
                continue
            try:
                d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            if d.get("dg") is not None or d.get("dg_after") is not None:
                done[(m.group(1), int(m.group(2)))] = d

    total = len(ARMS) * len(SEEDS)
    n = len(done)
    current = ""
    if LOG.exists():
        t = LOG.read_text(encoding="utf-8", errors="replace")
        names = re.findall(r"^\s*((?:frozen|text_only|vision_only|both)_s\d+)\s*$", t, re.M)
        if names:
            current = names[-1]

    # timing from the aggregate file if it exists, else from the individual run records
    per_run = None
    agg = REPO / "outputs" / "analysis" / "llava_sites.json"
    if agg.exists():
        try:
            a = json.loads(agg.read_text(encoding="utf-8", errors="ignore"))
            secs = [r.get("train_seconds", 0) + 1500 for r in a.get("runs", [])
                    if r.get("train_seconds")]
            if secs:
                per_run = sum(secs) / len(secs) / 60.0
        except Exception:
            pass

    running = bool([p for p in subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-Process python -EA SilentlyContinue | Where-Object { $_.WorkingSet64 -gt 3GB } | "
         "Select-Object -ExpandProperty Id"],
        capture_output=True, timeout=30).stdout.decode("utf-8", "replace").split() if p.isdigit()])

    if n >= total:
        vals = [d.get("dg_rel_change") for d in done.values()
                if d.get("dg_rel_change") is not None]
        s = ""
        if vals:
            s = f"，ΔDG 均值 {sum(vals) / len(vals):+.2%}"
        print(f"【LLaVA 全量】全部 {total} 个 run 完成{s}")
        return 0

    if running:
        est = ""
        if per_run:
            est = f"，按已完成的 run 估计还需 {per_run * (total - n) / 60:.1f} 小时"
        print(f"【LLaVA 全量】{n}/{total} 个 run 完成"
              + (f"（{', '.join(f'{a}_s{s}' for a, s in sorted(done))}）" if n else "")
              + f"，正在跑 {current or '（加载/隔离检查）'}{est}")
    else:
        print(f"【LLaVA 全量】🔴 进程已停止：{n}/{total} 个 run 完成 —— 需要重新启动")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
