# -*- coding: utf-8 -*-
r"""映射 PR 审稿意见 → 我们在 paper合/A1 里的对应修复（2026-10-12）。

## 审稿人意见（`C:\Users\hongr\Desktop\PR结果10_11.txt`）

**AE**：*severe numerical inconsistencies, flawed statistics, unsubstantiated causal
claims and unreliable generalization*。

| # | 来源 | 主张 |
|---|---|---|
| R1.1 | R1 | 数值不一致（text-only r8 α64：核心 −0.081/0.637 vs Route D **+0.079**/0.389，符号翻转）；R@1 0.627 vs 0.427 |
| R1.2 | R1 | DG–检索统计**伪重复 + 组间混杂**；要求 within-dataset / within-model + 混合效应/聚类 bootstrap |
| R1.3 | R1 | 噪声/梯度/有效秩被称为"**直接因果证据**"→ 要求层级归一化扰动、多噪声级、匹配相对扰动预算、多种子 |
| R1.4 | R1 | 跨架构/跨数据集概化过强（COCO R@1<0.001、BLIP-1 近随机、SigLIP 差异极小） |
| R1.5 | R1 | DG 监控"**zero-overhead**"不实（每 2 epoch 算 5000 对）；且 Route E 有失败案例 |
| R1.6 | R1 | 全量微调与 PEFT 用**同一优化超参**（batch 128/10ep/1e-4）→ 不公平 |
| R2.1 | R2 | 标题 "Protect, Don't Perturb" 概化过度 |
| R2.2 | R2 | 与先前工作的**新颖性区分不足** |
| R2.3 | R2 | 116 实验多为**超参变体**，核心仅 Flickr30k/COCO |
| R2.4 | R2 | "Visual Fragility" 仍**描述性**，无法排除正则化/模态优化差异 |
| R2.5 | R2 | DG 监控**尚属初步**；DG-ES 会**过早终止**好 run |
| R3.1 | R3 | 摘要/结论 +0.079 vs 表格 −0.064/−0.066；**封面信稿号与文件不符** |
| R3.2 | R3 | DG–检索为**汇集的非独立**实验，偏相关不足，且为 **post hoc 非预测性** |
| R3.3 | R3 | Visual Fragility **过度声称因果**，控制不足 |
| R3.4 | R3 | COCO R@1<0.001、BLIP-1 用选择性解冻 → 检索协议需澄清 |

## 本脚本：把每条映射到我们**已做**的修复（可核对）

    python tools\_p243_map_pr_to_fixes.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "pr_to_fixes_map.json"


def has(path: str, pat: str, flags=re.I) -> bool:
    p = REPO / path
    if not p.exists():
        return False
    t = io.open(p, encoding="utf-8", errors="replace").read()
    return bool(re.search(pat, t))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    checks = [
        ("R1.1", "批次/配置不一致（符号翻转）",
         "统一 batch=128（100 run）",
         (REPO / "outputs" / "analysis" / "batchfix_plan.json").exists()),
        ("R1.1", "配置对照表",
         "paper合 有 tab:position_strict + 配置说明",
         has("paper合/sections/empirical.tex", r"tab:position_strict")),
        ("R1.1", "分层（按数据集）图/表",
         "paper合 有数据集翻转段（Flickr30k vs COCO）",
         has("paper合/sections/validation.tex", r"flip|Flickr30k.*COCO")),
        ("R1.2", "组内/组间统计（伪重复）",
         "**A1** 有 sec:hardening 的组内相关 + `_p219` n=30 组内 Fisher +0.840",
         has("paper_a1/main.tex", r"within-dataset|orders datasets")),
        ("R1.2", "留出/预测性验证",
         "**A1** 有 sec:holdout（leave-one-family-out, R²=0.371/0.378）",
         has("paper_a1/main.tex", r"sec:holdout|held-out")),
        ("R1.2", "混合效应/聚类 bootstrap",
         "**A1** 有 `a1_h_bootstrap.json`（bootstrap 点估计）",
         (REPO / "outputs" / "a1_h_bootstrap.json").exists()),
        ("R1.3", "参数匹配的扰动 / 多种子",
         "**A1** 有噪声扫描 + 种子（`a1_h_seed_summary.json`）",
         (REPO / "outputs" / "a1_h_seed_summary.json").exists()),
        ("R1.4", "跨架构证据强度",
         "**A1** 明确 scope（三族；`we claim this for no other families`）",
         has("paper_a1/main.tex", r"claim this for no other families")),
        ("R1.5", "零开销不实",
         "**A1** 已改为「不需要额外前向」+**停止决策价值未证明**（E-B 实验）",
         has("paper_a1/main.tex", r"does \\emph\{not\} license a stopping rule|"
                                  r"rather than a decision rule|costs no additional forward")),
        ("R1.5", "Route E 失败案例",
         "**A1** 有 sec:disclosed（主动披露 two limitations）",
         has("paper_a1/main.tex", r"sec:disclosed|disclosed after internal review")),
        ("R1.6", "优化超参公平性",
         "**A1** 有 sec:protocol_note（严格 LoRA-only 协议）",
         has("paper_a1/main.tex", r"sec:protocol_note")),
        ("R2.1", "标题概化过度",
         "**A1** 标题已改：Tracks Zero-Shot Accuracy under Classification Fine-Tuning",
         has("paper_a1/main.tex", r"Tracks Zero-Shot Accuracy")),
        ("R2.2", "新颖性区分",
         "**A1** 有 Related Work 43 条 + `Placement Against Prior Work` 小节",
         (REPO / "paper_a1/related_work.tex").exists()),
        ("R2.5", "DG-ES 过早终止",
         "**A1** 已**删除监控器主张**，改为「diagnostic」+ 决策局限段",
         has("paper_a1/main.tex", r"diagnostic.*rather than a decision rule|"
                                  r"does not improve the stopping")),
        ("R3.1", "稿号与文件不符",
         "**A1** cover_letter 的披露已重写（含 `PRLETTERS-D-26-02378` / `26-0663`）",
         has("paper_a1/cover_letter.tex", r"PRLETTERS-D-26-02378")),
        ("R3.2", "post hoc 非预测性",
         "**A1** 有 sec:holdout（留出族）+ `_p218` 100 检查点组内预测",
         has("paper_a1/main.tex", r"sec:holdout")),
        ("R3.3", "因果过度声称",
         "**A1** 已把 r=1.000 降级为「自洽检查，非独立验证」",
         has("paper_a1/main.tex", r"self-consistency check, not independent")),
        ("R3.4", "检索协议澄清",
         "**A1** 有 sec:ckpt_transfer（协议差异如实并列两个测量）",
         has("paper_a1/main.tex", r"sec:ckpt_transfer")),
    ]

    print("=" * 100)
    print("PR 审稿意见 → 我们的对应修复")
    print("=" * 100)
    print(f"  {'#':<7}{'审稿人关注':<34}{'状态':<6}我们的措施")
    print("-" * 100)
    done = 0
    rows = []
    for tag, issue, action, ok in checks:
        print(f"  {tag:<7}{issue[:32]:<34}{'✅ 已做' if ok else '⚠️ 待核':<6}{action[:58]}")
        rows.append({"tag": tag, "issue": issue, "action": action, "done": bool(ok)})
        done += 1 if ok else 0
    print("-" * 100)
    print(f"  已做 {done}/{len(checks)}")

    print()
    print("=" * 100)
    print("来源文件存在性")
    print("=" * 100)
    for f in ("outputs/analysis/batchfix_plan.json", "outputs/a1_h_seed_summary.json",
              "outputs/a1_h_bootstrap.json", "outputs/a1_epoch_sweep.json",
              "paper_a1/main.tex", "paper合/sections/empirical.tex"):
        p = REPO / f
        print(f"  {'✅' if p.exists() else '🔴'} {f}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"rows": rows, "done": done, "total": len(checks)},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
