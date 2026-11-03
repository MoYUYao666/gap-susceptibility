# -*- coding: utf-8 -*-
r"""Finalise the local upgrade round: record results in the handover docs and rebuild all revision packages.

Prerequisite: outputs/analysis/p3_rerun_analysis.json, a23_uatd_domain.json, a1_stopping_baselines_rules.json exist.
This script only writes docs and packages; it does NOT push the mirror and does NOT create any tag or release.

    python tools/_p1385_finalize_round.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HANDOFF = os.path.join(REPO, "HANDOFF.md")
MAP = os.path.join(REPO, "文件地图.md")
EVID = os.path.join(REPO, "docs", "EVIDENCE_MAP_2026-10-19.md")
A = "outputs/analysis/"


def load(name):
    p = os.path.join(REPO, A, name)
    return json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    p3 = load("p3_rerun_analysis.json")
    uatd = load("a23_uatd_domain.json")
    a1 = load("a1_stopping_baselines_rules.json")
    if not (p3 and uatd and a1):
        raise SystemExit("missing prerequisite archives: %s" % [n for n, v in
                                                                (("p3_rerun_analysis", p3), ("a23_uatd_domain", uatd),
                                                                 ("a1_stopping_baselines_rules", a1)) if not v])
    curve = {int(k): v for k, v in p3["curve"].items()}
    curve_txt = ", ".join("r=%d: %+.1f" % (r, v["dE_seed42"]) for r, v in sorted(curve.items()))
    perm = p3.get("permutation") or {}
    qwen = p3.get("qwen2b") or {}
    qwen_txt = ("local Qwen2-VL-2B check inconclusive（两 rank 轨迹相同，rank 未生效，未入稿）"
                if qwen.get("valid") is False else "无有效 Qwen 结果")
    uatd_txt = "; ".join("%s r(tau)=%+.2f r(CG)=%+.2f" % (k, v["r_tau"], v["r_CG"]) for k, v in uatd["models"].items())
    base = a1["rules"]
    ent = f"""> **🏁 2026-10-20 00:20 —— 本地升级全部完成：P3 完整曲线 + A23 第二声呐域 + A1 早停基线 + Commentary 合规段**
>
> | 项 | 结果 |
> |---|---|
> | **P3 当前协议完整曲线** | {curve_txt}（seed 42）；置换检验 r=5 vs r=6：p={perm.get('p_two_sided')}（n={perm.get('n_seeds')}，最小可达 p={perm.get('min_attainable_p')}）|
> | **P3 Qwen 本地检查** | {qwen_txt} |
> | **A23 UATD 第二声呐域** | {uatd_txt} — 已写入正文（扩展而非替换五域矩阵）|
> | **A1 早停基线** | min-M {base['min_M']['mean_regret']:.2f} vs max-softmax {base['max_softmax']['mean_regret']:.2f}、max-logit {base['max_logit']['mean_regret']:.2f}、entropy {base['min_entropy']['mean_regret']:.2f}、energy {base['min_energy']['mean_regret']:.2f}；60 checkpoints |
> | **A1 checkpoint 钩子** | `outputs/a1_monitor_ckpt/dtd_seed42/` 10 个 epoch LoRA 状态 |
> | **Commentary** | 六实例表 + "what reporting would change" 段，仍 7 页 |
> | **Release** | `RELEASE_NOTES_v2.0.md` 已备；**尚未建 tag/release**，等 mirror 推送与终审后执行 |
>
> 审计：A1 仅预期 I-02；A23 / Commentary / Paper A Springer READY/A；P3 待补充材料重编译后复审。冻结包未动。
>

"""
    mp = io.open(MAP, encoding="utf-8").read()
    row = (f"118. 🏁 **本地升级全部完成（2026-10-20 00:20）** —— P3 曲线 {curve_txt}；置换 p={perm.get('p_two_sided')}；"
           f"A23 第二声呐域（UATD）{uatd_txt}；A1 早停基线 min-M {base['min_M']['mean_regret']:.2f} vs 置信度 2.80–4.18；"
           f"Commentary 合规段守 7 页；release v2.0 待建（notes 已备）。\n")
    if a.apply:
        h = io.open(HANDOFF, encoding="utf-8").read()
        if "本地升级全部完成" not in h:
            i = h.find("# 项目交接文档")
            j = h.find("\n", i)
            io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ent + h[j + 1:])
            print("  handoff added")
        if "本地升级全部完成（2026-10-20 00:20）" not in mp:
            anchor = "117. 🔁 **P3 重跑归因"
            idx = mp.find(anchor)
            assert idx >= 0
            end = mp.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(mp[: end + 1] + row + mp[end + 1:])
            print("  map row added")
        import subprocess as sp
        pkgs = [
            ["tools/_p1336_build_venue_package.py", "--manuscript", "paper_a1/main.pdf", "--title-page",
             "paper_a1/title_page.pdf", "--cover-letter", "paper_a1/cover_letter.pdf", "--source", "paper_a1",
             "--figures", "paper_a1/figures", "--venue", "Pattern Analysis and Applications (A1)",
             "--out", "SUBMISSION/_venue_builds/A1_PAA_next", "--apply"],
            ["tools/_p1336_build_venue_package.py", "--manuscript", "paper3/paper_ieee/main.pdf", "--title-page",
             "paper3/paper_ieee/title_page_prl.pdf", "--cover-letter", "paper3/paper_ieee/cover_letter_prl.pdf",
             "--source", "paper3/paper_ieee", "--figures", "paper3/paper_ieee/figures", "--venue",
             "Pattern Recognition Letters (P3)", "--out", "SUBMISSION/_venue_builds/P3_PRL_next", "--apply"],
            ["tools/_p1336_build_venue_package.py", "--manuscript", "paper_a2/main_ieee.pdf", "--abstract",
             "paper_a2/abstract.pdf", "--cover-letter", "paper_a2/cover_letter.pdf", "--highlights",
             "paper_a2/highlights.pdf", "--source", "paper_a2", "--figures", "paper_a2/figures", "--venue",
             "IEEE JOE (A23)", "--out", "SUBMISSION/_venue_builds/A23_JOE_next", "--apply"],
            ["tools/_p1336_build_venue_package.py", "--manuscript", "paper_review_prl/main_prl.pdf",
             "--cover-letter", "paper_review_prl/cover_letter.pdf", "--highlights", "paper_review_prl/highlights.pdf",
             "--source", "paper_review_prl", "--figures", "paper_review_prl/figures", "--venue",
             "Pattern Recognition Letters (Commentary)", "--out", "SUBMISSION/_venue_builds/Commentary_PRL_next",
             "--apply"],
        ]
        for cmd in pkgs:
            r = sp.run([sys.executable] + cmd, cwd=REPO, capture_output=True, text=True)
            print("   package:", cmd[cmd.index("--out") + 1], "exit", r.returncode)
        print("  done; commit the changes manually")
    else:
        print("  (dry run)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
