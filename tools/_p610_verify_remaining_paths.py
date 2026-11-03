# -*- coding: utf-8 -*-
r"""核验剩余中文是否**指向真实存在的文件**（决定能否翻译）（2026-10-14）。

    python tools\_p610_verify_remaining_paths.py
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
ROOT = REPO
CJK = re.compile(r"[\u4e00-\u9fff]")

CHECKS = [
    ("outputs/analysis/p3_stats_recon.json", "outputs/_serial_logs"),
    ("outputs/analysis/dinov2_hetero/clip_baseline_check.json", None),
    ("outputs/analysis/a1_recheck16.json", None),
]


def main() -> int:
    # ① _serial_logs 目录里到底有哪些文件
    print("=" * 96)
    print("① outputs/_serial_logs/ 实际文件名（核验 p3_stats_recon.json 的路径）")
    print("=" * 96)
    for base in (PC / "outputs" / "_serial_logs", ROOT / "outputs" / "_serial_logs"):
        if base.exists():
            print(f"  {base}")
            for p in sorted(base.iterdir())[:20]:
                print(f"     {p.name}")
            break
    else:
        print("  ⚠️ 两个位置都没有 outputs/_serial_logs/")

    # ② dinov2 的 published_source 指向的真实目录
    print()
    print("=" * 96)
    print("② clip_baseline_check.json 的 published_source")
    print("=" * 96)
    p = PC / "outputs" / "analysis" / "dinov2_hetero" / "clip_baseline_check.json"
    if p.exists():
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        ps = d.get("published_source")
        print(f"  值：{ps!r}")
        m = re.match(r"([^ ]+)", str(ps))
        if m:
            cand = ROOT / m.group(1)
            print(f"  ⇒ 路径 {m.group(1)} 存在于工作区：**{cand.exists()}**")

    # ③ a1_recheck16 的 pattern
    print()
    print("=" * 96)
    print("③ a1_recheck16.json 里的中文（是正则模式还是说明文字？）")
    print("=" * 96)
    p = PC / "outputs" / "analysis" / "a1_recheck16.json"
    if p.exists():
        t = io.open(p, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r".{0,80}[\u4e00-\u9fff]+.{0,80}", t):
            print(f"  {' '.join(m.group(0).split())[:150]}")

    # ④ 全量：剩余中文的**完整清单与上下文**
    print()
    print("=" * 96)
    print("④ 全部剩余中文的上下文（逐个判断）")
    print("=" * 96)
    import subprocess
    r = subprocess.run(["git", "ls-files"], cwd=str(PC), capture_output=True)
    for rel in r.stdout.decode("utf-8", errors="replace").splitlines():
        if not rel.strip():
            continue
        fp = PC / rel
        if not fp.exists():
            continue
        try:
            b = fp.read_bytes()
            if b"\x00" in b[:4096]:
                continue
            t = b.decode("utf-8")
        except Exception:
            continue
        if not CJK.search(t):
            continue
        print(f"  ── {rel}")
        for m in list(re.finditer(r".{0,55}[\u4e00-\u9fff]+.{0,55}", t))[:4]:
            print(f"       {' '.join(m.group(0).split())[:130]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
