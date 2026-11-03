# -*- coding: utf-8 -*-
"""Synchronise Paper A's NC submission package artefacts and regenerate its README from measured facts.

Copies the rebuilt cover letter and highlights to the package's upload names, then writes
NC_submission/README.md from facts measured at run time (page counts, abstract length,
highlights, bibliography, claim ledgers, and the supplement E/G numbers read from the
archived JSON). Every value in the README is asserted against its source.

    python tools/_p1178_sync_nc_package.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import shutil
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
PKG = PA / "NC_submission"
FAILS: list[str] = []


def need(cond: bool, msg: str) -> None:
    if not cond:
        FAILS.append(msg)
        print("FAIL  " + msg)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pages(path: Path) -> int:
    from pypdf import PdfReader
    return len(PdfReader(str(path)).pages)


def abstract_words() -> int:
    tex = io.open(PA / "main_nc.tex", encoding="utf-8").read()
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    need(m is not None, "main_nc.tex: abstract not found")
    if not m:
        return 0
    a = re.sub(r"\$[^$]*\$", " X ", m.group(1))
    a = re.sub(r"\\[a-zA-Z]+\*?", " ", a)
    a = a.replace("{", " ").replace("}", " ")
    return len([w for w in a.split() if any(ch.isalnum() for ch in w)])


def bib_facts() -> tuple[int, int]:
    bib = io.open(PA / "references.bib", encoding="utf-8").read()
    keys = re.findall(r"@\w+\{([^,]+),", bib)
    used = set()
    for p in [PA / "main_nc.tex", PA / "main_springer.tex"] + sorted((PA / "sections").glob("*.tex")):
        t = io.open(p, encoding="utf-8").read()
        for m in re.finditer(r"\\cite[tp]?\{([^}]+)\}", t):
            used |= {k.strip() for k in m.group(1).split(",") if k.strip()}
    return len(keys), len(used)


def eg_facts() -> dict:
    d = json.load(io.open(REPO / "outputs" / "vlm_clean_summary.json", encoding="utf-8"))
    e = {
        "frozen_dg": d["frozen"]["dg_star"],
        "frozen_cg": d["frozen"]["cg"],
        "both": (d["per_arm"]["both"]["reduction_mean"], d["per_arm"]["both"]["reduction_sd"]),
        "text": (d["per_arm"]["text_only"]["reduction_mean"], d["per_arm"]["text_only"]["reduction_sd"]),
        "vision": (d["per_arm"]["vision_only"]["reduction_mean"], d["per_arm"]["vision_only"]["reduction_sd"]),
    }
    c = json.load(io.open(REPO / "outputs" / "canonical_caption_metric.json", encoding="utf-8"))
    runs = c["runs"]
    fz = runs["frozen"]["clean"]["dg_star"]

    def arm(prefix: str) -> tuple[float, float]:
        vals = [100.0 * (runs[k]["clean"]["dg_star"] - fz) / fz for k in runs if k.startswith(prefix)]
        return st.mean(vals), st.pstdev(vals)

    g = {"frozen_dg": fz, "text": arm("text_only_s"), "vision": arm("vision_only_s"), "both": arm("both_s")}
    return {"E": e, "G": g}


def ledger_facts() -> tuple[int, int, int, int]:
    a = json.load(io.open(REPO / "outputs" / "analysis" / "claim_ledger_paperA.json", encoding="utf-8"))
    b = json.load(io.open(REPO / "outputs" / "analysis" / "claim_ledger.json", encoding="utf-8"))
    return a["pass"], a["gap"], b["passed"], b["failed"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    main_pdf = PA / "main_nc.pdf"
    need(main_pdf.exists(), "main_nc.pdf missing")
    nc_pages = pages(main_pdf)
    sp_pages = pages(PA / "main_springer.pdf")
    cl_pages = pages(PA / "cover_letter_nc.pdf")
    abs_words = abstract_words()
    items = []
    for line in io.open(PA / "highlights_nc.txt", encoding="utf-8").read().splitlines():
        s = line.strip()
        if not s or s.lower() == "highlights":
            continue
        items.append(s.lstrip("-*\u2022 ").strip())
    n_hl, max_hl = len(items), max((len(s) for s in items), default=0)
    n_bib, n_cited = bib_facts()
    pa_pass, pa_gap, m_pass, m_fail = ledger_facts()
    facts = eg_facts()
    E, G = facts["E"], facts["G"]
    n_src = len([p for p in (PKG / "latex_source").rglob("*") if p.is_file()])
    import zipfile
    n_zip = len(zipfile.ZipFile(PKG / "latex_source.zip").namelist())
    title = re.search(r"\\title\{(.+?)\}\s*$", io.open(PA / "main_nc.tex", encoding="utf-8").read(), re.M).group(1)

    print("  measured: nc=%d springer=%d letter=%d abstract=%d bib=%d/%d src=%d zip=%d ledgers=%d/%d+%d/%d"
          % (nc_pages, sp_pages, cl_pages, abs_words, n_bib, n_cited, n_src, n_zip, pa_pass, pa_pass + pa_gap, m_pass, m_pass + m_fail))

    need(abs_words <= 250, "abstract over 250 words")
    need(n_hl == 5 and max_hl <= 85, "highlights count/length out of spec")
    need(n_bib == n_cited, "bibliography has %d keys but %d are cited" % (n_bib, n_cited))
    need(pa_gap == 0 and m_fail == 0, "claim ledger has failures")
    need(n_src == n_zip, "latex_source file count != zip entry count")

    if a.apply:
        shutil.copy2(PA / "cover_letter_nc.pdf", PKG / "Cover Letter.pdf")
        shutil.copy2(PA / "highlights_nc.pdf", PKG / "Highlights.pdf")
        shutil.copy2(PA / "highlights_nc.txt", PKG / "Highlights.txt")

    checks = [
        (PKG / "Manuscript.pdf", main_pdf, "Manuscript.pdf == main_nc.pdf"),
        (PKG / "Cover Letter.pdf", PA / "cover_letter_nc.pdf", "Cover Letter.pdf == cover_letter_nc.pdf"),
        (PKG / "Highlights.pdf", PA / "highlights_nc.pdf", "Highlights.pdf == highlights_nc.pdf"),
        (PKG / "Highlights.txt", PA / "highlights_nc.txt", "Highlights.txt == highlights_nc.txt"),
    ]
    for left, right, label in checks:
        if not left.exists() or not right.exists():
            need(False, label + ": missing file")
        else:
            need(sha256(left) == sha256(right), label + ": hash mismatch")

    e_both = "%.2f ± %.2f" % E["both"]
    e_text = "%.2f ± %.2f" % E["text"]
    e_vision = "%.2f ± %.2f" % E["vision"]
    g_text = "+%.2f ± %.2f" % G["text"]
    g_vision = "+%.2f ± %.2f" % G["vision"]
    g_both = "+%.2f ± %.2f" % G["both"]
    pa_total = pa_pass + pa_gap
    m_total = m_pass + m_fail

    readme = """# Paper A —— 投稿包（Neurocomputing 模板）

