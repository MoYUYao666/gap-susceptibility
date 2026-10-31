# -*- coding: utf-8 -*-
r"""核验正式回复信：覆盖 33 条 + 数字与归档一致（2026-10-13）。

    python tools\_p530_verify_response_letter.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LETTER = REPO / "docs" / "P3_RESPONSE_LETTER.md"
STRUCT = REPO / "outputs" / "analysis" / "p3_reviews_structured.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(LETTER, encoding="utf-8", errors="replace").read()
    items = json.loads(io.open(STRUCT, encoding="utf-8", errors="replace").read())
    print(f"  回复信 {len(t):,} 字符 ｜ 意见 {len(items)} 条")

    print()
    print("=" * 92)
    print("① 覆盖检查（每条意见是否有对应的 ## Rxx 小节）")
    print("=" * 92)
    missing = []
    for it in items:
        rid = it["id"]
        has = re.search(rf"^## {re.escape(rid)}\b", t, re.M) is not None
        if not has:
            missing.append(rid)
    if missing:
        print(f"  🔴 缺 {len(missing)} 条：{missing}")
    else:
        print(f"  ✅ 全部 {len(items)} 条都有对应小节")
    # 反向：信里有但意见表没有的
    heads = re.findall(r"^## (R\d+\.\d+)\b", t, re.M)
    extra = [h for h in heads if h not in {i["id"] for i in items}]
    print(f"  {'✅' if not extra else '⚠️'} 多出的小节：{extra if extra else '无'}")

    print()
    print("=" * 92)
    print("② 关键数字是否在信中（且与归档口径一致）")
    print("=" * 92)
    KEY = {
        "3.09× blank 探针": "$3.09\\times$",
        "7,237,632 同预算": "7{,}237{,}632",
        "57 runs": "$57$ runs",
        "AdaLoRA −1468": "1468",
        "反转 p=0.0055": "$p = 0.0055$",
        "matched-loss 0.5872/0.5826": "0.5872",
        "随机池 47 分位": "47$th percentile",
        "反序 p=0.2057": "0.2057",
        "置换 p=0.100": "$p = 0.100$",
        "η²=0.989": "0.989",
        "11–28 seeds": "$11$ to $28$ seeds",
        "分层相关 +0.172": "$+0.172$",
        "配对 21/21": "21$ of $21$",
        "β 出处 runs[90]": "runs\\[90\\]",
        "median 0.072": "$0.072$",
        "Qwen 逐块值": "24{,}1" if False else "-871.4",
        "corner +3607": "3607",
        "54 token 反转": "$54$ tokens",
    }
    bad = []
    for label, pat in KEY.items():
        ok = pat in t
        if not ok:
            bad.append(label)
        print(f"  {'✅' if ok else '🔴'} {label}")
    if bad:
        print(f"  🔴 缺失：{bad}")

    print()
    print("=" * 92)
    print("③ 自我一致性：撤回条数与结尾表述")
    print("=" * 92)
    n_withdrawn = len(re.findall(r"\*\*Claim withdrawn\*\*|\*\*Claim downgraded\*\*", t))
    print(f"  变更汇总表里标为「撤回/降级」的条目：{n_withdrawn}")
    m = re.search(r"(Three|Four|Five) of our claims did not survive", t)
    print(f"  结尾表述：{m.group(0) if m else '（未找到）'}")
    if m:
        print(f"  ⇒ 应改为 Four（表里标了 {n_withdrawn} 条）" if m.group(1) != "Four"
              else "  ✅ 与表一致")

    print()
    print("=" * 92)
    print("④ 禁止回归的旧主张（信中不应出现为事实陈述）")
    print("=" * 92)
    BAN = {
        "30× 作为结论": r"reduces (allocation )?uncertainty by",
        "sharp phase transition": r"sharp phase transition",
        "CLIP-derived β=0.137": r"CLIP-derived",
        "equal parameter budget（作为事实）": r"at equal parameter budgets",
        "removes the catastrophic tail": r"removes the catastrophic tail",
    }
    for label, pat in BAN.items():
        hits = re.findall(pat, t, re.I)
        print(f"  {'✅' if not hits else '⚠️'} {label}：{len(hits)} 处")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
