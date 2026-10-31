# -*- coding: utf-8 -*-
r"""Download the ModelScope weights with many connections, because one connection is throttled.

Measured on this host (2026-10-16): a single ModelScope connection gives ~1 MB/s while the link carries at
least 7 MB/s (1,887 KB/s from the running download plus 5,333 KB/s from 16 extra range requests), and tuna --
same host, same link -- reaches 4.6 MB/s. So the limit is per-connection, and the fix is to use many.

`aria2c` is not installable here (the container's apt has no such package), so the splitter is thirty lines of
Python: each file is cut into fixed-size ranges, the ranges are fetched with a thread pool, and each range is
written to its own part file so an interrupted run resumes rather than restarting. Progress is printed as a
rate, and the assembled file's size is checked against the registry's advertised size.

    python tools/_p1083_parallel_fetch.py --repo llava-hf/llava-1.5-7b-hf --dest /root/autodl-tmp/modelscope/hub/llava-hf/llava-1.5-7b-hf
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

CHUNK = 8 * 1024 * 1024          # 8 MiB per request
WORKERS = 32
RETRIES = 4

_lock = threading.Lock()
_done = {"bytes": 0, "chunks": 0, "failed": 0}


def fetch_range(url: str, start: int, end: int, dst: Path) -> bool:
    """Fetch [start, end] into dst, retrying a few times."""
    if dst.exists() and dst.stat().st_size == (end - start + 1):
        with _lock:
            _done["bytes"] += dst.stat().st_size
            _done["chunks"] += 1
        return True
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
            if len(data) != (end - start + 1):
                raise IOError(f"short read {len(data)} != {end - start + 1}")
            dst.write_bytes(data)
            with _lock:
                _done["bytes"] += len(data)
                _done["chunks"] += 1
            return True
        except Exception:
            if attempt == RETRIES - 1:
                with _lock:
                    _done["failed"] += 1
                return False
            time.sleep(1.5 * (attempt + 1))
    return False


def download(url: str, dst: Path, size: int) -> bool:
    parts = dst.parent / (dst.name + ".parts")
    parts.mkdir(parents=True, exist_ok=True)
    ranges = [(s, min(s + CHUNK - 1, size - 1)) for s in range(0, size, CHUNK)]
    print(f"  {dst.name}: {size / 1e9:.2f} GB in {len(ranges)} chunks", flush=True)

    t0 = time.time()
    stop = threading.Event()

    def reporter() -> None:
        last = 0
        while not stop.wait(15):
            with _lock:
                b, c, f = _done["bytes"], _done["chunks"], _done["failed"]
            dt = time.time() - t0
            print(f"    {b / 1e9:.2f}/{size / 1e9:.2f} GB  {c}/{len(ranges)} chunks  "
                  f"{(b - last) / 15 / 1e6:.1f} MB/s  failed={f}", flush=True)
            last = b

    th = threading.Thread(target=reporter, daemon=True)
    th.start()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = [ex.submit(fetch_range, url, s, e, parts / f"{s:012d}.part") for s, e in ranges]
        ok = all(f.result() for f in futures)
    stop.set()

    if not ok:
        print(f"  {dst.name}: some chunks failed; parts kept for a resume", flush=True)
        return False

    # assemble in order, verify the size, then drop the parts
    with open(dst, "wb") as out:
        for s, _e in ranges:
            out.write((parts / f"{s:012d}.part").read_bytes())
    got = dst.stat().st_size
    if got != size:
        print(f"  {dst.name}: size mismatch {got} != {size}", flush=True)
        return False
    for s, _e in ranges:
        (parts / f"{s:012d}.part").unlink(missing_ok=True)
    parts.rmdir()
    dt = time.time() - t0
    print(f"  {dst.name}: OK {got / 1e9:.2f} GB in {dt:.0f} s ({got / 1e6 / dt:.1f} MB/s)", flush=True)
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="llava-hf/llava-1.5-7b-hf")
    ap.add_argument("--revision", default="master")
    ap.add_argument("--dest", required=True)
    ap.add_argument("--min-size", type=int, default=1_000_000)
    a = ap.parse_args()

    from modelscope.hub.api import HubApi
    dest = Path(a.dest)
    dest.mkdir(parents=True, exist_ok=True)

    files = HubApi().get_model_files(a.repo, recursive=True)
    big = [(f["Path"], f.get("Size") or 0) for f in files if (f.get("Size") or 0) >= a.min_size]
    small = [(f["Path"], f.get("Size") or 0) for f in files if 0 < (f.get("Size") or 0) < a.min_size]
    print(f"  {len(big)} large files, {len(small)} small files")

    failed = []
    for path, size in big:
        url = f"https://modelscope.cn/models/{a.repo}/resolve/{a.revision}/{path}"
        if not download(url, dest / os.path.basename(path), size):
            failed.append(path)

    # small files: one connection is fine for these
    for path, size in small:
        out = dest / os.path.basename(path)
        if out.exists() and out.stat().st_size == size:
            continue
        url = f"https://modelscope.cn/models/{a.repo}/resolve/{a.revision}/{path}"
        try:
            urllib.request.urlretrieve(url, out)
            print(f"  {out.name}: {out.stat().st_size} bytes")
        except Exception as exc:
            print(f"  {out.name}: FAILED {type(exc).__name__}")
            failed.append(path)

    print("\n  failed:", failed if failed else "none")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
