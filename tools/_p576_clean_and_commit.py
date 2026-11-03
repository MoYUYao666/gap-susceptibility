# -*- coding: utf-8 -*-
r"""清掉暂存区里违反发布边界的文件，然后提交并发 release（2026-10-14）。

## 混入的 5 个（`_p575` 发现）

| 文件 | 体积 | 为何不该推 |
|---|---|---|
| `outputs/a1_class_aligned/_B_with_cached_tf.npy` | **19.07 MB** | **`.npy` 在 `_p574` 的排除表里**（旧库遗留跟踪，新排除规则没作用于已跟踪文件） |
| `outputs/a1_h_templates.json` | 7.45 MB | 论文 A1 的 HTML 模板集合（非结果数据） |
| `tools/_tmp_a23_index.json` | 5.64 MB | **`_tmp_` 临时文件**（论文 A23） |
| `outputs/a1_h_baseline_metrics.json` | 4.57 MB | 论文 A1 的大 JSON |
| `docs/els-cas-templates.zip` | 3.15 MB | **压缩包在排除表里** |

**⇒ 一律从索引移除**（`.gitignore` 已含这些类型）。

    python tools\_p576_clean_and_commit.py --apply
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"

DROP = [
    "outputs/a1_class_aligned/_B_with_cached_tf.npy",
    "outputs/a1_h_templates.json",
    "tools/_tmp_a23_index.json",
    "outputs/a1_h_baseline_metrics.json",
    "docs/els-cas-templates.zip",
]
# 另外：任何 >2 MB 的文件都逐一列出（不自动删，只报告）
SIZE_GUARD = 2 * 1024 * 1024


def run(args, cwd=PC):
    r = subprocess.run(args, cwd=str(cwd), capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", errors="replace"), r.stderr.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0
    for f in DROP:
        rc, out, err = run(["git", "rm", "--cached", "-q", "--ignore-unmatch", f])
        print(f"  {'✅' if rc == 0 else '⚠️'} 从索引移除 {f}（rc={rc}）")
    # 本地文件也删掉（它们是旧库遗留，不该在发布目录）
    for f in DROP:
        p = PC / f
        if p.exists():
            p.unlink()
    print()

    # 体积守卫：列出仍 >2 MB 的已跟踪文件
    rc, out, _ = run(["git", "ls-files"])
    tracked = [x for x in out.splitlines() if x.strip()]
    big = []
    for t in tracked:
        p = PC / t
        if p.exists() and p.stat().st_size > SIZE_GUARD:
            big.append((p.stat().st_size, t))
    print(f"  仍 >2 MB 的已跟踪文件：{len(big)} 个")
    for sz, n in sorted(big, reverse=True)[:10]:
        print(f"     {sz/1024/1024:>7.2f} MB  {n}")

    rc, out, _ = run(["git", "status", "--porcelain"])
    lines = [l for l in out.splitlines() if l.strip()]
    kinds = {}
    for l in lines:
        k = l[:2].strip() or "?"
        kinds[k] = kinds.get(k, 0) + 1
    print()
    print("  暂存状态：", dict(sorted(kinds.items(), key=lambda kv: -kv[1])))
    rc, out, _ = run(["git", "diff", "--cached", "--shortstat"])
    print(f"  {out.strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
