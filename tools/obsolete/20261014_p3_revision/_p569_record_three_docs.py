# -*- coding: utf-8 -*-
r"""落账：三件文案更新 + 判据加强抓出 13 处断头 + Zenodo×GitHub 指引（2026-10-14）。

    python tools\_p569_record_three_docs.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📄 2026-10-14 03:00 —— cover letter / title page / highlights 三件全部重写；判据加强又抓出 13 处断头；Zenodo×GitHub 指引已写**
>
> ### 一、🔴 三件文案原本都在**宣传已撤回的主张**
>
> | 文案 | 旧内容 | 处置 |
> |---|---|---|
> | **cover letter** | *"the **unique** scalar satisfying five requirements"* | 改为**需额外假设 R3$'$**（含反例） |
> | | *"an alignment-energy **phase transition with a critical rank**"* | 改为 **bracketed**，且属测量协议 |
> | | *"random allocation suffers a **$30\\times$** larger sd"* | **删除** |
> | | *"**190 runs** (181+9)"* | 改为 **126 + 57 runs** |
> | | *"which we attribute to **architectural differences**"* | **撤回**（token 预算伪影） |
> | | **无篇幅说明、无数据可用性** | **新增两段**（Guide 的 7 页 + Option C） |
> | **highlights** | *"the **unique** admissible allocation statistic"* | 改为"canonical" |
> | | *"A **critical rank** separates safe/damaging/collapsing"* | 改为**诚实的四条**（含"未胜对照"与"AdaLoRA 更优"） |
> | | *"predicts allocation **uncertainty**"* | **删除** |
> | **title page** | 7 处 `oindent`（已印进 PDF） | 修 |
>
> **⇒ cover letter 4,331 → 5,973 字符**；**highlights 五条全部 ≤85 字符**（Guide 上限）；
> **复核：`unique`/`sharp 相变`/`critical rank`/`190 runs`/`30×`/`架构差异`/`不确定性` 残留全 0。**
>
> ### 二、🔴 我的第 34 个错：断头命令的判据仍有漏洞
>
> 我先前判据是「行首 token 命中白名单 **且** 前一行"表达式没写完"」。但
> `title_page_prl.tex` 的写法是 `\vspace{1em}` 换行 + `oindent\\textbf{Author}` ——
> **前一行不以 `$`/`(` 结尾 ⇒ 判据不成立 ⇒ 漏检 7 处**，而 **PDF 里已印出 `oindentAuthor`**。
>
> **⇒ 加强判据（`tools/_p564`）**：**断头 token 后紧跟 `\\`（命令）或大写字母 ⇒ 必为断头**
> —— 因为 LaTeX 里 `oindent\\textbf{...}` 这种写法**永远不合法**。
> **⇒ 又抓出 13 处**：`title_page_prl.tex` 7、**`main.tex` 的 `oindentKeywords:`**、
> `main_10pp.tex`、`main_body_full.tex`、`sections_full/conclusion.tex` 等。
>
> **⚠️ 其中 `main.tex` 的 `oindentKeywords:` 会印进投稿件** —— 这是加强判据的直接价值。
>
> ### 三、✅ 六份 PDF 全部核验干净（`tools/_p565`）
>
> | PDF | 页数 | 错误 | PDF 里的 `??` | **PDF 里的 `oindent`/`abla`** |
> |---|---|---|---|---|
> | **main（投稿件）** | **10** | 0 | 0 | **0** |
> | main_full（完整版） | 13 | 0 | 0 | 0 |
> | **supplementary（补充）** | **5** | 0 | 0 | 0 |
> | cover letter | 2 | 0 | 0 | 0 |
> | title page | 1 | 0 | 0 | 0 |
> | highlights | 1 | 0 | 0 | 0 |
>
> **⚠️ 并修掉补充材料的两类问题**（`tools/_p566`/`_p567`）：
> ① **我移出内容时把中文小节标题写进了 tex**（`\\subsection{解码器 VLM}` 等 5 处）⇒ 报 20 个 Unicode 错误；
> ② **`\\ref` 指向主文档 label** ⇒ PDF 印出 `Theorem ??`、`Lemma ??`、`Table ??`（3 处）⇒ 改为明确文字。
> **③ 图片路径**：补充材料在子目录，改 `figures/` → `../figures/`。
>
> ### 四、✅ Zenodo × GitHub：**两者可打通，不是二选一**（`ARCHIVE_WITH_ZENODO.md`）
>
> 操作者反馈"Zenodo 不方便，不如 GitHub"。**正解**：
>
> | 需求 | 由谁满足 |
> |---|---|
> | 代码持续更新、`git push` 即改、方便浏览 | **GitHub** |
> | **DOI（Option C 要的"可引用"）** | **Zenodo 自动发**（GitHub release 触发） |
>
> **一次性设置（约 3 分钟）**：Zenodo → Settings → GitHub → Connect → 仓库开关 ON；
> 之后 **GitHub 打 tag/release ⇒ Zenodo 立刻生成 DOI** `10.5281/zenodo.XXXXXXX`。
> **⚠️ Zenodo 抓的是 release 快照**：改动后要再发 release 才有新 DOI。
> **⚠️ 仓库需公开**，否则 DOI 落地页要求登录，不满足"读者可访问"。
>
> **备选**：Zenodo 手动上传 zip（本包已备 `archive/p3_release.zip`，
> **431 文件 / 2.8 MB**：`README.md` + `tools/` 198 个 P3 脚本 + `outputs/` 228 个结果 JSON + `docs/` 4 个报告；
> **稿件类 0**，遵循本仓库既有发布边界）。
>
> **拿到 DOI 后要改三处**：① 稿件的 Data statement ② cover letter 的 `[REPOSITORY DOI]`
> ③ EM 表单的 Data availability 字段。
>
> ### 五、状态
>
> - **六份 PDF 全部 0 错 / 0 未定义 / 0 断头残留**
> - **修订包**：含 `UPLOAD_CHECKLIST.md`、`ARCHIVE_WITH_ZENODO.md`、`archive/p3_release.zip`、三份 EM 纯文本回复
> - **剩余**：① 操作者做 Zenodo–GitHub 绑定并拿 DOI（然后改三处）② EM 填三个回复框 ③ 提交
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "三件文案原本都在" in t:
        print("  已记录")
        return 0
    if not a.apply:
        print("  （预演）")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("三件文案原本都在", "第 34 个错", "oindentKeywords", "ARCHIVE_WITH_ZENODO", "431 文件"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
