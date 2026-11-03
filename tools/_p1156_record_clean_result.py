# -*- coding: utf-8 -*-
r"""Record the clean LLaVA measurement and the correction it forces, then commit-ready the docs.

This entry exists because an earlier claim in this session was wrong and the documents must say so rather than
quietly drop it:

  * the sweep's own measurement used the **prompt** as the text side (`with_labels=False`, so the sequence held no
    caption), and that produced text_only +35.7%, vision_only +7.2% -- i.e. "the text side dominates";
  * re-measuring the same nine adapters with the text side taken from the **caption positions** reverses it:
    text_only +73.3%, both +95.7%, **vision_only +121.5%**, so the vision side moves the clean gap most.

The numbers written here are asserted against `outputs/canonical_caption_metric.json` first.

    python tools/_p1156_record_clean_result.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
ART = REPO / "outputs" / "canonical_caption_metric.json"
MARK = "干净口径反转"

ENT = """> **🔁 2026-10-17 18:20 —— 干净口径测完，**推翻我先前的结论**：视觉侧移动 gap 最多（与论文一致）**
>
> ### 一、⚠️ 先认错：我下午报的"文本侧主导"是**假象**
>
> 下午我按重训脚本自带的口径报告：text_only **+35.7%**、vision_only **+7.2%** ⇒ 得出"文本侧主导、视觉侧几乎不动"。
> **那是错的**：该口径的文本侧取的是**提示词**（`_p820:200`，`with_labels=False` ⇒ 序列里**不含 caption**）。
>
> ### 二、干净口径（已实测，`tools/_p1145`，只做前向，无需重训）
>
> 定义：**I** = 末层隐状态在**图像 token** 位置均值池化；**T** = 末层隐状态在 **caption 位置**均值池化
> （`labels != -100`，每样本 **28** 个 caption token、**576** 个图像 token）；两侧 L2 归一化、**无投影**。
>
> | arm | 各 seed 的 clean DG\\* | 相对 frozen | 臂内 sd |
> |---|---|---|---|
> | frozen | **0.3566** | — | —（不训练，确定性）|
> | **text_only** | 0.5976 / 0.6000 / 0.6558 | **+73.27%** | 7.54 |
> | **both** | 0.6634 / 0.6971 / 0.7325 | **+95.66%** | 7.91 |
> | **vision_only** | 0.7114 / 0.8066 / 0.8510 | **+121.48%** | 16.33 |
>
> **⇨ 排序 vision_only > both > text_only**，即**视觉侧干预移动 gap 最多、文本侧最少** ——
> **与论文正文（CLIP 双塔）的核心论点同向**，也与"视觉侧是干预落点"的叙述一致。
>
> ### 三、三种口径的对比（同一批 9 个适配器，量化而非断言）
>
> | arm | **clean（caption 侧，无投影）** | prompt+caption | 提示词only（下午那个错的）|
> |---|---|---|---|
> | text_only | **+73.3%** | +57.2% | +35.7% |
> | vision_only | **+121.5%** | +92.9% | +7.2% |
> | both | **+95.7%** | +75.2% | +33.4% |
>
> ⇒ **三种口径给出两种排序**；只有 caption 侧（与论文 `src/dg_star_tracker.py` 同义）那种才是可发表的。
> 下午那个口径把 vision_only 压到 7.2%，纯属"文本侧=提示词"造成的。
>
> ### 四、✅ 已据此启动 E 节（Qwen2-VL-2B）的干净重跑
>
> | 项 | 值 |
> |---|---|
> | 模型 | Qwen2-VL-2B-Instruct（**4.42 GB**，2 分片，镜像多连接下齐）|
> | 数据 | Flickr30k fixture：**120 图 / 600 样本**（从 4.39 GB 归档**只解出需要的那几张**，未全量解压）|
> | 协议 | **与 `_p47` 完全一致**：400 样本 × 3 epoch、batch 2、rank 8、α=16、lr 1e-4、**对比损失** |
> | 只改测量 | T 取 **caption 位置**（原取全部非 padding）、**去掉两个随机投影**；同一前向顺带记录旧口径以便量化 |
> | 规模 | 3 臂 × **13 seed** = 39 run，两路并行 |
> | 冒烟 | ✅ `loss 0.6374`、clean DG\\* 0.7684、**legacy DG\\* 2.1471（≈2，正好印证旧口径被随机投影主导）**、分塔 `vision 0 / language 392` |
>
> ### 五、⏭️ 跑完之后
>
> 1. 按干净口径重算 E 的三臂均值±sd，再与 G 节（LLaVA，**同口径、但训练目标不同：SFT 生成**）对照；
> 2. 改写 E、G 两节 + `discussion.tex` ¶32 + 摘要相关句；过 `_claim_ledger_paperA.py`；重编译两个 PDF。
>
> **⚠️ 注意**：E 与原 G 的**训练目标仍然不同**（E = 对比对齐；G = caption 生成），所以**两表不宣称量级可比**，
> 只宣称"不同目标、不同模型下，视觉侧的相对位置"这一层结论。
>
> **脚本**：`_p1145`（干净重测）｜`_p1150`（修正版 Qwen 扫描）｜`_p1153`（Flickr fixture）｜`_p1155`（39-run 启动器）｜`_p1156`（本条）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not ART.exists():
        print("  !! outputs/canonical_caption_metric.json missing")
        return 2
    d = json.load(io.open(ART, encoding="utf-8"))
    runs = d["runs"]
    fz = runs["frozen"]["clean"]["dg_star"]
    print(f"=== asserting the clean numbers (frozen {fz:.4f}) ===")
    ok = True
    checks = [("frozen ~0.3566", abs(fz - 0.3566) < 5e-4)]
    for arm, expect in (("text_only", 73.27), ("vision_only", 121.48), ("both", 95.66)):
        vals = [v["clean"]["dg_star"] for k, v in runs.items() if k.startswith(arm)]
        rel = st.mean([100 * (x - fz) / fz for x in vals])
        good = abs(rel - expect) < 0.05
        checks.append((f"{arm} mean rel {rel:+.2f}% ~ {expect:+.2f}%", good))
        ok &= good
    for label, good in checks:
        print(f"  {'OK  ' if good else 'FAIL'} {label}")
        ok &= good
    if not ok:
        print("  !! refusing to write a record that disagrees with the measurement")
        return 1
    if not a.apply:
        print("\n  (dry run)")
        return 0

    doc = REPO / "docs" / "llava_clean_gap_2026-10-17.md"
    if not doc.exists():
        body = ("# LLaVA clean-gap measurement (2026-10-17 18:00)\n\n"
                "Same nine adapters as the canonical retrain, re-measured with the text side taken from the caption\n"
                "positions instead of the instruction prompt, and with no projection. Forward passes only.\n\n"
                f"* frozen DG* = {fz:.4f}\n"
                "* text_only  +73.27% +/- 7.54   (0.5976 / 0.6000 / 0.6558)\n"
                "* both       +95.66% +/- 7.91   (0.6634 / 0.6971 / 0.7325)\n"
                "* vision_only +121.48% +/- 16.33 (0.7114 / 0.8066 / 0.8510)\n\n"
                "Ordering: vision_only > both > text_only -- the vision side moves the clean gap most, which agrees\n"
                "with the paper's dual-encoder result. The earlier 'text side dominates' reading was produced by a\n"
                "measurement whose text side was the prompt (no caption in the sequence) and is superseded.\n\n"
                "Source: `outputs/canonical_caption_metric.json`, produced by `tools/_p1145_clean_gap_measure.py`.\n")
        io.open(doc, "w", encoding="utf-8", newline="").write(body)
        print(f"  wrote {doc.relative_to(REPO)}")

    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        print("  handoff entry added")

    mp = io.open(MAP, encoding="utf-8").read()
    row = ("52. 🔁 **干净口径反转：视觉侧移动 gap 最多（2026-10-17 18:20）** —— **先认错**：下午报的"
           "\"文本侧主导 +35.7% / 视觉侧 +7.2%\"是**假象**（该口径文本侧取的是**提示词**、序列不含 caption）。"
           "用 **I=图像 token、T=caption token、无投影** 重测同一批 9 个适配器（只前向，`_p1145`）："
           "frozen **0.3566**、text_only **+73.27%±7.54**、both **+95.66%±7.91**、**vision_only +121.48%±16.33** "
           "⇒ **排序 vision > both > text，与论文核心论点同向**。三种口径对比见 `HANDOFF.md`。"
           "已据此启动 **E 节（Qwen2-VL-2B）干净重跑**：模型 4.42 GB、Flickr fixture 120 图/600 样本、协议与 `_p47` 一致、"
           "仅改测量，**39 run 两路并行**；冒烟 `legacy DG*≈2.15` 印证旧口径被随机投影主导。"
           "⚠️ E（对比目标）与 G（生成目标）**仍不宣称量级可比**。详见 `docs/llava_clean_gap_2026-10-17.md`。\n")
    anchor = "51. 🔬 **发现 E/F 两节的测量口径都不是正文定义"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    else:
        print("  !! map anchor not found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
