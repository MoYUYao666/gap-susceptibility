# -*- coding: utf-8 -*-
r"""Paper A 投稿前审核 —— 新面审计（2026-10-05）。

## 为什么新写一个

已有的审计（`tools/audit/check_paperA.py`、`tools/_pa_final_check_nc.py`、
`tools/_pa_verify_core_claims.py`、`docs/CITATION_INTEGRITY_AUDIT.md` 等）**已覆盖**：
引用键匹配、编译、摘要词数、声明齐备、核心主张复算、图来源、`k` 的溯源。

**本脚本覆盖尚未查过的面**：

| # | 检查 | 为什么重要 |
|---|---|---|
| 1 | **引用渲染计数**（作者-年份制） | 终检脚本按 `[n]` 数字制统计，报"0 处"——**它自己的 bug**；需确认 PDF 里引用真的渲染了 |
| 2 | **`\ref` 目标完整性** | 有无指向不存在 label 的引用（会渲染成 `??`） |
| 3 | **重复 label** | 重复定义会导致引用静默指向错误位置 |
| 4 | **占位符 / TODO 残留** | 未填内容 |
| 5 | **图文件存在性** | `\includegraphics` 指向的文件是否都在 |
| 6 | **表格/图编号连续性** | 缺号说明有对象丢失 |
| 7 | **摘要 vs 正文数字一致性** | 摘要是审稿人首先读的，与正文冲突最致命 |
| 8 | **`\cite` 键是否都在 bib** | （已有脚本覆盖，此处复核并给出逐条清单） |

    python tools\_audit_paperA_preflight.py
"""
from __future__ import annotations

import io
import re
import subprocess
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
SEC = PA / "sections"
PDF = PA / "main_nc.pdf"


def body_text() -> str:
    """所有 section 文件的拼接（不含 main 的前置块）。"""
    out = []
    for f in sorted(SEC.glob("*.tex")):
        out.append(io.open(f, encoding="utf-8", errors="ignore").read())
    return "\n".join(out)


def pdf_text() -> str:
    if not PDF.exists():
        return ""
    r = subprocess.run(["pdftotext", str(PDF), "-"], capture_output=True)
    return r.stdout.decode("utf-8", "ignore")


