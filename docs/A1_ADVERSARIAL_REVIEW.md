# A1 — Adversarial pre-submission review (hostile but fair)

**Manuscript:** `paper_a1/main.tex` (+ `\input` of `related_work.tex`, `related_work_bibitems.tex`),
mirror `paper_a1/main_zh.tex`, staged package `paper_a1/revision_additions.tex` (blocks 1–19).
**Target:** Multimedia Tools and Applications (Q3/Q4). **Previous decision:** rejected by Pattern Recognition Letters
(PRLETTERS-D-26-01941), R1 six comments + R2 five comments.
**Reviewer stance:** I did not accept a single claim because a document asserts it. Every number below was re-read
from `outputs/**` or from the LaTeX source myself. Nothing in the workspace was modified except this file.

---

## 0. The single most important fact for this review

`revision_additions.tex` is **not part of the submitted manuscript**. Verified by exhaustive search:

* the only `\input` directives in `main.tex` are `related_work` (line 46) and `related_work_bibitems` (line 229);
* no file in `paper_a1/` references `revision_additions`;
* `main.out`/`main.aux` show the compiled 13-page PDF contains Section 2 (Related Work, §§2.1–2.8, pp. 2–5) and
  Section 5 (§§5.1–5.7) — and nothing from the package.

Consequently the revision is split into **two different documents**: what the editor will read (`main.tex`), and what
the authors think they wrote (`revision_additions.tex`). **Seven of the twelve reviewer complaints are answered only in
the second document.** Worse, `main.tex` cites the second document to the reader twice:

* `main.tex:101` (footnote): "…(revision package, response to R1.6)."
* `main.tex:155` (footnote): "…so $\tau$ is comparable only at a fixed $k$ (revision package, response to R2.2)."

A reviewer cannot open a "revision package". These two phrases are a self-inflicted desk-reject risk (§4, D3).

**Merge status audited block by block** (see §2). Mechanically the merge is trivial and safe: the package compiles
standalone, it has **zero label collisions** with `main.tex` + `related_work.tex`, and every `\ref` in the package
resolves either internally or to an existing `main.tex` label (I checked all 23 cross-references; no dangling label).

---

## 1. The twelve complaints: verdicts

Legend: **A** = answered in the submitted manuscript · **C** = answered only by conceding · **U** = answered only in the
unmerged package (therefore *not* answered in the submission) · **O** = still open.

