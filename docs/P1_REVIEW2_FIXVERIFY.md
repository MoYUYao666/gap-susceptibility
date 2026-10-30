# P1 — Remediation Round 2: Fix-Verification Report (built-PDF level)

**Verifier role**: independent verification reviewer, read-only on the workspace. The only file written is this report.
**Manuscript (P1)**: *Protect, Don't Perturb: Cross-Modal Alignment under PEFT of Vision-Language Models* — sole author Hongrui Wan, `PR-D-26-10149`, under review at *Pattern Recognition*.
**Artefact under test**: `paper/main_nn.pdf` — **41 pages**, 2,719,824 bytes, pdfTeX-1.40.27, `CreationDate = Sun Sep 20 13:40:08 2026`, `Output written on main_nn.pdf (41 pages, 2719824 bytes)` (`paper/main_nn.log`).
**Checklist sources**: `docs/P1_REMEDIATION_LOG.md` (sections 一–七, mtime 2026-09-20 13:41:12) and `docs/P1_ADVERSARIAL_REVIEW.md` ([M1]–[M26]).
**Evidence rule applied**: every verdict below quotes the artefact (built PDF, embedded figure raster, or archived JSON). The remediation log's word was never accepted as evidence.

---

## 0. Provenance of the text I verified

`paper/_p1pdf.txt` is **faithful** to the built PDF — a fresh `pdftotext paper/main_nn.pdf -` dump is byte-identical after CRLF normalisation:

```
fresh_len=76903 old_len=76903
identical: True
```

(An earlier apparent mismatch was an encoding artefact of my own PowerShell read, not a stale dump. Note for future rounds: read `_p1pdf.txt` as UTF-8 explicitly, or `Get-Content -Raw` decodes it as CP936 and produces mojibake such as `鈥檛` for `’t`.)

All line numbers cited as `dump L<n>` refer to that dump (1,906 lines). `pdftotext` inserts one form-feed per page, so `page N` = the N-th form-feed block; this agrees with `pdfinfo` (41 pages) and with the LaTeX log.

---

## 1. Page count and build state (brief item 5, first half)

| Quantity | Claimed in the log | Actual | Verdict |
|---|---|---|---|
| Page count | **40 页** — §五 table (`编译 \| 40 页，0 error`) and §七 (`编译状态：40 页，0 error、0 undefined citation`) | **41** (`pdfinfo`: `Pages: 41`; log: `Output written on main_nn.pdf (41 pages, 2719824 bytes)`) | **FAIL (stale)** |
| undefined references | "唯一警告 = 待 Patch B 补的 `sec:strictcontrol` 引用" / "唯一待办 = Patch B 的 `sec:strictcontrol` 标签" | **None.** Grouped warnings from `main_nn.log` contain no `undefined`, no `multiply defined`, and no `LaTeX Warning` other than 10× `hyperref Token not allowed in a PDF string`; the remainder are 15 over/underfull hboxes | **FAIL (stale)** — Patch B **has landed** |

**Patch B landed, and the log does not know it.** `paper/sections/strict_control.tex` was created 2026-09-20 13:40:03, the PDF was built 13:40:08, and the built PDF contains the section and its table:

> PDF p21: **`5. Strict-Freeze Control: The Adapter-Only Manipulation`** … "With only the adapters trainable the vision encoder of the text-only configuration receives no updates: 0 of 199 vision-side backbone tensors change"

> PDF p21, **`Table 8: Strict-freeze control on Flickr30k …`** … `Text-only | 5 | 196,608 | −0.047 ± 0.003 | 0.624 | 0/199`

The log was last written (13:41:12) **after** the final compile (13:40:08), yet §六 item 1 still lists Patch B as outstanding ("**Patch B（等实验）**… 当前编译只剩这一条 undefined reference") and §六 item 4 as "needs redoing after Patch B". Both are now stale. This is the *safe* direction of error (the log understates completion), but a reviewer relying on the log would mis-describe the artefact.

**The strict-control numbers are backed by real artefacts — no fabrication.** `outputs/analysis/strict_control_summary.json` (2026-09-20 13:39:21) holds:

```json
"text_only": { "n_seeds": 5, "n_trainable_params": 196608,
  "cg_delta_mean": -0.0465049147605896, "cg_delta_std": 0.0026959439833470354,
  "r1_mean": 0.6238000094890594, "vision_nonzero_tensors": [0], "vision_tensors": 199,
  "vision_rank_delta_mean": 0.0, "text_rank_delta_mean": 0.4611843327681221 }
```

Every Table 8 cell traces: `196,608` ✓; `−0.04650… → −0.047` ✓; `0.00270 → ±0.003` ✓; `0.62380 → 0.624` ✓; `0/199` ✓. The five per-seed runs exist under `outputs/strict_freeze/text_only/seed{42,123,456,789,1024}/results.json`, all with `n_trainable_params = 196608`, plus `outputs/strict_freeze/frozen/results.json`. The claim "the layer-wise effective rank of the vision encoder is identical before and after training" matches `vision_rank_delta_mean: 0.0`, and "the text-side rank moves" matches `text_rank_delta_mean: 0.461`. **PASS.**

---

## 2. Superseded-value sweep of the built PDF (brief item 3)

Searches were run both line-by-line (for tokens) and on whitespace-flattened text (for cross-line phrases).

| Superseded item (from round 1) | Hits in built PDF | Survivor analysis | Verdict |
|---|---|---|---|
| `-0.827` | **1** | dump L506 / PDF p15: "An earlier version of this analysis reported r = −0.827 for DG over an n = 81 subset; the selection rule for that subset was lost with the original script and cannot be reconstructed, so the values below supersede it." — **deliberate superseded-value disclosure** (log §二 requires exactly this) | PASS |
| `-0.807` | **0** | — | PASS |
| `0.683` (as a correlation) | **1** | dump L1048 — sits inside a stream of R@1 values in the Table 10 catalogue (`… 0.686, 0.687, **0.683**, 0.669, 0.699 …`, PDF p32), not a correlation. The correlation triple 0.827/0.683/0.807 is gone | PASS (benign residue) |
| `0.012` with `p = 0.915` | `0.915` = **0**; `0.012` = 3 | The three `+0.012` are CG∆ values: rank-64 Adapter ablation (dump L86, L235) and its Table 10 row (L997). No `p = 0.915` anywhere | PASS |
| `81 experiments` | **0** | — | PASS |
| `n = 81` | **1** | Only inside the same superseded-value disclosure as `-0.827` above | PASS |
| `zero vision-side updates` | **0** | — | PASS |
| `non-triviality` (of our metrics) | **0** for the phrase; 2 for the token | Survivors are the *section headings* `4.11. DG Metric Non-Triviality` (p20) and `E. Gap Metrics Non-Triviality Checks` (p34) — legitimate titles, and the flagged phrase "non-triviality of our metrics" is absent | PASS |
| `DG is not a redundant proxy` | **0** | Replaced by the honest inversion: p10 "…partialling out CG leaves DG at r = −0.581, so we do not claim that DG carries information that CG misses" | PASS |
| `116 experiments` | **0** (`\b116\b` = 0) | `117` appears 11×; partition `XIII. Zero-Shot Generalization and SigLIP — **8 experiments**` (was "7", the round-1 [M14] defect) | PASS |
| `first systematic study` | **0** | Abstract now: "we conduct **a systematic study** of modality gap evolution during fine-tuning" | PASS |
| `24%` (old gap increase) | **0** | Now `23.3% ± 0.9% over five seeds` (abstract p1; intro L66) | PASS |
| `-0.100` as Adapter mean | **2** | Both on p15, both inside the **withdrawal paragraph**: "…reported a one-way ANOVA in favour of Adapter (F = 13.37, p = 5 × 10⁻⁴, Adapter mean CG∆ = −0.100). That comparison mixed baselines… Recomputed against a common frozen baseline … the Adapter group mean is +0.229 rather than −0.100, no Adapter configuration reduces the gap, and the earlier conclusion does not hold." Deliberate | PASS |
| Adapter `-0.046` / `-0.040` as gap reductions | `−0.046` ×6, `−0.040` ×2 | **Mixed.** `−0.046` is now predominantly a *text-only LoRA* value (p12 §4.3: "Five-seed validation of text-only on Flickr30k: CG∆ = −0.046 ± 0.002"; p15: "text-only LoRA (−0.046, R@1≈0.62)"). **But Table 2 (p13) still shows the Adapter column as `Text-only −0.046 / Both −0.040 / Vision-only −0.083`** — the Adapter's own post-injection baseline — under the caption "Effect of LoRA position on CG∆. Bold = best." with no on-table baseline note. See finding **S-1** | **FAIL (see S-1)** |

