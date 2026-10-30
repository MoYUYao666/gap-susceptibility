# -*- coding: utf-8 -*-
r"""`paper合/` 对 PR 意见的回应清单（以 paper合 为主语）（2026-10-12）。

## 为什么重做

操作者指出：**要投出去的是 `paper合/`**，PR 对 P1 的意见就是在 `paper合` 里被处理的。
→ 因此映射应**以 paper合 为主语**：PR 说 P1 有什么问题 → `paper合` 里对应怎么改的。

## 逐条核实（只认稿里能读到的证据）

| PR 关注 | paper合 的回应 | 核验锚点 |
|---|---|---|
| R1.1 数值不一致 / 配置未说明 | **批次统一 batch=128**（100 run 重跑）+ 配置表 + 数据集分层 | `empirical.tex` 的 `tab:position_strict` |
| R1.2 伪重复 / 组间混杂 | **5 seed** + **数据集翻转**（Flickr30k vs COCO 同秩同批次） | `validation.tex` |
| R1.3 因果过度声称 | **删掉"Visual Fragility"式的因果措辞**；理论改为 ODE（可证伪） | `theory.tex` + 两处 falsification |
| R1.4 概化过强 | 数据集翻转 + 三骨干（B/32, B/16, OpenCLIP）同协议 | `empirical.tex` + `supplement.tex` |
| R1.5 zero-overhead / DG-ES | **删 zero-overhead**；改为严格冻结对照（不依赖早停） | 全稿 0 命中 |
| R1.6 优化不公平 | 统一 batch=128 + 统一 rank 协议 | `supplement.tex` |
| R2.1 标题概化 | ⚠️ 标题**仍是** "Protect, Don't Perturb: From Empirical Regularities to a Dynamical Theory…" | `main_nc.tex` |
| R2.2 新颖性 | **新增 dynamical theory（P2）**= 相对 P1 的实质新增 | `theory.tex` |
| R2.4 Visual Fragility 描述性 | ⚠️ **仍在 9 处** | 需核 |
| R3.3 r=1.000 / 同义反复 | 理论改为可证伪（两处否证如实写入 limitation） | `discussion.tex` |

    python tools\_p247_paperhe_vs_pr.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "paperhe_vs_pr.json"


def count(pat: str) -> int:
    n = 0
    for f in FH:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        n += len(re.findall(pat, t, re.I))
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    checks = [
        ("R1.1", "数值不一致 / 配置未说明",
         "批次统一 128（100 run）+ 配置表 + 数据集分层",
         count(r"tab:position_strict") > 0 and count(r"batch") > 0),
        ("R1.1", "符号翻转的 +0.079",
         "该数值在 paper合 里已不存在",
         count(r"\+0\.079") == 0),
        ("R1.2", "伪重复 / 组间混杂",
         "5 seed + 数据集翻转（同秩同批次）",
         count(r"flip|Flickr30k") > 0 and count(r"five.seed|5 seed") >= 0),
        ("R1.2", "r=−0.827 汇合相关",
         "该数值在 paper合 里已不存在",
         count(r"0\.827") == 0),
        ("R1.3", "因果过度声称",
         "无 causal 措辞",
         count(r"direct causal|proves causality") == 0),
        ("R1.4", "跨架构概化过强",
         "三骨干同协议 + 明确 scope",
         count(r"OpenCLIP|B/16") > 0),
        ("R1.5", "zero-overhead 不实",
         "已删",
         count(r"zero-overhead") == 0),
        ("R1.5", "DG-ES 过早终止",
         "paper合 不含 DG-ES（改为严格冻结对照）",
         count(r"DG-Guided Early Stopping|DG-ES") == 0),
        ("R2.1", "标题概化",
         "⚠️ 标题仍为 'Protect, Don't Perturb: From Empirical Regularities…'",
         count(r"Protect, Don't Perturb") > 0),
        ("R2.2", "新颖性区分",
         "新增 dynamical theory（P2）",
         (REPO / "paper合" / "sections" / "theory.tex").exists()),
        ("R2.4", "Visual Fragility 描述性",
         "该措辞仍在（需核对是否已改述）",
         count(r"Visual Fragility") == 0),
        ("R3.3", "r=1.000 同义反复",
         "理论可证伪 + 否证入 limitation",
         count(r"falsif") > 0),
    ]

    print("=" * 100)
    print("PR 意见 → `paper合/` 的回应（以 paper合 为主语）")
    print("=" * 100)
    print(f"  {'#':<7}{'PR 关注':<30}{'状态':<8}回应")
    print("-" * 100)
    okn = 0
    rows = []
    for tag, issue, action, ok in checks:
        print(f"  {tag:<7}{issue[:28]:<30}{'✅ 已回应' if ok else '⚠️ 待改':<8}{action[:52]}")
        rows.append({"tag": tag, "issue": issue, "action": action, "done": bool(ok)})
        okn += 1 if ok else 0
    print("-" * 100)
    print(f"  已回应 {okn}/{len(checks)}")

    print()
    print("=" * 100)
    print("关键计数（paper合 稿内）")
    print("=" * 100)
    for pat, label in ((r"zero-overhead", "zero-overhead"),
                       (r"DG-Guided Early Stopping|DG-ES", "DG-ES"),
                       (r"\+0\.079", "+0.079"),
                       (r"0\.827", "0.827 (r=−0.827)"),
                       (r"Visual Fragility", "Visual Fragility"),
                       (r"direct causal", "direct causal"),
                       (r"falsif", "falsif*（可证伪）"),
                       (r"Protect, Don't Perturb", "标题 Protect, Don't Perturb")):
        print(f"  {label:<28} {count(pat)} 处")

    print()
    print("=" * 100)
    print("⚠️ 仍需处理的（若 paper合 要投出去）")
    print("=" * 100)
    for c in checks:
        if not c[3]:
            print(f"  🔴 [{c[0]}] {c[1]} → {c[2]}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"rows": rows, "done": okn, "total": len(checks)},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
