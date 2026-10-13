# -*- coding: utf-8 -*-
r"""落账：A1 投稿件按 Neural Networks 过一遍（2026-10-10）。

    python tools\_docs_nn_submission_files.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📄 2026-10-10 —— A1 投稿件按 `Neural Networks` 全部过一遍（6 份）**
>
> ### 一、五份投稿件的终态
>
> | 文件 | 页数 | 错误 | 改动 |
> |---|---|---|---|
> | `main.tex` | **41** | 0 | 参考文献转 APA（56 条）；`\\journal{Neural Networks}` |
> | `cover_letter.tex` | **2** | 0 | **整篇重写**（见下） |
> | `declaration.tex` | **1** | 0 | 标题/日期更新（旧标题 → 新标题；16 Sep → **10 Oct 2026**） |
> | `highlights.tex` | **1** | 0 | **未改**（已合规：5 条，最长 **68** 字符 ≤ 85） |
> | `abstract.tex` | **1** | 0 | 标题更新（旧标题含 `\\\\` 换行，需正则匹配） |
>
> ### 二、`cover_letter` 重写要点（**旧版有 3 处实质问题**）
>
> | # | 旧版 | 问题 | 新版 |
> |---|---|---|---|
> | 1 | `Neurocomputing`（4 处） | 刊名错 | **`Neural Networks`** |
> | 2 | 旧标题 | 标题已改 | **新标题** |
> | 3 | *"A companion empirical study … is currently **under review at Pattern Recognition** (PR-D-26-10149)"* | 🔴 **与事实不符**：`paper合`（P1+P2 合并稿）**尚未投出**（`文件地图.md`：状态"待投"，候选 CVIU/ESWA）；PR 在审的是 **P1**，不是这本 | 改为：姊妹稿 **"is not yet submitted to any journal"**；并**如实说明** P1 在 PR 在审（`PR-D-26-10149`） |
>
> **新版还加了**：
> - **"零开销"卖点**（新定位的核心）——$\tau$ 可由验证时已有的 top-$k$ 类集合算出，**无需额外成本**；
> - **适用边界**（检索用 gap、分类用 $\tau$）；
> - **`Prior consideration`** 段：**如实声明曾投他刊未被接受**，并说明本次改了什么（Elsevier 要求）；
> - **`top-$k$` 消融**已做（佐证结论不依赖 $k$ 的选取）。
>
> **披露三行**（按 `docs/PAPERA_VS_COMMENTARY.md` §二既有规定）：
> ① 与姊妹稿的关系与区别；② P1 在 PR 在审；③ 本文引用它们作 prior work。
>
> ### 三、我又犯并修正的 **1 个错**（留档）
>
> | 错 | 真因 | 修法 |
> |---|---|---|
> | 在 Crossref/OpenAlex 的 `mailto=` 里写了 `hrw1n24@soton.ac.uk` | **项目实际邮箱是 `contact@example.com`**（全项目 20 处；`hrw1n24` **0 处**） | 修 **10 个脚本 / 16 处**（**只影响礼貌池标识，不影响已取回的数据**） |
>
> ### 四、一致性终检（`tools/_p135_a1_consistency.py`）
>
> ```
> main / cover_letter / declaration / highlights / abstract / related_work   → 全部 ✅ 干净
> 旧标题 0 ｜ 旧刊名 0 ｜ 错误邮箱 0 ｜ 旧日期 0
> PDF 是否最新：5/5 ✅
> ```
>
> ### 五、备份
>
> `cover_letter.tex.bak_nc`｜`declaration.tex.bak_nc`｜`abstract.tex.bak_nc`｜`main.tex.bak_preapa`
>
> ### 六、还差什么
>
> | # | 项 | 状态 |
> |---|---|---|
> | 1 | **接受 ATS 转投、选 Neural Networks** | ⏳ **待操作者**（截止 `Nov 08 2026 23:59`） |
> | 2 | `imod`/`hu2022lora` 两条文献作者（现 `Anon.`） | ⏳ 待操作者提供 PDF 或授权 |
> | 3 | `paper合` 的投稿（ESWA/KBS/CVIU） | ⏳ 待操作者定 |
> | 4 | COCO `text_only` 补跑（4 个剩余） | ▶ 后台进行中（已完成 7/11） |
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "A1 投稿件按 `Neural Networks` 全部过一遍" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("A1 投稿件按 `Neural Networks` 全部过一遍", "is not yet submitted to any journal",
              "Prior consideration", "contact@example.com", "Nov 08 2026", "68", "10 个脚本 / 16 处"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
