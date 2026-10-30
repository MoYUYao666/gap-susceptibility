# P1 — Adversarial Review #2: the causal / mechanistic claims

**Manuscript:** *Protect, Don't Perturb: Cross-Modal Alignment under PEFT of Vision-Language Models*
(sole author; Pattern Recognition **PR-D-26-10149**)
**Scope of this review:** the causal story only — `paper/sections/strict_control.tex`, `visual_fragility.tex`, the
mechanism sentences in `main_nn.tex` / `introduction.tex` / `conclusion.tex`, the training-convention disclosure in
`methodology.tex`, and the corroborating artefacts they lean on.
**Mode:** read-only. Only this report was written.
**Method:** every claim below is checked against the released JSON/LOG artefacts and the released code, not against
the prose. Where arithmetic could close a gap (e.g. what was actually trainable), it was closed exactly.

---

## 0. Artefacts actually inspected

| Artefact | What it is |
|---|---|
| `paper/sections/strict_control.tex` (37 lines) | new strict-freeze section |
| `paper/sections/visual_fragility.tex` (37 lines) | Visual Fragility Interpretation |
| `paper/main_nn.tex:36-62`, `introduction.tex`, `conclusion.tex`, `methodology.tex`, `discussion.tex`, `experiments.tex`, `supplementary.tex` | mechanism sentences and the tables they cite |
| `experiments/strict_freeze_control.py` (323 lines) | strict-freeze driver |
| `outputs/strict_freeze/text_only/seed{42,123,456,789,1024}/results.json`, `.../gap_history.json`, `.../best_checkpoint.pt` | the 5 strict runs |
| `outputs/strict_freeze/frozen/results.json` | frozen reference |
| `outputs/strict_freeze/both/seed42/best_checkpoint.pt` | **partial joint strict run** (no `results.json`) |
| `outputs/strict_freeze/run.log` (3,944 lines) | full run log incl. the aborted joint run |
| `outputs/analysis/strict_control_summary.json` | summary actually driving Table 8 |
| `outputs/effective_rank_tracking.json` | historical rank tracking |
| `outputs/noise_sensitivity.json`, `outputs/gsnr_results.json`, `outputs/gsnr_results_pre_fix.json` | corroboration |
| `outputs/flickr30k/**`, `outputs/flickr30k_seeds/**`, `outputs/route_e/**`, `outputs/layered_ft_results.json`, `outputs/vitl_layered_results.json`, `outputs/adapter_layered_results.json` | historical runs behind Tables 2/4 |
| `src/lora.py`, `src/trainer.py`, `src/peft_methods.py`, `src/dataset.py` | mechanism of the freeze/optimizer |
| `paper/scripts/{noise_sensitivity,gsnr_analysis,layered_finetune,weight_svd_analysis,plot_fig3_crossval}.py` | producers of the corroborating figures |
| `models/clip-vit-base-patch32/config.json` | dropout settings |

---

## 1. Is the central inference sound? (brief item 1)

**The sentence under attack** (`strict_control.tex:33-37`):

> "The gap is nevertheless reduced by $-0.047$, which is within noise of what the mixed runs achieved on the same
> protocol. Text-only adaptation therefore captures the alignment benefit with a visually untouched encoder, and the
> ``protect, don't perturb'' principle is **demonstrated rather than inferred**: the extra parameter budget of the
> historical runs contributed nothing measurable to this effect. **We report the control for the text-only
> configuration, which is the one that carries the mechanism claim.**"

### 1.1 What the control *does* license — and it licenses more than the paper claims

I re-derived the historical parameter budgets exactly, because everything turns on what "text-only" meant.

* Pristine CLIP ViT-B/32 total = **151,277,313** (`outputs/analysis/strict_control_summary.json:38`, and
  `outputs/flickr30k/baseline_full_ft/results.json:44`).
* LoRA-wrapped text-only model total = **151,473,921** (`outputs/strict_freeze/run.log:3`).
* Historical text-only trainable = **145,170,177**. Hence the LoRA library froze
  `151,473,921 − 145,170,177 = 6,303,744 = 24 × (512² + 512) = 24 × 262,656` — i.e. **exactly the 24 replaced
  text-side `q_proj`/`v_proj` weight+bias tensors**, and nothing else.
* Therefore **the historical "text-only" runs trained 145,170,177 / 151,277,313 = 95.96 % of the model, including
  all 199 vision-encoder tensors, `visual_projection.weight` and `logit_scale`.**

Strict runs, same protocol, five seeds: CGΔ **−0.0465 ± 0.0027**, R@1 **0.6238 ± 0.0049**
(`outputs/analysis/strict_control_summary.json:14-17`).
Historical mixed text-only, five seeds, same protocol (batch 128, 320 steps): per-seed CGΔ
−0.048, −0.044, −0.048, −0.043, −0.047 (`supplementary.tex:199-203`; recomputed from
`outputs/flickr30k_seeds/rq2_text_only/seed*/results.json`), R@1 0.616/0.610/0.638/0.620/0.621 → mean 0.621.

**So the "extra parameter budget contributed nothing measurable" clause is correct, and it is a stronger result than
the section claims**: training the entire vision tower versus training none of it changes CGΔ by ≤0.002 and R@1 by
≤0.003. As a *sufficiency* result ("the adapters alone are enough"), the control is sound and end-to-end verified
(`n_trainable_params == n_trainable_reported_by_trainer == 196,608` in all five JSONs — the trainer re-counted the
optimizer set independently at `src/trainer.py:243-244` via `src/peft_methods.py:137-138`).

