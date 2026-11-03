# -*- coding: utf-8 -*-
r"""落账 + 改稿：Adapter 的 `up.bias` 实现疏漏（2026-10-12）。

## 核实（我独立复核，非转述）

`tools/_p296_adapter_init_check.py` → `outputs/analysis/pr_adapter_init_check.json`：

| | zero-shot | CG | R@1 |
|---|---|---|---|
| 出厂插入 | **0.15%** | **1.2065** | 0.0015 |
| 把 `up.bias` 置零 | **59.91%** | **0.8155** | 0.1585 |
| 冻结模型 | 59.91% | 0.8157 | 0.1555 |

`bias_stats`：48 个 Adapter 层，`up_weight_all_zero = true`，
`up_bias_abs_mean = 0.0630`、`up_bias_abs_max = 0.1250` = **`nn.Linear` 默认均匀界 0.125**。

**代码层**（我直接读源码核对）：
- `src/peft_methods.py:18`（论文主路径）：`nn.init.zeros_(self.up.weight)` —— **只零权重，未碰 bias**
- `tools/clip_peft_gamma_ordering.py:74`（后来实现）：**`nn.init.zeros_(self.up.bias)`** —— 做了

→ **实现疏漏，非方法属性。**

    python tools\_p346_adapter_bias_note.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "discussion.tex"

ENT = """> **🔬 2026-10-12（续）—— Adapter「插入即破坏」查实为**实现疏漏**（`up.bias` 未初始化）**
>
> ### 现象
>
> task-6 测到瓶颈 Adapter **插入即把 CG 推 +0.4460、R@1 从 0.1555 掉到 0.0010**
> （与仓库既有 `adapter_common_baseline.json` 的 `dCG_common_mean = +0.1848` 同向）。
>
> ### 根因（`tools/_p296_adapter_init_check.py`，我已独立复核）
>
> | | zero-shot | CG | R@1 |
> |---|---|---|---|
> | **出厂插入** | **0.15%** | **1.2065** | 0.0015 |
> | **内存中把 `up.bias` 置零** | **59.91%** | **0.8155** | 0.1585 |
> | 冻结模型 | 59.91% | 0.8157 | 0.1555 |
>
> → **置零 `up.bias` 后精确恢复冻结模型**（CG 差 0.0002）。
>
> `bias_stats`：**48 个 Adapter 层**；`up_weight_all_zero = true`；
> `up_bias_abs_mean = 0.0630`、`up_bias_abs_max = 0.1250`
> = **`nn.Linear` 默认均匀初始化界 0.125**（即**从未被初始化**）。
>
> ### 代码层确认（直接读源码）
>
> | 文件 | `up` 的初始化 | 结论 |
> |---|---|---|
> | **`src/peft_methods.py:18`**（论文主路径，2026-06-19） | `nn.init.zeros_(self.up.weight)` | 🔴 **只零权重，漏了 bias** |
> | `tools/clip_peft_gamma_ordering.py:74`（后来实现，2026-09-13） | `nn.init.zeros_(self.up.bias)` | ✅ 做了 |
>
> **→ 判断：实现疏漏，不是设计属性。** 代码零初始化 `up.weight` 以求近恒等插入，
> **却把 `up.bias` 留在 `nn.Linear` 的随机默认值** → wrapper 在插入时**不是恒等**。
>
> ### 与稿中既有处理的关系
>
> `validation.tex:126` **早已**说明：旧约定测出的 text-only Adapter "reduction of $0.217$"
> **不得与 LoRA 数字比较**，并已统一改用 common frozen baseline。
> **`_p296` 是那条处理的独立复现 + 根因定位**——它解释了**为什么** Adapter 从自身
> post-injection 状态起算会给出错误符号。
>
> ### 本轮据此加入稿中的新限制（`discussion.tex`）
>
> 如实写明：**瓶颈 Adapter 在仓库当前实现下插入时不是恒等映射**（`up.bias` 未初始化，
> 后续实现已修正），故 Adapter 的 Cross-Gap 变化**与 LoRA 不具可比性**；
> 并说明这**不是方法本身的缺陷**。
>
> ### 与「子集匹配」那条并列的教训
>
> 本轮两次"看起来很严重的发现"最后都需要区分**实现问题 / 归档元数据问题 / 真正的方法问题**：
> - Adapter 插入破坏 → **实现疏漏**（可精确定位到一行初始化）
> - `tab:position_strict` 的 R@1 漂移 → **归档元数据问题**（`experiment` 字段重名）+ **2 格无来源**
> - **真正的方法层面结论**（ΔCG 12/12 精确、LoRA vs full-FT 不可区分、Visual Fragility 不成立）**均未被推翻**
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # 1) HANDOFF
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "Adapter「插入即破坏」查实为" not in t:
        i = t.find("# 项目交接文档")
        j = t.find("\n", i)
        io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
        print("  ✅ HANDOFF 已追加")
    else:
        print("  HANDOFF 已记录")

    # 2) discussion.tex 的限制条
    t = io.open(F, encoding="utf-8", errors="replace").read()
    anchor = r"Tenth, our cross-method comparison is made at one shared learning rate"
    if "up.bias" in t:
        print("  discussion 已含该限制")
    elif anchor in t:
        ADD = (
            "\n\n"
            r"Eleventh, the bottleneck Adapter is not an identity map at insertion in the "
            r"implementation this repository uses for it: \texttt{src/peft\_methods.py} "
            r"zero-initialises \texttt{up.weight} but leaves \texttt{up.bias} at its "
            r"\texttt{nn.Linear} default, and zeroing that bias in memory restores the frozen "
            r"model exactly (zero-shot $0.15\%\to59.91\%$, $\mathrm{CG}$ "
            r"$1.2065\to0.8155$). A later implementation in the same repository "
            r"(\texttt{tools/clip\_peft\_gamma\_ordering.py}) does zero it. This is an "
            r"implementation oversight rather than a property of bottleneck adapters, but it "
            r"means Adapter Cross-Gap changes in this work are measured from a perturbed "
            r"reference and are therefore not comparable with the LoRA figures; "
            r"Section~\ref{sec:validation} already restricts the Adapter comparison to the "
            r"common frozen baseline for the same reason.")
        if a.apply:
            bak = F.with_suffix(".tex.bak_p346")
            if not bak.exists():
                shutil.copy2(F, bak)
            io.open(F, "w", encoding="utf-8", newline="").write(t.replace(anchor, anchor + ADD, 1))
            print("  ✅ discussion 已加入 Eleventh 限制")
        else:
            print("  （预演）discussion 将加入 Eleventh 限制")
    else:
        print("  🔴 找不到 Tenth 限制锚点")

    if not a.apply:
        print("  （预演）")
        return 0
    t2 = io.open(hp, encoding="utf-8").read()
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    checks = {
        "HANDOFF 含根因表": "出厂插入" in t2 and "1.2065" in t2,
        "HANDOFF 含代码层对比": "nn.init.zeros_(self.up.bias)" in t2,
        "HANDOFF 含'非方法属性'": "不是设计属性" in t2 or "非方法属性" in t2,
        "discussion 含 up.bias 限制": "up.bias" in t3,
        "discussion 含不具可比性": "not comparable with the LoRA figures" in t3,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
