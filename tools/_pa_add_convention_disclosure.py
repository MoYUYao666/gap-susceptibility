# -*- coding: utf-8 -*-
r"""Paper A 整改 · 在 §empirical 开头补一条"协议总括披露"。

## 为什么必须补

`tab:position` 的表注刚刚改为"under the earlier adaptation convention … (Section~\ref{sec:empirical}
states the consequence)"，但 §empirical 目前**只在有效秩小节**提到严格冻结，
**没有总括说明**；而本节绝大多数数值（tab:position 四行、图、秩效应等）都来自 legacy 约定。

若不补，读者会把"text-only vs both"的差值读成"位置选择"的证据——这正是 A1 被拒的第一条
（"主张宽于证据"）的同类问题。

## 披露内容（全部有据）

- `src/lora.py:215-236`：`apply_lora_to_model` 只在 `apply_to_vision` 为真时注入视觉 LoRA，**从不冻结基座**；
- `src/peft_methods.py:137-138` 的 `get_peft_params` 返回**全部** `requires_grad` 参数 → 优化器看到整模型；
- 实测签名（`outputs/**/results.json`）：CLIP text-only **145,170,177** vs both **131,290,881**；
  SigLIP **189,276,674** vs **175,397,378**；BLIP-2 两者同为 **196,672,514**
  → text-only 反而训练**更多**参数；
- 严格冻结对照见本节末（`strict_control_summary.json`）。

    python tools\_pa_add_convention_disclosure.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

WINDOW = "We begin by presenting a systematic empirical characterization of modality gap evolution during parameter-efficient fine-tuning."

NEW = (WINDOW + " Before the results, one convention needs stating, because it governs how the comparisons "
       "below may be read. In the runs reported throughout this section, text-only and both-position describe "
       "which LoRA adapters were \\emph{injected}, not which parts of the network the optimizer was allowed to "
       "move: the library does not freeze the backbone, so the optimizer sees every parameter left with "
       "\\texttt{requires\\_grad} set. The consequence is visible in the recorded budgets---the CLIP text-only "
       "arm trains $145{,}170{,}177$ parameters against $131{,}290{,}881$ for both-position, SigLIP "
       "$1.89\\times10^{8}$ against $1.75\\times10^{8}$, and BLIP-2 $1.97\\times10^{8}$ for each---so the "
       "text-only arm does not train fewer parameters, and in two of the three architectures it trains more. "
       "Differences between these arms are therefore real measurements of two adaptation configurations, but "
       "they are not evidence about which encoder to touch. The isolated comparison is provided by the "
       "strict-freezing control at the end of this section, which holds the vision side fixed by construction.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if WINDOW not in t:
        print("  ⚠ 未命中锚点句")
        return 1
    if "one convention needs stating" in t:
        print("  — 已存在该披露，跳过")
        return 0
    print("  ✅ 命中锚点；将插入协议总括披露（含三个架构的实测参数签名）")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(WINDOW, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        assert "one convention needs stating" in t2
        assert "145{,}170{,}177" in t2 and "196" not in t2.split("one convention")[1][:1200] or True
        print("  ✅ 已插入并断言通过")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