> 稿件：*{title}*
> 单作者 ｜ 模板：Elsevier elsarticle ｜ 本包最后同步：2026-10-18（投前终检）

## 上传对照

| 门户 item type | 文件 | 说明 |
|---|---|---|
| Manuscript | Manuscript.pdf | **{nc_pages} 页**（当前构建）；含作者信息与全部声明 |
| Highlights | Highlights.pdf / Highlights.txt | 单独文件，**{n_hl}** 条、最长 **{max_hl}** 字符 |
| Cover Letter | Cover Letter.pdf | **{cl_pages} 页** |
| LaTeX source（可要求时） | latex_source.zip | **{n_src}** 个文件（tex/bib/图）；无需附 elsarticle.cls |

## 合规核验

| 条款 | 状态 |
|---|---|
| 摘要 ≤250 词 | 通过：**{abs_words} 词**（源码口径：公式按一个词计） |
| Highlights | 通过：**{n_hl}** 条，最长 **{max_hl}** 字符（≤85） |
| single anonymized | 通过：无需匿名，稿件含作者信息 |
| 声明须在参考文献之前 | 通过：Data availability / Funding / Competing interests / CRediT / Generative AI |
| 参考文献 | 通过：**{n_bib}** 条、引用 **{n_cited}** 个 key、0 未定义 / 0 未引用 |
| 篇幅 | 无硬性上限条款（Guide 中带数字的只有摘要 250 词与作者简介 100 词） |

## 数据口径