**No unexpected survivor was found.** The only survivors of the old numbers are the two values the log deliberately retains as superseded disclosures (`−0.827 / n = 81`, `F = 13.37 / −0.100`), and both are explicitly framed as withdrawn. `F = 13.37` is **confirmed intentional**: p15 states "…the earlier conclusion does not hold."

Also checked and clean: `p = 0.713` = 0; `0.234` = 0; `−0.042` = 0; `2501.00984` = 0; `p < 0.01` = 0 (conclusion now uses `p < 0.001`, resolving the round-1 [M12] p-value mismatch).

---

## 3. Full checklist — every fix the log claims

### 3.1 Log §二 — Patch A / A2 / A3 ("42 处替换")

| # | Claimed | Evidence in the built PDF | Verdict |
|---|---|---|---|
| 1 | **116 → 117**, 9 places, plus partition XIII "7 experiments" → 8 | `\b116\b` = 0; `117` = 11×; partition table p32: `XIII. Zero-Shot Generalization and SigLIP — 8 experiments` | **PASS** |
| 2 | "first systematic study" de-flagged in abstract / intro / conclusion → "a systematic study" | 0× phrase; abstract p1 "we conduct **a systematic study** of modality gap evolution during fine-tuning"; conclusion p29 "We conducted **a systematic study** of modality gap evolution…" | **PASS** |
| 3 | 24% → 23.3% (5-seed basis) | 0× `24%`; abstract p1 "increases the Centroid Gap by **23.3% ± 0.9% over five seeds**"; intro L66 "CG by +0.191 ± 0.008 on Flickr30k (**23.3% of the frozen value**, five seeds…)" | **PASS** |
| 4 | Adapter common baseline: Table 4 row, RQ4, ANOVA, intro ×2 — text-only **+0.237**, both **+0.500**, group mean **+0.229**, "not one configuration lowers the gap"; revoke the `F = 13.37` conclusion | Table 4, p15: `LoRA −0.004 \| 0.669 \| r=8, α=64, text-only` / `Adapter +0.229 \| 0.173 \| d=64, text-only (+0.064, R@1 0.574)` / `Full FT +0.191 \| 0.597 \| N/A`; §4.5 p14 "+0.237 vs. +0.500, measured against the frozen baseline"; "Measured against the frozen model, **no Adapter configuration reduces the gap**"; p15 withdrawal paragraph | **PASS** |
| 5 | DG/CG correlations → reproducible **n = 204** rule (−0.714 / −0.594 / partial −0.581 / DG↔CG +0.945 / DG∆ +0.134 p=0.055 / CG∆ +0.190 p=0.007) + disclose that the n=81 subset is unreconstructable and superseded; delete "DG significantly better than CG" and "partial −0.807 proves incremental value" | **Table 5, p16** reads exactly: `DG (final) → R@1 −0.714 <0.001` / `CG (final) → R@1 −0.594 <0.001` / `DG → R@1 (partial, controlling CG) −0.581 <0.001` / `DG ↔ CG +0.945 <0.001` / `DG ∆ → R@1 +0.134 0.055 (NS)` / `CG ∆ → R@1 +0.190 0.007`. n=81 disclosure p15 (quoted in §2). Inversion stated: p20 "we therefore treat them as interchangeable rather than as evidence that DG is an independent predictor" | **PASS** |
| 6 | **fig1** redrawn as a single dataset (Flickr30k + frozen reference + 5-seed band); caption states the data source | `paper/figures/fig1.png` (2051×1151, mtime 2026-09-20 12:41) = printed **Figure 1**, PDF p11. Raster shows legend `Full FT / Text-only / Both / Frozen / Text-only, 5-seed mean ± s.d.`, `Frozen` flat at 0.818. Caption: "**all series are Flickr30k runs** (batch 128, 10 epochs, 5,000 samples…)". The round-1 [M3] COCO/Flickr mix is gone (the old COCO Full-FT series ran 1.0531→1.2470; this one ends ≈1.02 = 0.818+0.20, the Flickr full-FT value) | **PASS** (but the monotonicity clause is wrong — finding **S-2**) |
| 7 | **fig2** redrawn to the reproducible rule (n=204, r=−0.714/−0.594); caption synced | `fig2.png` (2370×1019, mtime 12:39) = printed **Figure 4**, PDF p16. Raster panel titles read `r = -0.714  n = 204` and `r = -0.594  n = 204`. Caption: "…over the reproducible archive of n = 204 runs. DG correlates with R@1 at r = −0.714 and CG at r = −0.594…". The old hard-coded `n = 81` title over a 17-point scatter (round-1 [M4]) is gone | **PASS** |
| 8 | **fig3** Adapter bars → common baseline **+0.237 / +0.500**, with the note "Positive = gap enlarged relative to the frozen model" | `fig3.png` (2844×1348, mtime 12:39) = printed **Figure 2**, PDF p13. Raster shows bars `+0.237` (Text-only, Adapter) and `+0.500` (Both modalities, Adapter) and the red annotation `Positive = gap enlarged relative to the frozen model` | **PASS** |
| 9 | **fig5** redrawn; e2 relabelled from "Both-LoRA (α=4)" to "Text-only (r=8, α=4)"; caption synced | `fig5.png` (1841×941, mtime 12:41) = printed **Figure 5**, PDF p18. Raster legend reads exactly `Both (r=8, α=16)`, `Text-only (r=8, α=4)`, `Text-only (r=8, α=16)`. Round-1 [M6] resolved | **PASS** |
| 10 | **口径披露**: `methodology.tex` gains a "Disclosure of the fine-tuning convention" paragraph (historical LoRA runs froze only the replaced Linear layers; embedding/LayerNorm stayed trainable; records 145,170,177 trainable parameters) and points to the new strict-control section | PDF p9, §3.3: "**Disclosure of the fine-tuning convention.** The LoRA runs in the main catalog adapt the attention projections (q_proj, v_proj) of the selected encoder. In those runs the optimizer was constructed from every parameter with requires_grad set, and the PEFT library froze only the weights of the linear layers it replaced; the embedding and LayerNorm parameters of both encoders therefore remained trainable, and the archived runs record **145,170,177 trainable parameters** for the CLIP ViT-B/32 text-only configuration. … **Section 5 reports a control experiment in which every non-adapter parameter is frozen**" | **PASS** |
| 11 | Frozen R@1 added to the intro's Text+Vis-L1 sentence (R@1 = 0.617) | dump L95: "**(R@1=0.617, CG 0.814, same protocol)**" | **PASS** |
| 12 | **yi2025 措辞**: "proved that dimension collapse is the root cause" → "attributes the modality gap to dimension collapse" | Landed in 2 places — p5 (intro) "The work of [4] **attributes the modality gap to dimension collapse**"; p22 (§6.1) "Dimensional collapse asymmetry. [4] **attributes the modality gap to dimension collapse**." **But two sites still carry the original assertion** (see **M-1**) | **FAIL (partial)** |

