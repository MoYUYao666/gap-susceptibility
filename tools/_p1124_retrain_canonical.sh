#!/usr/bin/env bash
# Retrain all twelve runs with the corrected script: real weights saved, canonical metric recorded per run.
#
# Operator decision 2026-10-17 (option A). Basis for believing this run is sound:
#   * smoke test: checkpoint holds 448 LoRA tensors (240 MB) instead of the empty dict found on 2026-10-16;
#   * canonical DG*/CG/DG_emp are computed and stored alongside the legacy definition, so the numbers are
#     comparable both with the paper and with the archived twelve;
#   * the model path is passed explicitly because the mirror-downloaded weights have no `refs/main` for the
#     hub client to resolve under HF_HUB_OFFLINE.
#
# Config is the same as the archived sweep (1500 train / 500 held out, 3 epochs, rank 8, bf16, 3 seeds, 4 arms)
# so the only differences are the metric definition and the fact that the weights are actually saved.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
COCO=/root/p3/coco_eval
MODEL=/root/autodl-tmp/hf/hub/models--llava-hf--llava-1.5-7b-hf/snapshots/main
LOG=/root/p3/retrain_canonical.log
OUT=outputs/llava_canonical

pkill -9 -f _p820_llava_sites || true
for i in $(seq 1 30); do
  u=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  [ "$u" -lt 2000 ] && break; sleep 5
done
echo "=== device ==="
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo "=== fixture ==="
ls "$COCO/val2014" | wc -l
ls -la "$COCO/annotations/captions_val2014.json"
echo "=== model path ==="
ls "$MODEL/model.safetensors.index.json"

rm -rf "$OUT"
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root "$COCO" --model "$MODEL" --precision bf16 --alloc-warmup-gb 1.5 \
  --samples 1500 --eval-pairs 500 --epochs 3 \
  --batch 2 --eval-batch 8 --max-len 2048 --seeds 3 --lr 1e-4 --rank 8 \
  --arms frozen,text_only,vision_only,both --apply --report-every 25 \
  --out-dir "$OUT" >> "$LOG" 2>&1
echo "sweep exit $?"
echo RETRAIN_DONE
