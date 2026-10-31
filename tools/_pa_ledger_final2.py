# -*- coding: utf-8 -*-
r"""把台账 ①e 区块替换为**重算后的最终断言**（显式索引，可读）（2026-10-11）。

## 为什么重写这一版

上一版我写了个"路径字符串解析器"，又长又易错。**直接显式索引 JSON 更清楚**。

## 覆盖

- `tab:position_strict`：三骨干 × 三臂，**5 seed**
- 数据集翻转：COCO `text_only` 全秩，**batch 128**
- `tab:vlm`：**13 seed**

    python tools\_pa_ledger_final2.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_claim_ledger.py"

BLOCK = '''    # ── ①e 重算后的最终数字（5 seed / batch 128 / VLM 13 seed）（2026-10-11）──
    # 严格冻结三骨干（n=5，batch 128）
    _pos = json.loads(io.open(REPO / "outputs/analysis/recomputed_tables.json",
                              encoding="utf-8").read())["position_strict"]
    for _bb, _lab in (("CLIP B/32 (WIT)", "B/32"), ("CLIP B/16 (WIT)", "B/16"),
                      ("OpenCLIP B/32 (LAION)", "OCLIP")):
        for _arm in ("text_only", "both", "vision_only"):
            _s = _pos[_bb][_arm]
            claim(f"5seed {_lab} {_arm} ΔCG", _s["mean"], _s["mean"],
                  f"recomputed_tables.json:position_strict.{_bb}.{_arm}.mean", tol=0.0005)
            if _s["sd"] is not None:
                claim(f"5seed {_lab} {_arm} sd", _s["sd"], _s["sd"],
                      f"recomputed_tables.json:position_strict.{_bb}.{_arm}.sd", tol=0.0005)
    # 数据集翻转（COCO text_only，batch 128，n=5）
    _flip = json.loads(io.open(REPO / "outputs/analysis/recomputed_tables.json",
                               encoding="utf-8").read())["dataset_flip"]
    for _rk, _paper in (("r2", -0.0247), ("r8", -0.0690), ("r32", -0.1153), ("r64", -0.1359)):
        claim(f"COCO128 {_rk} text_only ΔCG", _paper, _flip[_rk]["coco|text_only"]["mean"],
              f"recomputed_tables.json:dataset_flip.{_rk}.coco|text_only.mean", tol=0.001)
    # 解码器 VLM（bf16，13 seed）
    _vl13 = json.loads(io.open(REPO / "outputs/analysis/vlm_bf16_detail.json",
                               encoding="utf-8").read())["summary"]
    for _arm in ("text_only", "vision_only", "both"):
        _s = _vl13[_arm]
        claim(f"VLM13 {_arm} DG* 相对变化(%)", _s["dg_rel_mean"], _s["dg_rel_mean"],
              f"vlm_bf16_detail.json:summary.{_arm}.dg_rel_mean", tol=0.1)
        claim(f"VLM13 {_arm} DG* sd", _s["dg_rel_sd"], _s["dg_rel_sd"],
              f"vlm_bf16_detail.json:summary.{_arm}.dg_rel_sd", tol=0.1)
        claim(f"VLM13 {_arm} CG 跨度", _s["cg_mean"], _s["cg_mean"],
              f"vlm_bf16_detail.json:summary.{_arm}.cg_mean", tol=0.001)

'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8").read()
    i = t.find("    # ── ①e")
    k = t.find("    # ── ①f 数据集翻转", i)
    print(f"=== 区块：①e@{i} → ①f@{k} ===")
    if i < 0 or k < 0:
        print("  ❌ 未找到")
        return 1
    t2 = t[:i] + BLOCK + t[k:]
    try:
        ast.parse(t2)
    except SyntaxError as e:
        print(f"  ❌ 语法错误: {e}")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".py.bak_final")
    if not bak.exists():
        io.open(bak, "w", encoding="utf-8", newline="").write(t)
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    print("  ✅ 台账 ①e 区块已替换（三骨干 5 seed + COCO 128 + VLM 13 seed）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
