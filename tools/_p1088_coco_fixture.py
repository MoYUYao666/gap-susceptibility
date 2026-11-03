# -*- coding: utf-8 -*-
r"""Fetch the COCO val2014 annotation archive with many connections, then trim it to the held-out ids.

The official archive crawls at ~400 B/s single-connection from this host, the same symptom ModelScope's weights
showed before the multi-connection fetcher took them to 15 MB/s. The archive is a plain, range-supporting HTTP
resource, so the same splitter applies. After it is on disk the script trims it to the first 2000 ids -- keeping
the annotation-file order, which is what makes the held-out 500 the same pairs the archived run measured -- and
downloads just those 500 images.

    python tools/_p1088_coco_fixture.py  (runs on the host)
"""
from __future__ import annotations

import io
import json
import os
import sys
import threading
import time
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

URL = "http://images.cocodataset.org/annotations/annotations_trainval2014.zip"
IMG = "http://images.cocodataset.org/val2014/COCO_val2014_{:012d}.jpg"
ROOT = Path("/root/p3/coco_eval")
CHUNK = 8 * 1024 * 1024
WORKERS = 32
TRAIN, EVAL, TOTAL = 1500, 500, 2000

_done = {"b": 0}
_lock = threading.Lock()


def head_size(url: str) -> int:
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=30) as r:
        return int(r.headers["Content-Length"])


def grab(url: str, s: int, e: int, dst: Path) -> bool:
    if dst.exists() and dst.stat().st_size == e - s + 1:
        with _lock:
            _done["b"] += dst.stat().st_size
        return True
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"Range": f"bytes={s}-{e}"})
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
            if len(data) != e - s + 1:
                raise IOError("short read")
            dst.write_bytes(data)
            with _lock:
                _done["b"] += len(data)
            return True
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return False


def multi_fetch(url: str, dst: Path) -> bool:
    parts = dst.parent / (dst.name + ".parts")
    parts.mkdir(parents=True, exist_ok=True)
    size = head_size(url)
    ranges = [(s, min(s + CHUNK - 1, size - 1)) for s in range(0, size, CHUNK)]
    print(f"  {dst.name}: {size/1e6:.0f} MB in {len(ranges)} chunks", flush=True)
    t0 = time.time()
    stop = threading.Event()

    def report() -> None:
        last = 0
        while not stop.wait(10):
            with _lock:
                b = _done["b"]
            print(f"    {b/1e6:.0f}/{size/1e6:.0f} MB  {(b-last)/10/1e6:.1f} MB/s", flush=True)
            last = b

    th = threading.Thread(target=report, daemon=True)
    th.start()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        ok = all(f.result() for f in
                 [ex.submit(grab, url, s, e, parts / f"{s:012d}.part") for s, e in ranges])
    stop.set()
    if not ok:
        print("  some chunks failed; parts kept", flush=True)
        return False
    with open(dst, "wb") as out:
        for s, _e in ranges:
            out.write((parts / f"{s:012d}.part").read_bytes())
    for s, _e in ranges:
        (parts / f"{s:012d}.part").unlink(missing_ok=True)
    parts.rmdir()
    dt = time.time() - t0
    print(f"  {dst.name}: {dst.stat().st_size/1e6:.0f} MB in {dt:.0f} s "
          f"({dst.stat().st_size/1e6/dt:.1f} MB/s)", flush=True)
    return True


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "val2014").mkdir(exist_ok=True)
    (ROOT / "annotations").mkdir(exist_ok=True)

    zpath = ROOT / "annotations_trainval2014.zip"
    if not (zpath.exists() and zpath.stat().st_size > 400_000_000):
        if not multi_fetch(URL, zpath):
            return 1
    print(f"  archive ready: {zpath.stat().st_size/1e6:.0f} MB")

    with zipfile.ZipFile(zpath) as zf:
        raw = zf.read("annotations/captions_val2014.json")
    ann = json.loads(raw)
    by: dict[int, list[str]] = {}
    for c in ann["annotations"]:
        by.setdefault(c["image_id"], []).append(c["caption"])
    ids = list(by)[:TOTAL]
    held = ids[TRAIN:TRAIN + EVAL]
    keep = set(ids)
    trimmed = {"info": ann.get("info", {}), "licenses": ann.get("licenses", []),
               "images": [i for i in ann["images"] if i["id"] in keep],
               "annotations": [c for c in ann["annotations"] if c["image_id"] in keep]}
    ap = ROOT / "annotations" / "captions_val2014.json"
    ap.write_text(json.dumps(trimmed), encoding="utf-8")
    (ROOT / "ids.txt").write_text("\n".join(str(i) for i in held), encoding="utf-8")
    print(f"  trimmed: {len(trimmed['images'])} images, {len(trimmed['annotations'])} captions; "
          f"held-out {len(held)}; first ids {held[:5]}")

    # the 500 held-out images, also multi-connection per file
    import hashlib
    def one(i: int) -> bool:
        dst = ROOT / "val2014" / f"COCO_val2014_{i:012d}.jpg"
        if dst.exists() and dst.stat().st_size > 5000:
            return True
        try:
            req = urllib.request.Request(IMG.format(i))
            with urllib.request.urlopen(req, timeout=60) as r:
                dst.write_bytes(r.read())
            return dst.stat().st_size > 5000
        except Exception:
            return False

    print(f"  fetching {len(held)} images ...", flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=24) as ex:
        got = sum(ex.map(one, held))
    print(f"  images {got}/{len(held)} in {time.time()-t0:.0f} s")

    man = {"purpose": "held-out evaluation pairs of the archived LLaVA sweep, for the canonical DG*/CG recomputation",
           "rule": f"annotation-file order; training=first {TRAIN}, held-out=next {EVAL}, ids kept={TOTAL}",
           "n_held_out": len(held), "images_ok": got,
           "ids_sha256": hashlib.sha256(("\n".join(str(i) for i in held)).encode()).hexdigest(),
           "annotation_sha256": hashlib.sha256(ap.read_bytes()).hexdigest()}
    (ROOT / "MANIFEST.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    print("  ids sha256:", man["ids_sha256"][:16], "| ann sha256:", man["annotation_sha256"][:16])
    zpath.unlink(missing_ok=True)          # 472 MB no longer needed once trimmed
    print("FIXTURE_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
