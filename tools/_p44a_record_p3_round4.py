# -*- coding: utf-8 -*-
r"""落账：task-10（F+G 组）完成 + P3 累计修 12 处（2026-10-12）。

    python tools\_p44a_record_p3_round4.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔬 2026-10-12（续 4）—— task-10（F+G 组）完成：**下游检验与能量相反，blank images 不是中性探针**
> **→ P3 累计修 12 处；核心主张已被自己的实验收窄**
>
> ### 一、task-10 的两条硬结果（我已**独立重算**，`tools/_p438`）
>
> #### ① 下游检验**与能量相反**（否证性结果）
>
> Flickr30k 真实图文（1000 图 × 5 描述，冻结基线 **R@1 = 0.7058**），CLIP B/32，LoRA 只注文本塔：
>
> | 量 | 值 |
> |---|---|
> | **Spearman(ΔE_test, ΔR@1)** | **−0.3819（n=79）** ⇒ **能量改善伴随检索变差** |
> | ΔE<0 组平均 ΔR@1 | +0.0056（n=54） |
> | ΔE>0 组平均 ΔR@1 | −0.0027（n=24） |
>
> **极端反例（n=1024, r=16，同 rank 同训练量）**：
>
> | 条件 | ΔE | **ΔR@1** |
> |---|---|---|
> | **real** | −0.0004 … +0.0011 | **+0.0197 / +0.0199 / +0.0153** |
> | **blank** | **−0.0059** … +0.0025 | **−0.0136 / −0.0107 / −0.0149** |
>
> ⇒ **blank 的 ΔE 与 real 同量级甚至更负，下游却反向** ⇒ **能量不是下游的代理**。
> （ΔE<0 组更优这一点**与图像条件混淆**——几乎全是 real run——故**不作因果解读**，
> 报告里明确要求两行一起写。）
>
> #### ② **blank images 不是中性探针**
>
> | | real | blank |
> |---|---|---|
> | Γ 块排序 | **vision > shallow > mid > deep** | **shallow** > vision > mid > deep |
> | 三个文本块 cos φ | **全负** | **全正** |
> | $\\Gamma_{\\text{shallow}}$ | **−0.25** | **+171.39** |
> | 任务损失 | 0.0071 | **2.8130（396×）** |
>
> ⇒ **按 blank 测的 Γ 去分配，在真实图文下可能给出方向相反的建议。**
>
> #### ③ rank transition 在真实图文下**未复现**
>
> n=16（论文协议）：real 全负、blank 全正，**全 rank 区间无符号翻转**；
> n=1024：real 全负，$\\Delta E_{\\text{test}}$ 仅在 r=8→16 **变零**（非显著转正）。
> **诚实边界**（成员已写）：论文相变测于 **LLaVA**（解码器+4bit），本实验是 **CLIP**（双塔 fp32），
> 且论文自报 Qwen2-VL 无相变 ⇒ **既不能确认也不能否证** LLaVA 特有相变，
> 能支持的是"**阈值非跨模型普适、对图像条件与训练量高度敏感**"。
>
> #### ④ blank vs real 强交互（39 对配对）
>
> - **n=16**：ΔR@1(blank−real) = **+0.0051 … +0.0081**（blank 反而略好）
> - **n=1024**：ΔR@1(blank−real) = **−0.0139 … −0.0314**（blank 明显更差，随 rank 单调放大）
> - **能量侧始终是 blank 降得更多** ⇒ **blank 下的"能量改善"无法预测下游方向**
>
> ### 二、已写入 P3 的 2 处（累计 **12 处**）
>
> | # | 意见 | 写入内容 |
> |---|---|---|
> | 11 | **R1.3 / R2.3 / R3.15 / R3.16** | 新增 *A downstream check, and it does not go the way the energy would suggest* 段 + *Blank images are not a neutral probe* 段：**全部数字 + 明确结论"minimising E does not reliably improve downstream retrieval，E 应读作表示几何的诊断量而非任务精度的代理"**；并**明确 $r_c\\in[5,6]$ 是本设置特异量、非模型无关常数** |
> | 12 | **R2.3（明确允许的第二选项）** | 新增 *What "optimal" means here* 段：**optimal 限定为 alignment energy**，并声明不主张对下游任务精度最优 |
>
> **编译：P3 `main.pdf` = 12 页 / 0 错误 / 0 未定义** ✅
>
> ### 三、成员自报的两件事（我采纳）
>
> 1. **脚本编号**：任务书给它 `_p430+`，但已被 `task-9` 占用 → 它**整体挪到 `_p460+`**
>    并**与 `p3-allocation` 双向确认**（处置正确）
> 2. **它自己踩到并修掉一个假数字**：CLIP 检索的 caption 张量未 reshape 成 (N,C,L)，
>    使 i2t R@1 **假降到 0.145**（真值 **0.822**）→ 已加硬断言 + 诊断脚本 `_p461b`
>    ⚠️ 它的提醒值得记入流程：**"这类错误会静默产出'看起来合理'的结果"**
>
> ### 四、门禁
>
> - `python tools\\_p466_verify_report.py` → **38/38 通过**（把报告每条关键主张对着归档断言）
> - 归档：`p3d_manifest.json`（1.19 MB）｜`p3d_clip_ranksweep.json`（**79 run**）｜`p3d_summary.json`
>   ｜`p3d_tables.md`｜`p3d_fig_ranksweep.png`｜`p3d_gamma_real_vs_blank.json`｜`p3d_qwen_ranksweep.json`
> - 报告：`docs/P3_DOWNSTREAM.md`
>
> ### 五、明确未做成（成员自列，我照收）
>
> 1. **LLaVA-1.5-7B 规模的真实图文复跑/下游评测**（13.157 GiB > 8 GiB，且禁 4-bit）
> 2. **VQA**（本地无任何 VQA 标注，遵守"不下载"）
> 3. **captioning 指标**（环境无 nltk/pycocoevalcap/sacrebleu/rouge_score，未安装）→ 改用检索 R@1/R@5
> 4. **Qwen2-VL-2B rank sweep**（GPU 三方轮换；脚本已 CPU 端到端验证通过，**给 7–30 min 窗口可跑**）
> 5. `both` 臂、n=128 档、$E_{\\text{train}}$ 全量（现为 min(n,256) 子样本）
>
> ### 六、待办
>
> - **task-9**（`p3-allocation`，E 组）：链式任务 `pwsh-244` 挂 23:45 自动起
> - `theory.tex` 两处 (A3) **同名不同义** → 需改编号
> - **33 条回复的正式文本**（工作文档已就绪；现有 E/F+G/I 三组的实验数据可支撑大部分回复）
> - **页数**：12 页（**投稿时 11 页**）——若继续增页，考虑移入 Supplementary
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
    if "P3 累计修 12 处" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("P3 累计修 12 处", "-0.3819", "0.7241", "+171.39", "396×"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")

    fm = REPO / "文件地图.md"
    if fm.exists():
        ft = io.open(fm, encoding="utf-8").read()
        if "task-10" not in ft:
            add = ("\n### P3 补实验进展（2026-10-12 夜）\n\n"
                   "- **task-11（I 组，统计/可复现性/NaN）**：✅ 完成 —— `docs/P3_STATS.md`（71.7 KB）｜"
                   "门禁 `_p44a` GATE PASSED、`_p44k` 41/41\n"
                   "  - 关键：**\"30×\" 必须删除**（η²(rank)=0.989、同秩 sd 比 0.98）｜"
                   "**\"sharp phase transition\" 降级**（CI 跨零、置换 p=0.100、功效不足）｜"
                   "**NaN=表示塌缩可加强**（17/17 任务 loss 全程有限）｜"
                   "**P3 不走 `create_dataloaders`**，姊妹项目缺陷不影响 P3\n"
                   "  - **归档里另有 10-seed 族**（论文只用 3 个）→ 已写入并**分层披露 E0 环境簇**\n"
                   "- **task-10（F+G 组，真实图文/下游）**：✅ 完成 —— `docs/P3_DOWNSTREAM.md`｜"
                   "门禁 `_p466` 38/38\n"
                   "  - **下游检验与能量相反**：Spearman(ΔE,ΔR@1) = **−0.3819**（n=79）｜"
                   "n=1024/r=16 real **+0.0197** vs blank **−0.0136**\n"
                   "  - **blank images 非中性**：Γ 块排序互换、cos φ 变号、Γ 差 2–3 数量级、loss 差 **396×**\n"
                   "  - rank transition 在真实图文下**未复现**（CLIP 双塔 vs LLaVA 解码器，不能互证）\n"
                   "- **task-9（E 组，真逐块 Γ 分配）**：🔄 链式任务 `pwsh-244` 挂 23:45 自动起\n"
                   "- **P3 已修 12 处**（见 `HANDOFF.md` 各轮条目）；编译 **12 页 / 0 错 / 0 未定义**\n"
                   "- **待办**：`theory.tex` 两处 (A3) 同名不同义；**33 条回复正式文本**；页数 11→12\n")
            io.open(fm, "w", encoding="utf-8", newline="").write(ft.rstrip() + "\n" + add)
            print("  ✅ 文件地图已追加补实验进展段")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
