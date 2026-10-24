#!/bin/bash
# Phase 1 driver: the matched decoder ladder, run sequentially in the background.
# Runs on the cloud box; resumable (a valid output is skipped).
cd /root/autodl-tmp/p3work || exit 1
PY=/root/miniconda3/bin/python
L=logs
mkdir -p $L outputs/analysis

# the smoke runs wrote to the seed42 filenames; remove them so the real runs are not skipped
rm -f outputs/analysis/decoder_attribution_llava15-7b_contrastive_seed42.json \
      outputs/analysis/decoder_attribution_llava15-7b_generative_seed42.json

for spec in "llava15-7b contrastive" "llava15-7b generative" \
            "qwen2vl-2b contrastive" "qwen2vl-2b generative" "qwen25vl-7b generative"; do
  set -- $spec
  M=$1; O=$2
  OUT=outputs/analysis/decoder_attribution_${M}_${O}_seed42.json
  if [ -s "$OUT" ]; then echo "skip $M $O (exists)"; continue; fi
  echo "=== $M $O start $(date -Is) ==="
  timeout 21600 $PY tools/_p1612_objective_control_multimodel.py --model "$M" --objective "$O" \
      --seed 42 --protocol match --apply > "$L/p1_${M}_${O}.log" 2>&1
  echo "rc=$? end $(date -Is)" >> "$L/p1_${M}_${O}.log"
  echo "--- $M $O tail ---"; tail -n 3 "$L/p1_${M}_${O}.log"
done
echo "P1_DONE $(date -Is)"