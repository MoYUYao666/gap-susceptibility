# A23 multi-encoder threshold transfer — cloud notes (phase 4)

Status: **the full grid has been executed locally; this document is otherwise unchanged except for the loader
table in §3 and the RemoteCLIP correction below it.** This document
is the operator-facing note for `tools/_p1614_a23_multi_encoder_transfer.py`, `cloud_next/a23_encoders.sh` and
the cloud phase 4 in `cloud_next/expected_outputs.json`. Nothing here needs a GPU instance to prepare, and
nothing here starts one. §9 records what was actually executed on 2026-10-24 (five units, four of them
reproducing archived certificate values bit-exactly, and one cross-encoder transfer table); the full
seven-encoder / 21-unit grid was then run on this workstation on 2026-10-25 07:37–07:39
(`meta.finished_at = 2026-10-25T07:39:56+0800`) and rewrote `outputs/analysis/a23_multiencoder_transfer.json`
wholesale — see `docs/a23_21unit_switch_notes.md` for the switch record and the gate results.

---

## 1. What this run settles

The A23 revision (IEEE JOE `26-0663`) carries a negative claim about the margin-mass certificate
`M(eps) = P(margin <= 2 eps)`: it is informative *within* a domain at a domain-relative resolution, but **no
threshold on it transfers across domains or encoders** (best cross-domain balanced accuracy `0.50`–`0.55`
against chance `0.50`). That claim currently rests on three encoders: the generic-CLIP control
(`openai/clip-vit-base-patch32`) over the FathomNet-derived optical tree and the NKSID sonar tree, plus the two
adapted encoders BioCLIP and OceanCLIP over the 67-class marine subset
(`outputs/analysis/a23_fine_eps_certificate.json`, `docs/a23_fine_eps_text.md` §2.3).

Phase 4 widens the test instead of repeating it:

* **the same three corpora**, re-encoded with a registry of **seven frozen encoders** (five generic or
  frozen-feature backbones plus the two adapted ones already cited) → **21 encoder × corpus units**;
* **every ordered pair** of units (all `21 × 21 = 441`, self-pairs included and labelled) is asked the
  archived question: pick the threshold on `M` that is optimal on the source, score the target;
* the same table is produced for the **domain-relative resolution** `eps = c * median_i(margin_i)`, `c in
  {0.005, 0.01, 0.02}`, and for the sigma-relative variant kept from `_p1472`;
* every entry carries a **paired bootstrap over images** (2,000 draws): the source threshold is refitted on the
  resampled source family and the target balanced accuracy is recomputed on the resampled target family. Pairs
  that share a corpus reuse the same image indices (genuinely paired); cross-corpus pairs use independent draws
  and say so (`bootstrap.paired = false`).

What it does **not** do: no fine-tuning of any encoder, no new corpora, no multi-seed probe study, no change to
any existing archive, and no manuscript edit.

## 2. Exact commands

Local proof run (this workstation, `D:\Anaconda\envs\pytorch\python.exe`; the note in §9 records what was
actually executed):

```powershell
$env:PYTHONIOENCODING='utf-8'
# 1. plan first: prints the unit grid, the expected cache paths and the fetch command for anything missing
D:\Anaconda\envs\pytorch\python.exe tools/_p1614_a23_multi_encoder_transfer.py --dry-run
# 2. encode + analyse one encoder over the three corpora (the cheap pipeline proof)
D:\Anaconda\envs\pytorch\python.exe tools/_p1614_a23_multi_encoder_transfer.py --encode --analyze `
    --encoders clip-vit-base-patch32
# 3. re-run the dry-run: every number it prints is now asserted against the JSON it wrote
D:\Anaconda\envs\pytorch\python.exe tools/_p1614_a23_multi_encoder_transfer.py --dry-run
```

Cloud (instance checkout `BASE=/root/autodl-tmp/p3work`, data disk `/root/autodl-tmp`):

```bash
# the whole phase, resumable, with per-step logs in cloud_next/logs/
bash cloud_next/run_all.sh phase4          # -> bash cloud_next/a23_encoders.sh

# or the same thing step by step
export HF_ENDPOINT=https://hf-mirror.com HF_HOME=/root/autodl-tmp/hf
export MODELSCOPE_CACHE=/root/autodl-tmp/ms_cache PYTHONIOENCODING=utf-8
cd /root/autodl-tmp/p3work
python tools/_p1614_a23_multi_encoder_transfer.py --dry-run \
    --data-root data --models-root models --cache-root outputs/analysis/_cache/a23_multiencoder
