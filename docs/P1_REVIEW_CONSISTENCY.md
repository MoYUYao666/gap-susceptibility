# P1 — Independent adversarial review: internal consistency and claim strength

**Manuscript under review**: "Protect, Don't Perturb: Cross-Modal Alignment under PEFT of Vision-Language
Models", Hongrui Wan (sole author), *Pattern Recognition*, MS **PR-D-26-10149**.

**Scope of this round.** Source is `paper/main_nn.tex` + `paper/sections/*.tex`; companion submissions are
`paper/cover_letter.tex`, `paper/cover_letter_zeroshot_correction.tex`, `paper/highlights.tex`,
`paper/title_page.tex`, `paper/declaration.tex`. The artefact of record is the compiled
`paper/main_nn.pdf` (37 pages, build stamp 2026-08-22 13:10). Read-only: **no file under `paper/`,
`outputs/`, `src/`, `tools/` or `.worktrees/` was created or modified**; this report is the only file written.

**Method.** For every load-bearing claim I traced: (a) source `.tex` line → (b) the same sentence in the
compiled PDF (page number from `pdftotext -layout`, printed page numbers verified against the footer) →
(c) the archived JSON / code that the claim depends on. `docs/P1_eval_audit.md`'s finding is treated as known
and is *not* re-derived; what is checked here is whether its three prescribed disclosures landed. Claims
resting only on `docs/*.md` or `paper/REVIEW_DEFENSE.md` are treated as claims, not evidence — and
`REVIEW_DEFENSE.md` is checked for objections that exist only there.

**Build check (precedent honoured).** `paper/main_nn.log`: `Output written on main_nn.pdf (37 pages,
2611229 bytes)`; no undefined reference/citation warnings. Spot-checks of tex→PDF correspondence all pass:
abstract exception list (PDF p.1 = `main_nn.tex:44-45`), Intro exception list (PDF p.4 = `introduction.tex:15`),
n=81 correlation table (PDF p.14 = `experiments.tex:168-172`), ImageNet table (PDF p.17 =
`experiments.tex:226-229`), catalogue rows (PDF pp.28-30 = `supplementary.tex:28-167`). **No stale-sentence
discrepancy of the sibling-manuscript kind exists here.** The PDF is stale in a different and more serious
way — see F1.

---

## 1. Findings, ordered by severity

Numbers in **[brackets]** are this report's finding ids.

### 1.1 Must fix before this manuscript can be defended

---

**[F1] — The submitted PDF does not contain the corrections its own second cover letter promises; the cover
letter and the manuscript now state different zero-shot protocols and different numbers.**

*Evidence chain.*
- `paper/cover_letter_zeroshot_correction.tex:37` — "the attached manuscript corrects these values and the
  associated claims"; `:42` — "frozen **59.37%**, text-only LoRA **58.76%** (−0.6pp), both-position LoRA
  **59.67%** (+0.3pp), full fine-tuning **0.13%** (−59.2pp). The measurements use the single-template protocol
  (… ) on a **14,288-image ImageNet validation subset**, stated in the table footnote";
  `:51` — "The revised manuscript was re-compiled (**37 pages**, no undefined references)".
- The compiled PDF (37 pages) instead carries the *earlier* values: `paper/sections/supplementary.tex:127-130`
  = PDF p.17 `Frozen 59.28% / Text-only 58.66% / Both 59.67% / Full fine-tuning 2.6%`, and
  `supplementary.tex:173` footnote `^e` = PDF p.17 caption: "on the **full 50,000-image** ImageNet
  validation set … the full-FT row reports means over 3 retrained seeds (CGΔ range +0.26–+0.67; Top-1 range
  0.1–4.1%)".
- Ground truth in the archive: `outputs/imagenet1k_ckpt_check.json` (`n_images: 14288`, `frozen 59.37`,
  `text_only_r8 58.76`) and `outputs/imagenet_zs_rerun/full_ft/results.json:17-22`
  (`"zero_shot_imagenet1k": {"synset_single_template": 0.13, …, "n_images": 14288}`) support the *cover
  letter*; `outputs/imagenet1k_zs_50k_plain.json` (`frozen 59.28 / text_only_r8 58.66 / both_r8 59.67 /
  full_ft_s42 0.13 / s123 4.09 / s999 3.54`) supports the *paper*.
- So the two artefacts describe the **same four rows measured under two different protocols on two different
  evaluation sets** (50,000 images vs a 14,288-image subset) and give two different full-FT results
  (mean 2.6% vs 0.13%).

*Why it matters.* A reviewer holding both documents sees a manuscript that contradicts the correction letter
that introduced it. The Table 7 caption asserts a protocol that was not used for half of its own rows
(full-FT `CGΔ +0.40` and Top-1 range `0.1–4.1%` come from the 50k plain run; the `CGΔ +0.26–+0.67` in the
supplementary footnote comes from the 14,288-image rerun — `outputs/imagenet_zs_rerun/full_ft_s123/centroid_gap.json`
`cg_delta 0.2609`, `full_ft_s999/centroid_gap.json` `cg_delta 0.2672`, `full_ft/centroid_gap.json` `cg_delta 0.6646`).
The abstract's "mean 2.6% over 3 retrained seeds" (`main_nn.tex:46`, PDF p.1) is therefore a number the
authors' own latest verification disowns.

*Fix.* Pick one protocol, re-measure the four rows under it, and make Table 7's caption, the supplementary
footnote `^e`, §4.10, Fig. 6, the abstract and the correction letter agree. State the evaluation-set size
explicitly in every place a zero-shot number appears.

---

**[F2] — The required disclosure of the training convention (audit action 1) is absent from the submitted
manuscript, and the paper asserts the opposite of what the code does.**

*Evidence chain.*
- Audit requirement: `docs/P1_eval_audit.md:33-35` — disclose that "LoRA adapters on attention projections;
  the embedding and LayerNorm parameters remain trainable".
- Code: `src/peft_methods.py:137-138` `get_peft_params` returns `[p for p in model.parameters() if
  p.requires_grad]`; `src/trainer.py:243-244` uses it as the optimiser parameter list; `src/lora.py:39-41`
  freezes **only** the replaced `nn.Linear` (and its bias). Nothing else is frozen in the LoRA path
  (`src/trainer.py:144-162` has no global freeze). Archived proof that non-LoRA parameters were live:
  `outputs/imagenet_zs/text_only_r8/results.json:44` `"n_trainable_params": 6500352` (a text-side LoRA-only
  count is ~2.4e5 and full text encoder + LoRA is 14,451,712); every `flickr30k/rq2_text_only` run records
  `n_trainable_params: 14517…` (e.g. `outputs/flickr30k/rq2_text_only/results.json`, `outputs/master_results.json`
  histogram: 22 records with `n_trainable_params = 145170177` for nominally "LoRA" runs).