### 3.2 Log §三 — citation repairs

| # | Claimed | Evidence in the built PDF bibliography | Verdict |
|---|---|---|---|
| 13 | Two arXiv IDs swapped back (`xu2026vlreasoning` ↔ `morelli2026sparse`) | p41: "**[34] Y. Xu, …** Do vision-language models truly perform vision reasoning? A rigorous study of the modality gap in reasoning, arXiv preprint **arXiv:2604.16256**"; "**[35] F. Morelli, …** Sparse autoencoders enable robust and interpretable fine-tuning of CLIP models, arXiv preprint **arXiv:2605.15961**". Each paper now carries its own ID | **PASS** |
| 14 | `gao2026uniformity` DOI `2501.00984` → `2602.09507` | p41: "[36] W. Yin, … Towards uniformity and alignment for multimodal representation learning, ICML, 2026. **doi:10.48550/arXiv.2602.09507**"; `2501.00984` = 0 hits | **PASS** |
| 15 | `niss2025reviving` year 2025 → 2026 | p40: "[24] L. Niss, … arXiv preprint arXiv:2605.11659 (**2026**)" | **PASS** |
| 16 | `yi2025decipher` gains the ICML 2026 formal-version title note | p39: "[4] … arXiv preprint arXiv:2510.03268 **The Convergent Representation of Contrastive Vision-Language Models: Geometry, Modality Gap and Shared Space Alignment (ICML 2026 version)** (2025)" | **PASS** |
| 17 | (explicitly still open) add Huang et al., *Mind the Gap…*, ICCV 2025 | **Absent.** `Mind the Gap` = 0, `11444362` = 0; the only `Huang` in the PDF is a co-author of reference [15] (p41). The log honestly records this as pending ("**仍未做（需 VPN 关闭后手动一次）**… 不得凭猜写作者") | **FAIL (open, correctly declared)** — see **M-3** |

### 3.3 Log §五 — patch A5–A7 and the PDF-level recheck

| # | Claimed | Evidence | Verdict |
|---|---|---|---|
| 18 | A5: Table 4 column is "Mean CG∆" so the Adapter row must be the **group mean +0.229** (R@1 0.173) with the best configuration in the right column; full-FT row becomes the 5-seed mean **+0.191** (R@1 0.597); caption gains `n` | Table 4 p15 + caption "…Adapter **n = 7** runs; full fine-tuning **n = 5** seeds; the LoRA row is the mean over the LoRA catalog. **The right-hand column names the best configuration of each group rather than its mean.**" with right column `d=64, text-only (+0.064, R@1 0.574)` | **PASS** |
| 19 | A6/A7 lesson: after recompiling, `0.827` / `0.807` / `81 experiments` in `methodology.tex`, `discussion.tex`, `supplementary.tex` are cleared in the **product** | Confirmed at product level — see §2. Only the deliberate disclosures survive | **PASS** |
| 20 | `0.012, p = 0.915`, "non-triviality of our metrics", "DG is not a redundant proxy" → 0 | All 0 — see §2 | **PASS** |
| 21 | `24\%` and `-0.100` → 0 | `24%` = 0. `−0.100` survives 2× but only inside the explicit withdrawal paragraph (p15) | **PASS** |
| 22 | `F = 13.37` deliberately retained, with the new ANOVA paragraph stating the old conclusion does not hold | Confirmed — p15 withdrawal paragraph | **PASS** |
| 23 | `0.199` retained for single-run contexts, annotated as single-run vs 5-seed | p12 "…Full fine-tuning is catastrophic across all datasets, increasing CG by +0.191 ± 0.008 over five seeds on Flickr (**the single archived run gives +0.199**)"; Table 11 p35 lists `+0.199` per seed | **PASS** |
| 24 | `paper/cover_letter_revision.tex` — 3 pages, compiles, contains the companion disclosure + a proactive corrections table | `cover_letter_revision.tex` (6,345 B, 12:43:19) → `cover_letter_revision.pdf` (103,773 B, 12:43:23), `pdfinfo` = **`Pages: 3`**. Contains "**Companion work (disclosure).** … a companion manuscript by the same author … previously submitted to *Pattern Recognition Letters* and has been revised and submitted to *Neurocomputing* (manuscript NEUCOM-D-26-20952)" and a 7-row corrections table (training convention / Adapter comparison / gap–retrieval correlation / full fine-tuning / experiment count / figures / effective rank) | **PASS** (one cross-reference defect — finding **S-5**) |

### 3.4 Log §七 — patch A8 / A9, highlights, figure–artefact check