### 1.2 What it does **not** license

The claim that is *not* licensed is the comparative half. "Protect, don't perturb" is a two-arm claim:

* arm A = adapters in the text tower, vision protected;
* arm B = adapters in both towers, vision perturbed.

The control provides **only arm A**. The joint arm under the same freeze was never completed — and a *partial*
artefact exists that the paper does not disclose (§S3 below): `outputs/strict_freeze/both/seed42/best_checkpoint.pt`
with `run.log:3642` recording `trainable=491520  lora_layers=48`, then `Epoch 4/10 … R@1: 0.685 | Time: 325.6s` and a
gap check `Centroid: 0.8140`, after which the log stops mid-epoch 5.

Worse, the paper's own numbers remove the mechanism the sentence asserts. In the archive, the historical "text-only"
arm **also perturbed the whole vision encoder** (95.96 % trainable), and its outcome is statistically
indistinguishable from the strict-freeze arm that perturbed nothing. So within the paper's data
*vision-side perturbation is neither necessary nor, on its own, harmful*. What separates text-only from both must lie
somewhere else (text-side adapter placement, the joint update interaction, or an artefact of the historical
optimizer), not in "the visual encoder was perturbed".

The last sentence — *"We report the control for the text-only configuration, which is the one that carries the
mechanism claim"* — is the exact move that is not allowed: the text-only arm carries the *existence* half of the
claim, and the joint arm carries the *comparative* half. Declaring the comparative half out of scope and then
concluding the comparative principle is demonstrated is a non sequitur.

### 1.3 Verdict for item 1

**Overstated (must-fix).** What may be concluded:

1. the adapter-only manipulation is sufficient to reproduce the text-only gap reduction and retrieval level
   (−0.0465 ± 0.0027; 0.6238 ± 0.0049);
2. all **398** non-adapter tensors are bit-identical after training — the effect is produced without touching the
   vision tower, `visual_projection`, `text_projection` or `logit_scale`;
3. the historical runs' extra ~145 M trainable parameters (the entire vision tower included) contributed nothing
   measurable in the text-only configuration.

What may not be concluded: anything about the joint configuration under the same freeze; that "protecting" the
vision encoder *causes* the benefit; that Visual Fragility is the mechanism separating text-only from both.

**Minimum fix:** either (a) run the strict-freeze joint arm (5 seeds × ~50 min ≈ 4 h on the authors' own measured
cost — see §S3) and report it, or (b) delete "demonstrated rather than inferred" and the "which is the one that
carries the mechanism claim" sentence, and restate the control as: *"adapter-only training is sufficient; the joint
arm under the same freeze remains untested."*

---

## 2. End-to-end check of "no vision-side update" (brief item 2)

**The sentence** (`strict_control.tex:29-33`):

> "With only the adapters trainable the vision encoder of the text-only configuration receives \emph{no} updates:
> 0 of 199 vision-side backbone tensors change, the adapter update norm is non-zero on the text side only …"

### 2.1 Is the measurement right? Yes — verified by structure and by arithmetic

`backbone_deltas()` (`experiments/strict_freeze_control.py:159-182`) enumerates `model.named_parameters()`,
normalises `.original.` → `.`, skips anything not in the pristine CLIP state dict (this is how the LoRA `lora_A`/
`lora_B` tensors are excluded), and buckets by name prefix (`:170-171`).

I recomputed the denominators from CLIP's known parameter structure:

* `vision_model.*` = 3 embedding + 2 `pre_layrnorm` + 12 × 16 (2 × LayerNorm, 4 × attention w+b, 2 × MLP w+b) +
  2 `post_layernorm` = **199** ✔ matches `backbone_delta.vision.tensors` in all six JSONs.
* `text_model.*` = 2 embedding + 12 × 16 + 2 `final_layer_norm` = **196** ✔
* `other` = **3** = `logit_scale`, `visual_projection.weight`, `text_projection.weight` ✔

So the counters are exactly right, and — importantly — the claim is *under*-stated: in every one of the five runs,
**all 398** non-adapter tensors show `nonzero_tensors: 0`, `max_abs_delta: 0.0`, `frobenius: 0.0`
(`outputs/strict_freeze/text_only/seed*/results.json`, `backbone_delta`). The same is true of the frozen reference
(`outputs/strict_freeze/frozen/results.json:32-51`).

### 2.2 Is "vision-side" the right definition? No — and the paper uses two conflicting ones

`visual_projection` and `logit_scale` land in the **`other`** bucket here. But the paper's own weight/spectral
analysis classifies `visual_projection` as **vision**:

```python
# paper/scripts/weight_svd_analysis.py:322
bucket = "vision" if k.startswith(("vision", "visual_projection")) else "text"
```

Functionally the reviewer's point stands: `visual_projection` is the map from the vision tower's pooled output into
the shared embedding space and receives gradient exclusively from image features — a reader will reasonably call it
vision-side. The manuscript therefore has two definitions of "vision side" in its own code base, and the strict
control uses the narrower one while the appendix uses the wider one. This is not fatal for the strict runs (all 398
are frozen), but it makes the "0 of 199" figure look like a selected denominator exactly where it invites the most
scrutiny.

**Recommended wording:** *"0 of 398 non-adapter tensors changed: 199 in the vision tower, 196 in the text tower and
3 top-level (`visual_projection`, `text_projection`, `logit_scale`)."*

### 2.3 Does the LoRA naming hide anything? No — and it is a useful consistency check

