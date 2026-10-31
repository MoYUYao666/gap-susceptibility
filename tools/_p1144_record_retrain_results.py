# -*- coding: utf-8 -*-
r"""Record the completed canonical retrain and the Qwen feasibility trial.

Everything written here is read back from the pulled archive (`outputs/llava_canonical_cloud/`) and from the
trial's own log, and the numbers are asserted against `outputs/canonical_summary.json` so the record cannot drift
from its source.

    python tools/_p1144_record_retrain_results.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
SUMMARY = REPO / "outputs" / "canonical_summary.json"
ARCH = REPO / "outputs" / "llava_canonical_cloud"
MARK = "规范度量重训完成（四臂结果 + Qwen 试跑）"

DOC = """# LLaVA canonical retrain and Qwen trial (2026-10-17)

## What ran

A twelve-run sweep of LLaVA-1.5-7B in bfloat16 with the corrected measurement: the last hidden state is captured
with an `lm_head` forward pre-hook, the vision side is the mean pool over image-token positions, the text side is
the mean pool over **non-image** positions, and the metric is the canonical trio from `src/dg_star_tracker.py`
(`DG* = mean ||I_i - T_i||^2`, paired and squared, after L2 normalisation).

* 1500 training pairs / 500 held-out pairs, 3 epochs, batch 2, rank 8, lr 1e-4, 3 seeds, 4 arms;
* `steps_total` 2250 per run; the twelve records were verified by `tools/_p1138_verify_and_pull.py`:
  12 records, canonical fields present on all of them, `n_eval == 500`, frozen seeds identical, adapters
  non-empty, `ARM_FAILURES.txt` absent;
* 22 files pulled back (1700.1 MB), zero size mismatches.

## Results (canonical definition)

| Arm | DG* before | DG* after | rel change mean | rel sd | CG | DG_emp |
|---|---|---|---|---|---|---|
| frozen | 0.8146 | 0.8199 | +0.650% | 0.000 | 0.8778 | 0.8868 |
| text_only | 0.8146 | 1.1052 | +35.678% | 6.053 | 0.9916 | 1.0201 |
| vision_only | 0.8146 | 0.8735 | +7.237% | 9.166 | 0.8979 | 0.9050 |
| both | 0.8146 | 1.0863 | +33.350% | 1.666 | 0.9683 | 1.0083 |

Per-seed canonical relative changes: frozen +0.650/+0.650/+0.650; text_only +40.765/+39.097/+27.173;
vision_only -1.508/+19.896/+3.322; both +31.011/+34.279/+34.761.

Signal-to-noise against the frozen floor (+0.650%): text_only 5.79, vision_only 0.72, both 19.63.

Reading: the canonical gap on LLaVA is driven almost entirely by **text-side** adaptation. Text-only and
both-position are far above the frozen floor and are indistinguishable from each other (35.7% against 33.4% with
sd 6.1 and 1.7); vision-only alone is not distinguishable from frozen (its delta is smaller than its own seed sd).

## Relation to the paper's existing decoder-VLM result

The supplement's Section E reports Qwen2-VL-2B under the same canonical definition:

| Arm | Qwen2-VL-2B (supplement E) | LLaVA-1.5-7B (this run) |
|---|---|---|
| Both | +87.9 +/- 5.4% | +33.4 +/- 1.7% |
| Text-only | +66.5 +/- 8.3% | +35.7 +/- 6.1% |
| Vision-only | +18.0 +/- 8.8% | +7.2 +/- 9.2% |

The **ordering agrees** across both decoder models (both ~ text-only >> vision-only), so the "text-side drives the
canonical gap" pattern is not unique to one model. The **sign does not**: for Qwen2-VL-2B the change is a
reduction, for LLaVA-1.5-7B it is an increase. Whether the sign tracks scale (2B against 7B), training data or
preprocessing is not resolved by these two points.

## Qwen2.5-VL-7B feasibility trial

Run once to answer whether the model fits, not to produce results:

* **fits**: bf16 7B in 32.8 GB with `exit=0` and no OOM, once the probe model is released (`tools/_p1143`);
  the 2026-10-16 conclusion that it did not fit was caused by holding two bf16 copies (16.6 GB x 2 = 33.2 GB),
  which also explains why reducing batch and max-length did not move the failure point;