- Manuscript: the compiled PDF contains **0** occurrences of `LoRA adapters`, `LayerNorm`, `layernorm`,
  `embedding layers`, `trainable parameters` (in a setup sense), `reconstruct`, `archived`, or
  `hyperparameter`; `Methodology` §3.3 (`paper/sections/methodology.tex:18-20`, PDF p.8) states only
  "batch size 128, 10 epochs, AdamW with learning rate 1e-4, single NVIDIA RTX 4060 GPU" and never lists
  trainable parameter groups. `paper/sections/visual_fragility.tex:8-12` and
  `paper/sections/supplementary.tex:259` instead assert the opposite of the code path: "(A) … text-only has
  **zero vision-side updates**".
- The `zero vision-side updates` figure is an artefact of the checkpoint format, not of the model:
  `paper/scripts/weight_svd_analysis.py:54-60` computes `ΔW` **only from `ckpt["lora_state_dict"]`**, and
  `src/trainer.py:893-901` `_save_checkpoint` stores `lora_state_dict` and nothing else (docstring: "仅LoRA权重，
  不含冻结的完整模型"). For a text-only run there is no vision entry in that dict, so the plotted vision-side
  update is zero by construction.

*Why it matters.* One of the two headline numbers of the paper (the 0.6 pp zero-shot preservation) and the
entire "weight-level evidence" panel rest on an unreported, non-standard training convention. As written, a
reader who reproduces "LoRA" from the paper will not reproduce the experiment.

*Fix.* Add one explicit paragraph in §3.3 (Setup) and one footnote to the Fig. 8 caption: name the exact
parameter groups in AdamW, state that checkpoints archive LoRA tensors only, and relabel the Fig. 8(A) panel
as "archived LoRA updates" rather than "updates".

---

**[F3] — Audit action 2 (zero-shot numbers come from reconstructed LoRA-only models) is not disclosed
anywhere in the submitted manuscript; the only place it surfaces is the audit file.**

*Evidence chain.*
- Requirement: `docs/P1_eval_audit.md:36-37`.
- `paper/scripts/zeroshot_extra.py:114-141` builds each evaluated model from scratch
  (`CLIPModel.from_pretrained(...)`, `apply_lora_to_model(...)`) and **never loads a checkpoint** — this is the
  script that produced the DTD/Food101 numbers used in `supplementary.tex:173` footnote `^d`
  (`outputs/dtd_food101_zs_check.json:20-31`, whose `results.*` values 42.87/43.30/43.03/82.32/81.58/81.63 are
  the footnote values verbatim, while its own `paper_footnote_values` block records a *different* older set
  43.27/42.53/80.6/79.73).
- Every mention of zero-shot in the PDF is silent on provenance: `main_nn.tex:46` (abstract, PDF p.1),
  `introduction.tex:27` (PDF p.5), `experiments.tex:215-229` (PDF p.17), `supplementary.tex:173`
  (PDF p.29). The grep counts for `checkpoint` in the PDF are 2, and both refer to the full-FT row
  ("original checkpoint not saved") — not to the LoRA rows.

*Why it matters.* The paper's second-most-quoted number ("limits zero-shot degradation to 0.6 percentage
points") is presented as a property of the LoRA model that was trained. It is a property of a *reconstructed*
model whose embedding/LayerNorm parameters were reset to pre-training. This is exactly the kind of protocol
detail Pattern Recognition reviewers reject on when they discover it themselves.

*Fix.* One sentence in §4.10 and one in the Table 7 footnote.

---

**[F4] — The abstract's headline exception list omits exceptions that the paper's own data contain, and the
Discussion's list of the same exceptions is inconsistent with the table it cites.**

*Evidence chain.*
- Abstract (`main_nn.tex:44-45`, PDF p.1): "…across LoRA, Adapter, BLIP-1, and ViT-L configurations, with a
  **few exceptions (e.g., SigLIP both-position and ViT-B all-layer text-only)**."
- Introduction (`introduction.tex:15`, PDF p.4): "…one of a few exceptions together with SigLIP both-position,
  **Adapter vision-only**, and ViT-B all-layer text-only (CGΔ = +0.237)".
- Discussion (`discussion.tex:6`, PDF p.20): "…with a few exceptions (**COCO both-position, SigLIP
  both-position, Adapter vision-only, and ViT-B all-layer text-only**; Table~\ref{tab:cross_val})" — note the
  table it points at (`supplementary.tex:222-234`, PDF p.31) has no `ViT-B` row at all, and no `SigLIP` or
  `ViT-B` column.
- Data: `outputs/phase1/adapter_d16_vis/results.json` → CGΔ −0.0834 vs `adapter_d16_text` −0.0462;
  `outputs/siglip/s4_siglip_lora_both/results.json` → +0.058 vs `s4_siglip_lora_text_only` +0.067;
  `outputs/siglip/s3_siglip_lora_r8` → +0.078; `outputs/coco/rq2_both_coco` → −0.052 vs `rq2_text_only_coco`
  −0.041; `outputs/layered_ft_results.json` "Text-only" → 0.8137→1.0508 (+0.237). So COCO both-position and
  Adapter vision-only are visual **defeats** of the text-only claim in the paper's own headline dataset and
  headline method, and Adapter vision-only is the single largest gap reduction in the entire Adapter set.
- Neither the abstract nor the Introduction concedes **COCO both-position**; the Discussion does. The
  correction letter claims to have "disclosed the ViT-B all-layer text-only configuration (CGΔ = +0.237) in
  the exception lists of the Abstract, Introduction, and **Discussion**"
  (`cover_letter_zeroshot_correction.tex:46`) — the Discussion list in the built PDF (p.20) does contain it,
  and the Abstract/Intro do, so that item did land; but the *three-way* lists still do not agree with each
  other, and the strongest counterexamples (COCO, Adapter vision-only) never reach the paper's most-read
  sentence.

*Fix.* Normalise one exception list, use it verbatim in abstract, introduction, discussion and conclusion,
and add the Adapter/CG magnitudes so the reader can judge how large the exceptions are.

---

**[F5] — The conclusion does not carry the exception list at all and states the exception-ridden finding
without qualification, and its 5-seed significance claim contradicts the experiments section.**

*Evidence chain.*
- `conclusion.tex:6` (PDF p.25): "…we find that text-only fine-tuning preserves cross-modal alignment **in
  most configurations**, while joint-modality fine-tuning and full fine-tuning systematically degrade it. The
  effect is robust across LoRA, Adapter, BLIP-1, and ViT-L, and is statistically significant across five
  random seeds ($p < 0.01$). Text-only LoRA largely contains the Centroid Gap increase compared to
  $+0.199$ for full fine-tuning." No exceptions are named; contrast `discussion.tex:6`, which names four.
