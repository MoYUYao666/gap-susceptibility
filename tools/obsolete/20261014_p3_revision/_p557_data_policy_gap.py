# -*- coding: utf-8 -*-
r"""核查 GitHub 仓库与 README，并改 Data statement 以符合 PRL 的 Option C（2026-10-13）。

## 一、PRL 的硬要求（Guide 原文）

> **Research data deposit, citation and linking** —
> *For this journal, **Option C** instructions from our research data guidelines apply.
> This means that you are **required** to:*
> - ***Deposit your research data in a relevant data repository.***
> - ***Cite and link to this dataset in your article.***
> - *If this is not possible, make a statement explaining why research data cannot be shared.*
>
> **Data statement** — *you are **required** to state the availability of any data at submission.*

**⇒ 即：**① 数据要存仓库；② 正文要引用并链接；③ 不行就说明原因；④ 必须交 Data statement。**
**（Guide 里没有"必须开 GitHub"的条款 —— 要求的是"数据仓库 + 引用链接"，代码可用仓库承载。）**

## 二、本脚本要查

1. `publish_clean/` 的 README 是否足够详细（能否让第三方按它复现）
2. 当前 Data statement 的措辞与 Option C 的差距
3. 是否已有可引用的数据集标识（DOI / 仓库名）

    python tools\_p557_data_policy_gap.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 100)
    print("① GitHub 发布仓库（`publish_clean/`）的 README")
    print("=" * 100)
    pc = REPO / "publish_clean"
    if not pc.exists():
        print("  ⚠️ 无 publish_clean/")
    else:
        rms = sorted(pc.glob("README*"))
        print(f"  找到 README {len(rms)} 个")
        for r in rms:
            t = io.open(r, encoding="utf-8", errors="replace").read()
            print(f"  ── {r.name}（{len(t):,} 字符 / {len(t.splitlines())} 行）")
            print("     小节：")
            for m in re.finditer(r"^(#{1,3})\s*(.+)$", t, re.M):
                print(f"       {'  ' * (len(m.group(1)) - 1)}{m.group(2)[:70]}")
        # 关键要素检查
        allrm = "".join(io.open(r, encoding="utf-8", errors="replace").read()
                        for r in rms) if rms else ""
        print()
        print("  复现要素检查：")
        for label, pat in (("安装/环境", r"pip install|conda|requirements|environment"),
                           ("数据获取", r"dataset|download|Alpaca|COCO|Flickr"),
                           ("模型获取", r"model|checkpoint|huggingface|HF_HUB"),
                           ("复现命令", r"python\s+\S+\.py|bash\s"),
                           ("结果位置", r"outputs/|results"),
                           ("硬件要求", r"GPU|VRAM|4060|A800"),
                           ("许可", r"[Ll]icense|MIT|Apache|CC BY"),
                           ("引用", r"[Cc]itation|cite|BibTeX")):
            n = len(re.findall(pat, allrm, re.I))
            print(f"     {'✅' if n else '🔴'} {label:<12} {n} 处")

    print()
    print("=" * 100)
    print("② 当前 Data statement（稿件）")
    print("=" * 100)
    main_tex = io.open(REPO / "paper3" / "paper_ieee" / "main.tex",
                       encoding="utf-8", errors="replace").read()
    m = re.search(r"\\section\*\{Data statement\}(.*?)(?=\\section\*|\\bibliographystyle)",
                  main_tex, re.S)
    if m:
        print("  " + " ".join(m.group(1).split()))
    else:
        print("  🔴 未找到 Data statement")
    print()
    print("  **与 Option C 的差距**：")
    print("     Guide 要求：**deposit 数据到仓库 + 正文引用链接**（不行则说明原因）")
    cur = " ".join(m.group(1).split()) if m else ""
    for label, ok in (("提到公共数据集", "public" in cur.lower()),
                      ("提到本项目产出的归档", "JSON" in cur or "archived" in cur),
                      ("给出仓库链接/DOI", bool(re.search(r"https?://|doi|10\.\d{4}", cur))),
                      ("承诺公开", "public" in cur.lower()),
                      ("说明不能共享的原因（若适用）", False)):
        print(f"     {'✅' if ok else '🔴'} {label}")

    print()
    print("=" * 100)
    print("③ 是否有可引用的数据集标识")
    print("=" * 100)
    for pat, label in ((r"zenodo", "Zenodo"), (r"figshare", "figshare"),
                       (r"mendeley", "Mendeley Data"), (r"10\.\d{4,}/", "DOI")):
        n = 0
        for f in list((REPO / "paper3").rglob("*.tex")) + list((REPO / "docs").rglob("*.md")):
            if ".bak" in f.name:
                continue
            try:
                t = io.open(f, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            n += len(re.findall(pat, t, re.I))
        print(f"  {'✅' if n else '🔴'} {label:<14} {n} 处")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
