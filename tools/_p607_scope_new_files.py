# -*- coding: utf-8 -*-
r"""清点 `7ee0059` 新增的 876 个文件（决定处理方式）（2026-10-14）。

## 发生了什么（我的第 37 个错）

`_p605` 修完 `.gitignore` 后，我跑 `git add -A` 再提交 ——
**该命令把 873 个从未翻译的未跟踪文件一并收录**，commit message 却只写了 gitignore。
⇒ 库里中文字符从 **27 反弹到 6,908**（109 个文件）。

**⇒ 两个失误**：① 扫描未跟踪文件**之前**先 `git add -A`（⇒ 扫描看到"未跟踪 0"）
② `git add -A` 前**没先看 `git status` 的 `??` 数量**。

    python tools\_p607_scope_new_files.py --apply
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
OUT = REPO / "outputs" / "analysis" / "publish_newfiles_scope.json"
CJK = re.compile(r"[\u4e00-\u9fff]")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    # 7ee0059 相对父提交新增的文件
    r = subprocess.run(["git", "diff", "--name-only", "--diff-filter=A", "7ee0059^", "7ee0059"],
                       cwd=str(PC), capture_output=True)
    added = [x for x in r.stdout.decode("utf-8", errors="replace").splitlines() if x.strip()]
    print(f"  7ee0059 新增文件：{len(added)}")

    ext = collections.Counter()
    size = collections.Counter()
    cjk = {}
    for rel in added:
        p = PC / rel
        ext[Path(rel).suffix.lower() or "(none)"] += 1
        if p.exists():
            size[Path(rel).suffix.lower() or "(none)"] += p.stat().st_size
            try:
                b = p.read_bytes()
                if b"\x00" in b[:8192]:
                    continue
                t = b.decode("utf-8")
            except Exception:
                continue
            n = len(CJK.findall(t))
            if n:
                cjk[rel] = n
    print()
    print("  按类型：")
    for k, v in ext.most_common(14):
        print(f"     {k:<12} {v:>4} 个 ｜ {size.get(k,0)/1024/1024:>7.2f} MB")
    print()
    print(f"  **其中含中文：{len(cjk)} 个 / {sum(cjk.values()):,} 字符**")
    print()
    print("  按目录：")
    d = collections.Counter()
    dc = collections.Counter()
    for rel in added:
        parts = rel.split("/")
        k = "/".join(parts[:2]) if len(parts) > 2 else "/".join(parts[:1])
        d[k] += 1
        dc[k] += cjk.get(rel, 0)
    for k in sorted(d, key=lambda x: -dc[x])[:16]:
        print(f"     {k:<44} {d[k]:>4} 个 ｜ {dc[k]:>6,} 中文字符")
    print()
    print("  含中文最多的 20 个：")
    for rel, n in sorted(cjk.items(), key=lambda kv: -kv[1])[:20]:
        print(f"     {n:>5}  {rel}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"added": len(added), "ext": dict(ext), "cjk": cjk,
             "cjk_total": sum(cjk.values())}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
