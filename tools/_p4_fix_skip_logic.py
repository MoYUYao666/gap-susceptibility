# -*- coding: utf-8 -*-
r"""修 `_p4_download_clip_b16_ms.py` 的"跳过"逻辑（2026-10-07）。

## 问题（连续两次踩同一坑）

原逻辑：**目录非空 → 判定"已存在" → 跳过下载 → 直接校验 → 校验失败**。

两次实测都因此失败：
1. 第一次：目录有 `.gitattributes`/`config.json` 等配置，但**权重尚未下**；
2. 第二次：删掉残件后**配置仍在** → 又跳过。

**正确判据**：**权重文件存在且完整**，而非"目录非空"。

## 修法

- 判据改为：存在 `pytorch_model.bin` 或 `model.safetensors`，**且大小 > 500 MB**；
- 不满足则**照常下载**（已有配置会被跳过，只补权重）。

    python tools\_p4_fix_skip_logic.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p4_download_clip_b16_ms.py"

OLD = '''    if DST.exists() and any(DST.iterdir()):
        n = sum(f.stat().st_size for f in DST.rglob("*") if f.is_file()) / 2**20
        print(f"  ✅ 已存在（{n:.0f} MB）→ 直接校验")
        return 0 if verify() else 1'''

NEW = '''    # 判据：**权重存在且够大**，而非"目录非空"——
    # 实测两次踩坑：目录有配置但权重未下（或被删残件后配置仍在）→ 误判"已完成"而跳过。
    weights = [DST / "pytorch_model.bin", DST / "model.safetensors"]
    have_w = [w for w in weights if w.exists() and w.stat().st_size > 500 * 2**20]
    if have_w:
        n = sum(f.stat().st_size for f in DST.rglob("*") if f.is_file()) / 2**20
        print(f"  ✅ 权重已就位（{have_w[0].name}, {n:.0f} MB）→ 直接校验")
        return 0 if verify() else 1
    print("  ⏳ 权重缺失或过小 → 继续下载")'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "权重存在且够大" in t:
        print("  已修，跳过")
        return 0
    c = t.count(OLD)
    print(f"  命中 {c} 次")
    if c != 1:
        return 1
    if not apply:
        print("  （预演）")
        return 0
    new = t.replace(OLD, NEW, 1)
    ast.parse(new)
    io.open(F, "w", encoding="utf-8", newline="").write(new)
    print("  ✅ 已修：跳过判据改为「权重存在且 >500 MB」")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