| # | Complaint | Verdict | What decides it (file:line) |
|---|---|---|---|
| **R1.1** | "gap as universal health indicator" not backed by citations | **A** (narrowed) | `main.tex:25` and `main.tex:31` now carry block 12's replacement text verbatim ("widely used as a *diagnostic* … often read *implicitly* as a proxy"; "What we dispute is the *unconditional* form of that reading"). `related_work.tex:315–332` restates the weakened claim. The original wording is gone from the English text. **Caveat: it survives in `main_zh.tex:33,39`** (§4, N3). |
| **R1.2** | Related Work is one paragraph, misses 7 topics | **A** | `main.tex:46` `\input{related_work}`; compiled PDF Section 2 = §§2.1–2.8 covering zero-shot robustness, drift/gap geometry, catastrophic forgetting, ranking stability, calibration, prompt sensitivity, alternative metrics, plus a scope statement. 40 new `\bibitem`s; I verified **53/53 cited keys defined, 0 uncited entries**. Two blemishes: the legacy paragraph (`main.tex:48`) is retained *after* §2.8, so the section ends on a duplicated paragraph; and `main_zh.tex:54–57` still has the single paragraph. |
| **R1.3** | τ partly true by definition | **U / O** | The answer is `revision_additions.tex:422–455` (block 11): τ is a Kendall coefficient over each image's *frozen top-5* set vs a 1 000-way argmax; the reviewers' own counterexample proves non-identity; the anti-tautology evidence is the held-out family. **None of this reasoning is in `main.tex`.** The only trace is `main.tex:212`, where the family-calibrated mapping ($R^2$ 0.371/0.378, ρ 0.927) appears as a *calibration caveat*, not as the rebuttal. A reviewer re-reading their own comment will not find themselves answered. |
| **R1.4** | own results contradict a τ-alone story (Gaussian τ=0.761→58.8% vs contraction τ=0.615→78.6%) | **C, and the concession is contradicted inside the submission** | Concession exists at `related_work.tex:334–341` ("Order preservation is **not a sufficient** statistic … class-conditional contractions improve accuracy while *lowering* the coefficient relative to the frozen reference"). But the Results section still asserts the retracted form twice: `main.tex:112` ("contracting each image toward its own class centroid **preserves order** and improves accuracy to 78.6%") and the Table 2 caption `main.tex:117` ("class-aligned perturbations (P) **preserve order**"). The paper's own Table 2 (`main.tex:129`) gives that row **τ = 0.615**, below the Gaussian row it calls destructive (τ = 0.761, 58.8%). Both rows verified in `outputs/a1_subspace_results.json`. The unmerged block 10 (`revision_additions.tex:379–415`) is where the honest reading lives. |
| **R1.5** | global translation is not real fine-tuning | **C (adequate)** | `main.tex:207` Limitations ("Global translation is a crude model of real embedding drift"); `main.tex:205` now argues from real LoRA geometry; `related_work.tex:122–128` states the non-claim explicitly ("We do not claim that fine-tuning reduces to a global translation … the translation is an idealised probe"). §5.5 carries a real-checkpoint trajectory. Weakened only by the fact that block 4 (training-time dose–response) and block 9 (exactness) stay unmerged. |
| **R1.6** | only five checkpoints, all Flickr30k | **C (merged) + evidence referenced but not presented** | Wording narrowed in `main.tex:25,203,212` (merged). `main.tex:101` now *reports* four controlled LoRA runs on COCO/Food-101/DTD/same-code-Flickr30k and their +3.3…+5.5 excess — but the table (block 18, `revision_additions.tex:853–930`) and the seed-spread analysis (block 19, `:1089–1149`) are not in the paper. **Also: the abstract's own scope clause now under-describes the evidence** ("adaptation by LoRA or full fine-tuning on Flickr30k", `main.tex:25`) while `main.tex:101` cites COCO/Food-101/DTD. And block 19's decisive negative result — τ does **not** rank seeds within a dataset ($\rho=-0.5$ COCO, $-0.5$ Food-101, $+1.0$ DTD) — appears nowhere in `main.tex`. |
| **R2.1** | first-order approximation assumes a small perturbation, but perturbation ≈ gap | **U / O** | The answer — that the pair-inversion criterion $\lambda\|g\|(m_j-m_i)>d_{ij}$ is *exact* for every λ, with the renormalisation cancelling as a positive per-image constant — exists **only** in `revision_additions.tex:314–370` (block 9). `main.tex:71–81` still presents only "a first-order expansion in $\|\delta\|$" and asserts "the second term is negligible". String search: the words *residual*, *exact*, *inversion criterion*, *non-perturbative* occur nowhere in `main.tex` or `related_work.tex`. This is the cheapest, highest-value unmerged block. |
| **R2.2** | top-5 unjustified, needs top-k ablation | **U (footnote only in submission)** | `main.tex:155` footnote now states the k-dependence ("at λ=0.5 it falls from ≈0.496 at k=3 to ≈0.411 at k=100 — so τ is comparable only at a fixed k") — but it cites the "revision package", and the ablation table (block 16, `:669–751`) with ρ 0.9125–0.9357 and the *honest* provenance finding (the archived 0.926 could only be reproduced at k=10, not k=5) is not in the paper. I verified the k=5 ρ = 0.9125, p = 8.478e-11 in `outputs/a1_rr_e2_topk.json`. |
| **R2.3** | only ImageNet + Flickr30k | **U / O** | Block 17 (`:759–843`) adds DTD/Food-101/iNat-wild/rare-species with the required protocol-deviation disclosures. `main.tex` contains no mention of these four benchmarks. Verified in `outputs/a1_rr_e3_benchmarks.json`: DTD frozen 43.1383, τ(1) 0.352979, contraction 58.4574/0.580745 — all match the block 17 table. |
| **R2.4** | three compositional-ZSL works must be cited | **U / O** | The three CZSL references (TNNLS 36(6), TIP 35, TIP 34) exist **only** as inline prose in `revision_additions.tex:629–660`; there is **no CZSL citation in `main.tex`, `related_work.tex` or `related_work_bibitems.tex`** (string search for TNNLS / compositional zero-shot / Concept-aware returns nothing). `related_work.tex:65,188` cite Winoground/`yuksekgonul2023when`, which are compositional *evaluation*, not the CZSL method literature the reviewer named. This is a zero-effort complaint left unaddressed. |
| **R2.5** | r = 1.0 anomalous; needs scatter plots, CIs, error analysis | **U / O** | `main.tex:137` still presents it as verification: "the measured mean per-class shifts at λ=1 match the prediction with Pearson $r=1.000$ … **no other mechanism is needed**". There is no scatter figure, no interval, no error analysis, and **no n** — the source (`outputs/a1_baseline_metrics.json::theory_verification`) stores only `pearson_actual_vs_predicted: 1.0, p: 0.0, std_m_c: 0.0673` (a p-value of exactly 0.0 is itself a red flag). The reframing is block 13 (`:534–577`); block 9 already concedes at `:344–348` that this $r=1.000$ "will be labelled as such rather than presented as independent validation" — i.e. the authors know `main.tex:137` currently over-claims. The bootstrap intervals (block 19) are also unmerged. |

