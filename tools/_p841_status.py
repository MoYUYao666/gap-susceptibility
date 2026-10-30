# -*- coding: utf-8 -*-
r"""One-line progress report for the full-COCO scale-up and the full LLaVA run.

    python tools/_p841_status.py
"""
from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
COCO_DIR = REPO / "outputs" / "full_coco"
LLAVA_DIR = REPO / "outputs" / "llava_sites"
# The live full-COCO log. It moved from _p839_coco.out to _p845_coco.out when the run was relaunched
# behind the chained launchers; pointing at the stale file made this reporter read a frozen log that
# stopped at 08:35 and report "evaluating frozen baseline" while s456 was in fact training epoch 3.
COCO_OUT = REPO / "outputs" / "analysis" / "_p845_coco.out"
COCO_AGG = REPO / "outputs" / "analysis" / "full_coco.json"
LLAVA_OUT = REPO / "outputs" / "analysis" / "_p838_llava.out"


def running() -> bool:
    """True when a GPU job is active.

    A resident-memory threshold is the wrong test: the full-COCO job holds only about 0.7 GB of host
    memory while it trains, so a 1 GB cut-off reported no work running. The GPU utilisation and the
    presence of any python process whose CPU time is advancing are what distinguish an active job.
    """
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "$u = (nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits) -replace '\\D',''; "
             "if ([int]$u -gt 5) { 'yes' } else { "
             "  $a = (Get-Process python -EA SilentlyContinue | Measure-Object CPU -Sum).Sum; "
             "  Start-Sleep -Seconds 5; "
             "  $b = (Get-Process python -EA SilentlyContinue | Measure-Object CPU -Sum).Sum; "
             "  if (($b - $a) -gt 1) { 'yes' } else { 'no' } }"],
            capture_output=True, timeout=60)
        return "yes" in r.stdout.decode("utf-8", "replace")
    except Exception:
        return False


def llava_is_the_live_job() -> bool:
    """True when the process holding the GPU was started from the LLaVA script."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object { $_.CommandLine -like '*_p820_llava_sites*' } | "
             "Select-Object -ExpandProperty ProcessId"],
            capture_output=True, timeout=40)
        return bool([x for x in r.stdout.decode("utf-8", "replace").split() if x.strip().isdigit()])
    except Exception:
        return False


LLAVA_ACTIVE = llava_is_the_live_job()


def coco_line() -> str:
    n = 0
    if COCO_DIR.exists():
        for p in COCO_DIR.glob("*.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            if d.get("R@1") is not None:
                n += 1
    # The aggregate is the run's own completion marker: once it exists the log's last phase
    # ("s456 … 正在全量评测") is history, not the current state, and reporting it would be the same
    # stale-reading failure this reporter was just fixed for.
    if COCO_AGG.exists():
        return f"COCO 全量 {n}/3 个训练 run 完成，汇总已落盘"
    return f"COCO 全量 {n}/3 个训练 run 完成{coco_phase()}"


def coco_phase() -> str:
    """Name the phase the full-COCO job is actually in, from its own log.

    The first version of this function indexed on the *frozen* heading and on any occurrence of
    "full_text_only", so once the frozen baseline had been evaluated it reported the frozen
    evaluation forever -- it never looked at the text that follows.

    The log mixes in Chinese section headings that get mangled by the redirect, so only ASCII markers
    are parsed here: the epoch lines ("Epoch   3/3 | Loss: ... | Time: ..."), the ASCII results path
    that ends an epoch, and the per-run summary line ("train 3700s  eval 720s  R@1 0.5821"). Each
    epoch's own "results.json" is attributed to the run that precedes it, because the trainer writes
    one per epoch while the final full-gallery evaluation is what produces the aggregate.
    """
    if not COCO_OUT.exists():
        return ""
    text = COCO_OUT.read_text(encoding="utf-8", errors="replace")
    # Match the run name where it stands alone, not where it is part of a path: a substring test also
    # hits the trainer's per-epoch "results saved" line, whose path ends in
    # "..._r8_s456\results.json" and would therefore look like a later occurrence of that run.
    hits = list(re.finditer(r"(?<![A-Za-z0-9_])full_text_only_r\d+_s\d+(?![A-Za-z0-9_])", text))
    if not hits:
        tail = text[text.rfind("frozen CLIP"):]
        return "（正在评测冻结基线，40,504 图）" if "R@1" not in tail else ""
    # Each run leaves three name hits: its header, its per-epoch "results saved" path, and its summary
    # line. Anchor on the last hit that is followed by evidence of work -- otherwise the anchor lands
    # on the trailing "results saved ... s456\results.json" and every epoch of that run looks absent.
    start = None
    for h in reversed(hits):
        if (re.search(r"Epoch\s+\d+/\d+\s*\|", text[h.start():])
                or re.search(r"train\s+[\d.]+s\s+eval\s+[\d.]+s", text[h.start():])):
            start = h.start()
            break
    if start is None:
        start = hits[-1].start()
    cur = re.search(r"full_text_only_r\d+_s\d+", text[start:]).group(0)
    after = text[start:]
    if re.search(r"train\s+[\d.]+s\s+eval\s+[\d.]+s", after):
        return f"（{cur} 训练完，正在全量评测）"
    n_ep = len(re.findall(r"Epoch\s+\d+/\d+\s*\|", after))
    if n_ep >= 3:
        # All three epochs are logged but the run summary has not been written yet, and no new log
        # line has appeared for a while: the only remaining step is the full-gallery evaluation,
        # which runs for many minutes without emitting anything. Training emits a line every epoch
        # (about 20 min apart), so a quiet log means evaluation rather than training.
        if time.time() - COCO_OUT.stat().st_mtime > 600:
            return f"（{cur} 训练完，正在全量评测）"
        return f"（{cur} 正在第 3/3 轮收尾）"
    return f"（正在训练 {cur}，第 {n_ep + 1}/3 轮）"


def llava_line() -> str:
    n = 0
    if LLAVA_DIR.exists():
        for p in LLAVA_DIR.glob("*.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            if d.get("dg_after") is not None:
                n += 1
    # Only report a current run when LLaVA is the job actually executing; otherwise an old log line
    # would keep naming a finished run as the active one.
    cur = ""
    if LLAVA_ACTIVE:
        if LLAVA_OUT.exists():
            t = LLAVA_OUT.read_text(encoding="utf-8", errors="replace")
            m = re.findall(r"^\s*((?:frozen|text_only|vision_only|both)_s\d+)\s*$", t, re.M)
            if m:
                cur = f"（正在跑 {m[-1]}）"
    return f"LLaVA 全量 {n}/12 个 run 完成{cur}"


def main() -> int:
    live = running()
    prefix = "" if live else "🔴 无任务在跑 ｜ "
    print(f"【{prefix}{coco_line()} ｜ {llava_line()}】")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
