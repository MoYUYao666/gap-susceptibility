# -*- coding: utf-8 -*-
r"""落账：六项实验的当前状态（2026-10-07 夜）。

    python tools\_docs_exp_status.py [--apply]
"""
from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def sh(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception as e:
        return f"(失败 {e})"


def main() -> int:
    apply = "--apply" in sys.argv
    gpu = sh(["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu",
              "--format=csv,noheader"])
    b16 = (REPO / "models" / "clip-vit-base-patch16").exists()
    log = REPO / "outputs" / "theory" / "alpha_from_gradients" / "run_both.log"
    ep = 0
    if log.exists():
        ep = len([l for l in io.open(log, encoding="utf-8", errors="ignore")
                  if " DG*=" in l and "ep" in l])

    print(f"  GPU      : {gpu}")
    print(f"  CLIP B/16: {'✅ 已就位' if b16 else '⏳ 下载中/未完成'}")
    print(f"  α 实验   : {ep}/30 epoch")

    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    ent = f"""> **📊 2026-10-07 夜 —— 六项实验状态总览（实测）**
>
> | # | 实验 | 成本 | 解决 | 状态 |
> |---|---|---|---|---|
> | 1 | 逐 epoch 梯度 → **预测 α**（both 臂） | ~1 h | ①（最致命） | ⏳ **运行中 {ep}/30 epoch** |
> | 2 | **留一配置交叉验证** | 近零 | ① | ✅ **完成**（LoRA 族内 R²=**0.745**、中位 **0.952**、corr(α)=**0.640**） |
> | 3 | patch-16 骨干 + 多 rank | 2–3 h | ③ | ⏸ **排队**（模型{'已就位' if b16 else '**下载中**'}） |
> | 4 | 解码器 VLM 对照（Qwen2-VL 三臂） | 3–4 h | ④ | ⏸ **排队**（前置**分塔验证已完成**） |
> | 5 | **monitor DG 早停准则** | 近零 | ⑤ | ✅ **完成**（监控有效 r=−0.71；**早停不成立**，论文已改） |
> | 6 | 第二组数据集（非自然图像） | 近零 | ② | ✅ **完成**（方向支持 3/4，**幅度极小**；**不给论文加码**） |
>
> ### 🔴 硬约束（实测）
>
> **GPU 只有 8 GB**：`nvidia-smi` = **{gpu}**
> → **只能容纳一个实验**，③ 与 ④ **必须串行**，且都须**排在 α 之后**。
>
> ### 本阶段的自我修正（三次，均记录在案）
>
> | # | 我错在哪 | 更正 |
> |---|---|---|
> | 1 | LOCO **混方法池** → "不能外推" | 限 LoRA 族内 → **可外推** |
> | 2 | monitor DG 用**事后择优** | 改**可实现规则** → 结论反向（早停仍不成立，但理由不同） |
> | 3 | 实验 ⑥ 用 **\\|CGΔ\\| 最小** 当"保护" | 按论文定义（**CGΔ 最负**）→ 结论从 0/4 变 **3/4** |
>
> **三次的共同点**：**先用一个方便的定义，再发现它与论文/可部署性不符。**
> **对策**：判据**事先写明**（已写进各脚本的 docstring）。
>
> ### 顺带查出的既有错误
>
> `clip_vlm_vision_instruction_dynamics.py:142` 的 LoRA 目标
> `q/k/v/o_proj` + `gate/up/down_proj` **在 Qwen2-VL 视觉塔里一个都没有**
> → 该配置实为**文本侧**，而它被称作"both"。**脚本注释与 A2 论文描述需更正。**
"""
    if "六项实验状态总览（实测）" not in h:
        anchor = "> **🧪 2026-10-07 深夜 —— 实验 ⑥（非自然图像域零样本外部效度）"
        i = h.find(anchor)
        assert i > 0, "未找到 HANDOFF 锚点"
        io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ent + "\n" + h[i:])
        h2 = io.open(hp, encoding="utf-8").read()
        for k in ("六项实验状态总览", "0.745", "监控有效", "方向支持 3/4", "视觉塔里一个都没有"):
            assert k in h2, f"HANDOFF 断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
