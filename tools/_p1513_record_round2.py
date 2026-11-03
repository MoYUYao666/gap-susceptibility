# -*- coding: utf-8 -*-
"""Record the second gap-fill round (S23-S26) in the hand-off documents."""
import io
import json

HANDOFF = "HANDOFF.md"
MAP = "文件地图.md"
GAPS = "docs/P3_REMAINING_GAPS_2026-10-22.md"
AUD = "docs/P3_RESUBMISSION_AUDIT_2026-10-21.md"

ENTRY = """> **🧪 2026-10-22 09:30 —— R1 剩余项第二轮：S23–S26 入稿，剩余缩到 3 类**
>
> 新增并以实测/归档写入下一版草稿（已投 `PRLETTERS-D-26-02671` 未动）：
>
> | 缺口 | 新内容 | 结果 |
> |---|---|---|
> | R3.4 Γ batch 敏感性 | **S23** `tab:gammabatch` | 参考 batch n∈{2,4,8,16}×3 组成：CV **0.32–0.55**，块排序随组成变化 → Γ 在小 batch 下是噪声统计量 |
> | R3.5 Qwen Hessian | **S18 扩展** | Qwen2-VL-2B 上 share 为 −0.42%/+0.25%/−0.87%（|share|<1%），一阶近似成立 |
> | R3.22 NaN 诊断 | **S24** | 156 日志：17 run 能量 NaN 而 loss 有限；初始化探针 33 层 hidden 全有限、E 已非有限 → 非优化器爆炸 |
> | R2.3/R3.16 指令跟随 | **S25** `tab:instr` | base F1 0.5003 → r5/r6 0.5074，BLEU 全 0.1559：**无实质提升** |
> | R1.4 新族多种子 | **S26** `tab:newerseeds` | Qwen2.5 三种子：r5 +608/+208/+416、r6 −48/−416/−208 → 符号模式稳定且与 LLaVA 相反 |
>
> 正文 10 页、补充 **10 页（S1–S26）**；`audit_check`/`audit_pdf` 0/0；provenance gate PASS（P3 floats=17）。
> **剩余 3 类**：R2.4/R3.9 官方基线（HALoRA/IGU/Shap 未实现）、VQA 指标与 VQA 数据族（R2.3/R3.16/R3.23）、R3.18 硬件矩阵（不可得）。
>

"""


def main() -> int:
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "R1 剩余项第二轮" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENTRY + h[j + 1:])
        print("handoff updated")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("144. 🧪 **R1 剩余项第二轮（2026-10-22 09:30）** —— S23 Γ batch 敏感性（CV 0.32–0.55）、S18 扩展 "
           "Qwen Hessian（<1%）、S24 NaN 诊断、S25 指令跟随（无实质提升）、S26 新族多种子（符号稳定反向）；"
           "补充 10 页 S1–S26；剩余 3 类（官方基线/VQA/硬件）。\n")
    anchor = "143. 📋 **R1 剩余项盘点"
    if "R1 剩余项第二轮" not in m:
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        m = m[: end + 1] + row + m[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(m)
        print("map updated")
    g = io.open(GAPS, encoding="utf-8").read()
    g2 = g.replace("## 二、部分解决（10 条）", "## 二、部分解决 / 已补（2026-10-22 第二轮后）")
    if "## 七、第二轮补充后的剩余" not in g2:
        g2 = g2.rstrip() + """

## 七、第二轮补充后的剩余（2026-10-22 09:30）

已补并写入稿子：
- **R3.4** → S23（CV 0.32–0.55，排序随 batch 变化）；
- **R3.5** → S18 扩展（Qwen2-VL-2B |share|<1%）；
- **R3.22** → S24（156 日志 + 初始化探针）；
- **R2.3/R3.16** → S25 指令跟随（base F1 0.5003 → r5/r6 0.5074，BLEU 不变，无实质提升）；
- **R1.4** → S26 三种子（r5 全正、r6 全负，方向稳定但为反证）。

**真正剩余（3 类）**：
1. **R2.4/R3.9**：HALoRA / IGU-LoRA / ShapLoRA 的忠实实现与等预算训练（未实现）；
2. **VQA 指标与数据族**（R2.3 / R3.16 / R3.23）：需 VQA 数据与评测流程；
3. **R3.18**：CUDA/PyTorch/硬件矩阵（单机不可得，已声明限制）。
"""
    io.open(GAPS, "w", encoding="utf-8", newline="").write(g2)
    print("gaps doc updated")
    a = io.open(AUD, encoding="utf-8").read()
    if "第二轮补充" not in a:
        a = a.rstrip() + """

## 十、第二轮补充（2026-10-22，S23–S26）

见 `docs/P3_REMAINING_GAPS_2026-10-22.md` 第七节：R3.4/R3.5/R3.22/R2.3/R3.16/R1.4 已补并写入下一版草稿；
剩余仅 R2.4/R3.9 官方基线、VQA 指标/数据族、R3.18 硬件矩阵三类。补充材料 10 页（S1–S26），正文 10 页。
"""
        io.open(AUD, "w", encoding="utf-8", newline="").write(a)
        print("audit updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
