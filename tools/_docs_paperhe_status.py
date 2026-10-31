# -*- coding: utf-8 -*-
r"""落账：`paper合` 状态清点 + OpenCLIP 效应量修正（2026-10-10）。

    python tools\_docs_paperhe_status.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📊 2026-10-10 —— `paper合` 状态清点 + OpenCLIP 效应量**修正**（我先前的"2×"是错的）**
>
> ### 一、`paper合` 现在处于什么状态
>
> | 项 | 状态 |
> |---|---|
> | 编译 | **Springer 40 页 / NC 54 页**｜**0 错误、0 未定义引用、0 Overfull** |
> | 门禁 `_claim_ledger.py` | ✅ **46/46 通过**（退出码 0） |
> | seed 覆盖 | **三骨干 × 三臂 × 3 seed 全齐**（B/32 r4、B/16 r4、OpenCLIP r4 各 9 run） |
> | 目标刊 | **未投**。候选（免 APC + 无拒稿史）：**ESWA / KBS / CVIU**（`docs/PAPERA_VENUE_DECISION.md`） |
> | 投稿包 | `paper合/NC_submission/`（已有） |
>
> ### 二、✅ 本轮真正**解决**掉的（相对本会话开始）
>
> | 风险 | 处置 |
> |---|---|
> | **B1** patch-size 归因错误 | ✅ **改按预训练目标分组**，表注写明"patch size 不分离两组" |
> | **B3** OpenCLIP 效应量 | ✅ **本轮重算并修表注**（见下） |
> | **B4** COCO 下 `DG*` 不动 | ✅ 写入 **Fourth** limitation（含实测 0.003–0.006） |
> | **C1** COCO ODE 表 | ✅ **撤回**，理由写入补充材料 D 节 |
> | **C2** 单 seed | ✅ **已补到 3 seed**（三骨干 × 三臂） |
> | **C3** 解码器 VLM 单模型/单 seed/4-bit | ⚠️ **部分**：补了"框架在解码器 VLM 上成立"（补充材料 E 节），**但仍是单模型、单 seed、4-bit**（已如实标注三点） |
> | **C4** `α` 预测 | ✅ **核查后确认论文表述准确**（6/6 同号、中位误差 34%、排序已验证不一致并写明） |
> | **C5** 4-bit vs bf16 | ✅ 写作说明（bf16 下 `vision_only` 不可行，故三臂统一用 4-bit） |
> | **C6** 训练规模小 | ✅ 已在 limitation 标注"测排序方向，非最终性能" |
> | **C7** `Γ_m` 未在解码器 VLM 验证 | ✅ **本轮完成**（硬校验通过：冻结侧梯度严格为 0） |
> | **新增** | ✅ `dg_pred` 偏差写入 **Sixth** limitation（2.44× / 3.33× / +0.225 / 2-of-5） |
> | **新增** | ✅ `Γ_m` 蒙特卡洛噪声写入补充材料 C 节（sd 27–49 vs 均值 18–32） |
>
> ### 三、🔴 本轮**修正了我自己写错的一处**（重要）
>
> 我 2026-10-08 在表注里写：
> *"On OpenCLIP the gap between adjacent arms is … **at about twice the archived
> seed-to-seed deviation**"* —— **"twice" 是错的。**
>
> **根因**：那个说法用了**错误的参照量**（拿 CLIP B/32 r8 的**跨臂** sd = 0.0030 当分母）。
>
> **按逐臂 sd 重算**（`tools/_p92_oclip_effectsize.py`，OpenCLIP 现已 3 seed）：
>
> | 相邻臂 | \|Δmean\| | 合并 sd | **效应量** |
> |---|---|---|---|
> | `text_only` vs `both` | 0.0092 | 0.0175 | **0.52 sd** |
> | `both` vs `vision_only` | 0.0105 | 0.0192 | **0.55 sd** |
> | `text_only` vs `vision_only` | 0.0197 | 0.0186 | 1.05 sd |
>
> **对照**：CLIP B/32 r4 相邻 = **7.5 / 13.2 sd**｜CLIP B/16 r4 = **4.7 / 1.2 sd**
>
> **→ OpenCLIP 的相邻臂差异**小于一个 sd**（0.52 / 0.55）→ **统计上不成立**。
> **表注已改为实测值**，并明确写："**the arm ordering on this backbone is not resolved
> and we do not rest any conclusion on it**"（三臂均值 +0.066 / +0.075 / +0.086）。
>
> ### 四、仍未解决的（**诚实的剩余项**）
>
> | # | 项 | 性质 |
> |---|---|---|
> | **C3** | 解码器 VLM：**单模型、单 seed、4-bit** | 需新实验（云端已证明不可用于本任务） |
> | **B2** | COCO 的 `text_only` 3 个秩未测（`both` 9 配置齐备） | 可选加固 |
> | **新** | `f(DG₀)` 与 `α_fit` **方向相反、量级差 2.4×**（`tools/_p86`） | **未写入论文**（`dg_pred` 的偏差已写，但这一条更根本） |
> | **新** | 驱动项轨迹：三臂**极差 16.53%**，**排序与实测不一致** | **未写入论文** |
>
> ### 五、我建议的解决路径（按优先级）
>
> | 序 | 动作 | 成本 | 解决什么 |
> |---|---|---|---|
> | 1 | **把 `f(DG₀)` 与驱动项排序的那两条也写进 limitation** | **~30 min** | 把理论层的两处否证**如实写明**——这是"可被否证"的兑现，**增强而非削弱论文** |
> | 2 | **补 COCO 的 `text_only` 3 个秩**（B2） | ~5 h（本地） | 让"数据集翻转"那张表两臂齐备 |
> | 3 | **投 ESWA**（免 APC、无拒稿史、scope 合） | ~1 h | **把稿子投出去**——它已具备可投状态 |
> | 4 | 解码器 VLM 补 seed/补模型（C3） | 需可用 GPU | 进一步加固 |
>
> **→ 我的建议：先做 1（30 min，把两处否证写明），再立刻做 3（投出去）。
> 2 与 4 可以边投边补（Elsevier 允许投稿后补材料）。**
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "`paper合` 状态清点" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("`paper合` 状态清点", "0.52 sd", "0.55 sd", "\"twice\" 是错的",
              "the arm ordering on this backbone is not resolved", "投 ESWA"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
