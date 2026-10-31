# -*- coding: utf-8 -*-
r"""把「SigLIP r4 落错目录 + seed 覆盖」的事件记进 HANDOFF（2026-10-04）。

    python tools\_docs_siglip_r4_incident.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENTRY = r"""> **🔧 2026-10-04 上午 —— 修两处 bug（其一让 SigLIP r4 数据被覆盖），并完成 k 的最终重测**
>
> ### ① `k` 重测完成（覆盖 $r\in[1,64]$）—— 结论：**平坦成立，但斜率不可复现且不应报**
>
> both 臂 6 个 rank 齐备后重测（严格冻结，3 seeds 平均）：
>
> | rank | 1 | 4 | 8 | 16 | 32 | 64 |
> |---|---|---|---|---|---|---|
> | $\|g_v\|$ | 13.037 | 12.754 | 13.369 | 13.127 | 14.093 | 13.815 |
>
> - **「平坦」成立且裕度极大**：极差 **10%**，而 $\sqrt r$ 预测应变化 **8 倍（800%）** → 实测比预测小约 **80 倍**；
> - **论文的 $k=0.043$ 无法复现**（线性拟合得 0.257）；
> - **但斜率本身不应报**：相邻区间局部斜率为 **−0.20 / +0.89 / −0.35 / +1.39 / −0.40**，**正负交替** →
>   无可辨趋势，任何斜率都只是噪声残差。**正确陈述**是「区间 12.75–14.09 vs $\sqrt r$ 预测 8 倍」。
>
> 详见 `docs/K043_INVESTIGATION.md`（已追加最终结论）。产物 `outputs/analysis/k_remeasured_both.json`。
>
> ### ② Bug：`strict_freeze_control.py` 的护栏过紧，误杀 rank64/both
>
> `assert self.strict_n < 2_000_000` 是按 rank8/text-only（196,608）定的；**rank64/both 合法地是 3,932,160**
> → 被误杀。**（讽刺的是 `siglip_experiments.py` 里早已写对不变量「可训参数必须全属 LoRA 矩阵」，
> 我没同步过来。）** 已改为检查 `non_lora == 0` + 按配置推算上界。
>
> ### ③ Bug：runner 在失败步骤上白等 6 小时
>
> 步骤失败后 `wait_until()` 不知道命令已死，仍轮询到超时 → **2026-10-03 整晚浪费**，SigLIP/OpenCLIP 一步未跑。
> 已加**静默检测**（产物 N 分钟无增长即判失败并跳下一步）。
>
> ### ④ Bug（本次新发现）：SigLIP r4 结果落错目录 + **5 个 seed 互相覆盖**
>
> `tools/_run_siglip_r4.py` **没传 `--outputs_dir`** → 结果落到默认 `./outputs/siglip`，
> **5 个 seed 写同一文件**，只剩最后一个 seed 的数据 —— **违反「数据来源必须明确」**。
> 且 runner 的完成判据查 `outputs/siglip_strict/*`，与落盘位置不符 → 26 分钟「静默」被误判失败。
>
> **处置**：删除了那两个被覆盖的文件（来源不明确）；改写 runner **每 seed 传独立
> `--outputs_dir outputs/siglip_strict/seed<SEED>`**，并加**落盘位置校验**（不在期望路径即报错）。
>
> **顺带澄清一个我先前的误判**：SigLIP 的 text_only/rank4 可训参数是 **147,456**
> （= $2\times4\times\mathbf{768}\times24$），**不是** 98,304 —— 后者是拿 CLIP 的 512 维去套，
> **SigLIP 文本隐藏维是 768**。147,456 是正确的。
>
> ### ⑤ 已完成 / 进行中
>
> | 项 | 状态 |
> |---|---|
> | both r1、both r64 | ✅ 各 3/3 |
> | CLIP r1/r64 text_only | ✅ 各 3/3 |
> | `k` 重测（r∈[1,64]） | ✅ 完成 |
> | **SigLIP r4** | 🏃 重跑中（10 个 run，落盘位置已修正） |
> | OpenCLIP r4 | ⏳ 排队 |

"""


def main() -> int:
    apply = "--apply" in sys.argv
    p = REPO / "HANDOFF.md"
    t = io.open(p, encoding="utf-8").read()
    if "2026-10-04 上午 —— 修两处 bug" in t:
        print("  已记录，跳过")
        return 0
    anchor = "> **🛑 2026-10-03 晚"
    i = t.find(anchor)
    if i < 0:
        print("  ⚠ 未找到锚点")
        return 1
    if apply:
        io.open(p, "w", encoding="utf-8", newline="").write(t[:i] + ENTRY + t[i:])
        t2 = io.open(p, encoding="utf-8").read()
        for k in ("147,456", "5 个 seed 写同一文件", "正负交替", "静默检测"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