**Tally.** Answered as submitted: **2 / 12** (R1.1, R1.2). Answered by conceding inside the submission: **2** (R1.5,
R1.6 — partially). Answered *only* in the unmerged package: **5** (R1.3, R1.4, R2.1, R2.2, R2.5). Still open because
the answer is nowhere usable: **3** (R2.3, R2.4, plus R2.1 by the same argument). Net: **8 of 12 remain live in the
submitted manuscript**, and R1.4 is worse than live — it is contradicted.

---

## 2. Merge-status audit (package block → submission)

| Block | Content | Reviewer item | In `main.tex`? | Evidence |
|---|---|---|---|---|
| 1 (`:14–47`) | point-wise τ(λ) prediction | R2.1/R1.3 support | **No** | — |
| 2 (`:53–96`) | Qwen2-VL decoder VLM | (scope) | **No** | — |
| 3 (`:101–133`) | 5-seed stability | R2.2 support | **No** | — |
| 4 (`:138–159`) | training-time class-alignment dose–response | R1.5 | **No** | — |
| 5 (`:164–181`) | DINOv2 negative control | (scope) | **No** | — |
| 6 (`:186–232`) | per-epoch monitor table | R1.5 | **No** | — |
| 7 (`:237–257`) | protocol note | R1.5 | **No** | — |
| 8 (`:287–306`) | out-of-family hold-out | R1.3/R2.5 | **No** (numbers reused at `main.tex:212`) | `outputs/a1_tau_holdout.json` |
| 9 (`:314–370`) | exactness of the inversion criterion | **R2.1** | **No** | absent from `main.tex` |
| 10 (`:379–415`) | τ necessary-not-sufficient | **R1.4** | **No** | concession only at `related_work.tex:334–341` |
| 11 (`:422–455`) | τ vs accuracy are different objects | **R1.3** | **No** | — |
| 12 (`:465–527`) | claim-scope wording | R1.1, R1.6 | **Yes, partially** | replacement text is verbatim in `main.tex:25,31,203,212`; the package header note "未动 `main.tex`" is stale (`main.tex` mtime 2026-09-15 16:47 > plan mtime 07:28) |
| 13 (`:534–577`) | r=1.0 is a self-consistency check | **R2.5** | **No** | — |
| 14 (`:584–622`) | two disclosed limitations | R1.5 | **No** | — |
| 15 (`:629–660`) | CZSL positioning + 3 refs | **R2.4** | **No** | no CZSL string anywhere in the submission |
| 16 (`:669–751`) | top-k ablation | **R2.2** | footnote only | `main.tex:155` |
| 17 (`:759–843`) | 4 further benchmarks | **R2.3** | **No** | — |
| 18 (`:853–930`) | non-Flickr30k checkpoints | **R1.6** | prose only | `main.tex:101` |
| 19 (`:946–1214`) | 5 hardening experiments | R1.6/R2.5 | **No** | — |

**Only block 12 (partially) and the off-package `related_work.tex` have actually reached the manuscript.**

---

## 3. New problems created by the revision

Severity: **[D]** desk-reject / whole-paper credibility · **[H]** major, must fix · **[M]** should fix · **[L]** cosmetic.

### N1 [D] The manuscript cites a document the reviewer cannot obtain
`main.tex:101` footnote — "…(revision package, response to R1.6)"; `main.tex:155` footnote — "…(revision package,
response to R2.2)". Both are inside footnotes of the two load-bearing results paragraphs. An editor reads this as a
botched conversion from an internal rebuttal document.

### N2 [H] The Results section contradicts the paper's own table and its own Related Work (R1.4 reproduced internally)
* `main.tex:112` — "contracting each image toward its own class centroid **preserves order** and improves accuracy to 78.6% ($a=0.5$)".
* `main.tex:117` (Table 2 caption) — "class-aligned perturbations (P) **preserve order**".
* `main.tex:129` (the same table) — class contraction $a=0.5$: top-1 78.6, **τ = 0.615**; Gaussian σ=0.25: top-1 58.8, **τ = 0.761**.
* `related_work.tex:334–341` — "class-conditional contractions improve accuracy while *lowering* the coefficient relative to the frozen reference … order preservation is **not a sufficient** statistic".
Both Table 2 rows verified in `outputs/a1_subspace_results.json` (`class_contraction 0.5 → 78.58 / 0.615`;
`gaussian 0.25 → 58.8 / 0.7612`). The paper therefore prints the reviewer's counterexample and mislabels it.

