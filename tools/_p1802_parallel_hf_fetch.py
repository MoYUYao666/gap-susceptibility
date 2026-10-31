# -*- coding: utf-8 -*-
r"""Download one file with many range connections, for mirrors that throttle each connection.

Why: on 2026-10-28 the model hub mirror answered a single-stream download at 0.04 MB/s while the same link carried much
more when probed with parallel range requests. The fix mirrors `tools/_p1083_parallel_fetch.py` (which is ModelScope
specific): probe the size, cut the file into fixed ranges, fetch the ranges with a thread pool, then assemble the parts
in order. Parts are kept on disk, so an interrupted run resumes instead of restarting.

Usage
  python tools/_p1802_parallel_hf_fetch.py --url <https url> --dest <file> [--workers 16] [--chunk-mb 8]
  python tools/_p1802_parallel_hf_fetch.py --self-test
"""
import argparse
import io
import os
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

UA = "a3-data/1.0"
_lock = threading.Lock()
_done = {"bytes": 0, "parts": 0, "failed": 0}


def probe_size(url):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return int(r.headers.get("Content-Length") or 0)


def fetch_range(url, start, end, dst, retries=4):
    want = end - start + 1
    for attempt in range(retries):
        if dst.exists() and dst.stat().st_size == want:
            with _lock:
                _done["bytes"] += want
                _done["parts"] += 1
            return True
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Range": "bytes=%d-%d" % (start, end)})
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
            if len(data) != want:
                raise IOError("short read: %d of %d" % (len(data), want))
            with io.open(dst, "wb") as f:
                f.write(data)
            with _lock:
                _done["bytes"] += want
                _done["parts"] += 1
            return True
        except Exception:
            time.sleep(2 * (attempt + 1))
    with _lock:
        _done["failed"] += 1
    return False


def fetch(url, dest, workers=16, chunk_mb=8):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    total = probe_size(url)
    if total <= 0:
        raise SystemExit("cannot determine size for %s" % url)
    chunk = chunk_mb * 1024 * 1024
    ranges = [(s, min(s + chunk - 1, total - 1)) for s in range(0, total, chunk)]
    parts_dir = dest.with_suffix(dest.suffix + ".parts")
    parts_dir.mkdir(exist_ok=True)
    print("size %.1f MB, %d ranges, %d workers" % (total / 1e6, len(ranges), workers))
    started = time.time()
    reporter_stop = threading.Event()

    def report():
        while not reporter_stop.wait(10):
            with _lock:
                got, parts, failed = _done["bytes"], _done["parts"], _done["failed"]
            rate = got / max(1e-9, time.time() - started) / 1e6
            print("  %.1f MB, %d/%d parts, %.2f MB/s, failed %d" % (got / 1e6, parts, len(ranges), rate, failed))

    th = threading.Thread(target=report, daemon=True)
    th.start()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(fetch_range, url, s, e, parts_dir / ("%05d.part" % i))
                   for i, (s, e) in enumerate(ranges)]
        ok = all(f.result() for f in futures)
    reporter_stop.set()
    if not ok:
        raise SystemExit("some ranges failed; parts kept at %s, rerun to resume" % parts_dir)
    with io.open(dest, "wb") as out:
        for i in range(len(ranges)):
            with io.open(parts_dir / ("%05d.part" % i), "rb") as f:
                out.write(f.read())
    written = dest.stat().st_size
    if written != total:
        raise SystemExit("assembled %d bytes, expected %d" % (written, total))
    for p in parts_dir.glob("*.part"):
        p.unlink()
    parts_dir.rmdir()
    print("done: %s (%.1f MB in %.0f s)" % (dest, written / 1e6, time.time() - started))
    return dest


def self_test():
    """Round-trip against a local HTTP server that honours Range requests (file:// has no Content-Length)."""
    import http.server
    import tempfile
    import threading as _th

    payload = bytes(range(256)) * 40000  # 10.24 MB deterministic
    tmpdir = tempfile.mkdtemp(prefix="parallel_fetch_selftest_")
    src = os.path.join(tmpdir, "payload.bin")
    with io.open(src, "wb") as f:
        f.write(payload)

    class RangeHandler(http.server.BaseHTTPRequestHandler):
        def do_HEAD(self):
            self.send_response(200)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()

        def do_GET(self):
            rng = self.headers.get("Range", "")
            m = __import__("re").match(r"bytes=(\d+)-(\d+)", rng or "")
            if not m:
                self.send_response(200)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            start, end = int(m.group(1)), int(m.group(2))
            chunk = payload[start:end + 1]
            self.send_response(206)
            self.send_header("Content-Length", str(len(chunk)))
            self.end_headers()
            self.wfile.write(chunk)

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), RangeHandler)
    port = server.server_address[1]
    th = _th.Thread(target=server.serve_forever, daemon=True)
    th.start()
    try:
        url = "http://127.0.0.1:%d/payload.bin" % port
        out = fetch(url, os.path.join(tmpdir, "out.bin"), workers=8, chunk_mb=1)
        ok = io.open(out, "rb").read() == payload
        print("  [%s] http range roundtrip" % ("PASS" if ok else "FAIL"))
        return 0 if ok else 1
    finally:
        server.shutdown()
        for name in os.listdir(tmpdir):
            os.remove(os.path.join(tmpdir, name))
        os.rmdir(tmpdir)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--dest")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--chunk-mb", type=int, default=8)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.url or not args.dest:
        print("provide --url and --dest, or --self-test", file=sys.stderr)
        return 2
    fetch(args.url, args.dest, workers=args.workers, chunk_mb=args.chunk_mb)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
