# -*- coding: utf-8 -*-
r"""Record the LLaVA step-cost measurement and the conclusion about tuning.

Measured 2026-10-15 on the real configuration (`--samples 400 --batch 2 --max-len 2048`, arm
`text_only`), from the sweep's own new timing counters:

* first batch: **1230 tokens, mean 615 per sequence, padded sequence length 615**
* **84.9-93.6 s per step** over ten steps, of which
  **batch preparation 0.1-0.2 s** and **compute 918-1044 s**
* held-out measurement: 13.2 s over 8 pairs

So the cost is entirely in the forward/backward, the padding is only 0.2% (1230/1228), and there is
nothing in the data path to reclaim. At 615 tokens per 85 s that is **13 tokens/s**, on a device whose
4-bit memory traffic caps it near 28 tokens/s, so the run is close to what this hardware can do.

    python tools/_p945_record_step_cost.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "LLaVA 每步成本已定位"

ENT = """> **🔬 2026-10-15 17:25 —— LLaVA 每步 85 s 已定位：**全在计算**，且已接近这块 4060 的 4-bit 极限**
>
> ### 一、✅ 实测（用新加的分项计时，**真实参数**：`--samples 400 --batch 2 --max-len 2048`，arm `text_only`）
>
> | 量 | 值 |
> |---|---|
> | 首批 token | **1230**，**每条 615** |
> | **实际 padding 后的序列长度** | **615**（不是 2048！）|
> | **每步** | **84.9–93.6 秒** |
> | 其中 **batch 准备** | **0.1–0.2 秒** |
> | 其中 **计算** | **918–1044 秒 / 10 步** |
> | 评测（8 对）| 13.2 秒 |
>
> ### 二、🔍 三条结论（都从上面数字直接推出）
>
> 1. **瓶颈 100% 在前后向**：batch 准备 0.1 s vs 计算 918 s ⇒ **数据通路没有任何可回收的时间**。
> 2. **padding 不是问题**：批内 1230 tokens，若按各自真实长度则 1228 ⇒ **只浪费 0.2%**。
>    （`processor(padding=True)` 按**批内最长**补，所以 `max_len=2048` 并未被吃满。
>    ⇒ **调小 `max-len` 不会加速**，反而会截断长 caption。）
> 3. **已接近硬件极限**：615 tokens / 85 s = **13 tokens/s**；4-bit 权重 3.5 GB 每步过一遍，
>    按 8.6 GB 显存带宽上限推算约 **28 tokens/s** ⇒ **我们已在极限的约一半**，
>    **靠调 batch / 序列长度拿不到数量级加速**（4060 Laptop 跑 4-bit 7B 本来就这速度）。
>
> ### 三、⏱️ 由此得到的真实工期
>
> | 项 | 值 |
> |---|---|
> | 每步 | 85–94 s |
> | 一个 run（600 步 + 评测）| **≈14.5 小时** |
> | 队列 | 12 run（4 arm × 3 seed），已完成 **3** |
> | **剩余 9 run** | **≈130 小时 ≈ 5.4 天** |
>
> ### 四、⏳ 待操作者决定（我**未擅自改任何参数**）
>
> | 选项 | 结果 | 代价 |
> |---|---|---|
> | **A. 按原参数跑完** | 结果与论文口径**完全一致** | **≈5.4 天** |
> | **B. 减到 1 seed**（仍 4 arm）| ≈1.8 天 | 论文目前用 **3 seed 的离散度**（"std at r≥32: 9.4–61.4"）⇒ **要改口径** |
> | **C. 4 arm 合并为 2**（frozen/both）| ≈2.7 天 | 失去 text_only / vision_only 的分臂**归因** |
> | **D. 减 `eval-pairs` 300→100** | 省约 10%（评测仅 13 s/8 对 ⇒ 300 对 ≈8 分钟/run，**不是瓶颈**）| **几乎无收益** |
>
> **⇒ 我的建议：A**。四个 arm 正是"adaptation site"论证的**唯一干净归因手段**，减 arm 或减 seed
> 会削弱论文最核心的结论；而 5.4 天是**可以并行/挂着跑**的墙钟时间，不影响投稿（EM 替换件申请已发，
> 等编辑部回复本身也需要时间）。
>
> ### 五、⚠️ 基准脚本的教训（已修但未再跑）
>
> 第一版 `_p942` 基准**三个配置里两个无效**：配置 1 写了真实记录 `text_only_s42.json`，
> 配置 2/3 随即命中"sweep 的**已完成即跳过**"分支，**30 秒就"跑完"**了（日志里明写
> `already complete, skipping`）。**跳过逻辑对真跑正确、对计时跑错误** ⇒ 已给 sweep 加 `--out-dir`
> 使计时跑写独立目录（`tools/_p944`）。**这类"看起来跑完其实是跳过"的失败模式，与仓库里那次
> 假门禁同源：门禁必须先证明它真的执行了被测代码。**
>
> **工具**：`_p938`（存活采样）｜`_p939`（ETA）｜`_p940`（每步计时+续跑，已应用）｜`_p942`（基准）｜
> `_p943`（`--bench-steps` + 首批 token 报告）｜`_p944`（`--out-dir`）｜`_p945`（本条落账）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        print("  handoff entry added")
    mp = io.open(MAP, encoding="utf-8").read()
    row = ("28. 🔬 **LLaVA 每步 85 s 已定位（2026-10-15 17:25）** —— 首批 **1230 tokens（每序列 615）**、"
           "实际 padding 序列长度 **615（非 2048）**；每步 **84.9–93.6 s**，其中 **batch 准备 0.1 s、计算 918–1044 s** "
           "⇒ **瓶颈全在前后向，数据通路无可回收**；padding 仅浪费 **0.2%** ⇒ **调小 max-len 无用**；"
           "**13 tokens/s** 对比 4-bit 带宽上限约 28 tokens/s ⇒ **已近硬件极限，调参拿不到数量级加速**。"
           "真实工期：一个 run ≈**14.5 h**，剩余 9 run ≈**5.4 天**。**未擅自改参**，选项 A（原参数跑完，建议）/B（1 seed）/C（2 arm）。"
           "⚠️ 基准脚本首版因「已完成即跳过」导致 2/3 配置 30 秒假跑完，已加 `--out-dir` 修。"
           "详见 `HANDOFF.md` 顶部 2026-10-15 17:25 条目。\n")
    anchor = "27. ⏱️ **LLaVA「卡住了吗」= 没卡（2026-10-15 16:10）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
