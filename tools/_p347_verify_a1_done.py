# -*- coding: utf-8 -*-
r"""核实 A1 的 10 项改写是否真的做完（2026-10-12）。

`docs/A1_REFRAME_PLAN.md` §四 执行清单标了 10 项"待做"，
但那是 2026-10-11 22:19 写的计划，而 `paper_a1/main.tex` 是 **2026-10-12 02:05**（其后）。
**不能按时间戳推断，必须逐条在稿里核。**

    python tools\_p347_verify_a1_done.py
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
M = REPO / "paper_a1" / "main.tex"
H = REPO / "paper_a1" / "highlights.tex"


def main() -> int:
    t = io.open(M, encoding="utf-8", errors="replace").read()
    h = io.open(H, encoding="utf-8", errors="replace").read() if H.exists() else ""
    print("=" * 100)
    print("A1 改写清单逐条核实（在稿中找证据，不按时间戳推断）")
    print("=" * 100)

    checks = []

    # 1) 标题
    m = re.search(r"\\title\{(.{0,200}?)\}", t, re.S)
    title = " ".join(m.group(1).split()) if m else "?"
    checks.append(("1 标题已定（不再承诺 monitor）",
                   ("monitor" not in title.lower()) and len(title) > 20, title[:120]))

    # 4) 摘要首句 necessary, not sufficient
    a = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S)
    ab = " ".join(a.group(1).split()) if a else ""
    checks.append(("4 摘要含 'necessary, not sufficient'",
                   bool(re.search(r"necessary\s*,?\s*(but\s*)?not\s+sufficient", ab, re.I)),
                   ab[:150]))

    # 5) zero-overhead monitor 已改
    z = len(re.findall(r"zero-overhead", t, re.I))
    checks.append(("5 'zero-overhead' 计数（应 0 或仅出现在否定/改写语境）", z == 0, f"出现 {z} 次"))

    # 6) Simpson / 数据集混杂
    s = re.findall(r"Simpson|dataset confound|confound", t, re.I)
    checks.append(("6 已写入 Simpson/数据集混杂", len(s) >= 1, f"命中 {len(s)} 次"))

    # 7) highlights r=1.000 加限定
    hv = re.findall(r"1\.000|r\s*=\s*1\.0+", h)
    checks.append(("7 highlights 的 r=1.000 已加限定",
                   len(hv) == 0 or bool(re.search(r"within|confound|dataset|pooled", h, re.I)),
                   f"highlights 中 1.000 出现 {len(hv)} 次；含限定词="
                   f"{bool(re.search(r'within|confound|dataset|pooled', h, re.I))}"))

    # 8) four decimals -> three decimals
    fd = len(re.findall(r"four decimals", t, re.I))
    td = len(re.findall(r"three decimals", t, re.I))
    # item 8 的判据必须绑定「目标量」（摘要里 $r{=}1.000$ 的精度声明），
    # 而不是「four decimals 出现次数」——稿中另有一处 four decimals 用在
    # 多 seed Pearson $1.0000$（归档 0.9999917）上，那句话是正确的。
    hdr = ab  # 整个摘要（先前误限 600 字符，而 three decimals 在第 800+ 字符处）
    checks.append(("8 摘要精度声明已改（three decimals 且无 four decimals）",
                   ("three decimals" in hdr) and ("four decimals" not in hdr),
                   "摘要内 three=" + str(hdr.count("three decimals")) + " ｜ "
                   "全文 four=" + str(fd) + "（另一处用在多 seed Pearson，正确）"))

    # 9) 检索表述
    checks.append(("9 摘要含检索相关修正表述",
                   bool(re.search(r"retriev", ab, re.I)), ab[-160:]))

    # 3) 组内 τ 结论是否已写入
    wt = re.findall(r"within-dataset|within dataset|within one dataset", t, re.I)
    checks.append(("3 组内（within-dataset）分析已写入", len(wt) >= 1, f"命中 {len(wt)} 次"))

    # 10) 门禁/编译
    lg = REPO / "paper_a1" / "main.log"
    if lg.exists():
        L = io.open(lg, encoding="utf-8", errors="replace").read()
        err = len(re.findall(r"^!", L, re.M))
        und = len(re.findall(r"(Citation|Reference) .* undefined", L))
        pg = re.search(r"Output written on main\.pdf \((\d+) pages", L)
        checks.append(("10 编译：0 错误 / 0 未定义", err == 0 and und == 0,
                       f"错误 {err} ｜ 未定义 {und} ｜ {pg.group(1) if pg else '?'} 页"))
    else:
        checks.append(("10 编译", False, "无 main.log"))

    ok = 0
    for name, passed, ev in checks:
        print(f"  {'✅' if passed else '🔴'} {name}")
        print(f"       {ev}")
        ok += 1 if passed else 0
    print()
    print(f"  → {ok}/{len(checks)} 项通过")
    return 0 if ok == len(checks) else 2


if __name__ == "__main__":
    raise SystemExit(main())
