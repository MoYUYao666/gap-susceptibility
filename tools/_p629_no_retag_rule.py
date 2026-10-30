# -*- coding: utf-8 -*-
r"""Write the "never re-tag after Zenodo is linked" rule into AGENTS.md and CLAUDE.md.

Why this rule exists (my mistake, 2026-10-14): after the GitHub-Zenodo integration created
the first archive, I kept force-moving the tag and deleting/recreating the Release. Zenodo
treats each of those as a new version, so it minted another DOI. The operator now has two
published records for the same snapshot.

Rule: once Zenodo has archived the repository, the tag is frozen. Publish a *new* version
with a *new* tag (v1.1, v1.2, ...) and let Zenodo mint one new version DOI under the same
concept DOI; never move or recreate an existing tag.

    python tools/_p629_no_retag_rule.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

RULE = """
### 🔴🔴 DOI / tag 冻结纪律（2026-10-14 立，因我的操作失误）

> **教训**：Zenodo 归档建好之后，我**又反复强制移动 tag、删除并重建 GitHub Release**
> （`cc9bdac` → `5e1da98` → `e320e75` …）。**Zenodo 把每一次都当成新版本** ⇒
> **同一份快照被铸出了两个 DOI**（`10.5281/zenodo.23341083` 与 `10.5281/zenodo.23341223`），
> 操作者看到的就是"每更新一次 DOI 就变"。

**⇒ 铁律**：

1. **一旦 Zenodo 抓取了某个 tag，该 tag 就冻结** —— **不得** `git tag -d` + 重打，
   **不得** `git push :refs/tags/<tag>`，**不得**删除并重建对应的 GitHub Release。
   （三者都会让 Zenodo 认为是新版本 ⇒ 铸新 DOI。）
2. **要出新版本，就用新 tag**（`v1.1`、`v1.2`…）⇒ Zenodo 会在**同一个概念 DOI**下
   新增一个版本 DOI，DOI 不会"漂移"。
3. **引用规则**：**引用具体版本的 DOI**（Zenodo 官方建议），
   **概念 DOI 用于"始终指向最新版"**。稿件的 Data statement 写具体版本 DOI。
4. **改 README / 元数据这类小修，不值得新铸 DOI**：
   在 Zenodo 记录页直接改描述即可，不动 tag。
5. **需要改 tag 之前，先问操作者** —— 因为这会产生一个新的 DOI，属于对外可见的后果。

**⏸ 当前状态**：`v1.0-prl-revision` **已冻结在 `e320e75`**（对应 Zenodo `23341223`）；
**在操作者决定用哪个 DOI 之前，不再有任何 tag / Release 操作。**
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    for name in ("AGENTS.md", "CLAUDE.md"):
        p = REPO / name
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        if "DOI / tag 冻结纪律" in t:
            print(f"  {name}: already recorded")
            continue
        bak = p.with_suffix(p.suffix + ".bak_p629")
        if not bak.exists():
            shutil.copy2(p, bak)
        k = t.find("## 🔴 发布边界")
        if k < 0:
            k = t.find("## 关键约束")
        t2 = t[:k] + RULE.strip() + "\n\n" + t[k:] if k > 0 else t.rstrip() + "\n" + RULE
        io.open(p, "w", encoding="utf-8", newline="").write(t2)
        print(f"  {name}: {len(t):,} -> {len(t2):,} chars")
    for name in ("AGENTS.md", "CLAUDE.md"):
        t = io.open(REPO / name, encoding="utf-8").read()
        ok = "DOI / tag 冻结纪律" in t and "不得" in t
        print(f"  {'OK ' if ok else 'BAD'} {name} ({len(t.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
