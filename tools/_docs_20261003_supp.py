# -*- coding: utf-8 -*-
r"""记录 2026-10-03 补充实验完成 + 正文改动（阶段收尾三件套）。

按项目规则：**追加不重写**、每条可复核、过期结论标注而非静默覆盖。

    python tools\_docs_20261003_supp.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENTRY = r"""> **✅ 2026-10-03 —— 补充实验 38/38 全部完成，两条设计模式被改写**
>
> 昨晚起的补充实验全部跑完（OpenCLIP 15 + SigLIP vision_only 5 + rank sweep 18 = **38/38**）。
> 所有 run 的**模型身份与可训参数逐项核对**：
>
> - SigLIP vision_only：`final_gap` 与 text_only **不同**（若非则说明加载错模型）✅
> - rank sweep：`n_trainable` 随 rank 正确变化 —— r4：98,304/245,760 ｜ r16：393,216/983,040 ｜
>   r32：786,432/1,966,080（`--rank` 确认生效）✅
>
> ### ① 三骨干三臂图谱（**同一协议**：5000 样本/10 epochs/rank8+α16/5 seeds/同一 InfoNCE 微调损失）
>
> | 骨干 | text_only | both | vision_only | ΔCG 排序 vs 检索排序 |
> |---|---|---|---|---|
> | CLIP B/32 (WIT) | **−0.0465** / 0.624 | −0.0258 / **0.693** | +0.0106 / 0.680 | **完全反转** |
> | OpenCLIP B/32 (LAION) | **+0.0694** / 0.643 | +0.0881 / **0.680** | +0.0925 / 0.672 | **完全反转** |
> | SigLIP B/16 | +0.0664 / 0.432 | **−0.0114** / **0.619** | +0.0522 / 0.341 | **一致** |
>
> **两个 B/32 骨干的三臂排序逐项相同，且都与检索排序完全反转**（降间隙最好的 text_only 检索最差）；
> **SigLIP 两个排序都不相同**。→ **"哪个位置最优"不跨骨干迁移**。
> 脚本：`tools/_pa_three_arm_stats.py` ｜ 表：`tab:position_strict`（`empirical.tex`）
>
> ### ② 设计模式②"更低 rank 更能保对齐" —— **被反证，已改写**
>
> | rank | legacy 约定（不冻结基座） | 严格冻结（text_only） | 严格冻结（both） |
> |---|---|---|---|
> | 4 | −0.0272 | −0.0285 | −0.0184 |
> | 8 | −0.0304 | −0.0465 | −0.0258 |
> | 16 | −0.0199 | −0.0598 | −0.0149 |
> | 32 | **+0.0010** | **−0.0754** | −0.0032 |
> | 64 | **+0.0121** | 未跑 | 未跑 |
>
> **legacy 下 rank≥32 转正**（原文"lower ranks reduce, higher increase"在其自身约定下成立）；
> **严格冻结下 text_only 单调递减（rank 越高越降间隙），rank 32 处两者符号相反**（+0.0010 vs −0.0754）。
> 严格冻结 3 seeds 方差极小（±0.0019），**非噪声**。
> → **该规则是"基座也在训练"的产物，不是 rank 的性质。**
> 脚本：`tools/_pa_rank_sweep_stats.py`、`tools/_pa_rank_legacy_vs_strict.py`
>
> ### ③ 据此改写的正文位置
>
> | 文件 | 改动 |
> |---|---|
> | `empirical.tex:124` 设计模式①② | ①改为"同一骨干内排序稳定、但优选端不迁移" + 指向 `tab:position_strict`；②改为"**rank 效应依赖训练约定**"并给出两种约定数据 |
> | `empirical.tex:59` | rank 段落改为"LoRA 的 rank 效应是约定产物"，指向 §validation |
> | `empirical.tex:17` 小节标题 | `Core Finding: Text-Only Preserves Alignment` → **`The Position Effect Under the Earlier Convention`**（加约定限定） |
> | `empirical.tex` 新增 | **`tab:position_strict`** 三骨干三臂表 |
> | `validation.tex` SigLIP 段 | 补 vision_only（+0.0522 / R@1 0.341，**两项都最差**） |
>
> ### ④ 编译与合规（改后复核）
>
> NC 版 **41 页**、Springer 版 **30 页**｜均为 **0 错误、0 未定义引用**｜cites 41 / bib 41 全匹配
> 摘要 **244 词** ≤250 ｜ `tools/_pa_final_check_nc.py` 全绿 ｜ 投稿包已重建
>
> ### ⑤ 本阶段踩到并修掉的坑（**都已加断言防线**）
>
> | 坑 | 后果 | 防线 |
> |---|---|---|
> | `--model` 未传入 `TrainConfig.clip_model` | OpenCLIP 整批与 CLIP **逐位相同**、白跑 2.5h | 传入 + `[model-check]` 断言 |
> | rank sweep 三个 rank 共用 `--out-dir` | 后跑的 rank 读到前一个结果并"跳过"，**静默污染** | 驱动脚本改为 `r4/r16/r32` 独立目录 + 脚本内**拒绝**无 rank 标识的 out-dir |
>
> ### ⑥ 仍未解决
>
> - **`k = 0.043`**（`fig:falsification`/`fig:ers` 的 \|g_v\| 对 rank 斜率）：**无法从归档独立复算**，待核。
> - **`empirical.tex:28` 的 legacy 数值**（−0.064 vs −0.032）：与严格冻结不同协议，已在表注披露，未动。
> - **"162 ODE fits"与实测记录数（9）的对应关系**：未逐一重建。
> - **方向反转的归因**：骨干 vs 预训练未完全分离（现有三点支持"结构按骨干、符号按预训练"，n 小）。

"""


def main() -> int:
    apply = "--apply" in sys.argv
    F = REPO / "HANDOFF.md"
    t = io.open(F, encoding="utf-8").read()
    anchor = "> **⏸️ 2026-10-02 14:15"
    i = t.find(anchor)
    if i < 0:
        print("  ⚠ 未找到锚点")
        return 1
    if "2026-10-03 —— 补充实验 38/38" in t:
        print("  已记录，跳过")
        return 0
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t[:i] + ENTRY + t[i:])
        t2 = io.open(F, encoding="utf-8").read()
        for k in ("38/38", "tab:position_strict", "−0.0754", "The Position Effect Under the Earlier Convention"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
