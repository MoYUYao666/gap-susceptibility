# -*- coding: utf-8 -*-
r"""把三份纯文本回复写入修订包 README，并说明 EM 的「三个回复框」（2026-10-13）。

    python tools\_p551_update_readme_three_boxes.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
README = REPO / "SUBMISSION" / "P3_PRL_revision" / "README.md"
OUTDIR = REPO / "SUBMISSION" / "P3_PRL_revision" / "response"

MARK = "三个回复框"
SECTION = """
## ⚠️ EM 的回复界面：「**每个审稿人一个回复框**」（不是逐条一个框）

操作者 2026-10-13 澄清：**EM 的 Response to Reviewers 是对每个审稿人给一个输入框。**
⇒ 本包按此提供**三份独立、自足、可直接整段粘贴**的回复：

| 文件 | 对应回复框 | 内部覆盖 | 规模 |
|---|---|---|---|
| **`response/P3_RESPONSE_Reviewer1_plain.txt`** | **Reviewer 1** | 他的 **4 条 Weaknesses**（W1–W4） | 8,200 字符 |
| **`response/P3_RESPONSE_Reviewer2_plain.txt`** | **Reviewer 2** | 他的 **5 条编号意见**（1–5） | 7,930 字符 |
| **`response/P3_RESPONSE_Reviewer3_plain.txt`** | **Reviewer 3** | 他的 **23 条编号意见**（1–23） | 26,257 字符 |

**每条内部格式**：
```
Point N. <审稿人的该条意见原文>
Response: <我方回复>
```

### 用哪个文件

| 用途 | 用哪个 |
|---|---|
| **粘进 EM 的三个回复框** | **`*_plain.txt`**（**纯文本，无 LaTeX/Markdown 记号**） |
| 生成 PDF/Word 版回复信 | `P3_RESPONSE_Reviewer{1,2,3}.txt`（Markdown 版） |
| 一份完整存档（33 条，按审稿人分组） | `P3_RESPONSE_LETTER.md` / `.txt` |

### ⚠️ 三个已知的对应关系细节

1. **Reviewer 1 的 W2 含两个子问题**（唯一性 vs 熵正则最优性 ＋ 为何用 |Γ|），
   我们分为 *(1)* 与 *(2)* 两段回答。
2. **Reviewer 3 的第 20–23 条**是**未编号的补充段落**（原意见里连着写），
   我们按内容切为 4 条并在回复中标注。
3. **审稿人原文里的数学记号保持原样**（如 `\(|x\|^2\)`）——那是他们写的，**不改**；
   只有我方回复做了可读化。

### 生成与核验（可重跑）

```bash
python tools/_p547_make_three_responses.py --apply    # 三份 Markdown 版（按审稿人分组）
python tools/_p548_plaintext_responses.py --apply     # 三份纯文本版（EM 粘贴用）
python tools/_p550_check_plain_readability.py         # 可读性核验（LaTeX 命令 0 / 裸 $ 0 / ** 0）
```
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(README, encoding="utf-8", errors="replace").read()
    print(f"  README {len(t):,} 字符 ｜ 已含「{MARK}」: {MARK in t}")
    if MARK in t:
        print("  已更新")
        return 0
    if not a.apply:
        print("  （预演）")
        return 0
    # 插在「本次修订的 11 项变更」之前
    k = t.find("## 本次修订的 11 项变更")
    if k < 0:
        k = t.find("## ⚠️ 提交前必办")
    if k < 0:
        t = t.rstrip() + "\n" + SECTION
    else:
        t = t[:k] + SECTION.strip() + "\n\n" + t[k:]
    io.open(README, "w", encoding="utf-8", newline="").write(t.rstrip() + "\n")
    t2 = io.open(README, encoding="utf-8", errors="replace").read()
    for k2 in (MARK, "P3_RESPONSE_Reviewer1_plain.txt", "W1–W4", "26,257"):
        print(f"  {'✅' if k2 in t2 else '🔴'} {k2}")
    print(f"  → {len(t2):,} 字符")
    # 列出 response/ 目录
    print()
    print("  response/ 目录：")
    for p in sorted(OUTDIR.iterdir()):
        if p.is_file():
            print(f"     {p.name:<42} {p.stat().st_size:>8,} B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
