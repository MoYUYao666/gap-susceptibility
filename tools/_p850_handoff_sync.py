# -*- coding: utf-8 -*-
r"""Handoff sync for the current stage: the running GPU queue, its first results, and the two fixes.

Operator instruction: "更新handoff". Three things belong in the handoff and only one of them was
already there (the P3 status row):

1. the live queue state and its measured results so far (COCO 2/3 runs, LLaVA 3/12, the chain that
   starts LLaVA automatically, the measured per-phase cost so an ETA can be judged);
2. the reporter defect that made every progress answer since 08:35 read a stale file, plus the
   second defect found while fixing it (a substring test matching a path, which mis-reported the
   active epoch);
3. the documentation-integrity incident from recording the P3 row (a folded `\t` in the text, and an
   in-place repair that cut the head off the following entry), with the rule that replaced it.

Insertion is by anchor on a clean base, never by deleting text in place. Backslashes are built from
chr(92) so no escape can be folded on write, and the inserted block is asserted TAB-free.

    python tools/_p850_handoff_sync.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
COCO_DIR = REPO / "outputs" / "full_coco"
BT = chr(96)
BS = chr(92)
TAB = chr(9)
MARK = "GPU 队列现状与首批结果"          # a phrase inside the HANDOFF entry
MAP_MARK = "12. 🖥️ **GPU 队列（2026-10-15 12:59 状态）**"   # the map item's own first line

# Anchors: the P3 entry ends with this line, and the next entry starts with this heading.
P3_LAST = "> 唯一下一步是**等下一次状态变化**（" + BT + "Under Review" + BT + " / " + BT + "Decision" + BT + "）。"
NEXT_HEAD = "> **🔄 2026-10-16 01:00 —— 按操作者要求重排任务；labels bug 修复；4-bit 噪声地板已量化**"
MAP_LIST_END = "11. ⏳ **本轮改动未推 GitHub**"


def read_runs() -> dict:
    """Read the per-run JSONs that exist, so every number printed comes from an archive."""
    out = {}
    for p in sorted(COCO_DIR.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        out[d.get("name")] = d
    return out


def q(name: str) -> str:
    return BT + name + BT


def build_entry() -> str:
    runs = read_runs()
    s42 = runs["full_text_only_r8_s42"]
    s123 = runs["full_text_only_r8_s123"]
    rows = [
        "| 阶段 | 状态 | 归档 |",
        "|---|---|---|",
        "| 冻结基线（40,504 图 / 202,654 caption 全 gallery）| ✅ 完成 | " + q("outputs/analysis/_p845_coco.out") + " |",
        "| " + q("full_text_only_r8_s42") + " | ✅ 完成 | " + q("outputs/full_coco/full_text_only_r8_s42.json") + " |",
        "| " + q("full_text_only_r8_s123") + " | ✅ 完成 | " + q("outputs/full_coco/full_text_only_r8_s123.json") + " |",
        "| " + q("full_text_only_r8_s456") + " | ⏳ 三轮训练完，正在全量评测 | " + q("outputs/analysis/_p845_coco.out") + " |",
        "| " + q("outputs/analysis/full_coco.json") + "（三 seed 汇总）| ⏳ 待 s456 评测完 | — |",
    ]
    return "\n".join([
        "> **🖥️ 2026-10-15 12:59 —— GPU 队列现状与首批结果；进度脚本两个读数缺陷已修**",
        ">",
        "> ### 一、COCO 全量（真 LoRA，10,000 训练图 / 全部 val2014 评测，rank 8，3 epoch）",
        ">",
        "> | run | R@1 | R@5 | 训练 | 评测 |",
        "> |---|---|---|---|---|",
        "> | 冻结基线 | **0.5655** | 0.6410 | — | 713.2 s |",
        "> | " + q("s42") + " | **" + f"{s42['R@1']:.4f}" + "** | " + f"{s42['R@5']:.4f}"
        + " | " + f"{s42['train_seconds']:.0f}" + " s | " + f"{s42['seconds']:.0f}" + " s |",
        "> | " + q("s123") + " | **" + f"{s123['R@1']:.4f}" + "** | " + f"{s123['R@5']:.4f}"
        + " | " + f"{s123['train_seconds']:.0f}" + " s | " + f"{s123['seconds']:.0f}" + " s |",
        ">",
        "> **⇒ 两个 seed 相差 0.0004**（" + f"{s42['R@1']:.4f}" + " vs " + f"{s123['R@1']:.4f}"
        + "）⇒ 该规模下结果稳定；对冻结基线 **+1.7 pt**。",
        "> " + q("s456") + " 三轮训练已完成（epoch R@1 0.576 / 0.578 / 0.578），"
        "**正在跑 40,504 图全量评测**；",
        "> 评测产出 " + q("results.json") + "（逐 run）后写 " + q("outputs/analysis/full_coco.json")
        + "（三 seed 汇总）。",
        "> **实测成本**：训练 **≈ 20 min/epoch**（3,400 s / 3）、全量评测 **≈ 12–14 min**"
        "（单 run ≈ 70 min）。",
        ">",
        "> ### 二、LLaVA-1.5-7B 4-bit 适配位置实验（" + q("outputs/llava_sites/") + "）",
        ">",
        "> | 阶段 | 状态 | 归档 |",
        "> |---|---|---|",
        "> | 全量 12 run（4 臂 × 3 seed）| ⏳ **3/12**（frozen × 3）| " + q("outputs/llava_sites/") + " |",
        "> | 接力启动 | ⏸ 由 " + q("tools/_p845_chain.ps1") + " **按 PID 等 COCO 结束**后自动开始 | "
        + q("outputs/analysis/_p845_chain.log") + " |",
        ">",
        "> 三个 frozen 记录一致（" + q("dg_rel_change") + " = −0.766%）；**4-bit 噪声地板 ≈ 0.8%**，"
        "各臂效应须超过它才算信号。",
        ">",
        "> ### 三、⚠️ 进度脚本（" + q("tools/_p841_status.py") + "）两个读数缺陷 —— 已修",
        ">",
        "> | # | 缺陷 | 后果 | 修法 |",
        "> |---|---|---|---|",
        "> | 1 | 日志路径写死在 " + q("_p839_coco.out") + "（**08:35 后不再更新**）| "
        "**08:35 起的每次进度答复都读旧文件**：s456 明明在训第 3 轮，脚本一直报「正在评测冻结基线」| "
        "改指正在写的 " + q("_p845_coco.out") + " |",
        "> | 2 | 用子串匹配 run 名 | 日志里 " + q("..._r8_s456" + BS + "results.json") + " 这类**路径**"
        "也算命中 ⇒ 锚点落到最后一行，该 run 的 epoch 全被当成不存在（报第 1/3 轮）| "
        "改用词边界 " + q("(?<![A-Za-z0-9_])…(?![A-Za-z0-9_])") + " |",
        ">",
        "> **教训**：状态脚本必须指**正在写的那个文件**，且判定阶段要用**结构化锚点**而非子串——"
        "否则报出的「现状」是几小时前的。",
        ">",
        "> ### 四、⚠️ 文档完整性事故与规则（落账 P3 状态条目时发生，已修复）",
        ">",
        "> 1. 落账脚本里的字面量 " + q(BS + "title{...}") + " 在写入时**反斜杠被折成制表符**，"
        + q("HANDOFF.md") + " 与 " + q("文件地图.md") + " 一度出现 " + q("<TAB>itle{...}") + "；",
        "> 2. 第一次「就地修补」用「跳过空行」规则删除损坏块，**越过条目末尾，把下一条目的开头删掉**"
        "（2026-10-16 01:00 标题 + 3 条要点）。",
        ">",
        "> **⇒ 现行规则**：① 反斜杠一律用 " + q("chr(92)") + " 拼，不用转义序列；"
        "② 插入块写盘前断言**不含制表符**且含预期字面量；"
        "③ **修补 = 在干净基线（" + q("git checkout -- <file>") + "）上重新插入，绝不就地删文本**；"
        "④ 写完断言**邻居完好**（标题行、下一条目标题、小节标题），不只比长度。",
        "> 两个失败脚本已移入 " + q("tools/obsolete/_p846_p847_superseded_by_p848/") + "（附 README）。",
        "> ⚠️ " + q("文件地图.md") + " 第 38/40/42/790/798/805 行的同类制表符损坏**早于本次会话**，"
        "按「只管今后，存量不动」保持原样。",
        ">",
        "> ### 五、commit",
        ">",
        "> " + q("1d080ae") + " P3 状态落账 + 进度脚本修复 ｜ " + q("b9d7d97") + " P3 应答工作文档转为存档。",
        ">",
        "> （P3 修订稿 " + q("With Editor") + " 的状态条目见上一条 2026-10-15 12:54。）",
        "",
    ])


def map_block() -> str:
    runs = read_runs()
    s42, s123 = runs["full_text_only_r8_s42"], runs["full_text_only_r8_s123"]
    return "\n".join([
        "12. 🖥️ **GPU 队列（2026-10-15 12:59 状态）** —— COCO 全量 **2/3 run 完成**"
        "（" + q("s42") + " R@1 **" + f"{s42['R@1']:.4f}" + "** / " + q("s123") + " R@1 **"
        + f"{s123['R@1']:.4f}" + "**，冻结基线 **0.5655**），" + q("s456") + " **正在 40,504 图全量评测**；",
        "    LLaVA-1.5-7B 4-bit **3/12**，由 " + q("tools/_p845_chain.ps1") + " **按 PID** 等 COCO 结束后接力；",
        "    实时一句话进度：`python tools\\_p841_status.py`。归档 " + q("outputs/full_coco/")
        + "、" + q("outputs/llava_sites/") + "；详见 " + q("HANDOFF.md") + " 顶部 2026-10-15 12:59 条目。",
        "13. ⚠️ **文档完整性规则（2026-10-15 立）** —— 落账脚本中的反斜杠一律用 " + q("chr(92)")
        + " 拼；插入块写盘前断言不含制表符；**修补一律在干净基线上重新插入，绝不就地删文本**；"
        "写完断言邻居完好。事故经过见 " + q("tools/obsolete/_p846_p847_superseded_by_p848/README.md") + "。",
    ])


def insert_after(text: str, anchor_line: str, block: str, prefix: bool = False,
                 span: int = 1) -> str:
    """Insert block on its own lines directly after the anchor, which may span several lines.

    With prefix=True the anchor is matched by startswith. The map's item 11 continues onto a second
    line ("    `docs/` ..."), so inserting after its first line splits the item and leaves the
    continuation stranded below the new text -- observed, and the reason span exists.
    """
    lines = text.split("\n")
    if prefix:
        idx = [i for i, ln in enumerate(lines) if ln.startswith(anchor_line)]
    else:
        idx = [i for i, ln in enumerate(lines) if ln == anchor_line]
    assert len(idx) == 1, f"expected exactly one anchor line, found {len(idx)}"
    i = idx[0] + span - 1
    return "\n".join(lines[: i + 1] + [""] + block.split("\n") + lines[i + 1:])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    runs = read_runs()
    # s42/s123 must be there; s456 may land while this runs, so require a subset, not equality.
    assert {"full_text_only_r8_s42", "full_text_only_r8_s123"} <= set(runs), \
        f"missing completed COCO runs: {sorted(runs)}"
    for k, d in runs.items():
        assert "R@1" in d, f"{k} has no R@1 -- archive is incomplete"

    hp = io.open(HANDOFF, encoding="utf-8").read()
    mp = io.open(MAP, encoding="utf-8").read()
    ent = build_entry()
    mb = map_block()
    assert TAB not in ent and TAB not in mb, "an inserted block contains a TAB"
    assert P3_LAST in hp and NEXT_HEAD in hp, "HANDOFF anchors not found"
    assert MAP_LIST_END in mp, "map anchor not found"

    # The map half is idempotent on the presence of item 12 at all, not on its exact header text:
    # tools/_p851 rewrites that header to the finished state, so matching the original wording would
    # make this script re-insert the block and duplicate items 12-13 (observed once).
    map_done = "12. 🖥️ **GPU 队列（" in mp
    if MARK in hp and map_done:
        print("  already recorded")
        return 0
    if a.apply:
        if MARK not in hp:
            hp = insert_after(hp, P3_LAST, ent)
            io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        if not map_done:
            mp = insert_after(mp, MAP_LIST_END, mb, prefix=True, span=2)
            io.open(MAP, "w", encoding="utf-8", newline="").write(mp)

        h2 = io.open(HANDOFF, encoding="utf-8").read()
        m2 = io.open(MAP, encoding="utf-8").read()
        # neighbours of both insertions must survive, and the P3 entry must still be the first one
        hl = h2.split("\n")
        assert hl[2].startswith("> **📮 2026-10-15 12:54"), "P3 entry is no longer first"
        assert any(ln == P3_LAST for ln in hl), "P3 entry lost its last line"
        assert any(ln == NEXT_HEAD for ln in hl), "the 2026-10-16 entry lost its heading"
        assert "LABELS VERIFIED" in h2, "the 2026-10-16 LABELS bullet was lost"
        assert h2.count(MARK) == 1, "stage entry duplicated in the handoff"
        assert m2.count(MAP_MARK) == 1, "map stage item duplicated"
        assert "P3 修订包（PRL Revise，2026-10-13 建）" in m2, "map P3 subsection lost"
        # item 12 must sit directly under item 11, not somewhere else in the file
        # (item 11 spans two lines, then the blank separator, then item 12)
        ml = m2.split("\n")
        i11 = [i for i, ln in enumerate(ml) if ln.startswith(MAP_LIST_END)][0]
        assert ml[i11 + 1].startswith("    " + BT + "docs/"), "map item 11 lost its second line"
        assert ml[i11 + 2] == "", "map item 11 is not followed by a blank separator"
        assert ml[i11 + 3].startswith("12. "), (
            f"map item 12 is not directly under item 11: next line = {ml[i11 + 3][:60]!r}")
        assert "P3 修订包（PRL Revise，2026-10-13 建）" in m2, "map P3 subsection lost"
        for k in ("0.5655", f"{runs['full_text_only_r8_s42']['R@1']:.4f}",
                  f"{runs['full_text_only_r8_s123']['R@1']:.4f}", "3/12", "_p845_chain.ps1"):
            print(f"  {'OK ' if k in h2 else 'BAD'} handoff::{k}")
        print(f"  HANDOFF lines = {len(h2.splitlines())}  map lines = {len(m2.splitlines())}")
        return 0

    print("  (dry run)")
    print(f"  would insert {len(ent.splitlines())} lines into HANDOFF.md after the P3 entry")
    print(f"  would insert {len(mb.splitlines())} lines into 文件地图.md after item 11")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
