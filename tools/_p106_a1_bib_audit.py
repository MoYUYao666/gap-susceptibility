# -*- coding: utf-8 -*-
r"""核查 A1 的文献与引用完整性（2026-10-10）。

## 为什么

`related_work_bibitems.tex`（43 条，为 R1.2 准备）被 `\input` 在**最后一个 `\bibitem` 内部**，
按该文件自己的说明应在 `thebibliography` 环境**内部任意位置**并入。

**本脚本查**：① A1 现在实际是多少条文献；② 是否有未定义引用；③ 43 条是否真被并入。

    python tools\_p106_a1_bib_audit.py [--apply]
"""
from __future__ import annotations

import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "paper_a1"


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(A1 / "main.tex", encoding="utf-8", errors="replace").read()
    extra = io.open(A1 / "related_work_bibitems.tex", encoding="utf-8", errors="replace").read()

    main_keys = re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}", t)
    extra_keys = re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}", extra)
    print("=== 文献条数 ===")
    print(f"  main.tex 内: {len(main_keys)} 条")
    print(f"  related_work_bibitems.tex 内: {len(extra_keys)} 条")
    dup = set(main_keys) & set(extra_keys)
    print(f"  重叠 key: {len(dup)} 个 {sorted(dup)[:6]}")
    print(f"  → 并集: **{len(set(main_keys) | set(extra_keys))}** 条")

    print("\n=== 引用的 key ===")
    cited = set()
    for f in (A1 / "main.tex", A1 / "related_work.tex"):
        if f.exists():
            s = io.open(f, encoding="utf-8", errors="replace").read()
            for m in re.finditer(r"\\cite[tp]?\{([^}]*)\}", s):
                for k in m.group(1).split(","):
                    if k.strip():
                        cited.add(k.strip())
    print(f"  正文引用 {len(cited)} 个 key")
    defined = set(main_keys) | set(extra_keys)
    undef = sorted(cited - defined)
    unused = sorted(defined - cited)
    print(f"  **未定义引用**: {len(undef)} {undef[:10]}")
    print(f"  定义但未引用: {len(unused)} {unused[:6]}")

    print("\n=== 编译日志的引用警告 ===")
    log = A1 / "main.log"
    if log.exists():
        s = io.open(log, encoding="utf-8", errors="replace").read()
        warn = [l for l in s.splitlines()
                if "undefined" in l.lower() or "Citation" in l]
        print(f"  含 'undefined'/'Citation' 的日志行: {len(warn)}")
        for l in warn[:6]:
            print("   ", l.strip()[:120])
    else:
        print("  （无 main.log）")

    print("\n=== 判定 ===")
    if undef:
        print(f"  ❌ **有 {len(undef)} 个未定义引用** → 需先修")
    elif len(unused) > 5:
        print(f"  ⚠️ 有 {len(unused)} 条定义未引用 → `\\input` 的 43 条**已并入但多数未被正文引用**")
    else:
        print("  ✅ 引用与定义一致")

    if apply:
        out = REPO / "outputs" / "analysis" / "a1_bib_audit.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        io.open(out, "w", encoding="utf-8", newline="").write(json.dumps({
            "main_bibitems": len(main_keys), "extra_bibitems": len(extra_keys),
            "union": len(defined), "cited": len(cited),
            "undefined": undef, "unused": unused,
        }, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
