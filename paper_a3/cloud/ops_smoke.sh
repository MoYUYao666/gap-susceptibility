#!/bin/bash
set -e
export PATH=/root/miniconda3/bin:$PATH
export PYTHONIOENCODING=utf-8
export HF_ENDPOINT=https://hf-mirror.com
cd /root/autodl-tmp/a3
mkdir -p runs/logs
echo "[smoke] start $(date)"
python -u scripts/train_lora_provenance.py --corpus corpora/rsicd/human.jsonl --images-root data/rsicd   --model models/RemoteCLIP-ViT-L-14.pt --site both --seed 0 --epochs 2 --batch 8 --max-pairs 10000   --one-per-image --workers 8 --out-prefix runs/smoke_l14
echo "[smoke] done $(date)"
python - <<PY
import json, io
r = json.loads(io.open("runs/smoke_l14.json", encoding="utf-8").read())
print("SMOKE_R1", r["metrics"]["R@1_i2t"], "peak_vram_gb", r.get("peak_vram_gb"), "wall_min", round(r["wall_seconds"]/60, 1), "pairs", r.get("pairs_used"))
PY
echo SMOKE_DONE
