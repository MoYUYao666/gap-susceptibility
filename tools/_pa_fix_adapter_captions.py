# -*- coding: utf-8 -*-
r"""Paper A 整改 · 修两处与已改正文矛盾的图注（Adapter 的主张）。

## 核实（`outputs/analysis/adapter_common_baseline.json` 逐 run 重算）

冻结基线 `frozen_reference_cg = 0.8184`；旧口径为"各 run 自身注入后基线"。

| run | dCG_old | **dCG_common** | R@1 |
|---|---|---|---|
| `adapter_d64_text` | −0.2167 | **+0.0636** | 0.574 |
| `adapter_d32_text` | −0.2041 | **+0.1029** | 0.458 |
| `adapter_d16_text` | −0.0462 | **+0.2368** | 0.072 |
| **`adapter_d16_both`** | −0.0399 | **+0.5003** | **0.002** |
| `adapter_d16_vis` | −0.0834 | **+0.1806** | 0.036 |
| text-only 组（n=5） | −0.1155 | **+0.1848** | 0.235 |

**结论（与正文 `validation.tex:111` 的修正一致）**：
1. **所有 Adapter 变体在共同基线下都使间隙增大**（无负数）；
2. **text-only 不优于 both**：`d16` 下 text(+0.2368) 明显差于 both(+0.5003)；
   d=64 时 text(+0.0636) 与 d=16 both(+0.5003) 不可直接比（维度不同）；
3. **both 的 R@1 = 0.002（检索随机水平）**——该 run 本身不是一次成功的适配，
   所以"both 更优"这一读数也不可当真。**Adapter 的位置证据整体不可靠**。

## 需修的两处图注

| 图注 | 原称 | 改为 |
|---|---|---|
| `fig:crossmethod` | "LoRA and Adapter **both benefit from text-only** training" | 按数据描述：两者都随位置变化，但 **Adapter 无一致的 text-only 优势** |
| `fig:adapter_layered` | "Text-only **preserves CG better** than text+vision Adapter" | 改为按实测描述（text+Vis-L1 达 frozen 级 CG） |

    python tools\_pa_fix_adapter_captions.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
S = REPO / "paper合" / "sections"

EDITS: list[tuple[str, str, str, str]] = [
    ("empirical.tex",
     "\\caption{Cross-method comparison. LoRA and Adapter both benefit from text-only training, but "
     "exhibit opposite rank-dimension scaling.}",
     "\\caption{Cross-method comparison. Both methods respond to where the adapters sit and to their "
     "dimension, but the direction differs: LoRA favours the text-only setting, whereas for Adapter no "
     "consistent text-only advantage is present once every run is scored against a common frozen "
     "baseline (Section~\\ref{sec:validation}).}",
     "fig:crossmethod"),
    ("supplement.tex",
     "\\caption{Adapter layered fine-tuning. Text-only preserves CG better than text+vision Adapter.}",
     "\\caption{Adapter layered fine-tuning. Training an Adapter on the text side only reaches "
     "frozen-level CG while its text+vision counterpart does not; this is a layered-configuration "
     "comparison, and the aggregate cross-dimension comparison in Section~\\ref{sec:validation} does not "
     "reproduce a text-only advantage for Adapter.}",
     "fig:adapter_layered"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    n = 0
    for fname, old, new, why in EDITS:
        p = S / fname
        t = io.open(p, encoding="utf-8").read()
        c = t.count(old)
        if c == 1:
            print(f"  ✅ {fname}: {why}")
            if apply:
                io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
            n += 1
        elif c == 0:
            print(f"  ⚠ {fname}: 未命中（{why}）")
        else:
            print(f"  ⚠ {fname}: 命中 {c} 次，拒绝改动（{why}）")
    print(f"\n{n}/{len(EDITS)} 处{'已改' if apply else '可改'}")
    if apply:
        bad = []
        for f in S.glob("*.tex"):
            tt = io.open(f, encoding="utf-8").read()
            for pat in ("both benefit from text-only training",
                        "Text-only preserves CG better than text+vision Adapter"):
                if pat in tt:
                    bad.append(f"{f.name}:{pat}")
        assert not bad, f"仍有矛盾图注：{bad}"
        print("✅ 断言通过：两处矛盾图注已消除")
    else:
        print("（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
