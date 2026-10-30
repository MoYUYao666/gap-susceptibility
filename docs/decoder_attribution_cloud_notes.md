# Decoder attribution ladder — cloud run notes

Audience: whoever operates the cloud GPU for Paper A. The tool is
`tools/_p1612_objective_control_multimodel.py`; it is a generalisation of the proven local control
`tools/_p1595_qwen_objective_control.py`. Under `--protocol reduced` it reproduces that control's
protocol *fields* (160 pairs, 1 epoch, batch 4, `both` arm, same data, same seed) but not its actual
image resolution — §1 explains why, and it is the first thing to read before quoting the archived
`-73.5 %` / `-14.2 %` pair next to anything this script produces.

Status of everything below: the script, the dry runs, the image-token plumbing, the backbone
equivalence check, both objectives and both model classes were verified locally on an 8 GB card,
including **a complete LLaVA-1.5-7B 4-bit smoke run, which fits that card without OOM**. **No
`--protocol match` run has been executed anywhere yet**, so every wall-clock number in this file is
labelled `measured` or `projected`, and each projection states its basis. Do not silently promote a
projection into a measurement.

---

## 1. What the ladder is for

Paper A Section H (`paper合/sections/supplement.tex`, lines 421–455) ends with the honest statement
that the two decoder experiments differ simultaneously in objective, scale, family, dataset and
budget, so the opposite signs cannot be attributed. Section H.1 adds the local control: at
Qwen2-VL-2B the objective changes the *magnitude* by about a factor of five (contrastive
$-73.5\%$, generative $-14.2\%$) without changing the *sign*.

The ladder is what turns that into an attribution. It runs the same protocol, the same two losses,
the same adaptation arm and the same measurement across four checkpoints, so that objective, scale
and family can be varied one at a time:

| Registry id | Repo | Class | Family | Image side of `DG*` |
|---|---|---|---|---|
| `qwen2vl-2b` | `Qwen/Qwen2-VL-2B-Instruct` | `Qwen2VLForConditionalGeneration` | Qwen2-VL | dynamic, capped by `--image-tokens` |
| `qwen25vl-3b` | `Qwen/Qwen2.5-VL-3B-Instruct` | `Qwen2_5_VLForConditionalGeneration` | Qwen2.5-VL | dynamic, capped by `--image-tokens` |
| `qwen25vl-7b` | `Qwen/Qwen2.5-VL-7B-Instruct` | `Qwen2_5_VLForConditionalGeneration` | Qwen2.5-VL | dynamic, capped by `--image-tokens` |
| `llava15-7b` | `llava-hf/llava-1.5-7b-hf` | `LlavaForConditionalGeneration` | LLaVA-1.5 | fixed: 576 tokens per image, 336×336 CLIP |

Two asymmetries are structural and are recorded in every output JSON so that no later reader has to
rediscover them:

- **LLaVA's image side cannot be capped.** `llava-1.5-7b-hf` ships a `CLIPImageProcessor` with a
  fixed 336×336 crop, so `--image-tokens` is inert for that model and the realised count is exactly
  576 per image. Qwen sizes by a *pixel budget* and the realised count always lands **under** the
  cap, because it preserves the aspect ratio and rounds both edges to a multiple of
  `patch_size × merge_size`. Measured on the first four `marine_captions` images (very different
  aspect ratios): cap 32 → 22 tokens per image, cap 144 → 111, cap 196 → 164. The field
  `meta.image_tokens_realised` carries the truth for the first batch, and
  `meta.image_token_budget_applied_via` records which attribute spelling the cap went through.
- **LLaVA's batch must stay smaller.** See §4.

### The image-token cap is a trap, and it has already been stepped on once

`--image-tokens` is applied by writing a **total pixel budget** of `image_tokens × patch_size²` to
the Qwen image processor. The spelling of that attribute changed under us and getting it wrong is
**silent**. This is the single most important operational warning in this document: a run can look
perfectly healthy, write a complete JSON, and have trained at a completely different image
resolution than its own metadata claims.

