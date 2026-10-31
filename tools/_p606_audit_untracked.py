# -*- coding: utf-8 -*-
r"""扫描 `publish_clean/` 里**未跟踪**文件的中文（决定能否收录）（2026-10-14）。

## 为什么

`git status` 显示约 200+ 个未跟踪文件（多为 `outputs/` 下的结果 JSON，本轮新增的）。
**它们不在库里，但若收录，必须同样满足全英文。**

    python tools\_p606_audit_untracked.py [--apply]
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
OUT = REPO / "outputs" / "analysis" / "publish_untracked_cjk.json"
CJK = re.compile(r"[\u4e00-\u9fff]")
PUNCT = re.compile(r"[\u3000-\u303f\uff00-\uffef]")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = subprocess.run(["git", "status", "--porcelain", "-z"], cwd=str(PC), capture_output=True)
    raw = r.stdout.decode("utf-8", errors="replace").split("\0")
    untracked = []
    for x in raw:
        if x.startswith("?? "):
            p = x[3:].strip()
            fp = PC / p
            if fp.is_dir():
                for q in fp.rglob("*"):
                    if q.is_file():
                        untracked.append(q.relative_to(PC).as_posix())
            elif fp.is_file():
                untracked.append(p)
    print(f"  未跟踪文件：{len(untracked)} 个")

    cjk = {}
    punct = {}
    bins = 0
    for rel in untracked:
        p = PC / rel
        try:
            b = p.read_bytes()
        except Exception:
            continue
        if b"\x00" in b[:8192]:
            bins += 1
            continue
        try:
            t = b.decode("utf-8")
        except UnicodeDecodeError:
            cjk[rel] = -1
            continue
        n = len(CJK.findall(t))
        if n:
            cjk[rel] = n
        m = len(PUNCT.findall(t))
        if m:
            punct[rel] = m

    print(f"  二进制：{bins} 个")
    print(f"  **含中文：{len(cjk)} 个 / {sum(v for v in cjk.values() if v > 0)} 字符**")
    print(f"  含中文/全角标点：{len(punct)} 个")
    print()
    if cjk:
        print("  最多的 25 个：")
        for rel, n in sorted(cjk.items(), key=lambda kv: -kv[1])[:25]:
            print(f"     {n:>5}  {rel}")
        print()
        print("  按目录：")
        d = collections.Counter()
        for rel in cjk:
            d[rel.split("/")[0] + ("/" + rel.split("/")[1] if rel.count("/") >= 1 else "")] += 1
        for k, v in d.most_common(12):
            print(f"     {k:<40} {v}")
    else:
        print("  ✅ 未跟踪文件全部无中文（可直接收录）")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"untracked": len(untracked), "cjk": cjk, "punct": punct},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