python tools/_p1614_a23_multi_encoder_transfer.py --encode --analyze \
    --data-root data --models-root models --cache-root outputs/analysis/_cache/a23_multiencoder \
    --include-adapted --boot 2000
python cloud_next/verify_cloud_artifacts.py --phase phase4 --apply
```

Useful flags: `--units <enc>__<corpus>,…` (targeted subset), `--encoders`, `--corpora`, `--include-adapted`
(adds BioCLIP/OceanCLIP), `--allow-missing-models` (skip an encoder whose weights are absent, recorded in
`meta.units_skipped`), `--force` (re-encode), `--boot N`, `--probe-seed S`, `--device cpu|cuda|auto`,
`--data-root/--cache-root/--models-root/--subset-json` for any layout. Wrapper variables:
`BASE`, `DISK`, `PY`, `BOOT`, `ADAPTED=0|1`, `FETCH=0|1`, `UNITS`.

The script **never downloads**: every model is loaded with `local_files_only=True`, either from
`<models-root>/<dir>` (this workstation) or from the local Hugging Face cache that `HF_HOME` points at (the
cloud). A missing model is a hard error that prints the repository id and the fetch command; `--dry-run` does
the same before any encoding starts.

## 3. Models: repository ids, sizes, fetch policy

| Registry id | Repository id | Required file(s) | Size on disk | Loader |
|---|---|---|---|---|
| `clip-vit-base-patch32` | `openai/clip-vit-base-patch32` | `config.json`, `preprocessor_config.json`, `pytorch_model.bin` | 580.7 MB | transformers `CLIPModel`: `vision_model` + `visual_projection`, `text_model` + `text_projection` |
| `siglip-base-patch16-224` | `google/siglip-base-patch16-224` | `config.json`, `preprocessor_config.json`, `model.safetensors` | 778.1 MB | transformers `AutoModel` (`SiglipModel`): `visual_projection` does not exist on this class in transformers 5.16.1, so the image embedding is `vision_model.head(last_hidden_state)` and the text embedding `text_model.head(text_model.pooler_output)` (`text_path = text_model_head`) |
| `clip-vit-large-patch14` | `openai/clip-vit-large-patch14` | `config.json`, `preprocessor_config.json`, tokenizer files, `model.safetensors` | 1,634.9 MB | transformers `CLIPModel`: `vision_model` + `visual_projection`, `text_model` + `text_projection` |
| `dinov2-base` | `facebook/dinov2-base` | `config.json`, `preprocessor_config.json`, `model.safetensors` | 330.3 MB | transformers `AutoModel` (`Dinov2Model`, vision tower only, image path `model` — the class has no text tower) + the no-bias cosine probe for top-1, scored on the held-out 30 % split only |
| `remoteclip` | `chendelong/RemoteCLIP` | `RemoteCLIP-ViT-B-32.pt` | 577.2 MB | open_clip `create_model_and_transforms('ViT-B-32', pretrained=None)` + `load_state_dict(…, strict=False)`: 302 keys, 0 missing / 0 unexpected |
| `bioclip` (adapted) | `imageomics/bioclip` | `open_clip_pytorch_model.bin` (+ `open_clip_config.json`) | ≈ 600 MB | open_clip `ViT-B-16` + `load_state_dict` |
| `oceanclip` (adapted) | `zjunlp/OceanCLIP-0.15B` | `oceanclip-bio/epoch_50.pt` (+ BioCLIP base weights) | ≈ 2,300 MB | BioCLIP-init `ViT-B-16`, then `epoch_50.pt` |

The two rows that used to read "`SiglipModel` towers + projections" and "`Dinov2Model` (CLS token) + linear
probe" were the **pre-fix** extraction paths: SigLIP has no `visual_projection`/`text_projection` on the
`transformers` class in 5.16.1 (the head is used instead, and the fallback that was actually taken is recorded
in the archive as `model_source.extraction`), and the DINOv2 arm reads the tower output through the probe
protocol rather than a CLS token. The authoritative record is now
`registry.encoders.<id>.loader` / `registry.encoders.<id>.image_path` / `registry.encoders.<id>.text_path` and
`encoders.<id>.corpora.<corpus>.model_source.extraction` inside `outputs/analysis/a23_multiencoder_transfer.json`.

**RemoteCLIP correction (2026-10-25).** An earlier note in this document and in the cloud wrapper's fallback
logic treated RemoteCLIP as unfetchable ("hf-mirror 403"). That 403 came from an API probe against the wrong
URL, not from the checkpoint: `RemoteCLIP-ViT-B-32.pt` was fetched successfully on 2026-10-25 into
`models/RemoteCLIP/RemoteCLIP-ViT-B-32.pt` (605,208,421 bytes) and its sha256 is
`60014e395d930a3f2963d1d89c8522bf4ad56775571e4356e866864789af85c4`, which is bit-identical to the
`chendelong/RemoteCLIP` LFS object listed by the mirror API
(`https://hf-mirror.com/api/models/chendelong/RemoteCLIP/tree/main?recursive=true`, queried 2026-10-25). It
loads with 302 keys and 0 missing / 0 unexpected parameters, and it is a genuine remote-sensing fine-tune of
OpenAI CLIP ViT-B/32 (every tensor within cos 0.995–1.000 of `models/clip-vit-base-patch32/pytorch_model.bin`,
`logit_scale = 4.6037`). Its zero-shot top-1 on the three corpora of this study is nevertheless at chance:
12.83 % / 11.27 % / 2.43 % against 14.29 % / 14.29 % / 1.49 %
(`encoders.remoteclip.corpora.<corpus>.frozen_row.top1` and `chance_percent`), i.e. within a factor of two of
chance, so the 21-unit claim carries it as a fifth limit rather than as a reference pipeline. The chance-level
result is a property of that checkpoint on non-remote-sensing corpora, not an unloaded model.