def main() -> int:
    t = body_text()
    pt = pdf_text()
    problems: list[str] = []

    print("=== ① 引用渲染计数（作者-年份制）===")
    # 'Radford et al. (2021)' / 'Liu et al. (2026)' / '(Schrodi et al., 2025)'
    pat1 = re.compile(r"[A-Z][a-zA-Z\-]+(?:\s+(?:et\s+al\.|and\s+[A-Z][a-zA-Z\-]+))?\s*\(\d{4}[a-z]?\)")
    pat2 = re.compile(r"\([A-Z][a-zA-Z\-]+(?:\s+(?:et\s+al\.|and\s+[A-Z][a-zA-Z\-]+))?,\s*\d{4}[a-z]?\)")
    n1, n2 = len(pat1.findall(pt)), len(pat2.findall(pt))
    print(f"  'X et al. (YYYY)' 形式: {n1} 处 ｜ '(X, YYYY)' 形式: {n2} 处 ｜ 合计 {n1+n2}")
    if n1 + n2 == 0:
        problems.append("PDF 中未检出任何作者-年份引用")
    else:
        print("  → ✅ 引用已渲染（前版本脚本按数字制统计故报 0，属其自身缺陷）")

    print("\n=== ② \\ref 目标完整性 ===")
    labels = set(re.findall(r"\\label\{([^}]+)\}", t))
    refs = set(re.findall(r"\\ref\{([^}]+)\}", t))
    missing = sorted(refs - labels)
    print(f"  labels {len(labels)} ｜ refs {len(refs)} ｜ 悬空 ref: {len(missing)}")
    if missing:
        problems.append(f"悬空 \\ref: {missing}")
        print("  ❌ " + ", ".join(missing))
    else:
        print("  ✅ 无悬空引用")
    if "??" in pt:
        problems.append("PDF 含 '??'（未解析引用）")
        print("  ❌ PDF 中出现 '??'")
    else:
        print("  ✅ PDF 无 '??'")

    print("\n=== ③ 重复 label ===")
    dup = [k for k, v in Counter(re.findall(r"\\label\{([^}]+)\}", t)).items() if v > 1]
    print(f"  重复: {len(dup)}" + (f" → {dup}" if dup else " ✅"))
    if dup:
        problems.append(f"重复 label: {dup}")

    print("\n=== ④ 占位符 / TODO 残留 ===")
    ph = []
    for f in list(SEC.glob("*.tex")) + [PA / "main_nc.tex"]:
        s = io.open(f, encoding="utf-8", errors="ignore").read()
        for m in re.finditer(r"(TODO|FIXME|XXX|TBD|PLACEHOLDER|\\\\todo)", s, re.I):
            ph.append(f"{f.name}:{m.group(0)}")
    print(f"  命中: {len(ph)}" + (f" → {ph[:6]}" if ph else " ✅"))
    if ph:
        problems.append(f"占位符残留: {ph[:6]}")

    print("\n=== ⑤ 图文件存在性 ===")
    figs = set(re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", t))
    miss_f = []
    for g in sorted(figs):
        p = PA / g if not g.startswith("figures/") else PA / g
        if not p.exists():
            miss_f.append(g)
    print(f"  引用图 {len(figs)} 个 ｜ 缺文件: {len(miss_f)}")
    for g in miss_f:
        print(f"  ❌ {g}")
    if miss_f:
        problems.append(f"缺图文件: {miss_f}")
    else:
        print("  ✅ 全部存在")

    print("\n=== ⑥ 编号连续性（图/表分别计数）===")
    # 修正两处自身缺陷：
    #  ① 原写法用 (fig|tab) 把两类 label 一起数 → 图 12 对 20、表 7 对 20，**两个假问题**；
    #  ② 表也可能是 longtable（supplement.tex 就用了 `\begin{longtable}`），只数 table 会漏。
    envs = {"figure": r"\\begin\{figure\}", "table": r"\\begin\{(?:long)?table\*?\}"}
    pres = {"figure": "fig", "table": "tab"}
    names = {"figure": "图", "table": "表"}
    for env in ("figure", "table"):
        n = len(re.findall(envs[env], t))
        lab = len(re.findall(r"\\label\{" + pres[env] + r":", t))
        ok = "✅ 一致" if n == lab else f"⚠ 不一致（{n} vs {lab}）"
        print(f"  {names[env]}: {n} 个环境 ｜ {lab} 个 label ｜ {ok}")
        if n != lab:
            problems.append(f"{names[env]}的环境数与 label 数不符（{n} vs {lab}）")

    print("\n=== ⑦ 摘要 vs 正文数字一致性 ===")
    main = io.open(PA / "main_nc.tex", encoding="utf-8", errors="ignore").read()
    m = re.search(r"\\begin\{abstract\}([\s\S]*?)\\end\{abstract\}", main)
    abstract = m.group(1) if m else ""
    nums = set(re.findall(r"\$?(\d+\.\d+)\$?", abstract))
    print(f"  摘要中的小数: {sorted(nums) if nums else '（无）'}")
    for v in sorted(nums):
        print(f"    {v}: 正文出现 {t.count(v)} 次" + ("" if t.count(v) else "  ⚠ 正文未见"))
    r2 = re.findall(r"0\.9\d+", abstract)
    if r2:
        print(f"  摘要中的 R²: {r2} ｜ 正文含 0.986: {'0.986' in t}")

    print("\n=== ⑧ \\cite 逐条核对 ===")
    keys = set()
    for m2 in re.finditer(r"\\cite\{([^}]+)\}", t):
        for k in m2.group(1).split(","):
            keys.add(k.strip())
    bib = io.open(PA / "references.bib", encoding="utf-8", errors="ignore").read()
    bk = set(re.findall(r"@\w+\{([^,]+),", bib))
    print(f"  正文引用 {len(keys)} 个键 ｜ bib {len(bk)} 条 ｜ 缺失: {sorted(keys - bk) or '无'} ｜ 未使用: {sorted(bk - keys) or '无'}")
    if keys - bk:
        problems.append(f"引用缺失: {sorted(keys - bk)}")
    if bk - keys:
        problems.append(f"未使用条目: {sorted(bk - keys)}")

    print("\n" + "=" * 60)
    if problems:
        print(f"❌ 发现 {len(problems)} 项问题：")
        for p in problems:
            print("  • " + p)
    else:
        print("✅ 新面审计全部通过")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
