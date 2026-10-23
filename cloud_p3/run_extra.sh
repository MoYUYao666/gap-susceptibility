#!/bin/bash
set -u
BASE=/root/autodl-tmp/p3work
cd $BASE
PY=/root/miniconda3/bin/python
export HF_HUB_OFFLINE=1
echo "== convert dolly jsonl =="
$PY - <<'PY'
import io, json
import pandas as pd
rows = []
for line in io.open("/root/autodl-tmp/p3work/dolly_test.jsonl", encoding="utf-8"):
    d = json.loads(line)
    instr = d.get("instruction", "")
    ctx = d.get("context", "")
    if ctx:
        instr = instr + "\n\n" + ctx
    rows.append({"instruction": instr, "output": d.get("response", "")})
pd.DataFrame(rows).to_parquet("/root/autodl-tmp/p3work/paper3/train-dolly-00000.parquet")
print("dolly rows", len(rows))
PY
echo "== D4 dolly runs =="
for r in 4 5 6 7; do
  for s in 42 123; do
    $PY paper3/scripts/run_training.py --rank $r --seed $s --epochs 3 --num-samples 20 \
      --data-path paper3/train-dolly-00000.parquet >/dev/null 2>&1 || echo "FAIL d4 r$r s$s"
  done
done
echo "D4 DONE"
echo "== D1 LLaVA-OneVision =="
$PY tools/loo_run.py 2>&1 | tail -8
echo "D1 DONE"
echo "EXTRA_DONE $(date +%H:%M:%S)"
