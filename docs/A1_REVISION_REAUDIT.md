# A1 revision re-audit — blocks 4, 6, 7 of `paper_a1/revision_additions.tex`

**Audit kind:** read-only verification of numbers against raw result files.
**Date of audit:** 2026-09-14 (session).
**Files modified by this audit:** this report only (`docs/A1_REVISION_REAUDIT.md`).
**Python used:** `D:\Anaconda\envs\pytorch\python.exe` (read-only `json.load` of the named key paths).

**Authoritative input set**

| Artefact | Path pattern |
|---|---|
| Endpoint top-1 / val loss | `outputs/a1_class_aligned/lr{0.0,0.05,0.1,0.25,0.5,1.0}/seed{42,123,456}/results.json` → `top1_50k`, `val_loss` |
| Endpoint τ (recomputed) | `outputs/a1_class_aligned/lr*/seed*/tau_recomputed_ep10.json` → `tau_final`, `tau_sd_across_samples` |
| Per-epoch sweep (λ=0, seed 42) | `outputs/a1_class_aligned/lr0.0/seed42/eval_epoch{1,2,3,5,10}.json` → `tau_final`, `top1_50k`, `val_loss` |
| Per-epoch τ (recomputed) | `outputs/a1_class_aligned/lr0.0/seed42/tau_recomputed_ep{1,2,3,5,10}.json` |
| Gate script | `tools/ap3_a1_revision_check.py` |
| Manuscript | `paper_a1/revision_additions.tex` (blocks 4 @131–151, 6 @178–220, 7 @225–242) |

**Two structural facts established up front (they drive several verdicts)**

1. `tau_final` is `null` in every `results.json` (verified: `lr0.0/seed42/results.json` → `"tau_final": null`). Any gate assertion reading τ from `results.json` would therefore fail-closed. All τ must come from `tau_recomputed_ep*.json` (or `eval_epoch*.json` for the λ=0/seed-42 sweep).
2. All 17 present `results.json` carry `fingerprint.class_names = 1000` and the same
   `parquet_sig = d13718e47e9e41c2`, `refs_mtime = 1789384934`, `parquet_files = 14` — i.e. one homogeneous 1000-class, one-shard-set basis. No 1001-class contamination survives in the current tree.

**± convention (asked for explicitly in item 1).** The printed `±` is the **sample standard deviation (ddof = 1)**, not the population sd. Two independent confirmations:

* Recomputed from block-4 raw values: λ=0 top-1 sample sd 0.045078 (prints "0.05") vs population sd 0.036806 (would print "0.04"); λ=1 τ sample sd 0.008253 ("0.008") vs population 0.006739 ("0.007"). Only ddof=1 matches the printed digits, at all six quantities.
* Project convention: `tools/clip_a1_multiseed.py:220` writes the block-3 σ as `np.std(rs, ddof=1)`. Verified against data: τ per-seed Spearman `[0.912479, 0.909060, 0.915897, 0.924786, 0.921368]` → ddof=0 sd 0.005727, ddof=1 sd **0.006403** = the stored `aggregate.spearman.tau.std` (0.006403). So `±` = sample sd is the house convention, and block 4 follows it consistently.

---

## 1. Block 4 — λ_reg dose–response (VERDICT: 6/6 quantities PASS, 1 FAIL on the "three seeds each" scope)

### 1.1 The six quantities, recomputed

Raw values (exact `repr` from the JSON):

