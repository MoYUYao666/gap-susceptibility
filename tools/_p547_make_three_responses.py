# -*- coding: utf-8 -*-
r"""生成 EM 投稿用的**三个独立回复**（每个审稿人一个回复框）（2026-10-13）。

## 操作者澄清（2026-10-13 14:37）

> **"注意不是逐条回复，是三个回复框对应三个审稿人"**

**⇒ EM 的回复界面对每个审稿人只有一个输入框** ⇒ 要产出**三段独立、自足、可直接整段粘贴**的回复：

| 文件 | 对应 | 内部结构 |
|---|---|---|
| `P3_RESPONSE_Reviewer1.txt` | Reviewer 1 | 开头致谢 → **W1–W4**（他的 4 条 Weaknesses） |
| `P3_RESPONSE_Reviewer2.txt` | Reviewer 2 | 开头 → **1–5**（他的编号点，1:1） |
| `P3_RESPONSE_Reviewer3.txt` | Reviewer 3 | 开头 → **1–23**（他的编号点，1:1） |

**每条内部格式**：`**Point N.** <他的意见要点>` 换行 `**Response:** <回复>`

**⚠️ 内容全部来自**：`docs/P3_RESPONSE_LETTER.md`（33 条，已核验 33/33 + 数字全在）。
**本脚本只做"重新分组与编号对齐"，不改动任何实质内容。**

    python tools\_p547_make_three_responses.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STRUCT = REPO / "outputs" / "analysis" / "p3_reviews_structured.json"
LETTER = REPO / "docs" / "P3_RESPONSE_LETTER.md"
OUTDIR = REPO / "SUBMISSION" / "P3_PRL_revision" / "response"

# 我的 33 条（R1.x / R2.x / R3.x）→ 审稿人原文编号
# R1 原文有 **4 条 Weaknesses**；我的 R1.1/R1.2 是 strengths 致谢（归入开头）。
# ⚠️ W2 实际含**两个问题**（唯一性 vs 熵正则最优性 ＋ 为何用 |Γ|），我分别答在 R3.1 与 R3.8
#    ⇒ **W2 需合成两段**（元组 (label, [rid...])）
MAP_R1 = [
    ("W1", ["R1.5"]),              # 证明缺口
    ("W2", ["R3.1", "R3.8"]),      # 唯一性 vs 最优性 ＋ |Γ| 的方向信息
    ("W3", ["R1.3"]),              # 下游表现
    ("W4", ["R1.4"]),              # 更多架构
]
MAP_R2 = [(str(i), [f"R2.{i}"]) for i in range(1, 6)]
MAP_R3 = [(str(i), [f"R3.{i}"]) for i in range(1, 24)]

HEAD_R1 = """Dear Reviewer 1,

We thank you for the summary, for recognising the problem and for finding the
first-order gradient-coupling interpretation well motivated, and above all for locating a
genuine gap in our proof. Acting on the review changed the paper's claims: we now state the
missing property as an explicit axiom and we prove that it does not follow from the
requirements we had listed. Weakness 1 was the single most valuable comment we received.

Below we answer the four weaknesses in the order you gave them. Every number can be traced
to a script and an archived field, and the archived runs are self-describing.
"""

HEAD_R2 = """Dear Reviewer 2,

We thank you for five pointed comments, three of which required new experiments. We ran
them. Two of the results go against the paper as submitted, and we report them as such
rather than as qualifications: the allocation rule's advantage does not survive our own
controls, and the alignment energy is not a proxy for downstream performance.

Below we answer the five points in the order you gave them. Every number can be traced to a
script and an archived field.
"""

HEAD_R3 = """Dear Reviewer 3,

We thank you for a detailed and technically precise report. Several of your questions
exposed claims we could not sustain, and we have withdrawn or downgraded four of them:
the "sharp phase transition", the "architecture-dependent" finding, the 30x variance ratio,
and the claim that our allocation rule beats the uniform baseline. We also implemented
AdaLoRA at matched budget and swept both methods over the same learning rates; it is better
than any of our arms on this metric, and the paper now says so.

