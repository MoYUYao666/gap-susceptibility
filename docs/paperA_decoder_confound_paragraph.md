# Paper A — the two decoder-VLM experiments: bounded paragraph and provenance

Audience: the author of Paper A (`paper合/`, Neurocomputing `NEUCOM-D-26-23760`).
Status: analysis only. No `.tex` file was edited, no archive was modified; the two files
produced by this task are `outputs/analysis/paperA_decoder_confound.json` and this note,
both generated from `tools/_p1580_paperA_decoder_confound.py`, which reads the archives and
runs no training.

The problem this note answers: supplement Section E (Table `tab:vlm`, Qwen2-VL-2B) reports that
adaptation **narrows** the measured gap, while Section G (Table `tab:llava`, LLaVA-1.5-7B)
reports that it **widens** it. The manuscript states both results but explains neither the
conflict nor the confound behind it.

---

## (a) Paragraph suitable for the manuscript

> The two decoder experiments move the measured gap in opposite directions, and the difference is
> not attributable to any single factor on this evidence. On Qwen2-VL-2B-Instruct a contrastive
> objective narrows $DG^*$ under all three adaptation arms, by $98.57\pm0.44\%$ (both-position),
> $96.74\pm0.29\%$ (text-only) and $89.41\pm1.01\%$ (vision-only) over thirteen seeds with disjoint
> seed ranges, whereas on LLaVA-1.5-7B a caption-generation objective widens it under all three, by
> $+73.27\pm7.54\%$ (text-only), $+121.48\pm16.33\%$ (vision-only) and $+95.66\pm7.91\%$
> (both-position) over three seeds. Each model's own sign is stable --- it survives the change of
> text-side convention on LLaVA, no archived Qwen run of any construction increases the gap, and no
> arm mean changes sign on resampling of seeds --- but the two experiments differ simultaneously in
> training objective, parameter scale ($2$B against $7$B), pretraining family, dataset (Flickr30k
> against MS-COCO) and training-set size ($320$ against $1500$ pairs), so the sign cannot be assigned
> to the objective, to scale or to the data here. Isolating it requires holding model, data, budget
> and adaptation-site specification fixed and varying only the loss, which the present archive does
> not contain.

Four sentences; drops into a supplement section without disturbing the existing text. A shorter
two-sentence version, if space is tighter, is the first sentence plus the final one.

**Sign caution.** Paper A prints a `+` sign on a *reduction* in Table E
(`Reduction $+98.57\pm0.44\%$`) and on an *increase* in Table G
(`Change vs frozen $+73.27\pm7.54\%$`). The column headers differ and the prose disambiguates, but
one glyph denotes opposite directions in the two tables. Every number in this note and in the JSON
is instead a single signed quantity, `(after - before) / before * 100`, where negative means the gap
narrowed.

---

## (b) Provenance table

Every number below was recomputed from the archived per-run records by
`tools/_p1580_paperA_decoder_confound.py`, which asserts each value against the manuscript before
writing its output. `{arm}` is `text_only`, `vision_only` or `both`; the run index is the seed.

### Qwen2-VL-2B-Instruct — supplement Section E, Table `tab:vlm`

| Reported number | Value | JSON path | Field |
|---|---|---|---|
| untrained baseline $DG^*$ | `0.7778259515762329` | `outputs/vlm_clean_cloud/frozen_baseline.json` | `dg_star` |
| evaluation pairs | `320` | `outputs/vlm_clean_cloud/frozen_baseline.json` | `n_pairs` |
| seeds per arm | `13` (39 records total) | `outputs/vlm_clean_cloud/{arm}_seed*.json`; aggregate `outputs/vlm_clean_summary.json` | `seed`; `verification.n_records` |
| both-position $DG^*$ after | `0.011143` | 13 × `outputs/vlm_clean_cloud/both_seed*.json` | `dg_star[2]` (epoch 3) |
| both-position reduction | `-98.567% ± 0.439` | `outputs/vlm_clean_summary.json` | `per_arm.both.reduction_mean`, `per_arm.both.reduction_sd` |
| text-only $DG^*$ after | `0.025328` | 13 × `outputs/vlm_clean_cloud/text_only_seed*.json` | `dg_star[2]` |
| text-only reduction | `-96.744% ± 0.291` | `outputs/vlm_clean_summary.json` | `per_arm.text_only.reduction_mean`, `per_arm.text_only.reduction_sd` |
| vision-only $DG^*$ after | `0.082393` | 13 × `outputs/vlm_clean_cloud/vision_only_seed*.json` | `dg_star[2]` |
| vision-only reduction | `-89.407% ± 1.014` | `outputs/vlm_clean_summary.json` | `per_arm.vision_only.reduction_mean`, `per_arm.vision_only.reduction_sd` |
| seed ranges 97.72–99.44 / 95.86–97.07 / 87.08–90.74 | min/max of the 13 runs | as above | `dg_star[2]` |
| objective is contrastive | symmetric InfoNCE | `tools/_p1150_qwen_clean_sweep.py` | line 253, `loss = (F.cross_entropy(logits, labels) + F.cross_entropy(logits.T, labels)) / 2` |