| λ | seed | file | key | value |
|---|---|---|---|---|
| 0.0 | 42 | `lr0.0/seed42/results.json` | `top1_50k` | 58.077999999999996 |
| 0.0 | 123 | `lr0.0/seed123/results.json` | `top1_50k` | 58.158 |
| 0.0 | 456 | `lr0.0/seed456/results.json` | `top1_50k` | 58.082 |
| 1.0 | 42 | `lr1.0/seed42/results.json` | `top1_50k` | 55.494 |
| 1.0 | 123 | `lr1.0/seed123/results.json` | `top1_50k` | 55.908 |
| 1.0 | 456 | `lr1.0/seed456/results.json` | `top1_50k` | 55.388000000000005 |
| 0.0 | 42/123/456 | `lr0.0/seed*/tau_recomputed_ep10.json` | `tau_final` | 0.7087733149528503 / 0.7134555578231812 / 0.7015377879142761 |
| 1.0 | 42/123/456 | `lr1.0/seed*/tau_recomputed_ep10.json` | `tau_final` | 0.6397344470024109 / 0.6401955485343933 / 0.6256755590438843 |
| 0.0 | 42/123/456 | `lr0.0/seed*/results.json` | `val_loss` | 2.3590543041229246 / 2.289771484375 / 2.336320240020752 |
| 1.0 | 42/123/456 | `lr1.0/seed*/results.json` | `val_loss` | 2.1348359327316286 / 2.103867835998535 / 2.133292381286621 |

Recomputation (n = 3, all means over seeds 42/123/456):

| Quantity | Arithmetic | Mean | sd (n−1) | sd (n) | Manuscript | Verdict |
|---|---|---|---|---|---|---|
| top-1 @ λ=0 | (58.0780+58.1580+58.0820)/3 = 174.3180/3 | **58.106000** | **0.045078** | 0.036806 | 58.11 ± 0.05 | **PASS** (sample sd; prints right) |
| top-1 @ λ=1 | (55.4940+55.9080+55.3880)/3 = 166.7900/3 | **55.596667** | **0.274782** | 0.224359 | 55.60 ± 0.27 | **PASS** (sample sd; prints right) |
| τ @ λ=0 | (0.708773315+0.713455558+0.701537788)/3 = 2.123766661/3 | **0.707922** | **0.006004** | 0.004902 | 0.708 ± 0.006 | **PASS** (sample sd; prints right) |
| τ @ λ=1 | (0.639734447+0.640195549+0.625675559)/3 = 1.905605555/3 | **0.635202** | **0.008253** | 0.006739 | 0.635 ± 0.008 | **PASS** (sample sd; prints right) |
| val loss @ λ=0 | (2.359054304+2.289771484+2.336320240)/3 = 6.985146029/3 | **2.328382** | 0.035317 | 0.028836 | 2.33 | **PASS** |
| val loss @ λ=1 | (2.134835933+2.103867836+2.133292381)/3 = 6.371996150/3 | **2.123999** | 0.017451 | 0.014249 | 2.12 | **PASS** |

Direction check: τ falls 0.7079 → 0.6352 (−10.3%), top-1 falls 58.106 → 55.597 (−4.3%), val loss *improves* 2.3284 → 2.1240 (−8.8%). All three as claimed.

### 1.2 Monotonicity of the full λ sweep (VERDICT: PASS, with a scope caveat)

Per-λ values (τ from `tau_recomputed_ep10.tau_final`, top-1/val from `results.json`):

| λ | top-1 (seed 42 / 3-seed mean) | τ (seed 42 / 3-seed mean) | val loss (seed 42 / 3-seed mean) |
|---|---|---|---|
| 0.0 | 58.0780 / 58.1060 | 0.708773 / 0.707922 | 2.359054 / 2.328382 |
| 0.05 | 57.9660 / **n=1** | 0.706591 / **n=1** | 2.337642 / **n=1** |
| 0.1 | 57.8000 / 57.8207 | 0.703929 / 0.702220 | 2.317838 / 2.288076 |
| 0.25 | 57.3840 / **n=1** | 0.688280 / **n=1** | 2.267493 / **n=1** |
| 0.5 | 56.7300 / 56.7127 | 0.667622 / 0.662211 | 2.204543 / 2.185134 |
| 1.0 | 55.4940 / 55.5967 | 0.639734 / 0.635202 | 2.134836 / 2.123999 |

Strict monotonicity holds at **every** λ step for all three metrics, on the seed-42 series (Δ all negative: top-1 −0.1120/−0.1660/−0.4160/−0.6540/−1.2360; τ −0.002182/−0.002662/−0.015649/−0.020658/−0.027888; val −0.02141/−0.01980/−0.05035/−0.06295/−0.06971) and also on the three-seed subset λ ∈ {0, 0.1, 0.5, 1.0}. **The monotone claim is supported.** The caveat that makes it a FAIL for the parenthetical clause is below.

