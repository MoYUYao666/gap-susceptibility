# -*- coding: utf-8 -*-
"""Append the real-R1 audit section (33 comments) to the P3 resubmission audit report and update related docs."""
import io

AUDIT = "docs/P3_RESUBMISSION_AUDIT_2026-10-21.md"
OBJ = "docs/P3_REVIEWER_OBJECTIONS.md"

SECTION = """
## 七、按 R1 真实审稿意见重审（2026-10-21 晚；更正）

**更正**：本文件第二节原按"预判清单"写；实际上 **R1 的完整审稿意见、我们的 44 KB 逐条回复、以及 10 页修订稿
（`CORRECTED_2026-10-15/`）都在归档里**——先前"审稿意见原文未取得"只适用于**拒稿通知**（它没有附新的审稿报告）。

来源文件（`SUBMISSION/_archive/P3_PRL_rejected_2026-10-21/`）：

| 文件 | 内容 |
|---|---|
| `reviews/PRLETTERS-D-26-02378-reviews.pdf` | 三位审稿人报告原件 |
| `reviews/PRL Revison.txt` | R1 决定信（Revise，2026-09-30，截止 2026-11-02）|
| `evidence/p3_reviews_structured.json` | 33 条意见结构化版（R1.1–R3.23）|
| `response/P3_RESPONSE_LETTER.md` | 44 KB 逐条回复（11 项主要改动，含 5 处反向修改/撤稿）|
| `CORRECTED_2026-10-15/` | R1 修订稿（10 页 + 6 页补充）|

**逐条状态**（33 条）：✅ **25 条已实质处理**；⚠️ **8 条部分处理/明确声明为限制**；无一条被忽略。

| 状态 | 意见 ID | 说明 / 在改投版中的位置 |
|---|---|---|
| ✅ | R1.1 R1.2 R1.3 R1.5 R2.1 R2.2 R2.4 R2.5 R3.1 R3.2 R3.3 R3.4 R3.6 R3.7 R3.8 R3.10 R3.11 R3.12 R3.13 R3.14 R3.15 R3.17 R3.19 R3.20 R3.21 | 见 `P3_RESPONSE_LETTER.md` 对应条；R1.5 的 R3′ 公理、R2.2 的逐块分配实验、R1.3 的下游检索反例、R3.12 的逐块 Γ 表、R3.17/R3.19 的统计降级均在正文/补充中可检索到 |
| ⚠️ | **R1.4** | 未补"更新的 VLM 家族"；改为真实图文对复跑 + Qwen 边界 + 范围声明 |
| ⚠️ | **R2.3 / R3.16** | 下游只补了 CLIP 检索 `R@1`；VQA/captioning 任务指标未做 |
| ⚠️ | **R3.5** | Hessian 项**未测量**，已在论文中明确声明该限制 |
| ⚠️ | **R3.9** | 只实现并对比了 AdaLoRA；HALoRA / IGU-LoRA / ShapLoRA / NTK 仅在文中讨论，未做同预算实验 |
| ⚠️ | **R3.18** | 做了受控软件环境/seed 对比，但 CUDA/PyTorch/硬件矩阵不完整 |
| ⚠️ | **R3.22** | 报告了多重比较校正；未做权重/激活/梯度级别的 NaN 诊断 |
| ⚠️ | **R3.23** | 用真实图文对回答了"分布差异"，但未换到 VQA/captioning 数据集族 |

**改投版相对 R1 修订稿的新增**（补强，不替代 R1 回复）：
- **S14**：五 seed 统计（r=5 −23.0±22.3 vs r=6 +65.5±38.5；精确置换 **p=0.008**），直接加强 R3.17/R3.19；
- **S16**：协议窗口测量（n=12 的 r=5 −39.5 vs 默认 n=20 −10.5），部分回应 R3.18；
- **S17**：claim-status 表（把 R1.5/R2.2/R2.3/R3.5/R3.9/R3.11 的"不支持/仅边界"逐条公开）；
- 数据 DOI 改为 v2.2、文件名规则、封面信披露前稿号。

**结论**：R1 的 33 条里，**25 条已实质处理、8 条为部分处理或声明限制**；这些内容都随 R1 修订稿进入了本次改投版。
**无法确认的是 R2 阶段审稿人为何仍判"not substantially addressed"**——拒稿信没有附新报告；最可能的争议点就是上表 8 条 ⚠️
（尤其 R1.4 的新模型族、R2.3/R3.16 的任务指标、R3.9 的更多基线）。
"""


def main() -> int:
    t = io.open(AUDIT, encoding="utf-8").read()
    if "按 R1 真实审稿意见重审" not in t:
        t = t.rstrip() + "\n" + SECTION
        io.open(AUDIT, "w", encoding="utf-8", newline="").write(t)
        print("audit report updated")
    o = io.open(OBJ, encoding="utf-8").read()
    note = """
## 2026-10-21 晚：R1 完整意见已启用（更正）

R1 的审稿报告、33 条结构化意见、44 KB 逐条回复与 10 页修订稿都在
`SUBMISSION/_archive/P3_PRL_rejected_2026-10-21/`（`reviews/`、`evidence/p3_reviews_structured.json`、`response/`、
`CORRECTED_2026-10-15/`）。按真实意见的重审结论见
`docs/P3_RESUBMISSION_AUDIT_2026-10-21.md` 第七节：25 条实质处理、8 条部分处理/声明限制。
"""
    if "R1 完整意见已启用" not in o:
        io.open(OBJ, "w", encoding="utf-8", newline="").write(o.rstrip() + "\n" + note)
        print("reviewer-objections doc updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
