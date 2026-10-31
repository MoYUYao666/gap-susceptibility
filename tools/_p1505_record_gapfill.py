# -*- coding: utf-8 -*-
"""Record the R1 gap-fill results in the audit report, HANDOFF and the file map."""
import io

AUDIT = "docs/P3_RESUBMISSION_AUDIT_2026-10-21.md"
HANDOFF = "HANDOFF.md"
MAP = "文件地图.md"

SECTION = """
## 八、R1 缺口补齐结果（2026-10-21 晚，改投后完成）

原始结果：`outputs/analysis/p3_gapfill_summary.json`；说明文档 `docs/P3_GAPFILL_2026-10-21.md`。

| 缺口 | 补了什么 | 结果 | 状态 |
|---|---|---|---|
| **R3.5** Hessian | LLaVA-1.5-7B 4-bit + LoRA r=5/6，有限差分测 $g^\\top H g$ | 在训练学习率 $\\eta=5\\times10^{-5}$ 下二阶项为**一阶项的 −3.5%（sd 0.3–0.4%）**；曲率由 vision 塔主导；探测步长 $10^{-3}$ 时比例升至约 −0.7（局部性） | ✅ 已实测（结论：一阶近似在操作点成立但二阶非零，须按局部表述）|
| **R3.9** 更多基线 | NTK 对角线分配 + Γ 分配 + uniform 的**计算对比**（CLIP，真实图文对） | NTK 规则把预算更多给 vision（8/5/2/1），Γ 规则为（5/5/4/2）；两种排序不一致 | ⚠️ 仅计算、未训练（HALoRA/IGU/Shap 仍未实现）|
| **R3.18** 环境矩阵 | 五 seed 归档 + transformers 4.57 vs 5.16 对照 | r5：n=5，−23.0±22.3，范围 [−49.0,+8.0]；r6：+65.5±38.5，[+25.5,+115.0]；跨版本 ΔE 0.0 vs −39.5（轨迹形状一致）| ⚠️ 单机单卡，硬件矩阵不可扩 |
| **R3.22** NaN 诊断 | 已有 `p3_nan_diagnostics.json` / `p3_nan_probe.json`（156 日志扫描 + 初始化 GPU 探针） | E 先 NaN 而 loss 有限 → 能量泛函在病态几何上产生非有限值，不是优化器爆炸 | ✅ 已有归档，无需新跑 |
| **R2.3/R3.16** 下游任务 | 在 marine caption 数据上训 r=5/r=6 适配器（20 样本、3 epochs），对 4 个留出样本测 BLEU-4 / token F1 / CLIP 相似度 | 三个 arm 生成完全相同：BLEU-4=0、token F1=0.1787、CLIP=0.3233 → **零结果**（20 样本适配器不改变贪婪生成）| ⚠️ 仅小规模 sanity check；VQA 未做 |
| **R3.23** 数据集族 | 同一 captioning run 用的是 marine caption（不同于 Alpaca/ShareGPT 指令数据） | caption 协议下 ΔE：r5 +17.0、r6 +105.5（与 blank-image 协议不同） | ⚠️ 仅一个替代数据集族 |
| **R1.4** 新模型族 | 下载并跑 **Qwen2.5-VL-3B-Instruct**（blank-image，20 样本，3 epochs，rank 5/6） | r5 ΔE **+608.0**（+2.9%）、r6 **−48.0**（−0.2%）→ **符号模式与 LLaVA 相反，crossing 不复现** | ✅ 已实测（结果是"不支持强跨架构声明"，与协议依赖结论一致）|

**总体**：R1 的 33 条中，原本 8 条部分项现在有 **4 条补成实测（R3.5、R1.4、R3.22、R3.18 部分）**、**3 条仍为部分（R3.9、R2.3/R3.16、R3.23）**、1 条（R3.22）本就有归档。
新结果对论文的含义：**支持"协议依赖 + 范围限制"**，但 **R1.4 的新模型族结果与 LLaVA 相反**，不能用来支持"跨架构可迁移"——若审稿人再问，应如实引用，而不是掩盖。
"""


def main() -> int:
    t = io.open(AUDIT, encoding="utf-8").read()
    if "R1 缺口补齐结果" not in t:
        io.open(AUDIT, "w", encoding="utf-8", newline="").write(t.rstrip() + "\n" + SECTION)
        print("audit updated")
    h = io.open(HANDOFF, encoding="utf-8").read()
    entry = """> **🧪 2026-10-21 19:25 —— R1 缺口补齐（改投后证据包）**
>
> 针对 R1 的 8 条部分项补跑/补算，结果入 `docs/P3_GAPFILL_2026-10-21.md` + `outputs/analysis/p3_gapfill_summary.json`：
>
> | 项 | 结果 | 状态 |
> |---|---|---|
> | R3.5 Hessian | 训练 lr 下二阶项 = 一阶项的 **−3.5%**（vision 塔主导；$10^{-3}$ 探测步长时 −0.7，局部性）| ✅ 实测 |
> | R1.4 新模型族 | **Qwen2.5-VL-3B**：r5 **+608.0**、r6 **−48.0** → 与 LLaVA 符号相反，**crossing 不复现** | ✅ 实测（结果不支持强跨架构声明）|
> | R3.9 基线 | NTK 分配 (8/5/2/1) vs Γ (5/5/4/2) vs uniform，仅计算未训练 | ⚠️ 部分 |
> | R3.18 环境 | 五 seed + tf4.57/5.16 对照；单机单卡 | ⚠️ 部分 |
> | R2.3/R3.16 下游 | marine caption：三个 arm 生成完全相同（BLEU-4 0、F1 0.1787、CLIP 0.3233）→ **零结果** | ⚠️ 仅 sanity check，VQA 未做 |
> | R3.23 数据集族 | caption 协议 ΔE：r5 +17.0、r6 +105.5 | ⚠️ 单个替代数据集 |
> | R3.22 NaN | 已有归档（156 日志 + 初始化探针）| ✅ 已有 |
>
> 这些是**改投版之后的下一轮证据**，不影响已投的 `PRLETTERS-D-26-02671`；若审稿意见回来，可直接按此表回应/补写。
>

"""
    if "R1 缺口补齐（改投后证据包）" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + entry + h[j + 1:])
        print("handoff updated")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("141. 🧪 **R1 缺口补齐证据包（2026-10-21 19:25）** —— Hessian 实测（lr 下 −3.5%）；Qwen2.5-VL-3B "
           "r5 +608/r6 −48（crossing 不复现）；NTK 分配对比；caption 下游零结果；五 seed/env 矩阵。"
           "`docs/P3_GAPFILL_2026-10-21.md`。\n")
    anchor = "140. 📚 **R1 完整意见启用"
    if "R1 缺口补齐证据包" not in m:
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        m = m[: end + 1] + row + m[end + 1:]
    io.open(MAP, "w", encoding="utf-8", newline="").write(m)
    print("map updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
