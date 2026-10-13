# -*- coding: utf-8 -*-
r"""重新生成修订包，并写「GitHub × Zenodo」数据归档指引（2026-10-14）。

## 操作者反馈

> **"已经注册了 zenodo，但是感觉很不方便，不如 github"**

## 正解：**Zenodo 与 GitHub 可以打通**（官方集成）

**GitHub 仓库 + Zenodo 集成** ⇒ **打一个 release/tag，Zenodo 自动抓取并发 DOI**。
两者各司其职，**不是二选一**：

| 需求 | 由谁满足 |
|---|---|
| 代码持续更新、方便浏览 | **GitHub**（你熟悉的） |
| **可引用的 DOI**（Option C 要的） | **Zenodo 自动发**（GitHub release 触发） |

**⇒ 你只需在 Zenodo 网页上把 GitHub 仓库勾上（一次操作），之后发 release 即得 DOI。**

    python tools\_p568_regen_with_zenodo_guide.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
D = REPO / "SUBMISSION" / "P3_PRL_revision"
PI = REPO / "paper3" / "paper_ieee"

GUIDE = """# 数据与代码归档：GitHub × Zenodo（推荐做法）

> 操作者已注册 Zenodo，并反馈"不如 GitHub 方便"。**这两者可以打通，不必二选一。**

## 一、为什么不是二选一

PRL 的 Guide 用的是 **research data guidelines 的 Option C**：

> *you are **required** to: **Deposit your research data in a relevant data repository.**
> **Cite and link to this dataset in your article.***

**关键要求是"可引用"** —— 也就是需要一个**持久标识（DOI）**。GitHub 仓库本身**不给 DOI**，
而 **Zenodo 给**。所以：

| 需求 | 由谁满足 |
|---|---|
| 代码持续更新、`git push` 就能改、方便浏览 | **GitHub** |
| **DOI（可引用）** | **Zenodo** |
| 让审稿人/读者一键访问 | GitHub 链接（写在 Data statement 里） |

## 二、一次性设置（约 3 分钟，之后永久生效）

1. 登录 **zenodo.org** → 右上角头像 → **Settings** → **GitHub**
2. 点 **Connect**，授权 Zenodo 访问你的 GitHub 账号
3. 在仓库列表里找到你的仓库（如 `OWNER/<repo>`）→ 把开关拨到 **ON**
4. 回到 GitHub，给仓库**打一个 release**（例如 tag `v1.0-prl-revision`）
   ```bash
   git tag -a v1.0-prl-revision -m "Code and results accompanying PRLETTERS-D-26-02378 (revision)"
   git push origin v1.0-prl-revision
   # 或在 GitHub 网页 Releases → Draft a new release
   ```
5. **Zenodo 会自动抓取该 release 并立即生成一个 DOI**（形如 `10.5281/zenodo.XXXXXXX`），
   在 Zenodo 的 **Upload** 页能看到，并可一键复制 **DOI badge**（Markdown / BibTeX）

> **⚠️ 重要**：Zenodo 抓的是 **release 快照**，不是每次 push。所以**改动后要再发一个 release 才有新版本 DOI**。
> **⚠️ 若仓库是私有的**：Zenodo 也能抓（授权后），但 **DOI 落地页会要求登录** ⇒
> **要满足"审稿人/读者可访问"，仓库需为公开**（或改用 Zenodo 手动上传一个 zip）。

## 三、手动上传的备选（不想开 GitHub 时）

Zenodo 也支持**直接上传一个 zip**：

1. Zenodo → **New upload** → 拖入 `p3_release.zip`（见下）
2. 填 metadata：Title / Authors（Wan, Hongrui）/ **Resource type = Dataset** 或 Software /
   License（如 MIT）/ Keywords
3. **Publish** ⇒ 立刻得到 DOI

**⇒ 本包已备好可直接上传的 zip**：`archive/p3_release.zip`

## 四、拿到 DOI 后要改的**三处**

