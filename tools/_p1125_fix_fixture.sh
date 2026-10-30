#!/usr/bin/env bash
# Stop the retrain, fetch all 2000 images (the run had only the 500 held-out ones), and relaunch.
#
# What went wrong, from the log: `train_progress.json` reported `steps_total: 750` instead of 2250, and the frozen
# arm failed with
#     TypeError: unsupported format string passed to NoneType.__format__
# at the canonical print. Both follow from the fixture: only the 500 held-out images were downloaded, so
#     ids          = [i for i in by_img if (val2014 / ...).exists()]   -> 500 entries
#     train_ids    = ids[:1500]                                        -> 500
#     eval_ids     = ids[1500:2000]                                    -> EMPTY
# The empty evaluation set makes `measure()` return None for both sides, which the new print then formats.
# Fix: download all 2000 images, and make the print tolerate None (a missing measurement must not kill an arm).
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
PY=/root/miniconda3/bin/python
ROOT=/root/p3/coco_eval

echo "=== stop the retrain ==="
pkill -9 -f _p1124.sh || true
pkill -9 -f _p820_llava_sites || true
sleep 3
nvidia-smi --query-gpu=memory.used --format=csv,noheader

echo "=== which ids exist now? ==="
$PY - <<'PYEOF'
import json
from pathlib import Path
root = Path("/root/p3/coco_eval")
ann = json.loads((root / "annotations" / "captions_val2014.json").read_text(encoding="utf-8"))
by = {}
for c in ann["annotations"]:
    by.setdefault(c["image_id"], []).append(c["caption"])
ids = list(by)
present = [i for i in ids if (root / "val2014" / ("COCO_val2014_%012d.jpg" % i)).exists()]
print(f"  ids in annotation: {len(ids)} | images present: {len(present)}")
(root / "all_ids.txt").write_text("\n".join(str(i) for i in ids), encoding="utf-8")
(root / "all_urls.txt").write_text(
    "\n".join("http://images.cocodataset.org/val2014/COCO_val2014_%012d.jpg" % i for i in ids) + "\n",
    encoding="utf-8")
PYEOF

echo "=== fetch all 2000 images (24 parallel) ==="
(cd "$ROOT/val2014" && xargs -a "$ROOT/all_urls.txt" -P 24 -n 1 -I{} sh -c 'f=$(basename {}); [ -s "$f" ] || curl -sS -m 90 -o "$f" {}')
echo "  files now: $(ls "$ROOT/val2014" | wc -l)"

$PY - <<'PYEOF'
import json
from pathlib import Path
root = Path("/root/p3/coco_eval")
ann = json.loads((root / "annotations" / "captions_val2014.json").read_text(encoding="utf-8"))
by = {}
for c in ann["annotations"]:
    by.setdefault(c["image_id"], []).append(c["caption"])
ids = [i for i in by if (root / "val2014" / ("COCO_val2014_%012d.jpg" % i)).exists()]
print(f"  usable ids: {len(ids)}  (train would take {len(ids[:1500])}, eval {len(ids[1500:2000])})")
assert len(ids) >= 2000, "still not enough images"
print("  OK: 2000 available")
PYEOF
echo IMAGES_DONE