Sizes are the on-disk footprint measured in this workspace (`models/<dir>`, recursive, 2026-10-24); the two new
repositories are quoted from the Hugging Face file listing (`RemoteCLIP-ViT-B-32.pt` is one of three
checkpoints in `chendelong/RemoteCLIP`, whose `usedStorage` is 2.7 GB, so the fetch uses
`allow_patterns=['RemoteCLIP-ViT-B-32.pt', '*.json', '*.md', '.gitattributes']`).

**Download policy (repository rule, highest priority).** Weights are fetched **on the server**, never uploaded
from the laptop. Mirror first (`HF_ENDPOINT=https://hf-mirror.com` with `snapshot_download`), ModelScope as the
fallback, with the throughput measured on the host before choosing (hosts differed by up to 60× on the same
day). `cloud_next/a23_encoders.sh` probes the mirror for 12 s, tries the mirror, falls back to ModelScope, and
verifies the ModelScope repository id with `HubApi().get_model_files()` if the fallback is actually needed —
the mirror ids `imageomics/bioclip`, `zjunlp/OceanCLIP-0.15B` and the file list of `chendelong/RemoteCLIP`
were checked through the Hugging Face API on 2026-10-24. `HF_HOME` and `MODELSCOPE_CACHE` are pinned to the
data disk (`/root/autodl-tmp/...`) because the root disk is small. Everything is resumable: a repository that
already resolves from the local cache is skipped, and the encode step reuses every valid cache file.

## 4. Expected runtime

Encoding is the bulk of the run; the analysis pass is cache-only and short. Two anchors, both sourced:

* **archived anchor** — `819 s` to encode the 1,608-image subset with OceanCLIP, checkpoint load included,
  i.e. **0.51 s/image**, the slowest encoder in the existing certificate; BioCLIP took `138 s` for the same
  subset and the two generic-CLIP control arms `25 s` (343 images) and `4 s` (1,783 images)
  (`docs/a23_fine_eps_text.md` §1, §6);
* **measured in this session** (`encoders.*.corpora.*.cache_creation.encode_seconds` in the local JSON; the
  encode loop only, model loading excluded): `clip-vit-base-patch32` 343 images in **8.01 s**, 1,783 images in
  **18.14 s**, 1,608 images in **415.11 s**; `bioclip` 1,608 images in **287.12 s**; `oceanclip` 1,608 images
  in **415.83 s**. The spread between the two `clip-vit-base-patch32` runs (0.010 vs 0.258 s/image on two
  different corpora) is GPU contention, not corpus size: this laptop's RTX 4060 was shared with two other
  training jobs for most of the run, so the measured numbers are upper bounds.

