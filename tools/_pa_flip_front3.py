# -*- coding: utf-8 -*-
r"""改翻转段的 3-seed 数字（**修正正则**：文件里是 `\pm` 单反斜杠）（2026-10-11）。

## 我上一个脚本的错

我写了 `r"\$-0\.0288\\pm0\.0013\$"` —— 在 **Python raw string** 里
`\\pm` 表示**字面两个字符** `\` + `\` 后跟 `pm`，即匹配 `\\pm`。
而文件里是 **`\pm`（单反斜杠）** → **不匹配**。

**正确写法**：`r"\$-0\.0288\\pm..."` 中 `\\` 在正则里表示"一个字面反斜杠"，
但 raw string 里 `\\` 又是两个字符……**统一用 `re.escape()` 最稳**。

    python tools\_pa_flip_front3.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "validation.tex"

OLD_S = (r"text-only holds the gap at $-0.0288\pm0.0013$ on Flickr30k against "
         r"$-0.0188\pm0.0004$ for the both-position arm")
NEW_S = (r"text-only holds the gap at $-0.0304\pm0.0039$ on Flickr30k against "
         r"$-0.0204\pm0.0028$ for the both-position arm")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()

    # 用 re.escape 把字面串转成正则，并把空白放宽为 \s+
    pat = re.compile(re.escape(OLD_S).replace(r"\ ", r"\s+"))
    ms = list(pat.finditer(t))
    print(f"=== 正则命中 {len(ms)} ===")
    if len(ms) != 1:
        return 1
    t2 = pat.sub(lambda _: NEW_S, t, count=1)

    if not a.apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    for k in (r"$-0.0304\pm0.0039$", r"$-0.0204\pm0.0028$"):
        assert k in t3, f"断言失败：缺 {k}"
    assert "-0.0288" not in t3 and "-0.0188" not in t3, "旧数字仍在"
    print("  ✅ 已更新为 5-seed（batch 128）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
