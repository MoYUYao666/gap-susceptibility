# -*- coding: utf-8 -*-
r"""把门禁台账里的 VLM 断言同步为 **5 seed** 的值（2026-10-10 晚）。

## 为什么

`tools/_p158_vlm_bf16_detail.py` 重跑后，`vlm_bf16_detail.json` 的汇总从 3 seed 变成 5 seed：
`text_only` 66.8→**67.4**、`vision_only` 12.4→**15.8**、`both` 85.2→**86.5**，
CG 均值也变（0.2053→0.1958 等）→ **旧断言会失败**。

**本脚本按 JSON 现值改写台账里的那些期望值**（**以归档为准，不手填**）。

    python tools\_pa_ledger_vlm5.py [--apply]
"""
from __future__ import annotations

import ast
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_claim_ledger.py"
D = REPO / "outputs" / "analysis" / "vlm_bf16_detail.json"


def main() -> int:
    apply = "--apply" in sys.argv
    d = json.loads(io.open(D, encoding="utf-8").read())["summary"]
    want = {
        "text_only": (d["text_only"]["dg_rel_mean"], d["text_only"]["dg_rel_sd"],
                      d["text_only"]["cg_mean"]),
        "vision_only": (d["vision_only"]["dg_rel_mean"], d["vision_only"]["dg_rel_sd"],
                        d["vision_only"]["cg_mean"]),
        "both": (d["both"]["dg_rel_mean"], d["both"]["dg_rel_sd"],
                 d["both"]["cg_mean"]),
    }
    print("=== 归档现值（5 seed）===")
    for k, (rel, sd, cg) in want.items():
        print(f"  {k:<12} DG*={rel}±{sd}  CG={cg}")

    t = io.open(F, encoding="utf-8").read()
    i = t.find("    # ── ①g 解码器 VLM")
    j = t.find("    # ── ①f 数据集翻转", i)
    if i < 0 or j < 0:
        print("  ❌ 未找到 ①g 区块")
        return 1
    block = t[i:j]
    print(f"\n=== 原区块 {len(block)} 字符，重写 ===")

    new_block = '''    # ── ①g 解码器 VLM（bf16, **5 seed**；2026-10-10 晚更新）──
    _vl = json.loads(io.open(REPO / "outputs/analysis/vlm_bf16_detail.json",
                             encoding="utf-8").read())
    for _arm, _rel, _sd, _cg in (
            ("text_only", %s, %s, %s),
            ("vision_only", %s, %s, %s),
            ("both", %s, %s, %s)):
        _s = _vl["summary"][_arm]
        claim(f"VLM {_arm} DG* 相对变化(%%), n=5", _rel, _s["dg_rel_mean"],
              f"vlm_bf16_detail.json:summary.{_arm}.dg_rel_mean", tol=0.1)
        claim(f"VLM {_arm} DG* 相对变化 sd, n=5", _sd, _s["dg_rel_sd"],
              f"vlm_bf16_detail.json:summary.{_arm}.dg_rel_sd", tol=0.1)
        claim(f"VLM {_arm} CG 跨度均值, n=5", _cg, _s["cg_mean"],
              f"vlm_bf16_detail.json:summary.{_arm}.cg_mean", tol=0.001)
    # 逐 seed 的种子范围（论文表的 Seed range 列）
    for _arm, _lo, _hi in (("text_only", %s, %s), ("vision_only", %s, %s),
                           ("both", %s, %s)):
        _rels = _vl["summary"][_arm]["dg_rel"]
        claim(f"VLM {_arm} 种子下界(%%)", _lo, min(_rels),
              f"vlm_bf16_detail.json:summary.{_arm}.dg_rel", tol=0.1)
        claim(f"VLM {_arm} 种子上界(%%)", _hi, max(_rels),
              f"vlm_bf16_detail.json:summary.{_arm}.dg_rel", tol=0.1)

''' % (
        want["text_only"][0], want["text_only"][1], want["text_only"][2],
        want["vision_only"][0], want["vision_only"][1], want["vision_only"][2],
        want["both"][0], want["both"][1], want["both"][2],
        min(d["text_only"]["dg_rel"]), max(d["text_only"]["dg_rel"]),
        min(d["vision_only"]["dg_rel"]), max(d["vision_only"]["dg_rel"]),
        min(d["both"]["dg_rel"]), max(d["both"]["dg_rel"]),
    )
    t2 = t[:i] + new_block + t[j:]
    try:
        ast.parse(t2)
    except SyntaxError as e:
        print(f"  ❌ 语法错误: {e}")
        return 1
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    print("  ✅ 台账 ①g 区块已同步为 5-seed 值（14 条断言）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