| transformers | correct spelling | meaning |
|---|---|---|
| 4.x | `image_processor.max_pixels` / `.min_pixels` | total pixel budget (the keys `preprocessor_config.json` ships) |
| 5.x | `image_processor.size.longest_edge` / `.shortest_edge` | same budget, collapsed into the `size` SizeDict |

Assigning v4-style pixel values to `size` *as if the edges were lengths* raises no error and does
not bind; neither does replacing `ip.size` with a plain dict, which fails outright at resize time.
Both spellings are set by `set_pixel_budget()` in the script, which reports which one took, and a
run whose realised count exceeds `0.6 × batch × cap` **aborts with an explicit message** rather than
training at the wrong resolution.

This matters because the archived local control (`tools/_p1595_qwen_objective_control.py`) is a
victim of exactly this: its `proc.image_processor.size = {"longest_edge": 12*28, ...}` assignment
was discarded by the processor call, so the run proceeded on the processor **defaults** — no cap at
all — at roughly 1200–2500 image tokens per image. Its own JSON declares `max_image_tokens: 12` and
its prose says "about 64 image tokens"; neither is what the model saw. That also corrects the
direction of the comparison with this script: `--protocol reduced` (cap 144, realising ~111–135
tokens per image) is **coarser**, not finer, than the archived control. Anything claiming to be
comparable with the archived pair must compare **protocol fields**, and must not trust the archive's
image-budget metadata.

To reproduce the archived construction exactly you would have to leave the pixel budget untouched,
which **this script never does** — it always applies `--image-tokens`. So there is no CLI flag that
reproduces the archive; a reproduction would be the archived script itself (or a copy of it) run in
bf16. Use this script's frozen value as a fingerprint instead:

The archived frozen baseline is `frozen_dg_star = 1.0703125`, `frozen_cg = 0.86328125` over its 160
pairs. Those two numbers identify the archived construction: if a run reports them, it reproduced the
archive; if it reports something else, it did not, whatever its metadata says. A correctly capped
`--protocol reduced` run will **not** report them.

Both objectives share one frozen forward pass per `(model, seed)`. That is not a convention here,
it is asserted: see §5.

### Implementation facts verified locally, so nobody re-derives them on the instance

- **The hidden state is read through the backbone, never through `lm_head`.** For LLaVA the registry
  path is `LlavaForConditionalGeneration.model` (a `LlavaModel` owning `language_model` and
  `vision_tower`); for the Qwen family it is `Qwen2VLForConditionalGeneration.model`. Checked by
  hooking `lm_head` and comparing: the backbone tensor is **bitwise identical** to the tensor
  `lm_head` receives (`max abs diff 0.0`), while the full `forward` materialises a
  `(2, 58, 151936)` logits tensor that the measurement path never allocates. The JSON records
  `meta.backbone_path` and `meta.lm_head_called: false`.
- **Gradient checkpointing is really on** (`is_gradient_checkpointing` true on the backbone), and
  gradients reach both towers through the backbone path. Adapters at the *input* layer of each tower
  (language layer 0, visual block 0) receive an exactly zero `lora_A` gradient because their input
  tensor is the frozen embedding, which has no upstream gradient. That is expected, matches the
  archived runs' construction, and is identical with and without checkpointing — it is not a
  checkpointing artefact and not a reason to distrust a run.
- **The tower split is structural, not string-guessing.** Targets are fully qualified module names
  filtered by tower (`vision_tower`/`visual` → vision, `multi_modal_projector` → projector,
  `language_model`/`model.layers` → language) and any adapter that cannot be assigned aborts the run.
  Verified adapter counts at `--arm both`: `qwen2vl-2b` 256 vision / 392 language / 0 projector;
  `llava15-7b` 288 vision / 448 language / 4 projector.
- **CLI defaults resolve from the protocol.** Piping `--protocol reduced --model qwen2vl-2b` through
  `--epochs`, `--num-samples` or `--image-tokens` without a value resolves to the archived local
  protocol (160 pairs, 1 epoch, cap 144, batch 4), which is what makes the cloud run comparable with
  the archived pair.

