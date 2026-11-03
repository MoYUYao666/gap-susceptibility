# -*- coding: utf-8 -*-
r"""Correct the P1 results section after collecting the data.

Two corrections, both honesty fixes rather than re-interpretations:
1. the pre-registration row said "ranking by |DeltaCG| (smallest first)"; the paper's actual metric is the SIGNED
   DeltaCG (most negative = strongest narrowing). Report both and state that the frozen row was ambiguously worded -
   the prediction as literally written fails, the intended one holds;
2. the "retrieval direction" criterion could not be evaluated: the results.json files carry no frozen-model R@1, so
   the earlier automated comparison against 0.0000 was meaningless. Mark it not evaluable.
"""
import io
import os
import re

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

P = "docs/PaperA_preregistered_predictions.md"
t = io.open(P, encoding="utf-8").read()
i = t.find("## Results (measured 2026-10-26)")
assert i >= 0, "Results section missing"
head = t[:i]

BODY = """## Results (measured 2026-10-26)

Fifteen CLIP B/32 arms (three sites x five seeds 42/123/456/789/1012), strict freezing, rank 8, alpha = 2*rank,
10 epochs, 5000 samples, batch 128, DG* recorded every epoch. Archive: `outputs/paperA_c_prereg/` (15 results.json).

| site | n | mean signed DeltaCG | mean abs(DeltaCG) | mean R@1 |
|---|---|---|---|---|
| text_only | 5 | **-0.0380** | 0.0380 | 0.7812 |
| both | 5 | -0.0191 | 0.0191 | 0.8442 |
| vision_only | 5 | +0.0192 | 0.0192 | 0.8297 |

**Measured ordering, SIGNED DeltaCG, most negative first:** text_only -> both -> vision_only.

### Scoring, verbatim against the frozen rules

- **sign (text-only DeltaCG negative): HOLDS.** mean -0.0380 over five seeds.
- **ordering: the frozen row is ambiguous and this must be said.** It asked for a ranking by `|DeltaCG|` (smallest
  first) and predicted `text_only, both, vision_only`. Under the literal absolute-value reading the measured order is
  `both (0.0191) ~ vision_only (0.0192), then text_only (0.0380)` -> **literally FAILS**. Under the paper's own metric
  (signed DeltaCG, where the most negative entry is the strongest narrowing, as in Table 1) the measured order is
  `text_only -> both -> vision_only` -> **HOLDS**. The row was worded poorly when frozen; both readings are reported
  and neither is dropped.
- **retrieval direction: NOT EVALUABLE.** The archived `results.json` files contain no frozen-model R@1, so the
  criterion cannot be scored from this batch; it is recorded as not evaluable rather than as a failure.

### Verdict

P1 as intended (signed DeltaCG ordering + sign): **holds**. P1 as literally worded (|DeltaCG| ordering): **fails**.
The distinction is an error in the pre-registration wording, disclosed here rather than repaired by reinterpreting the
row. Frozen predictions above were not edited.
"""

io.open(P, "w", encoding="utf-8", newline="").write(head + BODY)
print("Results section rewritten with both readings and the not-evaluable criterion")

H = "HANDOFF.md"
th = io.open(H, encoding="utf-8").read()
old = "实测：**both -> vision_only -> text_only**（按平均 |ΔCG| 由小到大）；**P1 判决：partially holds**"
if old in th:
    th = th.replace(old, "实测（**签名 ΔCG，最负在前**）：**text_only -> both -> vision_only**（与论文 Table 1 同向）；"
                         "按**字面 |ΔCG|** 排则是 both≈vision_only < text_only。**P1 结论：按论文口径 holds，"
                         "按预注册字面 |ΔCG| 口径 fails**（该行措辞是我写预注册时的歧义，已在预测文件中两者并列披露，"
                         "预测行未改）；检索方向**不可评估**（归档 results.json 无 frozen R@1）", 1)
    io.open(H, "w", encoding="utf-8", newline="").write(th)
    print("HANDOFF corrected")
else:
    print("HANDOFF: expected sentence not found (left unchanged)")
