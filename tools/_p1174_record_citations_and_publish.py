# -*- coding: utf-8 -*-
r"""Record the citation additions, the widened data statement and the published decoder records.

    python tools/_p1174_record_citations_and_publish.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "补模型引用并把解码器记录发布"

ENT = """> **📚 2026-10-17 21:40 —— 补 4 条模型引用 + 数据声明扩到 E/G + **已发布到公开仓库**（`4499ef7`）**
>
> ### 一、文献引用（全部**逐条核实**后才写入）
>
> | 模型 | 核实方式 | bib key |
> |---|---|---|
> | SigLIP | Crossref：Zhai, Mustafa, Kolesnikov, Beyer，ICCV 2023，**DOI 10.1109/ICCV51070.2023.01100** | `zhai2023siglip` |
> | BioCLIP | Crossref：Stevens et al.，CVPR 2024，**DOI 10.1109/CVPR52733.2024.01836** | `stevens2024bioclip` |
> | DINOv2 | arXiv 元数据：**arXiv:2304.07193**，Oquab et al. | `oquab2023dinov2` |
> | OpenCLIP | GitHub API：`mlfoundations/open_clip` **HTTP 200 / public / 14.2k stars**（Zenodo 直连被本机网络拦，未编造 DOI） | `ilharco2021openclip` |
>
> 引用插在**各自首次实质出现处**（introduction 的 SigLIP、empirical 的 OpenCLIP/BioCLIP 与 DINOv2），**不逐处堆引**。
>
> ⚠️ 过程中我自己引入过一个 bug：`empirical.tex` 有两处修改，我先各自基于原文生成再顺序写盘 ⇒ **第二处覆盖第一处**，导致 OpenCLIP/BioCLIP 引用丢失（构建报"未被引用"）。已发现并补回，最终 **bib 52 条 / 被引 52 / 0 未定义 / 0 未使用**。
>
> ### 二、数据可用性声明（两版稿件同步）
>
> 由
> `their per-run records are available from the author, and the adapters are not redistributed because of their size.`
> 改为
> `their per-run records are openly available in the same repository, and the adapters are not redistributed because the reported statistics are archived as per-run records and the adapters are not required to reproduce them.`
>
> 理由：E/G 记录现已实际发布（见下）；适配器"因体积不分发"的说法偏弱（1.58 GB 并不大），改为**"复现统计量不需要适配器"**更站得住。
>
> ### 三、✅ 解码器记录已发布到公开仓库（**不需要新 DOI**）
>
> | 项 | 值 |
> |---|---|
> | 内容 | **69 个 JSON / 79.1 KB**：`outputs/vlm_clean_cloud/`（53）、`llava_canonical_cloud/`（12 条记录）、两个 summary、frozen 基线 |
> | 校验 | 逐文件 **SHA-256 与源一致，0 不符**；暂存 **72 文件 / 3927 行**；**无 >20 MB 文件** |
> | 推送 | `43b733c..4499ef7  main -> main`，rc=0 |
> | 公开可见 | GitHub API 抽查三个新文件均 **HTTP 200** |
> | **DOI 状态** | **未变**：查询时点快照仍为 `10.5281/zenodo.23341223`；按冻结纪律**未动 tag、未铸新 DOI** |
>
> ### 四、重建与门禁
>
> | 项 | 结果 |
> |---|---|
> | `main_nc.pdf` | **69 页**（+1，因新增引用与声明）；**0 错误 / 0 未定义 / 0 Overfull** |
> | `main_springer.pdf` | **49 页**；同上 0/0/0 |
> | `NC_submission/` | 已刷新：`Manuscript.pdf` **69 页**、源码包 **45 文件**、独立编译通过 |
> | 台账 | Paper A **74/74**、主台账 **96/96** |
>
> ### 五、仍未决定/未做（保持原状）
>
> 1. **Paper A 投稿时点**：建议 **2026-11-09 之后**（避开 P3 R1 11-02 与 A1 转投确认 11-08；A1 亦投 Neurocomputing，同刊并行需错开）；
> 2. **162 个 ODE 拟合逐条归档缺口**：建议**显式声明**而非重跑（逐 run 轨迹也未归档，重跑等于重做整链）；
> 3. 若要让 E/G 成为**可引用数据集**，需新 tag → 新版本 DOI，属一次性对外后果，**须操作者明确批准**后再做。
>
> **脚本**：`_p1172`（引用+声明）｜`_p1173`（发布+校验+推送）｜`_p1174`（本条）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        print("  handoff entry added")
    mp = io.open(MAP, encoding="utf-8").read()
    row = ("60. 📚 **补 4 条模型引用 + 数据声明扩到 E/G + 解码器记录已发布（2026-10-17 21:40）** —— "
           "SigLIP(DOI 10.1109/ICCV51070.2023.01100)/BioCLIP(DOI 10.1109/CVPR52733.2024.01836)/DINOv2(arXiv:2304.07193)/"
           "OpenCLIP(公开仓库，未见可核实 DOI 故不编造)，逐条核实后插入首次出现处 ⇒ **bib 52/52**。"
           "数据声明改为\"解码器记录在同仓库公开、适配器因复现统计不需要而不分发\"。**69 个 JSON 已推送公开仓库**"
           "（`43b733c..4499ef7`，SHA-256 逐个一致、无大文件、API 抽查 HTTP 200）；**DOI 未变、未动 tag**。"
           "NC **69 页** / Springer **49 页**（0/0/0），投稿包已刷新并独立编译通过，台账 74/74 与 96/96。"
           "详见 `HANDOFF.md` 21:40 条目。\n")
    if "补 4 条模型引用 + 数据声明扩到 E/G" not in mp:
        anchor = "56. 🤖 **自动化任务交接"
        idx = mp.find(anchor)
        if idx >= 0:
            end = mp.find("\n", idx)
            mp = mp[: end + 1] + row + mp[end + 1:]
            io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
            print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