The `.original.` → `.` normalisation is collision-free for CLIP (no parameter is named `…original…`). Because the
deltas are exactly 0.0, it also proves the trainer's own loader and the pristine reference directory
(`models/clip-vit-base-patch32`) hold identical weights — otherwise every tensor would show a non-zero delta. That is
a genuine positive control and should be stated as such.

### 2.4 One measurement defect (note)

`lora_update_norms()` computes

```python
# experiments/strict_freeze_control.py:191
delta = (w.scaling * (w.lora_A @ w.lora_B)).detach().cpu().float()
```

whereas the actual update is `scaling · (A B)ᵀ` (`src/lora.py:66`, merged at `:75`). The two matrices are transposes
of each other, so the Frobenius norm (the quantity reported) is unaffected — **not a numerical error**, but it will
read as one to any referee who checks, and it should carry a comment.

---

## 3. The effective-rank claim (brief item 3)

**The sentence** (`strict_control.tex:31-33`):

> "… and the layer-wise effective rank of the vision encoder is identical before and after training, while the
> text-side rank moves."

**Supplementary restatement** (`supplementary.tex:173` and `:261` panel D):

> "the legacy text-only runs reduce it, while the strict control leaves it exactly unchanged"

### 3.1 It is true — bit-identical, not merely close

Across all five seeds and all 12 vision layers, `effective_rank_init` == `effective_rank_final` **exactly**
(max |Δ| = 0, checked key-by-key; e.g. `outputs/strict_freeze/text_only/seed42/results.json:74` vs `:100`,
`vis_L0 = 9.333293914794922` in both). Text-side values all move.

### 3.2 It is circular — it *must* be unchanged

`CLIPVisionConfig.dropout = 0.0` and `attention_dropout = 0.0`
(`models/clip-vit-base-patch32/config.json`, `vision_config`). `layer_effective_ranks()` is called under
`@torch.no_grad()` on the **same materialised batch object** (`first`, `experiments/strict_freeze_control.py:214-215`
and `:221-222`), in eval mode. Given (i) zero parameter change and (ii) a deterministic forward pass, the layer
outputs are bit-identical by construction, so the effective rank is identical by construction. The measurement adds
**no information beyond the max-|Δ| = 0 check**; presenting it as a second, independent line of evidence is
double-counting.

### 3.3 Is the measurement strong enough in general? No — three limits

1. **It cannot discriminate.** The statistic is `exp(entropy of normalised singular values)` of a **16 × D**
   mean-pooled matrix (`strict_freeze_control.py:126-155`, `n_samples=16`), so it is bounded above by 16. Reported
   vision values are 12.0–13.4 and text values 1.7–11.3 — i.e. the vision statistic sits near its ceiling. A metric
   with hard cap 16 that reports 13.4 has very little resolution for a "rank preserved / rank collapsed" claim.
2. **It is a noisy estimator at n = 16.** Within the strict runs, `vis_L0` varies 9.3265–9.4245 across seeds purely
   from which images are drawn (see §3.4), i.e. ±0.05 per layer. Any comparison between single legacy runs must be
   read against that band.
3. **Terminology mismatch.** The supplement calls it the *"effective rank of layer-wise image embeddings"*
   (`supplementary.tex:173`, `:272`), but the hooks are on **encoder layer hidden states**, before
   `visual_projection` (`noise_sensitivity.py:200-206`; `strict_freeze_control.py:137-140`). These are not image
   embeddings.

### 3.4 A confound in the released artefacts: the "val" loader is augmented

`create_dataloaders()` builds the Flickr30k loaders by `random_split` of the **train-split dataset object**
(`src/dataset.py:404, 416-425`), whose transform is the training transform —
`RandomHorizontalFlip(p=0.5)` + `ColorJitter` (`src/dataset.py:23-32`). The separately constructed `val_dataset` is
discarded. Consequences:

* validation R@1 and gap numbers are computed on randomly augmented images (affects the whole paper, not only the
  strict control — note-severity, but it should be disclosed);
* `frozen/results.json` is **not batch-matched** to the runs: `vis_L0 = 9.3669` there vs 9.3265–9.4245 in the five
  runs, while `txt_L*` is identical everywhere (captions are not augmented). The mismatch is a different random
  augmentation, not a weight difference. `outputs/analysis/strict_control_summary.json:3` therefore reports a
  "frozen" reference drawn from a different sample than the runs.

This is worth stating explicitly in the strict-control section, because a referee who diffs the frozen reference
against `effective_rank_init` will find a 0.03–0.09 discrepancy on the vision side and conclude the encoder *did*
move.

### 3.5 Verdict for item 3

**True but circular; must not be presented as evidence (should-fix→downgrade to a consistency check).** Suggested
replacement: *"Consistent with the zero-delta check, the layer-wise effective rank of the vision encoder is unchanged
(exactly, as it must be when no weight changed)."*

### 3.6 The historical side of the same claim *is* informative — and it cuts against the story

`outputs/effective_rank_tracking.json` records, for the historical text-only run, vision ranks collapsing:
`vis_L0` 9.386 (init) → 6.828 → 6.164 → 7.021 over three training epochs, i.e. a 27–34 % drop. Since the sampling
noise band is ±0.05 (§3.4), this is real. The supplement has already been hedged to admit it
(`supplementary.tex:261` panel D; `:173` footnote c). But note what it means: **the historical "text-only"
configuration did perturb the visual representation space markedly — and still reduced the CG.** That is direct
counter-evidence to the interpretation that vision-side perturbation is what degrades alignment in the paper's
archive, and it is the strongest single tension in the mechanistic story.

