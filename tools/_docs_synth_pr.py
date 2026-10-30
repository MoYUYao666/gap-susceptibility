# -*- coding: utf-8 -*-
r"""落账：PR 意见在 `paper合` 上的合成改稿（第一批）（2026-10-12）。

    python tools\_docs_synth_pr.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📝 2026-10-12 —— 把 PR 对 P1 的意见**逐条改到 `paper合`**（第一批，操作者"全改对"）**
>
> ### 三个由 Lead 拍板的决定（操作者授权"全改对"）
>
> | # | 决定 |
> |---|---|
> | 1 | **标题 = T1**：*Adaptation Site and the Modality Gap: Empirical Regularities and a Gradient-Flow Theory for PEFT of Contrastive Dual-Encoders* |
> | 2 | **COCO/BLIP-1/ViT-L 近似随机检索**：新增协议澄清段 + 表注逐行标 $R@1$ + 明确排除出跨架构结论 |
> | 3 | **计数不符**：按归档改为 **49 on Flickr30k + 6 on MS-COCO = 55**（原写 43+6=49≠55） |
>
> ### 本批改动（每项都有归档依据）
>
> | # | 对应 PR 意见 | 改动 | 脚本 | 依据 |
> |---|---|---|---|---|
> | 1 | **R2.1** 标题泛化 | 标题收窄（6 处：`main_nc` ×2 含镜像、`main_springer`（短+长）、`highlights_nc`、两封 cover letter）；**保留** `cover_letter*:78` 对前任稿标题的**披露** | `_p270`/`_p271` | 审稿人 R2.1 |
> | 2 | **R1.2/R3.2** 伪重复 | 摘要改为 *"$n=204$ archived runs drawn from six dataset $\\times$ backbone cells---so the effective sample size is far smaller than $204$"*，并补聚类稳健统计（$-1.05$, CR1 SE $0.29$, $p=0.016$；族聚类 bootstrap $[-0.89,-0.62]$；混合模型 $\\beta=-0.95\\pm0.08$；组内 $-1.07$ vs 组间 $-1.01$） | `_p272`/`_p273`/`_p274` | `tools/_p260`（task-1） |
> | 3 | **R1.1/R3.1** 数值不一致 | **`+0.079` 张冠李戴已修**：该值出自 `route_d/d1_alpha64_text_r8`（$\\alpha=64$, $R@1=0.389$），原文却挂在"text-only 限制 CG 增长"上；改为 **$-0.064$**（$\\alpha=16$, $R@1=0.627$）并写明撤回 | `_p278` | `outputs/master_results.json`、`outputs/flickr30k/rq2_text_only/results.json` |
> | 4 | **R2.4/R3.3** α 普适为负 | 三处改为"**222 个拟合里 203 个为负**"，并列出 19 个例外（Adapter 10/50 最大 $+0.061$；LoRA 4 个最大 $+0.011$；**CLIP BitFit 3 个 $\\approx+4\\times10^{-4}$**） | `_p277` | `tools/_p276`（`ode_ledger`/`ode_loco`/`adapter_all_results`/`bitfit_results`） |
> | 5 | **R1.3** 噪声描述与代码不符 | `isotropic Gaussian noise` → **"逐张量 $\\sigma\\,\\mathrm{std}(W_i)$；LayerNorm 因过滤器未匹配 HF 命名而被注入，占 vision 注入 Frobenius 范数 $73.9\\%$"** | `_p279` | `paper/scripts/noise_sensitivity.py`（`tools/_p255` 复核） |
> | 6 | **R2.4/R3.3** Visual Fragility 因果 | 9 处**逐处限定**（小节标题改为 *"…an Interpretation of Where the Adapters Sit, Not of a Fragile Tower"*；写入匹配相对扰动的**负结果**：预算比 $0.91\\pm0.45$/$0.99\\pm0.45$，协议翻转 $0.60$ vs $2.47$，$1.14\\times$ 相对扰动偏差） | `_p281` | `tools/_p255`（task-2） |
> | 7 | **R1.4** 概化过强 | `apply to any contrastive backbone` / `guaranteed alignment protection` / `inherently more sensitive` / `regardless of adapter capacity`（2 处）**全部限定到实测范围** | `_p281` | 归档 + R1.4 |
> | 8 | **R3.4** 检索协议 | 新增 *"Retrieval protocol, and which rows we treat as informative"* 段：COCO $R@1=1/5000$ 即 chance、BLIP-1 为选择性解冻（两臂同训 $196{,}672{,}514$ 参数）、ViT-L 近似随机 | `_p282` | `outputs/coco/rq2_text_only_coco/results.json`、`experiments/blip2_experiments.py:369` |
> | 9 | **R5/R3.1** Springer 摘要 $R^2$ | `0.986`（**超过集合最大值** $0.9773$，且与 `main_nc` 的 0.949 矛盾）→ 改为与归档一致的 `0.949`（Flickr30k `0.953`、COCO `0.903`） | `_p256` | `outputs/analysis/ode_ledger.json::subsets` |
> | 10 | **R3.1** 计数 | *"55 archived LoRA runs (43 on Flickr30k, 6 on MS-COCO)"*（43+6=49≠55）→ **49 on Flickr30k, 6 on MS-COCO**（4 处） | `_p279` | `ode_ledger.json::subsets.lora_flickr=49` |
>
> ### 编译与投稿包
>
> | 稿 | 页数 | 错误 | 未定义 | Overfull |
> |---|---|---|---|---|
> | `main_nc` | **58** | 0 | 0 | 0 |
> | `main_springer` | **42** | 0 | 0 | 0 |
> | 投稿包 `Manuscript.pdf` | **58** | 0 | 0 | — |
>
> 投稿包已重建（`tools/_p190`）：sections/main_nc/references.bib **哈希一致**，zip 43 文件 1.92 MB。
>
> ### 过程中修掉一个**我自己造成的错**
>
> 用 PowerShell 内联 here-string 写 LaTeX 时 `$` 被吞 → Springer 摘要出现 4 处编译错误
> （`Missing $ inserted`）。**已用 `tools/_p274` 整段重写修好**，并把该教训再次落到文档：
> **Windows 下改 LaTeX 必须写脚本文件，不得在命令行拼字符串。**
>
> ### 仍待做
>
> - 16 处概化句还剩约 7 处（写作面 `docs/PR_WRITING_FIX.md` §A.1 有逐条替换文本）
> - `discussion.tex:56` 的 *"pre-hoc configuration selection without training"* 与同文件
>   limitation 冲突，待改
> - `discussion.tex:17` 的 *"88 of 94"* 无归档 → 待补归档或删除
> - 架构计数不统一（five / seven / 表行数）待统一
> - `related_work.tex` 新增 §A.2 的 novelty 段（写作面已给可粘贴文本）
> - task-5（全量微调 lr 扫描，PR R1.6）跑中
"""


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "逐条改到 `paper合`（第一批" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("逐条改到 `paper合`（第一批", "Adaptation Site and the Modality Gap",
              "张冠李戴已修", "203 个为负", "73.9", "1/5000", "0.9773",
              "Windows 下改 LaTeX 必须写脚本文件"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
