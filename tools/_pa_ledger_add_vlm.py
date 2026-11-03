# -*- coding: utf-8 -*-
r"""把实验 ④ 的数字加进门禁台账（2026-10-08 21:55）。

## 为什么

论文新增了（`discussion.tex` 的 scope 句 + `supplement.tex` 的 E 节）：
- 相对降幅 **83.8% / 73.9% / 11.0%**；
- 起点相差 **3.4 倍**（0.6364 vs 2.1759）；
- `n_trainable` 三个值。

**唯一原则：每个数字必须指名来源。** 故加进 `tools/_claim_ledger.py`。

    python tools\_pa_ledger_add_vlm.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_claim_ledger.py"

ANCHOR = "    # ── ② ODE 台账（逐 run 拟合）"

ADD = '''    # ── ①c 解码器 VLM（实验 ④，2026-10-08 加入 discussion 与 supplement E 节）──
    qv = json.loads(io.open(REPO / "outputs/analysis/qwen_verdict.json",
                            encoding="utf-8").read())
    for _arm, _paper_rel in (("both", 0.838), ("text_only", 0.739), ("vision_only", 0.110)):
        claim(f"Qwen2-VL {_arm} DG* 相对降幅", _paper_rel,
              qv["rows"][_arm]["rel"], "qwen_verdict.json:rows.<arm>.rel", tol=0.002)
    claim("Qwen2-VL 三臂起点比", 3.4, qv["start_ratio"],
          "qwen_verdict.json:start_ratio", tol=0.06)
    for _arm, _paper_n in (("both", 14494912), ("text_only", 9232384), ("vision_only", 5262528)):
        claim(f"Qwen2-VL {_arm} n_trainable", float(_paper_n),
              float(qv["n_trainable"][_arm]) if "n_trainable" in qv
              else float(json.loads(io.open(
                  REPO / f"outputs/vlm_strictfreeze/{_arm}_seed42.json",
                  encoding="utf-8").read())["n_trainable"]),
              f"vlm_strictfreeze/{_arm}_seed42.json:n_trainable", tol=0.6)

''' + ANCHOR


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "解码器 VLM（实验 ④" in t:
        print("  已加，跳过")
        return 0
    if t.count(ANCHOR) != 1:
        print(f"  ❌ 锚点未唯一命中（{t.count(ANCHOR)}）")
        return 1
    if not apply:
        print("  （预演）")
        return 0
    t = t.replace(ANCHOR, ADD, 1)
    ast.parse(t)
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    print("  ✅ 已加 7 条主张（3 相对降幅 + 1 起点比 + 3 n_trainable）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
