#!/usr/bin/env bash
# Five-minute smoke test of the modified sweep on the host, before an eight-hour retrain.
#
# Verifies the three things that would otherwise waste the whole run:
#   1. the canonical DG* / CG / DG_emp are computed and printed (not the legacy definition alone);
#   2. the saved checkpoint is NON-EMPTY -- the `model` dict must hold the trainable tensors, which is exactly
#      what failed on 2026-10-16 when every checkpoint came out as `{'model': {}, ...}`;
#   3. the record JSON carries the canonical fields.
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

pkill -9 -f _p820_llava_sites || true
for i in $(seq 1 30); do
  u=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  [ "$u" -lt 2000 ] && break; sleep 5
done

echo "=== static markers in the uploaded sweep ==="
grep -c "_trainable_names" tools/_p820_llava_sites.py
grep -c "dg_star = float(" tools/_p820_llava_sites.py
grep -c "out.hidden_states\[-1\]" tools/_p820_llava_sites.py

echo "=== smoke: 1 arm, 3 steps, 16 pairs ==="
rm -rf outputs/smoke_canonical
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root "$COCO" --model "$MODEL" --precision bf16 --alloc-warmup-gb 1.5 \
  --samples 16 --eval-pairs 8 --epochs 1 --batch 2 --eval-batch 8 --max-len 2048 \
  --seeds 1 --rank 8 --arms text_only --bench-steps 3 --report-every 1 --apply \
  --out-dir outputs/smoke_canonical > /root/p3/smoke_canonical.out 2>&1
echo "  exit=$?"
echo
echo "=== key output ==="
grep -aE "batch tokens|canonical DG|legacy|trainable|epoch 1/1|ARM FAILED|Traceback|Error" \
  /root/p3/smoke_canonical.out | head -14
echo
echo "=== checkpoint contents (must NOT be empty) ==="
$PY - <<'PYEOF'
import glob, torch
from pathlib import Path
fs = sorted(glob.glob("/root/p3/outputs/smoke_canonical/*.pt"))
if not fs:
    print("  NO CHECKPOINT WRITTEN")
else:
    for f in fs:
        obj = torch.load(f, map_location="cpu")
        model = obj.get("model", {})
        print(f"  {Path(f).name}: {Path(f).stat().st_size/1e6:.1f} MB | model tensors: {len(model)}")
        for k, v in list(model.items())[:3]:
            print(f"      {k} {tuple(v.shape)}")
        print("  ->", "NON-EMPTY (good)" if len(model) else "EMPTY (the defect is back)")
PYEOF
echo
echo "=== record fields ==="
$PY - <<'PYEOF'
import glob, json
fs = [f for f in glob.glob("/root/p3/outputs/smoke_canonical/*.json") if "progress" not in f and "sites" not in f]
for f in fs:
    d = json.load(open(f, encoding="utf-8"))
    keys = ("arm", "dg_star_before", "dg_star_after", "dg_star_rel_change",
            "cg_canonical_after", "dg_empirical_after", "dg_before", "dg_after")
    print(f"  {f.split('/')[-1]}")
    for k in keys:
        print(f"    {k:<22} {d.get(k)}")
PYEOF
echo SMOKE_DONE
