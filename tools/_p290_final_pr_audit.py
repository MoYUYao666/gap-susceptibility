# -*- coding: utf-8 -*-
r"""最终核验：PR 全部意见在 `paper合` 上的处置状态（2026-10-12）。

    python tools\_p290_final_pr_audit.py [--apply]
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


def C(pat: str) -> int:
    """统计匹配数。

    **重要**：LaTeX 源码里句子常跨行（写到 ~95 字符就换行），
    所以先**把空白归一成单个空格**再匹配——否则 `six dataset $\\times$ backbone cells`
    这类短语会因换行而漏判（本项目已两次踩到）。
    """
    n = 0
    for f in FH:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        t = re.sub(r"\s+", " ", t)
        n += len(re.findall(pat, t, re.I))
    return n


CHECKS = [
    ("R2.1", "标题已收窄（无 Protect, Don't Perturb）", C(r"Protect, Don't Perturb") == 0),
    ("R2.1", "新标题在稿中", C(r"Adaptation Site and the Modality Gap") > 0),
    ("R1.1", "+0.079 已修（仅撤回语境）", C(r"\$\+0\.079\$") <= 1),
    ("R1.1", "43 on Flickr30k 已改", C(r"43 on Flickr30k|\(43 on Flickr30k") == 0),
    ("R1.2", "聚类稳健统计已入摘要", C(r"cluster-robust inference") >= 2),
    ("R1.2", "six dataset × backbone cells 已写", C(r"six dataset") >= 2),
    ("R1.2", "混合效应结果已写", C(r"mixed model with random") > 0),
    ("R1.3", "isotropic 噪声描述已改", C(r"isotropic Gaussian noise") == 0),
    ("R1.3", "LayerNorm 溯源已披露", C(r"73\.9") > 0),
    ("R1.3", "匹配相对扰动负结果已写", C(r"0\.91\\pm0\.45|0\.912") > 0),
    ("R1.4", "apply to any contrastive 已限定", C(r"apply to any contrastive") == 0),
    ("R1.4", "guaranteed alignment 已删", C(r"guaranteed alignment") == 0),
    ("R1.5", "zero-overhead 为 0", C(r"zero-overhead") == 0),
    ("R1.5", "DG-ES 为 0", C(r"DG-Guided Early Stopping|DG-ES") == 0),
    ("R1.5", "88 of 94 已补归档注", C(r"monitor\\_dg\\_check2") > 0),
    ("R1.6", "lr 扫描已写（1e-6 不崩）", C(r"60\.9\\pm0\.2|60\.87") > 0),
    ("R1.6", "共享 lr limitation 已写", C(r"shared learning rate") > 0),
    ("R2.2", "novelty 小节已加", C(r"sec:novelty") > 0),
    ("R2.4", "Fragility 小节标题已限定", C(r"Not of a Fragile Tower") > 0),
    ("R2.4", "inherently more sensitive 已删", C(r"inherently more sensitive") == 0),
    # 只查我们自己的正文（main*.tex）；related_work 里的 0.986 是引用他人工作（liu2026tpc）
    ("R3.1", "Springer 摘要 R²=0.986 已修（不含他人引用）",
     all("0.986" not in io.open(f, encoding="utf-8", errors="replace").read()
         for f in glob.glob(str(REPO / "paper合" / "main*.tex")))),
    ("R3.3", "α universally/consistently negative 已删",
     C(r"universally negative|consistently negative") == 0),
    ("R3.4", "检索协议澄清段已加", C(r"Retrieval protocol, and which rows") > 0),
    ("R3.4", "R@1=1/5000 已披露", C(r"1/5000") > 0),
    ("RX", "pre-hoc 承诺已限定为未验证", C(r"We have not established that it works") > 0),
    ("RX", "架构计数已统一（six backbones）", C(r"six backbones") > 0),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print("=" * 100)
    print("PR 意见 -> paper合 最终核验")
    print("=" * 100)
    ok = 0
    fails = []
    for tag, desc, passed in CHECKS:
        print(f"  {'✅' if passed else '🔴'} [{tag}] {desc}")
        ok += 1 if passed else 0
        if not passed:
            fails.append((tag, desc))
    print("-" * 100)
    print(f"  {ok}/{len(CHECKS)} 通过")
    if fails:
        print("  未通过：")
        for tag, desc in fails:
            print(f"    🔴 [{tag}] {desc}")

    print()
    print("=" * 100)
    print("编译与投稿包")
    print("=" * 100)
    import subprocess
    for name, pdf in (("NC", REPO / "paper合" / "main_nc.pdf"),
                      ("Springer", REPO / "paper合" / "main_springer.pdf"),
                      ("投稿包", REPO / "paper合" / "NC_submission" / "Manuscript.pdf")):
        if pdf.exists():
            o = subprocess.run(["pdfinfo", str(pdf)], capture_output=True,
                               encoding="utf-8", errors="replace").stdout or ""
            m = re.search(r"Pages:\s+(\d+)", o)
            print(f"  ✅ {name:<10} {m.group(1) if m else '?'} 页")
    for name, log in (("NC", REPO / "paper合" / "main_nc.log"),
                      ("Springer", REPO / "paper合" / "main_springer.log")):
        if log.exists():
            t = io.open(log, encoding="utf-8", errors="replace").read()
            print(f"  {name}: 错误 {len(re.findall(r'^!', t, re.M))} ｜ "
                  f"未定义 {len(re.findall(r'(Citation|Reference) .* undefined', t))} ｜ "
                  f"Overfull {len(re.findall(r'Overfull .hbox', t))}")
    return 0 if not fails else 2


if __name__ == "__main__":
    raise SystemExit(main())
