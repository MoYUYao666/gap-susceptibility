# -*- coding: utf-8 -*-
r"""把 COCO 新数据与表注修正加进门禁台账（2026-10-10）。

新增主张（全部来自 `outputs/analysis/dataset_flip_strict.json`）：
- Flickr30k r4 `text_only = −0.0288 ± 0.0013`｜`both = −0.0188 ± 0.0004`
- COCO r4 `text_only = −0.0414 ± 0.0015`｜`both = −0.0886 ± 0.0026`
- COCO `text_only` 全秩：r2 −0.0488｜r8 −0.0944｜r32 −0.1315｜r64 −0.1396

    python tools\_pa_ledger_coco.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_claim_ledger.py"
ANCHOR = "    # ── ①e 两处理论否证"

ADD = '''    # ── ①f 数据集翻转（严格冻结，r4；2026-10-10 COCO text_only 补齐）──
    _fl = json.loads(io.open(REPO / "outputs/analysis/dataset_flip_strict.json",
                             encoding="utf-8").read())
    for _k, _v in (("Flickr30k|text_only", -0.0288), ("Flickr30k|both", -0.0188),
                   ("COCO|text_only", -0.0414), ("COCO|both", -0.0886)):
        claim(f"r4 {_k} ΔCG", _v, _fl["r4"][_k]["mean"],
              f"dataset_flip_strict.json:r4.{_k}.mean", tol=0.001)
    for _k, _v in (("Flickr30k|text_only", 0.0013), ("COCO|both", 0.0026)):
        claim(f"r4 {_k} sd", _v, _fl["r4"][_k]["sd"],
              f"dataset_flip_strict.json:r4.{_k}.sd", tol=0.0005)
    # COCO text_only 全秩（论文新写的趋势句）
    _tr = [("r2", -0.0488), ("r8", -0.0944), ("r32", -0.1315), ("r64", -0.1396)]
    for _r, _v in _tr:
        _xs = []
        import glob as _g
        for _f in sorted(_g.glob(str(REPO / f"outputs/coco_sweep_text_only/{_r}/text_only/seed*/results.json"))):
            _d = json.loads(io.open(_f, encoding="utf-8").read())
            _xs.append(_d["final_gap"]["centroid_gap"] - _d["initial_gap"]["centroid_gap"])
        import statistics as _st
        claim(f"COCO text_only {_r} ΔCG", _v, _st.mean(_xs),
              f"coco_sweep_text_only/{_r}/text_only/seed*/results.json:mean", tol=0.001)

''' + ANCHOR


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "数据集翻转（严格冻结，r4" in t:
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
    print("  ✅ 已加 10 条主张")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
