# -*- coding: utf-8 -*-
r"""把台账同步为重算后的 **5-seed / batch-128** 数字（2026-10-11）。

## 变更来源

- `tab:position_strict`：三骨干 × 三臂 → 5 seed 均值（`recomputed_tables.json`）
- 数据集翻转：COCO `text_only` 全秩 → batch 128 新值
- `tab:vlm`：13 seed（`vlm_bf16_detail.json`）

**本脚本按归档 JSON 现值改写台账里的 ①e/①f/①g 三个区块**（以归档为准，不手填）。

    python tools\_pa_ledger_sync_final.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_claim_ledger.py"
RT = REPO / "outputs" / "analysis" / "recomputed_tables.json"
VL = REPO / "outputs" / "analysis" / "vlm_bf16_detail.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rt = json.loads(io.open(RT, encoding="utf-8").read())
    vl = json.loads(io.open(VL, encoding="utf-8").read())["summary"]

    t = io.open(F, encoding="utf-8").read()
    i = t.find("    # ── ①e 两处理论否证")
    j = t.find("    # ── ①d dg_pred 偏差", 0)
    # 找 ①g 之后的下一个区块起点
    k = t.find("    # ── ①f 数据集翻转", i)
    print(f"=== 区块位置：①e@{i} ｜ ①f@{k} ===")
    if i < 0 or k < 0:
        print("  ❌ 未找到区块")
        return 1

    pos = rt["position_strict"]
    flip = rt["dataset_flip"]
    rows = []
    # ① tab:position_strict（5 seed）
    for label, key in (("CLIP B/32", "CLIP B/32 (WIT)"),
                       ("CLIP B/16", "CLIP B/16 (WIT)"),
                       ("OpenCLIP", "OpenCLIP B/32 (LAION)")):
        for arm in ("text_only", "both", "vision_only"):
            s = pos.get(key, {}).get(arm)
            if s:
                rows.append((f"5seed {label} {arm} ΔCG", s["mean"],
                             f"recomputed_tables.json:position_strict.{key}.{arm}.mean",
                             f"recomputed_tables.json:position_strict.{key}.{arm}.mean",
                             0.001))
    # ② COCO text_only 全秩（batch 128）
    for rank in ("r2", "r8", "r32", "r64"):
        s = flip.get(rank, {}).get("coco|text_only")
        if s:
            rows.append((f"COCO128 {rank} text_only", s["mean"],
                         f"recomputed_tables.json:dataset_flip.{rank}.coco|text_only.mean",
                         f"recomputed_tables.json:dataset_flip.{rank}.coco|text_only.mean",
                         0.001))
    # ③ VLM 13 seed
    for arm, rel, sd in (("text_only", vl["text_only"]["dg_rel_mean"], vl["text_only"]["dg_rel_sd"]),
                         ("vision_only", vl["vision_only"]["dg_rel_mean"], vl["vision_only"]["dg_rel_sd"]),
                         ("both", vl["both"]["dg_rel_mean"], vl["both"]["dg_rel_sd"])):
        rows.append((f"VLM13 {arm} DG*%", rel,
                     f"vlm_bf16_detail.json:summary.{arm}.dg_rel_mean",
                     f"vlm_bf16_detail.json:summary.{arm}.dg_rel_mean", 0.1))
        rows.append((f"VLM13 {arm} DG*% sd", sd,
                     f"vlm_bf16_detail.json:summary.{arm}.dg_rel_sd",
                     f"vlm_bf16_detail.json:summary.{arm}.dg_rel_sd", 0.1))

    print(f"=== 将写入 {len(rows)} 条断言 ===")
    for r in rows[:6]:
        print(f"  {r[0]:<34} {r[1]}")

    block = ["    # ── ①e 重算后的最终数字（5 seed / batch 128 / VLM 13 seed）（2026-10-11）──",
             '    _rt = json.loads(io.open(REPO / "outputs/analysis/recomputed_tables.json",',
             '                             encoding="utf-8").read())',
             '    _vl13 = json.loads(io.open(REPO / "outputs/analysis/vlm_bf16_detail.json",',
             '                              encoding="utf-8").read())["summary"]',
             "    for _lab, _val, _path in ("]
    for lab, val, p1, p2, tol in rows:
        block.append(f'            ("{lab}", {val}, "{p2}"),')
    block.append("    ):")
    block.append('        _v = _rt')
    block.append('        for _k in _path.split(":")[1].split("."):')
    block.append('            if "|" in _k:')
    block.append('                _kk = _k.split("|")')
    block.append('                _v = _v[_kk[0]][_kk[1]]')
    block.append('            else:')
    block.append('                _v = _v[_k]')
    block.append('        if isinstance(_v, dict):')
    block.append('            _v = _v.get("mean", _v.get("dg_rel_mean"))')
    block.append('        claim(_lab, float(_val), float(_v), _path, tol=0.01)')
    block.append("")

    t2 = t[:i] + "\n".join(block) + t[k:]
    try:
        ast.parse(t2)
    except SyntaxError as e:
        print(f"  ❌ 语法错误: {e}")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    print(f"  ✅ 台账已同步（{len(rows)} 条）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