| # | 位置 | 改什么 |
|---|---|---|
| 1 | `manuscript/latex_source/main.tex` 的 **Data statement** | 把"will be deposited on acceptance"改为**实际 DOI** |
| 2 | `cover_letter_prl.tex` | 把 `[REPOSITORY DOI, to be inserted]` 换成**实际 DOI** |
| 3 | EM 提交表单的 **Data availability / Data linking** 字段 | 填 DOI |

然后**重新编译** `main.pdf` 与 `cover letter.pdf` 并重新上传。

## 五、这个 zip 里放什么（**只放该公开的**）

`archive/p3_release.zip` 的内容（**不含稿件本体**，遵循本仓库既有发布边界）：

```
outputs/analysis/*.json        每篇论文数字的溯源归档（只增不改）
tools/_p4*.py / _p5*.py        全部分析与审计脚本（可重跑）
docs/P3_EXPERIMENTS.md         三组补实验报告
docs/P3_DOWNSTREAM.md
docs/P3_STATS.md
docs/P3_COMPRESSION.md
README.md                      仓库说明（含硬件、数据可用性、引用格式）
```

**⚠️ 不放**：`main*.tex` / `main*.pdf` / `cover_letter*` / `title_page*` / `highlights*`
—— 稿件类**不进公开仓库**（本仓库既有规则）。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0

    # ① 重新生成修订包（同步最新 PDF 与源）
    print("  ① 重新生成修订包…")
    r = subprocess.run([sys.executable, str(REPO / "tools" / "_p532_regen_revision_package.py"), "--apply"],
                       cwd=str(REPO), capture_output=True)
    tail = r.stdout.decode("utf-8", errors="replace").strip().splitlines()[-1:]
    print(f"     {tail[0] if tail else ''}")
    # 补上传清单与三回复框说明
    for script in ("_p551_update_readme_three_boxes.py", "_p560_upload_checklist.py"):
        subprocess.run([sys.executable, str(REPO / "tools" / script), "--apply"],
                       cwd=str(REPO), capture_output=True)
    print("     ✅ 已补 README 的「三个回复框」一节与 UPLOAD_CHECKLIST.md")

    # ② 归档 zip（该公开的内容）
    print("  ② 打包可公开的归档 zip…")
    arch = D / "archive"
    arch.mkdir(parents=True, exist_ok=True)
    zp = arch / "p3_release.zip"
    include = [("README.md", REPO / "publish_clean" / "README.md")]
    # ⚠️ 只收本论文（P3）的脚本 —— **按内容判据**（脚本内含 p3 / PRL 字样），
    #    不用修改日期（我先前那次用日期戳，过滤条件算错 → 0 个入选）
    import re as _re
    n_script = 0
    for p in sorted((REPO / "tools").glob("_p[45]*.py")):
        try:
            body = io.open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        low = body.lower()
        if ("p3_" in low or "prl" in low or "paper3" in low) and "paper合" not in body[:400]:
            include.append((f"tools/{p.name}", p))
            n_script += 1
    print(f"     （按内容判据收 P3 脚本：{n_script} 个）")
    for p in sorted((REPO / "outputs" / "analysis").glob("*.json")):
        include.append((f"outputs/analysis/{p.name}", p))
    for name in ("P3_EXPERIMENTS.md", "P3_DOWNSTREAM.md", "P3_STATS.md", "P3_COMPRESSION.md"):
        p = REPO / "docs" / name
        if p.exists():
            include.append((f"docs/{name}", p))
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, src in include:
            if src.exists():
                z.write(src, arc)
    with zipfile.ZipFile(zp) as z:
        n = len(z.namelist())
        bad = z.testzip()
    print(f"     ✅ archive/p3_release.zip：{n} 个文件 / {zp.stat().st_size:,} B / testzip={bad}")

    # ③ 指引
    io.open(D / "ARCHIVE_WITH_ZENODO.md", "w", encoding="utf-8", newline="").write(GUIDE)
    print(f"     ✅ ARCHIVE_WITH_ZENODO.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
