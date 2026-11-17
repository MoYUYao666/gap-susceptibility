# Paper B v2 — PEFT checkpoint-selection data and analysis

This directory releases the **derived data and analysis code** for the Paper B v2 manuscript on checkpoint
selection in parameter-efficient fine-tuning. It contains **no manuscript source, PDF, cover letter, or model
weights**.

## Evidence

- **552 runs / 1656 checkpoints**
  - CLIP-B/32: 324 runs (144 frozen + 180 full-P1)
  - CLIP-B/16: 144 runs
  - SigLIP-B/16: 36 runs
  - TextVQA/Qwen2-VL: 16 runs
  - VQAv2/Qwen2-VL: 16 runs
  - ChartQA/Qwen2-VL: 16 runs
- Every run has three epoch records.

## Layout

| path | content |
|---|---|
| `results/` | aggregate JSON files used by the manuscript |
| `analysis/` | scripts that write every reported aggregate |
| `experiments/` | CLIP/SigLIP/Qwen runners |
| `../outputs/paper_b/` | per-run JSON records (CLIP, CLIP-B/16, P1, SigLIP, Qwen VQA) |
| `gate_check.py`, `gate_check_prl.py` | submission gates |
| `THEORY.md`, `P1_FULL_ANALYSIS.md`, `FINAL_AUDIT.md` | theory and analysis notes |

## Reproduce

The analysis is deterministic given the per-run JSONs:

```bash
python paper_b_v2/analysis/p1_full.py
python paper_b_v2/analysis/qwen_vqa_three_datasets.py
python paper_b_v2/gate_check.py
python paper_b_v2/gate_check_prl.py
```

Some scripts expect the historical local dataset/model paths; the result JSONs are the frozen artifacts and are
included so every aggregate can be checked without re-running training.

## Scope and caveats

- VQA evidence is a small single-protocol pilot (80 train / 12 test questions per task), not a full VQA benchmark.
- The theory notes label standard results explicitly; no new theorem is claimed.
- No raw datasets or model weights are redistributed.
