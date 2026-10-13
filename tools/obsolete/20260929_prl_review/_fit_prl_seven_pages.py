# -*- coding: utf-8 -*-
r"""把 PRL 稿件压到 7 页以内（硬上限，超页=自动拒稿）。

页数账（实测）：前置 1 页 + 正文 5 页 + 参考文献 2 页 = 8 页 → 需掉 1 页。
三条并行手段：
  A. 删 8 条"边缘但保留要点"的引用（每条省约 0.04 页，共约 0.3 页）
  B. 正文压缩（§2、§3.7、§4 各删冗语，约 −400 词 ≈ 0.4 页）
  C. 两张表格 table* → table（单栏），每张省约 0.15–0.2 页

    python tools/_fit_prl_seven_pages.py            # 预演
    python tools/_fit_prl_seven_pages.py --apply
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MD = REPO / "paper_review_prl" / "MANUSCRIPT.md"
BUILD = REPO / "tools" / "_build_prl_tex.py"

# A. 删除的边缘引用（要点由保留的引用承载）
DROP = [
    "shao2025tokencompression",   # 效率综述，主线为"分配"，非"压缩"
    "dettmers2023qlora",          # 量化：§3.3 的"组合式预算"点由 MoRA 承载
    "fu2025mme",                  # 基准：与 mmbench/pope 重复说明评测口径问题
    "mao2022unipelt",             # 若仍残留则一并清
    "chen2024rightway",           # 评测批判：与 song2025bothleaked 同点
    "jie2022convpass",            # 视觉适配：已由 VPT/SSF/AdaptFormer 三者代表
    "he2023safe",                 # 同上
    "lialin2023scalingdown",      # 教程性综述：与 xu2026peftsurvey 同用途
]

# B. 正文压缩（等价改写，不删论点）
TEXT_PAIRS: list[tuple[str, str]] = [
    # §2.2 四策略描述收紧
    ("*Uniform allocation* assigns the same configuration — typically the same rank — to every module.\n"
     "This is the default in most applications of the low-rank family, and it is a reasonable baseline\n"
     "precisely because it embodies no assumption about which modules matter.",
     "*Uniform allocation* assigns the same configuration — typically the same rank — to every module. It\n"
     "is the default in most applications of the low-rank family, and a reasonable baseline precisely\n"
     "because it assumes nothing about which modules matter."),
    ("*Search-based allocation* treats the configuration as a hyperparameter to be optimised [zhou2024autopeft;\n"
     "liu2022ia3]. It is the most expensive and the most prone to overfitting the validation set, and — this\n"
     "is the point that matters here — a search cannot be used to demonstrate that a principled allocation\n"
     "rule is superior, because the search replaces the rule with its outcome.",
     "*Search-based allocation* treats the configuration as a hyperparameter [zhou2024autopeft; liu2022ia3].\n"
     "It is the most expensive and the most prone to overfitting, and — the point that matters here — a\n"
     "search cannot show that a principled rule is superior, because it replaces the rule with its outcome."),
    # §2.3 三条理由收紧
    ("First, it changes what a result means. \"We adapt the backbone with rank 8 and improve by two points\"\n"
     "answers the second decision while leaving the first fixed and unstated. \"We adapt the projector\n"
     "rather than the backbone\" answers the first while leaving the second fixed. Papers rarely say which\n"
     "of the two their contribution addresses, so a reader cannot tell whether an improvement is evidence\n"
     "about siting or about division.",
     "First, it changes what a result means. \"We adapt the backbone with rank 8 and gain two points\"\n"
     "answers the second decision while leaving the first unstated; \"we adapt the projector rather than the\n"
     "backbone\" does the reverse. Papers rarely say which decision they address, so a reader cannot tell\n"
     "whether a gain is evidence about siting or about division."),
    ("Second, the decisions have different governing variables. The first is governed by architecture and\n"
     "data volume: with a few hundred examples, adapting a large site is a poor bet regardless of the\n"
     "allocation, whereas with a large task-specific corpus the site choice may matter less than the\n"
     "protocol used to evaluate it. The second is governed by the target metric, and the same budget can\n"
     "be optimal for one metric and damaging for another — an allocation that improves task accuracy need\n"
     "not preserve the base model's alignment behaviour, and vice versa.",
     "Second, the decisions answer to different variables. The first follows architecture and data volume:\n"
     "with a few hundred examples, adapting a large site is a poor bet whatever the allocation, whereas with\n"
     "a large corpus the site may matter less than the protocol used to evaluate it. The second follows the\n"
     "target metric, and the same budget can be optimal for one metric and damaging for another."),
    # §3.7 三条稳健结论收紧
    ("Three conclusions\nappear robust. First, *site dominates allocation in the small-data regime*: with a small\n"
     "task corpus, which site is trainable matters more than how a budget is divided within it, because a\n"
     "small corpus gives little signal with which to estimate an importance score [zhang2023adalora;\n"
     "wang2024loraga; silvarodriguez2024closerlook]. Second, *intervening at the projector is the lowest-risk\n"
     "change*: it is the smallest site, its modification cannot destroy representations the encoder produced,\n"
     "and training it alone has been reported as sufficient [iskandar2026projector]. Third, *uniform\n"
     "allocation is the appropriate default* until a paper states the protocol under which a non-uniform\n"
     "rule was estimated, since a rule whose estimation protocol is unstated is not reproducible, and\n"
     "standardised harnesses for comparing adaptation methods have only recently begun to appear\n"
     "[belanec2026peftbench].",
     "Three conclusions\nappear robust. *Site dominates allocation in the small-data regime*: with a small corpus,\n"
     "which site is trainable matters more than how the budget is divided within it, because a small corpus\n"
     "gives little signal for estimating an importance score [zhang2023adalora; wang2024loraga;\n"
     "silvarodriguez2024closerlook]. *Intervening at the projector is the lowest-risk change*: it is the\n"
     "smallest site, it cannot destroy representations the encoder produced, and training it alone has been\n"
     "reported as sufficient [iskandar2026projector]. And *uniform allocation is the appropriate default*\n"
     "until a paper states the protocol by which a non-uniform rule was estimated, since an unstated\n"
     "protocol is not reproducible; standardised harnesses have only recently begun to appear\n"
     "[belanec2026peftbench]."),
    # §4 引言段收紧
    ("The instances in §3 share one cause: information required for comparison is missing from reports\n"
     "rather than wrong in them. The remedy is a reporting standard, and because such standards are only\n"
     "useful if they are concrete, we give one. The twelve items below are the minimum we found necessary\n"
     "to compare two multimodal adaptation results; they are deliberately phrased so that a reader of a\n"
     "paper can check compliance without access to code. We group them by the question they answer.",
     "The instances in §3 share one cause: information required for comparison is absent from reports rather\n"
     "than wrong in them. The remedy is a reporting standard, and such standards are only useful if\n"
     "concrete. The twelve items below are the minimum needed to compare two multimodal adaptation results,\n"
     "phrased so a reader can check compliance without access to code."),
]


def strip_key(text: str, key: str) -> tuple[str, int]:
    n = 0

    def fix(m: re.Match) -> str:
        nonlocal n
        inner = m.group(1)
        if key not in inner:
            return m.group(0)
        parts = re.split(r"([;,])", inner)
        kept, i = [], 0
        while i < len(parts):
            if parts[i].strip() == key:
                if kept and kept[-1].strip() in ";,":
                    kept.pop()
                i += 2 if i + 1 < len(parts) and parts[i + 1].strip() in ";," else 1
                n += 1
                continue
            kept.append(parts[i])
            i += 1
        out = "".join(kept).strip().strip(";,").strip()
        return f"[{out}]" if out else ""

    return re.sub(r"\[([^\]\[]+)\]", fix, text), n


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(MD, encoding="utf-8").read()

    for k in DROP:
        t, cnt_tbl = re.subn(r"^\| \[" + re.escape(k) + r"\][^\n]*\n", "", t, flags=re.M)
        t, cnt_inl = strip_key(t, k)
        print(f"  {k:<30} 表格行 {cnt_tbl} ｜ 行内 {cnt_inl}")

    n_pairs = 0
    for old, new in TEXT_PAIRS:
        if old in t:
            t = t.replace(old, new, 1)
            n_pairs += 1
        else:
            print(f"  ⚠ 压缩未命中: {old[:48]}…")
    print(f"\n正文压缩命中 {n_pairs}/{len(TEXT_PAIRS)}")
    leftover = [k for k in DROP if k in t]
    print(f"残留: {leftover if leftover else '无 ✅'}")

    if apply:
        io.open(MD, "w", encoding="utf-8", newline="").write(t)
        print("已写入 MANUSCRIPT.md")
        # C. 表格改单栏
        b = io.open(BUILD, encoding="utf-8").read()
        if r"\begin{table*}[t]" in b:
            b = b.replace(r"\begin{table*}[t]", r"\begin{table}[t]").replace(r"\end{table*}", r"\end{table}")
            io.open(BUILD, "w", encoding="utf-8", newline="").write(b)
            print("已把表格改为单栏（table* → table）")
    else:
        print("（预演，加 --apply 生效）")
    return 1 if leftover else 0


if __name__ == "__main__":
    raise SystemExit(main())
