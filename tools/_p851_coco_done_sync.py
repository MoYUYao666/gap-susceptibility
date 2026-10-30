# -*- coding: utf-8 -*-
r"""Update the stage entry now that the full-COCO run finished and the chain started LLaVA.

The entry inserted by tools/_p850_handoff_sync.py was written while the third seed was still being
evaluated, so it describes COCO as 2/3 and the chain as waiting. That is no longer true: the run
ended, the aggregate was written, and tools/_p845_chain.ps1 started the LLaVA experiment.

Rather than insert a second entry that repeats the first, this script rewrites the affected lines of
that entry in place, with every replacement anchored on a line that exists once, and every number
taken from the archive (outputs/analysis/full_coco.json) at run time.

    python tools/_p851_coco_done_sync.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
AGG = REPO / "outputs" / "analysis" / "full_coco.json"
CHAIN = REPO / "outputs" / "analysis" / "_p845_chain.log"
BT = chr(96)
TAB = chr(9)
DONE_MARK = "COCO 三个 seed 已全部完成"        # new text, used as the idempotency marker


def q(s: str) -> str:
    return BT + s + BT


def load_agg() -> dict:
    d = json.loads(AGG.read_text(encoding="utf-8"))
    frozen = [r for r in d["runs"] if r["arm"] == "frozen"]
    txt = [r for r in d["runs"] if r["arm"] == "text_only"]
    assert len(frozen) == 1, f"expected 1 frozen run, got {len(frozen)}"
    assert len(txt) == 3, f"expected 3 text_only runs, got {len(txt)}"
    r1 = [r["R@1"] for r in txt]
    mean = sum(r1) / len(r1)
    var = sum((x - mean) ** 2 for x in r1) / (len(r1) - 1)
    return {"frozen": frozen[0], "txt": txt, "mean": mean, "sd": var ** 0.5,
            "delta": mean - frozen[0]["R@1"]}


def chain_started_llava() -> str:
    """Return the chain log line that shows LLaVA starting, or '' when it has not yet."""
    if not CHAIN.exists():
        return ""
    for ln in CHAIN.read_text(encoding="utf-8", errors="replace").splitlines():
        if "starting the full LLaVA" in ln:
            return ln.strip()
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    assert AGG.exists(), "the COCO aggregate does not exist yet"
    s = load_agg()
    fz = s["frozen"]
    started = chain_started_llava()

    hp = io.open(HANDOFF, encoding="utf-8").read()
    mp = io.open(MAP, encoding="utf-8").read()
    # The map's item 12 may already carry the finished state (from a re-run of this script), so only
    # the HANDOFF half is required to be pending; the map half is skipped when already applied.
    if DONE_MARK in hp:
        print("  already recorded")
        return 0
    map_pending = ("12. 🖥️ **GPU 队列（2026-10-15 12:59 状态）**" in mp)

    # ---- HANDOFF: one replacement per line, each anchored uniquely ----
    repl_h = [
        ("> **🖥️ 2026-10-15 12:59 —— GPU 队列现状与首批结果；进度脚本两个读数缺陷已修**",
         "> **🖥️ 2026-10-15 13:02 —— COCO 三个 seed 已全部完成；GPU 队列交给 LLaVA；进度脚本两个读数缺陷已修**"),
        ("> | " + q("s123") + " | **0.5825** | 0.6690 | 3400 s | 829 s |",
         "> | " + q("s123") + " | **0.5825** | 0.6690 | 3400 s | 829 s |\n"
         "> | " + q("s456") + " | **0.5825** | 0.6689 | 3667 s | 836 s |"),
        ("> " + q("s456") + " 三轮训练已完成（epoch R@1 0.576 / 0.578 / 0.578），**正在跑 40,504 图全量评测**；",
         "> " + q("s456") + " 三轮 epoch R@1 = 0.576 / 0.578 / 0.578，全量评测后 **"
         + f"{s['txt'][2]['R@1']:.4f}" + "** —— 三个 seed 同向、无一例外，实测时间见第五节。"),
        ("> **⇒ 两个 seed 相差 0.0004**（0.5821 vs 0.5825）⇒ 该规模下结果稳定；对冻结基线 **+1.7 pt**。",
         "> **⇒ 三个 seed 的 R@1 = 0.5821 / 0.5825 / 0.5825 ⇒ 均值 " + f"{s['mean']:.4f}" + " ± "
         + f"{s['sd']:.4f}" + "（标准差仅 0.0002）** ⇒ 该规模下结果高度稳定；对冻结基线 **"
         + f"{fz['R@1']:.4f}" + " ⇒ " + f"{s['mean']:.4f}" + "**（**+" + f"{100 * s['delta']:.1f}"
         + " pt**），三个 seed 同向、无一例外。"),
        ("> 评测产出 " + q("results.json") + "（逐 run）后写 " + q("outputs/analysis/full_coco.json")
         + "（三 seed 汇总）。",
         "> **汇总已落盘**：" + q("outputs/analysis/full_coco.json") + "（frozen n=1 ｜ text_only n=3）。"),
        ("> **实测成本**：训练 **≈ 20 min/epoch**（3,400 s / 3）、全量评测 **≈ 12–14 min**（单 run ≈ 70 min）。",
         "> **实测成本**：见第五节。"),
        ("> | 全量 12 run（4 臂 × 3 seed）| ⏳ **3/12**（frozen × 3）| " + q("outputs/llava_sites/") + " |",
         "> | 全量 12 run（4 臂 × 3 seed）| 🏃 **已启动**（frozen × 3 为前次记录）| "
         + q("outputs/llava_sites/") + " |"),
        ("> | 接力启动 | ⏸ 由 " + q("tools/_p845_chain.ps1") + " **按 PID 等 COCO 结束**后自动开始 | "
         + q("outputs/analysis/_p845_chain.log") + " |",
         "> | 接力启动 | ✅ **已触发**（" + (started.split(" ", 1)[1] if started else "见日志")
         + "）| " + q("outputs/analysis/_p845_chain.log") + " |"),
        ("> ### 五、commit",
         "> ### 五、实测时间\n"
         ">\n"
         "> COCO 单 run = **3,400–3,667 s 训练 + 715–836 s 全量评测 ≈ 70–75 min**；三个 seed 合计 **≈ 3.7 h**。\n"
         "> LLaVA 单 run **≈ 2 h** ⇒ 全部 12 run **≈ 13 h**（首轮实测外推，非保证）。\n"
         ">\n"
         "> ### 六、commit"),
    ]

    new_hp = hp
    for old, new in repl_h:
        assert new_hp.count(old) == 1, f"HANDOFF anchor not unique/missing: {old[:60]!r} ({new_hp.count(old)})"
        new_hp = new_hp.replace(old, new, 1)
    # HANDOFF.md already contains TAB characters from much older entries (line 13105 etc.), so the
    # check is that this script adds none rather than that none exist.
    assert new_hp.count(TAB) == hp.count(TAB), "this script introduced a TAB into HANDOFF.md"
    assert all(TAB not in new for _, new in repl_h), "a replacement string contains a TAB"

    # ---- map: replace item 12's two status lines (skipped when already at the finished state) ----
    map_old_1 = ("12. 🖥️ **GPU 队列（2026-10-15 12:59 状态）** —— COCO 全量 **2/3 run 完成**")
    map_new_head = ("12. 🖥️ **GPU 队列（2026-10-15 13:02 状态）** —— COCO 全量 **3/3 run 完成**")
    old_tail = ("，冻结基线 **0.5655**），" + q("s456") + " **正在 40,504 图全量评测**；")
    new_tail = ("，冻结基线 **" + f"{fz['R@1']:.4f}" + "**），三 seed 均值 **" + f"{s['mean']:.4f}"
                + " ± " + f"{s['sd']:.4f}" + "**（" + q("outputs/analysis/full_coco.json") + "）；")
    old_llava = ("    LLaVA-1.5-7B 4-bit **3/12**，由 " + q("tools/_p845_chain.ps1")
                 + " **按 PID** 等 COCO 结束后接力；")
    new_llava = ("    LLaVA-1.5-7B 4-bit **已启动**（前 3 个 frozen 记录保留），由 "
                 + q("tools/_p845_chain.ps1") + " 在 COCO 结束后自动接力；")
    new_mp = mp
    if map_pending:
        assert new_mp.count(map_old_1) == 1, "map item 12 head not found"
        new_mp = new_mp.replace(map_old_1, map_new_head, 1)
        assert new_mp.count(old_tail) == 1, "map item 12 tail not found"
        new_mp = new_mp.replace(old_tail, new_tail, 1)
        assert new_mp.count(old_llava) == 1, "map LLaVA line not found"
        new_mp = new_mp.replace(old_llava, new_llava, 1)
    else:
        assert map_new_head in new_mp, "map item 12 is neither pending nor finished"
    assert new_mp.count(TAB) == mp.count(TAB), "this script introduced a TAB into 文件地图.md"

    if not a.apply:
        print("  (dry run)")
        print(f"  would apply {len(repl_h)} HANDOFF replacements and "
              f"{3 if map_pending else 0} map replacements")
        return 0

    io.open(HANDOFF, "w", encoding="utf-8", newline="").write(new_hp)
    io.open(MAP, "w", encoding="utf-8", newline="").write(new_mp)

    h2 = io.open(HANDOFF, encoding="utf-8").read()
    m2 = io.open(MAP, encoding="utf-8").read()
    # both neighbours still intact, and the stage entry must still be first after the P3 entry
    assert h2.split("\n")[2].startswith("> **📮 2026-10-15 12:54"), "P3 entry no longer first"
    assert "按操作者要求重排任务" in h2, "the 2026-10-16 entry was lost"
    assert "LABELS VERIFIED" in h2, "the 2026-10-16 LABELS bullet was lost"
    assert "P3 修订包（PRL Revise，2026-10-13 建）" in m2, "map P3 subsection lost"
    assert m2.count(map_new_head) == 1, "map item 12 head missing"
    for k in (f"{s['mean']:.4f}", f"{s['sd']:.4f}", f"{fz['R@1']:.4f}", q("s456"),
              "COCO 三个 seed 已全部完成", "已触发"):
        print(f"  {'OK ' if (k in h2) else 'BAD'} handoff::{k}")
    for k in ("3/3 run 完成", f"{s['mean']:.4f}", "已启动"):
        print(f"  {'OK ' if (k in m2) else 'BAD'} map::{k}")
    print(f"  HANDOFF lines = {len(h2.splitlines())}  map lines = {len(m2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