*Reproducibility aside (should-fix):* `paper/scripts/noise_sensitivity.py:252-324` writes **three** configs
(`Frozen`, `text-only`, `Full FT`), but `outputs/effective_rank_tracking.json` has only **two** keys. The released
script therefore cannot regenerate the released artefact.

---

## 4. Sentence-by-sentence verdicts (brief item 4)

| # | Sentence (quoted) | Location | Verdict |
|---|---|---|---|
| A | "We propose the **Visual Fragility Interpretation** … as a parsimonious account, and **isolate its mechanism** with a strict control in which only the adapters are trainable: the visual encoder then receives no updates at all while the gap is still reduced." | `main_nn.tex:53-55` | **Overstated.** Facts supported (`strict_freeze/text_only/seed*`); "isolate its mechanism" is not — one arm only (§1.2). |
| B | "**The mechanism is isolated by a strict control**: with every non-adapter parameter frozen---196,608 trainable parameters, $0.13\%$ of the model---text-only adaptation still reduces the gap ($-0.047$) while not a single vision-encoder tensor changes, and vision-encoder noise degrades retrieval 2.6$\times$ more than text-encoder noise in the noise-sensitivity analysis." | `introduction.tex:25` | **Overstated.** "not a single vision-encoder tensor changes" supported (and under-stated: 0/398). "The mechanism is isolated" not supported; the 2.6× clause is a *different* experiment presented as if it completed the isolation (§6.1). |
| C | "We further isolate the mechanism with a strict control in which only the adapters are trainable, so that **the visual encoder is provably left unchanged** while the alignment benefit persists." | `introduction.tex:8` | **Mixed / overstated.** "provably left unchanged" = supported (0/398, max\|Δ\|=0). "isolate the mechanism" = not supported. |
| D | "With only the adapters trainable the vision encoder … receives no updates: 0 of 199 vision-side backbone tensors change, the adapter update norm is non-zero on the text side only, and the layer-wise effective rank of the vision encoder is identical before and after training, while the text-side rank moves." | `strict_control.tex:29-33` | **Supported as fact; the rank clause is vacuous** (circular, §3.2). Denominator should be 398 (§2.2). |
| E | "The gap is nevertheless reduced by $-0.047$, which is within noise of what the mixed runs achieved on the same protocol." | `strict_control.tex:33-34` | **Supported.** Strict −0.0465 ± 0.0027 / R@1 0.6238 vs mixed −0.046 ± 0.002 / R@1 0.621. |
| F | "Text-only adaptation therefore captures the alignment benefit with a visually untouched encoder, and the ``protect, don't perturb'' principle is **demonstrated rather than inferred**: the extra parameter budget of the historical runs contributed nothing measurable to this effect." | `strict_control.tex:34-36` | **Split.** Clause 1 supported (sufficiency). Clause 2 **unsupported** (needs the joint arm; §1.2). Clause 3 supported. |
| G | "We report the control for the text-only configuration, **which is the one that carries the mechanism claim**." | `strict_control.tex:36-37` | **Unsupported.** The comparative half is exactly what the mechanism claim needs. |
| H | "Under strict freezing the joint configuration places trainable parameters inside the vision tower, so a full vision-side backward pass becomes necessary and **the measured cost per run rises from about six minutes to about fifty**; the joint rows are left to future work rather than reported at a reduced seed count." | `strict_control.tex:37` | **Supported** (6 min: `run.log` 349.7–388 s; ~50 min: 325.6 s/epoch × 10). But a **partial joint run exists and is undisclosed** (S3). |
| I | "Our evidence---parameter noise sensitivity, gradient contribution quantification, and a strict control that leaves the visual encoder provably unchanged---**converges** on this interpretation." | `conclusion.tex:10` | **Partly unsupported.** Strict control ✔; noise sensitivity ⚠ (§6.1); "gradient contribution quantification" ✘ (§6.2). |
| J | "The strict control makes the first clause concrete: with $196,608$ trainable adapter parameters and no vision-side update at all, the gap is still reduced by $-0.047$." | `conclusion.tex:14` | **Supported as fact; overstated as support** for "protect the visual encoder's parameters" (see F). |
| K | "The strict control sharpens the picture: when only the adapters are trainable the visual encoder is untouched (0 of 199 vision-side tensors change) and the gap is still reduced, **so the benefit does not require perturbing the visual space**; joint adaptation and full fine-tuning do perturb it, and they degrade alignment." | `visual_fragility.tex:37` | **Split.** "does not require perturbing" = **supported** (necessary-condition claim — the one inference the control does license). "joint adaptation … do perturb it, and they degrade alignment" = **overstated**: the paper's text-only arm also perturbed it and did not degrade (§1.2). |
| L | "the pre-trained visual embedding space appears more sensitive to parameter perturbation than the text embedding space" | `visual_fragility.tex:4` | **Hedged — acceptable as an interpretation**; the only direct test is weak (§6.1). |
| M | "the text encoder, operating closer to its capacity limit, has fewer degrees of freedom for perturbation-induced disruption" | `visual_fragility.tex:10` | **Unsupported conjecture** (no measurement), and it runs against the usual reading of "at capacity ⇒ brittle". Note. |
| N | "Our weight and spectral analyses (Appendix) show that fine-tuning the vision encoder produces **localized parameter shifts concentrated in the vision encoder**" | `visual_fragility.tex:12` | **Contradicted by its own appendix.** `supplementary.tex:261` (A): "the archived text-only runs record no vision-side updates while the text side changes (‖ΔW_txt‖ = 0.66)". Must-fix. |
| O | "Our results provide complementary evidence …: **fine-tuning the visual encoder consistently increases the gap**, while fine-tuning only the text encoder preserves or even reduces it." | `discussion.tex:10` | **Contradicted by the paper's own numbers.** The legacy "text-only" runs fine-tuned the whole vision encoder (95.96 % trainable) and reduced CG by −0.046. Must-fix. |
| P | "The visual fragility interpretation predicts that DG should remain stable under text-only fine-tuning (**since the visual encoder is untouched**) …" | `discussion.tex:44` | **False premise** for the runs cited in the same paragraph (`outputs/route_e/e3_dges_text_r8/results.json`: 145,170,177 trainable). Must-fix. |
| Q | Table row: "Text-only $>$ **any strategy perturbing the visual encoder** … Confirmed on LoRA Flickr, Adapter, and BLIP-1" and "DG rises when visual encoder perturbed, **stable under text-only**" | `visual_fragility.tex:26-27` | **Overstated premise.** The LoRA-Flickr "text-only" bar perturbs the visual encoder as much as the "both" bar does; the contrast as stated is not the contrast measured. Should-fix. |

