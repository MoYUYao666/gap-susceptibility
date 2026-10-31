# -*- coding: utf-8 -*-
r"""Record the DOI switch and the no-retag discipline in the handoff document.

    python tools/_p631_record_doi_switch.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OLD = "10.5281/zenodo.23341083"
NEW = "10.5281/zenodo.23341223"

ENT = f"""> **🔴 2026-10-14 11:00 —— 操作者指出"每更新一次 DOI 就变"，根因是**我的操作**；已改正 + 立纪律**
>
> ### 一、操作者反馈
>
> > **（附 GitHub Releases 页截图）"你每次更新完会变DOI"**
>
> **⇒ 完全属实，是我的操作失误。**
>
> ### 二、🔴 根因
>
> | 我的动作 | Zenodo 的反应 |
> |---|---|
> | 第 1 次推 tag + 建 Release（`7755f70`） | 铸 **`{OLD}`** |
> | 之后**反复「删 tag → 重打 → 删 Release → 重建」**（`fd7a28a`→`78256b4`→`c4a6c22`→`7755f70`→`8352d8d`→`cc9bdac`→`5e1da98`→`e320e75`） | **Zenodo 把每一次都当成新版本** ⇒ 又铸 **`{NEW}`** |
>
> **⇒ 根因：Zenodo 的 GitHub 集成对「新 Release / tag 变动」都视为版本事件。
> 我在建好归档之后又把 tag 当草稿反复改，才导致 DOI 增殖。**
>
> **⇒ 权威依据**（Zenodo 官方）：**引用具体版本的 DOI**；**概念 DOI 用于"始终指向最新版"**
> —— [Zenodo: Compilation of Data Versioning Use Cases](https://zenodo.org/records/3772884/files/Compilation%20of%20Data%20Versioning%20Use%20Cases%20V1.3%20Zenodo%20Complete.pdf?download=1#11#7)
>
> ### 三、✅ 已立铁律（写入 `AGENTS.md` 166 行 / `CLAUDE.md` 98 行）
>
> 1. **一旦 Zenodo 抓取某个 tag，该 tag 冻结**：不得 `git tag -d` + 重打、不得 `git push :refs/tags/<tag>`、不得删建 GitHub Release
> 2. **出新版本用新 tag**（`v1.1`、`v1.2`…）⇒ 在**同一概念 DOI** 下新增版本 DOI
> 3. **引用具体版本 DOI**；概念 DOI 用于"始终指向最新版"
> 4. **改 README / 元数据不值得新铸 DOI** ⇒ 在 Zenodo 记录页直接改
> 5. **动 tag 之前先问操作者**（会产生对外可见的新 DOI）
>
> ### 四、✅ 操作者裁定：引用 `{NEW}`
>
> > 选项里选 **"10.5281/zenodo.23341223（推荐）"**
>
> **理由**：它是 **GitHub 仓库页头部徽章显示的那个**，且是**仓库改为公开之后**铸出的 ⇒ 快照内容最新（README 带 DOI 徽章）。
>
> ### 五、✅ 全库替换（`tools/_p630`）：**22 处 / 9 个文件**，残留旧 DOI **0**
>
> | 文件 | 处数 |
> |---|---|
> | `paper3/paper_ieee/main.tex`（Data statement） | 2 |
> | `paper3/paper_ieee/cover_letter_prl.tex` | 2 |
> | `SUBMISSION/P3_PRL_revision/manuscript/latex_source/main.tex` | 2 |
> | `publish_clean/README.md`（含徽章 URL） | 4 |
> | `README.md`（仓库根） | 4 |
> | 修订包 `README.md` / `ARCHIVE_WITH_ZENODO.md` / `UPLOAD_CHECKLIST.md` | 各 2 |
> | `PRL_submission/EM_author_classifications.txt` | 2 |
>
> ### 六、✅ 重编译与核验
>
> | 文件 | 页数 | 错误 | 未定义 | 新 DOI 在 | 旧 DOI 残留 |
> |---|---|---|---|---|---|
> | `main.pdf` | **10** | **0** | **0** | ✅ | **无** ✅ |
> | `cover_letter_prl.pdf` | 2 | **0** | **0** | ✅ | **无** ✅ |
>
> **源包**：12 成员 / **128,816 字节**；**解压到干净目录独立编译 3 遍 ⇒ 0 错误 / 10 页** ✅
>
> ### 七、🔧 顺带修一个我埋的坑
>
> `tools/_p623`（同步包）**自己会先打一个只有 4 个文件的残包**（6,775 字节），随后被 `_p624` 覆盖成正确的 ——
> **单独跑 `_p623` 就会把源包做坏**。**已删掉该段**，改为提示用 `_p624`；
> **复跑验证：源包 128,816 → 128,816 字节，不再被破坏** ✅
>
> ### 八、✅ 本次严格遵守冻结纪律
>
> | 项 | 值 |
> |---|---|
> | 提交 | **`2b48e40`**（`8b03800..2b48e40`） |
> | **tag 是否被动** | **否** ✅（仍为 `e320e75`，指向 `8b03800`） |
> | **Release 是否被动** | **否** ✅（未删未建） |
> | ⇒ 未产生新 DOI | ✅ |
>
> **⇒ 这次推送到 `main` 不影响 Zenodo 快照**（快照是 tag 的，tag 未动）。
>
> ### 九、⚠️ 一个已知小瑕疵（可接受，不再动 tag 去"修"）
>
> `main` 上 README 的 DOI 已改为 `{NEW}`，但 **tag 快照 `8b03800` 里 README 写的是 `{OLD}`**
> —— 即**归档快照内部引用了另一个 DOI**。
> **两者都解析到同一仓库的已发布记录，不构成错误引用**；**不值得为改一行 README 再铸第三个 DOI**（那正是本次教训）。
> **⇒ 若日后确要新版本，用新 tag（如 `v1.1`）；在 `v1.1` 里这段就自洽了。**
>
> ### 十、剩余
>
> ① **重传 EM**：`manuscript/main.pdf`（414,993）＋ `cover_letter.pdf`（131,744）＋ `P3_latex_source_revision.zip`（128,816）
> ② **EM 三个回复框**：粘贴 `response/P3_RESPONSE_Reviewer{{1,2,3}}_plain.txt`
> ③ **EM 表单**：Data availability 勾"数据在公开仓库中可用" + 填 `{NEW}`
> ④ `p3d_summary.json` 指纹更新（非阻塞）⑤ 提交
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "每更新一次 DOI 就变" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("每更新一次 DOI 就变", NEW, "2b48e40", "tag 冻结", "残包"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
