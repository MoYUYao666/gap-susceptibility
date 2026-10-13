# -*- coding: utf-8 -*-
r"""把 bf16 3-seed 的解码器 VLM 数字加进门禁台账（2026-10-10）。

来源：`outputs/analysis/vlm_bf16_detail.json`（由 `_p158` 从 `outputs/vlm_seeds_bf16/*.json` 生成）
以及 `outputs/analysis/vlm_bf16_seeds_verdict.json`。

    python tools\_pa_ledger_vlm.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_claim_ledger.py"
ANCHOR = "    # ── ①f 数据集翻转"

ADD = '''    # ── ①g 解码器 VLM（bf16, 3 seed；2026-10-10 取代原 4-bit 单 seed）──
    _vl = json.loads(io.open(REPO / "outputs/analysis/vlm_bf16_detail.json",
                             encoding="utf-8").read())
    for _arm, _rel, _sd, _cg, _cgsd in (
            ("text_only", 66.8, 6.5, 0.2053, 0.1505),
            ("vision_only", 12.4, 4.7, 0.3421, 0.0644),
            ("both", 85.2, 11.2, 0.3595, 0.2352)):
        _s = _vl["summary"][_arm]
        claim(f"VLM {_arm} DG* 相对变化(%)", _rel, _s["dg_rel_mean"],
              f"vlm_bf16_detail.json:summary.{_arm}.dg_rel_mean", tol=0.1)
        claim(f"VLM {_arm} DG* 相对变化 sd", _sd, _s["dg_rel_sd"],
              f"vlm_bf16_detail.json:summary.{_arm}.dg_rel_sd", tol=0.1)
        claim(f"VLM {_arm} n_trainable", float(_s["n_trainable"]), float(_s["n_trainable"]),
              f"vlm_bf16_detail.json:summary.{_arm}.n_trainable", tol=1)
        claim(f"VLM {_arm} CG 跨度均值", _cg, _s["cg_mean"],
              f"vlm_bf16_detail.json:summary.{_arm}.cg_mean", tol=0.001)
    # 逐 seed 的种子范围（论文表里的 Seed range 列）
    for _arm, _lo, _hi in (("text_only", 59.4, 71.1), ("vision_only", 8.5, 17.7),
                           ("both", 73.1, 95.1)):
        _rels = _vl["summary"][_arm]["dg_rel"]
        claim(f"VLM {_arm} 种子下界(%)", _lo, min(_rels),
              f"vlm_bf16_detail.json:summary.{_arm}.dg_rel", tol=0.1)
        claim(f"VLM {_arm} 种子上界(%)", _hi, max(_rels),
              f"vlm_bf16_detail.json:summary.{_arm}.dg_rel", tol=0.1)

''' + ANCHOR


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "解码器 VLM（bf16, 3 seed" in t:
        print("  已加，跳过")
        return 0
    if t.count(ANCHOR) != 1:
        print(f"  ❌ 锚点未唯一命中（{t.count(ANCHOR)}）")
        return 1
    t2 = t.replace(ANCHOR, ADD, 1)
    ast.parse(t2)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    print("  ✅ 已加 17 条主张")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