---

## 5. The historical runs and the main tables (brief item 5)

The manuscript keeps the historical numbers in the main tables while disclosing the convention. The disclosure is
**accurate for Adapter/Prefix** — verified: `src/peft_methods.py:107` and `:129` freeze the backbone before
injection, so `methodology.tex:22`'s last sentence is correct. For LoRA it is **materially incomplete**:

> "the embedding and LayerNorm parameters of both encoders therefore remained trainable" (`methodology.tex:22`)

The frozen set is *exactly* the 24 replaced text-side `q_proj`/`v_proj` weight+bias matrices
(6,303,744 = 24 × 262,656, §1.1). Everything else — all attention and MLP weights of the vision tower, all of the
text tower except those 24 matrices, both projections and the logit scale — was trainable. "Embedding and LayerNorm
parameters" invites the reader to infer that the vision encoder's attention/MLP weights were frozen. They were not.
**This understatement is the single most consequential wording problem in the revision**, because every mechanistic
sentence in §4 depends on the reader's mental model of what the historical "text-only" arm actually did.

Concrete places that still invite the strict reading:

| Item | Location | Problem |
|---|---|---|
| Table 2 (`tab:position`), "Text-only" row Flickr −0.064 / both −0.032 | `experiments.tex:66,71,77-78` | Both come from batch-64 single runs (`outputs/flickr30k/rq2_*`) whose "text-only" arm trained 96 % of the model. Label conveys "vision untouched"; it wasn't. Also `final_gap.step = 630` ⇒ batch 64, whereas `methodology.tex:20` says "All experiments: batch size 128". |
| Table 4 (`tab:method_compare`) | `experiments.tex:126-144` | Same rows, same labelling; the paragraph is otherwise careful about baselines. |
| Figure 3 (cross-validation) | `experiments.tex:90-95`; `paper/scripts/plot_fig3_crossval.py:29-30` | Hard-coded legacy values `TEXT_ONLY = [-0.064, -0.041, +0.2368, +0.047, -0.036]`, drawn with the label "Text-only". Adapter bars were corrected to a common baseline (good), but the "Text-only" label was not corrected to "text-side adapters, backbone trainable". Caption (`experiments.tex:93`) carries no caveat. |
| Figure 5 (DG-ES) | `experiments.tex:184-189` | The "text-only" runs shown are legacy-convention (`outputs/route_e/e2,e3` = 145,170,177 trainable). |
| Layered fine-tuning (intro contribution 6; `discussion.tex:27`) | `introduction.tex:23`, `discussion.tex:27` | **Confounded comparison — see below.** |
| Supplementary Fig. 8 panel B | `supplementary.tex:261`; `paper/scripts/weight_svd_analysis.py:365` | **Measured on pristine vision weights — see below.** |
| "117 experiments" / "117 experimental observations" | `main_nn.tex:39`, `introduction.tex:8`, `visual_fragility.tex:37`, `supplementary.tex:5,12,169` | The 5 strict-control runs (plus a frozen reference) are not counted; Table 9 still totals 117. Should say "117 archived + 5 strict-control runs". |

### 5.1 Layered fine-tuning is confounded by the freeze convention (must-fix)

`introduction.tex:23` claims Text+Vis-L1 "achiev[es] frozen-level alignment with minimal perturbation … outperforming
pure text-only (R@1=0.427), full both-modality (R@1=0.510)". In `paper/scripts/layered_finetune.py`:

* `vis_layers == 0` (Text-only) and `-1` (Both) call `apply_lora_to_model(...)` — **no freeze**, historical
  convention, 145 M trainable (`:135-144`);
* `vis_layers ∈ {1,2,4}` call `apply_lora_to_vision_layers(...)`, which **freezes everything first** and re-enables
  only `lora_A`/`lora_B` (`:57-58`, `:85-87`, `:146-148`) — i.e. the strict convention.

The two comparators therefore run the *conventional* regime and both **diverged**: `outputs/layered_ft_results.json`
"Text-only" epoch 1 → CG 1.2865, R@1 0.010 (final R@1 0.427); "Both (all Vis)" → CG 1.2639, R@1 0.060. The R@1 = 0.427
figure quoted in the introduction is the final epoch of a diverged run, not a text-only baseline (the main-protocol
text-only reaches R@1 0.62). Meanwhile Text+Vis-L1 is stable **because its backbone is frozen**, not because it
perturbs one vision layer.

