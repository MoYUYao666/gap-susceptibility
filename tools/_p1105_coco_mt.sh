#!/usr/bin/env bash
# COCO fixture: multi-connection annotation archive, then trim and fetch the 500 held-out images.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
PY=/root/miniconda3/bin/python
ROOT=/root/p3/coco_eval
ZIP=$ROOT/annotations_trainval2014.zip
mkdir -p "$ROOT/val2014" "$ROOT/annotations"

echo "=== annotation archive, 32 connections ==="
if [ ! -s "$ZIP" ] || [ "$(stat -c %s "$ZIP")" -lt 470000000 ]; then
  $PY /root/p3/tools/_p1101_parallel_fetch_any.py \
    --base "http://images.cocodataset.org/annotations/{f}" \
    --files annotations_trainval2014.zip --sizes 0 \
    --dest "$ROOT" 2>&1 | tail -8
fi
ls -la "$ZIP" 2>/dev/null || echo "  archive missing"

echo "=== trim to the first 2000 ids and select the held-out 500 ==="
$PY - <<'PYEOF'
import json, hashlib, zipfile
from pathlib import Path
root = Path("/root/p3/coco_eval")
zp = root / "annotations_trainval2014.zip"
if not zp.exists():
    raise SystemExit("  no archive; aborting")
with zipfile.ZipFile(zp) as zf:
    ann = json.loads(zf.read("annotations/captions_val2014.json"))
by = {}
for c in ann["annotations"]:
    by.setdefault(c["image_id"], []).append(c["caption"])
ids = list(by)[:2000]
held = ids[1500:2000]
keep = set(ids)
trimmed = {"info": ann.get("info", {}), "licenses": ann.get("licenses", []),
           "images": [i for i in ann["images"] if i["id"] in keep],
           "annotations": [c for c in ann["annotations"] if c["image_id"] in keep]}
ap = root / "annotations" / "captions_val2014.json"
ap.write_text(json.dumps(trimmed), encoding="utf-8")
(root / "ids.txt").write_text("\n".join(str(i) for i in held), encoding="utf-8")
(root / "urls.txt").write_text(
    "\n".join("http://images.cocodataset.org/val2014/COCO_val2014_%012d.jpg" % i for i in held) + "\n",
    encoding="utf-8")
man = {"purpose": "held-out pairs of the archived LLaVA sweep, for the canonical DG*/CG recomputation",
       "rule": "annotation-file order; training=first 1500, held-out=next 500, ids kept=2000",
       "n_held_out": len(held),
       "ids_sha256": hashlib.sha256(("\n".join(str(i) for i in held)).encode()).hexdigest(),
       "annotation_sha256": hashlib.sha256(ap.read_bytes()).hexdigest()}
(root / "MANIFEST.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
print("  held-out:", len(held), "| first ids:", held[:5])
print("  ids sha256:", man["ids_sha256"][:16], "| ann sha256:", man["annotation_sha256"][:16])
PYEOF

echo "=== the 500 held-out images, 24 parallel ==="
(cd "$ROOT/val2014" && xargs -a "$ROOT/urls.txt" -P 24 -n 1 -I{} sh -c 'f=$(basename {}); [ -s "$f" ] || curl -sS -m 90 -o "$f" {}')
echo "  files: $(ls "$ROOT/val2014" | wc -l)"

echo "=== verification ==="
$PY - <<'PYEOF'
from pathlib import Path
root = Path("/root/p3/coco_eval")
ids = [int(x) for x in (root / "ids.txt").read_text().split()]
missing = [i for i in ids if not (root / "val2014" / ("COCO_val2014_%012d.jpg" % i)).exists()]
small = [i for i in ids if (root / "val2014" / ("COCO_val2014_%012d.jpg" % i)).exists()
         and (root / "val2014" / ("COCO_val2014_%012d.jpg" % i)).stat().st_size < 5000]
print("  expected %d | missing %d | too small %d" % (len(ids), len(missing), len(small)))
PYEOF
rm -f "$ZIP"
du -sh "$ROOT"
echo COCO_MT_DONE
