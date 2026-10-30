# -*- coding: utf-8 -*-
r"""两份稿子的最终检查清单（2026-10-11）。

## A1（投 Neural Networks）

① 五份投稿件是否齐全且干净（旧标题/旧刊名/旧邮箱 0 残留）
② 摘要词数 ≤250｜关键词 1–6｜highlights 3–5 条 ≤85 字符
③ 56 条文献全为 APA（作者-年、字母序、无未定义引用）
④ PDF 是否最新

## paper合

⑤ 门禁 + 统计审核
⑥ 旧数字残留扫描
⑦ 编译（Spring / NC）
⑧ 投稿包是否齐备

    python tools\_final_review.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "paper_a1"
HE = REPO / "paper合"
PY = sys.executable


def sh(cmd, cwd=None):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", cwd=cwd or str(REPO), shell=True)


def pdf_pages(p: Path):
    if not p.exists():
        return None
    o = sh(f'pdfinfo "{p}"').stdout
    m = re.search(r"Pages:\s+(\d+)", o)
    return int(m.group(1)) if m else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    fails = []

    # ══════════ A1 ══════════
    print("=" * 84)
    print("A1 —— 投稿件（Neural Networks）")
    print("=" * 84)
    FILES = ["main.tex", "cover_letter.tex", "declaration.tex", "highlights.tex",
             "abstract.tex", "related_work.tex"]
    STALE = [("Order Preservation Governs Zero-Shot Robustness", "旧标题"),
             ("Neurocomputing", "旧刊名"),
             ("hrw1n24@soton.ac.uk", "我写错的邮箱"),
             ("16 September 2026", "旧日期")]
    for name in FILES:
        f = A1 / name
        if not f.exists():
            print(f"  ❌ {name} 缺失")
            fails.append(f"A1/{name} 缺失")
            continue
        t = io.open(f, encoding="utf-8", errors="replace").read()
        hits = [tag for pat, tag in STALE if pat in t]
        print(f"  {'✅' if not hits else '🔴'} {name:<22} "
              + ("干净" if not hits else "残留: " + "｜".join(hits)))
        if hits:
            fails.append(f"A1/{name} {hits}")

    # 摘要词数
    t = io.open(A1 / "main.tex", encoding="utf-8", errors="replace").read()
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S)
    if m:
        b = re.sub(r"\\[a-zA-Z]+", " ", m.group(1))
        b = re.sub(r"[{}$\\]", " ", b)
        wc = len(b.split())
        print(f"  {'✅' if wc <= 250 else '🔴'} 摘要 {wc} 词（限 250）")
        if wc > 250:
            fails.append(f"A1 摘要 {wc} 词超限")
    # 关键词
    m = re.search(r"\\keywords\{(.*?)\}", t, re.S)
    if not m:
        m = re.search(r"\\begin\{keyword\}(.*?)\\end\{keyword\}", t, re.S)
    nkw = m.group(1).count("\\sep") + 1 if m else 0
    print(f"  {'✅' if 1 <= nkw <= 6 else '🔴'} 关键词 {nkw} 个（限 1–6）")
    if not (1 <= nkw <= 6):
        fails.append(f"A1 关键词 {nkw}")
    # highlights
    h = io.open(A1 / "highlights.tex", encoding="utf-8", errors="replace").read()
    items = [re.sub(r"\\[a-zA-Z]+", "", x).strip()
             for x in re.findall(r"\\item\s+(.+)", h)]
    over = [i for i in items if len(i) > 85]
    print(f"  {'✅' if 3 <= len(items) <= 5 and not over else '🔴'} "
          f"highlights {len(items)} 条（限 3–5），超 85 字符 {len(over)} 条")
    if not (3 <= len(items) <= 5) or over:
        fails.append("A1 highlights")
    # 文献
    n_bib = len(re.findall(r"\\bibitem\[[^\]]*\]\{[^}]*\}", t))
    n_nolab = len(re.findall(r"\\bibitem\{", t))
    print(f"  {'✅' if n_bib and not n_nolab else '🔴'} 文献 {n_bib} 条，缺 label {n_nolab}")
    if not n_bib or n_nolab:
        fails.append("A1 文献 label")
    # PDF
    for name in ("main", "cover_letter", "declaration", "highlights", "abstract"):
        tex, pdf = A1 / f"{name}.tex", A1 / f"{name}.pdf"
        if tex.exists() and pdf.exists():
            newer = pdf.stat().st_mtime >= tex.stat().st_mtime
            pg = pdf_pages(pdf)
            print(f"  {'✅' if newer else '⚠️'} {name:<14} {pg} 页"
                  + ("" if newer else "  ← PDF 比 tex 旧"))
            if not newer:
                fails.append(f"A1/{name}.pdf 过期")

    # ══════════ paper合 ══════════
    print()
    print("=" * 84)
    print("paper合 —— 数据、门禁、编译")
    print("=" * 84)
    r = sh([PY, "tools/_claim_ledger.py", "--apply"])
    ok = r.returncode == 0
    line = next((l.strip() for l in (r.stdout or "").splitlines()
                 if "汇总" in l or "通过" in l and "失败" in l), "")
    m = re.search(r"通过 (\d+) ｜ ❌ 失败 (\d+)", r.stdout or "")
    print(f"  {'✅' if ok else '🔴'} 门禁：" + (m.group(0) if m else line[:70]))
    if not ok:
        fails.append("paper合 门禁")

    r = sh([PY, "tools/_audit_statistics.py", "--apply"])
    m = re.search(r"审核汇总：(\d+)/(\d+) 项数字匹配 ｜ 问题 (\d+) 个", r.stdout or "")
    aok = bool(m) and m.group(3) == "0"
    print(f"  {'✅' if aok else '🔴'} 统计审核：" + (m.group(0) if m else "未解析"))
    if not aok:
        fails.append("paper合 统计审核")

    r = sh([PY, "tools/_p178_scan_stale_numbers.py"])
    m = re.search(r"旧数字残留总计: (\d+)", r.stdout or "")
    sok = bool(m) and m.group(1) == "0"
    print(f"  {'✅' if sok else '🔴'} 旧数字残留：" + (m.group(0) if m else "未解析"))
    if not sok:
        fails.append("paper合 旧数字残留")

    for m_ in ("main_springer", "main_nc"):
        pdf, log = HE / f"{m_}.pdf", HE / f"{m_}.log"
        pg = pdf_pages(pdf)
        err = un = ov = "?"
        if log.exists():
            tt = io.open(log, encoding="utf-8", errors="replace").read()
            err = len(re.findall(r"^!", tt, re.M))
            un = len(re.findall(r"(Citation|Reference) .* undefined", tt))
            ov = len(re.findall(r"Overfull \\hbox", tt))
        good = (err == 0 and un == 0)
        print(f"  {'✅' if good else '🔴'} {m_:<16} {pg} 页 ｜ 错误 {err} ｜ "
              f"未定义 {un} ｜ Overfull {ov}")
        if not good:
            fails.append(f"paper合 {m_} 编译")

    # 投稿包
    ncs = HE / "NC_submission"
    if ncs.exists():
        n = len(list(ncs.rglob("*")))
        print(f"  ✅ 投稿包 NC_submission/ 存在（{n} 个条目）")
    else:
        print("  ⚠️ NC_submission/ 不存在")

    print()
    print("=" * 84)
    print(f"检查结论：{'✅ 全部通过' if not fails else '🔴 ' + str(len(fails)) + ' 项未通过'}")
    for f in fails:
        print("  ❌ " + f)
    print("=" * 84)
    return 0 if not fails else 2


if __name__ == "__main__":
    raise SystemExit(main())
