# -*- coding: utf-8 -*-
r"""落账：A1 转投 Neural Networks 的合规改造完成（2026-10-10）。

    python tools\_docs_nn_compliance.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📮 2026-10-10 —— A1 转投 **Neural Networks**：合规改造完成（操作者决定"转"）**
>
> ### 一、转投目标确定：**Neural Networks**（ISSN 0893-6080）
>
> **依据**（`期刊指南/_guide_neuralnetworks.txt`，由操作者提供的 Guide PDF 提取，60,481 字符）：
>
> | 项 | Guide 原文要求 | A1 现状 |
> |---|---|---|
> | 摘要 | **does not exceed 250 words** | ✅ **245 词** |
> | 关键词 | **1 to 6 keywords** | ✅ **5 个** |
> | Highlights | **3 to 5**，每条 ≤85 字符 | ✅ **5 条，最长 68** |
> | 参考文献 | **APA（American Psychological Association）第 7 版** | ✅ **已转换（见下）** |
> | 文件 | `.tex` 可编辑源文件 | ✅ elsarticle |
> | 免 APC | hybrid，在 **Southampton 确定覆盖**名单内 | ✅ |
> | 转投通道 | Guide 明载 **Article Transfer Service** | ✅ 与我们路径一致 |
>
> **为何不选清单里其它 9 个刊**：`Pattern Recognition`（PR 三次拒过 P1，且 P1 正投 PR 审稿中）、
> `Displays`/`Big Data Research`/`Journal of the Franklin Institute`（scope 不合）、
> `Biomedical Signal Processing and Control`（**A1 无生物医学内容**）、
> `Natural Language Processing Journal`（**A1 是视觉**）、
> `Intelligent Systems with Applications`/`Array`/`Systems and Soft Computing`（**fully OA，不免 APC**）。
>
> ### 二、参考文献改为 APA 第 7 版（**56 条**）
>
> **为何必须改**：Neural Networks Guide 明写 APA；A1 原为 `elsarticle` 数字制（`\cite` → `[1]`）。
>
> **做法（可复核）**：
> 1. **作者名单用 OpenAlex 补全**（**Crossref 对 ML 会议论文覆盖差**，实测 `radford2021` 在
>    Crossref 标题检索返回鱼类分类等无关论文；OpenAlex 精确命中）→ `tools/_p110` / `_p112` / `_p114` / `_p115` / `_p116`
> 2. **姓以 bibitem 为准**（原文已写对），OpenAlex 只补名 → 修 `Lingjie Yi`（姓被解析成 "Lingjie"）
> 3. **按字母序**重排 → `tools/_p130`
> 4. 正文 `\\cite` → `\\citep`（10 处）｜文档类 `\\documentclass[review,authoryear]{elsarticle}`
>
> | 结果 | 条数 |
> |---|---|
> | ✅ OpenAlex 解析成功 | **52** |
> | ✅ 手工（作者即本人 / 已核） | **2** |
> | ⚠️ **UNAVAILABLE（无据可查，不猜）** | **2**（`imod` CVPR 2026 未索引；`hu2022lora` OpenAlex 无规范条目） |
>
> **那 2 条标 `Anon.` 并置顶**，**未编造作者**（符合项目唯一原则）。
> **落盘证据**：`outputs/analysis/a1_refs_openalex.json`（含每条的 `method`/`similarity`/`openalex_id`/作者）。
>
> ### 三、过程中我犯并修正的 **5 个错**（逐条留档）
>
> | # | 我的错 | 真因 | 修法 |
> |---|---|---|---|
> | 1 | 断言 `yi2025` 作者解析错 | 其实 `family='Yi'` 本正确，**是我的匹配表达式写错**（没处理 `display` 的 "姓, 名" 格式） | 修匹配 + 去重音（`Yüksekgönül`） |
> | 2 | `hu2022lora` 填了**另一篇论文**的作者 | 我按错误 DOI `10.48550/arXiv.2106.09685` 直查，返回 **"LoRA Fine-Tuning of a 3B Code LLM"**（不同论文，只是作者里也有 Hu） | **撤回，改标 UNAVAILABLE** |
> | 3 | 书目姓提取**全空** | bibitem 用 **`~`（LaTeX 不换行空格）**，而我的正则用 `\s*` **匹配不到 `~`** | 先归一化 `~` |
> | 4 | **`Option clash for package natbib`** | **`elsarticle` 已自行加载 natbib（数字制）**，我又 `\\usepackage[authoryear]{natbib}` | 改为文档类选项 `[review,authoryear]`，删掉我的 `\\usepackage` |
> | 5 | **`\\bibitem[[?], 2026]`** 导致该条被吞 | **嵌套方括号**：`[?]` 里的 `]` 提前闭合了可选参数 | 标签改 `Anon., 2026` |
>
> 另有：52 处 `&` 未转义（`\\&`）、Unicode `ȩ` 无 LaTeX 映射（加 `inputenc` + 去音）。
>
> ### 四、编译
>
> | 稿 | 页数 | 错误 | 未定义引用 | Overfull |
> |---|---|---|---|---|
> | **A1**（`paper_a1/main.tex`） | **41** | **0** | **0** | **0** |
>
> **页数 40→41**：56 条参考文献由数字制改为作者-年制后变长。
> **书目完整性**：**56 条 / 56 key / 0 缺失 / 0 未定义**（`tools/_p131_bib_integrity.py`）。
> **备份**：`paper_a1/main.tex.bak_preapa`（改前状态）。
>
> ### 五、还差什么
>
> | # | 项 | 状态 |
> |---|---|---|
> | 1 | **接受 ATS 转投、选 Neural Networks** | ⏳ **待操作者**（截止 **Nov 08 2026 23:59**） |
> | 2 | **A1 的 `highlights.tex` / `cover_letter.tex` 是否要按 NN 要求更新** | ⏳ 待做 |
> | 3 | **`imod` / `hu2022lora` 的作者**（现为 `Anon.`） | ⏳ 待操作者提供 PDF 或授权按常识补 |
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "转投 **Neural Networks**：合规改造完成" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("转投 **Neural Networks**：合规改造完成", "APA 第 7 版", "Option clash for package natbib",
              "Anon., 2026", "**41**", "56 key", "hu2022lora", "Nov 08 2026"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