---

## 2. Setup on the instance

Model weights are downloaded **on the server** (standing rule in `AGENTS.md`); never local-then-upload.

```bash
# 1. probe the sources first, then pick one (do not trust the previous machine's numbers)
curl -m 12 -o /dev/null -w '%{speed_download}\n' https://hf-mirror.com/api/models/Qwen/Qwen2.5-VL-7B-Instruct

# 2. mirror first, cache on the data disk
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/hf
python -c "from huggingface_hub import snapshot_download as d; print(d('Qwen/Qwen2-VL-2B-Instruct'))"
python -c "from huggingface_hub import snapshot_download as d; print(d('Qwen/Qwen2.5-VL-3B-Instruct'))"
python -c "from huggingface_hub import snapshot_download as d; print(d('Qwen/Qwen2.5-VL-7B-Instruct'))"
python -c "from huggingface_hub import snapshot_download as d; print(d('llava-hf/llava-1.5-7b-hf'))"

# 3. fallback if the mirror is slow: ModelScope, verifying the repo name through the API first
python -c "from modelscope.hub.api import HubApi; print(HubApi().get_model_files('Qwen/Qwen2.5-VL-7B-Instruct'))"
# and for a single slow connection, the multi-connection fetcher already used in this project:
#   python tools/_p1083_parallel_fetch.py ...

# 4. dependencies (torch is already on these images; do not touch download.pytorch.org)
export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
export PIP_CACHE_DIR=/root/autodl-tmp/pipcache
pip install -U "transformers>=4.49" peft bitsandbytes accelerate -i $PIP_INDEX_URL

# 5. run environment
export PYTORCH_ALLOC_CONF=expandable_segments:True
export PYTHONIOENCODING=utf-8
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1
```

The script searches these snapshot directories before falling back to the HF repo id:
`models/ms_cache/models/Qwen--<name>/snapshots/master` (ModelScope layout), then the plain HF cache
path for `llava-hf/llava-1.5-7b-hf`. Run `--dry-run` first on every instance: it prints which
weights were found and whether they are local.

Always check that the `transformers` on the instance exposes all four classes, or the run dies at
load time rather than at the first step:

```bash
python -c 'import transformers as t; print(t.__version__, [hasattr(t,c) for c in ("Qwen2VLForConditionalGeneration","Qwen2_5_VLForConditionalGeneration","LlavaForConditionalGeneration")])'
```

---

## 3. The commands

Every run writes exactly one JSON,
`outputs/analysis/decoder_attribution_<model>_<objective>_seed<seed>.json`, and never touches the
archived 2B control files (`qwen_objective_control_*`) or anything else already under
`outputs/analysis/`.

Common prefix (bash), so the phase blocks below stay readable:

```bash
cd /root/autodl-tmp/New            # the repository root on the instance
S=tools/_p1612_objective_control_multimodel.py
export PYTORCH_ALLOC_CONF=expandable_segments:True PYTHONIOENCODING=utf-8
```

Pre-flight, once per instance and before anything else:

```bash
python $S --dry-run --model qwen2vl-2b   --objective contrastive
python $S --dry-run --model qwen25vl-3b  --objective generative
python $S --dry-run --model qwen25vl-7b  --objective generative
python $S --dry-run --model llava15-7b   --objective contrastive
```

### Phase 1 — decisive: does LLaVA-1.5-7B widen under a contrastive loss?

The whole question in Section H is whether the sign of the 7B LLaVA result is objective-driven. Two
runs answer it, because the two objectives share a frozen baseline and differ only in the loss.

```bash
# Phase 1a (must run; these two are the experiment)
python $S --model llava15-7b --objective contrastive --protocol match --seed 42 --apply
python $S --model llava15-7b --objective generative  --protocol match --seed 42 --apply

# Phase 1b (run if time allows; these turn one seed into a spread)
for s in 7 123; do
  for o in contrastive generative; do
    python $S --model llava15-7b --objective $o --protocol match --seed $s --apply
  done
done
```

