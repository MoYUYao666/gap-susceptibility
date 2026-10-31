# -*- coding: utf-8 -*-
r"""落账：实验 ⑤ 完成 + GPU 串行约束 + α 重跑中（2026-10-07）。

    python tools\_docs_exp5_gpu.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = r"""> **🧪 2026-10-07 深夜 —— 实验 ⑤（monitor DG）完成｜**GPU 只能串行****
>
> 操作者选 B 并指示"所有能补的实验都补上"。六项实验的执行顺序按 **GPU 争用**重排（见下）。
>
> ### ✅ 实验 ⑤：**「monitor DG」有效，但「DG 早停」不成立**
>
> 脚本：`tools/_p3_monitor_dg.py`（v1）、`_p3_monitor_dg2.py`（v2）、`_p3_monitor_dg3.py`（v3）。
> **三版逐版修正了我的方法缺陷**：
>
> | 版本 | 做法 | 缺陷 |
> |---|---|---|
> | v1 | 取 **DG 最小 epoch** 作早停 | **事后择优（oracle）**，部署中不可用 |
> | v2 | 5 种**可实现**早停规则 | ✅ 方法可信，但评价指标是 **CG** 而非 **R@1** |
> | v3 | 改为测**可直接测**的三件事 | ✅ **本版结论** |
>
> **v3 结果（`outputs/analysis/monitor_dg_check3.json`，n=96）**：
>
> | 检验 | 结果 | 支持什么 |
> |---|---|---|
> | **初始 $DG^*$ → 末态 R@1** | **r = −0.708**（p≈0） | ✅ **DG 是有效健康信号** |
> | epoch-1 $DG^*$ 相对变化 → R@1 | r = −0.151（p≈0.14） | ❌ 首步变化无预测力 |
> | **DG 与 CG 的 argmin epoch 一致率** | **42%**（40/96） | ❌ **不能替代任务指标作停止准则** |
> | 5 种可实现早停规则 vs 不早停 | **0/5 更优**（R1: **88/94 更差**） | ❌ 早停无收益 |
>
> **→ 论文设计原则 ③ 已按证据收紧**（`tools/_pa_fix_monitor_dg_claim.py`）：
> 拆成两句——① **监控 DG** 作诊断（附 $r=-0.71$、$n=96$ 证据）；
> ② **明确说明以 DG 作停止准则未获支持**（42% 一致率、5 规则 0 胜）。
>
> ### ⚠️ 归档局限（影响实验 ④ 的设计）
>
> `results.json` / `v1_result.json` **只有末态检索指标，无逐 epoch R@1**
> → **"早停对检索的影响"无法用归档直接测**；本版如实改测可直接测的三件事。
>
> ### 🔴 **GPU 串行约束（实测）**
>
> `nvidia-smi`：**7812 / 8188 MiB，利用率 100%**（α 实验独占）。
> **8GB 显存只能容纳一个实验** → 实验 ③（patch-16 骨干）与 ④（解码器 VLM）
> **必须排在 α 之后串行执行**，不能并行。
>
> ### ⏳ 进行中
>
> **α 预测（both 臂）**：`tools/_p2_alpha_from_gradients.py --arms both --seeds 42,123,456 --epochs 10`
> （操作者选 B 缩小规模）→ 30 个 epoch，**约 3.5 min/epoch ≈ 1.7 h**。
> 已加命令行开关（`--arms/--seeds/--epochs/--maxsamples`），脚本 `tools/_p2_add_cli_flags.py`。
>
> ### 📋 六项实验状态
>
> | # | 实验 | 状态 |
> |---|---|---|
> | 1 | 逐 epoch 梯度 → 预测 α | ⏳ **运行中**（both 臂，~1.7 h） |
> | 2 | 留一配置交叉验证 | ✅ **完成**（LoRA 族内 R²=0.745、中位 0.952、corr(α)=0.640） |
> | 3 | patch-16 骨干 + 多 rank | ⏸ **排队**（等 GPU） |
> | 4 | 解码器 VLM 对照（Qwen2-VL-2B） | ⏸ **排队**（等 GPU） |
> | 5 | monitor DG 早停准则 | ✅ **完成**（见上，论文已改） |
> | 6 | 第二组数据集（非自然图像） | ⏸ 排队 |
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    if "实验 ⑤（monitor DG）完成" in h:
        print("  已记录，跳过")
        return 0
    anchor = "> **🛠️ 2026-10-07 深夜 —— 选项 B 完成"
    i = h.find(anchor)
    assert i > 0, "未找到 HANDOFF 锚点"
    io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ENT + "\n" + h[i:])
    h2 = io.open(hp, encoding="utf-8").read()
    for k in ("monitor DG", "r = −0.708", "42%", "7812 / 8188 MiB", "88/94"):
        assert k in h2, f"HANDOFF 断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