| # | Claimed | Evidence | Verdict |
|---|---|---|---|
| 25 | A8: supplementary footnote c rank definition changed from "threshold 0.99 explained variance" to `exp(−Σ pᵢ log pᵢ)`, matching the tracking code, and stating legacy runs reduce it while the strict control does not | PDF p34 footnote c: "**Effective rank of layer-wise image embeddings, exp(−Σ pᵢ log pᵢ) with pᵢ the normalised singular values of the mean-pooled token representations (the definition used by the tracking code); the legacy text-only runs reduce it, while the strict control leaves it exactly unchanged (Section 5).**" | **PASS** |
| 26 | A9: Connector-S cited to the IJCAI 2025 formal version, DOI 10.24963/ijcai.2025/1202 | p41: "[39] X. Zhu, … Connector-S: A survey of connectors in multimodal large language models, in: Proceedings of the Thirty-Fourth International Joint Conference on Artificial Intelligence (**IJCAI**), 2025. **doi:10.24963/ijcai.2025/1202**" | **PASS** |
| 27 | A9: GTMA gains the IEEE Xplore doc note; journal name not guessed | p40: "[28] J. Zhang, … GTMA: Dynamic representation optimization for out-of-distribution vision-language models, arXiv preprint arXiv:2512.18504 **Published version: IEEE Xplore, document 11463397 (title: GTMA: Dynamic Representation Optimization for OOD VLMs)** (2025)" | **PASS** |
| 28 | A9: `zhu2026fi` (an LLM-fragility paper) reframed in `related_work.tex:20` and `visual_fragility.tex:12` as an LLM-setting result we *conjecture* transfers | p7 related work: "[32] identified, **in the LLM setting**, that a small subset of parameters disproportionately contributes to model brittleness—**a mechanism we conjecture transfers to vision encoders**"; p22 §6.1: "…contributing disproportionately to brittleness **in the LLM setting**…, **which we conjecture transfers to vision encoders**" | **PASS** |
| 29 | A9: `visual_fragility.tex:8` "proved" → "attributes" | Present (p22 §6.1) — but two sibling sites were missed: **M-1** | **PASS (for the named site only)** |
| 30 | `highlights.tex` rewritten — all 5 old bullets contained superseded claims (first / 116 / r=−0.827 / partial −0.807 / causal evidence); new bullets render 78–85 chars incl. bullet, within Elsevier's ≤85 | `paper/highlights.tex` now: `117 PEFT experiments trace modality-gap evolution across three model families` / `Text-only adaptation preserves cross-modal alignment better than joint adaptation` / `Full fine-tuning raises the gap by 23.3\% over five seeds and collapses zero-shot` / `Gap magnitude predicts retrieval; Centroid and Distribution Gap are interchangeable` / `A strict control shows text-only adapters leave the visual encoder untouched`. Measured body lengths 77, 81, **81**, **83**, 76 → +2 for the bullet glyph = **78–85** ✓; `116`, `0.827`, `0.807` and "causal evidence" are all absent. `highlights.pdf` (24,867 B, 12:46:35) post-dates `highlights.tex` (12:46:30) | **PASS (5/5)** |
| 31 | Figure–artefact check: `pdfimages -list` vs source PNG dimensions — fig1/fig2/fig3/fig5/fig7 all embedded in the recompiled PDF at 2051×1151 / 2370×1019 / 2844×1348 / 1841×941 / 1691×1027 | Independently reproduced **exactly**: `pdfimages -list` gives p11 `2051×1151`, p13 `2844×1348`, p14 `3143×1402`, p16 `2370×1019`, p18 `1841×941`, p20 `1586×1076`, p20 `1691×1027`; the PNG files on disk match one-for-one (fig1 2051×1151, fig2 2370×1019, fig3 2844×1348, fig5 1841×941, fig7 1691×1027, fig4 3143×1402, fig6 1586×1076). Four of the five regenerated rasters carry 2026-09-20 12:39–12:42 mtimes | **PASS** |
| 32 | Compile status "40 pages, 0 error, only `sec:strictcontrol` outstanding" | **41 pages; the reference is resolved** — §1 | **FAIL (stale)** |
| 33 | New tool `tools/p1_strict_control_summary.py` produces the strict-control summary (idempotent) | Exists (6,519 B, 12:46:46); its output `outputs/analysis/strict_control_summary.json` reproduces every Table 8 cell — §1 | **PASS** |

### 3.5 Log §四 — rejected agent conclusions, re-tested

| # | Claimed | My independent test | Verdict |
|---|---|---|---|
| 34 | [M5]/[F13] "Figures 2 and 3 are swapped" is a **false positive**: the `\includegraphics` are `fig3.png` under the "Cross-validation" caption and **`fig4.png`** under the "Ablation" caption; `fig3.png` genuinely *is* the cross-validation bar chart. The round-1 agent mis-recorded fig4 as fig2 | **Confirmed by direct inspection of the rasters.** `fig3.png` renders a bar chart titled "Text-only overwhelmingly preserves cross-modal alignment" with bars −0.064/−0.032, −0.041/−0.052, **+0.237/+0.500**, +0.047/+0.152, −0.036/+0.128 over categories CLIP Flickr / CLIP COCO / Adapter / BLIP-1 / ViT-L → matches its "Cross-validation" caption. `fig4.png` renders three panels "Rank effect / Alpha effect / Module effect" → matches its "Ablation of LoRA scaling factor α…" caption. Source order `fig3.png` (experiments.tex:92) before `fig4.png` (:103) is preserved in the output: figures are numbered 1–7 in strictly ascending page order (p11, p13, p14, p16, p18, p20, p20), so no float drift occurred | **PASS — the log's rebuttal is correct** |
| 35 | "ap3 的 refs.bib 也有互换的 ID" is a false positive | Out of scope (I verified `paper/` only) | **not tested** |
| 36 | "Abstract 59.3% vs Table 7 59.28% is rounding, not a defect" | Table 7 p19: `Frozen 59.28%`, `Text-only 58.66%`, `Both 59.67%`; abstract p1: "vs. **59.3%** frozen". Also matches `outputs/imagenet1k_zs_50k_plain.json`: `"frozen": 59.28, "text_only_r8": 58.66, "both_r8": 59.67` with `"n_images": 50000` | **PASS — not a defect** |
| 37 | [M16] Table 7 uses the **50k full validation set + 3 retrained seeds** protocol, whereas the 08-14 correction letter describes a 14,288 subset — two distinct protocols, and the manuscript is internally self-consistent, so the manuscript needs no change | Table 7 caption p19: "Top-1 evaluated with the single-template protocol … on the **full 50,000-image ImageNet validation set**; CG∆ for text-only/both from the original training logs, for full fine-tuning the **mean over 3 retrained seeds (original checkpoint not saved)**". Backed by `imagenet1k_zs_50k_plain.json` (`n_images: 50000`); the three retrained seeds reproduce exactly: full-FT CG∆ `0.6646 / 0.2609 / 0.2672` → mean **0.3976 ≈ Table 7's `+0.40`**; Top-1 `0.13 / 4.09 / 3.54` → mean **2.587 ≈ Table 7's `2.6%`**, range **0.13–4.09 ≈ p19's "range 0.1–4.1% across 3 retrained seeds"** | **PASS — the coordinator's reading holds, and the new range is numerically correct** |

---

## 4. Figure / caption pairing audit (brief item 4)

LaTeX renumbers figures by placement order. Extracted from the built PDF (`Figure N:` captions with page + the image on that page):