Per-corpus, per-encoder estimate for the 21-unit grid. Columns are image counts (marine optical 343, acoustic
sonar 1,783, rare-species subset 1,608); rates marked *measured* come from the table above, the two marked
*estimated* are scaled from the nearest measured class and flagged as such.

| Encoder (class) | s/image (basis) | marine | sonar | rare-species | per-encoder total |
|---|---|---|---|---|---|
| `clip-vit-base-patch32` (ViT-B/32) | 0.026 *(measured)* | 9 s | 46 s | 42 s | ≈ 1.6 min |
| `remoteclip` (ViT-B/32) | 0.026 *(same class)* | 9 s | 46 s | 42 s | ≈ 1.6 min |
| `siglip-base-patch16-224` (ViT-B/16) | 0.178 *(measured for BioCLIP)* | 61 s | 5.3 min | 4.8 min | ≈ 10.6 min |
| `bioclip` (ViT-B/16) | 0.178 *(measured)* | 61 s | 5.3 min | 4.8 min | ≈ 10.6 min |
| `dinov2-base` (ViT-B/14 + probe) | 0.089 *(estimated: half the ViT-B/16 rate)* | 31 s | 2.6 min | 2.4 min | ≈ 5.3 min |
| `clip-vit-large-patch14` (ViT-L/14) | 0.214 *(estimated: 1.2× the ViT-B/16 rate)* | 73 s | 6.4 min | 5.7 min | ≈ 12.8 min |
| `oceanclip` (ViT-B/16 + 1.7 GB load) | 0.259 *(measured)* | 89 s | 7.7 min | 6.9 min | ≈ 15.4 min |
| **all seven (21 units)** | — | ≈ 5.6 min | ≈ 28.6 min | ≈ 25.8 min | **≈ 60 min** |

Reading of the table:

* with `ADAPTED=0` (five generic encoders, 15 units) the encode pass is roughly **half** of the above
  (≈ 30 min contended on this laptop); with `ADAPTED=1` it is the full ≈ 60 min, and `oceanclip` alone is a
  quarter of it;
* the archived OceanCLIP anchor (0.51 s/image, load included) is a conservative ceiling for any single
  encoder, including the ViT-L/14 and ViT-B/16 ones; on a dedicated laptop GPU or a datacenter GPU divide the
  whole column by roughly 3–10× and 10–30× respectively — the archive's own uncontended numbers (4 s for
  1,783 images with ViT-B/32) show what a quiet laptop GPU does;
* the image loading is paid once per corpus, not once per unit (`--encode` is corpus-major, so only one
  corpus is held in memory at a time; the 1,608-image parquet subset is 4.1 GB on disk);
* the analysis pass is cheap: `--analyze` on 5 units with `--boot 2000` took **17 s** wall clock on this
  laptop, so the 21-unit / 441-pair cloud analysis is a few minutes and can be re-run on a CPU-only box
  without touching the caches;
* a re-run costs nothing: valid caches are reused (metadata + image fingerprint are checked), so an
  interrupted phase restarts at the first missing unit — the local run itself demonstrated this by reusing
  `clip-vit-base-patch32__marine_optical.npz` from an earlier smoke run.

## 5. Artifacts and schema

| Artifact | Path | Notes |
|---|---|---|
| Result JSON | `outputs/analysis/a23_multiencoder_transfer.json` | required keys `meta`, `encoders`, `correlations`, `transfer`, `conclusion`, `limits` (phase 4 gate) |
| Embedding cache | `outputs/analysis/_cache/a23_multiencoder/<encoder>__<corpus>.npz` | one file per unit; image features, class/text-side matrix, labels, used-image mask, self-describing metadata |

Field paths the manuscript text will cite (all inside the JSON):

* `encoders.<encoder>.corpora.<corpus>` — `frozen_row.top1`, `frozen_row.margin_median`,
  `frozen_row.mass_0p001 … mass_0p1`, `chance_percent`, `n_images_used`, `probe`, `probe_protocol`,
  `rows[]` (the nine surgery configurations), `reproduction` (exact comparison with the archived certificate).
* `correlations.pooled.with_top1.<key>.r` and `correlations.within_unit.<unit>.<key>.r` — pooled and
  within-domain correlation with top-1.
