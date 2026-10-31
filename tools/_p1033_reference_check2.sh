#!/usr/bin/env bash
# Definitive comparison: the restored sweep against the patched one, same configuration, no determinism.
#
# The deterministic run was abandoned as too slow (26 minutes without producing a record -- the earlier
# 94 s/step measurement was for 4-bit; bf16 with determinism is slower still). Determinism is not needed for
# this comparison: the patched script produced **loss 4.3099** for this exact configuration and the frozen
# reference is **2.9496**, a gap far larger than the 1.7e-3 run-to-run spread. So the restored script is run
# once with the identical arguments and the loss is compared against the patched value.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
COCO=/root/p3/coco_full

pkill -9 -f _p820_llava_sites || true
for i in $(seq 1 40); do
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  [ "$used" -lt 2000 ] && break
  echo "  waiting for the device: ${used} MiB"; sleep 10
done

echo "=== restored sweep: 5 steps, samples 20, batch 2 (patched script gave 4.3099 here) ==="
rm -rf outputs/refcheck2
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root "$COCO" --precision bf16 --alloc-warmup-gb 1.5 \
  --samples 20 --eval-pairs 10 --epochs 1 --batch 2 --max-len 2048 \
  --seeds 1 --rank 8 --arms text_only --bench-steps 5 --report-every 5 --apply \
  --out-dir outputs/refcheck2 > /root/p3/refcheck2.out 2>&1
echo "exit=$?"
echo "=== result ==="
grep -aE "batch tokens|epoch 1/1|held-out" /root/p3/refcheck2.out | head -6
echo REFCHECK2_DONE