Below we answer your 23 points in the order you gave them. Every number can be traced to a
script and an archived field.
"""

TAIL = """

We are grateful for the specificity of this report. Where our data could not settle a
question you raised, we have said so in the paper rather than leaving the claim standing.
"""


def extract_replies(letter: str):
    """从 docs/P3_RESPONSE_LETTER.md 提取每条回复正文（去掉意见引用块）。"""
    i = letter.find("# Reviewer 1")
    body = letter[i:] if i >= 0 else letter
    parts = re.split(r"^## Comment (R\d+\.\d+)\s*$", body, flags=re.M)
    out = {}
    for k in range(1, len(parts) - 1, 2):
        rid = parts[k].strip()
        txt = parts[k + 1]
        txt = re.sub(r"^(?:> [^\n]*\n)+", "", txt.lstrip("\n"), count=1)
        txt = re.sub(r"\n*---\n+# Reviewer \d+\s*", "\n", txt)
        out[rid] = txt.strip()
    return out


def build(replies, mapping, head, items_by_id, title):
    L = [head, ""]
    for label, rids in mapping:
        # 该点的意见原文（一个点可能对应两个原始意见，取第一个作代表，其余在回复内说明）
        it = items_by_id[rids[0]]
        L.append(f"**Point {label}.** {it['comment']}")
        L.append("")
        if len(rids) == 1:
            L.append(f"**Response:** {replies[rids[0]]}")
        else:
            # 该点含两个子问题 ⇒ 合成一段，明确标出分别回答
            L.append("**Response:** This point raises two separate questions and we answer "
                     "them in turn.")
            L.append("")
            for n, rid in enumerate(rids, 1):
                L.append(f"*({n})* {replies[rid]}")
                L.append("")
        L.append("")
    L.append(TAIL.strip())
    L.append("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    items = json.loads(io.open(STRUCT, encoding="utf-8", errors="replace").read())
    by_id = {it["id"]: it for it in items}
    letter = io.open(LETTER, encoding="utf-8", errors="replace").read()
    replies = extract_replies(letter)
    print(f"  意见 {len(items)} 条 ｜ 从回复信提取 {len(replies)} 条回复")
    miss = [it["id"] for it in items if it["id"] not in replies]
    if miss:
        print(f"  🔴 缺：{miss}")
        return 1

    OUTDIR.mkdir(parents=True, exist_ok=True)
    jobs = [
        ("P3_RESPONSE_Reviewer1.txt", "Reviewer 1", MAP_R1, HEAD_R1),
        ("P3_RESPONSE_Reviewer2.txt", "Reviewer 2", MAP_R2, HEAD_R2),
        ("P3_RESPONSE_Reviewer3.txt", "Reviewer 3", MAP_R3, HEAD_R3),
    ]
    files = []
    for fname, title, mapping, head in jobs:
        text = build(replies, mapping, head, by_id, title)
        n_pts = len(mapping)
        print(f"  {fname:<32} {n_pts:>2} 点 ｜ {len(text):>7,} 字符")
        files.append((OUTDIR / fname, text, n_pts))
        if a.apply:
            io.open(OUTDIR / fname, "w", encoding="utf-8", newline="").write(text)

    if not a.apply:
        print("  （预演）")
        return 0

    print()
    print("  核验：")
    ok = True
    for p, text, n in files:
        got = len(re.findall(r"^\*\*Point ", text, re.M))
        good = got == n
        ok = ok and good
        print(f"  {'✅' if good else '🔴'} {p.name}：{got} 个 Point（应 {n}）")
    # 关键数字
    allt = "".join(t for _, t, _ in files)
    for k in ("$3.09\\times$", "7{,}237{,}632", "0.2057", "$p = 0.100$", "1468"):
        v = k in allt
        ok = ok and v
        print(f"  {'✅' if v else '🔴'} 三份合计保留 {k}")
    print()
    print(f"  **判定：{'✅ 三份齐备' if ok else '🔴 有问题'}**")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
