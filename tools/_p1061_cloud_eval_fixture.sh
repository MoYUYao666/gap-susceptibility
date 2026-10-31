#!/usr/bin/env bash
# Fetch the held-out evaluation set on the host: the same COCO ids the LLaVA sweep measured, and only those.
#
# The laptop cannot pull the 472 MB annotation archive quickly, and the project's convention is that bulk data
# is fetched server-side anyway. This downloads it here, trims it to the first 2000 ids in file order -- which
# preserves the train/held-out split, since the sweep took ids[:1500] for training and the next 500 for
# measurement -- keeps only the 500 held-out images, and writes a manifest with both hashes so the set can be
# identified later.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
PY=/root/miniconda3/bin/python
ROOT=/root/p3/coco_eval
mkdir -p "$ROOT/val2014" "$ROOT/annotations"

echo "=== annotations (472 MB) ==="
if [ ! -s "$ROOT/annotations/captions_val2014.json" ]; then
  if [ ! -s "$ROOT/_ann.zip" ]; then
    echo "  downloading ..."
    curl -sSL --retry 3 -o "$ROOT/_ann.zip" \
      http://images.cocodataset.org/annotations/annotations_trainval2014.zip
  fi
  ls -la "$ROOT/_ann.zip"
  (cd "$ROOT" && unzip -o -q _ann.zip annotations/captions_val2014.json)
  rm -f "$ROOT/_ann.zip"
fi
ls -la "$ROOT/annotations/captions_val2014.json"

echo "=== trim and select the held-out ids ==="
$PY - <<'PYEOF'
import hashlib, json
from pathlib import Path
root = Path("/root/p3/coco_eval")
ann = json.loads((root / "annotations" / "captions_val2014.json").read_text(encoding="utf-8", errors="ignore"))
by = {}
for c in ann["annotations"]:
    by.setdefault(c["image_id"], []).append(c["caption"])
ids = list(by)[:2000]
held = ids[1500:2000]
keep = set(ids)
trimmed = {"info": ann.get("info", {}), "licenses": ann.get("licenses", []),
           "images": [im for im in ann["images"] if im["id"] in keep],
           "annotations": [c for c in ann["annotations"] if c["image_id"] in keep]}
p = root / "annotations" / "captions_val2014.json"
p.write_text(json.dumps(trimmed), encoding="utf-8")
(root / "ids.txt").write_text("\n".join(str(i) for i in held), encoding="utf-8")
(root / "urls.txt").write_text(
    "\n".join("http://images.cocodataset.org/val2014/COCO_val2014_%012d.jpg" % i for i in held) + "\n",
    encoding="utf-8")
man = {"purpose": "held-out evaluation pairs of the archived LLaVA sweep, rebuilt for the canonical DG*/CG recomputation",
       "rule": ("ids in annotation-file iteration order; training = first 1500, held-out = next 500, "
                "ids kept = 2000"),
       "n_held_out": len(held),
       "ids_sha256": hashlib.sha256(("\n".join(str(i) for i in held)).encode()).hexdigest(),
       "annotation_sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
(root / "MANIFEST.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
print("  held-out:", len(held), "| ids sha256:", man["ids_sha256"][:16])
PYEOF

echo "=== the 500 held-out images ==="
(cd "$ROOT/val2014" && xargs -a "$ROOT/urls.txt" -P 16 -n 1 -I{} sh -c 'f=$(basename {}); [ -s "$f" ] || curl -sS -o "$f" {}')
echo "  files: $(ls "$ROOT/val2014" | wc -l)"
du -sh "$ROOT"

echo "=== verification: every held-out image present and non-trivial ==="
$PY - <<'PYEOF'
from pathlib import Path
root = Path("/root/p3/coco_eval")
ids = [int(x) for x in (root / "ids.txt").read_text().split()]
missing = [i for i in ids if not (root / "val2014" / ("COCO_val2014_%012d.jpg" % i)).exists()]
small = [i for i in ids if (root / "val2014" / ("COCO_val2014_%012d.jpg" % i)).exists()
         and (root / "val2014" / ("COCO_val2014_%012d.jpg" % i)).stat().st_size < 5000]
print("  expected %d | missing %d | too small %d" % (len(ids), len(missing), len(small)))
print("  first ids:", ids[:5])
PYEOF
echo EVAL_FIXTURE_DONE