### LLaVA-1.5-7B — supplement Section G, Table `tab:llava`

| Reported number | Value | JSON path | Field |
|---|---|---|---|
| untrained baseline $DG^*$ | `0.3565603693326314` | `outputs/canonical_caption_metric.json` | `runs.frozen.clean.dg_star` |
| held-out pairs | `500` / 63 batches | `outputs/llava_canonical_cloud/frozen_s42.json`; `outputs/canonical_caption_metric.json` | `n_eval`; `runs.frozen.clean.n_batches` |
| seeds per arm | `3` (`s42`, `s123`, `s456`) | `outputs/canonical_caption_metric.json` | run tags |
| text-only $DG^*$ after | `0.617809` | `outputs/canonical_caption_metric.json` | `runs.text_only_s{42,123,456}.clean.dg_star` |
| text-only change | `+73.269% ± 7.536` | same | three `clean.dg_star` values, ddof=0 |
| vision-only $DG^*$ after | `0.789693` | same | `runs.vision_only_s{42,123,456}.clean.dg_star` |
| vision-only change | `+121.475% ± 16.331` | same | three `clean.dg_star` values, ddof=0 |
| both-position $DG^*$ after | `0.697650` | same | `runs.both_s{42,123,456}.clean.dg_star` |
| both-position change | `+95.661% ± 7.914` | same | three `clean.dg_star` values, ddof=0 |
| per-seed ranges 67.61–83.92 and 86.04–105.43 | min/max of 3 runs | same | `clean.dg_star` |
| objective is generation | caption cross-entropy | `tools/_p820_llava_sites.py` | `out.loss` with labels, backward at line 617 |
| adapters behind these numbers | 9 non-empty `.pt` | `outputs/llava_canonical_cloud/*_ckpt.pt` | file inventory |

**Dispersion convention.** Both tables use the **population** standard deviation (`ddof=0`) of the
per-seed values divided by the single baseline. `ddof=1` does not reproduce either table
(it is 1.041× larger for the 13-seed Qwen arms and 1.225× larger for the 3-seed LLaVA arms). The
sample values are recorded alongside in the JSON.

**Three provenance defects found while assembling this table** (detailed in
`outputs/analysis/paperA_decoder_confound.json` → `provenance_findings`):

1. `docs/provenance_manifest.json` maps `tab:vlm` → `outputs/vlm_instruction_dynamics.json` and
   `tab:llava` → `outputs/llava_instruction_dynamics.json`, both marked `"status": "verified"`.
   Neither file carries the tables' numbers: they contain τ-versus-λ instruction-dynamics probes
   with no `dg_star` field, no `0.7778`, no `0.3566` and no arm reductions. The tables' real sources
   are those listed above. This directly contradicts the repository's standing provenance rule and
   should be corrected before any further audit run relies on the manifest.
2. `outputs/canonical_caption_metric.json` declares its adapters at
   `outputs/llava_canonical/*_ckpt.pt`; that directory does not exist locally. The nine adapters are
   in `outputs/llava_canonical_cloud/`. Path label only — the adapters are present and non-empty.
3. `outputs/llava_canonical_cloud/*.json` records an untrained `dg_star_before` of `0.814593874491178`,
   which matches neither variant of `canonical_caption_metric.json` (`0.3885` prompt, `0.3566` clean).
   It is a third, not-yet-reconciled LLaVA construction. It is used in this note **only** as a
   qualitative check that all three arms increase the gap, never for a reported magnitude.

