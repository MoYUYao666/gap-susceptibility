#!/bin/bash
set -e
export PATH=/root/miniconda3/bin:$PATH
export PYTHONIOENCODING=utf-8
cd /root/autodl-tmp/a3
echo "[nwpu] start $(date)"
python scripts/convert_nwpu.py --data-root data/nwpu_captions --out data/nwpu_captions.jsonl
rm -f data/rsicd/*.parquet data/nwpu_captions/*.parquet
echo "[nwpu] done $(date)"
python cloud/build_corpora.py
echo "[corpora] done $(date)"
du -sh data corpora models
df -h /root/autodl-tmp | tail -1
echo DATA_DONE