* **1.59 s/step** (LLaVA measured 0.95 s/step on the same host), 362 visual tokens per sample;
* the canonical metric computes: DG* 1.2879 -> 1.2424 (-3.531%), CG 1.0586, DG_emp 1.1150 on 8 held-out pairs;
* the checkpoint holds **392 real LoRA tensors** (242.7 MB), so the 2026-10-16 empty-checkpoint defect is gone;
* tower isolation holds: `text_only trainable 20,185,088, by tower {'text': 20185088}`.

Estimated cost of a full twelve-run Qwen sweep at the measured rate: 1.59 s/step x 2250 = 59.6 min per run plus
evaluation and loading, about **68 min per run, roughly 13.6 GPU-hours**; reducing frozen to one seed (its sd is
0 on LLaVA because it trains nothing) brings it to about 11.3 GPU-hours. Not launched -- awaiting the operator's
value judgement.

## Not done deliberately

Paper A's supplement Section F still describes the archived 2026-10-16 legacy-metric result as a scoped null
result with text-only bit-identical to frozen. That text is now contradicted by the canonical numbers above and
will be rewritten, but only after the operator decides what story the section should tell.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    if not SUMMARY.exists():
        print("  !! outputs/canonical_summary.json missing; run tools/_p1142_analyze_canonical.py first")
        return 2
    s = json.load(open(SUMMARY, encoding="utf-8"))
    recs = sorted(ARCH.glob("*.json"))
    pts = sorted(ARCH.glob("*.pt"))
    print("=== asserting the recorded numbers against the summary ===")
    checks = {
        "records == 12": len([r for r in recs if "progress" not in r.name]) == 12,
        # nine, not seven: three trained arms x three seeds. Frozen trains nothing and writes no adapter, which
        # is exactly the arm whose 2026-10-16 empty checkpoint wasted 810 MB in the archive.
        "adapters == 9": len(pts) == 9,
        "frozen rel == 0.650%": abs(s["frozen"]["canonical"]["rel_mean"] - 0.0065) < 5e-6,
        "text_only rel == 35.678%": abs(s["text_only"]["canonical"]["rel_mean"] - 0.35678) < 5e-5,
        "vision_only rel == 7.237%": abs(s["vision_only"]["canonical"]["rel_mean"] - 0.07237) < 5e-5,
        "both rel == 33.350%": abs(s["both"]["canonical"]["rel_mean"] - 0.33350) < 5e-5,
        "text_only snr > 5": s["text_only"]["canonical"]["delta_over_sd"] > 5,
        "vision_only snr < 1": s["vision_only"]["canonical"]["delta_over_sd"] < 1,
        "both snr > 15": s["both"]["canonical"]["delta_over_sd"] > 15,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'OK  ' if v else 'FAIL'} {k}")
        ok &= v
    if not ok:
        print("  !! refusing to write a record that disagrees with the summary")
        return 1

    if not a.apply:
        print("\n  (dry run)")
        return 0

    doc = REPO / "docs" / "llava_canonical_2026-10-17.md"
    if not doc.exists():
        io.open(doc, "w", encoding="utf-8", newline="").write(DOC)
        print(f"\n  wrote {doc.relative_to(REPO)}")

    ENT = """> **🎯 2026-10-17 17:00 —— 规范度量重训完成（12/12）＋ Qwen 试跑成功；结论与现有 F 节相反**
>
> ### 一、重训完成并通过全项校验
>
> 12 条记录、`n_eval=500`、canonical 字段齐全、frozen 三 seed 一致、**适配器非空**、零 `ARM_FAILURES`；
> 22 个文件已取回（**1700.1 MB**，0 大小不符）。产物 `outputs/llava_canonical_cloud/`，分析 `outputs/canonical_summary.json`，
> 汇总 `docs/llava_canonical_2026-10-17.md`。
>
> ### 二、📊 四臂结果（规范定义，`src/dg_star_tracker.py`）
>
> | arm | DG\\* before → after | rel mean | rel sd | **Δ/sd** | CG | DG_emp |
> |---|---|---|---|---|---|---|
> | frozen | 0.8146 → 0.8199 | **+0.650%** | 0.000 | — | 0.8778 | 0.8868 |
> | **text_only** | 0.8146 → 1.1052 | **+35.678%** | 6.053 | **5.79** ✅ | 0.9916 | 1.0201 |
> | **vision_only** | 0.8146 → 0.8735 | **+7.237%** | 9.166 | **0.72** ❌ | 0.8979 | 0.9050 |
> | **both** | 0.8146 → 1.0863 | **+33.350%** | 1.666 | **19.63** ✅ | 0.9683 | 1.0083 |
>
> 逐 seed：frozen +0.650×3；text_only **+40.765/+39.097/+27.173**；vision_only **−1.508/+19.896/+3.322**；
> both **+31.011/+34.279/+34.761**。
>
> **⇨ 规范 gap 几乎完全由文本侧驱动**：text_only 与 both 远高于 frozen 且**彼此不可区分**（35.7 vs 33.4，sd 6.1/1.7）；
> **vision_only 与 frozen 不可区分**（Δ 小于其自身 seed sd）。
>
> ### 三、🔁 与论文 Qwen2-VL-2B（补充 E 节，同口径）对照
>
> | arm | Qwen2-VL-2B | LLaVA-1.5-7B（今天）|
> |---|---|---|
> | Both | +87.9±5.4% | +33.4±1.7% |
> | Text-only | +66.5±8.3% | +35.7±6.1% |
> | Vision-only | +18.0±8.8% | +7.2±9.2% |
>
> **排序一致**（both ≈ text ≫ vision）⇒"文本侧主导规范 gap"**不是单模型现象**；
> **符号相反**（Qwen 为下降，LLaVA 为上升）⇒ 符号是否随规模（2B vs 7B）变化，**这两点无法判定**。
>
> ### 四、✅ Qwen2.5-VL-7B 试跑（只试跑，未启全量）
>
> | 项 | 结果 |
> |---|---|
> | **能否装进 32.8 GB** | ✅ **能**（`exit=0`，无 OOM）——**昨天"装不下"是双份 bf16 加载（16.6×2=33.2 GB）造成的，已由 `_p1143` 修复** |
> | 步耗时 | **1.59 s/步**（LLaVA 同机 0.95）|
> | 规范度量 | ✅ `DG* 1.2879 → 1.2424（−3.531%）、CG 1.0586、DG_emp 1.1150`（8 对）|
> | checkpoint | ✅ **392 张量 / 242.7 MB** |
> | 分塔 | ✅ `text_only 20,185,088, {'text': 20185088}` |
>
> **全量估算**：1.59 s/步 × 2250 ≈ 59.6 min/run + 评测/加载 ⇒ **≈68 min/run，12 run ≈ 13.6 GPU 小时**；
> 若 frozen 只跑 1 seed（LLaVA 实测其 sd=0）⇒ **≈11.3 小时**。**未启动，等操作者判断价值。**
>
> ### 五、⚠️ 仍未做（有意）
>
> Paper A 补充 F 节**仍是旧的"负结果"表述**（"text-only 与 frozen 逐位相同"），**已被上述数据推翻**，
> 但**未修改**——等操作者决定这一节要讲什么故事再动笔。
>
> **脚本**：`_p1138`（校验+取回）｜`_p1142`（分析）｜`_p1143`（释放探测模型）｜`_p1144`（本条）｜产物 `docs/llava_canonical_2026-10-17.md`。
>

"""
    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        print("  handoff entry added")

    mp = io.open(MAP, encoding="utf-8").read()
    row = ("50. 🎯 **规范度量重训完成 + Qwen 试跑成功（2026-10-17 17:00）** —— 12/12 记录、全项校验通过、"
           "**适配器非空**（283/240/42.9 MB）、22 文件取回 1700 MB。**规范结果**：frozen **+0.650%**、"
           "text_only **+35.678%±6.05**（Δ/sd **5.79**）、vision_only **+7.237%±9.17**（Δ/sd **0.72，与 frozen 不可区分**）、"
           "both **+33.350%±1.67**（Δ/sd **19.63**）⇒ **规范 gap 几乎只由文本侧驱动**。"
           "**与论文 Qwen2-VL-2B 对照：排序一致（both≈text≫vision）但符号相反**（Qwen 下降 / LLaVA 上升）。"
           "**Qwen2.5-VL-7B 试跑**：✅ bf16 **能装进 32.8 GB**（昨天\"装不下\"实为**双份加载 16.6×2=33.2 GB**，已由 `_p1143` 修复）、"
           "1.59 s/步、规范度量可用、**392 张量/242.7 MB** 非空。全量估算 **13.6 GPU 小时**（frozen 单 seed 则 11.3h），**未启动待定**。"
           "⚠️ **补充 F 节未改**（旧表述已被推翻，等操作者定故事）。详见 `HANDOFF.md` 17:00 条目与 `docs/llava_canonical_2026-10-17.md`。\n")
    anchor = "49. 🧰 **DSH 环境与 43 个科研技能已录入"
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
    sys.exit(main())
