# -*- coding: utf-8 -*-
r"""落账：解码器 VLM 结果写入 P3（2026-10-13）。

    python tools\_p44a_record_decoder_vlm.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔬 2026-10-13 03:00 —— 解码器 VLM 那一档跑成：**blank 问题最锋利的证明（换评测图，结论反过来）****
>
> ### 一、`p3-downstream` 用两段空档跑成（42 run，02:39–02:56）
>
> **模型**：`Qwen2-VL-2B-Instruct`（**bf16**，LoRA $q/k/v/o$，**视觉塔冻结**，α=2r，LR 5e-5，3 epochs，$n_{\\text{train}}=16$）
> **数据**：**COCO val2014 真实图文**；`blank` = 同形状纯黑 128×128
> **rank**：$\\{1,2,4,5,6,8,16\\}$ × {real, blank} × 3 seed = **42 run，全 cuda**；另 1 条 CPU 冻结基线
> **E 口径**：与论文一致（最后一层 $E=\\mathrm{mean}\\|\\mathrm{mean}(h_{\\text{vis}})-\\mathrm{mean}(h_{\\text{lang}})\\|^2$）
>
> ### 二、我独立重算（逐 rank × 条件）
>
> | 条件 | 逐 rank 均值 | 符号 |
> |---|---|---|
> | **blank** | −518.9 … −184.5 | **7/7 全负** |
> | **real** | +193.6 … +449.9 | **7/7 全正** |
>
> **无任何符号翻转**；符号**完全由图像条件决定、与 rank 无关**；配对（同 rank 同 seed）**21/21 全负**（均值 **−699.0**）
> ⇒ **解码器 VLM 上同样未复现 $r_c\\in[5,6]$**，与论文自报"Qwen2-VL-7B 无相变"一致，
> **并把该结论从 blank 图扩展到真实图文**。
>
> ### 三、⭐ 最锋利的一条：**用 held-out 真实图评测，结论方向反过来**
>
> | rank | **real 条件** | **blank 条件** |
> |---|---|---|
> | 1 | −236.0 | **−260.2** |
> | 4 | −211.0 | −28.9 |
> | 6 | −212.8 | **+7.6**（转正） |
> | 8 | −169.2 | **+149.2** |
> | 16 | −134.7 | **+178.7** |
>
> ⇒ 用**训练条件自身**测：blank 降能量；
> 用 **held-out 真实图**测：**real 条件 7/7 为负（改善）**，**blank 条件随 rank 由负转正**（−260 → +179）
> ⇒ **"blank 改善对齐"只在你用 blank 测 $E$ 时成立。**
>
> **这比"符号翻转"更干净**：同一个训练好的模型、**换一组评测图**，结论就反过来——
> **不依赖偶发观察，直接证明 blank 不是中性探针**（**R3.13 的最锋利答案**）。
>
> ### 四、成员同时报了一条**对论文不利**的不一致（好）
>
> $n=16$ 下 **CLIP 双塔** real 的 $\\Delta E_{\\text{train}}$ 为**负**、blank 为**正**；
> **Qwen 解码器恰好相反** ⇒ **"真实图文训练是否有益于对齐"的符号是架构相关的**
> —— **加强**"blank 结论不可外推"，但**削弱**"真实图文一定更好"的简单叙事。**稿中两边一起写。**
>
> ### 五、成员自标的简化限制（已写进稿）
>
> 为控显存把图上限设为 `max_pixels=16384`（128×128）→ **每样本只有 15 个 visual token**
> —— **这本身就是一种"简化视觉输入"，与被批评的 blank 同源**。
> 故只主张"**在低视觉 token 预算下差异显著且方向稳定**"，**不主张**完整分辨率下成立。
>
> **✅ 我已批准补跑 12 个 run**（`--max-pixels 50176`，224×224，约 60 token，≈10 min）——
> **它自己标注的这条限制是真的、且与被批评对象同源**，10 min 换掉一个同源缺陷值得。
> **时机由它选**（`p3-allocation` 正在跑 P1 ≈4 h）；**前提是不抢卡**；
> **若 224×224 下符号变了，如实报并改 §3.3 的结论**。
> 它已在 `_p464` 加了 `--min-pixels/--max-pixels`、**逐 run 记录像素预算**、
> **"同一归档不许混不同预算"的守卫**（三样都对）。
>
> ### 六、smoke 实测（`p3d_qwen_smoke.json`）
>
> | 量 | 实测 |
> |---|---|
> | 权重加载 | 3.8 s |
> | 单步 fwd+bwd（rank=4, batch=1） | **0.83 s** |
> | 峰值 allocated / reserved | **4.34 GiB / 4.64 GiB** |
> | 可训练参数 | **1,089,536**（= 手算 $28\\times[2r(1536{+}1536)+2r(1536{+}256)]$，**完全一致**） |
>
> **`18 s/run` vs `~9 min/run` 的解释**：token 预算不同（它每样本 **15 visual token**、平均序列 **53.8**）
> ⇒ **两者都是真数，但引用必须带各自的 `max_pixels`/`n_train`/`epochs`**。
>
> ### 七、n 口径（已锁死）
>
> `p3d_clip_ranksweep.json` = **79 条** = **1 冻结基线 + 78 训练**；能量↔下游分析用 **78**
>
> ### 八、门禁与状态
>
> - 新增 **§3.3**（完整 7×2 表、三条结论、自标限制）；`_p466` 加 16 条断言 → **59/59 通过**
> - **P3**：**13 页** / 0 错 / 0 未定义；**累计修 21 处**
> - **GPU**：`p3-allocation` 跑 P1（10 独立随机样本 × 3 seed = 30 run，≈4 h）→ 之后 P3（AdaLoRA）
> - **task-9/10/11 全部 complete**
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
    if "blank 问题最锋利的证明" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("最锋利的证明", "−260", "+178.7", "1,089,536", "累计修 21 处"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
