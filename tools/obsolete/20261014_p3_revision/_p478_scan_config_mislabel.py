# -*- coding: utf-8 -*-
r"""系统扫描"配置错标"类缺陷：归档字段写模块级常量而非 args（2026-10-13）。

## 触发

`p3-allocation` 修 `--lr` 后，我核出**同一文件仍有残留**：
`tools/_p434_alloc_train.py` **L345** 的汇总归档写 `"lr": LR`（**模块级常量 5e-5**），
而 L220（逐 run）与 L274（优化器）都已正确用 `args.lr`。

**⇒ 文件名写 `lr0.001`、逐 run 写 `1e-3`、汇总写 `5e-5`** —— 三处自相矛盾。

## 危害分级（我提出的）

**错标 > 覆盖 > 重写**：覆盖/重写会丢数据或丢方案（"少了一个"）；
**错标最危险 —— 所有产物都在、数字都"真实"，只是标签与内容不符，没有任何迹象提示你去查。**

## 本脚本要做的

**机器穷举**：找出所有「归档字段 = 模块级全大写常量」而**同文件存在对应 `args.*` / `--xxx` 参数**的地方。

    python tools\_p478_scan_config_mislabel.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "config_mislabel_scan.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    findings = []

    files = sorted(glob.glob(str(REPO / "tools/_p4*.py"))) + \
        sorted(glob.glob(str(REPO / "tools/_p44*.py"))) + \
        sorted(glob.glob(str(REPO / "tools/_p46*.py"))) + \
        sorted(glob.glob(str(REPO / "tools/_p47*.py")))
    files = sorted(set(files))
    print(f"  扫描 {len(files)} 个脚本")
    print()
    print("=" * 104)
    print("可疑点：归档字段写模块级常量，但同文件有对应 CLI 参数")
    print("=" * 104)

    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        base = os.path.basename(f)
        # 1) 模块级全大写常量
        consts = set(re.findall(r"^([A-Z][A-Z0-9_]{1,})\s*=", t, re.M))
        if not consts:
            continue
        # 2) CLI 参数名（--foo-bar）
        flags = set(x.replace("-", "_") for x in re.findall(r'add_argument\("--([a-z0-9\-]+)"', t))
        # 3) 归档字段
        for m in re.finditer(r'"([a-z_][a-z0-9_]*)"\s*:\s*([A-Z][A-Z0-9_]{1,})\b', t):
            key, const = m.group(1), m.group(2)
            if const not in consts:
                continue
            # 该 key 是否有对应 CLI 参数或 args.<key>
            has_flag = key in flags
            has_args = bool(re.search(rf"args\.{re.escape(key)}\b", t))
            if has_flag or has_args:
                ln = t[:m.start()].count("\n") + 1
                findings.append({"file": base, "line": ln, "field": key, "const": const,
                                 "has_cli_flag": has_flag, "has_args_attr": has_args})
                print(f"  🔴 {base}:{ln}  \"{key}\": {const}"
                      f"  ｜ CLI --{key.replace('_','-')}: {has_flag} ｜ args.{key}: {has_args}")

    print()
    if not findings:
        print("  ✅ 未发现（本次扫描范围）")
    else:
        print(f"  **共 {len(findings)} 处可疑**")
        byfile = {}
        for x in findings:
            byfile.setdefault(x["file"], []).append(x)
        print()
        print("  按文件：")
        for k in sorted(byfile):
            print(f"     {k:<46} {len(byfile[k])} 处："
                  f"{[(y['line'], y['field']) for y in byfile[k]]}")

    print()
    print("=" * 104)
    print("说明")
    print("=" * 104)
    print("  ⚠️ 命中**不必然是错**：若该配置在本脚本中确实**不可变**（如注释明写'不可按批次改动'），")
    print("     则写常量是正确的 —— 但**必须论证**，不能默认。")
    print("  ⇒ 逐条判断：① 该参数是否可被 CLI 改？② 若可改，写常量就是**错标**；③ 若不可改，需有注释/断言说明。")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps({"n_files": len(files), "findings": findings},
                       ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