* `transfer.pairs[]` — `source`, `target`, `by_statistic.<key>.{source_threshold, target_BA, chance,
  n_source, n_target}` plus `.bootstrap.{target_BA_ci95, delta_vs_chance_ci95, p_delta_gt_zero, survives,
  paired}`.
* `transfer.summary` and `conclusion` — `n_entries_above_chance`, `n_entries_surviving_bootstrap`,
  `best_pair_point_estimate`, `headline`, `answer`, `effect_on_a23_text.action`.
* `limits` — probe seed, class imbalance, encoder count, family size, bootstrap scope, corpus provenance.

Provenance-manifest row to add to `docs/PROVENANCE_MANIFEST_2026-10-20.md` (the manifest is operator-owned):

```
| A23 multi-encoder threshold transfer (text §, "no threshold transfers" claim)
  script: tools/_p1614_a23_multi_encoder_transfer.py
  json: outputs/analysis/a23_multiencoder_transfer.json
  (fields: transfer.summary.n_entries_above_chance,
           conclusion.n_entries_surviving_bootstrap,
           conclusion.best_pair_point_estimate.{source,target,statistic,target_BA,delta_ci95},
           encoders.<encoder>.corpora.<corpus>.frozen_row.top1,
           encoders.<encoder>.corpora.<corpus>.reproduction.max_abs_diff)
  caches: outputs/analysis/_cache/a23_multiencoder/*.npz (regenerable)
  status: local pipeline proof done 2026-10-24 (5 units; 4 reproduce their archived certificates with
          max |diff| = 0.0; 260 scored cross-unit entries, 0 bootstrap survivors; see §9);
          the cloud values over all 21 units are pending |
```

## 6. Acceptance criteria

The run is only complete when all of the following hold. Each is checked mechanically.

1. **Every selected encoder × corpus is cached.** `cloud_next/a23_encoders.sh` asserts
   `len(transfer.units) == expected` and that `<encoder>__<corpus>.npz` exists for every unit, and
   `meta.complete_for_selection` is `true`. Expected: **21 caches** with `ADAPTED=1`, **15** with `ADAPTED=0`.
   The dry-run additionally asserts that every selected encoder's weights resolve on the host.
2. **Every unit has a full row set.** Nine family configurations per unit (`n_family_rows == 9`:
   `lambda in {-1, -0.5, -0.25, 0, 0.25, 0.5, 1, 2}` plus `text1.0`), each row carrying `top1`, the margin
   quantiles, `sigma_D` and all 13 statistic values.
3. **The transfer table is complete.** `transfer.n_pairs == n_units ** 2` (441 entries with 21 units), each
   with `source_threshold`, `target_BA`, `chance`, `n_source`, `n_target` and a bootstrap block for all 13
   statistics; `n_degenerate_entries` is reported rather than hidden.
4. **The conclusion is backed by a bootstrap, not by the point estimate.** `conclusion` states how many
   entries beat chance nominally and how many keep a 95 % interval above chance over images
   (`transfer.summary.n_entries_surviving_bootstrap`), and `conclusion.claim` is one of the two branches of §7.
   The in-script check requires the interval field on every pair × statistic and the survivor count in the
   conclusion.
5. **The gate passes before shutdown.** `python cloud_next/verify_cloud_artifacts.py --phase phase4 --apply`
   must print PASS (it checks the six required top-level keys), then the artifacts are retrieved and the same
   gate is re-run locally; only then is the instance stopped (repository shutdown order: verify → retrieve →
   stop). The retrieval list is `outputs/analysis/a23_multiencoder_transfer.json` plus
   `outputs/analysis/_cache/a23_multiencoder/*.npz`.

Two extra checks that the run should also satisfy, and which are recorded in the JSON rather than asserted:

* `encoders.<encoder>.corpora.<corpus>.reproduction.reproduced` is `true` for the three units that have an
  archived counterpart (`clip-vit-base-patch32` on `marine_optical` and `acoustic_sonar` against
  `a23_certificate_control.json`; `bioclip`/`oceanclip` on `rare_species` against
  `a23_certificate_adapted.json`) — the prompt templates and class enumeration follow the archived scripts, so
  a mismatch means the encoders are not the archived ones;
* `meta.corpus_size_checks.*.ok` is `true` (343 / 7, 1,783 / 7 with the 834 root-level `tire` files excluded,
  1,608 / 67).

