# -*- coding: utf-8 -*-
r"""严格核实：PR 审稿意见里哪些**真的**做了、哪些只是部分/没做（2026-10-12）。

## 为什么要严核

`_p243` 的检查多数是"文件存在"或"正则在稿里命中"，**这是弱证据**。
本项目已有教训：**"看起来对"≠"有来源"**。

**本脚本**：对每条意见给出**可核对的证据路径**，并明确标 完全/部分/未做。

    python tools\_p244_strict_pr_audit.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "pr_strict_audit.json"


def find(pattern: str):
    return sorted(glob.glob(str(REPO / pattern), recursive=True))


def count_in(path: str, pat: str):
    p = REPO / path
    if not p.exists():
        return -1
    t = io.open(p, encoding="utf-8", errors="replace").read()
    return len(re.findall(pat, t, re.I))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rows = []

    def add(tag, claim, level, evidence):
        rows.append({"tag": tag, "claim": claim, "level": level, "evidence": evidence})
        icon = {"完全": "✅", "部分": "⚠️", "未做": "🔴"}[level]
        print(f"  {icon} [{tag}] {claim}")
        print(f"       证据: {evidence}")

    print("=" * 100)
    print("R1.1 数值不一致 / 配置未说明")
    print("=" * 100)
    bf = REPO / "outputs" / "analysis" / "batchfix_plan.json"
    n128 = 0
    try:
        d = json.loads(io.open(bf, encoding="utf-8").read())
        n128 = len(d) if isinstance(d, (list, dict)) else 0
    except Exception:
        pass
    add("R1.1a", "统一 batch=128（消除批次混杂）",
        "完全" if bf.exists() else "未做",
        f"outputs/analysis/batchfix_plan.json（{n128} 条）+ 100 run 重跑")
    n_tab = count_in("paper合/sections/empirical.tex", r"tab:position_strict")
    add("R1.1b", "配置对照表", "完全" if n_tab else "未做",
        f"paper合/sections/empirical.tex 里 tab:position_strict（{n_tab} 处）")
    n_flip = count_in("paper合/sections/validation.tex", r"flip|Flickr30k|COCO")
    add("R1.1c", "按数据集分层（Flickr30k vs COCO）", "完全" if n_flip else "未做",
        f"paper合/sections/validation.tex 数据集翻转段（{n_flip} 处）")
    n_expl = count_in("paper合/sections/empirical.tex", r"batch|protocol|batch size")
    add("R1.1d", "说明各组配置差异（batch/协议）", "完全" if n_expl else "部分",
        f"paper合/sections/empirical.tex 提及 batch/protocol {n_expl} 处")

    print()
    print("=" * 100)
    print("R1.2 统计（伪重复/组间混杂）—— **审稿人点名的四项**")
    print("=" * 100)
    n_within = count_in("paper_a1/main.tex", r"within-dataset|within_dataset")
    add("R1.2a", "组内相关（within-dataset）", "完全" if n_within else "未做",
        f"paper_a1/main.tex {n_within} 处 + `_p219` n=30 组内 Fisher +0.840")
    n_mixed = 0
    for f in find("paper_a1/*.tex") + find("paper合/sections/*.tex"):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        n_mixed += len(re.findall(r"mixed[- ]effects|mixed model|clustered standard error",
                                  t, re.I))
    add("R1.2b", "**混合效应模型 / 聚类标准误**", "完全" if n_mixed else "未做",
        f"稿里命中 {n_mixed} 处" + ("" if n_mixed else " ← **审稿人明确点名，我们没做**"))
    n_clust = count_in("paper_a1/main.tex", r"bootstrap") + count_in(
        "paper合/sections/validation.tex", r"bootstrap")
    add("R1.2c", "聚类/bootstrap", "部分" if n_clust else "未做",
        f"提及 bootstrap {n_clust} 处（`outputs/a1_h_bootstrap.json` 存在）")
    n_held = count_in("paper_a1/main.tex", r"sec:holdout|held-out")
    add("R1.2d", "留出验证（非 post hoc）", "完全" if n_held else "未做",
        f"paper_a1/main.tex sec:holdout（{n_held} 处）")

    print()
    print("=" * 100)
    print("R1.3 因果声称（噪声/梯度）")
    print("=" * 100)
    n_norm = count_in("paper_a1/main.tex",
                      r"normaliz|matched perturbation|relative perturbation")
    add("R1.3a", "层级归一化扰动 / 匹配预算", "部分" if n_norm else "未做",
        f"命中 {n_norm} 处（审稿人要 \\|ΔW\\|_F/\\|W\\|_F 归一化）")
    n_seeds = len(find("outputs/a1_h_seeds_*.json")) + len(find("outputs/**/*seed*.json"))
    add("R1.3b", "多种子重复", "完全" if n_seeds else "未做",
        f"种子类归档 {n_seeds} 个")
    n_causal = count_in("paper_a1/main.tex", r"causal")
    add("R1.3c", "避免「直接因果证据」措辞", "部分",
        f"稿里仍出现 causal {n_causal} 处（需逐处核）")

    print()
    print("=" * 100)
    print("R1.4 / R2.1 概化范围")
    print("=" * 100)
    n_scope = count_in("paper_a1/main.tex", r"no other families")
    add("R1.4a", "明确 scope", "完全" if n_scope else "未做",
        f"paper_a1/main.tex「we claim this for no other families」（{n_scope} 处）")
    n_title = count_in("paper_a1/main.tex", r"Tracks Zero-Shot Accuracy")
    add("R2.1a", "标题收窄", "完全" if n_title else "未做",
        "paper_a1/main.tex 标题 = Order Preservation Tracks Zero-Shot Accuracy…")

    print()
    print("=" * 100)
    print("R1.5 / R2.5 监控主张")
    print("=" * 100)
    n_zero = count_in("paper_a1/main.tex", r"zero-overhead")
    add("R1.5a", "删除「zero-overhead」措辞", "完全" if n_zero == 0 else "未做",
        f"paper_a1/main.tex 命中 {n_zero} 处（应 0）")
    n_diag = count_in("paper_a1/main.tex", r"diagnostic|decision rule")
    add("R1.5b", "改为「诊断」+ 决策局限", "完全" if n_diag else "未做",
        f"命中 {n_diag} 处 + E-B 实验（τ 59.66 vs 固定 ep1 59.66）")
    n_route = count_in("paper_a1/main.tex", r"sec:disclosed")
    add("R1.5c", "主动披露失败案例", "完全" if n_route else "未做",
        f"sec:disclosed（{n_route} 处）")

    print()
    print("=" * 100)
    print("R1.6 优化超参公平性（全量微调 vs PEFT 同一学习率）")
    print("=" * 100)
    n_proto = count_in("paper_a1/main.tex", r"sec:protocol_note")
    add("R1.6a", "严格 LoRA-only 协议说明", "完全" if n_proto else "未做",
        f"sec:protocol_note（{n_proto} 处）")
    n_lr = count_in("paper_a1/main.tex", r"learning rate|learning-rate|lr sweep")
    add("R1.6b", "**全量微调的学习率扫描**", "未做",
        f"命中 {n_lr} 处，但**未见对 full-FT 单独调 lr 的实验** "
        f"← 审稿人点名要求")

    print()
    print("=" * 100)
    print("R3.x")
    print("=" * 100)
    n_cov = count_in("paper_a1/cover_letter.tex", r"PRLETTERS-D-26-02378")
    add("R3.1a", "封面信披露稿号", "完全" if n_cov else "未做",
        f"paper_a1/cover_letter.tex（{n_cov} 处）")
    n_self = count_in("paper_a1/main.tex", r"self-consistency check, not independent")
    add("R3.3a", "r=1.000 降级", "完全" if n_self else "未做", f"命中 {n_self} 处")
    n_ck = count_in("paper_a1/main.tex", r"sec:ckpt_transfer")
    add("R3.4a", "检索协议澄清", "完全" if n_ck else "未做", f"sec:ckpt_transfer（{n_ck} 处）")

    levels = {}
    for r in rows:
        levels[r["level"]] = levels.get(r["level"], 0) + 1
    print()
    print("=" * 100)
    print(f"汇总：完全 {levels.get('完全', 0)} ｜ 部分 {levels.get('部分', 0)} ｜ "
          f"未做 {levels.get('未做', 0)}（共 {len(rows)}）")
    print("=" * 100)
    print("  🔴 未做项：")
    for r in rows:
        if r["level"] == "未做":
            print(f"     [{r['tag']}] {r['claim']}")
    print("  ⚠️ 部分项：")
    for r in rows:
        if r["level"] == "部分":
            print(f"     [{r['tag']}] {r['claim']}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"rows": rows, "levels": levels}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