Two consequences: (i) the intro/methods contrast is not a layer-count comparison; (ii) Text+Vis-L1 — recommended in
`discussion.tex:27` as the "best overall trade-off" — is in fact a *strict-freeze* configuration, which the
manuscript never says. Either the layered script must be re-run with a uniform (strict) convention for all arms, or
the Text-only / Both comparators must be replaced by the main-protocol numbers and the 0.427/0.510 figures dropped.

### 5.2 Supplementary Fig. 8 panel B is computed on pristine vision weights (must-fix)

`paper/scripts/weight_svd_analysis.py:362-377`, for the non-Full-FT configs:

```python
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", local_files_only=True)   # :365
sd = ckpt.get("lora_state_dict", {})                                                       # :366
... layers[ln].lora_A.data = w["A"]; layers[ln].lora_B.data = w["B"]                       # :374-377
```

The archived checkpoints contain **adapter tensors only** (exactly what the caption at `supplementary.tex:261`
concedes for panel A). So panel B's "text-only" curve is produced by a model whose vision weights were never
trained. "Image embedding singular value spectra: text-only overlaps with Frozen (σ₁ = 16.15)" is therefore a
tautology of the checkpoint format, not evidence that the legacy text-only run preserved the image geometry — and it
directly contradicts panel (D) of the *same figure*, which reports (from the actually-trained model,
`outputs/effective_rank_tracking.json`) that the same run's image-embedding rank fell from 9.43 to 6.16–7.02. The
caption discloses this for (A) but not for (B). Either re-run (B) from a checkpoint that stores backbone weights, or
mark (B) as "adapter-only reconstruction (vision weights pristine)".

---

## 6. Independent corroboration (brief item 6)

`conclusion.tex:10` names three pillars. Status of each artefact:

### 6.1 Noise sensitivity — artefact exists, supports the number, not the inference (should-fix)

Artefact: `outputs/noise_sensitivity.json` (produced 2026-08-03 by `paper/scripts/noise_sensitivity.py`).
At σ = 0.1: vision drop 9.2199 %, text drop 3.5461 % → ratio **2.600** ✔ so "2.6×" is arithmetically supported.
Problems:

* **One unseeded draw.** The script contains no `torch.manual_seed`/`np.random.seed` anywhere
  (`noise_sensitivity.py:120-163`), and `inject_noise_to_encoder` draws `torch.randn_like(param)`
  (`:83`). There is no repetition and no error bar.
* **Resolution.** `create_dataloaders("flickr30k", ".", batch_size=64, max_samples=2000)` (`:129`) ⇒ a 200-sample
  val split; every reported R@1 is a multiple of 0.005, i.e. each "drop" is 1–3 samples.
* **The dose–response is non-monotone and reverses.** Drop (%) for vision at σ = 0, 0.001, 0.003, 0.01, 0.03, 0.1:
  1.42, 2.84, **0.71**, 0.00, 1.42, 9.22; for text: 0.71, 0.71, **2.13**, 1.42, 0.71, 3.55. At σ = 0.003 *text*
  degrades 3× more than vision. Quoting only the σ = 0.1 endpoint hides this.
* The figure annotation in `noise_sensitivity.py:391-393` computes the ratio exactly the same way (last σ only).
* `inject_noise_to_encoder` perturbs *all* transformer block weights of the whole encoder (`:63-85`), including the
  vision attention/MLP weights, and uses `param.std()` as the scale (`:83`), so "equivalent parameter noise"
  (`supplementary.tex:272`) is proportional, not equivalent, noise across the two encoders.

**Verdict:** artefact supports the sentence as written *only* as "a single σ = 0.1 draw showed a 2.6× larger
retrieval drop for vision noise". It does not support "vision-encoder noise degrades retrieval 2.6× more than
text-encoder noise" as a general statement. Seed the script, run ≥5 draws per σ, and report mean ± sd — or downgrade
to "consistent with".

### 6.2 Gradient analysis — the artefact points the other way (must-fix)

Artefact: `outputs/gsnr_results.json` (rewritten 2026-09-20 by the now-seeded `paper/scripts/gsnr_analysis.py`;
byte-identical in content to `outputs/gsnr_results_pre_fix.json`, so the numbers are reproducible — a positive).

Values: `vis_grad_norm = 0.4510`, `txt_grad_norm = 0.3104`, `v_t_ratio = 1.4532`. `supplementary.tex:286` states
this correctly ("Visual gradients are 1.5× larger than text gradients in both-modality LoRA"). But
`conclusion.tex:10` cites this as evidence that *visual spaces are more sensitive to perturbation*, and
`visual_fragility.tex:37` lists "gradient concentration in the text branch" as a live alternative explanation.
The artefact says the opposite: in both-modality LoRA the **vision** parameters carry the larger per-parameter
gradient norm. Moreover the script's own docstring (`gsnr_analysis.py:4-5`) states the intended inference as
"Vis贡献<10 % → 视觉端扰动几乎无帮助", which the archived 1.45× does not show.

Additional weaknesses: the quantity is a **mean over parameters of per-parameter gradient norms** (`:66-72`), which
conflates tensor size with signal; it is measured over 15 batches × 3 epochs = 45 steps of a 2,000-sample subset
(`:84`, `:98`); no error bars; the text-only arm's gradients (`vis_g2`, `txt_g2`) are printed but **never saved**, so
the artefact cannot corroborate the two-bar panel of Fig. 11. The retained derived field
`text_advantage_pct = −639.8` is a mis-signed quantity the script itself flags as unused (`:149-152`).

