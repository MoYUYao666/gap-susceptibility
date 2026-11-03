# -*- coding: utf-8 -*-
r"""汇总 A1 的「编辑/审稿意见」与「我们的改动」（2026-10-12）。

来源：
- HANDOFF「A1 被 Neurocomputing 拒稿」条目（邮件逐字事实）
- `docs/A1_REVIEWER_RESPONSE_PLAN.md`（PRL 的 R1 六条 + R2 五条）
- `docs/A1_RESUBMISSION_MASTER_PLAN.md`、`docs/A1_HARDENING.md`（实际改动）

    python tools\_p198_a1_history.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "a1_history.json"


def grab(path: Path, pat: str, width: int = 700, n: int = 3):
    if not path.exists():
        return []
    t = io.open(path, encoding="utf-8", errors="replace").read()
    out = []
    for m in list(re.finditer(pat, t, re.S))[:n]:
        out.append(" ".join(t[max(0, m.start() - 120):m.start() + width].split()))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 86)
    print("① NEUCOM 拒稿信（逐字事实）")
    print("=" * 86)
    h = REPO / "HANDOFF.md"
    for seg in grab(h, r"NEUCOM-D-26-20952", width=1500, n=1):
        print("  " + seg[:1500])

    print()
    print("=" * 86)
    print("② PRL 的 R1 六条 + R2 五条（`docs/A1_REVIEWER_RESPONSE_PLAN.md`）")
    print("=" * 86)
    plan = REPO / "docs" / "A1_REVIEWER_RESPONSE_PLAN.md"
    if plan.exists():
        t = io.open(plan, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"\|\s*\*\*(\d\.\d)\*\*\s*\|([^|]{0,220})\|", t):
            print(f"  {m.group(1)}  {m.group(2).strip()[:200]}")
        print()
        # 关键反驳合集
        i = t.find("关键反驳合集")
        if i > 0:
            print("  ── 关键反驳合集 ──")
            print("  " + " ".join(t[i:i + 1400].split())[:1400])

    print()
    print("=" * 86)
    print("③ 我们的改动记录（A1_RESUBMISSION_MASTER_PLAN / A1_HARDENING）")
    print("=" * 86)
    mp = REPO / "docs" / "A1_RESUBMISSION_MASTER_PLAN.md"
    if mp.exists():
        t = io.open(mp, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"^#+ .*$", t, re.M):
            print("  " + m.group(0)[:110])

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps({
            "rejection": {
                "id": "NEUCOM-D-26-20952", "journal": "Neurocomputing",
                "date": "2026-10-10", "stage": "desk reject (initial evaluation)",
                "reasons": ["not appropriate for this journal's readership",
                            "falls within the aim and scope of our journal, it did not meet the significance level required"],
                "reviewer_comments": "none (Comments to Authors and Editor's comments both empty)",
                "transfer_deadline": "Nov 08 2026 11:59PM",
            },
            "prior_rejection": {"id": "PRLETTERS-D-26-01941", "date": "2026-09-14",
                                "reviewers": "R1 six points + R2 five points"},
        }, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