Order matters only in that the second run of each seed performs the A/B check against the first.
Run the two objectives of a seed back to back; run different seeds in any order.

### Phase 2 — the scale and family ladder, generative first

Phase 2 puts every checkpoint under the objective that the LLaVA result used, so that a monotone or
non-monotone trend in the objective effect becomes visible, and then adds the contrastive arm at the
same seed.

```bash
# Phase 2a: same objective (generative), three scales and two families, seed 42
python $S --model qwen2vl-2b  --objective generative --protocol match --seed 42 --apply
python $S --model qwen25vl-3b --objective generative --protocol match --seed 42 --apply
python $S --model qwen25vl-7b --objective generative --protocol match --seed 42 --apply

# Phase 2b: the contrastive arm of the two smaller Qwen checkpoints (the 2B one is the
#          scale-matched partner of the archived local control; the 3B one is the new point)
python $S --model qwen2vl-2b  --objective contrastive --protocol match --seed 42 --apply
python $S --model qwen25vl-3b --objective contrastive --protocol match --seed 42 --apply

# Phase 2c (optional but cheap and decisive for the family axis at 7B):
python $S --model qwen25vl-7b --objective contrastive --protocol match --seed 42 --apply
```

Phase 2c is the run that separates *family* from *scale* at 7B: `llava15-7b` contrastive against
`qwen25vl-7b` contrastive is a family comparison at equal scale and equal objective.

### Phase 3 — extra seeds

Only after the seed-42 ladder is complete and its A/B checks have passed. Spread the seeds so that
no model has only one seed.

```bash
for s in 7 123; do
  python $S --model qwen2vl-2b  --objective contrastive --protocol match --seed $s --apply
  python $S --model qwen2vl-2b  --objective generative  --protocol match --seed $s --apply
  python $S --model qwen25vl-3b --objective contrastive --protocol match --seed $s --apply
  python $S --model qwen25vl-3b --objective generative  --protocol match --seed $s --apply
done
# and, if the 7B axis is the one that matters after Phase 1/2:
for s in 7 123; do
  python $S --model qwen25vl-7b --objective generative --protocol match --seed $s --apply
done
```

### Optional cross-check: reproduce the archived local control in the cloud

`--protocol reduced` matches the archived local control **in protocol fields** (160 pairs, 1 epoch,
batch 4, `both` arm, same data, same seed), so it is the cheapest way to prove an instance is
configured correctly before spending hours. But it cannot reproduce the archived *numbers*, for two
independent reasons:

1. **Image budget.** The archived run's declared cap never bound (see §1): it ran on the processor
   defaults — no cap at all — at roughly 1200–2500 image tokens per image, whereas a correctly
   applied 144-token cap realises ~111–135 per image on this data. The frozen baselines therefore
   cannot agree, and no loader on the ladder can make them agree. The archived `1.0703` is a property
   of the *archived construction*, not of the protocol name.
2. **Precision.** The archived control ran **bfloat16**; the ladder defaults to **4-bit nf4** by
   design, so that the 7B models fit at all.

So use `--protocol reduced` to check that the pipeline runs, that the objective changes the
magnitude, and that the sign matches — **not** to reproduce `-73.5 %` / `-14.2 %` digit for digit.
Reproducing the archived numbers is a different experiment (it needs the unset budget *and* bf16),
belongs in its own script, and cannot be requested from this CLI:

```bash
# instance validation only: correct cap, 4-bit, same protocol fields as the archive
python $S --model qwen2vl-2b --objective contrastive --protocol reduced --seed 42 --apply
python $S --model qwen2vl-2b --objective generative  --protocol reduced --seed 42 --apply

# same pair in bf16, if the precision axis itself is what is being checked
python $S --model qwen2vl-2b --objective contrastive --protocol reduced --seed 42 --bf16 --apply
python $S --model qwen2vl-2b --objective generative  --protocol reduced --seed 42 --bf16 --apply
```

Do **not** mix precisions *within* the ladder: `meta.precision` must be identical across the runs
that are compared to each other (acceptance criterion 6). Pick one of the two forms above and stay
with it for the whole cross-check pair.

