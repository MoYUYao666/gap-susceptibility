#!/usr/bin/env bash
# Restart the sweep with the hardened release and the per-arm exception guard.
#
# Changes since the last attempt:
#   * the between-arm release now also calls synchronize and ipc_collect, and reports the sizes, because
#     three arms have died at a reload and the earlier release was not returning the memory;
#   * one arm failing no longer ends the sweep: the arm body is wrapped, the traceback goes to
#     outputs/llava_bf16_sites/ARM_FAILURES.txt, and the run continues with the next arm;
#   * the log is no longer piped through `grep`, which buffers and swallowed the tail (the last attempt's
#     log simply stopped mid-heartbeat with no error in it).
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
COCO=/root/p3/coco_full
LOG=/root/p3/sweep_run.log

echo "=== device before ==="
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader

echo "=== records already on disk (skipped on restart) ==="
ls outputs/llava_bf16_sites/*.json 2>/dev/null | xargs -n1 basename

echo "=== free the device and prove it is back to zero ==="
pkill -9 -f _p820_llava_sites || true
for i in $(seq 1 40); do
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  [ "$used" -lt 2000 ] && break
  echo "  waiting: ${used} MiB"; sleep 10
done
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader

echo "=== sweep version ==="
grep -c "_arm_guard" tools/_p820_llava_sites.py
grep -c "ipc_collect" tools/_p820_llava_sites.py

echo "=== resume: bf16, 1500 train / 500 held out, batch 2, eval-batch 32, 3 epochs, 3 seeds, 4 arms ==="
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root "$COCO" --precision bf16 --alloc-warmup-gb 1.5 \
  --samples 1500 --eval-pairs 500 --epochs 3 \
  --batch 2 --eval-batch 32 --max-len 2048 --seeds 3 --lr 1e-4 --rank 8 \
  --arms frozen,text_only,vision_only,both --apply --report-every 25 \
  --out-dir outputs/llava_bf16_sites >> "$LOG" 2>&1
echo "sweep exit $?"
echo BF16_SWEEP_DONE