---

## (c) Placement recommendation

**Recommended: a new Section H at the end of `paper合/sections/supplement.tex`,** immediately after
Section G (file currently ends at line 389). Reason: the confound spans two sections, and placing it
inside G would make Section E's numbers look like G's responsibility.

Suggested heading: `\section*{H. What the two decoder experiments do and do not separate}`
Suggested label: `\label{sec:decoderconfound}`.

**Acceptable alternative:** append the paragraph as a closing paragraph of Section G, after line 389.
Section G already ends by discussing its own measurement conventions, so a scope paragraph there reads
continuously; the cost is that the reader meets the confound only after the LLaVA table.

**Optional, main text.** `paper合/sections/discussion.tex` lines 29–36 already give the combined
reading and already say the two objectives are "not the same intervention". Note one stale clause at
the end of that paragraph: "whether the framework extends to generation-oriented objectives, as
distinct from decoder architectures, remains untested" — Section G *is* a generation-oriented
objective, so this clause now reads inconsistently with the paper's own supplement. Flagging only;
not edited.

**Do not** present the two tables' magnitudes as comparable anywhere. That caution is already in both
table captions and should stay.

---

## (d) What remains uncontrolled

Between the two experiments the following differ **simultaneously**; no archived run isolates any one
of them:

| Factor | Qwen2-VL-2B | LLaVA-1.5-7B | Separated by the archive? |
|---|---|---|---|
| Training objective | symmetric InfoNCE (contrastive) | caption-generation cross-entropy | **No** |
| Parameter scale | 2B | 7B | **No** |
| Base model family | Qwen2-VL (Qwen vision encoder + Qwen2 LM) | LLaVA-1.5 (CLIP ViT-L/14-336 + Vicuna-7B) | **No** |
| Training dataset | Flickr30k | MS-COCO | **No** |
| Training-set size | 320 pairs | 1500 pairs | **No** |
| Evaluation pairs | 320 | 500 | **No** |
| Seeds per arm | 13 | 3 | **No** |
| Adaptation-site specification | LoRA α=16, dropout 0.05, tower-specific targets | LoRA on vision encoder, LM and projector | **No** |
| Text-side convention of $DG^*$ | caption span after last image token | caption-token span, `labels != -100` | Partly — two LLaVA constructions archived, both increase, so this factor does not carry the sign |

Controlled and identical: arm definition, strict freezing (only adapters trainable), LoRA rank 8,
3 epochs, batch 2, learning rate 1e-4, bfloat16, image side of $DG^*$ (mean pool over image-token
positions, L2, no projection), $DG^*$ as paired squared distance, and comparison against an untrained
baseline.

**What the archive does separate** (quantified, and safe to state):

- **Seed stability.** All 39 Qwen runs (13 seeds × 3 arms) narrow the gap; the three arms have disjoint
  seed ranges. All 9 LLaVA runs under the manuscript's construction widen it. No arm mean flips sign.
- **Measurement convention, within model.** The Qwen sign survives three archived constructions: the
  corrected caption-span one (`vlm_clean_cloud::dg_star`, large reductions), the superseded projected
  all-token one (`vlm_clean_cloud::legacy_dg_star`, flat near 2.0 and therefore unresolvable), and the
  pre-2026-10-17 13-seed archive (`outputs/analysis/vlm_bf16_detail.json::per_run.*.*.dg_rel_pct`,
  baseline = epoch 1, **39 of 39 runs report a reduction**). The LLaVA sign survives two text-side
  conventions on the *same nine adapters* (caption span → `+73.27`/`+121.48`/`+95.66`; instruction
  prompt → `+35.68`/`+7.24`/`+33.35`). So the sign difference is not an artefact of how the text side
  is pooled.
- **One caveat on the LLaVA arm means.** Under the instruction-prompt construction, one of the nine
  LLaVA runs *narrows* the gap (`vision_only_s123`, `-1.508%` in
  `outputs/llava_canonical_cloud/vision_only_s123.json::dg_star_rel_change`), so "every arm widens it"
  is 3/3 on arm means but 8/9 on individual runs under that construction; under the construction the
  manuscript actually reports it is 9/9.

