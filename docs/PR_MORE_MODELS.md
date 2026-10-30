# PR R2.3 / R1.4 — broader model coverage: a non-contrastive vision tower, and a larger VLM

**Task**: `task-8` — answer R2 ("*Broader validation on larger datasets and modern VLMs is
needed to support the general claims*") by testing the adaptation-position ordering outside the
contrastive dual-encoder family, and by establishing honestly whether a 7B VLM can be run here.

**Status legend**: ✅ done with evidence · ⏳ running, blocker named · ⛔ infeasible, with the
measurement that shows it.

> **Every number below is rendered from JSON by `tools/_p293e_report.py`.** Nothing is
> transcribed by hand. Each table names the archive file and field that carries it.

## 0. What this report is, and what it is not

There is **no non-contrastive pretrained image–text dual encoder available locally**, and none
exists to be downloaded under this project's rules. DINOv2 is self-supervised on images alone
and therefore has **no text tower and no text space to be aligned with**. The experiment below
is consequently built from three parts:

    DINOv2-base vision tower  +  CLIP ViT-B/32 text tower  +  a shared 512-d projection head

This is a **heterogeneous pairing, not a native model.** Accordingly, the result is reported as
*"on a heterogeneous pairing whose vision tower is not contrastively pretrained"*. It must not
be written up as *"on DINOv2"* or as a result about *"non-contrastive models"*, because the text
side of this model is contrastively pretrained and the head is fitted here.

Two design choices bound how far the result reaches, and both are measured rather than asserted:

* **The head is fitted on a split disjoint from both training and evaluation** (Flickr30k train
  captions `[5000, 10000)`, while the arms train on `[0, 5000)` and are scored on the 500-pair
  validation gallery). It is then frozen for every arm, so the three arms still differ only in
  where the adapters sit.
* **A random-head condition is run as a control**, which bounds how much of the alignment is
  supplied by the head rather than by the adapters. Without it, "text-only preserves alignment"
  would be indistinguishable from "the fitted head already aligned the space and nothing moved".

### A correction that applies to this new experiment only

The strict-freeze control injects LoRA with `target_modules=["q_proj","v_proj"]`. **DINOv2 names
its attention projections `query`/`key`/`value`**, so that default matches *nothing* on the
vision tower: measured, the vision side received 0 LoRA layers and the only trainable parameters
(196,608) came from the text tower — a silently fake experiment. The fix is for each tower to use
its own codebase's projection names (vision `query`/`value`, text `q_proj`/`v_proj`) at the same
rank 8 and alpha 16.

**This is a property of the new experiment and is not a correction to any published number.** The
Lead verified this separately: `tools/_p310_audit_target_modules.py` finds `q_proj`/`v_proj`
present (×24/×24) on CLIP B/32, CLIP B/16, SigLIP and OpenCLIP, absent on DINOv2; and
`tools/_p309_audit_lora_injection.py` scanning 502 archive files finds real injection counts
196,608 (×25), 294,912 (×30), 491,520 (×18), with the 12 files recording
`n_trainable_params = 0` all being `*_frozen` baselines. The paper's archive is unaffected.

## 1. Evaluation protocol actually used (needed to read any number below)

Recorded by `tools/_p293c_protocol_check.py` →`outputs/analysis/dinov2_hetero/protocol_check.json`.

| quantity | value | archive field |
|---|---|---|
| data root that resolves | `.` →`./flickr30k` | `data_dir_used` |
| captions in corpus | 158915 | `corpus_captions_total` |
| `--max-samples` | 5000 | `max_samples` |
| cap applied | **before** the 80/10/10 split | `cap_applied_before_split` |
| split sizes | train 4000 / val 500 / test 500 | `split_sizes` |
| **retrieval gallery** | **500 pairs** | `retrieval_gallery_pairs` |
| **chance R@1** | **0.002** | `chance_R@1` |

The gallery is 500 pairs, not 1000, because `src/dataset.py:401` caps the dataset to
`max_samples` and only then runs `random_split` (`:416-425`). This is what makes the published
R@1 column (e.g. 0.624) interpretable: it is 312× chance, not a near-random number.

## 2. The comparison basis is verified against the published table

Any claim that the ordering "reverses" is a comparison, so the quantity compared has to be shown
to be the same quantity. `tools/_p293d_clip_baseline_check.py` recomputes
`ΔCG = final_gap.centroid_gap − initial_gap.centroid_gap` from the archive and checks it against
every published cell of `tab:position_strict`.

| published row | arm | ΔCG recomputed | ΔCG published | match | R@1 recomputed | R@1 published | match |
|---|---|---|---|---|---|---|---|
| CLIP B/32 r8 | text_only | -0.0465 | -0.0465 | ✅ | 0.6238 | 0.624 | ✅ |
| CLIP B/32 r8 | both | -0.0258 | -0.0258 | ✅ | 0.6932 | 0.693 | ✅ |
| CLIP B/32 r8 | vision_only | +0.0106 | +0.0106 | ✅ | 0.6800 | 0.680 | ✅ |
| CLIP B/32 r4 | text_only | -0.0304 | -0.0304 | ✅ | 0.6222 | 0.621 | ❌ |
| CLIP B/32 r4 | both | -0.0204 | -0.0204 | ✅ | 0.6796 | 0.679 | ❌ |
| CLIP B/32 r4 | vision_only | +0.0166 | +0.0166 | ✅ | 0.6698 | 0.670 | ✅ |
| CLIP B/16 r4 | text_only | -0.0166 | -0.0166 | ✅ | 0.6502 | 0.651 | ❌ |
| CLIP B/16 r4 | both | +0.0124 | +0.0124 | ✅ | 0.7070 | 0.707 | ✅ |
| CLIP B/16 r4 | vision_only | +0.0376 | +0.0376 | ✅ | 0.6860 | 0.686 | ✅ |
| OpenCLIP r4 | text_only | +0.0802 | +0.0802 | ✅ | 0.6366 | 0.643 | ❌ |
| OpenCLIP r4 | both | +0.0864 | +0.0864 | ✅ | 0.6818 | 0.680 | ❌ |
| OpenCLIP r4 | vision_only | +0.0996 | +0.0996 | ✅ | 0.6698 | 0.672 | ❌ |

**ΔCG reproduces 12/12 published cells exactly at the published precision** — so a ΔCG measured on the new backbone is directly comparable with the paper's table, and the reversal question is well posed.

The **R@1** column needs care, and the cause is identification rather than drift. `tools/_p293j_r1_provenance_exhaustive.py` grouped **every** archived `results.json` that carries `initial_gap`, `final_gap` and `final_task_metrics.R@1` (418 runs in 175 groups) and asked, per published cell, which group's **complete seed set** reproduces it at the published precision. The twelve cells split three ways:

| R@1 provenance | cells | which |
|---|---|---|
| reproduced by the row's own tree | 6 | `CLIP B/32 r8 / text_only`, `CLIP B/32 r8 / both`, `CLIP B/32 r8 / vision_only`, `CLIP B/32 r4 / vision_only`, `CLIP B/16 r4 / both`, `CLIP B/16 r4 / vision_only` |
| reproduced only by a **different** archive group | 3 | `OpenCLIP / text_only`, `OpenCLIP / both`, `OpenCLIP / vision_only` |
| **not reproducible at the printed precision** | 3 | `CLIP B/32 r4 / text_only`, `CLIP B/32 r4 / both`, `CLIP B/16 r4 / text_only` |

* `CLIP B/32 r4 / text_only` — published R@1 0.621; the row's own tree gives 0.6222 from its complete seed set.
* `CLIP B/32 r4 / both` — published R@1 0.679; the row's own tree gives 0.6796 from its complete seed set.
* `CLIP B/16 r4 / text_only` — published R@1 0.651; the row's own tree gives 0.6502 from its complete seed set.

For the OpenCLIP row this is decisive rather than incidental: its ΔCG matches `outputs/strict_freeze_oclip/r4` (rank 4) exactly, while **all three** of its R@1 values are reproduced by `outputs/strict_freeze_openclip` (rank 8), whose seeds differ (42— 024 against 42— 011). The two halves of that row therefore come from two different runs.

**Why seed-subset matches are not reported as a source.** Every one of the three unreproducible cells *is* reachable if one is allowed to pick a seed subset instead of the complete seed set. That is a coincidence, not a provenance: `tools/_p293l_subset_null_check.py` enumerates 5392 subsets of size 3—, whose means round to only 338 distinct 3-decimal values between 0.001 and 0.714, so a uniform spread over that grid hits any chosen target about **0.30%** of the time. Consistent with that, 13 subsets match 0.679, 4 match 0.651 and 11 match 0.621 — a subset match at this precision therefore carries no information, and the cells are described as *not reproducible from any group's complete seed set* rather than as having a subset source.

**Correction to this task's own earlier wording.** A first pass called these cells "no archive source"; that was too strong, because it depended on a subsearch this report had not quantified. A second pass then called them "reachable by subset" — also wrong, for the reason just measured. The wording used here ("not reproducible from any group's complete seed set") is the one the evidence supports, and it neither over- nor under-claims.

The root enabler is that neither the `experiment` field nor the run directory identifies a run uniquely on its own — two OpenCLIP trees both name their runs `strict_text_only` / `strict_both` / `strict_vision_only`. The Lead audited this independently (`tools/_p321_openclip_search.py`, `_p322_strict_final_match.py`, `_p323_find_r1_field.py`, `_p325`—–_p330`) and discloses the resulting R@1 caveat in the `tab:position_strict` caption of the manuscript.

**Consequence for this report**: every cross-model statement below rests on ΔCG only, which is exact for all twelve cells. No R@1 comparison is made across models, and no claim is made here about which published R@1 value is correct — the report only records which archive unit reproduces which cell.

## 3. Part A — the three adaptation positions on a non-contrastive vision tower

### 3.0 Read this before any number in this section

**(a) This is a heterogeneous pairing, not a model.** The system is

    DINOv2-base vision tower  +  CLIP ViT-B/32 text tower  +  a 512-d projection head,

with the head fitted on a split disjoint from both training and evaluation (`[5000,10000)`) and
then frozen. Every conclusion below is therefore about *"a heterogeneous pairing whose vision
tower is not contrastively pretrained"*. It must not be reported as *"on DINOv2"* or as a result
about *"non-contrastive models"*: the text tower **is** contrastively pretrained and the head is
fitted here.

**(b) n = 1 seed per arm (seed 42).** The paper's strict-freeze rows are five-seed means. With one
seed per arm there is **no seed dispersion**, so these numbers establish a **direction of
ordering**, not a magnitude. They are **not directly comparable with the magnitudes in
`tab:position_strict`**.

**(c) The InfoNCE temperature differs from the paper's — so this ΔCG must not be placed beside
the published ΔCG values.** The paper's runs use the `logit_scale` that ships in the CLIP
checkpoint, exp(4.605170) = **100.0**; this experiment hard-codes `LOGIT_SCALE_INIT` =
2.6592 (the value named in `config.json::logit_scale_init_value`, *not* the value in the weights),
i.e. a temperature of **14.2857**. The two runs therefore train under objectives that differ by a
factor of **7.00× in temperature**.

| source | `logit_scale` | exp (temperature) |
|---|---|---|
| `models/clip-vit-base-patch32/pytorch_model.bin` (weights) | 4.605170 | **100.0000** |
| `config.json::logit_scale_init_value` | 2.6592 | 14.2857 |
| **this experiment (hard-coded, frozen)** | **2.6592** | **14.2857** |

Source: `outputs/analysis/logit_scale_verify.json` (`tools/_p366_verify_logit_scale.py`).
Also measured: **no archived `results.json` records a `logit_scale` field at all**, so a run's
actual temperature cannot be recovered from the archive — a traceability gap in its own right.

**What this does and does not affect.** It does **not** affect the definition of ΔCG, and it does
**not** affect the comparison *between the three arms here*, which share one temperature. It
**does** invalidate placing this ΔCG beside the published ΔCG values in magnitude terms — **including the earlier suggestion in this project that −0.39 merely "falls inside the BioCLIP
range −0.29…−0.45". That comparison is withdrawn**: different temperature, so "same order"
is not established. The BioCLIP row is still reported below as the only *qualitative* precedent
for a non-contrastively-pretrained backbone, with the temperature caveat attached.

**(d) This experiment supplies a frozen-baseline measurement the paper's archive lacks.** The
audit found that `outputs/strict_freeze/frozen/results.json` has only six keys and **no**
CG/DG/R@1, and `outputs/flickr30k/baseline_frozen/results.json` has
`final_task_metrics = null`. A frozen CG/DG/R@1 for CLIP B/32 exists here (§3.1) but is a **new
measurement**, not an archived one; the audit separately measured CLIP B/32 frozen R@1 = 0.5770 on
the 500-pair gallery (draw 0). Neither should be cited as if it came from the paper's archive.

**(e) Image normalisation is CLIP's, not DINOv2's.** The dataloader applies CLIP mean/std
(`src/dataset.py:19-20`, recorded in every `results.json` as `image_normalisation`). DINOv2 was
pretrained under ImageNet statistics, so the vision tower receives out-of-distribution inputs.
This is a **limitation of the setting**, not a detail: it can degrade the frozen baseline and thus
make the gap easier to close. Left as-is for comparability with the control's own protocol, and
flagged here.

**(f) The evaluation gallery carries training augmentation — confirmed in source and by
measurement.** `create_dataloaders` applies the `is_train=True` transform to the object that is
later `random_split` into "val" (`src/dataset.py:404` then `:416-425`), and a `Subset` keeps that
transform, so the gallery images pass through `RandomHorizontalFlip` + `ColorJitter`. Confirmed at
source level, and measured: reading the same index twice differs by `max|Δ|` = 3.5568 / 3.8270 /
0.2551, and 66 files call `create_dataloaders` without disabling the random transform (including
`experiments/main.py`, the source of the paper's main table).

The audit bounds the consequence by re-evaluating one frozen checkpoint six times
(`outputs/analysis/gallery_noise_cg.json`, `tools/_p363_gallery_noise_cg.py`):

| quantity | mean | sampling sd | range | repeats / gallery |
|---|---|---|---|---|
| CG | 0.818674 | **0.000249** | 0.000698 | 6 / 500 pairs |
| DG | 0.865573 | **0.000306** | 0.000798 | 6 / 500 pairs |
| R@1 (i2t) | 0.578667 | **0.005497** | 0.014000 | 6 / 500 pairs |

The same measurement reproduces the paper's archived frozen gap: this run's CG mean 0.818674 against `outputs/flickr30k/baseline_frozen/results.json::initial_gap::centroid_gap` = 0.818501 (difference 0.000173).


So arm-to-arm **ΔCG** comparisons are robust — the sampling noise is roughly three orders of
magnitude below the arm differences — while **R@1 differences below ~0.006 must not be
interpreted**. An earlier 300-pair estimate (CG sd 0.00048, DG sd 0.00041, R@1 sd 0.00714) is
**superseded** by this 500-pair measurement. The audit's N=12 estimate will supersede it again
when it lands. Every CG/DG/R@1 below remains one draw from a stochastic gallery, so ΔCG is
reported as a **draw-robust comparison**, not an exact effect size.

**(g) Field availability differs between arms.** The `lora_update_*` fields were added after the
first arm finished (a review caught that the naive placement would have zeroed the trained
matrices). `text_only/seed42` therefore has them **recovered from its checkpoint** by
`tools/_p293m_recover_lora_norm.py`, with the provenance marked in the JSON
(`note: computed from the checkpoint, NOT measured in-process`). The report never presents a
recovered value as if it had been measured live.

**(h) This pairing has no single pre-training objective, so it cannot confirm or refute the
paper's grouping rule.** The paper's rule —"contrastively pre-trained backbones put text-only
first; backbones trained otherwise put both first" — is *defined over a jointly pre-trained
dual encoder*, because that is what gives a backbone a single objective to be grouped by. This
system is heterogeneous: a self-supervised vision tower plus a contrastively pre-trained text
tower plus a head fitted here. **There is no one objective to group it under.** Therefore the
three-arm result can only ever be reported as *the internal ordering of these three arms in this
heterogeneous setting*, and its agreement or disagreement with the paper's pattern is an
**observation, not a confirmation or a refutation of the grouping rule**. Establishing the rule
outside contrastive dual encoders would require an architecturally native non-contrastive
image–text model, which does not exist locally.

**(i) A timing artefact that must not be misread as instability.** The per-epoch cost of the
`both` arm rose from 26.4 s/it (epoch 1) to 73 s/it (epoch 3). That is **not** the GPU being
taken away: measured concurrently, utilisation was 100%, SM clock at its boost value
(2670 MHz), temperature 75 °C and system RAM 10.8 GB free, with no other GPU process present.
Part of the apparent slowdown is a **measurement-baseline artefact** — epoch 1 ran while the
project's audit was simultaneously running CPU probes, which masked the arm's true cost — so the
later figure is closer to the standalone steady state. Low board power (~33 W) at 100 %
utilisation indicates a low-arithmetic-intensity workload rather than a throttled device, but the
**cause of the residual step-to-step variation is not established and is left open** rather than
assigned an explanation.

### 3.1 Protocol

Flickr30k, 5000 training captions (4000 train / 500-pair retrieval gallery), 10 epochs, batch
128, AdamW lr $10^{-4}$, LoRA rank 8 / α 16 on each tower's own `query`+`value` (DINOv2) and
`q_proj`+`v_proj` (CLIP text). **Strict freeze**: every backbone parameter `requires_grad=False`;
only the LoRA A/B matrices trainable. The trainer (`src/trainer.py`), gap metrics
(`src/gap_metrics.py`) and retrieval metrics are the unmodified ones the published table was
produced with.

Per-run cross-checks, asserted in code and visible in each run's log:
`text_only` = 196,608 trainable (vision 0 / text 196,608, 24 layers);
`both` = 491,520 (vision 294,912 / text 196,608, 48 layers);
`vision_only` = 294,912. The frozen verification is also recorded: 223 vision + 197 text
pre-existing tensors with **zero** change under strict freezing.


### 3.2 **fitted head** — the head was fitted on the disjoint split `[5000,10000)` and then frozen

Frozen baseline (no training): CG = **0.6769**, DG = **0.7510**, R@1 = 0.2890 (`outputs/analysis/dinov2_hetero/fitted/frozen/results.json`).

| adaptation position | n seeds | ΔCG (mean ± sd) | Δ DG (mean ± sd) | R@1 (mean ± sd) | trainable | vision tensors changed |
|---|---|---|---|---|---|---|
| text_only | 1 | -0.3913 | -0.4462 | 0.354 | 196608 | 0 |
| both | 1 | -0.4099 | -0.4667 | 0.555 | 491520 | 0 |
| vision_only | — | PENDING | | | | |

Ordering by ΔCG, smallest (most protective) first: **both < text_only**.


**What actually moved.** Under strict freezing the pre-existing weights are unchanged by construction, so the freeze verification and the adaptation are two different quantities and are reported separately.

| arm | freeze verification (changed pre-existing tensors) | LoRA update, sqrt(sum ||s*A@B||^2) per tower | LoRA update, sum ||s*A@B|| per tower |
|---|---|---|---|
| text_only | vision 0/223, text 0/197 | 8.3371 (recovered) | 40.1049 (recovered, mean 1.6710/layer) |
| both | vision 0/223, text 0/197 | 11.9478 (recovered) | 81.3920 (recovered, mean 1.6957/layer) |

`text_only/seed42` predates the instrumentation; its values are **recovered from `best_checkpoint.pt`** by `tools/_p293m_recover_lora_norm.py` and marked as recovered in `lora_norm_recovered.json`. Two aggregates are given because they are genuinely different quantities (a root-sum-of-squares against a sum of norms); the root-sum-of-squares is the one comparable with the paper's `lora_update_norms()` (`src/lora.py`) and is the column to quote.

**The one cross-model comparison this section can make.** Taking the root-sum-of-squares column for the text tower:

| run | text-tower LoRA update (sqrt(sum ||s*A@B||^2)) | source |
|---|---|---|
| CLIP B/32 `strict_freeze/text_only`, 5 seeds | **5.4373** (per-seed 5.3564-5.4919) | `outputs/strict_freeze/text_only/seed*/results.json::lora_update_norm.text` |
| this heterogeneous pairing, `text_only/seed42` | **8.3371** | `.../text_only/seed42/lora_norm_recovered.json` |

→ the text tower is pushed **1.53×** further here, at the same rank, alpha, layer count, tower width, data and optimiser.

**Why the obvious explanation does not work — stated up front.** The two runs use different temperatures (100.0 against 14.2857, §3.0(c)), and it is natural to reach for that. But the direction is wrong: `src/trainer.py:419` forms `logits = logit_scale * I @ T.T` with `logit_scale = exp(self.model.logit_scale)`, so a **smaller** temperature makes the logits smaller, the softmax flatter, and the InfoNCE gradient **smaller** — which would predict a **smaller** learned LoRA update, the opposite of what is measured. The temperature difference therefore cannot explain this, and by the same token the measurement cannot be read as "a non-contrastive backbone pushes the text tower further": some other factor dominates and is not identified here.

This is recorded as an **exploratory observation with a source and no explanation**, deliberately not fitted to a mechanism. It is reported because it is measured, and it is not used in any conclusion below.

* `text_only`: seeds [42] →`outputs/analysis/dinov2_hetero/fitted/text_only/seed42/results.json`
* `both`: seeds [42] →`outputs/analysis/dinov2_hetero/fitted/both/seed42/results.json`


### 3.3 **random head** — control: the head is left at its seeded initialisation, so no alignment was supplied by fitting

Frozen baseline (no training): CG = **0.8717**, DG = **0.9078**, R@1 = 0.0050 (`outputs/analysis/dinov2_hetero/random/frozen/results.json`).

| adaptation position | n seeds | ΔCG (mean ± sd) | Δ DG (mean ± sd) | R@1 (mean ± sd) | trainable | vision tensors changed |
|---|---|---|---|---|---|---|
| text_only | 1 | -0.2988 | -0.3121 | 0.076 | 196608 | 0 |
| both | — | PENDING | | | | |
| vision_only | — | PENDING | | | | |

Ordering by ΔCG, smallest (most protective) first: **text_only**.


**What actually moved.** Under strict freezing the pre-existing weights are unchanged by construction, so the freeze verification and the adaptation are two different quantities and are reported separately.

| arm | freeze verification (changed pre-existing tensors) | LoRA update, sqrt(sum ||s*A@B||^2) per tower | LoRA update, sum ||s*A@B|| per tower |
|---|---|---|---|
| text_only | vision 0/223, text 0/197 | 9.7878 (recovered) | 46.2267 (recovered, mean 1.9261/layer) |

`text_only/seed42` predates the instrumentation; its values are **recovered from `best_checkpoint.pt`** by `tools/_p293m_recover_lora_norm.py` and marked as recovered in `lora_norm_recovered.json`. Two aggregates are given because they are genuinely different quantities (a root-sum-of-squares against a sum of norms); the root-sum-of-squares is the one comparable with the paper's `lora_update_norms()` (`src/lora.py`) and is the column to quote.

**The one cross-model comparison this section can make.** Taking the root-sum-of-squares column for the text tower:

| run | text-tower LoRA update (sqrt(sum ||s*A@B||^2)) | source |
|---|---|---|
| CLIP B/32 `strict_freeze/text_only`, 5 seeds | **5.4373** (per-seed 5.3564-5.4919) | `outputs/strict_freeze/text_only/seed*/results.json::lora_update_norm.text` |
| this heterogeneous pairing, `text_only/seed42` | **8.3371** | `.../text_only/seed42/lora_norm_recovered.json` |

→ the text tower is pushed **1.53×** further here, at the same rank, alpha, layer count, tower width, data and optimiser.

**Why the obvious explanation does not work — stated up front.** The two runs use different temperatures (100.0 against 14.2857, §3.0(c)), and it is natural to reach for that. But the direction is wrong: `src/trainer.py:419` forms `logits = logit_scale * I @ T.T` with `logit_scale = exp(self.model.logit_scale)`, so a **smaller** temperature makes the logits smaller, the softmax flatter, and the InfoNCE gradient **smaller** — which would predict a **smaller** learned LoRA update, the opposite of what is measured. The temperature difference therefore cannot explain this, and by the same token the measurement cannot be read as "a non-contrastive backbone pushes the text tower further": some other factor dominates and is not identified here.

This is recorded as an **exploratory observation with a source and no explanation**, deliberately not fitted to a mechanism. It is reported because it is measured, and it is not used in any conclusion below.

* `text_only`: seeds [42] →`outputs/analysis/dinov2_hetero/random/text_only/seed42/results.json`


### 3.4 The random-head control: is the effect the adapters', or the head's?

The fitted head has **656,384 parameters**, more than either adapter configuration (196,608 / 491,520). So "the text tower is pushed a long way" could in principle be a property of the head rather than of the adaptation site. The control re-runs **the same arm, the same protocol, the same data** with the head left at its seeded random initialisation and never fitted.

| | fitted head | random head |
|---|---|---|
| frozen baseline CG | 0.6769 | 0.8717 |
| frozen baseline DG | 0.7510 | 0.9078 |
| frozen baseline R@1 | 0.2890 | 0.0050 |
| text-only arm ΔCG | -0.3913 | -0.2988 |
| text-only arm ΔDG | -0.4462 | -0.3121 |
| text-only arm R@1 | 0.3540 | 0.0760 |
| text tower LoRA update, sqrt(sum ||s*A@B||^2) | nan | 9.7959 |

**Reading, and it bounds the finding rather than undermining it.** A random head leaves the two towers essentially unaligned to begin with (frozen R@1 0.0050 against 0.2890 for the fitted head), yet adapting **only the text tower still moves the gap by -0.2988** — **76%** of the fitted head's -0.3913 — and lifts R@1 from 0.0050 to 0.0760. So the text-tower adaptation is not an artefact of the head being fitted: the direction and most of the magnitude survive with a random, never-trained head.

**What it does not show**: it does not isolate the head's own contribution to the *absolute* gap. The random head starts from a much larger gap (0.8717 against 0.6769), so the two arms are not measuring the same quantity and their ΔCG values must not be subtracted from one another as if they were. What is comparable is the qualitative fact that the text-only site moves the gap substantially in both settings.

### 3.2.1 Verdict: the ordering of the adaptation sites in this heterogeneous setting

Only the arm comparison is meaningful here; the magnitude is not comparable with the published
table (temperature, §3.0(c)) and there is one seed per arm (§3.0(b)).

| arm | ΔCG | ΔDG | R@1 | trainable (vision side) |
|---|---|---|---|---|
| text-only | -0.3913 | -0.4462 | 0.354 | 196608 (0) |
| both | -0.4099 | -0.4667 | 0.555 | 491520 (294912) |
| frozen (no training) | CG 0.6769, DG 0.7510 | — | 0.289 | 0 |

`vision_only` was **not run**: the Lead's scope decision kept only the two arms needed to fix the ordering direction, because the full three-arm grid would have occupied the single GPU for several more hours. That is recorded as an unrun arm rather than estimated.

**Ordering by ΔCG (smaller = the arm whose gap change is more negative): both < text_only.**
**Ordering by R@1 (largest first): both > text_only.**

**Reading.** Both arms reduce the gap substantially against the frozen baseline (-0.3913 and -0.4099), and the both-position arm reduces it further than text-only, by 0.0186. It also retrieves far better (R@1 0.555 against 0.354) — so on this pairing the arm that closes the gap more is also the arm that retrieves better, i.e. the two orderings **agree** here, whereas on the paper's CLIP rows they run opposite to each other.

The paper reports two orderings to compare against. On its contrastively pre-trained backbones the
smallest ΔCG is **text-only**; on SigLIP and BioCLIP — the two backbones whose objective is not a
batch-softmax over image–text pairs — it is **both**. Here the smaller ΔCG is **both**, i.e. this
pairing lands with the **side of the split occupied by SigLIP and BioCLIP**.

**What this does and does not establish.** It is an observation about the internal ordering of
these arms in a heterogeneous pairing, and under §3.0(g) it **cannot confirm or refute** the
paper's grouping rule, because this system has no single pre-training objective to be grouped by.
It is also one seed, so no dispersion is available and no significance is claimed. What it does
show is that the direction of the site effect is not unique to contrastively pre-trained dual
encoders in this setting, and it does so with the arms differing only in where the adapters sit
(the strict freeze is verified: 0 of 223 vision and 0 of 197 text pre-existing tensors changed).
The random-head control of §3.4 additionally shows the text-tower effect survives when the head is
never fitted, so it is not an artefact of the head.

## 4. Part B — larger / modern VLMs

### 4.1 Qwen2-VL-2B (decoder VLM) — ✅ reused, not rerun

The runs already exist, are bf16, and reproduce bit for bit, so they are **reused rather than
repeated**. To make the reuse checkable instead of asserted,
`tools/_p293b_qwen_reuse_check.py` recomputes the per-arm statistic from the raw trajectories
`outputs/vlm_seeds_bf16/<arm>_seed<N>.json` (field `dg_star`), using the definition in
`src/dg_star_tracker.py`: $DG^* = \overline{\|z_I - z_T\|^2}$ over L2-normalised embeddings.


| arm | n seeds | $DG^*$ reduction (mean ± sd) | min–max | published | reproduced |
|---|---|---|---|---|---|
| both | 13 | 87.94 ± 5.35 % | 73.1-95.1 % | 87.9 ± 5.4 % | ✅ |
| text_only | 13 | 66.47 ± 8.32 % | 47.8-78.8 % | 66.5 ± 8.3 % | ✅ |
| vision_only | 13 | 18.03 ± 8.78 % | 8.5-35.7 % | 18.0 ± 8.8 % | ✅ |

Ordering by DG\* reduction, largest first: **both > text_only > vision_only**.

**Reading.** The decoder VLM agrees with the dual encoders on the *weakest* arm and not on the ordering of the two stronger ones: vision-only is the weakest arm by a margin no seed ordering can close (its largest reduction 35.7% is below text-only's smallest 47.8% and both's smallest 73.1%); the two stronger arms are not resolved against each other (ranges overlap).

### 4.2 LLaVA-1.5-7B — the bf16 question, measured


**4-bit is excluded by project rule, not by preference**: repeating one 4-bit configuration with an identical seed changed the measured gap span from 0.304 to 0.407, because quantised matrix multiplications are not deterministic. A 4-bit LLaVA run would therefore not be reproducible and cannot be evidence here. Only bf16 was attempted.

| quantity | value | source |
|---|---|---|
| model directory | `models\llava-hf` | `disk.model_dir` |
| safetensors shards | 3 | `disk.n_safetensors` |
| weight footprint on disk | **13.157 GiB** | `disk.total_GiB` |
| same weights at 4-bit (for reference) | 3.289 GiB | `disk.int4_GiB` |

## 5. Files, and what to write in the paper

### Deliverables

| artefact | path |
|---|---|
| Part A experiment (heterogeneous strict-freeze control) | `tools/_p293_dinov2_hetero_strict.py` |
| Part A GPU-serial driver / waiter | `tools/_p293_runner.py` |
| Part B1 Qwen reuse verifier | `tools/_p293b_qwen_reuse_check.py` |
| Evaluation-protocol check | `tools/_p293c_protocol_check.py` |
| ΔCG-convention check vs the published table | `tools/_p293d_clip_baseline_check.py` |
| Part B2 LLaVA bf16 feasibility | `tools/_p294_llava_bf16_feasibility.py` |
| This report's renderer | `tools/_p293e_report.py` |
| Part A archive | `outputs/analysis/dinov2_hetero/` |
| Part B1 archive | `outputs/analysis/vlm_qwen_reuse_check.json` |
| Part B2 archive | `outputs/analysis/llava_bf16_feasibility.json` |

### Suggested sentence for the manuscript

See §6 for the text, which is generated from the measured outcome rather than written in advance.

### What this report does **not** claim

* It does not claim any result "on DINOv2" or "on non-contrastive models" — the model is a
  heterogeneous pairing with a contrastively pretrained text tower and a head fitted here.
* It does not use the paper's R@1 column for any cross-model statement (§2).
* It does not use 4-bit results as evidence anywhere.
* It does not treat its ΔCG magnitudes as comparable with `tab:position_strict` (§3.0(c)).

### Process lessons this task produced

Two failures here were structural rather than careless, and both are worth encoding:

1. **Auto-continuation must encode the current scope.** A stage watcher written to "finish the
   grid" relaunched a full three-arm queue after an agreed two-arm scope, and started a
   third arm unattended at 20:47. It was caught and killed within the minute and wrote no result
   file, but the guard belongs in the tool: `_p293_runner.py` now takes `--arms` and the stage
   script refuses to run arms outside it. A watcher's stopping condition has to be the *agreed
   scope*, not "everything that remains".
2. **Never rewrite a file through a PowerShell `Get-Content -Raw | Set-Content` round trip.**
   Doing exactly that double-encoded `tools/_p293e_report.py` under the local ANSI codepage and
   corrupted every non-ASCII character in it, including two `%` format specifiers (which made the
   renderer crash). The project's rule already warned about PowerShell eating `$` and backslashes;
   the sharper form is that the round trip damages a file it merely *rewrites*. Repair scripts:
   `_p293n`, `_p293o`, `_p293p`, `_p293q`, `_p293s`. No archived number was affected.

## 6. Sentence for the manuscript (generated from the measured outcome)

> To test whether the adaptation-site ordering is specific to contrastively pre-trained dual encoders, we repeated the strict-freezing control on a **heterogeneous pairing** whose vision tower is self-supervised on images alone (DINOv2-base) rather than contrastively pre-trained, with a CLIP ViT-B/32 text tower and a projection head fitted on a split disjoint from both training and evaluation and then frozen. With the adapters as the only trainable parameters, the both-position arm changed the Centroid Gap by -0.4099 and text-only by -0.3913, and the both-position arm retrieved better (R@1 0.555 against 0.354, frozen baseline 0.289). The smaller gap change therefore sits at the **both** position — the same side of the paper's split as SigLIP and BioCLIP rather than as the contrastive backbones. Because this pairing has no single pre-training objective, we report it as the internal ordering of these arms in a heterogeneous setting, and **not** as confirmation or refutation of the pre-training-objective grouping; the magnitudes are also not comparable with Table~\ref{tab:position_strict} because the InfoNCE temperature differs, and each arm is a single seed.

> (`vision_only` was not run in this setting, so the third position is not reported; see §3.2.1.)

> The decoder-VLM control (Qwen2-VL-2B, bf16, 13 seeds) is consistent on the weakest arm — adapting the vision tower alone reduces $DG^*$ by only 18.0 ± 8.8 % against 66.5 ± 8.3 % (text-only) and 87.9 ± 5.4 % (both) — but does not resolve the two stronger arms against each other, so we draw no conclusion from it about which site is preferable.