## 7. The exact effect on the A23 text

The sentence at issue is the closing clause of the margin-certificate paragraph in
`paper_a2/ext_partII_domains.tex` (the revision text drafted in `docs/a23_fine_eps_text.md` §3.1/§3.2), whose
current scope is *"no threshold on `M` transfers across domains or encoders (best cross-domain balanced
accuracy 0.50–0.55 against chance 0.50)"*, supported by three encoders.

**Branch A — no pair survives (the expected outcome, and the one the widened claim needs).** Widen the
evidential base and quote the bootstrap instead of a range of point estimates:

```latex
no $\varepsilon$ and no calibration we tested transfers across domains or encoders: over all $N$ ordered pairs
among $E$ frozen encoders $\times$ $C$ corpora ($U$ encoder--corpus units, $P$ pairs, each scored by $13$
threshold statistics, $B$ image-bootstrap draws), $X$ entries reached a nominally above-chance balanced
accuracy and none kept its $95\,\%$ interval above chance ($\max$ point estimate $0.5Y$).
```

**Branch B — at least one pair survives.** The unconditional clause has to be weakened and the pair named:

```latex
one qualification is required: the threshold on $M$ fitted on <source encoder> over <source corpus>
($\hat\tau = t$) does transfer to <target encoder> over <target corpus>, with balanced accuracy $a$ against
chance $0.50$ ($95\,\%$ image-bootstrap interval $[l, u]$), so the claim is that the certificate is not
portable \emph{across general} domains and encoders rather than across all of them.
```

