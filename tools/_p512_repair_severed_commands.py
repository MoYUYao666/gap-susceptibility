# -*- coding: utf-8 -*-
r"""P3：修复 `sections/*.tex` 中被"非 raw 字符串 `\n`"事故**切断的行首命令**（2026-10-13）。

## 病因（与 `_p501` 不同，但同源）

某个脚本用**非 raw** 的 Python 字符串拼 LaTeX：`"\nabla"` 在 Python 里 `\n` 是换行
⇒ 写入 `.tex` 后变成 `（真换行）abla`。同型受害者：

| 原命令 | 切断后 | 出现文件 |
|---|---|---|
| `\nabla` | `abla` | theory(24) / introduction(3) / discussion(2) / conclusion(2) / main(2) / related_work(1) / appendix / supplementary |
| `\noindent` | `oindent` | conclusion / main / title_page / supplementary |
| `\neq` | `eq` | theory(2) / appendix / supplementary |

**关键**：这类损伤**不会报编译错**——`abla E` 在数学模式里只是四个变量字母，
`oindent` 在文本模式里只是一串字母。所以 `_p503`（只数字面 `\n`）报"0"、
`main.log` 报"0 errors"，而 PDF 里印的是 **`abla E` 而不是 `∇E`**。**静默错误比报错更危险。**

## 本脚本的判据（刻意做窄）

不写宽泛正则去"扫全文"。判据三重锁定：

1. **行首 token 白名单**：只有 `abla` → `\nabla`、`oindent` → `\noindent`、`eq` → `\neq` 三种映射；
2. **前一行锚点**：前一行必须以**续行**结尾（`\langle`、`\|`、`(`、`[`、`=`、`\perp`、`\Gamma `、`\cos(`、
   空行对应 `oindent`），否则**报错退出、不写盘**；
3. **逐行 diff 断言**：写入后逐行比对，**只允许被锁定的那几行发生变化**；字符增量必须**恰好等于
   `2 × 修复数`**（`\n` 多出的两个字符）。

**只改 `--files` 白名单里的文件**；用 `--scan` 可以只读地看全仓库还有哪些断头（不动手）。

    python tools\_p512_repair_severed_commands.py                 # 预演
    python tools\_p512_repair_severed_commands.py --apply         # 写入（白名单）
    python tools\_p512_repair_severed_commands.py --scan          # 全树只读扫描
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"

# token -> 完整命令（不写正则，逐字面量）
FIXMAP = {
    "abla": "\\nabla",
    "oindent": "\\noindent",
    "eq": "\\neq",
}

# 前一行"仍在表达式中间"的判据：**数学模式未闭合**，或以无法结束句子的符号结尾。
# 这是"正证据"判据——只有当上一行明确处于续行状态时才允许动手。
MID_EXPR_ENDINGS = ("(", "[", "|", "=", ",", "<", "\\langle", "\\perp",
                    "\\cos(", "\\Gamma", "\\exp(", "\\Big(", "\\big(")


def anchor_ok(prev_stripped: str, tok: str) -> bool:
    """上一行是否明确处于"表达式未写完"的状态。"""
    if tok == "oindent":
        return prev_stripped == ""          # \\noindent 只能紧跟空行
    if not prev_stripped:
        return False
    if prev_stripped.count("$") % 2 == 1:   # 数学模式未闭合 ⇒ 必然续行
        return True
    return prev_stripped.endswith(MID_EXPR_ENDINGS)

DEFAULT_FILES = [
    "paper3/paper_ieee/sections/theory.tex",
    "paper3/paper_ieee/sections/introduction.tex",
    "paper3/paper_ieee/sections/discussion.tex",
    "paper3/paper_ieee/sections/conclusion.tex",
]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def scan_tree() -> int:
    """只读：列出全树仍存在的行首断头命令。"""
    bad = 0
    print("=" * 104)
    print("全树只读扫描：行首断头命令")
    print("=" * 104)
    for f in sorted(PI.rglob("*.tex")):
        if ".bak" in f.name or "sections_full" in str(f) or "PRL_submission" in str(f):
            continue
        lines = _read(f).split("\n")
        hits = []
        for i, ln in enumerate(lines):
            for tok in FIXMAP:
                if ln.startswith(tok) and (len(ln) == len(tok) or not ln[len(tok)].isalnum()):
                    hits.append((i + 1, tok, ln[:46]))
                    break
        if hits:
            bad += len(hits)
            print(f"\n  {f.relative_to(REPO)}  —— {len(hits)} 处")
            for ln_no, tok, txt in hits:
                print(f"      L{ln_no:>4}  {tok:<8} -> {FIXMAP[tok]:<10} | {txt}")
    print()
    print(f"  合计 **{bad} 处**（其中 {len(DEFAULT_FILES)} 个白名单文件之外的部分**本脚本不动**）")
    return bad


def repair(paths: list[str], apply: bool) -> int:
    print("=" * 104)
    print("修复行首断头命令（白名单 + 前一行锚点 + 逐行 diff 断言）")
    print("=" * 104)
    total_fix = 0
    plan: list[tuple[Path, list[str], list[tuple[int, str]]]] = []
    for rel in paths:
        p = REPO / rel
        if not p.exists():
            print(f"  🔴 缺文件 {rel}")
            return 2
        lines = _read(p).split("\n")
        edits: list[tuple[int, str]] = []
        for i, ln in enumerate(lines):
            for tok in FIXMAP:
                if ln.startswith(tok) and (len(ln) == len(tok) or not ln[len(tok)].isalnum()):
                    prev = lines[i - 1].strip() if i > 0 else ""
                    if not anchor_ok(prev, tok):
                        print(f"  🔴 锚点不符，拒绝写入：{rel}:{i+1} token={tok!r} "
                              f"前一行为 {prev[-44:]!r}")
                        return 3
                    edits.append((i, tok))
                    break
        plan.append((p, lines, edits))
        total_fix += len(edits)
        print(f"  {rel:<52} 待修 {len(edits):>3} 处")
    if total_fix == 0:
        print("\n  ✅ 无断头命令（已修复过或本就干净）——无需写入")
        return 0
    print(f"\n  合计待修 {total_fix} 处")
    if not apply:
        print("  （预演）—— 未写入")
        return 0

    for p, lines, edits in plan:
        if not edits:
            continue
        before = "\n".join(lines)
        new = list(lines)
        for i, tok in edits:
            new[i] = FIXMAP[tok] + new[i][len(tok):]
        after = "\n".join(new)
        # 断言 1：字符增量恰好 = 2 × 修复数（`\n` 两字符）
        assert len(after) - len(before) == 2 * len(edits), \
            f"[增量异常] {p.name}: {len(before)} -> {len(after)}，修复 {len(edits)} 处"
        # 断言 2：逐行 diff，只有被锁定的行可以变
        b_lines, a_lines = before.split("\n"), after.split("\n")
        assert len(b_lines) == len(a_lines), f"[行数变了] {p.name}"
        changed = {i for i in range(len(b_lines)) if b_lines[i] != a_lines[i]}
        assert changed == {i for i, _ in edits}, \
            f"[越界改动] {p.name}: 期望 {sorted(i for i, _ in edits)}，实际 {sorted(changed)}"
        # 断言 3：无控制字符
        assert not any(ord(c) < 9 or (13 < ord(c) < 32) for c in after), \
            f"[控制字符] {p.name}"
        p.write_text(after, encoding="utf-8", newline="")
        print(f"  ✅ {p.name:<20} 修 {len(edits)} 处；断言 3 项全过")
    print(f"\n  → 共修 {total_fix} 处")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--scan", action="store_true", help="只读扫描全树")
    ap.add_argument("--files", nargs="*", default=None)
    a = ap.parse_args()
    if a.scan:
        scan_tree()
        return 0
    return repair(a.files or DEFAULT_FILES, a.apply)


if __name__ == "__main__":
    raise SystemExit(main())
