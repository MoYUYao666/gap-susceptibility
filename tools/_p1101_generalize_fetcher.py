# -*- coding: utf-8 -*-
r"""Generalise the multi-connection fetcher so it can serve the mirror as well as ModelScope.

Measured on the 2026-10-17 host: the mirror answers a range request at about **1.6 KB/s single-connection**
while **16 parallel connections reach 6.5 MB/s**. The existing fetcher (`_p1083`) is hard-wired to ModelScope's
URL shape, so this version takes a base URL template and a file list and works for either registry.

Usage on the host:
  python _p1101_parallel_fetch_any.py --base "https://hf-mirror.com/llava-hf/llava-1.5-7b-hf/resolve/main/{f}" \
      --files model-00001-of-00003.safetensors,model-00002-of-00003.safetensors,model-00003-of-00003.safetensors \
      --sizes 4992930200,4957878440,4176137408 --dest /root/autodl-tmp/hf/hub/models--llava-hf--llava-1.5-7b-hf

    python tools/_p1101_generalize_fetcher.py [--apply]   (writes the script into tools/)
"""
from __future__ import annotations

import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "tools" / "_p1101_parallel_fetch_any.py"

BODY = r'''# -*- coding: utf-8 -*-
r"""Multi-connection range fetcher for any registry that serves plain files over HTTP with Range support.

Single connections to both hf-mirror.com and modelscope.cn measured ~1-2 KB/s on the 2026-10-17 host, while
16-32 parallel range requests reached 6.5 and 13-18 MB/s respectively. This splits each file into ranges,
fetches them concurrently, and keeps per-range part files so an interrupted run resumes.

    python _p1101_parallel_fetch_any.py --base "<url with {f}>" --files a,b,c --sizes 1,2,3 --dest <dir>
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CHUNK = 8 * 1024 * 1024
WORKERS = 32
RETRIES = 4

_lock = threading.Lock()
_done = {"b": 0, "c": 0, "f": 0}


def head_size(url: str) -> int:
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=30) as r:
        return int(r.headers.get("Content-Length") or 0)


def grab(url: str, s: int, e: int, dst: Path) -> bool:
    if dst.exists() and dst.stat().st_size == e - s + 1:
        with _lock:
            _done["b"] += dst.stat().st_size
            _done["c"] += 1
        return True
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={"Range": f"bytes={s}-{e}"})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            if len(data) != e - s + 1:
                raise IOError(f"short read {len(data)} != {e - s + 1}")
            dst.write_bytes(data)
            with _lock:
                _done["b"] += len(data)
                _done["c"] += 1
            return True
        except Exception:
            if attempt == RETRIES - 1:
                with _lock:
                    _done["f"] += 1
                return False
            time.sleep(1.5 * (attempt + 1))
    return False


def fetch(url: str, dst: Path, size: int) -> bool:
    parts = dst.parent / (dst.name + ".parts")
    parts.mkdir(parents=True, exist_ok=True)
    ranges = [(s, min(s + CHUNK - 1, size - 1)) for s in range(0, size, CHUNK)]
    print(f"  {dst.name}: {size/1e9:.2f} GB, {len(ranges)} chunks", flush=True)
    t0 = time.time()
    stop = threading.Event()

    def report() -> None:
        last = 0
        while not stop.wait(15):
            with _lock:
                b, c, f = _done["b"], _done["c"], _done["f"]
            print(f"    {b/1e9:.2f}/{size/1e9:.2f} GB  {c}/{len(ranges)}  "
                  f"{(b-last)/15/1e6:.1f} MB/s  failed={f}", flush=True)
            last = b

    th = threading.Thread(target=report, daemon=True)
    th.start()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        ok = all(fu.result() for fu in
                 [ex.submit(grab, url, s, e, parts / f"{s:012d}.part") for s, e in ranges])
    stop.set()
    if not ok:
        print(f"  {dst.name}: chunks failed; parts kept for resume", flush=True)
        return False
    with open(dst, "wb") as out:
        for s, _e in ranges:
            out.write((parts / f"{s:012d}.part").read_bytes())
    got = dst.stat().st_size
    if got != size:
        print(f"  {dst.name}: size {got} != {size}", flush=True)
        return False
    for s, _e in ranges:
        (parts / f"{s:012d}.part").unlink(missing_ok=True)
    try:
        parts.rmdir()
    except OSError:
        pass
    dt = time.time() - t0
    print(f"  {dst.name}: OK {got/1e9:.2f} GB in {dt:.0f} s ({got/1e6/max(dt,1):.1f} MB/s)", flush=True)
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="URL template containing {f}")
    ap.add_argument("--files", required=True, help="comma-separated file names")
    ap.add_argument("--sizes", required=True, help="comma-separated sizes in bytes (0 = ask the server)")
    ap.add_argument("--dest", required=True)
    a = ap.parse_args()

    dest = Path(a.dest)
    dest.mkdir(parents=True, exist_ok=True)
    files = [f for f in a.files.split(",") if f]
    sizes = [int(x) for x in a.sizes.split(",") if x]
    if len(sizes) != len(files):
        print("  sizes and files differ in length", file=sys.stderr)
        return 2

    failed = []
    for f, size in zip(files, sizes):
        url = a.base.format(f=f)
        if not size:
            size = head_size(url)
        if not fetch(url, dest / os.path.basename(f), size):
            failed.append(f)
    print("\n  failed:", failed if failed else "none")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print(f"  would write {TARGET.relative_to(REPO)} ({len(BODY.splitlines())} lines)")
        return 0
    TARGET.write_text(BODY, encoding="utf-8", newline="")
    import ast
    ast.parse(BODY)
    print(f"  wrote {TARGET.relative_to(REPO)}; parses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
