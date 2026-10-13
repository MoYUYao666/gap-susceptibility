# -*- coding: utf-8 -*-
r"""把 PRL 稿件从 8 页压到 7 页：删除 4 条同用途引用 + 压缩两处正文。

为什么必须做：PRL 规定"双栏不超过 7 页（含全部材料）"，超页 = 自动拒稿。
实测 8 页 = 前置 1 + 正文 5 + 参考文献 2；需省约 1 页。

删除的 4 条（功能重叠，主论点不依赖它们）：
  xin2024vpeftsurvey      —— 与 xu2026peftsurvey 同为 PEFT 综述（视觉侧）
  prottasha2025pefta2z    —— 与 xu2026peftsurvey 同为 PEFT 综述
  qiu2024progressive      —— 与 khattak2023maple 同为多模态提示
  mao2022unipelt          —— 与 wang2023multilora 同为统一/组合框架

    python tools/_trim_prl_to_seven_pages.py            # 预演
    python tools/_trim_prl_to_seven_pages.py --apply
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MD = REPO / "paper_review_prl" / "MANUSCRIPT.md"

DROP = ["xin2024vpeftsurvey", "prottasha2025pefta2z", "qiu2024progressive", "mao2022unipelt"]

# 正文压缩（等价改写）
TEXT_PAIRS = [
    ("and tabulating reported results; two cover the language and vision settings respectively",
     "and tabulating reported results"),
    ("for which authoritative reviews exist [xu2026peftsurvey;\nlialin2023scalingdown]",
     "for which authoritative reviews exist [xu2026peftsurvey]"),
]


def strip_key(text: str, key: str) -> tuple[str, int]:
    """从 [a; b, c] 中移除某个 key；若括号因此为空则删掉整个括号。"""
    n = 0

    def fix(m: re.Match) -> str:
        nonlocal n
        inner = m.group(1)
        if key not in inner:
            return m.group(0)
        parts = [p for p in re.split(r"([;,])", inner)]
        kept, i = [], 0
        while i < len(parts):
            seg = parts[i].strip()
            if seg == key:
                # 同时吃掉相邻分隔符
                if kept and kept[-1].strip() in ";,":
                    kept.pop()
                i += 2 if i + 1 < len(parts) and parts[i + 1].strip() in ";," else 1
                n += 1
                continue
            kept.append(parts[i])
            i += 1
        out = "".join(kept).strip().strip(";,").strip()
        return f"[{out}]" if out else ""

    text = re.sub(r"\[([^\]\[]+)\]", fix, text)
    return text, n


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(MD, encoding="utf-8").read()
    before = len([w for w in re.findall(r"[A-Za-z']+", t)])

    # 1) 表格里的整行（形如 | [key] | ... |）
    for k in DROP:
        pat = re.compile(r"^\| \[" + re.escape(k) + r"\][^\n]*\n", re.M)
        t, cnt = pat.subn("", t)
        if cnt:
            print(f"  删除表格行: {k}")

    # 2) 行内引用
    for k in DROP:
        t, cnt = strip_key(t, k)
        print(f"  移除行内引用 {k}: {cnt} 处")

    # 3) 正文压缩
    for old, new in TEXT_PAIRS:
        if old in t:
            t = t.replace(old, new, 1)
            print(f"  压缩正文: {old[:50]}…")
        else:
            # 兼容换行差异
            old2 = old.replace("\n", " ")
            t2 = t.replace("\n", " ")
            if old2 in t2:
                print(f"  ⚠ 因换行未命中（需手动）: {old[:50]}…")

    after = len([w for w in re.findall(r"[A-Za-z']+", t)])
    leftover = [k for k in DROP if k in t]
    print(f"\n英文词 {before} → {after}")
    print(f"残留未删净: {leftover if leftover else '无 ✅'}")
    if apply:
        io.open(MD, "w", encoding="utf-8", newline="").write(t)
        print("已写入")
    else:
        print("（预演，加 --apply 生效）")
    return 1 if leftover else 0


if __name__ == "__main__":
    raise SystemExit(main())