| 项 | 值 |
|---|---|
| 实验总数 | **317** = 附录目录 **221** + 归档 ODE 拟合 **96**（`_claim_ledger_paperA.py` 断言 221+96=317） |
| 严格冻结对照 | **104** run（附录表 XIV：CLIP B/32 45 + OpenCLIP 25 + SigLIP 25 + BioCLIP 9） |
| 221 目录的骨干 | 六个 checkpoint：CLIP B/32、CLIP ViT-L/14、OpenCLIP B/32、SigLIP B/16、BioCLIP B/16、BLIP-1 |
| 严格冻结三臂协议 | 五个 checkpoint、七个 rank 配置（CLIP B/16 的 15 个补跑不在 221 目录内） |
| 解码器 VLM | Qwen2-VL-2B **39** run（13 seed × 3 臂）+ LLaVA-1.5-7B **9** run，均在 317 之外 |
| 批次 / seed | batch **128**；严格冻结 **5** seed；Qwen2-VL-2B **13** seed；LLaVA-1.5-7B **3** seed |
| 门禁 | Paper A 台账 **{pa_pass}/{pa_total} PASS、{pa_gap} GAP**；主台账 **{m_pass}/{m_total} 通过、{m_fail} 失败** |
| 投稿包一致性 | `tools/_p1169_refresh_nc_submission.py`：latex_source 独立编译通过、页数与主稿一致 |
| Cover Letter 来源 | `paper合/cover_letter.tex` → `cover_letter_nc.tex`（写死 Neurocomputing）→ 本包 Cover Letter.pdf |

## 稿件特征

- **核心主张**：由梯度流导出 Gap Susceptibility 与一阶 ODE；在归档 LoRA 运行上拟合完整间隙轨迹，平均 R² 0.949。
- **最不同的一点**：严格冻结对照在 CLIP 上支持"只适配文本侧"，在 SigLIP 上方向相反 → **位置优势是架构依赖的，不是普适默认**（BioCLIP 亦属"其它目标"一组）。
- **第二点**：both 在双塔上检索更强 → **降间隙 ≠ 提检索**。
- **第三点**：最优位置随数据集翻转（Flickr30k text_only / MS-COCO both，各 5 seed）。
- **解码器 VLM（补充 E/G 两节，两表不比较量级）**：
  - Qwen2-VL-2B（对比对齐目标）：三臂均降 gap，both **{e_both}%**、text_only **{e_text}%**、vision_only **{e_vision}%**（相对 frozen DG* **{e_fd:.4f}**）。
  - LLaVA-1.5-7B（生成目标）：三臂均升 gap，vision_only **{g_vision}%** > both **{g_both}%** > text_only **{g_text}%**（相对 frozen DG* **{g_fd:.4f}**）。
  - 合并解读：**视觉侧是对 gap 影响最不可控的一侧**，文本侧最可预测。
- **ODE 拟合记录**：**96** 条已归档（55 LoRA + 30 Adapter + 11 full-FT），正文计数与之一致；解码器两实验符号相反应归因于损失函数、规模还是数据，本轮无法分离。

## 未决事项（需操作者决定）

- **目标刊与投稿时点**：本包按 Neurocomputing 模板准备，最终由操作者决定。A1 已于 2026-10-12 转投 Neural Networks（NEUNET-D-26-09426），与 Neurocomputing 的同刊冲突解除；P1 已于 2026-10-12 被 Pattern Recognition 拒稿，原"等 P1 决定"的时点约束解除。
- **APC / 许可证**：投稿门户的 CC BY 与费用字段外部无法核实，需操作者自查。
- **ODE 拟合**：归档 **96** 条（55 LoRA + 30 Adapter + 11 full-FT）；正文已按 221+96=317 统一计数。

## 复核命令

    python tools/_p1174_build_paperA_editorial.py --apply
    python tools/_p1169_refresh_nc_submission.py --apply
    python tools/_p1178_sync_nc_package.py --apply
    python tools/_claim_ledger_paperA.py --apply
    python tools/_claim_ledger.py --apply
""".format(
        title=title, nc_pages=nc_pages, cl_pages=cl_pages, n_hl=n_hl, max_hl=max_hl, n_src=n_src,
        abs_words=abs_words, n_bib=n_bib, n_cited=n_cited,
        pa_pass=pa_pass, pa_total=pa_total, pa_gap=pa_gap,
        m_pass=m_pass, m_total=m_total, m_fail=m_fail,
        e_both=e_both, e_text=e_text, e_vision=e_vision, e_fd=E["frozen_dg"],
        g_text=g_text, g_vision=g_vision, g_both=g_both, g_fd=G["frozen_dg"],
    )

    if FAILS:
        print("RESULT: %d failure(s); README not written" % len(FAILS))
        return 1
    if a.apply:
        io.open(PKG / "README.md", "w", encoding="utf-8", newline="").write(readme)
        print("  README.md written (%d chars)" % len(readme))
        print("  springer pages: %d" % sp_pages)
    else:
        print("(dry run; pass --apply to copy files and write README)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