### 1.3 FAIL — `(three seeds each)` over-generalises the sweep

`lr0.05/{seed123,seed456}/` and `lr0.25/{seed123,seed456}/` **do not exist** (no `results.json`, no `tau_recomputed_ep10.json`; confirmed by full-tree listing and by `os.path.exists` per path). Only λ ∈ {0.0, 0.1, 0.5, 1.0} have n = 3. The manuscript's parenthetical "(three seeds each)" sits immediately before the monotone claim, which spans λ = 0 → 1, so the middle of the claimed monotone response (λ = 0.05 and 0.25) is single-seed. The six endpoint numbers quoted are all correctly three-seed; the *sweep* claim is not.

**Arithmetic (for completeness):** the three-seed means listed in §1.2 above are computed as e.g. λ=0.5 top-1 (56.7300+56.8420+56.5660)/3 = 170.1380/3 = 56.712667 and λ=0.1 τ (0.703929+0.705856+0.696876)/3 = 2.106661/3 = 0.702220.

### 1.4 Other Block-4 statements

* "fine-tune pure both-position LoRA (rank 8; only LoRA parameters trainable)" — supported by code: `tools/train_class_aligned.py:287` `apply_lora_to_model(model, rank=8, alpha=16.0, ...)` and `:316` `trainable = [p for n, p in model.named_parameters() if p.requires_grad and 'lora_' in n]`. **PASS**
* "pseudo-labels are wrong on ≈ 41% of images" — supported: `outputs/imagenet1k_zs_50k_plain.json` → `results_plain.frozen` = 59.28 (50k, single template) ⇒ 100 − 59.28 = **40.72% ≈ 41%**. **PASS** (note: the error rate on the *training* split is not recorded in any listed JSON; 40.72% is the frozen 50k top-1 complement and is the value the claim matches).
* The "59.3% → 78.6%" positive control belongs to §sec:results, not to the files in scope — not audited here.

---

## 2. Block 6 — per-epoch monitor table + narrative (VERDICT: 15/15 cells PASS, 3 FAIL in the narrative)

### 2.1 The 15 table cells — all PASS

Source: `outputs/a1_class_aligned/lr0.0/seed42/eval_epoch{1,2,3,5,10}.json`.

| key path | ep 1 | ep 2 | ep 3 | ep 5 | ep 10 | Table row | Verdict |
|---|---|---|---|---|---|---|---|
| `.tau_final` | 0.7563133835792542 | 0.7385711669921875 | 0.7270289063453674 | 0.7108844518661499 | 0.7087733149528503 | 0.7563 / 0.7386 / 0.7270 / 0.7109 / 0.7088 | **PASS 5/5** |
| `.top1_50k` | 59.788 | 59.343999999999994 | 58.87 | 58.282000000000004 | 58.077999999999996 | 59.79 / 59.34 / 58.87 / 58.28 / 58.08 | **PASS 5/5** |
| `.val_loss` | 2.33830029296875 | 2.323349510192871 | 2.3100979976654052 | 2.3478604164123533 | 2.3641718006134034 | 2.3383 / 2.3233 / 2.3101 / 2.3479 / 2.3642 | **PASS 5/5** |

Rounding is correct in all 15 cells (including the borderline ep-2 val loss 2.3233495… < 2.32335 ⇒ 2.3233 ✓).

Cross-check: the τ column is independently reproduced by `lr0.0/seed42/tau_recomputed_ep{1,2,3,5,10}.json` → `tau_final`, which is **bit-identical** to `eval_epoch*.json` at all five epochs (e.g. both 0.7563133835792542 and 0.7087733149528503). The two independent derivations agree exactly.

### 2.2 Derived narrative claims

