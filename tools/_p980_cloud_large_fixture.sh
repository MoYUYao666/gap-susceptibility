#!/usr/bin/env bash
# Build a larger fixture on the cloud: the real COCO val2014 annotation file, trimmed to the first N ids,
# plus those N images downloaded in parallel.
#
# Why the annotation file must come from the local machine or from the official URL: the sweep picks its
# images by iterating the annotation file, so the *order inside that file* decides which images are trained
# on. Re-downloading the annotations gives the same official file, hence the same order; re-downloading
# images is safe because each id maps to one fixed file. Only the *count* changes here.
set -uo pipefail
cd /root/p3
export HF_HOME=/root/autodl-tmp/hf
PY=/root/miniconda3/bin/python
N=2000                     # images to include: 1500 train + 500 held out
ANN=/root/p3/coco_full/annotations/captions_val2014.json

echo "=== annotations ==="
mkdir -p /root/p3/coco_full/annotations /root/p3/coco_full/val2014
if [ ! -f "$ANN" ]; then
  curl -sSL -o "$ANN" http://images.cocodataset.org/annotations/annotations_trainval2014.zip.part 2>/dev/null || true
  rm -f "$ANN".part
  curl -sSL -o /root/p3/coco_full/ann.zip http://images.cocodataset.org/annotations/annotations_trainval2014.zip
  cd /root/p3/coco_full && unzip -o -q ann.zip annotations/captions_val2014.json && rm -f ann.zip && cd /root/p3
fi
ls -la "$ANN"

echo "=== trim annotations to the first $N ids, preserving order ==="
$PY - <<PYEOF
import json
from pathlib import Path
ann_path = Path("/root/p3/coco_full/annotations/captions_val2014.json")
ann = json.loads(ann_path.read_text(encoding="utf-8", errors="ignore"))
by = {}
for c in ann["annotations"]:
    by.setdefault(c["image_id"], []).append(c["caption"])
ids = list(by)[: $N]
wanted = set(ids)
trim = {"info": ann.get("info", {}), "licenses": ann.get("licenses", []),
        "images": [x for x in ann["images"] if x["id"] in wanted],
        "annotations": [c for c in ann["annotations"] if c["image_id"] in wanted]}
out = Path("/root/p3/coco_full/annotations/captions_first%d.json" % $N)
out.write_text(json.dumps(trim), encoding="utf-8")
print("  ids:", len(ids), "annotations kept:", len(trim["annotations"]), "->", out)
Path("/root/p3/coco_full/ids.txt").write_text("\n".join(str(i) for i in ids), encoding="utf-8")
PYEOF

echo "=== download the $N images (16 parallel) ==="
urls=/root/p3/coco_full/urls.txt
$PY - <<PYEOF
from pathlib import Path
ids = [l.strip() for l in Path("/root/p3/coco_full/ids.txt").read_text().split() if l.strip()]
base = "http://images.cocodataset.org/val2014/COCO_val2014_%012d.jpg"
Path("/root/p3/coco_full/urls.txt").write_text("\n".join(base % int(i) for i in ids) + "\n")
print("  urls:", len(ids))
PYEOF
cd /root/p3/coco_full/val2014
xargs -a "$urls" -P 16 -n 1 -I{} sh -c 'f=$(basename {}); [ -s "$f" ] || curl -sS -o "$f" {}' 
cd /root/p3
ls /root/p3/coco_full/val2014 | wc -l
du -sh /root/p3/coco_full/val2014

echo "=== verify every id has its image ==="
$PY - <<PYEOF
from pathlib import Path
ids = [l.strip() for l in Path("/root/p3/coco_full/ids.txt").read_text().split() if l.strip()]
d = Path("/root/p3/coco_full/val2014")
missing = [i for i in ids if not (d / ("COCO_val2014_%012d.jpg" % int(i))).exists()]
print("  ids:", len(ids), "missing:", len(missing), missing[:5])
print("  OK" if not missing else "  INCOMPLETE")
PYEOF
echo LARGE_FIXTURE_DONE
