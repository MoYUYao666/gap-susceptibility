# -*- coding: utf-8 -*-
"""Record the P3 resubmission number and the audit outcome in the hand-off documents."""
import io

HANDOFF = "HANDOFF.md"
MAP = "文件地图.md"
SUB = "SUBMISSION/README.md"
PLAN = "docs/P3_RESUBMISSION_PLAN_2026-10-21.md"
OBJ = "docs/P3_REVIEWER_OBJECTIONS.md"

ENTRY = """> **✅ 2026-10-21 18:40 —— P3 改投正式提交：新稿号 `PRLETTERS-D-26-02671`**
>
> EM 状态：**Submitted to Journal**（2026-10-21）；标题为改投版新标题；数据 DOI `10.5281/zenodo.23523263`。
>
> | 项 | 值 |
> |---|---|
> | 新稿号 | **`PRLETTERS-D-26-02671`** |
> | 前稿号 | `PRLETTERS-D-26-02378R1`（2026-10-21 拒稿）|
> | 期刊 | Pattern Recognition Letters |
> | 状态 | Submitted to Journal |
> | 包 | `SUBMISSION/P3_PRL_resubmission/`（10 + 8 页 + CoverLetter/TitlePage/Highlights/Authorship/LaTeXSource）|
>
> **改投审核（`docs/P3_RESUBMISSION_AUDIT_2026-10-21.md`，脚本 `tools/_p1494_p3_submission_audit.py`）**：
> R1 的 8 条预判意见 + AE 拒稿信指出的"technical choice / interpretation"两类问题，**均已处理并可在本地验证**
> （S14 五 seed p=0.008、S16 协议窗口、S17 claim-status 表、真实图像数字、DOI 一致、无下划线文件名、作者声明）。
> **仍不能确认**：审稿意见原文未取得（无法逐条对齐真实意见）；R3′ 可加性未实测、n=64 窗口未完成、AdaLoRA 未重跑——
> 这三项属于下一轮加固，不影响当前已投版本。
>

"""

AUDIT_PLAN = """
## 2026-10-21 18:40：已提交

- 新稿号 **`PRLETTERS-D-26-02671`**，状态 **Submitted to Journal**。
- 改投审核报告：`docs/P3_RESUBMISSION_AUDIT_2026-10-21.md`（R1 8 条 + AE 两类问题逐条映射）。
"""


def main() -> int:
    # HANDOFF
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "P3 改投正式提交：新稿号" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENTRY + h[j + 1:])
        print("  handoff updated")
    # file map
    m = io.open(MAP, encoding="utf-8").read()
    block = """> **✅ 2026-10-21 18:40 状态更新：P3 改投已提交**
>
> | 稿件 | 新状态 | 稿号 |
> |---|---|---|
> | **P3（改投）** | **Submitted to Journal（2026-10-21）** | **`PRLETTERS-D-26-02671`** |
>
> 前稿 `PRLETTERS-D-26-02378R1` 已拒；审核报告 `docs/P3_RESUBMISSION_AUDIT_2026-10-21.md`。
>

"""
    if "P3 改投已提交" not in m:
        i = m.find("# 文件地图")
        j = m.find("\n", i)
        m = m[: j + 1] + "\n" + block + m[j + 1:]
    row = ("139. ✅ **P3 改投提交（2026-10-21 18:40）** —— 新稿号 `PRLETTERS-D-26-02671`，Submitted to Journal；"
           "包 10+8 页；数据 DOI v2.2；审核报告 `docs/P3_RESUBMISSION_AUDIT_2026-10-21.md`。\n")
    anchor = "138. 🔗 **v2.2 Zenodo DOI"
    if "P3 改投提交（2026-10-21 18:40）" not in m:
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        m = m[: end + 1] + row + m[end + 1:]
    io.open(MAP, "w", encoding="utf-8", newline="").write(m)
    print("  file map updated")
    # SUBMISSION README
    r = io.open(SUB, encoding="utf-8").read()
    old = ("| `P3_PRL_resubmission/` | **P3（改投稿）** | Pattern Recognition Letters（新投稿）| 待提交 | "
           "📝 **已备好、未提交**（2026-10-21）| 10 页主稿 + 8 页补充 + CoverLetter/TitlePage/Highlights/LaTeXSource"
           "（文件名均无下划线）|")
    new = ("| `P3_PRL_resubmission/` | **P3（改投稿）** | Pattern Recognition Letters（新投稿）| **`PRLETTERS-D-26-02671`** | "
           "✅ **已投 2026-10-21（Submitted to Journal）** | 10 页主稿 + 8 页补充 + CoverLetter/TitlePage/Highlights/"
           "Authorship/LaTeXSource（文件名均无下划线）|")
    if old in r:
        r = r.replace(old, new, 1)
        io.open(SUB, "w", encoding="utf-8", newline="").write(r)
        print("  SUBMISSION/README updated")
    # plan + objections docs
    for p, marker in ((PLAN, "## 2026-10-21 18:40：已提交"), (OBJ, "## 2026-10-21 18:40：已提交改投")):
        t = io.open(p, encoding="utf-8").read()
        if marker not in t:
            io.open(p, "w", encoding="utf-8", newline="").write(t.rstrip() + "\n" + AUDIT_PLAN)
            print("  updated", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
