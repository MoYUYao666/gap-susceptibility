# -*- coding: utf-8 -*-
r"""落账：P3 累计修 10 处 + seed 溯源更正（2026-10-12）。

    python tools\_p436_record_p3_round3.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🛠️ 2026-10-12（续 3）—— P3 累计修 10 处；`p3-stats` 完成（task-11）；我更正了一个错误说法**
>
> ### 🔴 我先前的说法是错的，必须更正
>
> 我在上一条里写：*"论文挑的 3 个 seed 恰好全在效应最弱的簇里"* —— **这句隐含"事后挑选"，是错的。**
> `p3-stats` 用 mtime/ctime 溯源（`tools/_p44n`，我已**独立复核** `tools/_p431`）：
>
> | rank | 最早两次 | 第三次 | 其余七个 |
> |---|---|---|---|
> | **r=5** | **123**（08-13 12:26）、**999**（12:58） | **42**（**ctime 08-13 11:53，最早**；mtime 09-09 因被 tf457 复现覆盖后恢复） | 09-12 21:24 起 |
> | **r=6** | 123（14:04）、999（14:25） | 42（**ctime 08-13 13:32，最早**） | 09-12 23:37 起 |
>
> - **`run_full_sweep.py` 硬编码 `SEEDS = [42, 123, 999]`** ✅
> - **E0 每 rank 只切 1 次**（r=5/r=6 时序均为 3930.5×3 → 3921.0×7，**连续块**）✅
> - **我的检查脚本 `_p431` 自身有个 bug**：把 r=5/r=6 混在一个列表取前三 → 得 `[123, 999, 123]` 重复；
>   **分开 rank 后**结论与成员一致
>
> ⇒ **正确说法**：**那 3 个 seed 是最早测的三次（不是挑选）；另外 7 个是后来在另一个数值环境里跑的**
> → **"10-seed 全族"把"环境变化"与"seed 变化"混在了一起**。
> **E0 的两个值（3930.5 / 3921.0）本身就是环境指纹。**
>
> ### 已写入 P3 的内容（`_p432` / `_p433`）
>
> **新增一段 *Seed provenance and a numerical-environment control* + *What replicates* + *Worst case rather than dispersion***：
>
> | 主张 | 已改为 |
> |---|---|
> | shell 环境 | **分层报告两个 E0 块**（不合并） |
> | r=6 | **两簇都全正**（3/3 与 7/7，共 **10/10**）；配对（同 seed）**9/10 正**、**t=5.57（df=9）**、bootstrap CI **[+66.0, +135.2]** |
> | r=5 | **只声明"夹住交叉点"（brackets the crossing point）**，不声明符号（一块 −1.33 且 CI 跨零、另一块 −49.0） |
> | **"30×"** | **明确写"must not be read as Γ reducing allocation uncertainty"**：Random 组故意混 4 个 rank，**98.9% 的方差是 between-rank**（$\\eta^2=0.989$）；**同秩（r=4，n=5 vs 8）sd 比 0.98**、Welch **p=0.47** |
> | **可辩护替代** | **worst-case**：Theory **5/5 全改善**（失败率 **0/5**，最坏 −76）vs Random **2/15 = 13.3%**（最坏 **+1659**） |
> | 排序证据 | **6/6 → 8/8**，二项 **p=0.031 → 0.0078** |
> | **"sharp phase transition"** | **降级为"location is bracketed"**：r=5 bootstrap CI **[−51.5, +12.5]** 跨零；置换 **p=0.100**；n=3 的 MDE **d=2.95** vs 实测 **d=1.95**（**功效不足**） |
>
> ### 我在这一轮自己犯的第 17 个错（已修）
>
> `_p432` 用 **`r"..."` 原始字符串**拼 LaTeX → **`\\n` 不是换行而是字面 `\\n`** 进了 `.tex`
> → **27 个 `! Undefined control sequence`**。修法：`_p435` 逐字符删除**行尾字面 `\\n`**
> （保留真换行），**剩余 0**，**编译恢复 12 页 / 0 错 / 0 未定义**。
> **教训**：**LaTeX 文本不能用 raw string 拼换行**。
>
> ### task-11（`p3-stats`）完成 —— 门禁全绿
>
> - 报告：**`docs/P3_STATS.md`（71.7 KB）**，含 §0 TL;DR + 6 组逐条结论 + **可直接粘贴的英文替换措辞**
> - 归档 9 件：`p3_stats_recon` / `p3_stats_hardened` / `p3_phase_boundary` / `p3_reproducibility`
>   / `p3_nan_diagnostics` / `p3_gamma_batch_sensitivity` / `p3_multiseed_family` / `p3_nan_probe`
>   / **`p3_seed_provenance`**
> - 脚本 `tools/_p440`–`_p44p`；门禁 `_p44a` **GATE PASSED**（含 seed provenance 6 条断言）；
>   `_p44k` **41/41** 报告数字与归档一致
>
> **它的关键结论（我已逐条核实）**：
> - **NaN = 表示塌缩 ✅ 可保留并加强**：**17/17** 个 NaN run 的**任务 loss 全程有限**（0 例 loss NaN）；
>   GPU 探针显示 r=24 在 fp16/bf16 下**全有限**，fp16 还有 **6.1× 余量**
> - **R3.18**：主表 6 个归档 **0/6** 有环境字段（**准确表述是"主表归档未记录环境"**，它已自行更正）；
>   受控跨版本（初始 E 差 **0.24%**、r=5 翻号、r=6 保号）；跨设备 **NaN epoch 是设备不变量**
> - **P3 不走 `create_dataloaders`**（10 个脚本 0 处），数据**按行位置取** →
>   **姊妹项目的随机画廊缺陷不影响 P3**；P3 的敏感性来自 **4-bit 前向的浮点归约顺序**
> - **R3.4**：跨 batch **vision 块 CV 59.9%、极差 5.38×**，但**排序留一 6/6 稳定**；
>   ⚠️ 但**"分配只依赖排序"不完全成立**（$\\beta=1/\\sigma(|\\Gamma|)$ 依赖绝对尺度，rank 向量漂移 **±1–2**）
>   → 已给出 §5.4b 可粘贴英文（*"cancels to the extent that the ordering is preserved, **it does not cancel exactly**"*）
> - **明确未做成**：两个 LLaVA 批次的具体差异超参**未定**；E0 差 0.24% 的**逐算子归因未定**；
>   论文 Γ 表的**真实 batch 敏感度无法测量**（逐 prompt 值未归档）；**R3.22 的"全训练 fp16 vs bf16"对照未跑**
>
> ### 排期失误（它自报，处置正确）
>
> 22:51–23:03 插了 3 个短探针，**抢掉 `p3-downstream` 的 CLIP sweep 窗口**（对方只得 12 分钟）。
> 已释放 GPU、取消后续任务、向两位同事说明、**如实写入报告 §9**。教训"**短任务也要先协调**"已采纳。
>
> ### 待办
>
> - **task-9**（`p3-allocation`，E 组）：链式任务 `pwsh-244` 挂 23:45 自动起
> - **task-10**（`p3-downstream`，F+G 组）：CLIP sweep 在跑
> - `theory.tex` 两处 (A3) **同名不同义** → 需改编号
> - **33 条回复的正式文本**（工作文档已就绪，待补实验数据）
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "P3 累计修 10 处" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("P3 累计修 10 处", "SEEDS = [42, 123, 999]", "98.9%", "0/5", "p3_seed_provenance"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