| # | Claim | Arithmetic / evidence | Verdict |
|---|---|---|---|
| B6.4 | "τ … loses 6.3% of its value (0.7563 → 0.7088)" | (0.7087733150 − 0.7563133836)/0.7563133836 = −0.0475400686/0.7563133836 = **−6.2858%** → −6.3% | **PASS** |
| B6.5 | "against 2.9% for zero-shot top-1 (59.79 → 58.08%)" | (58.078 − 59.788)/59.788 = −1.710/59.788 = **−2.8601%** → −2.9%; endpoints match `eval_epoch1.top1_50k` and `eval_epoch10.top1_50k` | **PASS** |
| B6.6 | "Top-1 … falls monotonically from the first evaluation" | 59.788 > 59.344 > 58.87 > 58.282 > 58.078 — strictly decreasing | **PASS** |
| B6.7 | "validation loss … minimum at epoch 3 (2.3101) … worsens to 2.3642 at the endpoint" | argmin = epoch 3 (2.3100980), and 2.3641718 is both the ep-10 value and the maximum of the five points | **PASS** |
| B6.8 | "τ erodes fastest … all three signals move adversely" | \|rel\| τ 6.2858% > top-1 2.8601% > val 1.1064% ((2.3641718−2.3383003)/2.3383003); τ ↓, top-1 ↓, val ↑ = worse | **PASS** |
| B6.9 | "per-image spread … (sd = 0.26–0.32)" | `lr0.0/seed42/tau_recomputed_ep*.json` → `tau_sd_across_samples` = 0.255746 (ep1), 0.266630 (ep2), 0.271254 (ep3), 0.281436 (ep5), 0.282159 (ep10) ⇒ range **0.2557–0.2822 ⇒ "0.26–0.28"**. The value 0.3172 (= 0.32) only appears corpus-wide (`lr1.0/seed456/tau_recomputed_ep10.json`), never in this sweep | **FAIL** |
| B6.10 | "a practitioner stopping on validation loss alone would stop three epochs late" | Best ordering (τ max = 0.7563) and best zero-shot (top-1 max = 59.788) are **both at epoch 1**; the val-loss stop point is epoch 3 ⇒ **two** epochs late (4 if the practitioner keeps the epoch-5 checkpoint instead of rolling back). No reading of the data yields three | **FAIL** |
| B6.11 | "we … evaluate every epoch in a fresh process" | Only `eval_epoch{1,2,3,5,10}.json` exist; `epoch{1..10}.pt` exist but epochs 4, 6, 7, 8, 9 have no evaluation file. The block's own caption says "Epochs 1, 2, 3, 5 and the endpoint 10 are the evaluated points of this sweep" | **FAIL** (minor, wording) |

Not contradicted: "All three signals move adversely" is true end-to-end (val loss does improve ep1→ep3, but the text itself flags val loss as non-monotone, and 2.3642 > 2.3383).

---

## 3. Block 7 — pure-LoRA re-verification note (VERDICT: 7/8 PASS)