**What the archive does not contain** (do not invent it):

- No LLaVA-1.5-7B run under a contrastive objective, and no Qwen2-VL-2B run under a caption-generation
  objective. Searched every script in `tools/` and `exp/` that names either model for a contrastive
  training loss (InfoNCE / `log_softmax` / `logits.T`) and for a generative one (`out.loss` + labels).
- No scale-matched decoder pair under one objective: the archive holds exactly one decoder model per
  scale.
- No matched training budget; 320 against 1500 pairs.
- `tools/_p1135_qwen_sites.py` declares `MODEL = "Qwen/Qwen2.5-VL-7B-Instruct"` and a generation loss
  and would be the closest thing to a scale-matched generative run, but its `OUT_DIR`
  (`outputs/qwen_sites`) does not exist and no JSON for it is present under `outputs/` — it was never
  run or never pulled back.
- The Qwen2.5-VL-7B feasibility pilot (`DG* 1.2879 → 1.2424`, `-3.531%` on 8 held-out pairs) exists
  **only as prose** in `docs/llava_canonical_2026-10-17.md` and `HANDOFF.md`. No archived JSON or field
  carries it and the arm is not stated, so under the repository's provenance rule it cannot be cited
  as evidence in either direction.
- `outputs/analysis/p3_smolvlm_family*.json` is a decoder model but records an energy field `E` over 20
  samples (`tools/_p1568_smolvlm_run.py`) — no gap field, so it cannot enter this comparison.
- Seed-level *variation* exists but only quantifies precision. It cannot separate objective from scale,
  because both models' signs are already unanimous.

**Related archive evidence, with a scope limit.** `outputs/analysis/dataset_flip_strict.json`
(`r4.<dataset>|<arm>.mean`) shows that changing dataset from Flickr30k to MS-COCO **flips the best
arm** among contrastive dual-encoders (text-only `-0.03038` against both `-0.02037` on Flickr30k;
both `-0.08860` against text-only `-0.04301` on COCO) **without flipping the sign** — every arm
narrows the centroid gap on both datasets. This is dual-encoder strict freezing, not decoders, so it
does not settle the decoder question, but it is the reason dataset cannot be dismissed as a candidate
explanation and should be named as uncontrolled rather than ruled out.

**Definitive control experiment (design only — not executed).** Hold model, data, budget, seed set and
adaptation-site specification fixed and vary only the loss. Take one LLaVA-1.5-7B checkpoint with the
toolchain already archived in `tools/_p820_llava_sites.py` so preprocessing, target modules and
measurement are identical to the existing run, and define two arms: (i) caption-generation
cross-entropy, (ii) the symmetric InfoNCE loss ported from `tools/_p1150_qwen_clean_sweep.py` line 253.
Both train on the same 1500 MS-COCO pairs, 3 epochs, batch 2, rank 8, lr 1e-4, bfloat16, and are
evaluated with `tools/_p1145_clean_gap_measure.py` so $DG^*$ is the definition Table G already uses.
Analysis is a 2 × 3 design (objective × arm) on the same seeds, with the frozen baseline measured once
per objective since the loss does not affect the untrained model. **Decision rule:** if the contrastive
arm narrows $DG^*$ and the generation arm widens it in the same model, the objective is sufficient and
scale is excluded; if both arms move the same way, the objective is excluded and the next control is
one objective at 2B against 7B within one family. Cost, from the archived LLaVA rate of 0.95 s/step at
2250 steps per run (`docs/llava_canonical_2026-10-17.md`), is six new training runs plus evaluation.
Even then, what stays uncontrolled is that the two objectives may need different learning rates to be
compared fairly (the archived runs use one rate for both), that a single model pair still cannot
separate family from scale, and that the 320-pair and 1500-pair budgets remain unequal unless the Qwen
side is re-run.

---

## Reproducing this note

```
python tools/_p1580_paperA_decoder_confound.py
```

Reads only; rewrites `outputs/analysis/paperA_decoder_confound.json`. The script asserts every
manuscript number it recomputes (Tables E and G, the per-arm spreads, the seed ranges, the documented
per-seed values of the second LLaVA construction) and fails loudly on any drift, so a future change to
the archives cannot silently invalidate this note.