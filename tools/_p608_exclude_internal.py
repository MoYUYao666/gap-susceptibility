# -*- coding: utf-8 -*-
r"""排除不该发布的内部文件，并核验其余 JSON 的翻译安全性（2026-10-14）。

## 第一步：排除

| 文件 | 为何不该发布 |
|---|---|
| `outputs/analysis/p3_reviews_structured.json` | **审稿意见结构化文本**（33 条原文） |
| `outputs/analysis/p3_review_classes.json` | **审稿意见分类** |
| `outputs/analysis/p3_reviews_parsed.json`（若在库） | 同上 |
| `outputs/analysis/p3_contradiction_scan.json` | 内含**审稿用语与我方撤回记录** |
| `outputs/analysis/paperhe_vs_pr.json` / `pr_*.json` / `prl_guide_rules.json` | 投稿策略与期刊对比 |
| `outputs/_remote_*.py` | 简陋的云端临时脚本（非管线） |
| `outputs/analysis/_p*.txt` | 会话临时日志 |

**⚠️ 这些在 `publish_clean` 里，但注意：**它们同时也被 `tools/` 或 `docs/` 引用 ⇒
排除后**引用会断**。**但**：引用它们的脚本多为一次性脚本（已移出），
且**这些 JSON 本身不是论文数字的来源**（是元数据）。

## 第二步：核验其余 JSON 的中文是否在"值"上（可安全翻译）

    python tools\_p608_exclude_internal.py [--dry-run|--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
KEEP = REPO / "_removed_from_publish" / "internal_metadata"
CJK = re.compile(r"[\u4e00-\u9fff]")

EXCLUDE = [
    "outputs/analysis/p3_reviews_structured.json",
    "outputs/analysis/p3_review_classes.json",
    "outputs/analysis/p3_reviews_parsed.json",
    "outputs/analysis/p3_contradiction_scan.json",
    "outputs/analysis/p3_page_feasibility.json",
    "outputs/analysis/p3_compress_allocation.json",
    "outputs/analysis/p3_compression_plan.json",
    "outputs/analysis/prl_guide_rules.json",
    "outputs/analysis/paperhe_vs_pr.json",
    "outputs/analysis/pr_to_fixes_map.json",
    "outputs/analysis/pr_full_inventory.json",
    "outputs/analysis/pr_strict_audit.json",
    "outputs/analysis/claim_ledger.json",
    "outputs/analysis/p3_config_mislabel_fixes.json",
    "outputs/analysis/config_mislabel_scan.json",
    "outputs/analysis/config_mislabel_scan2.json",
]


def run(args, cwd=PC):
    r = subprocess.run(args, cwd=str(cwd), capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", errors="replace"), r.stderr.decode("utf-8", errors="replace")


def walk_strings(obj, path="$"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield (f"{path}.{k}", k, True)
            yield from walk_strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield (path, obj, False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not (a.dry_run or a.apply):
        a.dry_run = True

    print("=" * 96)
    print("① 待排除的内部文件")
    print("=" * 96)
    present = []
    for rel in EXCLUDE:
        p = PC / rel
        if p.exists():
            n = len(CJK.findall(io.open(p, encoding="utf-8", errors="replace").read()))
            present.append(rel)
            print(f"  ✅ {rel:<56} {n:>5} 中文字符")
        else:
            print(f"  — {rel}（不在库）")
    print(f"  ⇒ 实际存在 {len(present)} 个")

    print()
    print("=" * 96)
    print("② 其余含中文 JSON 的键/值分布（判断翻译安全性）")
    print("=" * 96)
    rc, out, _ = run(["git", "ls-files", "outputs"])
    json_files = [x for x in out.splitlines() if x.endswith(".json")]
    unsafe = []
    checked = 0
    for rel in json_files:
        p = PC / rel
        if rel in EXCLUDE or not p.exists():
            continue
        try:
            b = p.read_bytes()
            if b"\x00" in b[:4096]:
                continue
            t = b.decode("utf-8")
        except Exception:
            continue
        if not CJK.search(t):
            continue
        try:
            obj = json.loads(t)
        except Exception:
            continue
        checked += 1
        key_cjk = val_cjk = 0
        for jp, s, is_key in walk_strings(obj):
            if isinstance(s, str) and CJK.search(s):
                if is_key:
                    key_cjk += len(CJK.findall(s))
                else:
                    val_cjk += len(CJK.findall(s))
        if key_cjk:
            unsafe.append((rel, key_cjk, val_cjk))
    print(f"  检查 {checked} 个含中文 JSON")
    print(f"  中文在**键**上（不可安全翻译）：**{len(unsafe)} 个**")
    for rel, k, v in sorted(unsafe, key=lambda x: -x[1])[:12]:
        print(f"     key {k:>4} / val {v:>4}  {rel}")

    if a.dry_run:
        print()
        print("  （dry-run；加 --apply 执行排除）")
        return 0

    KEEP.mkdir(parents=True, exist_ok=True)
    moved = 0
    for rel in present:
        p = PC / rel
        dst = KEEP / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)
        rc, _, _ = run(["git", "rm", "-q", "--cached", "--ignore-unmatch", rel])
        p.unlink(missing_ok=True)
        moved += 1
    print()
    print(f"  ✅ 已排除 {moved} 个（本地留存在 {KEEP.relative_to(REPO)}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
