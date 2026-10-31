# -*- coding: utf-8 -*-
r"""清点发布库里的个人信息（2026-10-14）。

    python tools\_p584_audit_personal_info.py
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
SLUG = "MoYUYao666/gap-susceptibility"

PATS = [
    (r"hw4c24@soton\.ac\.uk", "邮箱（Southampton）"),
    (r"2024282101@hrbeu\.edu\.cn", "邮箱（提交身份）"),
    (r"[\w.+-]+@[\w-]+\.[\w.]+", "任意邮箱"),
    (r"ORCID[:\s]*[\d-]{15,}", "ORCID"),
    (r"Hongrui\s+Wan|HongruiWan|Wan,\s*Hongrui", "姓名"),
    (r"\bMoYUYao666\b", "GitHub 用户名"),
    (r"00 44|0044|\+44\s?\d", "英国电话"),
    (r"\b1[3-9]\d{9}\b", "中国手机号"),
    (r"Southampton", "单位（可接受？）"),
    (r"hw4c24", "校园账号片段"),
]


def main() -> int:
    print("=" * 100)
    print("① README.md（远端）里的个人信息")
    print("=" * 100)
    r = subprocess.run(["gh", "api", f"repos/{SLUG}/readme", "--jq", ".content"],
                       capture_output=True)
    text = ""
    if r.returncode == 0:
        import base64
        text = base64.b64decode(r.stdout.decode().strip()).decode("utf-8", errors="replace")
    if not text:
        text = io.open(PC / "README.md", encoding="utf-8", errors="replace").read()
        print("  （用本地副本）")
    for pat, label in PATS:
        hits = re.findall(pat, text)
        n = len(hits)
        flag = "⚠️" if n else "✅"
        extra = f"  例：{list(dict.fromkeys(hits))[:3]}" if n else ""
        print(f"  {flag} {label:<22} {n} 处{extra}")

    print()
    print("=" * 100)
    print("② 整个发布库里其它位置")
    print("=" * 100)
    counts = {label: 0 for _, label in PATS}
    examples = {label: [] for _, label in PATS}
    files = [p for p in PC.rglob("*") if p.is_file() and ".git" not in p.parts]
    for p in files:
        try:
            t = io.open(p, encoding="utf-8", errors="strict").read()
        except Exception:
            continue
        for pat, label in PATS:
            hits = re.findall(pat, t)
            if hits:
                counts[label] += len(hits)
                if len(examples[label]) < 3:
                    examples[label].append(f"{p.relative_to(PC)}")
    for label in counts:
        n = counts[label]
        flag = "⚠️" if n else "✅"
        print(f"  {flag} {label:<22} {n:>5} 处  {examples[label] if n else ''}")

    print()
    print("=" * 100)
    print("③ commit 的作者身份（历史里）")
    print("=" * 100)
    r = subprocess.run(["git", "log", "--format=%an <%ae>", "-50"], cwd=str(PC), capture_output=True)
    idents = {}
    for line in r.stdout.decode("utf-8", errors="replace").splitlines():
        idents[line.strip()] = idents.get(line.strip(), 0) + 1
    for k, n in sorted(idents.items(), key=lambda kv: -kv[1]):
        print(f"     {n:>3} 次  {k}")

    print()
    print("=" * 100)
    print("④ 远端 README 的作者行")
    print("=" * 100)
    for l in text.splitlines()[:8]:
        if l.strip():
            print("     " + l[:110])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
