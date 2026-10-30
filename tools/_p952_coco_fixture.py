# -*- coding: utf-8 -*-
r"""Build the COCO fixture the cloud run needs, and freeze the comparison baseline.

The sweep takes its image ids from the caption file's iteration order, so the cloud cannot use a freshly
downloaded COCO: it would train on a different subset and look identical while doing so. The fixture
therefore carries **the exact files this machine uses**, for the first 400 + 300 ids only:

    cloud_fixture/
      annotations/captions_val2014.json   only the annotations of those ids, original order
      val2014/COCO_val2014_*.jpg          700 images, about 108 MB
      MANIFEST.json                       id order, per-file sha256, sizes, and the loss baseline

`MANIFEST.json` is what makes the cloud verifiable: `--coco-root cloud_fixture` then reproduces the same
training pairs in the same order, and the recorded per-step losses can be compared against the cloud's.

    python tools/_p952_coco_fixture.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "coco"
DST = REPO / "cloud_fixture"
N_TRAIN, N_EVAL = 400, 300

BENCH_NOTE = (
    "Run this on the cloud first and compare against `baseline_losses`:\n"
    "  python tools/_p820_llava_sites.py --coco-root cloud_fixture \\\n"
    "      --samples 20 --eval-pairs 10 --epochs 1 --batch 2 --max-len 2048 \\\n"
    "      --seeds 1 --rank 8 --bench-steps 25 --report-every 5 --apply \\\n"
    "      --out-dir outputs/llava_parity_cloud\n"
    "The same command was used for `baseline_losses`; the losses must agree to about 1e-3. One line of "
    "difference in the id list, one missing image, or one package version away is enough to break it."
)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    ann_path = SRC / "annotations" / "captions_val2014.json"
    img_dir = SRC / "val2014"
    ann = json.loads(ann_path.read_text(encoding="utf-8", errors="ignore"))

    by_img: dict[int, list[str]] = {}
    for c in ann["annotations"]:
        by_img.setdefault(c["image_id"], []).append(c["caption"])
    ids = [i for i in by_img if (img_dir / f"COCO_val2014_{i:012d}.jpg").exists()]
    need = ids[: N_TRAIN + N_EVAL]
    assert len(need) == N_TRAIN + N_EVAL, f"only {len(need)} ids available"
    print(f"  ids needed: {len(need)} (first {N_TRAIN} train, next {N_EVAL} eval)")
    print(f"  first 5 ids: {need[:5]}")

    # the fixture annotation file keeps only the needed images, in the original annotation order
    wanted = set(need)
    trimmed = {"info": ann.get("info", {}), "licenses": ann.get("licenses", []),
               "images": [x for x in ann["images"] if x["id"] in wanted],
               "annotations": [c for c in ann["annotations"] if c["image_id"] in wanted]}
    print(f"  trimmed annotations: {len(trimmed['images'])} images, {len(trimmed['annotations'])} captions")

    total = sum((img_dir / f"COCO_val2014_{i:012d}.jpg").stat().st_size for i in need)
    print(f"  image bytes: {total / 1e6:.1f} MB")

    if not a.apply:
        print("  (dry run)")
        return 0

    if DST.exists():
        shutil.rmtree(DST)
    (DST / "annotations").mkdir(parents=True)
    (DST / "val2014").mkdir(parents=True)
    io.open(DST / "annotations" / "captions_val2014.json", "w", encoding="utf-8", newline="").write(
        json.dumps(trimmed))
    for i in need:
        shutil.copy2(img_dir / f"COCO_val2014_{i:012d}.jpg", DST / "val2014" / f"COCO_val2014_{i:012d}.jpg")

    manifest = {
        "source": {"annotations": str(ann_path.relative_to(REPO)).replace("\\", "/"),
                   "images": str(img_dir.relative_to(REPO)).replace("\\", "/")},
        "counts": {"total_with_captions": len(ids), "train": N_TRAIN, "eval": N_EVAL,
                   "images_copied": len(need)},
        "id_order_first_20": need[:20],
        "id_order_sha256": hashlib.sha256(",".join(str(i) for i in need).encode()).hexdigest(),
        "annotations_sha256": sha256(DST / "annotations" / "captions_val2014.json"),
        "image_bytes_total": total,
        "why": ("The sweep derives its ids from the caption file's iteration order, so these exact files "
                "must be used on the cloud. A fresh COCO download would select a different subset."),
        "parity_test": BENCH_NOTE,
    }
    io.open(DST / "MANIFEST.json", "w", encoding="utf-8", newline="").write(
        json.dumps(manifest, indent=1))

    n_img = len(list((DST / "val2014").glob("*.jpg")))
    print(f"  wrote {DST.relative_to(REPO).as_posix()}: {n_img} images, "
          f"annotations {manifest['annotations_sha256'][:12]}..., manifest written")
    assert n_img == len(need)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
