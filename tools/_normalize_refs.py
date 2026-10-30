# -*- coding: utf-8 -*-
r"""规范化 markdown 里的方括号引用，并移除指定 key。

修复的 bug：早期 strip_key 在删 key 时留下悬空分号、甚至让相邻 key 粘连
（如 `[jin2024efficientmllm; shao2025tokencompression lialin2023scalingdown]`），
这在 LaTeX 里会变成未定义引用。

做法：取出每个方括号内容 → 按"是合法 key"重新切分 → 去重 → 用 "; " 重新连接。

    python tools/_normalize_refs.py            # 预演
    python tools/_normalize_refs.py --apply
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MD = REPO / "paper_review_prl" / "MANUSCRIPT.md"
DROP = {"shao2025tokencompression", "he2023safe", "lialin2023scalingdown", "peters2020semeval3"}

KEY = re.compile(r"^[a-z][a-z0-9_]*\d[a-z0-9_]*$")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(MD, encoding="utf-8").read()
    fixed = 0
    dropped = 0

    def fix(m: re.Match) -> str:
        nonlocal fixed, dropped
        inner = m.group(1)
        if "://" in inner:            # markdown 链接，跳过
            return m.group(0)
        # 把所有形如 key 的 token 抽出（容忍缺分隔符的粘连由 token 边界解决）
        toks = re.findall(r"[A-Za-z][A-Za-z0-9_]*\d[A-Za-z0-9_]*", inner)
        keep = []
        for k in toks:
            if k in DROP:
                dropped += 1
                continue
            if k not in keep:
                keep.append(k)
        if not toks:
            return m.group(0)
        new = "[" + "; ".join(keep) + "]" if keep else ""
        if new != m.group(0):
            fixed += 1
        return new

    t2 = re.sub(r"\[([^\]\[]+)\]", fix, t)
    print(f"规范化括号: {fixed} 处 ｜ 移除 key 次数: {dropped}")
    left = sorted(k for k in DROP if k in t2)
    print(f"残留: {left if left else '无 ✅'}")
    # 抽查
    for pat in ("efficiency more broadly", "authoritative reviews exist", "encoder's feed-forward"):
        i = t2.find(pat)
        if i >= 0:
            print(f"  检查「{pat}」→ …{re.sub(chr(10), ' ', t2[i:i+120])}…")
    if apply:
        io.open(MD, "w", encoding="utf-8", newline="").write(t2)
        print("已写入")
    else:
        print("（预演，加 --apply 生效）")
    return 1 if left else 0


if __name__ == "__main__":
    raise SystemExit(main())