### N3 [H] The Chinese mirror still contains every retracted claim, and disagrees numerically with the English text
`main_zh.tex` (mtime 2026-09-15 09:14) predates `main.tex` (16:47) and was not re-synchronised. It is a submission-grade
artifact (`main_zh.pdf`, 730 KB), so its content matters.
* `main_zh.tex:33` — "被广泛视为跨模态对齐的普适健康指标" = the exact R1.1 sentence the English abstract removed.
* `main_zh.tex:39` — "它已成为事实上的健康指标" = the exact R1.1 Introduction sentence removed at `main.tex:31`.
* `main_zh.tex:54–57` — Related Work is still the single legacy paragraph ⇒ the zh mirror fails R1.2.
* `main_zh.tex:110` — "真实检查点落在同一流形上" ("the real checkpoints lie **on the same manifold**") + τ = 0.794 / 0.748, top-1 58.7 / 58.9 %, versus `main.tex:101` τ = 0.791 / 0.750, top-1 58.8 / 58.6 % and "lie **on or above** … an outstanding open question". The English values match `outputs/a1_tau_trajectory.json` (text-only ep10 τ 0.7909, top-1 58.76; both ep10 τ 0.7497, top-1 58.58); the Chinese values match nothing.
* `main_zh.tex:212,221` — "对面向分类的自适应，排序保持 τ 是正确的信号" and "我们建议将 τ 作为面向分类微调的监控信号": the two retracted recommendations that `main.tex:203,212` deliberately weakened.
* `main_zh.tex:214` — "训练扰动以第一类为主" ("trained perturbations are predominantly the [gap] component"), which **inverts** `main.tex:205` ("trained perturbations are predominantly **orthogonal** to the gap direction") and contradicts block 19's measured orthogonal share of 86.0–99.7 % (`outputs/a1_h_offset.json`).

### N4 [H] An abstract editing fragment survived the merge
`main.tex:25`: "**We show that this implicit quality-proxy reading does not extend to zero-shot classification.
We show this is incomplete.**" — the second sentence is the orphaned tail of the pre-revision abstract; block 12's
replacement was pasted in front of it. Two consecutive "We show" clauses, the second a dangling fragment, on the first
line a reviewer reads.