| Printed | Page | `\includegraphics` file | Source line | Caption (verbatim head) | Image actually is | Match |
|---|---|---|---|---|---|---|
| Figure 1 | 11 | `figures/fig1.png` | `experiments.tex:10` | "Modality gap evolution during PEFT; all series are Flickr30k runs…" | Flickr-only evolution curves + Frozen line + 5-seed band | ✓ |
| **Figure 2** | 13 | `figures/fig3.png` | `experiments.tex:92` | "**Cross-validation**: text-only yields the smallest alignment degradation…" | Cross-validation bars incl. Adapter +0.237/+0.500 | ✓ |
| **Figure 3** | 14 | `figures/fig4.png` | `experiments.tex:103` | "**Ablation of LoRA scaling factor α (left) and target modules (right)**…" | Ablation: Rank / Alpha / Module panels | ✗ **positional mis-description** — see **S-3** |
| **Figure 4** | 16 | `figures/fig2.png` | `experiments.tex:153` | "Distribution Gap vs. Centroid Gap … reproducible archive of **n = 204** runs…" | Two scatters, `r = -0.714 n = 204` / `r = -0.594 n = 204` | ✓ |
| Figure 5 | 18 | `figures/fig5.png` | `experiments.tex:186` | "DG evolution during the Route E DG-ES proof-of-concept…" | DG-ES curves; legend `Both (r=8, α=16)` / `Text-only (r=8, α=4)` / `Text-only (r=8, α=16)` | ✓ |
| Figure 6 | 20 | `figures/fig6.png` | `experiments.tex:237` | "ImageNet zero-shot: text-only preserves 58.66% …" | zero-shot bars | ✓ |
| **Figure 7** | 20 | `figures/fig7.png` | `experiments.tex:248` | "Gap–retrieval correlations over the reproducible archive (n = 204)…" | 3 bars: **0.714 / 0.594 / 0.581**, `DG ↔ CG: r = +0.945` | ✓ |
| Figures 8–14 | 36–38 | `fig8_weight_svd` … `fig14_adapter_layered` | `supplementary.tex:260–306` | as listed | ✓ (fig11 content defect — **M-2**) | ✓ except M-2 |

**Two consequences the parent agent must note:**

1. **The brief's assumed numbering does not hold.** The brief asks about "figure 2 (DG/CG scatter, n=204)" and "figure 3 (cross-validation bars with Adapter +0.237/+0.500)". In the built PDF the DG/CG scatter is **Figure 4** and the cross-validation bars are **Figure 2**; printed **Figure 3** is the ablation chart. The four figures the brief names by content all exist with the right content and the right captions — they are simply numbered 1, 2, 4, 5, 7 rather than 1, 2, 3, 5, 7. Every printed caption **does** describe the image it is attached to (except the Figure 3 positional clause, S-3). No figure is swapped.
2. **Nothing in the manuscript body cites Figures 2–6 by number** — the only in-text figure references in the whole PDF are "Figure 7 summarises the comparison" (p20), "Figure 8 presents a four-panel summary" (p35) and "Figures 9–14 present…" (p36). So the renumbering breaks no cross-reference *inside the manuscript*. It does, however, break the **cover letter** (S-5).

---

## 5. Warnings-list accuracy (brief item 5, second half)

| Warning | Source | Still accurate? |
|---|---|---|
| "唯一待办 = Patch B 的 `sec:strictcontrol` 标签" | log §六 item 1, §七 | **NO — stale.** Section 5 + Table 8 are in the PDF (p21) and there are **no** undefined references in `main_nn.log` |
| "编译 40 页" | log §五, §七 | **NO — stale.** 41 pages |
| "fig11（唯一剩的图）… 面板 B 标题算出 'Vis grads contribute <640%'… 且其 'Text-only matches Both' 与稿件自己的脚注矛盾。**重生成需跑该脚本 → 占 GPU，必须等严格冻结实验结束后串行执行**" | log §六 item 2 | **SUBSTANTIVELY ACCURATE, but the stated blocker has expired.** `paper/figures/fig11_gsnr.png` is unchanged (mtime **2026-07-17 18:50**) and the built PDF p37 still prints the impossible panel: "**B: Text-only matches Both (Vis grads contribute <640% to loss reduction)**", which also contradicts the paper's own p34 footnote b ("text-only converges to a **higher** final loss (4.15 vs. 0.56 for both-modality)"). Meanwhile `paper/scripts/gsnr_analysis.py` **was already fixed** (mtime 2026-09-20 12:50:49) — its panel-B title is now `"B: Text-only converges to a higher loss\n(4.15 vs. 0.56) yet preserves alignment"`. So the only remaining step is re-running the script to regenerate the PNG; the GPU serialisation it waited on ended when the strict-freeze run finished (13:38:49, `outputs/strict_freeze/run.log`). See **M-2** |
| "返修封面信草稿 ✅" | log §六 item 3 | **Accurate** — `cover_letter_revision.tex/.pdf`, 3 pages |
| "重编译 + PDF 级复核 ✅ … Patch B 后需再做一次" | log §六 item 4 | **Stale** — the recheck after Patch B is what this report does; the PDF already post-dates Patch B |
| "第二轮独立子代理复查（待全部改完）" | log §六 item 5 | This report |
| "ap3 侧（非本轮）" | log §六 item 6 | Not tested (out of scope) |
| "需 VPN 关闭后手动核：Huang ICCV 2025 作者列表、niss2025reviving 作者列表" | log §六 item 7 | **Accurate** — Huang et al. still uncited (**M-3**); `niss2025reviving`'s year is fixed but its author list remains unverified against the log's own note |

