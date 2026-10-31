# -*- coding: utf-8 -*-
r"""并排显示 A1 改动前后（标题 + 摘要）（2026-10-10）。

    python tools\_p99_a1_before_after.py
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper_a1" / "main.tex"

# 改动前的原文（从 git 历史取）
REV = "d4503b1~1"


def clean(s: str) -> str:
    s = re.sub(r"\\emph\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\text\{([^}]*)\}", r"\1", s)
    s = s.replace("\\%", "%").replace("---", "—").replace("--", "-")
    s = re.sub(r"\\ref\{[^}]*\}", "[ref]", s)
    s = re.sub(r"\$([^$]*)\$", lambda m: m.group(1).replace("\\to", "→")
               .replace("\\Delta", "Δ").replace("\\tau", "τ")
               .replace("{,}", ",").replace("{=}", "=").replace("{", "").replace("}", ""),
               s)
    return " ".join(s.split())


def get(rev: str | None, kind: str) -> str:
    src = (io.open(F, encoding="utf-8", errors="replace").read() if rev is None
           else subprocess.run(["git", "show", f"{rev}:paper_a1/main.tex"],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace").stdout)
    if kind == "title":
        m = re.search(r"\\title\{(.+?)\}\s*\n\\", src, re.S)
    else:
        m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", src, re.S)
    return clean(m.group(1)) if m else "(未找到)"


def main() -> int:
    print("=" * 70)
    print("标题")
    print("=" * 70)
    print("【改前】", get(REV, "title"))
    print()
    print("【改后】", get(None, "title"))

    print()
    print("=" * 70)
    print("摘要（首段，即改动所在）")
    print("=" * 70)
    b = get(None, "abstract")
    # 只打印到 "Under gap surgery" 之前
    k = b.find("Under")
    print("【改后首段】", b[:k] if k > 0 else b[:600])
    print()
    print("【改前首段】", get(REV, "abstract").split("Under")[0])

    print()
    print("=" * 70)
    print("摘要其余部分（未改动，供核对）")
    print("=" * 70)
    print(b[k:] if k > 0 else b[600:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
