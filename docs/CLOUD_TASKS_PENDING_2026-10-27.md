# Cloud tasks pending (recorded 2026-10-27 22:40, to run when the operator provides an instance)

Two experiments cannot run on the local 8 GB card. Everything below is ready except the GPU instance. **Do not start
anything until the operator says go.**

## Needed from the operator

An instance with **>= 24 GB VRAM** (A100 40G / A800 / 4090 48G / L40S class), plus host, port and password. Suggested
disk: >= 100 GB free for the corpus and the checkpoints. The earlier workflow files (`src/`, `experiments/`) and the
Flickr30k corpus are already staged under `local_runs/` on the laptop and can be uploaded in minutes.

## Task 1 — power upgrade (workstream A)

Goal: raise the underpowered controls to a resolvable number of seeds.

| arm | now | target | why |
|---|---|---|---|
| allocation contrast (guided vs uniform, capacity-matched) | 6 seeds | **16 seeds** | the paper's own resolution paragraph says 11–28 seeds are needed |
| random same-budget pool, seed-paired | 4 pairs | **12 pairs** | converts `UNDERPOWERED_TO_DISTINGUISH` into a resolved comparison |
| strict-freezing position arms (optional) | 5 seeds | 10 seeds | tightens the Table-1 bootstrap intervals |

Plan: `docs/PaperA_power_upgrade_plan.md`. Cost estimate: ~44 arms; 4-bit 7B LoRA, 10 epochs, 5000 samples; about
35–50 min per arm on a 32 GB-class card, 14–18 h at parallelism 2–3 after measuring VRAM.

**Blocker that must be solved on the instance**: the allocation-arm runner is not in the repository (`experiments/`
holds `strict_freeze_control.py`, `main.py`, `phase1_experiments.py` but no allocation driver). Either locate it under
`弃用/07_旧云轮/cloud_pack`, or rebuild it to the archived convention. This is the one code task still open.

## Task 2 — the full-protocol SigLIP arms (P3)

Goal: test the archived SigLIP reversal under the protocol it was measured with, because the local pilot cannot
(batch 32/16 and a 1000-image subset are not comparable; the operator ruled the local numbers out).

Fixed requirements from the archive (`outputs/analysis/siglip_row_verify.json`, `outputs/siglip_strict/seed*/`):

- backbone **siglip-base-patch16-224**, **rank 4**, alpha = 2r, **batch 128**, 10 epochs, 5000 samples, five seeds;
- corpus: **full Flickr30k** (the local slice of 1000 images is not acceptable);
- text length: SigLIP caps at **64 positions** - use `PEFT_MAX_SEQ_LEN`/the patched `src/dataset.py`, never 77;
- **no `attention_mask`** for SigLIP (the patched `src/trainer.py` drops it); doing otherwise triggers
  `device-side assert`.

Expected comparison target (authoritative archive, five seeds): text_only **+0.0664**, both **−0.0114**,
vision_only **+0.0522** DeltaCG.

## Execution protocol (both tasks, in this order)

1. **Probe first**: `nvidia-smi`, disk, which checkpoints and corpora are already present, and a 12-second mirror
   speed test before downloading anything.
2. **Three gates**: `--plan`, `--self-test`, `--dry-run` all exit 0; name-collision check on every arm's output file.
3. **One-arm smoke** on the instance; inspect the artefacts; measure peak VRAM with `nvidia-smi`.
4. **Parallelism from the measurement** (total <= ~85% of card memory, never guess).
5. **Run detached**, log per arm, `ps aux` before launching to avoid duplicate jobs.
6. **Retrieve, verify, then shut down**: pull every JSON, check size > 1 KB, assert fields, then
   `sync && shutdown -h now`, then confirm the port is closed.
7. **Register the results**: update `docs/QUANTITY_REGISTRY.json`, the appropriate ledger, and the HANDOFF entry before
   any manuscript change.

## What is ready on the laptop

- `src/` with the backbone-agnostic trainer (SigLIP support: class selection, `PEFT_MAX_SEQ_LEN`, attention-mask drop,
  `AutoModel` pristine reload), and `experiments/strict_freeze_control.py`;
- `local_runs/models/siglip-base-patch16-224` and `local_runs/models/clap-htsat-unfused` weights;
- `local_runs/real/flickr30k-images.zip` (4.09 GB) + annotations — upload the annotation JSON only, or re-download the
  pack on the instance through `hf_hub_download` with `HF_HUB_DISABLE_XET=1` (fast, verified);
- `tools/_p1771_local_b1_siglip.py` (arm runner) and `tools/_p1775_local_real_corpus.py` (corpus builder);
- the reproduction and provenance gates for whatever the cloud runs produce.
