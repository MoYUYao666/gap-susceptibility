#!/usr/bin/env bash
# A1 seed top-up: first re-download the ImageNet 50k shards, then serially run two extra seeds of the dose-response plus a second early-stopping seed.
# Usage (run in the background):
#   bash tools/a1_supplement_seeds.sh > a1_supplement.log 2>&1 &
# GPU strictly serial: this script runs only one python process at a time.
set -u
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1
PY="${PY:-/d/Anaconda/envs/pytorch/python.exe}"
LOG_PREFIX="[$(date '+%F %H:%M:%S')]"

say() { echo; echo "===== $LOG_PREFIX $* ====="; }

say "checking ImageNet 50k shards"
N=$(ls data/imagenet_hf/*.parquet 2>/dev/null | wc -l)
echo "  existing shards: $N / 14"
if [ "$N" -lt 14 ]; then
  say "trying to re-download (hf-mirror first, direct connection on failure; gated dataset, hf token available on this machine)"
  for EP in "https://hf-mirror.com" "https://huggingface.co"; do
    echo "--- endpoint: $EP"
    HF_ENDPOINT="$EP" HF_HUB_DISABLE_XET=1 "$PY" - <<'PY'
import os, sys
try:
    from huggingface_hub import snapshot_download
    p = snapshot_download('imagenet-1k', repo_type='dataset',
                          allow_patterns=['data/*.parquet'],
                          local_dir='data/imagenet_hf')
    print('  download complete ->', p)
except Exception as e:
    print('  failed:', type(e).__name__, str(e)[:200])
    sys.exit(3)
PY
    [ $? -eq 0 ] && break
  done
  N=$(ls data/imagenet_hf/*.parquet 2>/dev/null | wc -l)
  [ "$N" -lt 14 ] && {
    say "shards still not ready ($N/14) → training skipped."
    echo "  need to re-download the 14 parquet shards manually (≈6.4 GB) into data/imagenet_hf/:"
    echo "  · Thunder/browser (that is how it was downloaded originally; direct links for gated datasets may return 401/403)"
    echo "  · or on a network that can reach HF: HF_ENDPOINT=https://hf-mirror.com python -c \"from huggingface_hub import snapshot_download; snapshot_download('imagenet-1k', repo_type='dataset', allow_patterns=['data/*.parquet'], local_dir='data/imagenet_hf')\""
    echo "  · once in place, just rerun this script to top up the seeds automatically"
    exit 3; }
fi
echo "  shards ready: $(ls data/imagenet_hf/*.parquet | wc -l) files"

say "starting the seed top-up (4 λ × 2 seeds = 8 training runs; GPU serial)"
for lam in 0 0.1 0.5 1.0; do
  for seed in 123 456; do
    if [ -f "outputs/a1_class_aligned/lr$lam/seed$seed/eval_epoch10.json" ]; then
      echo "  skipping λ=$lam seed=$seed (eval_epoch10.json already present)"
      continue
    fi
    echo "--- $(date '+%H:%M:%S') training λ=$lam seed=$seed"
    "$PY" tools/train_class_aligned.py --lambda-reg "$lam" --seed "$seed" || {
      echo "  λ=$lam seed=$seed training failed, moving on to the next"; continue; }
    echo "--- $(date '+%H:%M:%S') endpoint eval λ=$lam seed=$seed (epoch 10)"
    "$PY" tools/train_class_aligned.py --eval-only --epoch 10 --lambda-reg "$lam" --seed "$seed" \
      || echo "  endpoint eval failed"
  done
done

say "second/third seed for the early-stopping table (λ=0, per epoch 1/2/3/5/10)"
for seed in 123 456; do
  for ep in 1 2 3 5 10; do
    f="outputs/a1_class_aligned/lr0/seed$seed/eval_epoch$ep.json"
    [ -f "$f" ] && { echo "  skipping λ=0 seed=$seed ep=$ep"; continue; }
    echo "--- $(date '+%H:%M:%S') eval λ=0 seed=$seed ep=$ep"
    "$PY" tools/train_class_aligned.py --eval-only --epoch "$ep" --lambda-reg 0 --seed "$seed" \
      || echo "  eval failed ep=$ep"
  done
done

say "done; summarizing the endpoint results of each configuration"
for lam in 0 0.1 0.5 1.0; do
  for seed in 123 456; do
    f="outputs/a1_class_aligned/lr$lam/seed$seed/eval_epoch10.json"
    [ -f "$f" ] && echo "  λ=$lam seed=$seed: $(cat "$f")"
  done
done
echo
echo "===== finished $(date '+%F %H:%M:%S') ====="
