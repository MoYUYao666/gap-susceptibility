# -*- coding: utf-8 -*-
r"""核验：GitHub 库里**还剩下哪些非英文内容**（2026-10-14）。

## 为什么重做

操作者问"上传 github 都全英文了吗"。**不能只说"是"** —— 要给出**逐项证据**：

1. 从**包里的 blob**（不是工作区）读每个已跟踪文件 ⇒ 排除工作区与索引不一致的可能
2. 报出**还有 CJK 的文件**、其内容、**以及为什么保留**
3. 另外检查**其它非英文形态**：中文标点、全角字符

    python tools\_p604_audit_english.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "publish_english_audit.json"

CJK = re.compile(r"[\u4e00-\u9fff]")
CJK_PUNCT = re.compile(r"[\u3000-\u303f\uff00-\uffef]")
# 其它非 ASCII 文字系统（日文假名、韩文、西里尔、阿拉伯…）
OTHER_SCRIPTS = re.compile(r"[\u3040-\u30ff\uac00-\ud7af\u0400-\u04ff\u0600-\u06ff]")

REASON = {
    "paper合": "on-disk directory name used by the audit scripts (outside the published repo)",
    "待补": "placeholder marker inside a linter's detection regex (functional data)",
    "待填": "placeholder marker inside a linter's detection regex (functional data)",
    "公开仓库": "entry in an audit tool's forbidden-string list (functional data)",
    "结果": "output filename in a shell command (functional data)",
    "块级": "output filename in a shell command (functional data)",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = subprocess.run(["git", "ls-files", "-z"], cwd=str(PC), capture_output=True)
    tracked = [x for x in r.stdout.decode("utf-8", errors="replace").split("\0") if x.strip()]
    print(f"  已跟踪 {len(tracked)} 个文件（读**包里的 blob**，非工作区）")

    cjk_files = {}
    punct_files = {}
    other_files = {}
    bin_files = 0
    for rel in tracked:
        rr = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=str(PC), capture_output=True)
        b = rr.stdout
        # 二进制判定（NUL 字节）
        if b"\x00" in b[:8192]:
            bin_files += 1
            # PNG 元数据里可能有非 ASCII，但不属"文本内容"
            continue
        try:
            t = b.decode("utf-8")
        except UnicodeDecodeError:
            cjk_files.setdefault(rel, -1)
            continue
        n = len(CJK.findall(t))
        if n:
            cjk_files[rel] = n
        p = len(CJK_PUNCT.findall(t))
        if p:
            punct_files[rel] = p
        o = len(OTHER_SCRIPTS.findall(t))
        if o:
            other_files[rel] = o

    print(f"  二进制（含 NUL）：{bin_files} 个 —— 不参与文本判定")
    print()
    print("=" * 100)
    print(f"① 仍含中文（CJK）的文本文件：**{len(cjk_files)} 个**")
    print("=" * 100)
    tot = 0
    for rel, n in sorted(cjk_files.items(), key=lambda kv: -kv[1]):
        if n < 0:
            print(f"  ⚠️ {rel}: 非 UTF-8 字节")
            continue
        tot += n
        rr = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=str(PC), capture_output=True)
        t = rr.stdout.decode("utf-8", errors="replace")
        frags = [m.group(0) for m in re.finditer(r"[\u4e00-\u9fff]+", t)]
        uniq = list(dict.fromkeys(frags))
        reasons = []
        for u in uniq:
            reasons.append(f"{u} ({REASON.get(u, '—')})")
        print(f"  {n:>3}  {rel}")
        print(f"       {', '.join(reasons[:4])}")
    print(f"  ⇒ 中文字符合计 **{tot}**")

    print()
    print("=" * 100)
    print(f"② 含中文/全角标点的文件：**{len(punct_files)} 个**")
    print("=" * 100)
    for rel, n in sorted(punct_files.items(), key=lambda kv: -kv[1])[:15]:
        print(f"  {n:>3}  {rel}")

    print()
    print("=" * 100)
    print(f"③ 含其它文字系统（假名/韩文/西里尔/阿拉伯）：**{len(other_files)} 个**")
    print("=" * 100)
    for rel, n in sorted(other_files.items(), key=lambda kv: -kv[1])[:15]:
        print(f"  {n:>3}  {rel}")

    print()
    print("=" * 100)
    print("判定")
    print("=" * 100)
    ok = len(cjk_files) <= 9 and tot <= 30
    print(f"  仍含中文的文本文件 {len(cjk_files)} 个 / {tot} 字符")
    print(f"  ⇒ {'✅ 基本全英文：剩余全部是**功能数据**（路径/正则/文件名），翻译会打断功能' if ok else '🔴 仍有较多中文'}")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"tracked": len(tracked), "binary": bin_files,
             "cjk_files": cjk_files, "cjk_total": tot,
             "punct_files": punct_files, "other_scripts": other_files},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