Neither form overwrites `outputs/analysis/qwen_objective_control_*_seed42.json`; both write a new
file under the `decoder_attribution_*` name. The archived pair stays intact by design.

Smoke mode, if anything about an instance is in doubt:

```bash
python $S --smoke --model qwen2vl-2b --objective contrastive --apply   # 2 pairs, 1 epoch, 32 tokens
```

`--smoke` writes a JSON whose `meta.mode` is `"smoke"`; it is never a reportable result, and the
A/B check refuses to compare a smoke run against an apply run of the same model and seed.

---

## 4. Runtime and memory per run

### Memory (4-bit nf4 is the default; measured locally where marked)

| Model | 4-bit weights | Smallest card that fits | `--bf16` instead |
|---|---|---|---|
| `qwen2vl-2b` | ≈ 2.0 GB *(estimated from load time; the full smoke run fits an 8 GB card with room to spare)* | 8 GB | ≈ 5 GB (2B bf16) |
| `qwen25vl-3b` | ≈ 2.5 GB *(estimated)* | 8 GB *(not yet run locally)* | ≈ 7 GB |
| `qwen25vl-7b` | ≈ 5.0 GB *(estimated)* | 12 GB | ≈ 16 GB |
| `llava15-7b` | 4.07 GB **(measured)**; **5.33 GB peak during a real training step (measured)** | 8 GB **(measured: the full 2-pair smoke trained, measured and wrote its JSON on an 8 GB RTX 4060 Laptop)** | ≈ 15 GB |

Practical guidance:

- **16 GB comfortably covers every Phase 1/2 run in 4-bit; 24 GB is enough for anything here.**
  `--bf16` at 7B needs ≈ 16 GB for the weights alone and is not recommended for the ladder, because
  the ladder's value is that all its runs share one precision.
- **Never launch two runs on one card at once.** Each run loads its own copy of the model, and two
  7B copies in 4-bit plus activations will not fit in 24 GB. Serialise the commands; the loop forms
  above are already serial.
- Gradient checkpointing is on for every run, which is what makes the 7B models trainable at this
  batch size; it trades step time for activation memory.
- The measurement pass costs a full extra forward over the evaluation set, once before training and
  once per epoch. At `--protocol match` that is 4 evaluation sweeps of 160 batches each on top of
  the 480 training steps — a non-trivial share of the run, not a rounding error.

### Runtime

Measured anchors, all on the local 8 GB RTX 4060 Laptop card, 4-bit nf4, gradient checkpointing on.
They are the basis for the projections below and should be replaced by cloud numbers as soon as the
first cloud run lands:

| Anchor | Measured |
|---|---|
| `qwen2vl-2b`, `--smoke` (2 pairs, 1 epoch, cap 32) | ~13–15 s end to end, model load included |
| `llava15-7b`, `--smoke` (2 pairs, 1 epoch) | **~25 s** end to end, of which 22 s is 4-bit weight loading |
| `llava15-7b`, build (4-bit load + LoRA wrap) | **22.0 s** |
| `llava15-7b`, training step, contrastive, batch 2, 1152 image tokens | **3.62 s/step**, peak **5.33 GB** |
| `llava15-7b`, evaluation forward, no grad, batch 2 | **1.05 s/step**, peak 5.03 GB |
| `qwen2vl-2b`, `--protocol reduced` | not re-measured since the image-budget fix; the earlier 13 s figure was taken while the cap was still inert, so it is a lower bound rather than an anchor |

Local `--smoke` results (2 pairs, 1 epoch, 32-token cap, batch as the protocol resolves it), with the
final code. These are **pipeline checks, not scientific results** — two pairs cannot measure anything
about the gap — but they establish that both objectives run on both model classes and that the A/B
machinery works:

