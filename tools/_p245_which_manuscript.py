# -*- coding: utf-8 -*-
r"""核实：PR 来信（`PR-D-26-10149`）对应的**到底是哪份稿**（2026-10-12）。

## 为什么

操作者说"PR 针对的是 `paper合`"。但我先前的理解是"PR 针对 P1（`paper/`）"。
**必须用文件证据判定，不靠推断。**

## 判据

PR 来信的标题逐字为：
> *Protect, Don't Perturb: **Cross-Modal Alignment under PEFT of Vision-Language Models***

→ 与 `paper/`、`paper合/` 各自 `main*.tex` 的 `\title{}` 逐字比对；
再看**篇幅/节结构**与来信里审稿人描述的特征（116 实验、Route D/E、Visual Fragility）是否吻合。

    python tools\_p245_which_manuscript.py
"""
from __future__ import annotations

import glob
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PR_TITLE = "Protect, Don't Perturb: Cross-Modal Alignment under PEFT of Vision-Language Models"


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def main() -> int:
    print("=" * 96)
    print(f"PR 来信标题（逐字）:\n  {PR_TITLE}")
    print("=" * 96)

    for d in ("paper", "paper合", "paper_a1", "paper2", "paper_ap3"):
        p = REPO / d
        if not p.is_dir():
            continue
        print(f"\n── {d}/ ──")
        for f in sorted(glob.glob(str(p / "main*.tex"))):
            t = io.open(f, encoding="utf-8", errors="replace").read()
            m = re.search(r"\\title(?:\[[^\]]*\])?\{(.*?)\}\s*\n", t, re.S)
            title = " ".join(m.group(1).split()) if m else "(无)"
            same = norm(title) == norm(PR_TITLE)
            short = norm(PR_TITLE) in norm(title)
            words = len(t.split())
            secs = len(re.findall(r"\\section\{", t))
            inc = len(re.findall(r"\\input\{", t))
            print(f"  {Path(f).name:<22} {'✅ 逐字一致' if same else ('⚠️ 含 PR 标题' if short else '')}")
            print(f"     title: {title[:96]}")
            print(f"     词数 {words} ｜ \\section {secs} ｜ \\input {inc}")

    print()
    print("=" * 96)
    print("PR 来信里审稿人提到的关键词 → 在哪份稿里出现")
    print("=" * 96)
    KEYS = ["Route D", "Route E", "Visual Fragility", "DG-Guided Early Stopping",
            "Distribution Gap", "116 experiments", "effective rank"]
    for k in KEYS:
        hits = []
        for d in ("paper", "paper合", "paper_a1"):
            for f in glob.glob(str(REPO / d / "*.tex")) + glob.glob(
                    str(REPO / d / "sections" / "*.tex")):
                t = io.open(f, encoding="utf-8", errors="replace").read()
                n = len(re.findall(re.escape(k), t, re.I))
                if n:
                    hits.append(f"{Path(f).parent.name}/{Path(f).name}({n})")
        print(f"  {k:<28} {'、'.join(hits[:6]) if hits else '🔴 三份稿都没有'}")

    print()
    print("=" * 96)
    print("判定")
    print("=" * 96)
    print("  规则：**标题逐字一致** 的那份 = PR 实际收到的稿。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
