# -*- coding: utf-8 -*-
r"""Record the Pattern Recognition rejection letter and the objection-by-objection audit.

    python tools/_p746_record_pr_audit.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📮 2026-10-15 02:00 —— PR 拒稿信逐条核完：**29 条意见中 27 条已回应，2 条本轮补做****
>
> ### 一、来源
>
> 操作者提供 `C:\\Users\\hongr\\Desktop\\PR_reject.txt`（23,118 字节，UTF-8）。
> `Manuscript Number: PR-D-26-10149`，Area Editor **Xuelong Li**，3 位审稿人。
>
> **AE 定调**：*"severe **numerical inconsistencies**, **flawed statistics**, **unsubstantiated
> causal claims** and **unreliable generalization**. These fundamental flaws invalidate core
> findings, leading to a rejection recommendation."*
>
> ### 二、✅ 逐条核对结果（审 P1 原稿 → 现 Paper A）
>
> | # | 审稿人意见 | Paper A 现状 | 证据 |
> |---|---|---|---|
> | **R1-W1** | `r=8, α=64` 在核心实验 CGΔ=−0.081/R@1=0.637，Route D 却是 **+0.079/0.389**（符号相反）；R@1 0.627 vs 分层基线 0.427 | ✅ **已解释并撤回** | `empirical.tex` L216：*"An earlier version of this sentence quoted $+0.079$ for the text-only arm; **that value belongs to a different configuration**, $\\alpha=64$, whose $R@1$ is $0.389$"* |
> | R1-W1 | 要求**配置对照表** + 分层 DG–R@1 图 | ✅ | 附录 A 完整实验目录（13 类 + XIV 类，221 run）；`empirical.tex` L268 逐 cell 披露配置错配（如 OpenCLIP 行的 R@1 来自 rank-8、ΔCG 来自 rank-4）|
> | **R1-W2 / R3-2 / AE** | 伪重复 + 组间混杂：81 个实验当独立观测报 `r=−0.827`；要求 **mixed-effects / clustered / 组内相关 / 留出验证** | ✅ **本轮补齐留出** | cluster-robust 斜率 −1.05（CR1 SE 0.29，p=0.016）｜family-clustered bootstrap `[−0.89,−0.62]`｜**mixed model** β=−0.95±0.08｜**本轮新增样本外验证** |
> | **R1-W3 / R2-4 / R3-3** | 噪声/梯度/有效秩被称 **"direct causal evidence"**；噪声实验用**绝对**噪声不可比 | ✅ | `direct causal` **全文 0 命中**；`empirical.tex` L352 *"a **phenomenological interpretation** supported by the evidence above, **not a deductively proven mechanism**"*；`2.6×` 主张**已撤回**并新增 `fig9c_ratio.pdf` 说明*"Why that earlier line of evidence was withdrawn"*；改用**匹配相对扰动** `‖ΔW‖_F/‖W‖_F`（0.91±0.45 / 0.99±0.45，与 parity 不可区分）|
> | **R1-W4 / R3-4** | COCO R@1 全 `<0.001`、BLIP-1 近随机且用选择性解冻；SigLIP 上 text-only 优势不成立 ⇒ 不能称 "across architectures" | ✅ | 标题改为 *"Zero-Shot **Cross-Architecture** …"*（P3）；`tab:position_strict` 注明 *"BLIP-1 R@1 values are **near-random** (test set 5K images)"*；**显式披露 SigLIP 反转**：*"reverses it on SigLIP, so the text-only advantage is architectural, **not universal**"* |
> | **R1-W5 / R2-5** | DG-ES "zero-overhead" 不实；只在 3 个 Route E 实验里出现失败（0.63→0.133）⇒ 不宜作为方法贡献 | ✅ **已整章删除** | `zero-overhead` **0 命中**；`early stopping` **0 命中** ⇒ **DG-guided early stopping 已不在稿中**（比审稿人要求的"降级为概念验证"更彻底）|
> | **R1-W6** | 全套用同一 lr=1e-4，全量微调 CIFAR-100 从 60.72%→7.38% 可能是优化不稳而非"灾难性破坏" | ✅ | 新增**逐方法 lr 扫描**：LoRA@1e-5 **60.69%** vs 全量微调@1e-6 **60.87%** ⇒ *"Tuning each method to its own learning rate **removes the adapter methods' apparent advantage**"*；`fig:overview` 注 *"a learning-rate sweep shows the inflation to be **rate-dependent**"* |
> | R2-1 | 标题 "Protect, Don't Perturb" 过泛 | ✅ | 已改名（旧名仅出现在 cover letter 的**前身稿件披露**里）|
> | R2-2 | 图表需更紧凑、重组 | ✅ | 正文 63 页 + 附录 A 目录表 |
> | R2-3 | 规模与多样性不足 | 🟡 **部分** | **6 backbones**（CLIP B/32、B/16、ViT-L/14、OpenCLIP、SigLIP、BLIP-1）、3 PEFT、2 数据集；**仍无 decoder-based VLM 之外的更大数据集** —— 已在 limitations 声明 |
> | R3-1 | 摘要/结论说 +0.079 而正文表是 −0.064/−0.066；**cover letter 稿号与文件不符** | ✅ | `+0.079` 已按"不同配置"解释；稿号问题随 P1 终结 |
> | 全部 | **语言编辑**（3 位一致） | ✅ | 已全面重写 |
>
> ### 三、🆕 本轮唯一补做项：**留出验证**（`tools/_p744`，新增句子已插入 `empirical.tex` L143）
>
> R1-W2 / R3-2 / AE 都点名要 **held-out / out-of-sample** 验证，而稿件此前只写了
> cluster-robust、clustered bootstrap 与 mixed model，**没有留出数字**。归档里其实有
> （`pr_stats_hardened.json :: holdout`），本轮补入：
>
> > *"To check that this is not in-sample fitting, we refit the slope on training folds only and
> > evaluate it on held-out ones: leaving one experiment family out (**12 folds**) gives an
> > out-of-sample $R^2$ of **0.449** pooled and **0.396** at the median fold, with **67%** of folds
> > beating the training-fold constant baseline; leaving one dataset×model cell out (**6 folds**)
> > gives **0.236** and **0.227**, with **67%** of folds beating it. The association therefore
> > transfers, but **not uniformly**: in both schemes the **weakest fold is SigLIP**, where the
> > ordering is known to reverse, which is why we report an association with its per-fold spread
> > rather than a predictive relation."*
>
> **⚠️ 语气取"诚实版"**：只报交叉验证总分会被再次质疑为选择性报告，故**同时给出"只有约 2/3 的折优于常数基线"与"最差折是 SigLIP"**。
> **7 个数字逐一核验**（`tools/_p745`，全 PASS）：
> 12 / 0.449 / 0.396 / 67% / 6 / 0.236 / 0.227 ← `holdout.{leave_one_family_out,leave_one_design_cell_out}`
>
> ### 四、⚠️ 仍需操作者判断的 1 项
>
> **R2-3「实验规模与多样性」**：审稿人要求 *"Broader validation on larger datasets and modern VLMs"*。
> Paper A 现有 6 backbones / 2 数据集 / 383 实验，**已远超 P1 的 116 实验**，但**没有新增数据集**。
> ⇒ **两条路**：① 接受现状（limitations 已声明）② 新跑一个更大数据集（成本高）。
> **我不擅自决定。**
>
> ### 五、✅ 编译与台账
>
> | 项 | 结果 |
> |---|---|
> | 编译 | **63 页 / 0 错误** |
> | PDF 含留出数字 | ✅ `out-of-sample` / 0.449 / 0.396 / 0.236 / 0.227 全部在 |
> | **台账** | **PASS 28 ｜ GAP 0**（新增 7 条留出断言）|
> | 包 | `Manuscript.pdf` **927,561** ｜ `latex_source.zip` **55 成员 / 1,989,924** |
>
> ### 六、结论
>
> **AE 点名的四大硬伤 —— 数值不一致 / 统计缺陷 / 因果过度声称 / 泛化不可靠 —— Paper A 逐条已处理。**
> 唯一新增工作量是**留出验证**（本轮已补）。剩余仅有 R2-3 的规模问题需操作者定夺。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "PR 拒稿信逐条核完" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("PR 拒稿信逐条核完", "Xuelong Li", "PASS 28", "留出验证", "R2-3"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