| Run | Realised image tokens | Frozen `DG*` | After 1 epoch | `delta_DG%` | A/B verdict |
|---|---|---|---|---|---|
| `qwen2vl-2b` contrastive | 10 | 0.796875 | 0.757812 | −4.90 | identical (against the generative sibling) |
| `qwen2vl-2b` generative | 10 | 0.796875 | 0.804688 | +0.98 | identical |
| `llava15-7b` contrastive | 1152 (576 × 2) | 0.554199 | 0.541992 | −2.20 | identical (against the generative sibling) |
| `llava15-7b` generative | 1152 (576 × 2) | 0.554199 | 0.551758 | −0.44 | identical |

The two LLaVA rows are the important ones for Phase 1's feasibility: **a LLaVA-1.5-7B 4-bit run
really does fit an 8 GB card**, both objectives included, and the two objectives reproduce the
identical frozen baseline in two independent processes. Read nothing else into the four deltas — at
two pairs they are noise, and repeated identical-seed runs of the same row move inside a small band
(see §5, criterion 1). Note also that the sign of the generative 2B row flips between repeated smoke
runs: at two pairs it carries no information at all.

Projected wall clock for one `--protocol match` run (320 pairs, 3 epochs = 480 training steps plus 4
evaluation sweeps of 160 batches):

| Model | Projected per run | Basis |
|---|---|---|
| `qwen2vl-2b` | 8–15 min | measured reduced run scaled by 4× steps and a longer sequence |
| `qwen25vl-3b` | 15–25 min | 2.5× the 2B step cost at the same step count |
| `qwen25vl-7b` | 25–45 min | 7B at batch 4 with ~187 image tokens; the LLaVA measurement below scaled to that token count |
| `llava15-7b` | **41 min measured-projection** on this laptop card: 480 × 3.62 s + 4 × 160 × 1.05 s + 25 s | direct from the anchors above, i.e. the least uncertain of these rows |

A cloud A100/L40S-class card should be at least as fast as a 4060 Laptop for this workload; treat the
table as a conservative upper bound and **replace it with the first real cloud timing** rather than
carrying a projection forward.

Whole-ladder totals, serialised on one card: **Phase 1a ≈ 1.5–2.5 h**, Phase 1 complete (6 runs)
≈ 4–8 h, Phase 2a+2b (5 runs) ≈ 1–2 h, the optional 2c ≈ 0.5–1 h, Phase 3 (8 runs) ≈ 2–5 h.
Phases 1 and 2 together fit one 24-hour rental with a wide margin, even if the card is half the speed
of this laptop's.

---

## 5. Acceptance criteria

A run is acceptable only when all of the following hold. The first four are asserted by the script
itself and abort the run rather than write a JSON; the rest are checked by reading the JSON.

1. **Frozen `DG*` identical across the two objectives of the same `(model, seed)`.** The loss does
   not exist until after the frozen pass, so both objectives must measure the identical untrained
   baseline. The script compares `meta.frozen_signature` and `frozen_dg_star` against the sibling
   file and **raises instead of writing** on any mismatch, with tolerance 0 (bit-identical). The
   field `meta.ab_check.verdict` must read `identical frozen DG* across both objectives`; a
   `sibling objective not run yet` verdict means the A/B is not yet established and the pair must
   not be reported. Verified locally for both model classes at `--smoke`, seed 42: `qwen2vl-2b`
   measured `frozen_dg_star = 0.796875` in two independent processes and `llava15-7b` measured
   `0.554199` in two independent processes, and in both cases the second run accepted the first as
   its sibling with `abs_diff = 0.0`. The guard was also verified negatively: re-running one
   objective under a changed image budget made the script **refuse to write** and name the differing
   field, which is the behaviour to expect when a pair is genuinely unmatched.
   **The tolerance is 0 because the frozen pass is genuinely bit-deterministic; do not relax it to
   make a mismatching pair "pass".** A mismatch means the two runs did not share a protocol, and
   the pair is worthless.
   Contrast this with the *trained* number, which is deliberately not asserted: repeated
   identical-seed 4-bit smoke runs produced different LoRA weight hashes and moved the post-training
   `DG*` within a small band (measured spread ≈ 1 % of the frozen value at smoke scale). That is
   bitsandbytes/CUDA nondeterminism in the 4-bit backward pass. Report directions and multi-seed
   spreads, never a last-digit comparison between two runs.
