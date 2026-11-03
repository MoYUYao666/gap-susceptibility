# -*- coding: utf-8 -*-
r"""Record the corrected Qwen2-VL-2B results and the shutdown of the host.

Numbers are asserted against `outputs/vlm_clean_summary.json` before they are written into the handover documents,
and the shutdown record states the evidence (port probes and a failed connection), not just "done".

    python tools/_p1165_record_e_result.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
SUM = REPO / "outputs" / "vlm_clean_summary.json"
MARK = "E 节干净重跑完成并已关机"

ENT = """> **✅ 2026-10-17 19:55 —— 补充 E 节干净重跑完成（39/39）＋ 云端主机已关机**
>
> ### 一、结果（干净口径，相对 frozen 基线的降幅）
>
> frozen 基线：**clean DG\\* = 0.777826**，CG = 0.742107（320 对；与扫描同一 train split）。
>
> | arm | n | 训练后 clean DG\\* | **相对 frozen 降幅** | seed sd | legacy DG\\*（同批模型）|
> |---|---|---|---|---|---|
> | text_only | **13** | 0.0253 | **96.74%** | 0.29% | 2.0103 |
> | vision_only | **13** | 0.0824 | **89.41%** | 1.01% | 2.0322 |
> | both | **13** | 0.0111 | **98.57%** | 0.44% | 2.0192 |
>
> **⇨ 排序 `both > text_only > vision_only`**，**vision-only 降得最少**；seed 分散仅 0.3–1.0%，非常干净。
> **这与原 E 表的排序一致**（原表 87.9 / 66.5 / 18.0），但**量级完全不同**（原 text_only 66.5% vs 实测 **96.7%**）。
> **legacy 值恒在 ≈2.01–2.03 不动** ⇒ 再次证明旧口径测的是两个固定随机投影之间的距离，不是图像-文本 gap。
>
> ### 二、与 G 节（LLaVA-1.5-7B，干净口径、生成目标）的关系
>
> | | 目标 | 干净口径下各臂相对 frozen 的变化 |
> |---|---|---|
> | **E**（Qwen2-VL-2B）| **对比对齐** | 全部**下降**：both 98.6 > text 96.7 > **vision 89.4** |
> | **G**（LLaVA-1.5-7B）| **caption 生成** | 全部**上升**：**vision +121.5** > both +95.7 > text +73.3 |
>
> **两层结论**：
> 1. **两表不宣称量级可比**（目标不同：一个直接最小化对齐、一个训生成）；
> 2. 但两者在**"视觉侧的相对位置"**上互相印证：**视觉侧单独干预既最难把 gap 拉低（E 里降得最少），又最容易把 gap 推高（G 里升得最多）**
>    ⇒ 视觉侧是对 gap 影响最"不可控"的一侧，文本侧则是最可预测的一侧。这层结论可以写。
>
> ### 三、校验与取回（关机前置条件，全部满足）
>
> | 检查 | 结果 |
> |---|---|
> | 记录数 | **39/39**（3 臂 × 13 seed），`ALL_STREAMS_DONE`，**零 traceback** |
> | 逐条断言 | 每条 3 个 epoch 值、`legacy_dg_star`/`cg`/`loss`/token 计数齐全、图像与 caption mask 均非空、分塔隔离正确、epoch-3 clean DG\\* 均低于 frozen 基线 ⇒ **全部通过** |
> | 取回 | **53 个文件**（39 run + 13 summary + frozen）**0 不匹配**，另含三份日志 |
> | 汇总 | `outputs/vlm_clean_summary.json`；数据 `outputs/vlm_clean_cloud/` |
>
> ### 四、🔴 关机记录（按 `AGENTS.md` 云端收尾规则）
>
> | 步骤 | 证据 |
> |---|---|
> | ① 确认跑完 | `ALL_STREAMS_DONE`，`ps` 无残留进程，零 traceback |
> | ② 全项校验 | 见上表，断言全过 |
> | ③ 取回产物 | 53 文件 0 不匹配，日志已拉回 |
> | ④ 执行关机 | `sync; shutdown -h now`（通道随即关闭）|
> | ⑤ 验证不可达 | 端口探测 **3/3 False**；SSH `NoValidConnectionsError` ⇒ **确认已关机** |
>
> 关机时间：**2026-10-17 约 19:55（Asia/Shanghai）**。主机 `connect.westc.seetacloud.com:16320`。
>
> ### 五、⏭️ 下一步（纯本地，无需云端）
>
> 1. 改写补充 **E、G 两节** + `discussion.tex` ¶32 + 摘要相关句；
> 2. 过 `_claim_ledger_paperA.py`（新增 E/G 的断言）；
> 3. 重编译 `paper合/main_nc.pdf` 与 `main_springer.pdf`；更新 `NC_submission/`。
>
> **脚本**：`_p1150`（扫描）｜`_p1163`（frozen 基线）｜`_p1164`（校验+取回+汇总）｜`_p1165`（本条）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not SUM.exists():
        print("  !! outputs/vlm_clean_summary.json missing")
        return 2
    s = json.load(io.open(SUM, encoding="utf-8"))
    fz = s["frozen"]["dg_star"]
    print(f"=== asserting the recorded numbers (frozen {fz:.6f}) ===")
    ok = True
    expect = {"text_only": (0.0253, 96.74), "vision_only": (0.0824, 89.41), "both": (0.0111, 98.57)}
    for arm, (ep3, red) in expect.items():
        got_ep3 = s["per_arm"][arm]["dg_star_ep3_mean"]
        got_red = s["per_arm"][arm]["reduction_mean"]
        good = abs(got_ep3 - ep3) < 5e-4 and abs(got_red - red) < 0.05
        print(f"  {'OK  ' if good else 'FAIL'} {arm:<12} ep3 {got_ep3:.4f} (exp {ep3}) | reduction {got_red:.2f}% (exp {red})")
        ok &= good
    n = s["verification"]["n_records"]
    print(f"  {'OK  ' if n == 39 else 'FAIL'} records {n} == 39")
    ok &= n == 39
    if not ok:
        print("  !! refusing to write a record that disagrees with the summary")
        return 1
    if not a.apply:
        print("\n  (dry run)")
        return 0

    doc = REPO / "docs" / "qwen_e_clean_rerun_2026-10-17.md"
    if not doc.exists():
        body = "# Qwen2-VL-2B clean re-run (2026-10-17 19:55)\n\n"
        body += ("Same training protocol as `tools/_p47_qwen_train.py` (400 samples, 3 epochs, batch 2, rank 8,\n"
                 "alpha 16, contrastive objective, 13 seeds per arm), with the measurement corrected: the text side\n"
                 "is the caption span rather than every non-padding position, and the two fixed random projections\n"
                 "are removed. Produced by `tools/_p1150_qwen_clean_sweep.py`; baseline by\n"
                 "`tools/_p1163_qwen_frozen_baseline.py`.\n\n")
        body += f"* frozen clean DG* = {fz:.6f} (CG {s['frozen']['cg']:.6f})\n"
        for arm in ("both", "text_only", "vision_only"):
            r = s["per_arm"][arm]
            body += (f"* {arm:<12} ep3 {r['dg_star_ep3_mean']:.4f}, reduction {r['reduction_mean']:.2f}% "
                     f"+/- {r['reduction_sd']:.2f}, legacy {r['legacy_ep3_mean']:.4f}\n")
        body += ("\nOrdering: both > text_only > vision_only in reduction, i.e. vision-only moves the clean gap\n"
                 "least; the legacy construction stays at ~2.0 for every arm, which is the two random projections\n"
                 "talking, not the gap.\n\n"
                 "Note the objective differs from the LLaVA run (contrastive here, caption cross-entropy there), so\n"
                 "the two tables are not compared in magnitude -- only in which side is least/most consequential.\n")
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
    row = ("55. ✅ **E 节干净重跑完成（39/39）＋ 云端已关机（2026-10-17 19:55）** —— 干净口径、相对 frozen(0.777826)："
           "text_only **96.74%±0.29**、vision_only **89.41%±1.01**、both **98.57%±0.44** ⇒ **both > text > vision**，"
           "**vision 降得最少**；legacy 恒 ≈2.01–2.03（证明旧口径测的是投影差）。与 G（LLaVA，生成目标，"
           "vision +121.5 > both +95.7 > text +73.3）**不宣称量级可比**，但共同指向**视觉侧对 gap 最不可控**。"
           "校验：39 条全过断言、**53 文件取回 0 不匹配**；**关机已验证不可达（端口 3/3 False）**。"
           "数据 `outputs/vlm_clean_cloud/`、`outputs/vlm_clean_summary.json`。详见 `HANDOFF.md` 19:55 条目。\n")
    if "E 节干净重跑完成（39/39）" not in mp:
        anchor = "54. 🧹 **工作区清理"
        idx = mp.find(anchor)
        if idx >= 0:
            end = mp.find("\n", idx)
            mp = mp[: end + 1] + row + mp[end + 1:]
            io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
            print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