### N5 [H] A load-bearing prose claim is falsified by the project's own result file
`main.tex:101` + its footnote: "the three archived Flickr30k LoRA checkpoints have τ above the curve's entire range at
k=5 … so **no finite offset is defined** for them." The revision's own hardening experiment assigns them finite offsets:
`outputs/a1_h_offset.json` bisects λ for every checkpoint and reports
`flickr30k_text_only_r8` τ=0.7595 → matched λ 0.1428, excess **+0.48**;
`flickr30k_both_r8` τ=0.6962 → matched λ 0.1956, excess **+2.20**;
`flickr30k_retrain_both_ep10` τ=0.7497 → matched λ 0.1516, excess **+0.54**.
The premise that produced the error is still written into the producing script's docstring
(`tools/a1_h_offset.py:6–7`: "the three archived Flickr30k checkpoints have tau above the synthetic curve's entire
range") — the script then measured the opposite. Note that the "no finite offset" claim also sits awkwardly beside the
paper's own central boast that τ(λ) is computable in closed form for *any* λ.

### N6 [H] The headline gap-growth number is not reproducible under the paper's own evaluator
* Abstract/`main.tex:35`: both-position LoRA "increases the Centroid Gap from 0.82 to 0.93 ($\text{CG}\Delta=+0.114$)".
  Source: `outputs/imagenet_zs/both_r8/results.json` (`initial_gap.centroid_gap` 0.81883 → `final_gap.centroid_gap`
  0.93256, Δ = +0.1137). ✔ internally consistent.
* But the revision's shared evaluator re-measures **the same checkpoint file** — `outputs/a1_rr_e4_eval_archived.json`
  entry `flickr30k_both_r8`, `"ckpt": "outputs/imagenet_zs/both_r8/best_checkpoint.pt"` — at
  `CG_flickr_val = 0.847886`, i.e. **Δ = +0.033**, with the identical frozen reference (0.814736) that reproduces the
  trajectory logger (0.815, `outputs/a1_tau_trajectory.json`).
* `main.tex:160` explains the 0.848 as "run-to-run variability notwithstanding". It is **not** run-to-run variability:
  the same weights, the same 1 000-image Flickr30k validation subset, two different numbers (0.933 vs 0.848; Δ differs
  by a factor 3.4). The gap-growth figure in the abstract therefore rests on a legacy logger that the project's own
  later protocol does not reproduce, and the discrepancy is never disclosed as such.

### N7 [H] Full fine-tuning provenance: script lost, run diverged, honest rows labelled "archived weights"
* `main.tex:66`: "three full fine-tuning runs (seeds 42/123/999) — all trained on Flickr30k **with archived weights**."
* `outputs/imagenet_zs_rerun/{full_ft,full_ft_s123,full_ft_s999}/results.json` each carry
  `"reconstruction_note": "…原脚本已丢失"` ("the original script is lost"); the seed-42 rerun diverges
  (`val_losses` 4.11 → 7.88, `final_R1` 0.002).
* `outputs/imagenet_zs_rerun/full_ft/zero_shot_eval.json` carries a **hard-coded** `"paper_value": 7.38` in the
  generating script (`tools/clip_fullft_zeroshot_eval.py`, `out.update({... 'paper_value': 7.38})`) while the same file
  measures 0.13 %/0.12 % for those weights. `main.tex:101` attributes 7.4 % to seed 123 and 0.1 % to seed 42, matching
  `outputs/a1_e2b_e3b.json` (`full_ft_s42` 0.14, `full_ft_s123` 7.42, `full_ft_s999` 7.02) — so the manuscript is
  consistent with its JSON, but the JSON territory contains a stale "paper value" that contradicts it. With a
  reproducibility archive promised (`main.tex:212`), this is a discoverable inconsistency about the *only* full-FT
  evidence in the paper.

### N8 [M] The 50 k figures quoted for the archived checkpoints come from a protocol the paper does not name
`main.tex:35` quotes 59.7 % (50 k) for both-position. `outputs/imagenet1k_zs_50k_plain.json` gives 59.67 (plain
single-template) and `..._synset.json` gives 60.18 (synset template). The paper's setup (`main.tex:53`) says the plain
template, so the choice is defensible, but the two protocols differ by 0.5 points and the text labels neither.

### N9 [M] Figure 2 mixes two sample sizes and the caption does not say so
`tools/clip_a1_figures.py:38–46` plots `outputs/a1_full_results.json` (50 000-image accuracies) *and*
`a1_subspace_results.json` (5 000) *and* `a1_e2b_e3b.json` (5 000) in one τ–top-1 plane, while the real-checkpoint stars
are 5 k. `main.tex:62` asserts the different roles of the two samples, and `main.tex:101` compares real checkpoints
(5 k) against that mixed curve. The offset being claimed (+3.3…+5.5) is an order of magnitude larger than the 5 k/50 k
difference (e.g. frozen 59.10 vs 59.28), so the conclusion survives — but the caption of Fig. 2 should state it.

### N10 [M] Three different "condition counts" in one project
`main.tex:25` and `Fig. 2` caption: **34** conditions (verified: 20 `a1_full_results` + 11 `a1_subspace` + 3 `e2b`
points, per `tools/clip_a1_figures.py:38–46`). `main.tex:155`: **26** conditions ("this comparison grid", verified
`n_conditions: 26`). Unmerged block 8/12: **28** conditions (`a1_tau_holdout.json::key_numbers.total_conditions_with_metrics
= 28`, three model families). The manuscript never explains why 34 ≠ 26; after merge it will contain 26, 28 and 34.

### N11 [M] The "+3.3 to +5.5 excess" is quoted from the more favourable of two of the paper's own pipelines
`main.tex:101` and block 18 (`:910–912`) use `outputs/a1_rr_summary.json`
(COCO 5.4691, Food-101 4.69, DTD 4.4164, Flickr30k-ref 3.347 → range +3.3…+5.5, by linear interpolation on the sampled
λ grid). The later hardening pipeline bisects λ for an exact τ match and gets markedly smaller excesses
(`outputs/a1_h_offset.json`: 4.56, 4.06, 3.56, 3.12 → +3.1…+4.6). `main.tex` quotes the larger set; block 19 quotes the
smaller ($+3.62\pm1.41$ over twelve checkpoints — I reproduced exactly 3.6167/1.4075/0.54/6.06 from the JSON, so the
block-19 number is right). The two numbers will sit in the same paper after merging.

### N12 [M] "Prediction equals measurement" is used as validation, forty lines after the paper explains why that is not validation
Block 10 (`:404–415`) rests the R1.4 mechanism on "prediction equal to measurement (70.32 %/0.7598 at $a=0.25$ and
78.58 %/0.615 at $a=0.5$)". I read the producing script: `tools/clip_a1_theory_verify.py:161–174` computes
`S2 = S + a*Delta`, then `argmax` and Kendall — i.e. it re-applies the same affine map and calls the result
"predicted". `outputs/a1_theory_verify.json` returns values identical to the separate measurement in
`a1_subspace_results.json` to four significant digits. Block 13 (`:570–577`) states that the closed-form check *does not
apply* once you leave image-side translation ("Remove any one of the four — as text-side surgery, **class-conditional
contraction**, or any training-time update does"). The manuscript cannot simultaneously tell R2.5 that exact agreement
between two functions of the same frozen scores is not validation and use exact agreement as the mechanism proof for
R1.4.

### N13 [M] A concession is present in Related Work and absent from the Limitations
`main.tex:207` Limitations lists: crude translation; τ measured against frozen ranks; decoder VLMs. It does not list
(a) τ is not sufficient across mechanisms, (b) τ's absolute level is template-conditional, (c) τ does not rank seeds
within a dataset. (a) is stated in Related Work but not as a limitation of the *results*; (b) is only the weak
"we do not claim template-invariance" (`related_work.tex:267–269`) without the measured 0.065–0.111 spread from
`outputs/a1_h_templates.json`; (c) is unmerged entirely.

### N14 [L] Two cells of the unmerged point-wise table are rounded the wrong way
`revision_additions.tex:36` predicted λ=2 reads **0.155** (JSON `0.1559` → 0.156) and `:37` measured λ=−2 reads **0.201**
(JSON `0.2002` → 0.200). `outputs/a1_tau_holdout.json::theory_vs_measured_tau.predicted_tau_exact_vs_measured_tau_5k`.
The headline residual claim (max 0.0019, mean 0.0013) is correct.

### N15 [L] The r = −0.827 retrieval correlation the paper leans on is one the project itself flags as unrecoverable
`main.tex:48` cites the prior study's "Distribution Gap predicts retrieval R@1 ($r=-0.827$)". `HANDOFF.md:78,98` records
that this value came from an n=81 subset mislabelled n=94 and that the generating script is lost with its selection
rule unrecoverable. It is a cited prior-work number rather than a new claim, but it is the sole quantitative support
for "the gap is right for retrieval", so the new paper inherits the weakness.

### N16 [L] Structural debris in the merged Related Work
`main.tex:48` (the legacy paragraph) now sits **after** §2.8 "What this paper claims and what it does not", so the
section ends by re-narrating §2.2/§2.6 material. It also duplicates the `chowers2026`/`grassucci2026` discussion that
`related_work.tex:100–128` already handles with more care.

---

## 4. Number audit — prose vs. the JSON it names (spot-checks I ran)

Verified correct (no action needed): frozen 59.3 / CG 0.82; λ=0.5 → 47.6 / τ 0.46 / CG 0.41; λ=1 → 32.0 / τ 0.29 /
CG 0.01; λ=2 → 13.6 / τ 0.15 / CG 0.45; orthogonal λ=1 → 42.2 (`a1_full_results.json`). Asymmetry table 31.9/45.1 and
13.5/38.3, τ 0.29/0.43 and 0.15/0.36 (`a1_text_surgery.json`). All 12 cells of Table 4 for OpenCLIP and SigLIP
(`a1_crossmodel_results.json`). Spectrum rows 58.8/0.761, 41.5/0.434, 40.3/0.440, 40.1/0.404, 42.6/0.435, 70.3/0.760,
78.6/0.615 (`a1_subspace_results.json`, `a1_e2b_e3b.json`). τ 0.9125 with p = 8.5e-11; cosine 0.872; CKA 0.755;
CG −0.082 (p = 0.69) (`a1_rr_e2_topk.json`, `a1_baseline_metrics.json`). Real checkpoints τ 0.791/0.750, top-1
58.8/58.6, full-FT τ −0.083/0.122/0.122 and 0.1/7.4/7.0 (5 k) / 0.1/4.1/3.5 (50 k) (`a1_tau_trajectory.json`,
`a1_e2b_e3b.json`, `imagenet1k_zs_50k_plain.json`). Trajectory CG 0.815→0.848, archived 0.93, τ 1.00→0.75 by epoch 3,
text-only τ→0.79. Prompt ensembles 60.1/60.3 and 36.9/36.5 (`a1_multitemplate.json`). Task spectrum 100 %/54 %/81 %
(`a1_full_results.json` R@1 0.1345 → 0.1645). R² 0.3712/0.3776, pooled ρ 0.9272, p 1.36e-12, CG ρ −0.2507
(`a1_tau_holdout.json`). Block 19's seed spreads (0.0002/0.0146/0.0149), nine-run ρ +0.85/−0.27, within-dataset
ρ −0.5/−0.5/+1.0, template ranges 0.0707–0.2967 and spreads 0.088–0.111, k-shift 0.104, k-specificity table, excess
+3.62 ± 1.41 with t-interval [2.72, 4.51], +4.72 ± 0.70 over nine runs, 86.0–99.7 % orthogonality, and block 16's
top-k table — all reproduced from `a1_h_seed_summary.json`, `a1_h_templates.json`, `a1_h_bootstrap.json`,
`a1_h_offset.json`, `a1_rr_e2_topk.json`.

**Discrepancies found** (the load-bearing ones are N5, N6, N11, N14 above; summarised here):

| Prose | JSON it names | Verdict |
|---|---|---|
| `main.tex:101` "τ above the curve's entire range … no finite offset is defined" | `a1_h_offset.json` (excess +0.48, +2.20, +0.54) | **false** |
| `main.tex:35,101` CGΔ = +0.114 for the archived both-position checkpoint | `a1_rr_e4_eval_archived.json` CG 0.8479 for that same checkpoint file (Δ = +0.033) | **unreproducible under the paper's own protocol, undisclosed** |
| `main.tex:101` excess +3.3…+5.5 | `a1_rr_summary.json` min 3.347 / max 5.4691 → ✔ | correct, but see N11 (other pipeline says +3.1…+4.6) |
| `main.tex:155` τ = 0.9125 (p = 8.5e-11) | `a1_rr_e2_topk.json` k=5: 0.9125, p = 8.478e-11 → ✔ | correct; provenance of the archived 0.9262 = k=10 is honestly reported in block 16 only |
| `main.tex:137` r = 1.000 for per-class shifts | `a1_baseline_metrics.json` r = 1.0, **p = 0.0**, n not stored | number correct; framing unsupported (R2.5) |

---

## 5. The three most dangerous remaining objections, and the minimal fix for each

### D1. The Results section asserts the opposite of its own table and of its own Related Work (R1.4, unfixed)
**Evidence.** `main.tex:112` "contracting each image toward its own class centroid **preserves order** and improves
accuracy to 78.6%"; `main.tex:117` Table 2 caption "class-aligned perturbations (P) **preserve order**"; versus
`main.tex:129` (τ = 0.615 for that row), `main.tex:123` (τ = 0.761 for the 58.8 % Gaussian row that the text calls
destructive), and `related_work.tex:334–341` ("**not a sufficient** statistic … contractions improve accuracy while
*lowering* the coefficient"). Both table rows re-read in `outputs/a1_subspace_results.json`.
**Why it is fatal.** It is the one complaint a reviewer can adjudicate from the paper alone, with no archive, no code
and no rebuttal letter — and the paper now *prints the counterexample while denying it*. It also makes the abstract's
mechanism sentence ("Preservation arises … from its alignment with class structure", `main.tex:25`) read as an
over-claim. A hostile reviewer will call this "the authors concede the point in Related Work and contradict the
concession in Results", which is exactly the R1 verdict.
**Minimal fix (3 sentences, no new experiments).** Delete "preserves order" from `main.tex:112` and from the Table 2
caption; replace with block 10's sentence (`revision_additions.tex:388–396`): along the destruction direction τ is a
*necessary* proxy, sufficiency across mechanisms does not hold, and class contraction is a *second, structurally
different* route to accuracy (true-class self-field +0.0435 ± 0.0288, `outputs/a1_theory_verify.json`) for which
frozen-rank τ is the wrong reference. Add one sentence to Limitations (`main.tex:207`) repeating it. Cost: minutes.

### D2. The headline number of the abstract is not reproducible with the paper's own evaluator, and the only full-FT
evidence is a reconstruction with a lost training script (N6, N7)
**Evidence.** `main.tex:25,35,101` quote CGΔ = +0.114 from `outputs/imagenet_zs/both_r8/results.json` (0.81883 → 0.93256),
while `outputs/a1_rr_e4_eval_archived.json` measures the *same checkpoint file*
(`outputs/imagenet_zs/both_r8/best_checkpoint.pt`) at `CG_flickr_val = 0.847886` against the same frozen 0.814736 —
Δ = +0.033. `main.tex:160` mislabels the 0.848 as "run-to-run variability". Separately,
`main.tex:66` claims the full-FT runs come "with archived weights", while
`outputs/imagenet_zs_rerun/*/results.json` record `原脚本已丢失` (script lost) and the seed-42 rerun diverges
(val_loss 4.11 → 7.88, R@1 0.2 %), and `zero_shot_eval.json` carries a hard-coded `paper_value: 7.38` that its own
measurement (0.13 %) contradicts.
**Why it is dangerous.** The paper's entire contribution is a *quantitative* claim about the gap, and it promises a
reproducibility archive (`main.tex:212`). One reviewer who opens the archive finds a factor-3.4 discrepancy on the
abstract's number and a "paper_value" constant inside an evaluation script. That is the profile of a paper whose
numbers are not trusted at all — after which the (correct) τ results are also discounted.
**Minimal fix.** Report the reproducible value: change `CGΔ=+0.114` at `main.tex:25,35,101` to `+0.033` under the shared
evaluator (or quote both with the protocol named — "legacy training-time logger +0.114, shared evaluator +0.033" — and
delete the "run-to-run variability" excuse), then re-run full-FT once with a checked-in script or mark those three rows
`archived, reconstruction-only` in the table and in `main.tex:66`. Cost: one number change plus one experiment already
scripted (`tools/clip_fullft_rerun.py` exists).

### D3. Eight of twelve complaints are answered in a file that will not be submitted, and the manuscript points at it
**Evidence.** `revision_additions.tex` is `\input` by nothing (verified by directory-wide search); `main.tex:101` and
`main.tex:155` footnotes cite "revision package, response to R1.6 / R2.2"; the three CZSL references exist nowhere in
`main.tex`/`related_work.tex`/`related_work_bibitems.tex`; R2.1's exactness argument, R2.2's ablation, R2.3's four
benchmarks, R2.5's reframing and R1.3's scope argument are all package-only. The abstract's orphan fragment
(`main.tex:25`, N4) is visible proof that the merge stopped halfway.
**Why it is dangerous.** The most likely editorial outcome is not a scientific rejection but a *process* rejection:
a resubmission whose answers are invisible, whose manuscript references an unavailable document, and whose abstract
contains an editing stub, will be returned (or desk-rejected as premature) before the first substantive review round.
**Minimal fix.** One mechanical merge session. `revision_additions.tex` is already LaTeX-clean: I confirmed it has
**no label collisions** with `main.tex`+`related_work.tex` and that all 23 of its cross-references resolve (to itself or
to existing `main.tex` labels), so it can go in as an appendix/extension section with only numbering changes. Then:
convert block 15's inline CZSL entries into `\bibitem`s, delete both "revision package" phrases, fix `main.tex:112/117`
(D1), fix `main.tex:101`'s offset claim (N5), correct the `CGΔ` (D2) and re-sync or withdraw `main_zh.tex` (N3).
Estimated effort: 1–2 days, no new compute except the optional full-FT re-run.

---

## 6. Verdict

**Would this survive review at a Q3 journal? Not in its current state — but the science would, after a merge.**

The underlying contribution is real and, on the evidence I checked, sound: a controlled *intervention* (exact
translation of the image cluster) that decouples gap magnitude from zero-shot accuracy, replicated across three
pretrained families with all twelve cross-model cells matching their JSON to the last printed digit; the reviewer's
"r = 1.0 is suspicious" objection is pre-empted by honest cross-family held-out evidence (R² = 0.371/0.378, pooled
ρ = 0.927); and the revision's new experiments (top-k ablation, four further benchmarks, non-Flickr30k checkpoints,
template/k/seed sensitivity) are genuinely responsive and — in every case I re-computed — correctly reported. But the
*submitted* document is a half-merged artifact. Two of twelve complaints are answered in it, five are answered only in a
file it never includes yet cites to the reader twice, three (R2.3, R2.4, R2.1) are simply absent, and R1.4 — the
complaint a reviewer can verify from the page — is actively contradicted by the Results section
(`main.tex:112`/`:117` vs Table 2's τ = 0.615 and `related_work.tex:334–341`), which together with the abstract's
orphaned fragment (`main.tex:25`), the unreproducible headline CGΔ = +0.114 (abstract vs
`a1_rr_e4_eval_archived.json`), the falsified "no finite offset is defined" claim (`main.tex:101` vs
`a1_h_offset.json`), the reconstruction-only full-FT evidence, and a Chinese mirror that still asserts every retracted
claim, is more than enough for a "reject / major revision — the submitted version does not reflect the revision
described" decision. My prediction for the current files: desk-return or major revision at MTA, with the negative
outcome driven by process and internal consistency rather than by the idea. My prediction after the merge session in
D3 plus the three fixes in D1/D2: a defensible accept-with-minor-revision at MTA, because none of the remaining defects
is a defect of evidence — they are defects of packaging.

---

## 7. Limitations of this review (so the next reader can weigh it)

* I verified every number reproduced above against the cited `outputs/**` JSON, and the merge status by
  `\input`/label/search across `paper_a1/`. I did **not** re-run any model or recompute any statistic from
  embeddings; where a JSON could itself be wrong and self-consistent, I would not have caught it.
* I did not verify the 40 new bibliography entries against publisher records (the package claims Crossref checks for
  the three CZSL entries, which I could not inspect because they are prose-only). I did verify that every `\cite` key
  in the submission resolves and that no `\bibitem` is orphaned (53/53).
* `main_zh.tex` is treated as a submission-grade artifact because `main_zh.pdf` exists alongside it; if it is only an
  internal translation, N3 downgrades from [H] to a housekeeping note — but it should then not be shipped.
* The `outputs/` tree contains uncommitted modifications to `a1_class_aligned/**` and `a1_tau_trajectory.json`
  (`git status`), i.e. result files were edited after the fact. I verified the *current* contents are consistent with
  the manuscript's numbers, but I could not audit what changed, when, or why — which is itself a provenance gap the
  replication archive should address.
