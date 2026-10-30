#!/bin/bash
set -e
cd /root/autodl-tmp/a3
wc -l corpora/rsicd/human.jsonl corpora/rsicd/metadata.jsonl corpora/rsicd/humanrich.jsonl
wc -l corpora/nwpu_captions/human.jsonl corpora/nwpu_captions/metadata.jsonl corpora/nwpu_captions/humanrich.jsonl
ls -lh data/rsicd.jsonl data/nwpu_captions.jsonl models
python - <<PY
import json, io
for p in ("corpora/rsicd/human.jsonl", "corpora/nwpu_captions/human.jsonl"):
    rows = [json.loads(l) for l in io.open(p, encoding="utf-8")]
    print(p, len(rows), "splits", {s: sum(1 for r in rows if r["split"] == s) for s in ("train", "val", "test")})
PY
