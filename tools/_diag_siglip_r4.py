# -*- coding: utf-8 -*-
r"""诊断 SigLIP `s7_siglip_lora_r4_text_only` 的两个异常（2026-10-04）。

## 异常

1. **结果落在 `outputs/siglip/`（默认目录）而非 `outputs/siglip_strict/seed*/`** → 5 个 seed 写同一文件、互相覆盖；
2. **`n_trainable_params = 147,456`**，而按 CLIP 的口径推算 text_only/rank4 应为 **98,304**
   （$2\times r\times 512\times 24$）。
3. **结果里 `seed` 字段为 `None`** → 无法追溯是哪个 seed。

## 本脚本查什么

- `SIGLIP_EXPERIMENTS` 里 `s7_siglip_lora_r4_text_only` 的实际 LoRA 配置；
- SigLIP 的 LoRA 注入层数（视觉/文本各多少）；
- 由配置反推期望的可训参数，与实测 147,456 对照。

    python tools\_diag_siglip_r4.py
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "experiments" / "siglip_experiments.py"


def main() -> int:
    t = io.open(F, encoding="utf-8").read()

    print("=== ① SIGLIP_EXPERIMENTS 里的 s7 配置 ===")
    i = t.find("SIGLIP_EXPERIMENTS")
    seg = t[i:t.find("]", i) + 1]
    for l in seg.splitlines():
        if "s7_" in l or ("LoRAConfig" in l and "rank=4" in l):
            print("  " + l.strip()[:140])

    print("\n=== ② 结果文件里 `seed` 字段从哪来 ===")
    # 找把结果写进 json 的片段
    m = re.search(r"result\s*=\s*\{[\s\S]{0,900}?\n    \}", t)
    if m:
        for l in m.group(0).splitlines()[:24]:
            print("  " + l[:130])
    else:
        for mm in re.finditer(r'"experiment"\s*:', t):
            s = t.rfind("\n", 0, mm.start() - 400)
            print("  …" + t[mm.start() - 260:mm.start() + 320].replace("\n", " ")[:520])

    print("\n=== ③ LoRA 注入的层数（视觉/文本）===")
    for l in t.splitlines():
        if "视觉编码器" in l or "文本编码器" in l or "个 LoRA 层" in l:
            print("  " + l.strip()[:120])

    print("\n=== ④ 期望值推算 ===")
    print("  SigLIP text hidden = 768（SigLIP text_config.hidden_size）")
    print("  text_only rank4: 2 × 4 × 768 × n_text_lora_layers")
    for nlayer in (12, 24):
        print("    n=%d → %d" % (nlayer, 2 * 4 * 768 * nlayer))
    print("  实测 147,456 = 2 × 4 × 768 × %d" % (147456 // (2 * 4 * 768)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
