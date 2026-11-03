#!/usr/bin/env bash
# Full corrected Qwen2-VL-2B sweep: 3 arms x 13 seeds, clean gap measurement.
#
# Two parallel streams rather than one sequential loop: each process holds a 4.4 GB bf16 model plus LoRA and
# activations (~7 GB), so two fit comfortably in the 32.8 GB card while halving the wall time. Seeds are split
# between the streams so no seed is run twice.
#
# Each (arm, seed) runs in its own process because switching arms inside one process accumulates CUDA fragmentation
# on this stack (noted in tools/_p47_qwen_train.py: unknown CUDA error on the vision_only arm).
set -uo pipefail
cd /root/p3
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
export PYTHONIOENCODING=utf-8
PY=/root/miniconda3/bin/python
OUT=outputs/vlm_clean
mkdir -p "$OUT"

SEEDS_A="42 456 1011 1616 2323 3131 4141"
SEEDS_B="123 789 1313 1919 2727 3737"

run_stream() {
  local tag="$1"; shift
  local seeds="$1"; shift
  for seed in $seeds; do
    for arm in text_only vision_only both; do
      local f="$OUT/${arm}_seed${seed}.json"
      [ -s "$f" ] && { echo "[$tag] skip $arm seed $seed (exists)"; continue; }
      echo "[$tag] $(date +%H:%M:%S) $arm seed $seed"
      $PY -u -X utf8 tools/_p1150_qwen_clean_sweep.py --apply \
        --arms "$arm" --seed "$seed" --maxsamples 400 --epochs 3 --batch 2 \
        --outdir "$OUT" >> "/root/p3/vlm_clean_${tag}.log" 2>&1
      echo "[$tag] $(date +%H:%M:%S) exit=$? $arm seed $seed"
    done
  done
  echo "[$tag] DONE $(date +%H:%M:%S)"
}

run_stream A "$SEEDS_A" &
PA=$!
run_stream B "$SEEDS_B" &
PB=$!
wait $PA $PB
echo "ALL_STREAMS_DONE $(date +%H:%M:%S)"