**Round-1 report warnings list (`P1_ADVERSARIAL_REVIEW.md` §7, 11 actions):** actions 2 (Table 7 protocol — now stated in the caption, verified in §3.5 #37), 3 (audit action ① training convention — done; see **M-4** for ②), 4 (n=81 → reproducible rule), 5 (figure fixes, except fig11), 6 (Adapter common baseline + Table 4 n + ANOVA withdrawal), 7 (116→117, p-value unification), 8 (23.3%), 9 (partial: citation IDs/DOI/year/ICML note/IJCAI/GTMA done; **Huang still missing**), 10 (cover letter disclosure — drafted) are addressed at product level. Actions 1 (mechanism — resolved via the strict-freeze control), and 11 (ap3 sync) are out of scope/partially. **The only round-1 §7 actions with no product-level landing are #9's Huang citation (M-3) and #5's fig11 (M-2).**

---

## 6. Findings

### MUST-FIX

**M-1 — The `yi2025decipher` over-claim the log says it softened survives verbatim in two places.**
The log (§二) claims: *"'proved that dimension collapse is the root cause' → 'attributes the modality gap to dimension collapse'"*, with the stated rationale that the claim could not be independently verified. The substitution landed in two sites (intro; §6.1) but **two others still assert it in the built PDF**:

> PDF **p6**, Related Work `2.1`: "Recent theoretical work has deepened our understanding: **[4] provided the first proof that dimension collapse is the fundamental origin of the modality gap.**"

> PDF **p24**, §`Theoretical inevitability of the gap`: "**[4] showed that dimension collapse is the root cause**, and that under subspace constraints, perfect alignment is impossible."

Source: `paper/sections/related_work.tex:6` and `paper/sections/discussion.tex:8`. [4] is `yi2025decipher` (`paper/references.bib:146`). Because the log's own justification for softening was that the claim is unverifiable, an unreconstructed assertion of **"the first proof"** of a theoretical result — while the same bibliography now labels that paper a preprint with an "(ICML 2026 version)" note — is exactly the kind of over-claim a reviewer can challenge. This is a further recurrence of the failure mode the brief warns about: a wording fix counted as applied that reached only some of its sites.

**M-2 — Figure 11 in the built PDF still shows the physically impossible panel, and the fix is one command away.**
> PDF p37, **Figure 11** (raster `paper/figures/fig11_gsnr.png`, unchanged since 2026-07-17): "**B: Text-only matches Both (Vis grads contribute <640% to loss reduction)**"

This is round-1 [M7] (must-fix), and it flatly contradicts the manuscript's own p34 footnote b ("text-only converges to a higher final loss (4.15 vs. 0.56 for both-modality)"). The log lists it as remaining work — so the *log* is honest — **but the artefact under review still contains it**, and the blocker the log names has since expired: `paper/scripts/gsnr_analysis.py:184-186` was already corrected on 2026-09-20 12:50:49 to `"B: Text-only converges to a higher loss\n(4.15 vs. 0.56) yet preserves alignment"`, and the strict-freeze GPU run that had to finish first completed at 13:38:49. Recommendation: re-run `gsnr_analysis.py`, then recompile — this should close round-1 [M7] outright. (If regeneration is impossible before the next compile, deleting the panel-B title text is strictly better than shipping "<640%".)

**M-3 — The pre-empting citation (Huang et al., ICCV 2025) is still absent.**
Round-1 [M22] ✚核 made this a must-cite: a paper studying gap preservation during CLIP adaptation pre-empts the (now softened) priority claim. In the built PDF `Mind the Gap` = 0 hits, `11444362` = 0 hits, and `Huang` occurs only as a co-author of reference [15]. The log declares this as pending on VPN access ("必须需 VPN 关闭后手动一次 … **不得凭猜写作者**"). That is the correct call on not inventing an author list, but the item is unresolved in the artefact. Note this is now lower-risk than at round 1, because "first systematic study" has been removed from the abstract, intro and conclusion — the priority claim it threatened no longer exists. The right residual action is to obtain the author list (or the IEEE/CVF record) and add the citation; if that is impossible, the item should be recorded as still open rather than closed, and no author list may be guessed.

**M-4 — The zero-shot evaluation provenance is still undisclosed (round-1 [M15] action ②).**
Round-1 [M15] ✚核 listed three audit actions; ① (disclose the training convention) is now done — verified on PDF p9. Action ② — "state that the zero-shot numbers come from a **reconstructed LoRA-only model** (`paper/scripts/zeroshot_extra.py:114-141` never loads a checkpoint)" — has **not** landed: the built PDF has **0** occurrences of `reconstruct` in this sense and **0** of `LoRA-only`. What the PDF does say is narrower: Table 7's caption (p19) discloses that the *full fine-tuning* row is "the mean over 3 retrained seeds (original checkpoint not saved)" and that text-only/both CG∆ come from "the original training logs" — it never states which model produced the Top-1 column. `paper/scripts/zeroshot_extra.py` is untouched (mtime 2026-08-13 20:56). The remediation log never claims this item, so this is an unclaimed round-1 must-fix rather than a false claim — but it remains a live transparency gap for a paper under review.

### SHOULD-FIX

**S-1 — Table 2 still presents the Adapter column as gap *reductions* under its own baseline, and the convention note points at the wrong table.**
> PDF p13, **Table 2: Effect of LoRA position on CG∆. Bold = best.** Columns `Flickr | COCO | Adapter | BLIP-1`; rows `Text-only −0.064 | −0.041 | **−0.046** | +0.047`, `Both −0.032 | −0.052 | **−0.040** | +0.152`, `Vision-only −0.003 | +0.031 | −0.083 | —`.

Those Adapter cells are the own-post-injection-baseline values (round-1 [M8]/[M9]), which the corrected analysis now contradicts:
> PDF p15, §4.5: "**Measured against the frozen model, no Adapter configuration reduces the gap**: the best (d=64) still ends at +0.064, and the worst at +0.500."
> PDF p15, Table 4: `Adapter | +0.229`.

The convention *is* disclosed, but three pages later and in a way that does not locate the reader's problem:
> PDF p14, §4.5: "We note that **the Adapter and LoRA columns** use different baselines in the published convention…"

No table in the manuscript has side-by-side "Adapter and LoRA columns" — Table 4 has method **rows**, and Table 2's columns are datasets. Fix: put the baseline caveat on Table 2 itself (or add a footnote marker to the three Adapter cells), and reword the §4.5 sentence to name the tables.

**S-2 — Figure 1's caption asserts a monotonicity the figure contradicts.**
> PDF p11, Figure 1 caption: "**Full fine-tuning enlarges the gap monotonically**, both-position LoRA ends slightly below the frozen value, and text-only stays closest to it."

In the regenerated raster the Full-FT series reads approximately 0.818 → 1.05 → 1.02 → 1.00 → 1.01 → 1.015 → 1.02: it peaks at checkpoint 1 and then **falls** to a minimum at checkpoint 3 before rising again. It is not monotone. This clause appears to be a leftover from the pre-rewrite caption (the round-1 [M3] text was replaced with the "all series are Flickr30k runs" version). Fix: replace "monotonically" with the shape the plot shows, e.g. "raises the gap sharply at the first checkpoint and stays well above the frozen value throughout".

**S-3 — Figure 3's caption mis-describes its own panels, and Table 3's caption is a copy of it.**
> PDF p14, Figure 3 caption: "Ablation of LoRA scaling factor α **(left)** and target modules **(right)**." — but the raster is a **three**-panel chart: `Rank effect` (left), `Alpha effect` (**middle**), `Module effect` (right). The rank panel is not mentioned and α's position is wrong.
> PDF p14, **Table 3** caption: "Ablation of LoRA scaling factor α (left) and target modules (right)." — identical opening text on a **table** whose columns are `α | CG∆ | R@1 | Modules | CG∆ | R@1`; "left"/"right" are meaningless for it.

Source: `paper/sections/experiments.tex:104` (figure) and `:110` (table) carry the same caption string. `fig4.png` predates the remediation round (2026-07-17), so this is pre-existing, but it is exactly the caption↔figure mismatch the brief asks about.

**S-4 — A supplementary footnote's CG∆ range is off by 0.01.**
> PDF p34 footnote note: "…the full-FT row reports means over 3 retrained seeds (**CG∆ range +0.26–+0.67**; Top-1 range 0.1–4.1%; original checkpoint not saved)."

The three archived retrained seeds give `cg_delta` = **0.6646** (`outputs/imagenet_zs_rerun/full_ft/centroid_gap.json`), **0.2609** (`…/full_ft_s123/…`) and **0.2672** (`…/full_ft_s999/…`). The upper bound rounds to **+0.66**, not +0.67 (round-1 [M14] flagged precisely this). The companion claims in the same sentence are correct: mean 0.3976 ↔ Table 7's `+0.40`; Top-1 0.13/4.09/3.54 ↔ `2.6%`, range `0.1–4.1%`.

**S-5 — The revision cover letter cites manuscript figures by the wrong numbers.**
> `paper/cover_letter_revision.tex:103-105`: "Figure 1 mixed COCO curves with a Flickr30k seed band; **Figure 2 carried an n=81 title over a 17–30 point scatter**; Figure 5 labelled a text-only run as 'Both-LoRA'; **Figure 7 showed the superseded correlation values**".

In the built manuscript the n=81→n=204 scatter is **Figure 4**, while **Figure 2** is the cross-validation bar chart. "Figure 1", "Figure 5" and "Figure 7" happen to match the manuscript. Since this letter is a draft flagged "DRAFT 2026-09-18 — to be finalised and dated when the decision arrives" (`:3`), the fix is cheap — but if sent as-is, an editor checking "Figure 2" will find a bar chart and conclude the author mis-describes their own paper. (Round-1 [M3]/[M5] themselves referred to this scatter as "fig2", i.e. by *file* name; that is the likely origin of the slip. The same file-vs-printed-number slip is what makes the brief's own item-4 numbering expectations miss.)

**S-6 — The conclusion still drops the named exceptions that the abstract, intro and §6 now list.**
> PDF p1 abstract: "…with a few exceptions (**e.g., COCO both-position, SigLIP both-position, Adapter vision-only and ViT-B all-layer text-only**)."
> PDF p22 §6: "…across LoRA, Adapter, BLIP-1, and ViT-L, with a few exceptions (**COCO both-position, SigLIP both-position, Adapter vision-only, and ViT-B all-layer text-only; Table 12**)…"
> PDF **p29** conclusion: "…text-only fine-tuning preserves cross-modal alignment **in most configurations**, while joint-modality fine-tuning and full fine-tuning systematically degrade it."

The conclusion's p-value mismatch flagged in round-1 [M12] **is** fixed (`p < 0.001`; `p < 0.01` = 0 hits) and the Adapter-robustness over-claim is gone, so [M12] is mostly closed — but the "例外清单三处统一" part is 3-of-4. Naming them once in the conclusion (or adding "e.g." + a pointer to Table 12) would finish it.

### NOTE

**N-1 — The log's build-status block no longer describes the artefact** (40 vs 41 pages; `sec:strictcontrol` listed as outstanding though it resolves). §1. Harmless in effect, but the log is the running record of *what was verified against the product*, so a stale snapshot weakens exactly the control that caught the earlier A6/A7 miss.

**N-2 — The supplementary catalogue still names a partition "XII. Causal Evidence — 3 experiments"** (PDF p34; and the Table 9 note on p32 reads "Superscript letters in **Causal Evidence** and Zero-Shot rows…"). The abstract's "direct causal evidence" claim has been correctly replaced by the strict-freeze control ("isolate its mechanism with a strict control in which only the adapters are trainable: the visual encoder then receives no updates at all"), so this is now only a legacy partition label. Renaming it (e.g. "Perturbation Analysis") would remove the last echo of the withdrawn causal framing.

**N-3 — `0.683` survives once, benignly.** dump L1048 lies inside the Table 10 R@1 column (`… 0.686, 0.687, 0.683, 0.669 …`, PDF p32), not in any correlation. The flagged correlation triple is gone. Similarly, the three surviving `+0.012` values are CG∆ ablations, not the old `r = +0.012, p = 0.915`.

**N-4 — Two retained old values are deliberate and correctly framed.** `F = 13.37` / `Adapter mean CG∆ = −0.100` (p15) and `r = −0.827` / `n = 81` (p15) appear only inside paragraphs that state the old conclusion "does not hold" and that "the values below supersede it". This is good practice — do **not** strip them on a later pass; they are the audit trail a reviewer would otherwise ask for.

**N-5 — Positive results worth recording.** Every one of the five regenerated figures is genuinely embedded in the built PDF at the exact dimensions the log claims; the strict-freeze control's five seeds, trainable-parameter count, tensor-level vision-update count, rank deltas and R@1 all trace to `outputs/analysis/strict_control_summary.json` and five per-seed `results.json`; `highlights.tex` is fully rewritten with no superseded number; the revision cover letter exists at 3 pages with a companion disclosure and a proactive 7-row corrections table. No fabricated number was found in this round.

---

## 7. Compact verdict table (claimed fix → where found → PASS/FAIL)

| # | Claimed fix (log ref) | Where I found it (file:line / PDF quote) | Verdict |
|---|---|---|---|
| 1 | 116 → 117 + partition XIII 7→8 (§二) | `117` on PDF p1, p3, p10, p12, p18, p23, p25, p29, p32 (×2), p34; partition `XIII … — 8 experiments` (PDF p34); `\b116\b`=0, `117`=11 | **PASS** |
| 2 | "first systematic study" → "a systematic study" ×3 (§二) | PDF p1 abstract; p5 intro; p29 conclusion; phrase = 0 hits | **PASS** |
| 3 | 24% → 23.3% (§二) | PDF p1 "23.3% ± 0.9% over five seeds"; L66 "23.3% of the frozen value, five seeds"; `24%`=0 | **PASS** |
| 4 | Adapter common baseline +0.237/+0.500, mean +0.229, no config reduces gap; revoke F=13.37 (§二) | PDF p14 §4.5; p15 Table 4 `Adapter +0.229 \| 0.173`; p15 withdrawal paragraph | **PASS** |
| 5 | DG/CG → n=204 (−0.714/−0.594/−0.581/+0.945/+0.134/+0.190) + n=81 disclosure (§二) | PDF p16 **Table 5** (all six rows verbatim); p15 n=81 disclosure; p20 "treat them as interchangeable" | **PASS** |
| 6 | fig1 redrawn, single dataset + frozen reference; caption states source (§二) | `figures/fig1.png` = printed Figure 1, PDF p11; caption "all series are Flickr30k runs" | **PASS** (monotonic clause → S-2) |
| 7 | fig2 redrawn, n=204, r=−0.714/−0.594; caption synced (§二) | `figures/fig2.png` = printed Figure 4, PDF p16; raster `r = -0.714 n = 204` | **PASS** |
| 8 | fig3 Adapter bars +0.237/+0.500 + "Positive = gap enlarged…" note (§二) | `figures/fig3.png` = printed Figure 2, PDF p13; raster shows both bars and the note | **PASS** |
| 9 | fig5 relabel e2 → "Text-only (r=8, α=4)" (§二) | `figures/fig5.png` = printed Figure 5, PDF p18; legend has all three labels | **PASS** |
| 10 | `methodology.tex` "Disclosure of the fine-tuning convention" (§二) | PDF p9 §3.3 verbatim, incl. `145,170,177` and the pointer to Section 5 | **PASS** |
| 11 | intro Text+Vis-L1 gains frozen R@1=0.617 (§二) | dump L95 "(R@1=0.617, CG 0.814, same protocol)" | **PASS** |
| 12 | yi2025 wording "proved"/"root cause" → "attributes" (§二, §七) | Landed: PDF p5 intro, p22 §6.1. **Survives: PDF p6 "provided the first proof that dimension collapse is the fundamental origin"; p24 "showed that dimension collapse is the root cause"** | **FAIL** → M-1 |
| 13 | arXiv ID swap fixed (§三) | PDF p41 [34] Xu → `2604.16256`; [35] Morelli → `2605.15961` | **PASS** |
| 14 | `gao2026uniformity` DOI → 2602.09507 (§三) | PDF p41 [36] `doi:10.48550/arXiv.2602.09507`; `2501.00984`=0 | **PASS** |
| 15 | `niss2025reviving` 2025 → 2026 (§三) | PDF p40 [24] "arXiv:2605.11659 (2026)" | **PASS** |
| 16 | `yi2025decipher` ICML 2026 note (§三) | PDF p39 [4] "(ICML 2026 version)" | **PASS** |
| 17 | Add Huang et al. ICCV 2025 (§三, declared still open) | **Absent** — `Mind the Gap`=0, `11444362`=0; `Huang` only as co-author of [15] | **FAIL (open)** → M-3 |
| 18 | A5: Table 4 mean +0.229 / R@1 0.173, best config right, full-FT +0.191 / 0.597, caption n (§五) | PDF p15 Table 4 + caption "Adapter n = 7 runs; full fine-tuning n = 5 seeds…" | **PASS** |
| 19 | A6/A7: post-compile sweep clears 0.827/0.807/81 experiments in the product (§五) | §2 of this report — only the intended disclosures survive | **PASS** |
| 20 | `0.012, p=0.915` / "non-triviality of our metrics" / "DG is not a redundant proxy" → 0 (§五) | `0.915`=0, phrase=0, `DG is not a redundant proxy`=0 | **PASS** |
| 21 | `24\%` / `-0.100` → 0 (§五) | `24%`=0; `−0.100` survives only inside the p15 withdrawal paragraph | **PASS** |
| 22 | `F = 13.37` deliberately retained as superseded (§五) | PDF p15 "…the earlier conclusion does not hold" | **PASS** |
| 23 | `0.199` retained for single-run contexts (§五) | PDF p12 "(the single archived run gives +0.199)"; Table 11 p35 per-seed | **PASS** |
| 24 | `cover_letter_revision.tex` 3 pp, companion disclosure + corrections table (§五) | `cover_letter_revision.pdf` `Pages: 3`; disclosure at `.tex:51-61`; 7-row table at `:67-116` | **PASS** (numbering → S-5) |
| 25 | A8: footnote c rank definition `exp(−Σ pᵢ log pᵢ)` + "legacy reduces / strict control unchanged" | PDF p34 footnote c verbatim | **PASS** |
| 26 | A9: Connector-S IJCAI 2025 DOI 10.24963/ijcai.2025/1202 | PDF p41 [39] verbatim | **PASS** |
| 27 | A9: GTMA `IEEE Xplore, document 11463397` note, journal not guessed | PDF p40 [28] "Published version: IEEE Xplore, document 11463397 (title: …OOD VLMs)" | **PASS** |
| 28 | A9: `zhu2026fi` reframed as LLM-setting + conjecture | PDF p7 related work; p22 §6.1 — both carry "in the LLM setting"/"we conjecture transfers" | **PASS** |
| 29 | A9: `visual_fragility.tex:8` "proved" → "attributes" | PDF p22 §6.1 "…attributes the modality gap to dimension collapse." (sibling sites missed → M-1) | **PASS** (named site) |
| 30 | `highlights.tex` rewritten, 5 bullets, 78–85 chars | `paper/highlights.tex:8-12`, measured 78–85 incl. bullet; no superseded values | **PASS** |
| 31 | fig1/2/3/5/7 embedded at claimed dimensions (§七) | `pdfimages -list`: p11 2051×1151, p16 2370×1019, p13 2844×1348, p18 1841×941, p20 1691×1027 — exact | **PASS** |
| 32 | Compile status 40 pp, 0 error, only `sec:strictcontrol` outstanding (§五/§七) | **41 pages**; no undefined refs in `main_nn.log` | **FAIL (stale)** → N-1 |
| 33 | `tools/p1_strict_control_summary.py` + strict-control table (§七) | tool exists; `outputs/analysis/strict_control_summary.json` reproduces every Table 8 cell | **PASS** |
| 34 | [M5] "figures 2 and 3 swapped" = false positive; fig3.png↔Cross-validation, fig4.png↔Ablation (§四) | Rasters inspected: `fig3.png` = cross-validation bars; `fig4.png` = Rank/Alpha/Module ablation; numbering 1–7 in ascending page order | **PASS** |
| 35 | "ap3 refs.bib also swapped" = false positive (§四) | out of scope (paper/ only) | **not tested** |
| 36 | "59.3% vs 59.28% is rounding" (§四) | PDF p19 Table 7 `59.28%`/`58.66%`/`59.67%`; abstract `59.3%`; JSON identical | **PASS** |
| 37 | [M16] Table 7 = 50k + 3 seeds, distinct from the 14,288-subset letter; manuscript self-consistent (§四) | PDF p19 caption "full 50,000-image … mean over 3 retrained seeds"; seeds reproduce mean 0.3976↔`+0.40`, Top-1 2.587↔`2.6%` | **PASS** |
| 38 | §六 "fig11 still broken" warning | **Accurate** — PDF p37 raster still prints "Vis grads contribute <640%"; but blocker expired → M-2 | **PASS as a warning** (defect open) |

---

## 8. Counts

| Severity | Count | Items |
|---|---|---|
| **must-fix** | **4** | M-1 yi2025 over-claim survives in 2 PDF sites; M-2 Figure 11 "<640%" panel still in the built PDF (script fixed, raster not regenerated; blocker expired); M-3 Huang ICCV 2025 citation still missing; M-4 zero-shot reconstruction provenance still undisclosed (round-1 [M15] ②, unclaimed by the log) |
| **should-fix** | **6** | S-1 Table 2 Adapter own-baseline cells + misdirected convention note; S-2 Figure 1 "monotonically"; S-3 Figure 3 / Table 3 caption mis-describes panels (and is duplicated); S-4 footnote range "+0.26–+0.67" should be +0.66; S-5 cover letter cites figure numbers that moved; S-6 conclusion still omits the named exceptions |
| **note** | **5** | N-1 log build-status stale (40 vs 41 pp; Patch B status); N-2 "XII. Causal Evidence" partition name retained; N-3 `0.683` benign R@1 residue; N-4 `F=13.37`/`−0.100`/`−0.827`/`n=81` are intentional audit-trail disclosures — keep; N-5 positive verification of figures, strict-control numbers, highlights, cover letter |
| **claimed fixes verified PASS** | **31 of 34 testable claims** | (items 1–11, 13–16, 18–31, 33–34, 36–38 above) |
| **claimed fixes FAIL** | **3** | #12 (yi2025 wording) → M-1; #17 (Huang, self-declared open) → M-3; #32 (build status) → N-1 |

**Bottom line.** The remediation round did land: the headline numbers, the Adapter baseline reversal, the n=204 correlation overhaul, the five redrawn figures, the strict-freeze control and its table, the citation-ID/DOI/year repairs, the highlights rewrite and the disclosure paragraph are all present **in the built 41-page PDF**, and the strict-freeze figures trace to real per-seed artefacts. The failure mode the brief warned about has **not** recurred for those items. It has recurred in one narrow case — the `yi2025decipher` wording, where two of four sites were missed (M-1) — and it is presently live in a second case of exactly that shape, where the *script* was fixed but the *raster* was not regenerated (M-2, Figure 11). Recommended immediate actions, in order: regenerate `fig11_gsnr.png` and recompile (M-2, closes round-1 [M7]); fix the two `yi2025decipher` sentences (M-1, three-line edit); correct the log's build-status block and add the Table 2 baseline note (N-1/S-1).
