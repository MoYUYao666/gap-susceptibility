# -*- coding: utf-8 -*-
r"""清点 PR 对 P1 的全部意见，并核实 `paper合` 的**当前真实状态**（2026-10-12）。

## 来源

`C:\Users\hongr\Desktop\PR结果10_11.txt`（AE + R1 六条 + R2 五条 + R3 四条）

**本脚本**：对每条给出 ① 审稿人原话要点 ② `paper合` 里的当前证据（计数/锚点）
③ 处置（已做 / 待做 / 需实验）。

    python tools\_p249_pr_full_inventory.py [--apply]
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
FH = sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex"))) + \
    sorted(glob.glob(str(REPO / "paper合" / "main*.tex")))
OUT = REPO / "outputs" / "analysis" / "pr_full_inventory.json"


def C(pat: str) -> int:
    n = 0
    for f in FH:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        n += len(re.findall(pat, t, re.I))
    return n


def where(pat: str, n=4):
    out = []
    for f in FH:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        c = len(re.findall(pat, t, re.I))
        if c:
            out.append(f"{Path(f).name}({c})")
    return "、".join(out[:n]) if out else "—"


# (编号, 审稿人要点, 处置类型, 核验正则, 说明)
ITEMS = [
    ("AE", "severe numerical inconsistencies", "写作+数据",
     r"batch", "批次混杂根因已查明并统一重跑 100 run"),
    ("AE", "flawed statistics", "实验", r"mixed|cluster|bootstrap",
     "组内分层+5seed+留出已做；**混合效应待补**"),
    ("AE", "unsubstantiated causal claims", "写作", r"causal",
     "causal 措辞已清零；Visual Fragility 已限定"),
    ("AE", "unreliable generalization", "写作", r"scope|claim",
     "三骨干同协议；标题待收窄"),
    ("R1.1", "配置不一致 +0.079 符号翻转 / 需配置对照表 + 分层图", "写作+数据",
     r"tab:position_strict", "批次统一；+0.079 已证实为另一实验（严格冻结）"),
    ("R1.2", "伪重复 + 组间混杂 → within-dataset/model + 混合效应 + 聚类 + 留出",
     "实验", r"within|mixed|cluster", "**混合效应/聚类标准误未做**"),
    ("R1.3", "噪声/梯度被称 direct causal；需归一化扰动+多噪声级+匹配预算+多种子",
     "实验", r"normaliz|matched perturbation", "**参数匹配扰动待补**"),
    ("R1.4", "跨架构/跨数据集概化过强；**COCO R@1<0.001、BLIP-1 选择性解冻**",
     "写作+核验", r"BLIP|COCO", "**需核 paper合 是否仍含这些行**"),
    ("R1.5", "zero-overhead 不实；DG-ES 会过早终止 → 重新定位为 PoC + 报开销",
     "写作", r"zero-overhead|DG-ES", "均 0 处（已删）"),
    ("R1.6", "全量微调与 PEFT 同一 lr 不公平 → lr 扫描/权重衰减/早停",
     "实验", r"learning rate|full.fine.tun", "**lr 扫描未做**"),
    ("R2.1", "标题 Protect, Don't Perturb 概化过度", "写作",
     r"Protect, Don't Perturb", "**标题仍是它**"),
    ("R2.2", "与先前工作新颖性区分不足", "写作",
     r"related work|prior work", "新增 dynamical theory（P2）"),
    ("R2.3", "116 实验多为超参变体；核心仅 Flickr30k/COCO → 更大数据集+现代 VLM",
     "实验", r"Food101|DTD|iNat", "已有 DTD/Food-101/iNat；**更大 VLM 未做**"),
    ("R2.4", "Visual Fragility 描述性 → 更强因果/理论证据", "写作",
     r"Visual Fragility", "已加「phenomenological, not proven」+ sec:theory"),
    ("R2.5", "DG-ES 会过早终止好 run → DG 作诊断可以，作监控不行", "写作",
     r"DG-ES|early stopping", "DG-ES 已删"),
    ("R3.1", "摘要/结论 +0.079 vs 表格 −0.064；稿号与文件不符", "写作+数据",
     r"0\.079|0\.064", "**需逐处核 paper合 的 +0.079/−0.064**"),
    ("R3.2", "DG–检索为汇集的非独立实验；偏相关不足；post hoc 非预测性",
     "实验", r"holdout|held.out|cluster", "**留出/聚类待补**"),
    ("R3.3", "Visual Fragility 过度声称因果；控制不足", "写作",
     r"causal|phenomenological", "已限定"),
    ("R3.4", "COCO R@1<0.001、BLIP-1 用选择性解冻 → 检索协议需澄清", "写作+核验",
     r"selective unfreez|R@1", "**需核**"),
    ("R2.3b", "封面信/稿里 '116 experiments' 的计数", "核验",
     r"116", "**需核**"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print("=" * 104)
    print("PR 全部意见 → `paper合` 当前状态")
    print("=" * 104)
    print(f"  {'#':<7}{'处置':<10}{'命中':>5}  审稿人要点 / 说明")
    print("-" * 104)
    rows = []
    for tag, issue, kind, pat, note in ITEMS:
        n = C(pat)
        print(f"  {tag:<7}{kind:<10}{n:>5}  {issue[:62]}")
        print(f"         {note[:96]}")
        print(f"         位置: {where(pat)}")
        rows.append({"tag": tag, "issue": issue, "kind": kind, "hits": n,
                     "where": where(pat), "note": note})
    print("-" * 104)
    need_exp = [r for r in rows if r["kind"] == "实验"]
    print(f"  共 {len(rows)} 条；其中**需实验** {len(need_exp)} 条：")
    for r in need_exp:
        print(f"     [{r['tag']}] {r['issue'][:70]}")
    print()
    print("  需核验（可能含旧数值/旧表述）：")
    for r in rows:
        if r["kind"] in ("核验", "写作+核验") and r["hits"]:
            print(f"     [{r['tag']}] {r['hits']} 处 → {r['where']}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rows, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
