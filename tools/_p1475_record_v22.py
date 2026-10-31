# -*- coding: utf-8 -*-
r"""Record the v2.2 release in the hand-off documents."""
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HANDOFF = os.path.join(REPO, "HANDOFF.md")
MAP = os.path.join(REPO, "文件地图.md")

ENTRY = """> **📦 2026-10-21 10:25 —— GitHub v2.2 release 已创建**
>
> | 字段 | 值 |
> |---|---|
> | Release | **v2.2**（Latest）|
> | URL | https://github.com/MoYUYao666/gap-susceptibility/releases/tag/v2.2 |
> | Tag | `v2.2`（annotated `0630332` → mirror 提交 `92b34ef`）|
> | 内容 | 审计修复后的分析脚本/结果归档/打包工具/provenance manifest/终检报告；**tag 树 2,487 文件，`paper*`/`SUBMISSION*` 路径 0、`.tex` 0** |
> | 正文 | 通用内容清单（"Included / Excluded / Verification"），无论文题名、状态或结果 |
> | 镜像 | `publish_clean` main `a3043c5..92b34ef` 已推；v2.1 tag 保持冻结于 `c01cd0b` |
> | Zenodo | **版本 DOI 待核**（本机 zenodo.org DNS 不可用）；概念 DOI 不变 |
>
> 至此 v2.1 之后的所有修复（P3 补材、A1 包封面信、A23 评测集、provenance 附录等）均已进入 v2.2 快照。
>

"""

ROW = ("130. 📦 **GitHub v2.2 release（2026-10-21 10:25）** —— tag `v2.2`（`0630332` → mirror `92b34ef`）；"
       "内容=审计修复后的脚本/归档/打包工具/provenance/终检报告；正文为通用清单；tag 树 2,487 文件、稿件路径 0、.tex 0；"
       "mirror `a3043c5..92b34ef` 已推；v2.1 冻结不动；Zenodo 版本 DOI 待核。\n")


def main() -> int:
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "GitHub v2.2 release 已创建" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENTRY + h[j + 1:])
        print("  handoff updated")
    m = io.open(MAP, encoding="utf-8").read()
    if "GitHub v2.2 release（2026-10-21 10:25）" not in m:
        anchor = "129. 🔎 **独立审计 + 问题修复"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + ROW + m[end + 1:])
        print("  file map updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