- The robustness sentence is false as written for Adapter: `outputs/phase1/adapter_d16_vis` −0.0834 is better
  than `adapter_d16_text` −0.0462. "Robust across … Adapter" is the exact opposite of the Adapter result.
- Significance level: the intro commits to `p < 0.001` for the full-FT 5-seed comparison
  (`introduction.tex:13`, PDF p.3-4) and `supplementary.tex:214` states "All pairwise comparisons between
  text\_only and full\_ft are significant at $p < 0.001$ (Welch's $t$-test)". The conclusion's `p < 0.01`
  (`conclusion.tex:6`) is a different threshold for the same claim.
- The `+0.199` in the conclusion is the *single-run* Flickr30k full-FT value
  (`outputs/flickr30k/baseline_full_ft/results.json`: 0.8185→1.0179, +0.1994). The five-seed mean is
  **+0.191 ± 0.008** (`outputs/flickr30k_seeds/summary.json` `baseline_full_ft.cg_delta_mean
  0.1906357…`; recomputed from the five `results.json` files: +0.1865, +0.1791, +0.1903, +0.1985, +0.1987 →
  mean +0.1906). The single-run value is the maximum of the five seeds. Using it in the conclusion — and in
  the abstract's "24 %" (see F6) — while simultaneously invoking the 5-seed suite is a selective report.

*Fix.* Restate the conclusion's contribution 1 with the same exception list as the Discussion, quote the
5-seed mean (+0.191 ± 0.008) rather than the best seed, and align the significance threshold.

---

**[F6] — "Full fine-tuning increases the CG by 24%" is a single-seed, one-dataset relativity presented as the
abstract's headline effect size, and the same abstract sentence mixes two different measurement regimes.**

*Evidence chain.*
- `main_nn.tex:45-46` (PDF p.1): "Full fine-tuning increases the Centroid Gap by **24%** and collapses
  zero-shot accuracy to near-chance levels (mean 2.6% over 3 **retrained seeds**, vs. 59.3% frozen), while
  text-only LoRA largely contains the gap increase and limits zero-shot degradation to 0.6 percentage points."
- The 24% is `+0.1994 / 0.8185` computed from one run (`outputs/flickr30k/baseline_full_ft/results.json`),
  i.e. `0.1994/0.8185 = 24.4%`. The 5-seed mean gives `0.1906/0.8185 = 23.3%`; the worst seed gives 21.9%.
  The intro repeats it verbatim (`introduction.tex:13`, PDF p.4) with "18% on COCO"
  (`outputs/coco/baseline_full_ft_coco`: +0.1940/1.0530 = 18.4%).
- Frozen reference: `main_nn.tex:46` says "59.3% frozen"; Table 7 (`experiments.tex:226`) and the archive
  (`outputs/imagenet1k_zs_50k_plain.json`) say 59.28%. 59.28 % does not round to 59.3 % (it rounds to 59.3
  only at two significant figures).
- "0.6 percentage points" is true only on ImageNet. On Food101 both-position degrades by 0.69 pp
  (frozen 82.32 → both 81.63, `outputs/dtd_food101_zs_check.json:26-30`) versus text-only 0.74 pp (81.58).
  The abstract's single number therefore hides the one benchmark where text-only does *not* win.

*Fix.* Report the 5-seed mean and its spread, state that "24 %" is the Flickr30k single-run relative change
(5-seed: 23 %), and give the zero-shot figure as a range across ImageNet/DTD/Food101 or name the benchmark.

---

**[F7] — The n=81 correlation analysis behind the paper's third contribution is declared irreproducible in
the authors' own figure-generating script, and no archived subset reproduces its numbers.**

*Evidence chain.*
- `paper/scripts/generate_figures.py:72-77` (comment written 2026-08-14): "标注值强制从 verified 档案读取
  (outputs/analysis/correlations.json) … **生成 n=81 相关分析的选择规则随原脚本丢失 … n=81 子集无法精确重建**"
  ("the selection rule that generated the n=81 correlation analysis was lost with the original script … the
  n=81 subset cannot be exactly reconstructed"), and for Fig. 2: "请勿重生成 fig2" ("do not regenerate fig2").
- `paper/figures/fig2.png` (read directly) annotates the scatter with `r = -0.827  n = 81` and
  `r = -0.683  n = 81`; the archive it was told to trust, `outputs/analysis/correlations.json`, holds
  `-0.8274 / -0.6832 / partial -0.8069` with `n: 81`, but no script in the repository produces it
  (`grep` for `all_metrics|analysis/correlations` finds only the comment above).
- The nearest reproducible datasets give different numbers: `outputs/analysis/all_metrics.csv` (89 rows)
  → DG r = −0.820, CG r = −0.676, partial = −0.790, DGΔ = +0.001, CGΔ = +0.019 (p = 0.861);
  `outputs/master_results.json` (94 records with `dg_final` and `R1`) → DG r = −0.8152.
- The two change-score rows in Table 5 (PDF p.14: `DGΔ → R@1 r = −0.042, p = 0.713`; `CGΔ → R@1 r = +0.012,
  p = 0.915`) are attributed to the same n = 81 set but reproduce in **neither** of the recoverable sets
  (89-row set: +0.001 and +0.019, p = 0.861).

*Why it matters.* Table 5 and Fig. 2 are the evidence for "DG predicts retrieval", which is the basis of the
DG-monitoring contribution. With the sampling rule lost, the numbers are unfalsifiable as submitted.

*Fix.* Re-run the correlation analysis with a documented, scripted exclusion list over `outputs/**/results.json`,
report the new n and r (the qualitative conclusion survives: every recoverable subset gives r between −0.79
and −0.86), and update Table 5, Fig. 2, the abstract, §4.6, §4.9, §5.4, §6.5 and the conclusion.

---

### 1.2 Should fix

---

**[F8] — The independence/overclaim objection the paper raises against itself is *already answered* by
numerical work in the repository, but the answer is not in the manuscript; the manuscript instead promises
the analysis to future work.**

*Evidence chain.*
- Manuscript (`discussion.tex:36`, PDF p.24): "Our correlation analysis treats each experiment as an
  independent observation; experiments with shared configurations (e.g., different seeds) are not fully
  independent. A mixed-effects model or clustered standard errors **would** provide a more conservative
  estimate, and we **encourage future work** to adopt such approaches."
- Existing result, in the same repository: clustered bootstrap by configuration over
  `outputs/master_results.json` yields **naive r = −0.8152** and **clustered r = −0.8185, 95 % CI
  [−0.867, −0.759], 0/10,000 resamples ≥ 0** over **94 experiments in 79 clusters** (recomputed here from
  `outputs/master_results.json`; identical to `paper/REVIEW_DEFENSE.md:44-52` and `:113-114`, which label it
  "Paper 1 的核心防御武器" — the paper's core defensive weapon).
- A later, differently-scoped run exists too (`outputs/clustered_bootstrap_dg_r1.json`: 98 experiments,
  14 clusters, r = −0.8474, CI [−0.936, −0.709], which itself notes it "replaces the earlier reported
  −0.819 / 94 experiments / 79 clusters figure, which had no local source script").
- Neither number appears anywhere in the PDF (0 occurrences of `bootstrap`, `0.819`, `0.815`).

*Why it matters.* This is the single highest-value sentence the authors could add, and it converts a
self-declared weakness into a robustness result. Reviewers of correlational claims test exactly this.

*Fix.* Add two sentences with the clustered-bootstrap number, the cluster count and the CI to §5.2 and to
§4.6, and delete the "we encourage future work" framing.

---

**[F9] — Table 4 attributes an Adapter mean (CGΔ −0.100, mean R@1 0.173) to the Adapter method that no
archived Adapter experiment set produces; the number comes from a near-random-retrieval run set, and the
LoRA-vs-Adapter ANOVA that rests on it is unreproducible.**

*Evidence chain.*
- `experiments.tex:128-144` (Table 4, PDF p.13): `Adapter | −0.100 | 0.173 | d=64, text-only`;
  `experiments.tex:144` (PDF p.13-14): "One-way ANOVA across PEFT methods (LoRA vs. Adapter, using the
  correctly matched Adapter group): F = 13.37, p = 5e-4 … Adapter attains substantially larger gap reduction
  on average (mean CGΔ = −0.100 vs. −0.004 for LoRA)".
- The −0.100 / 0.173 pair is the mean over the seven `outputs/phase1/adapter_*` runs
  (`adapter_d4_text` −0.069/0.033, `d8` −0.041/0.036, `d16_text` −0.046/0.072, `d32` −0.130/0.458,
  `d64` −0.217/0.574, `d16_both` −0.040/0.002, `d16_vis` −0.083/0.036; computed mean R@1 = 0.173).
- The project's own cross-method table for the same construct reports something different:
  `outputs/cross_method/paper_tables.md:9` `adapter | −0.0472 | 0.6228 | 5` and
  `outputs/master_results.json` `cross_method_summary.efficiency.adapter` = `{n_experiments: 5, cg_delta_mean:
  −0.0472, R1_mean: 0.6228, cg_delta_best: −0.0808, sample_experiments: ["flickr30k/alpha_16", …
  "flickr30k/alpha_64"]}` — i.e. the *archived* "Adapter" aggregate is built from five **LoRA α-sweep**
  experiments (`n_trainable_params` ≈ 145.2 M) and its `cg_delta_best` (−0.0808) is a LoRA run.
- No script in the repository computes F = 13.37 / p = 5e-4. The value was introduced by the authors' own
  patch script `tools/audit/fix_paper1_round3.py:19-23`, which replaced an earlier, opposite conclusion
  ("F = 2.17, p = 0.146 (not significant)") together with the Table 4 Adapter row
  (`'Adapter & $-$0.047 & 0.623 & $d$=64, text-only'` → `'Adapter & $-$0.100 & 0.173 & …'`).
- The Adapter evidence cannot carry a "text-only is a general PEFT strategy" conclusion: the only
  text-vs-both Adapter contrast is at d = 16 and both arms retrieve at chance (`adapter_d16_text` R@1 0.072
  vs `adapter_d16_both` 0.002), while at d = 32 and d = 64 — the only Adapter settings with real retrieval
  (0.458, 0.574) — no both-position counterpart was run. The vision-only Adapter beats the text-only Adapter
  at the same d (0.036 vs 0.072 exclusion aside, −0.083 vs −0.046 on CGΔ).

*Fix.* Recompute Table 4 from a documented Adapter-only set, drop or re-derive the ANOVA, report the d = 32 /
d = 64 text-vs-both arms (or state that they were not run) and restrict the "general PEFT strategy" claim to
the configurations actually tested on both sides.

---

**[F10] — The zero-shot generalisation claim is contradicted on one of the two benchmarks it rests on, and
the source numbers are not the ones the footnote implies.**

*Evidence chain.*
- `introduction.tex:27` (PDF p.5): "Zero-shot preservation generalizes: on DTD and Food101, text-only and
  both-modality stay within ±0.8 percentage points of the frozen baseline…".
- `supplementary.tex:173` footnote `^d` gives Frozen DTD 42.87 → Text-only 43.30 (**+0.43**), Both 43.03
  (+0.16); Frozen Food101 82.32 → Text-only 81.58 (**−0.74**), Both 81.63 (−0.69). So the claim conflates a
  gain and a loss into a symmetric "±0.8", and it is on **Food101** specifically that both-position
  degrades more than the text-only variant the abstract credits with preservation.
- Those numbers exist in the archive (`outputs/dtd_food101_zs_check.json:20-31`) — but that same file's
  `paper_footnote_values` block preserves a *different* older set (43.27 / 42.53 / 80.6 / 79.73) that matches
  the un-checkpointed `outputs/zeroshot_extra.json` produced by `paper/scripts/zeroshot_extra.py`. Two
  protocols for the same footnote, one of them the known-flawed random-init run (F3).
- Fig. 12's caption (`supplementary.tex:291`) repeats "All fine-tuned variants stay within 0.8 percentage
  points of the frozen baseline" — the same conflation.

*Fix.* Report both benchmarks with signs, state the evaluation set and the checkpoint provenance, and note
explicitly that on Food101 both-position is the more preservative configuration.

---

**[F11] — The "causal evidence" claim is not supported by the effective-rank artefact, which shows the
opposite trend, and the retrieval models behind two of the three "causal" probes retrieve at chance.**

*Evidence chain.*
- Claims: `main_nn.tex:52-53` (abstract, PDF p.1) "provide **direct causal evidence** through noise
  sensitivity, gradient analysis, and effective rank tracking"; `introduction.tex:25` (PDF p.4) "effective
  rank tracking **confirms** text-only preserves visual embedding geometry"; highlights item 4
  (`highlights.tex:11`) "Causal evidence for Visual Fragility: noise sensitivity, gradient, effective rank".
- Artefact: `outputs/effective_rank_tracking.json`. Frozen image effective rank `vis_L0` 9.4256 →
  text-only runs 9.3861 (**unchanged**), 6.8279, **6.1639**, 7.0211 — i.e. the largest text-only runs lose
  ~35 % of visual effective rank while the text side is preserved exactly (Frozen txt_L11 9.8775 = text-only
  run 1 txt_L11 9.8775). The supplementary text asserts the opposite
  (`supplementary.tex:173` footnote `^c`: "text-only preserves rank") and there is a `null` entry inside the
  `text-only` array, so the four entries are not four repeats of one run.
- Model identity in the causal probes: `paper/scripts/noise_sensitivity.py:63-68` injects noise into
  transformer block weights only; the R@1 baseline used is 0.705, which matches
  `outputs/flickr30k/rq2_both/results.json` R@1 (0.700) rather than the text-only run (0.627) — the
  "protection" probe is evaluated on a both-position model. `flickr30k/rq1_rank4` (the seed-42 arm of the
  5-seed suite) retrieves 0.673, so the quantitative picture of what is being perturbed is not stated in the
  manuscript at all.
- GSNR (`outputs/gsnr_results.json`): `vis_grad_norm 0.4510`, `txt_grad_norm 0.3104`, ratio **1.45** (the
  paper's "1.5×", `supplementary.tex:284`), and `text_final_loss 4.154` vs `both_final_loss 0.561`
  (`supplementary.tex:173` footnote `^b`, `:284`). Larger vision gradients and a 7.4× higher text-only
  training loss are as consistent with "text-only merely fits the task less" as with "the text encoder is
  robust"; the manuscript reports both numbers but never mentions this competing reading.

*Fix.* Either (a) drop "causal"/"confirms" from abstract, intro and highlights for the effective-rank and
gradient legs and state what each probe actually shows (perturbation response, gradient magnitude,
rank-under-training), or (b) re-run the effective-rank tracking on the text-only checkpoint with the
embedding/LayerNorm update path made explicit, and report the rank loss. Rename the "causal evidence"
contribution as "interventional and correlational evidence".

---

**[F12] — Table 1's `Best CGΔ` column mixes two different rankings inside single categories, and the
"Route C/D/E" numbering does not divide the way the text says.**

*Evidence chain.*
- `experiments.tex:15-52` (Table 1, PDF p.11). `Adapter 7 | −0.217 | 0.574`: both cells are the d = 64
  text-only run (`outputs/phase1/adapter_d64_text`). `BLIP-1 7 | −0.476 | 0.175`: both cells are rank-4
  (`outputs/blip2/b3_blip2_lora_r4`, R@1 0.1750). `Route C 8 | +0.181 | 0.671`: **the two cells come from
  different runs** — +0.181 is `c3_gapinit_text_r1` (R@1 0.630) and 0.671 is `c3_gapinit_text_r4`
  (CGΔ +0.193). `SigLIP 5 | +0.058 | 0.479`: +0.058 is `siglip_both`, 0.479 is `siglip_lora_r4`. `ViT-B
  layered FT 5 | −0.009 | 0.713`: −0.009 is vis-L2, 0.713 is vis-L4.
- `experiments.tex:179` (PDF p.14): "We test **three** enhanced strategies over **13** additional
  experiments: Gap-Regularized Loss (Gap-Reg), Gap-Init with text-only, α Annealing, and strategic
  combinations" — four items are listed, and Route C alone contains 8 runs
  (`supplementary.tex:99-106`). Route C + D + E = 16 (`supplementary.tex:96` header: "Route C/D/E Enhanced
  Strategies --- 16 experiments"), so "13" is wrong for any partition of that section.
- Section §4.7's heading (`experiments.tex:177`) is "Enhanced Strategies (Route C/D)" while the same
  subsection discusses Route E (`experiments.tex:181`).

*Fix.* Define once whether each category's cell is "best-CGΔ run" or "best-R@1 run", and correct the counts
in §4.7 to match the 16-row catalogue section.

---

**[F13] — Figures 2 and 3 carry each other's captions, and the caption printed for Figure 7 promises a
"variance component" verification that the figure does not show.**

*Evidence chain.*
- Numbering is internally consistent in the compiled PDF (`paper/main_nn.aux`: `fig:evolution`=1, `fig:position`=2,
  `fig:ablation`=3, `fig:dg_predictor`=4, `fig:dges`=5, `fig:zeroshot`=6, `fig:normcheck`=7, … 14), so the defect
  is not numbering — it is that the two figures in §4.3 (`experiments.tex:90-95` and `:101-106`) are swapped.
  The caption printed as **Figure 2** reads "Cross-validation: text-only yields the smallest alignment
  degradation in the vast majority of settings…" (`experiments.tex:93`) but the file it includes,
  `paper/figures/fig3.png` (2290×940 px, read directly), is the **ablation** bar chart produced by
  `paper/scripts/generate_figures.py:93-112` (`def fig3(): … fig,ax=plt.subplots(figsize=(10,5))`, whose
  hardcoded data list is the five position pairs). The caption printed as **Figure 3** reads "Ablation of LoRA
  scaling factor α (left) and target modules (right)…" (`experiments.tex:104`) but the file it includes,
  `paper/figures/fig2.png` (2890×1390 px, read directly, annotated `r = -0.827 n = 81` / `r = -0.683 n = 81`),
  is the DG-vs-R@1 scatter from `generate_figures.py:63-91` (`def fig2(): … fig,(ax1,ax2)=…`) — which the
  manuscript also wants as Figure 4 for §4.6 (`experiments.tex:151-156`). So the ablation chart is captioned
  as the cross-validation figure, and the correlation scatter the paper says is Figure 4 is printed as
  Figure 3, in the wrong section, with the ablation caption underneath it.
- Caption vs content, Figure 7: the caption printed for it reads "DG is not a redundant proxy for CG. Verified
  by **partial correlation and independent variance component**" (`experiments.tex:248`).
  `paper/figures/fig7.png` (read directly) is a three-bar chart of |r| = 0.827 (DG→R@1), 0.683 (CG→R@1), 0.807
  (DG partial, control CG) — it contains **no variance-component panel**. The manuscript sentence that cites it
  asserts the missing panel: "the variance component $\sqrt{G_D^2-G_C^2}$ independently correlates with \Rk{1}
  (Figure~\ref{fig:normcheck})" (`experiments.tex:243`, PDF p.18), and supplementary §E repeats it as
  "**Construct validity**: … the variance component independently correlates with \Rk{1}"
  (`supplementary.tex:249`, PDF p.31). No numeric value for that correlation appears anywhere in the paper or
  in `outputs/analysis/correlations.json` (which holds only CG, DG, both deltas and cosine-separation), so
  none of the three self-described "non-triviality checks" can be evaluated by the reader.
- `cover_letter.tex:47` states that Fig. 7 was "regenerated from the verified correlation values
  ($r=-0.827/-0.683/-0.807$); one unsupported bar removed". The removal is what created this gap: the caption
  and both sentences still claim the removed check.

*Fix.* Swap the `fig3.png` / `fig4.png` includes (or the two captions) in §4.3, and either show the
variance-component correlation as a fourth panel with its number or delete the claim from
`experiments.tex:243` and `supplementary.tex:249`.

---

**[F14] — The ViT-B layering result contradicts the paper's central message and is presented as support for
it.**

*Evidence chain.*
- `introduction.tex:23` (PDF p.4) and `discussion.tex:27` (PDF p.23) present Text+Vis-L1 as the best
  overall trade-off: "CG remains at 0.814 (same as frozen) while R@1 reaches 0.700, outperforming both pure
  text-only (R@1=0.427) and full both-modality (R@1=0.510)".
- Artefact: `outputs/layered_ft_results.json`. "Text + Vis-L1" epoch 5 → CG 0.81434, R@1 **0.700**;
  "Frozen" → CG 0.81372, R@1 **0.6167**. That is the frozen model itself, and the *recommended* configuration
  beats the frozen baseline by +8.3 pp R@1 while matching its gap — i.e. perturbing one vision layer produces
  the best alignment/retrieval combination in the entire study. The paper's slogan is "protect the visual
  encoder"; the paper's best configuration deliberately perturbs it. Neither the introduction, the discussion
  guidelines, nor the conclusion notes this tension.

*Fix.* State the frozen baseline's R@1 (0.617) in the same sentence as Text+Vis-L1's (0.700) and add one
sentence reconciling it: minimal, not zero, visual adaptation is optimal.

---

**[F15] — Two "model families" in the abstract's scope sentence are evaluated only on tasks where retrieval
is at chance, which the paper does not disclose in the claim itself.**

*Evidence chain.*
- `main_nn.tex:39-41` (PDF p.1): "116 experiments spanning two PEFT methods, **three model families**, two
  retrieval datasets, and three zero-shot benchmarks". `conclusion.tex:4` (PDF p.25) names them: "three model
  families (CLIP, BLIP-1, SigLIP)".
- The three-family claim cannot be weighted by any prefix: `CLIP ViT-B/32` is listed in §3.3
  (`methodology.tex:20`, PDF p.8) as the study's base model but is not one of the named families.
- BLIP-1 headline numbers are correlation-only: `outputs/blip2/b4_blip2_lora_text_only` R@1 **0.002**,
  `b4_blip2_lora_both` R@1 0.002, `b3_blip2_lora_r8` R@1 0.002 (test 5K); only `b3_blip2_lora_r4` reaches
  0.175. The paper concedes "near-random" in the catalogue footnote (`supplementary.tex:5`) but the abstract
  and intro use BLIP-1 as evidence without qualification.
- SigLIP: `outputs/siglip/s3_siglip_lora_r4/r8/r16` R@1 0.479/0.468/0.463 (final) vs frozen R@1 0.075 —
  a 0.4-point gap, i.e. a marginal effect — while the abstract's "preserves cross-modal alignment better
  …across LoRA, Adapter, BLIP-1, and ViT-L" claim is built on the sign of CGΔ in a family whose whole gap
  range is +0.058…+0.078 (`supplementary.tex:163-167`).
- ViT-L: `outputs/vitl/vitl_text_only` R@1 0.005, `vitl_rank4` 0.003, and the layered ViT-L runs report R@1
  ≈ 0.01 throughout (`outputs/vitl_layered_results.json`), i.e. all near chance; the paper reports "---" for
  those R@1 cells (`supplementary.tex:142-145`).

*Fix.* Add a one-line grading of each validation family: which conclusion each family can and cannot carry.

---

**[F16] — The same experiment count is quoted with four different values across the project, and the
"116 experiments" figure is never derived from the archive.**

*Evidence chain.*
- `paper/FOR_ADVISOR.md:27-28`: "实验数 96 实际为 94 | 修正为 116" ("the experiment count 96 is really 94 |
  corrected to 116") — the author's own record that the submission count of 116 does not follow from the
  audited count of 94.
- `outputs/master_results.json._meta` = `{"total_experiments_with_results": 100, "complete": 94, …}`.
- `paper/scripts/generate_figures.py:74-75` (comment): "原始数据仍存于 outputs/\*\*/results.json（176 行有效）"
  ("effective rows: 176").
- The manuscript never enumerates the 116: Table 1's category rows sum arithmetically to 116 but include
  entries whose numbers come from the same run counted under two categories (e.g. `baseline_full_ft`
  appears in Flickr30k and 5-Seed; `imagenet_zs` rows are evaluations, not trainings, and Table 7's full-FT
  row is a **different training** than `outputs/imagenet_zs/full_ft`, whose `n_trainable_params` = 151277313
  and CGΔ = +0.1887/`R@1` = 0.647). Table 9's own rows also total 116 only by crediting multi-run rows
  (5-seed = 20 runs) as several experiments.
- `paper/FOR_ADVISOR.md:5` also still carries a stale submission date (June 11, 2026) and a stale affiliation
  (Harbin Engineering University) that disagree with `paper/title_page.tex:16` (Southampton) and
  `main_nn.tex:27-32` (Southampton) — a companion-document inconsistency a desk editor could see.

*Fix.* Publish the experiment-to-catalogue mapping (the Supplementary Table 9 row ids are already there),
state the counting rule in the Table 1 caption and in §4.1, and bring `FOR_ADVISOR.md`/`title_page.tex` dates
into line with the actual submission.

---

**[F17] — Scope qualifiers that appear once and then disappear: the "dual-encoder only" and
"not-unique-mechanism" caveats are in the conclusion but not in the abstract's generalisation, and the
highlights assert the strongest form of every claim.**

*Evidence chain.*
- `highlights.tex:8-12`: "First systematic study of modality gap evolution under PEFT (116 experiments)";
  "**Text-only overwhelmingly preserves** cross-modal alignment across three model families";
  "**Causal evidence** for Visual Fragility: noise sensitivity, gradient, effective rank"; "DG-based
  Alignment Monitoring as **zero-overhead** training-time signal".
- The manuscript's own text has retreated from each of these: the discussion concedes the three highest-value
  exceptions to the "overwhelmingly" wording (`discussion.tex:6`), the conclusion calls visual fragility "a
  phenomenological interpretation, not a deductively proven mechanism" (`conclusion.tex:10`) and admits DG-ES
  "proved brittle under default parameters" (`conclusion.tex:12`), and the abstract already scopes the
  generalisation to "contrastive vision-language backbone" (`conclusion.tex:14`).
- The scope caveat that limits the whole study — dual-encoder contrastive architecture only
  (`conclusion.tex:16`) — appears in the conclusion and nowhere earlier; the abstract's "Our results provide
  systematic empirical grounding for gap-aware fine-tuning" (`main_nn.tex:57-58`, PDF p.1) has no
  architecture qualifier, and `highlights.tex:12` has none either. (A companion-work defence for this exists
  in `paper/REVIEW_DEFENSE.md:5-14` — see F19.)

*Fix.* Rewrite the highlights to the strength the conclusion can defend, and add the architecture scope to
the abstract's final sentence.

---

**[F18] — Fig. 3's rendered title asserts more than the paper concedes, and its numbers are hardcoded rather
than read from the archive.**

*Evidence chain.*
- `paper/figures/fig3.png` (read directly) is titled "**Text-only overwhelmingly preserves cross-modal
  alignment**" and shows the CLIP COCO pair (text-only −0.041 vs both −0.052) and Adapter (−0.046 vs −0.040)
  with the opposite ordering to the title — i.e. the figure's own bars contradict its headline.
- `paper/scripts/generate_figures.py:95-96` hardcodes those five value pairs in the script rather than reading
  `outputs/**/results.json`, which the project's own data-integrity rule forbids
  (`AGENTS.md`: figure data must be read from JSON). The values themselves do match the archive
  (`outputs/coco/rq2_both_coco` −0.0524, `outputs/phase1/adapter_d16_both` −0.0399, etc.), so this is a
  provenance risk rather than a wrong number.
- The float's caption in the manuscript is weaker and correct: "text-only yields the smallest alignment
  degradation in the vast majority of settings" (`experiments.tex:93`, PDF p.12).

*Fix.* Retitle the figure to the caption's wording and make the script read the JSON.

---

### 1.3 Notes

---

**[F19] — Objections the manuscript does not answer but the defence file does.** Reading
`paper/REVIEW_DEFENSE.md` (a rebuttal template, not verified fact) against the compiled PDF:

| Defence-file item | Answered in the manuscript? | Where |
|---|---|---|
| Clustered bootstrap for the DG–R@1 independence objection (`REVIEW_DEFENSE.md:40-97`) | **No** — the manuscript asks for it as future work | `discussion.tex:36`; see F8 |
| Dual-encoder-only scope, with cross-architecture support from decoder VLMs and Gap-Init in BLIP-2 (`REVIEW_DEFENSE.md:5-19`) | **No** — the conclusion lists it as an open limitation, with no counter-evidence | `conclusion.tex:16`; not in abstract, intro, or highlights |
| Cross-task DG evidence: rank ordering across ImageNet/DTD/Food101 (`REVIEW_DEFENSE.md:23-36`) | **No** — and the claimed ordering does not hold in the archive (Food101 frozen 82.32 > text-only 81.58) | `supplementary.tex:173` |
| Differentiation from DMNSP / continual-vs-single-task PEFT (`REVIEW_DEFENSE.md` §4, `FOR_ADVISOR.md:97`) | **No** — the DMNSP reference was removed and the related-work paragraph is now a citation-less fragment | `related_work.tex:14` |

The last row is the most damaging of the four: `paper/sections/related_work.tex:14` now reads "The
vulnerability of visual encoders during fine-tuning has been independently documented. From the distinct
perspective of single-task PEFT and modality gap dynamics, our work provides direct evidence on the
sensitivity of visual representations." — the first sentence is citation-less in a bibliography-heavy
paragraph, and the second is a dangling clause whose antecedent work is no longer named. The reviewer sees a
scope-differentiation claim with nothing attached to it.

---

**[F20] — Duplicated-number audit.** Every number appearing in more than one place, and whether the two
places agree. (A) = agrees verbatim; (B) = agrees to stated precision; (C) = disagrees.

| Quantity | Places | Verdict |
|---|---|---|
| 116 experiments | abstract p.1, intro p.3-4, §4.1 p.9, §5.1 p.22, conclusion p.25, Supp. p.28-30 | **B** (count never derived — see F16) |
| DG→R@1 r = −0.827 | abstract p.1, intro p.4, §4.6 p.14, Table 5 p.14, §5.2 p.23, §6.5 p.25, highlights, cover letter | **A** but unreproducible (F7) |
| CG→R@1 r = −0.683 | abstract (implied), intro p.4, Table 5, §4.6, §5.2, cover letter | **A** (archive −0.6832) |
| partial r = −0.807 | abstract, intro, Table 5, §4.5, §4.6, Supp. E, highlights, cover letter | **A** (archive −0.8069) |
| n = 81 | intro p.4, Table 5 caption, §4.6, Supp. E, Fig. 2 annotation | **A** (all 81; archive subset unrecoverable) |
| DGΔ r = −0.042, p = 0.713 | Table 5 p.14, cover letter item 1 | **A**, and **C** vs the 89-row archive (+0.001) |
| CGΔ r = +0.012, p = 0.915 | Table 5, §4.5, §4.6, §5.2, §6.5, cover letter | **A**, and **C** vs the 89-row archive (+0.019, p = 0.861) |
| Text-only Flickr CGΔ −0.064 | Table 2 p.12, Supp. Table 9 p.28, Fig. 3 p.12 | **A** (archive −0.0635) |
| Both Flickr CGΔ −0.032 / −0.030 | Table 2 (−0.032), Supp. Catalogue `rq1_rank8` (−0.030), `rq2_both` (−0.032) | **B/C** — Table 2's "Both" column is `rq2_both`; the ranking table's r=8 both row is a different run |
| Both COCO CGΔ −0.052 / −0.052 | Table 2, Supp., intro | **A** (−0.0524) |
| Adapter text CGΔ −0.046 | Table 2, intro p.4, §4.4, Supp. | **A** (−0.0462) |
| Adapter vision CGΔ −0.083 | Table 2, Supp., intro exception list | **A** (−0.0834) |
| BLIP-1 +0.047 / +0.152 | Table 2, intro, §4.9, Supp. | **A** (+0.0469 / +0.1516) |
| BLIP-1 R@1 0.175 | Table 1, cover letter item 5, Supp. | **A** (archive 0.1750) |
| SigLIP five R@1 0.479/0.468/0.463/0.455/0.454 | Table 1 (0.479, best), Supp., cover letter item 3 | **A**; note Table 1's `−0.217/0.574` Adapter and `+0.058/0.479` SigLIP pair different runs (F12) |
| Full FT CGΔ +0.199 | abstract (24 %), intro, Table 2, Table 4, conclusion, Supp. | **C** vs 5-seed +0.191 ± 0.008 (F5/F6) |
| Frozen ImageNet 59.28 % | abstract (59.3 %), Table 7 p.17, Supp. p.29 | **B** (59.28 does not round to 59.3) |
| Full FT zero-shot 2.6 % | abstract, intro p.5, §4.10 p.17, Fig. 6 caption p.18 | **A internally**, **C** vs `imagenet_zs_rerun` 0.13 % and the correction letter (F1) |
| Zero-shot degradation 0.6 pp | abstract, Fig. 6 caption, §4.10 | **A internally**, **C** as a cross-benchmark claim (F6/F10) |
| Text+Vis-L1 CG 0.814, R@1 0.700 | intro p.4, §5.3 guidelines p.23, Supp. Fig. 10 | **A** (0.81434 / 0.7000) |
| Frozen ViT-B retrieval 0.586 / 0.6167 | Supp. Catalogue p.28 (0.586), `outputs/layered_ft_results.json` (0.6167), Supp. Fig. 10 (not stated) | **C** — two different frozen R@1 values for the same construct (F14) |
| BLIP-1 R@1 in Table 1 (0.171→0.175) | patched by `tools/audit/fix_paper1_round3.py:25-26` | **B** (now 0.175, matches archive) |
| 5-seed std ±0.007 / ±0.003 / ±0.002 / ±0.008 | §4.2 p.12, §4.3, Supp. Table 9 | **C** in convention: ddof=1 gives 0.0079/0.0031/0.0023/0.0084; the printed set matches ddof=0 for rank-4 (0.0070) and full-FT (0.0075) and ddof=1 for the others |
| Route C best CGΔ +0.181 | Table 1 vs §4.7 (+0.190–+0.196 range quoted) | **B** (different runs of the same category) |
| Route D best +0.079 with R@1 | Table 1 (0.671) vs §4.6/§4.7/§5.3 (0.389) vs Supp. (0.389) | **C** — Table 1 puts a Route C R@1 in the Route D row (F12) |

---

**[F21] — Figure 6's caption in the compiled PDF and the cover letter's item 5 disagree on which
configuration is plotted.**

`cover_letter_zeroshot_correction.tex:46` reports removing "a configuration description in the Discussion
that did not correspond to any single experiment (``rank-16 + α=16 + qvko'')" — that string is indeed absent
from the PDF (0 occurrences), so the item landed. But `paper/figures/fig7.png` still exists in the tree as a
separate artefact whose caption content reappears on the wrong float (F13), and `paper/figures/fig6.png`'
s zero-shot bars (58.66/59.67/2.6) match the *50k* archive, not the correction letter's re-measurement — so
whichever of Fig. 6 / Fig. 7 the reviewers open will disagree with at least one companion document.

---

## 2. Verified-consistent items (no action)

Recorded so the fixes above are not over-applied.

- `paper/main_nn.pdf` is a faithful build of `paper/sections/*.tex`: all spot-checked sentences, tables and
  catalogue rows correspond (see Method). **The sibling-manuscript failure mode — a fix present in the `.tex`
  but not in the built PDF — does not occur here.**
- The 5-seed archive reproduces Table 9's summary rows exactly: `outputs/flickr30k_seeds/summary.json`
  mean CGΔ = −0.0198 / −0.0017 / −0.0458 / +0.1906 for rank-4 / rank-32 / text-only / full-FT, matching
  `supplementary.tex:120-123` and `§4.2–4.3`.
- Welch's *t* = −22.96 / p = 3.5e-31 and the "F = 13.37" ANOVA could not be reproduced from any script in
  the tree (F9), but the LoRA-vs-full-FT comparison they describe is directionally uncontroversial
  (full-FT CGΔ > 0, all PEFT CGΔ < 0 in the archive).
- α-sweep, q/qv/qvko, Gap-Init, Route C/D/E and layered catalogs all match their `results.json` files
  cell-by-cell (checked: `alpha_4/8/16/32/64`, `modules_q/qv/qvko`, `gap_init_r1/r2/r4/r8`,
  `c1_gapreg_*`, `c3_gapinit_*`, `c4_alpha_anneal_*`, `d1–d5`, `e1–e3`, `vitb_layered_*`, `vitl_layered_*`,
  `adapter_layered*`, `adapter_d*`).
- `declaration.tex`, `title_page.tex` (ORCID, affiliation), `highlights.tex` item 2's numeric content and
  `cover_letter.tex` items 1–6 (Table 4 correlations, Fig. 7 bars, SigLIP R@1s, layered CGΔ values, BLIP-1
  0.175, footnote clean-up) all correspond to the archive.
- Corrected values from `cover_letter.tex` are present in the built PDF: Table 5's `−0.042/0.713` and
  `+0.012/0.915` (PDF p.14), the SigLIP five R@1s (p.29), the layered CGΔ values (p.28-30), BLIP-1 0.175
  (p.11). The cover letter's promise was kept for these items; it was broken for the zero-shot item (F1).
- `docs/P1_eval_audit.md` action 3 (re-run with the correct LoRA-only filter) was **not** taken — no re-run
  artefacts exist (`outputs/` contains no LoRA-only-filter run of the main grid) — which is consistent with
  the audit's "if re-running" phrasing, but it makes F2 the only remedy available.

---

## 3. Verdict

The paper is internally coherent on its *secondary* layers — the α/module/rank/route catalogues, the
5-seed summary statistics, and the layered fine-tuning tables all trace to archived JSON cell-by-cell, and
the compiled PDF matches the source, so there is no stale-build problem. The problems are concentrated in
exactly the places Pattern Recognition reviewers attack first:

1. **Provenance.** The abstract's two headline numbers are a single-seed relative change (+24 %, best of five
   seeds) and a zero-shot result measured under a protocol the authors' own latest cover letter supersedes
   (F1, F5, F6). Three claims — the DTD/Food101 footnote, the ImageNet table, the full-FT row — are each
   supported by two mutually inconsistent archived measurements, and the manuscript never says which one it
   is using.
2. **Disclosure.** None of the three actions required by the 2026-08-16 audit landed in the submitted PDF
   (F2, F3). The training convention is not merely undisclosed — the supplementary material asserts the
   opposite of what the trainer does, and the supporting figure is computed from a checkpoint that cannot
   contain the updates in question.
3. **Exceptions.** The abstract concedes two exceptions; the data contain at least four, and the two
   strongest (Adapter vision-only, COCO both-position) appear in different lists in different sections. The
   conclusion drops the list entirely while claiming robustness across the method family the exception comes
   from (F4, F5).
4. **Statements the archive contradicts.** Effective-rank tracking shows text-only *degrading* visual
   effective rank by up to 35 % (F11); the frozen baseline outperforms the paper's recommended configuration
   on retrieval at equal gap (F14); Adapter's "text-only wins" evidence is a single chance-level comparison
   (F9).
5. **Reproducibility of the third contribution.** The DG-correlation subset is documented in the authors' own
   script as unrecoverable (F7); the independence objection is answered only in a file the reviewers will
   never see (F8/F19).

Of the reviewer objections anticipated in `paper/REVIEW_DEFENSE.md`, only one (the layered/DMNSP clean-up) is
genuinely closed in the manuscript; the other three — clustered inference, dual-encoder scope, cross-task DG
evidence — exist only in the defence file, and one of them (cross-task ordering) does not survive contact with
the archived DTD/Food101 numbers.

**Bottom line:** this is not a fabrication problem — every number I checked is a real measurement of something.
It is a *labelling* problem four layers deep: the trained model is not the described model, the checkpoint is
not the trained model, the evaluated protocol is not the described protocol, and the manuscript is not the
version its own cover letter describes. A competent reviewer with access to the artefacts will find at least
F1, F2, F3 and F7. All four are fixable with disclosure and re-labelling rather than new experiments, except
F7, which needs one re-run of a single correlation script.