In both branches the numbers come from `transfer.summary` / `conclusion` (`E`, `C`, `U`, `P`, `X`, the maximum
point estimate, and for branch B the pair's `target_BA` and `delta_vs_chance_ci95`); the script writes
`conclusion.effect_on_a23_text.action` as the one-line instruction, and `conclusion.answer` is `"yes"` or
`"no"`. The paragraph's `Source:` line becomes:

```
Source: tools/_p1614_a23_multi_encoder_transfer.py; outputs/analysis/a23_multiencoder_transfer.json
```

Revision mechanics: the paragraph is absent from the submitted `26-0663` (`SUBMISSION/A23_JOE/current/`), so
this stays under *new analyses added during revision*, and the widened sentence must not be used anywhere
before the cloud JSON exists — a two- or three-encoder statement is not a seven-encoder statement.

## 8. Risks and limits (what would invalidate the run)

* **Probe units are a different kind of measurement.** `dinov2-base` has no text tower, so its top-1 comes
  from a no-bias cosine logistic probe on frozen features (stratified 70/30 split, `numpy.random.default_rng(0)`;
  full-batch Adam, 400 epochs, `torch.manual_seed(0)` on the CPU), and only the held-out 30 % enters the
  family. One seed, no cross-validation: a different split can move that unit's top-1 by a few points. The
  unit is flagged `probe: true` and the protocol is stored in `probe_protocol` and `probe_stats`.
* **The health label is the archived convention, and it is weak.** A configuration is labelled when its top-1
  is at or below its unit's median: nine configurations per unit, so the target balanced accuracy is coarse
  (granularity 1/4 to 1/5) and a source fit near 1.0 on nine points is not evidence of a usable operating
  point. This is inherited from `_p1352`/`_p1370` for comparability.
* **Cross-corpus intervals are unpaired.** The paired bootstrap is only available when source and target share
  a corpus; the other pairs use independent image draws (`bootstrap.paired = false`).
* **The bootstrap covers image sampling only.** Encoder choice, prompt template and the construction of the
  surgery family are not resampled.
* **The corpora are raw data trees, not the manuscript's canonical protocols**: 7 classes / 343 images and
  7 classes / 1,783 images with the eighth sonar class (`tire`, 834 root-level files) excluded by construction;
  the 67-class subset is the manuscript's marine reference domain. Chance levels are 14.29 % and 14.29 % and
  1.49 % respectively, and the sonar tree is imbalanced (`floats` 951/1,783).
* **`M(eps)` saturates on the coarse grid** (it is the margin CDF at `2 eps`, and the median margin of these
  deep operating points is negative), which is why the fine grid starts at 0.001 and why the median-margin
  relative statistic is reported alongside the absolute one.
* **Two adapted encoder ids are mirror-level facts.** `zjunlp/OceanCLIP-0.15B` was verified through the
  Hugging Face API on 2026-10-24 (the local snapshot's own file listing matches: `bioclip/…`,
  `oceanclip-bio/epoch_50.pt`); if the ModelScope fallback is ever needed, re-verify the id with
  `HubApi().get_model_files()` before trusting it. `imageomics/bioclip` is the official BioCLIP release used
  by open_clip's `hf-hub:` loader.
* **A partially loaded checkpoint is fatal by construction**: the open_clip loader refuses to encode when
  `load_state_dict` leaves any parameter uninitialised, and records the missing/unexpected key counts in the
  cache metadata (`model.load_report`) and therefore in `encoders.*.corpora.*.model_source`.
* **GPU contention and disk.** The analysis pass is CPU-only, but the encode pass needs the GPU; on an
  instance with other jobs running, expect the per-image rates of §4 to degrade. `HF_HOME` must stay on the
  data disk (`/root/autodl-tmp/hf`, ≈ 7 GB for the full registry) — the root disk is 30 GB.

## 9. Local verification record

Run on this workstation on 2026-10-24 (Python 3.12.14, torch 2.9.1+cu130, transformers 5.16.1,
open_clip 3.3.0, RTX 4060 Laptop 8 GB **shared with two other training jobs**), interpreter
`D:\Anaconda\envs\pytorch\python.exe`, `PYTHONIOENCODING=utf-8`.

```powershell
# pipeline proof over the two control corpora plus the 67-class subset, with the two local adapted encoders
D:\Anaconda\envs\pytorch\python.exe tools/_p1614_a23_multi_encoder_transfer.py --encode --include-adapted `
  --units clip-vit-base-patch32__marine_optical,clip-vit-base-patch32__acoustic_sonar,`
clip-vit-base-patch32__rare_species,bioclip__rare_species,oceanclip__rare_species --boot 2000
# statistics from the cache alone (17 s), after the bootstrap fix described below
D:\Anaconda\envs\pytorch\python.exe tools/_p1614_a23_multi_encoder_transfer.py --analyze --include-adapted `
  --units <same list> --boot 2000
# plan + assertions against the JSON just written
D:\Anaconda\envs\pytorch\python.exe tools/_p1614_a23_multi_encoder_transfer.py --dry-run --include-adapted `
  --units <same list> --boot 2000        # -> 68 asserted OK, 0 unasserted, 0 FAILED, exit 0
```

**What ran.** Five units were encoded and analysed: `clip-vit-base-patch32` on all three corpora, plus
`bioclip` and `oceanclip` on the 67-class subset (both present locally, and the two encoders the published
claim rests on). Encode times are the `encode_seconds` recorded inside each cache:
`clip-vit-base-patch32` 8.01 s (343 images) / 18.14 s (1,783) / 415.11 s (1,608); `bioclip` 287.12 s;
`oceanclip` 415.83 s. The analysis pass took 17 s; the JSON is 487 KB.

**The archived values are reproduced bit-exactly.** `reproduction.max_abs_diff = 0.0` with
`reproduced = true` on all four units that have an archived counterpart, over 128 compared values
(`top1` and `M(0.02)/M(0.05)/M(0.10)` for every λ row present in the archive):

| Unit | frozen top-1 (this run) | archived | archive | pairs compared |
|---|---|---|---|---|
| `clip-vit-base-patch32` / marine_optical | 21.574344 % | 21.574344 % | `a23_certificate_control.json` | 28 |
| `clip-vit-base-patch32` / acoustic_sonar | 22.041503 % | 22.041503 % | `a23_certificate_control.json` | 28 |
| `bioclip` / rare_species | 21.766169 % | 21.766169 % | `a23_certificate_adapted.json` | 36 |
| `oceanclip` / rare_species | 24.129353 % | 24.129353 % | `a23_certificate_adapted.json` | 36 |

The remaining unit is new (`clip-vit-base-patch32` / rare_species): frozen top-1 **6.5920 %** on 67 classes
(chance 1.4925 %), median margin −0.0304, `M(0.001) = 0.9428` — generic CLIP is nearly saturated even at the
finest grid on that corpus, which is exactly why the subset is the adapted encoders' domain.

**The correlations match the archived fine-eps run as well.** Restricted to the seven λ rows the control
archive carries (this family adds λ = 2.0 and the text-side row), the two CLIP control units produce identical
top-1 vectors and identical within-domain correlations with top-1 at every fine ε:

| Unit | ε | this run | `a23_fine_eps_certificate.json` |
|---|---|---|---|
| marine_optical | 0.001 / 0.002 / 0.005 / 0.01 / 0.02 | −0.3890 / +0.2224 / **+0.8175** / +0.5173 / +0.4344 | −0.3890 / +0.2224 / **+0.8175** / +0.5173 / +0.4344 |
| acoustic_sonar | 0.001 / 0.002 / 0.005 / 0.01 | −0.9977 / −0.9937 / −0.9423 / −0.4281 | −0.9977 / −0.9937 / −0.9423 / −0.4281 |

so the new pipeline is not merely "the same corpora": it lands on the archived numbers, including the
sign-flipping marine-optical relation that the manuscript cites as evidence that the certificate's resolution
is per-domain.

**Correlations with top-1 (five units, 45 family rows).** Pooled `r` is −0.9909 at ε = 0.001, −0.9603 at
0.002, −0.8620 at 0.005, −0.6979 at 0.01, −0.5331 at 0.02, and −0.9993 / −0.9988 / −0.9979 for the
median-margin-relative statistic at c = 0.005 / 0.01 / 0.02. Within units (nine family rows each), the archived
pattern repeats: `marine_optical` is the weak, sign-flipping one (−0.614 at ε = 0.001, **+0.905** at 0.005),
the sonar and the three subset units are strongly negative at ε ≤ 0.002 (−0.997, −0.995, −0.989, −0.988).

**Transfer table (5 units, 25 ordered pairs, 260 scored cross-unit entries, 0 degenerate).** Seven entries
reach a nominally above-chance target balanced accuracy and **none survives the paired bootstrap**. The best
nominal entry is `oceanclip__rare_species → clip-vit-base-patch32__marine_optical` at ε = 0.01: target BA
**1.000** with a source fit of **0.500** (the threshold was at chance on its own source family) and a 95 %
image-bootstrap interval on (BA − chance) of **[−0.150, +0.500]**. The verdict is therefore the archive's:
no threshold on `M` transfers, now measured over three corpora and three encoders locally, with the interval
computed rather than eyeballed. `conclusion.answer = "no"`, `conclusion.claim = "the no-transfer claim can be
widened to every registered encoder x corpus pair"`, and `conclusion.effect_on_a23_text.action` records that
this local selection covers only the three encoders already cited, so the sentence may be widened only after
the full 21-unit grid has been analysed.

**Two bugs were found and fixed by this verification** (kept in the record because they explain why the
bundled local JSON was rewritten once): the per-image indicators behind the bootstrap were initially built
from the statistic *value* instead of the per-configuration epsilon, which made every bootstrap interval
degenerate at exactly 0.5; and the health label of a bootstrap draw is recomputed from the resampled top-1
values, which is what makes the interval honest. The point estimates were unaffected by the first bug, so the
reproduction table above is valid for both runs.

**Nothing existing was touched.** `outputs/analysis/a23_fine_eps_certificate.json` (mtime 16:51) and its four
caches (15:36–15:54) all predate this run, and the new caches live in their own directory
(`outputs/analysis/_cache/a23_multiencoder/`, five files). `git status --porcelain` shows no modification of
any file outside this work: its entries are the untracked new files of the cloud round (this script, the shell
entry point, this document, plus the files the parallel cloud-round sessions added) and, at the time of the
last check, three modifications made by a parallel Paper 3 session
(`paper3/paper_ieee/audit_check.py`, `audit_pdf.py`, `supplementary/supplementary.tex`) which are not part of
this task. `outputs/` is gitignored, so the JSON and the caches do not appear there at all.

**The shell entry point was smoke-tested locally** under Git Bash with `FETCH=0` (no model download, per the
policy) and a single unit written to a temporary JSON path: the dry-run gate, the encode-with-cache-reuse
step, the analyze step, the acceptance check and the retrieval list all ran; the acceptance check correctly
refused the one-unit case until it was taught that `n_scored_entries_cross_unit` is 0 by construction when a
selection contains no pair. The cloud run is the same script with its real defaults.

The local JSON covers fewer units than the cloud run by construction (`meta.selection`,
`meta.complete_for_selection = true` for that selection); the cloud `--analyze` rebuilds the file from the
caches and replaces it wholesale.