2. **The two objectives differ only in the loss.** Same `meta.protocol`, `num_samples`, `epochs`,
   `max_image_tokens`, `batch`, `seed`, `precision`, `arm`, `lora`. The script asserts this too.
3. **Adapter counts are positive and correctly split.** `n_trainable > 0`, `n_language_adapters > 0`,
   and for `--arm both` also `n_vision_adapters > 0`. A `text_only` run that touches vision adapters,
   or a `vision_only` run that touches language adapters, aborts with a `tower leak` error.
4. **Numbers are finite.** `delta_DG_percent` finite, `frozen_dg_star` a positive finite number,
   `len(dg_star) == len(loss) == epochs`, and no non-finite value anywhere in the history.
5. **Required fields present** in every JSON: `meta.script`, `meta.model_repo`, `meta.revision`,
   `meta.protocol`, `meta.num_samples`, `meta.epochs`, `meta.max_image_tokens`, `meta.batch`,
   `meta.lr`, `meta.seed`, `meta.precision`, `meta.lora`, `meta.n_trainable`,
   `meta.n_vision_adapters`, `meta.n_language_adapters`, `meta.elapsed_sec`, `meta.versions.torch`,
   `meta.versions.cuda`, `meta.versions.transformers`, `meta.hostname`, `meta.measurement`,
   `meta.ab_check`, `meta.image_tokens_realised`, `meta.image_token_budget_applied_via`, plus
   `frozen_dg_star`, `dg_star`, `loss`, `delta_DG_percent`.
   `meta.mode` must be `"apply"`, not `"smoke"`.
6. **`meta.precision` is the same for every run of the ladder** (`4-bit nf4` unless deliberately
   changed everywhere), and `meta.image_tokens_realised` is plausible for the model: **under** the
   cap for the Qwen family (a few tens at cap 32, roughly 100–140 at cap 144, roughly 150–200 at cap
   196, depending on image aspect ratios), and exactly `576 × batch` for LLaVA. A value that
   *exceeds* `0.6 × batch × cap` means the cap silently failed and the run must not be used; the
   script aborts on that case before writing.
7. **The archived control files are untouched**: `outputs/analysis/qwen_objective_control_*.json`
   must still exist with their original sizes.

One-line audit over a completed batch:

```bash
python - <<'PY'
import json, glob, math
for p in sorted(glob.glob("outputs/analysis/decoder_attribution_*.json")):
    r = json.load(open(p))
    m = r["meta"]
    assert m["mode"] == "apply", (p, "smoke run in the ladder")
    assert math.isfinite(r["delta_DG_percent"]), p
    assert m["n_language_adapters"] > 0 and m["n_trainable"] > 0, p
    assert len(r["dg_star"]) == len(r["loss"]) == m["epochs"], p
    print("%-46s %-11s %-6s DG* %8.4f -> %8.4f  %+7.2f%%  %6.1fs  %s"
          % (p.split("/")[-1], m["model"], m["objective"], r["frozen_dg_star"], r["dg_star"][-1],
             r["delta_DG_percent"], m["elapsed_sec"], m["ab_check"].get("verdict", "")[:34]))
PY
```

Then pair the objectives of each model and seed and assert the frozen equality across the batch:

```bash
python - <<'PY'
import json, glob, collections
g = collections.defaultdict(dict)
for p in glob.glob("outputs/analysis/decoder_attribution_*.json"):
    r = json.load(open(p)); m = r["meta"]
    g[(m["model"], m["seed"])][m["objective"]] = r
for k, d in sorted(g.items()):
    if len(d) == 2:
        a, b = d["contrastive"]["frozen_dg_star"], d["generative"]["frozen_dg_star"]
        assert a == b, (k, a, b)
        print(k, "frozen identical", a, "| contrastive %+.2f%%  generative %+.2f%%"
              % (d["contrastive"]["delta_DG_percent"], d["generative"]["delta_DG_percent"]))
    else:
        print(k, "INCOMPLETE — only", list(d))
PY
```