**Verdict:** the "gradient contribution quantification" pillar does not support the sentence and should be removed
from `conclusion.tex:10` or re-described as "vision parameters receive larger gradient norms in joint adaptation".

### 6.3 Effective-rank tracking — see §3.6

The artefact supports the *supplementary* sentence ("the legacy text-only runs reduce it") and refutes the framing
that vision perturbation is what degrades alignment. It does **not** support the strict-control sentence as
independent evidence (circular), and the released script cannot regenerate the released JSON (3 configured
artefacts vs 2 stored).

---

## 7. Findings, with severity

### Must-fix

* **M1. The central inference is not licensed by a one-armed control.**
  `strict_control.tex:34-37` ("demonstrated rather than inferred"; "which is the one that carries the mechanism
  claim"). Evidence: only the text-only arm was run; the joint arm has no `results.json` (§S3); the historical
  text-only arm perturbed the whole vision tower and matched the strict arm (§1.1).
* **M2. The disclosure understates the historical convention.** `methodology.tex:22` vs the exact freeze set
  (6,303,744 = 24 × 262,656; 145,170,177 / 151,277,313 = 95.96 %). Rewrite as "every parameter except the 24
  replaced text-side linear weights and biases, including the entire vision encoder, `visual_projection` and
  `logit_scale`".
* **M3. Mechanism sentences contradicted by the paper's own numbers.**
  `discussion.tex:10` ("fine-tuning the visual encoder consistently increases the gap, while fine-tuning only the
  text encoder preserves or even reduces it") and `discussion.tex:44` ("since the visual encoder is untouched").
  Evidence: `outputs/flickr30k_seeds/rq2_text_only/seed*/results.json` (145,170,177 trainable) CGΔ −0.046 ± 0.002,
  indistinguishable from `outputs/strict_freeze/text_only/seed*` (196,608 trainable) CGΔ −0.0465 ± 0.0027.
* **M4. Layered fine-tuning comparison is confounded by the freeze convention.** `introduction.tex:23`,
  `discussion.tex:27`; `paper/scripts/layered_finetune.py:57-58,85-87,135-148`;
  `outputs/layered_ft_results.json` (comparators diverged: CG 1.2865, R@1 0.010 at epoch 1).
* **M5. Supplementary Fig. 8 panel B is computed on pristine vision weights.** `supplementary.tex:261`;
  `paper/scripts/weight_svd_analysis.py:365,372-377`; contradicts panel (D) of the same figure.
* **M6. "Gradient contribution quantification" does not support the visual-fragility sentence.**
  `conclusion.tex:10` vs `outputs/gsnr_results.json` (`v_t_ratio = 1.453`, vision larger).
* **M7. `visual_fragility.tex:12` contradicts `supplementary.tex:261` about where the parameter shifts are.**

### Should-fix

* **S1. The "0 of 199" denominator.** Report 0 of 398 (199 vision / 196 text / 3 top-level) and state that
  `visual_projection` is vision-side by the paper's own definition (`weight_svd_analysis.py:322`).
* **S2. Present the unchanged effective rank as a consistency check, not evidence** (bit-identical by construction:
  no weight change + `dropout = 0.0`). Do not count it as a second line of evidence.
* **S3. Disclose the aborted strict joint run.** `outputs/strict_freeze/both/seed42/best_checkpoint.pt` +
  `run.log:3642` (`trainable=491520`) with `Epoch 4/10 … R@1: 0.685 | Time: 325.6s`, gap check `Centroid: 0.8140`,
  interrupted mid-epoch 5. The ~50-minute cost estimate is derived from it; a reader who inspects the release will
  find it. Either finish it (≈4 h for 5 seeds) or state "started, abandoned after 4/10 epochs" in the caption.
* **S4. Protocol surface.** `methodology.tex:20` says batch 128; Table 2 / Table 4 / Fig. 3 come from batch-64 runs
  (`final_gap.step = 630` vs 320). Table 8's caption says "the same protocol as the main experiment". Say which
  protocol each row belongs to.
* **S5. Experiment count.** 117 excludes the 5 strict runs + frozen reference; update `main_nn.tex:39`,
  `introduction.tex:8`, `visual_fragility.tex:37`, `supplementary.tex:5,12,169`.
* **S6. Noise-sensitivity robustness.** Seed the script (`paper/scripts/noise_sensitivity.py` has no seed), repeat
  over ≥5 draws, report mean ± sd, disclose the non-monotonicity and the σ = 0.003 reversal.
* **S7. Caveat the "Text-only" labels** in Table 2 (`experiments.tex:71`), Table 4 (`:131`), Fig. 3
  (`experiments.tex:93`; `plot_fig3_crossval.py:29`) and Fig. 5 (`experiments.tex:187`) as
  "text-side adapters (backbone trainable)".
* **S8. `visual_fragility.tex:26-27` table rows** — the premise "any strategy perturbing the visual encoder" is not
  the comparison the archived bars perform.
* **S9. Batch-matching of the frozen reference.** `outputs/analysis/strict_control_summary.json:3` reports
  `frozen.vis_L0 = 9.3669` from a different random augmentation than the runs (9.3265–9.4245); because
  `create_dataloaders` returns a `random_split` of the *train* dataset with the train transform
  (`src/dataset.py:404,416-425,23-32`), the "validation" set is augmented. Disclose, or pass `is_train=False` images
  for measurement.
* **S10. `outputs/effective_rank_tracking.json` is not regenerable** by `paper/scripts/noise_sensitivity.py`
  (`:252-324` writes three configs; the artefact has two).

### Note

* **N1. Terminology.** The statistic is over encoder layer hidden states (pre-`visual_projection`); the supplement
  calls it "image embeddings" (`supplementary.tex:173,272`). Fix the label.
* **N2. Estimator ceiling.** `exp(entropy)` on a 16 × D pooled matrix is capped at 16; report the cap and prefer
  n = 64.
* **N3. `strict_freeze_control.py:191`** computes `A @ B` where the update is `(A B)ᵀ`; harmless for the Frobenius
  norm but it needs a comment.
* **N4. `outputs/gsnr_results.json`** retains the unused, mis-signed `text_advantage_pct = −639.8`
  (`gsnr_analysis.py:149-152`).
* **N5.** The GSNR text-only arm's final loss (4.15) is ~16× the strict-freeze text-only final loss (0.253 train /
  0.521 val, `outputs/strict_freeze/text_only/seed42/results.json:48-49`); the Fig. 11 caption's "text-only
  converges to a higher loss" rests on a 45-step run under the old convention.
* **N6. Positive result worth stating.** `n_trainable_params == n_trainable_reported_by_trainer == 196,608` in all
  five strict runs is an independent end-to-end confirmation that the freeze reached the optimizer
  (`src/trainer.py:243-244`, `src/peft_methods.py:137-138`). The zero deltas across 398 tensors additionally prove
  the trainer's loader and the pristine reference directory hold identical weights.
* **N7. `visual_fragility.tex:10`** ("fewer degrees of freedom ⇒ less disruption") is asserted, not measured, and
  reads against the ordinary "at capacity ⇒ brittle" intuition.
* **N8. `conclusion.tex:10`** cites "the concentration of trainable parameters in vision encoders"; in the paper's
  own historical configuration the concentration was in the *whole* model (96 %).

---

## 8. What would settle the mechanistic claim

1. **Run the strict-freeze joint arm** (5 seeds, ~50 min each on the authors' measured epoch time). Without it the
   comparative claim has no evidence, and the section already measures the cost of obtaining it.
2. **Re-run the historical "text-only" configurations with a vision-side probe** — i.e. record `max|Δ|` and per-tensor
   `‖ΔW‖_F` for the *vision* encoder in the mixed runs, not only the adapters. This turns §1.1's arithmetic inference
   into a direct measurement and makes the "vision perturbation is inert in the text-only arm" statement explicit.
3. **Correct the disclosure wording** (M2) and the three contradicted mechanism sentences (M3, M7), and demote the
   effective-rank observation to a consistency check (S2).
4. **Re-run the layered arms under one convention** (M4) or drop the 0.427/0.510 comparison.
5. **Rebuild panel B of Supplementary Fig. 8** from a checkpoint that stores backbone weights, or label it
   "adapter-only reconstruction" (M5).

---

## 9. Appendix — checks performed and their results

| Check | Result |
|---|---|
| Reconcile historical text-only trainable count | `151,473,921 − 145,170,177 = 6,303,744 = 24 × (512²+512)` — exact; frozen set = the 24 replaced text q/v weight+bias tensors |
| Fraction of model trained in historical "text-only" | 145,170,177 / 151,277,313 = **95.96 %** |
| Vision/text/other tensor counts | 199 / 196 / 3, derived independently from CLIP structure; matches `backbone_delta.*.tensors` in all six strict JSONs |
| Strict-run trainable params | 196,608 = 24 × (8×512 + 8×512); joint arm = 491,520 = 24×12,288 (vision, d=768) + 24×8,192 (text, d=512) |
| Vision rank change (strict) | max \|Δ\| = 0 across 12 layers × 5 seeds |
| Text rank change (strict) | non-zero in all 5 seeds (e.g. seed42 `txt_L11` 9.7622 → 11.3427) |
| Mixed 5-seed text-only CGΔ / R@1 | −0.048, −0.044, −0.048, −0.043, −0.047 (mean −0.046) / 0.616, 0.610, 0.638, 0.620, 0.621 (mean 0.621) |
| Strict 5-seed text-only CGΔ / R@1 | −0.0465 ± 0.0027 / 0.6238 ± 0.0049 |
| Noise ratio at σ = 0.1 | 9.2199 / 3.5461 = 2.600 ✔ |
| Noise monotonicity | **fails** — vision drop at σ = 0.003 (0.71 %) < text drop (2.13 %) |
| GSNR | vision 0.4510 > text 0.3104 (ratio 1.453); `gsnr_results.json` == `gsnr_results_pre_fix.json` |
| Historical vision rank | 9.386 → 6.828 → 6.164 → 7.021 (`outputs/effective_rank_tracking.json`, `text-only`) |
| Partial joint strict run | `run.log:3642` onward; 4/10 epochs; epoch-4 CG 0.8140, R@1 0.685; ~325.6 s/epoch |
| Batch sizes | legacy `outputs/flickr30k/*`: step 630 ⇒ batch 64; seeds/alpha/strict: step 320 ⇒ batch 128 |
| Doc validation | `src/peft_methods.py:107,129` confirm Adapter/Prefix freeze-first (`methodology.tex:22` correct for those paths) |
| CLIP dropout | `models/clip-vit-base-patch32/config.json`: `dropout = 0.0`, `attention_dropout = 0.0` in both towers |