| Claim | Evidence (file → key → value) | Verdict |
|---|---|---|
| τ = 0.7563 at epoch 1 | `lr0.0/seed42/eval_epoch1.json` → `tau_final` = 0.7563133835792542 (= `tau_recomputed_ep1.json` → 0.7563133835792542) | **PASS** |
| τ = 0.7270 at epoch 3 | `lr0.0/seed42/eval_epoch3.json` → `tau_final` = 0.7270289063453674 | **PASS** |
| τ = 0.7088 at epoch 10 | `lr0.0/seed42/eval_epoch10.json` → `tau_final` = 0.7087733149528503 | **PASS** |
| top-1 59.79 → 58.08% | `eval_epoch1.top1_50k` = 59.788 → `eval_epoch10.top1_50k` = 58.077999999999996 | **PASS** |
| "the dose–response script selects trainable parameters by name (the `lora_` prefix), so it cannot update embeddings or LayerNorms" | `tools/train_class_aligned.py:313–316` (comment + `trainable = [... if 'lora_' in n]`); rank 8 at `:287` | **PASS** |
| Path `a1_class_aligned/lr0.0/seed42` | All six files referenced above resolve under that directory | **PASS** |
| Block no longer quotes τ = 0.767 → 0.748 as evidence | `grep` over `paper_a1/*.tex`: `revision_additions.tex:235` contains "0.767 → 0.748" **only** inside the retirement sentence; "58.86"/"58.90" occur **nowhere** in `revision_additions.tex` | **PASS** |
| Reason for retiring is stated | `revision_additions.tex:234–238`: "An earlier internal comparison against the archived submitted checkpoints returned τ = 0.767 → 0.748, but that measurement used a frozen-reference cache built from an ImageNet shard copy that is no longer on disk and cannot be rebuilt identically…" — consistent with the incident diagnosis (`docs/A1_CLASS_ALIGNED_INCIDENT.md`, 缺陷 1: `frozen_refs.pt`'s `S0` no longer corresponds to the current shard; stale reference archived as `frozen_refs.STALE_2026-08-16.pt`) | **PASS** |

### 3.1 FAIL — the retired numbers are still quoted as evidence in the manuscript this block belongs to

The provenance of the retired comparison is still on disk and traceable: `outputs/a1_tau_trajectory.json` → `both[0].tau` = 0.7665 (⇒ 0.767) and `both[9].tau` = 0.7483 (⇒ 0.748); `both[0].top1` = 58.86 and `both[9].top1` = 58.9 (⇒ 58.86 → 58.90%). The same file supplies values still asserted in the manuscript body:

* `paper_a1/main.tex:102` (Figure `fig:tau` caption): "… both-position ($\tau=0.748$, top-1 $58.9\%$)" — the exact retired endpoint, quoted as one of five real checkpoints.
* `paper_a1/main.tex:161` (§`sec:traj`, cited by blocks 6 and 7): "$\tau$ declines early ($1.00\to 0.75$ by epoch 3) … zero-shot top-1 remains flat at $58.5$–$58.9\%$ throughout" — matches `a1_tau_trajectory.json` `both[2].tau` = 0.7478 and `both[*].top1` ∈ [58.46, 58.94].
* `paper_a1/main.tex:166` (Figure `fig:traj` caption): "top-1 stays flat at $58.5$–$58.9\%$".

So within block 7 the retirement is honest and complete, but the retire-and-narrow is **not propagated**: the manuscript paragraph that blocks 6 and 7 cite as "Section~\ref{sec:traj}" still rests on the void-reference trajectory, and still asserts the "top-1 is inert" reading that block 7 explicitly narrows ("The conclusion this block supports is correspondingly narrower than 'top-1 is inert'"). `docs/A1_CLASS_ALIGNED_INCIDENT.md` 待办 #4 lists `a1_tau_trajectory.json` as still needing re-verification. This must be reconciled before the two artefacts are merged.

---

## 4. Cross-block consistency (VERDICT: 3/5 PASS — 2 FAIL, the highest-risk item)

The λ_reg = 0 / seed-42 endpoint is described in three places:

| Block | Text | Quantity | Source value | Correctly labelled? |
|---|---|---|---|---|
| 4 (@143) | τ "0.708±0.006", top-1 "58.11±0.05" | **three-seed mean** | 0.707922 ± 0.006004; 58.106 ± 0.045078 | yes ("three seeds each") |
| 6 (@196–197) | epoch-10 row: τ 0.7088, top-1 58.08 | **single seed (42)** | 0.7087733149528503; 58.077999999999996 | yes (caption: "λ_reg = 0, seed 42") |
| 7 (@232–233) | τ 0.7088 (ep10), top-1 59.79 → 58.08% | **single seed (42)** | same files as block 6 | yes (path cited) |

* **X.1 PASS** — the single-seed τ 0.7087733 lies inside the three-seed interval 0.707922 ± 0.006004 = [0.70192, 0.71393]; τ is the *same* underlying run, so agreement is expected and holds.
* **X.2 PASS** — 58.078 lies inside 58.106 ± 0.045078 = [58.061, 58.151]. (58.078 is only 0.028 below the mean — i.e. the seed-42 run is slightly *below* average at λ=0; not a contradiction.)
* **X.4 PASS** — the two val-loss figures are **not** conflated in the text: block 4's "2.33 → 2.12" are the λ=0 and λ=1 *three-seed means* (2.328382, 2.123999), while block 6's "2.3642" is the λ=0 *single-seed* endpoint. They are quoted in separate blocks with different labels; no sentence equates them.

### 4.1 FAIL — single-seed vs three-seed is blurred in block 6, lines 216–218

> "Second, this sweep is one seed; the λ_reg = 0 endpoint ($58.11\%$, $\tau=0.708\pm0.006$) is the same run whose three-seed endpoint appears in the dose–response block above, so the two blocks describe one trajectory."

The parenthetical `(58.11%, τ=0.708±0.006)` is the **three-seed mean**, but it is offered as the endpoint *of this one-seed sweep*, whose actual endpoint is 58.08 / 0.7088 (the table row two lines above). The sentence simultaneously asserts "this sweep is one seed" and equates the sweep with a three-seed statistic — the precise blur item 4 was asked to catch. The defensible phrasing would quote 58.08 / 0.7088 as this run's endpoint and say it is one of the three seeds averaged in the dose–response block.

### 4.2 FAIL — the λ=0 / seed-42 endpoint has two different val losses in two authoritative files

| File | Written | key | value |
|---|---|---|---|
| `outputs/a1_class_aligned/lr0.0/seed42/results.json` | 2026-09-14 19:37:52 | `val_loss` | **2.3590543041229246** |
| `outputs/a1_class_aligned/lr0.0/seed42/eval_epoch10.json` | 2026-09-14 22:25:17 | `val_loss` | **2.3641718006134034** |

Δ = **0.0051175**. Same (λ, seed, epoch), same `fingerprint` (`parquet_sig d13718e47e9e41c2`, `refs_mtime 1789384934`, `class_names 1000`), and the two files agree **exactly** on `top1_50k` (58.077999999999996) and on τ (0.7087733149528503) — only `val_loss` diverges. Consequence: block 4's λ=0 three-seed mean (2.328382, built from the `results.json` series 2.359054/2.289771/2.336320) and block 6's endpoint cell (2.3642, from `eval_epoch10.json`) rest on **mutually inconsistent records of the same run**, even though block 6 declares the two blocks to be "one trajectory". Neither manuscript block mentions the discrepancy. Whichever value is canonical, the other file must be regenerated or the difference explained (EMA/non-EMA, val-subsampling or batch-order difference — `results.json` carries `"ema": true`; `eval_epoch10.json` has no `ema` key).

*(Note: the rounded block-4 figure is insensitive — substituting 2.3641718 gives 2.330088, still "2.33" — which is exactly why nothing has caught it.)*

---

## 5. The gate script `tools/ap3_a1_revision_check.py` (VERDICT: 4/5 PASS — passes cleanly, but is staleness-blind)

### 5.1 Re-run result — PASS

```
$ python tools/ap3_a1_revision_check.py
=== B1 逐点预测 τ(λ) ===
  n=9 pearson=1.0 max_abs_diff=0.0019 identical=False
=== B2 Qwen2-VL-2B 逐 λ ===
=== B3 5 seeds 稳健 ===
=== B4 剂量-响应（λ_reg 0→1；seed42 端点 + 三种子均值）===
=== B5 DINOv2 ===
  τ 最小 0.9301（素材称 '>0.93' → 实际 成立但仅高 0.0001）
=== B6 τ 早停（lr0.0 逐 epoch）===
=== B8 跨族留出泛化 ===

通过 63 项，失败 0 项
[exit code: 0]
```

Reproduces the claimed "通过 63 项，失败 0 项" and exits 0. **PASS**

### 5.2 B4/B6 read the authoritative files — PASS

* B4 τ assertions: `tau_rec()` (`tools/ap3_a1_revision_check.py:74–76`) opens `outputs/a1_class_aligned/{lr}/seed{s}/tau_recomputed_ep10.json` and returns `['tau_final']`. Used at `:87` (λ=0 seed 42), `:88` (λ=1 seed 42) and `:100` (all three seeds). **It never touches an `eval_epoch10.json` path.** The only `eval_epoch*` reader is `rd()` (`:36–38`), called exclusively by B6 with `'lr0.0'` (`:126`). **PASS**
* `lr1.0` has **no** `eval_epoch10.json` in the active tree: `outputs/a1_class_aligned/lr1.0/seed42/` contains only `epoch{1..10}.pt`, `results.json`, `tau_recomputed_ep10.json` (same for seeds 123/456). The predecessor artefact survives only in the archive: `outputs/a1_class_aligned/_archive_broken_cents_0816_0914/lr1.0/seed42/eval_epoch10.json` → `tau_final` = 0.6107386840685854, `top1_50k` = 54.364, `val_loss` = 2.1026611862182616. Had the gate still pointed there, its B4 τ assertion (expected 0.6397 ± 0.0006) would **fail** with \|0.6107 − 0.6397\| = 0.029 ≫ 0.0006 — and a missing file yields `None`, which `check()` treats as a failure. So the risky path is both absent and fail-closed. **PASS**

### 5.3 FAIL — the gate can pass on stale (or internally inconsistent) data

Facts:

1. Every reader (`j`, `rd`, `res`, `tau_rec`) tests only `os.path.exists`. No assertion verifies that a file's declared `lambda_reg` / `seed` / `epoch` matches the directory it was found in, that `sub_indices_source` is the current reference (`cache` → `frozen_refs.pt`; the stale dual `frozen_refs.STALE_2026-08-16.pt` is still on disk beside it), or that the `fingerprint` block matches the other files. Numeric tolerance (τ ±0.0006, val ±0.0006, top-1 ±0.06) is the *only* staleness defence.
2. The three-seed means print `n=` in the label but never assert `n == 3` (`:103–105`); n-correctness is enforced only incidentally by tolerance. (Empirically it does hold here — dropping a seed moves λ=1 τ to 0.639965 and top-1 to 55.701, both outside tolerance — but that is luck, not design.)
3. There is **no cross-file consistency assertion**, so §4.2's 0.0051175 val-loss disagreement between `results.json` and `eval_epoch10.json` for the same endpoint passes unnoticed. Concretely: B4's `check('B4 val 起点(seed42)', lo['val_loss'], 2.3591, 0.005)` (`:89`) is pinned to `results.json` (diff 4.6e-5, passes); pointed at `eval_epoch10.json` the same assertion would **fail** (diff 5.07e-3 > 5e-3). The gate asserts one of two conflicting values and cannot see the conflict.
4. Coverage gaps: the gate asserts the **15 raw table cells** but nothing else in blocks 4/6/7. It has **no assertion** for `tau_sd_across_samples` (hence the unsupported "0.26–0.32" survives), for the derived −6.3% / −2.9% erosions, for the monotone claims, for "val-loss minimum at epoch 3", for any three-seed mean of the *middle* λ points, or for any Block 7 statement.

**Answer to the question asked:** yes — the gate can pass on stale data. It is fail-closed for *missing* files and tight enough to reject the *known* stale artefact (`lr1.0/eval_epoch10.json`, τ 0.6107), but it has no provenance, fingerprint, metadata or cross-file check, so a stale file whose numbers land inside the tolerance band — or two current files that disagree with each other — pass silently. It demonstrates this today with §4.2.

---

## 6. Open-ended sweep of blocks 4, 6, 7 (VERDICT: 2/3 PASS)

* **O.1 PASS** — Block 4's "pseudo-labels are wrong on ≈41% of images" is supported by `outputs/imagenet1k_zs_50k_plain.json` → `results_plain.frozen` = 59.28 ⇒ 40.72% error. (Not in the listed authoritative set; no listed JSON records the training-split pseudo-label error rate, so this is the nearest traceable source and it agrees.)
* **O.2 PASS** — Block 7's account of the retired comparison is accurate and its provenance is traceable to `outputs/a1_tau_trajectory.json` (`both[*].tau` 0.7665→0.7483; `top1` 58.86→58.9). Nothing in the block overstates the retracted measurement.
* **O.3 FAIL** — Block 7 narrows the "top-1 is inert" reading, but the manuscript section it cites (`paper_a1/main.tex:161, 166`) still asserts "top-1 remains flat at 58.5–58.9%" from that same retired file; and `main.tex:102` still lists the retired endpoint (τ = 0.748, top-1 58.9%) among the "five real checkpoints". Block 6's own sentence "The direction is consistent with the retrain trajectory of Section~\ref{sec:traj}, where the erosion was larger" therefore compares the new sweep against a number that block 7 has just retired. Same root cause as §3.1.

### Newly noticed, logged for completeness (no manuscript claim contradicts them)

* `tau_recomputed_ep10.json` files carry `"sub_indices_source": "cache"` and `n_samples: 5000` — i.e. every quoted τ is a 5,000-image subsample from `frozen_refs.pt`. The λ=0/seed-42 sweep's τ is reproduced bit-identically by an independent recompute (`eval_epoch*.json` vs `tau_recomputed_ep*.json`), which is the strongest available evidence that the reference is no longer void; but nothing in the data records *which* reference build produced it beyond that string.
* Both `frozen_refs.pt` and `frozen_refs.STALE_2026-08-16.pt` sit in the same directory (`outputs/a1_class_aligned/`). Block 7's "cannot be rebuilt identically" is correct about the shard mapping, though the stale reference file itself does still exist on disk.
* `outputs/a1_class_aligned/lr0.5_noema/seed42/` and `lr1.0_noema/seed42/` exist but are referenced by no block; the EMA/non-EMA question is the most likely explanation for §4.2 and is not documented in the blocks.

---

## 7. Tally

**41 checks — 32 PASS, 9 FAIL.**

FAIL list (one line each):

1. **B4.9** — "(three seeds each)" over-generalises: `lr0.05/{seed123,seed456}` and `lr0.25/{seed123,seed456}` do not exist, so the monotone sweep is single-seed (n=1) at λ=0.05 and 0.25.
2. **B6.9** — "sd = 0.26–0.32" is overstated: the sweep's `tau_sd_across_samples` range is 0.255746–0.282159 (0.26–0.28); 0.3172 (→0.32) belongs to `lr1.0/seed456`, not to this sweep.
3. **B6.10** — "would stop three epochs late" is unsupported: best τ (0.7563) and best top-1 (59.788) are both at epoch 1, so stopping at epoch 3 is two epochs late.
4. **B6.11** — "evaluate every epoch in a fresh process" contradicts its own caption and the data: only epochs 1, 2, 3, 5, 10 have `eval_epoch*.json`.
5. **B7.8** — the retired τ = 0.748 / top-1 58.9% figures are still quoted as evidence in `paper_a1/main.tex` (lines 102, 161, 166: "top-1 remains flat at 58.5–58.9%"), sourced from the same void-reference `outputs/a1_tau_trajectory.json`.
6. **X.3** — single-seed vs three-seed is blurred at `revision_additions.tex:217`, which offers the three-seed means "58.11%, τ=0.708±0.006" as "the λ_reg=0 endpoint" of the one-seed sweep whose endpoint is 58.08 / 0.7088.
7. **X.5** — the λ=0/seed-42 epoch-10 val loss is not uniquely determined: 2.3590543 in `results.json` vs 2.3641718 in `eval_epoch10.json` (Δ = 0.0051175) for the same checkpoint, fingerprint, top-1 and τ.
8. **G.5** — the gate is staleness-blind and can pass on stale or self-inconsistent data (existence-only reads, no fingerprint/metadata/provenance check, no cross-file consistency check, no assertions for the sd range, derived percentages, monotonicity, val-min or Block 7) — demonstrated by check 7 passing unnoticed.
9. **O.3** — block 7 narrows the claim against "top-1 is inert" while the section it cites (`main.tex` §`sec:traj`) still asserts top-1 flat at 58.5–58.9% from the retired trajectory file; the two passages cannot both stand.