---

## 6. What each outcome means for Paper A Section H

`delta_DG_percent` is one signed number; negative means the gap narrowed. This is the same sign
convention `docs/paperA_decoder_confound_paragraph.md` uses, and the opposite of the `+` glyph that
Tables E and G print for the same two directions — keep the JSON's sign convention in the prose.

**Phase 1, the decisive comparison** (LLaVA-1.5-7B, both objectives, same frozen pass):

| Outcome at 7B | Reading | What Section H becomes |
|---|---|---|
| contrastive **narrows** and generative **widens** (opposite signs) | The objective decides the sign at 7B, and the local 2B control's "objective changes magnitude, not sign" does not generalise upward | The confound is resolved in favour of the objective: the widening in Table `tab:llava` is a property of the caption-generation loss at that scale, and the ladder's other arms become a scale trend for that loss. Section H.1 must be rewritten from "the objective changes the magnitude by about a factor of five without changing the sign" to a scale-qualified statement |
| **both narrow**, contrastive by more | The sign is not objective-driven at 7B either; the local 2B result replicates upward and the archived widening must come from something the ladder still shares (data, budget, or the archived run's own site specification) | Section H.1's conclusion is strengthened from one model to two, and the widening in Table `tab:llava` is explicitly attributed to a factor this control fixes — which sharpens, rather than removes, the section's original caveat |
| **both widen** | The objective does not carry the sign at all; something common to both ladder objectives — most plausibly the image-token budget or the data — does | The objective is excluded as the explanation and Section H must say so plainly; the next control is data and image budget at fixed model and loss, not another objective |
| contrastive **widens** and generative narrows | The archived 2B contrastive result does not survive the change of scale | Report as a scale-dependent sign flip; this is the outcome that most damages the current framing and it must not be smoothed over |

**Phase 2 (scale and family), read as a trend, not as single numbers:**

- Generative `delta_DG_percent` as a function of scale within the Qwen2.5-VL family
  (3B → 7B), against the 2B Qwen2-VL point, says whether the generative loss becomes
  gap-widening with scale. A monotone trend would give Section H a scale axis for the first time.
- `qwen25vl-7b` contrastive against `llava15-7b` contrastive separates family from scale at equal
  parameter count and equal objective: if LLaVA contrastive narrows while Qwen contrastive at the
  same size widens (or the reverse), the family, not the objective or the scale, is implicated.
- If every model of the ladder narrows under both objectives, then the archived LLaVA widening is
  not reproducible under this protocol at all, which is itself a finding for Section H and points at
  the one thing the ladder cannot vary: the archived run's own data and site specification.

**What the ladder still will not settle, and which Section H must keep saying:**

- The image-token budget differs by necessity between families (576 for LLaVA, ≈187 for Qwen at a
  196 cap); a sign difference across families can never be fully separated from that difference.
- The dataset and pair count are held fixed *within* the ladder, so a dataset effect cannot be
  measured here — only excluded as an explanation for a ladder-internal difference.
- Fewer than three seeds per cell quantifies nothing about dispersion; treat single-seed cells as
  direction only. `natural`-language caveats about learning rate (the same rate is used for both
  objectives) stay true.

---

## 7. Hand-off checklist after the cloud session

Per the standing cloud rules in `AGENTS.md`, in this order:

1. Confirm every run exited and no traceback or `ARM_FAILURES` line exists in the logs.
2. Run the §5 audit and the §5 pairing check; both must pass. Record the printed table.
3. Pull **all** `outputs/analysis/decoder_attribution_*.json` to the local machine and verify each
   file's size and parseability locally. Nothing that is needed may be left on the instance.
4. Append the results and the measured (now real) runtimes to `HANDOFF.md` and update
   `文件地图.md`, with the script path, the exact commands and the JSON field paths for every
   number that will be quoted.
5. Only then power the instance off (`sync && (shutdown -h now || poweroff)`) and record the time.