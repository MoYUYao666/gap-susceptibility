# -*- coding: utf-8 -*-
"""把核验 FAIL 的条目从候选清单移入隔离区（不静默删除）。

理由：核验失败的条目**不得进入参考文献表**，但删除会丢失诊断信息。
隔离文件 `refs_quarantined.json` 记录条目原文 + 失败原因 + 处置建议，供人工复核。

    python tools/_quarantine_failed_refs.py
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DIR = REPO / "paper_review"
ALL_REFS = DIR / "refs_all.json"
VERIFIED = DIR / "refs_verified.json"
QUARANTINE = DIR / "refs_quarantined.json"


def main() -> int:
    if not VERIFIED.exists():
        print("先跑 tools/_verify_citations.py 生成 refs_verified.json")
        return 1
    verified = json.loads(VERIFIED.read_text(encoding="utf-8"))
    bad = {r["key"]: r for r in verified if r.get("status") != "PASS"}

    if not ALL_REFS.exists():
        print(f"找不到 {ALL_REFS}")
        return 1
    refs = json.loads(ALL_REFS.read_text(encoding="utf-8"))

    if not bad:
        print("核验结果中没有 FAIL/WEAK → 无需隔离")
        return 0

    moved, kept = [], []
    for e in refs:
        k = (e.get("key") or "").strip().lower()
        if k in bad:
            r = bad[k]
            moved.append({
                "entry": e,
                "status": r["status"],
                "source": r.get("source", ""),
                "title_ratio": r.get("title_ratio", 0),
                "found_title": r.get("found_title", ""),
                "found_doi": r.get("found_doi", ""),
                "reasons": r.get("notes", []),
                "handling": "从参考文献表移除；如需保留该论点，请另找可核验的支撑文献",
            })
        else:
            kept.append(e)

    QUARANTINE.write_text(json.dumps(moved, ensure_ascii=False, indent=2), encoding="utf-8")
    ALL_REFS.write_text(json.dumps(kept, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"隔离 {len(moved)} 条 → {QUARANTINE.relative_to(REPO)}")
    for m in moved:
        print(f"  ❌ {m['entry'].get('key')}：{m['entry'].get('title', '')[:62]}")
        for x in m["reasons"][:2]:
            print(f"       - {x[:110]}")
    print(f"\n候选清单由 {len(refs)} 条缩减为 {len(kept)} 条（仅 PASS 可入表）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
