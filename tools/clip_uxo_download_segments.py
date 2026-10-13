"""Parallel segmented resumable download of Zenodo recordings.7z (supports Range: 206).
Usage: python clip_uxo_download_segments.py
Before concatenation the current file must be a complete [0, S0) prefix (guaranteed by the prior resumable download).
"""
import os, sys, subprocess, concurrent.futures

URL = ('https://zenodo.org/records/13778485/files/'
       'data_export_recordings.7z?download=1')
TOTAL = 16658054765
OUT = 'data/ctx_uxo/recordings.7z'
K = 10

s0 = os.path.getsize(OUT)
assert s0 < TOTAL, 'already complete?'
rem = TOTAL - s0
seglen = (rem + K - 1) // K
segs = [(s0 + i * seglen, min(s0 + (i + 1) * seglen - 1, TOTAL - 1)) for i in range(K)]
print('current=%d remaining=%d segments=%d (len=%d)' % (s0, rem, K, seglen), flush=True)


def fetch(seg):
    lo, hi = seg
    part = '%s.part%d' % (OUT, seg[0])
    for attempt in range(8):
        r = subprocess.run(
            ['curl.exe', '-sS', '-L', '--retry', '3', '--retry-delay', '3',
             '-r', '%d-%d' % (lo, hi), '-o', part, URL],
            capture_output=True, text=True)
        if r.returncode == 0 and os.path.getsize(part) == hi - lo + 1:
            return seg, True, None
        if attempt == 7:
            return seg, False, r.stderr[-120:]
    return seg, False, 'unreachable'


with concurrent.futures.ThreadPoolExecutor(max_workers=K) as ex:
    futs = {ex.submit(fetch, s): s for s in segs}
    for fu in concurrent.futures.as_completed(futs):
        seg, ok, err = fu.result()
        print('seg %d-%d: %s %s' % (seg[0], seg[1], 'OK' if ok else 'FAIL', err or ''), flush=True)
        if not ok:
            sys.exit(1)

# concatenate in order
with open(OUT, 'ab') as f:
    for seg in segs:
        part = '%s.part%d' % (OUT, seg[0])
        with open(part, 'rb') as p:
            while True:
                b = p.read(1 << 20)
                if not b:
                    break
                f.write(b)
        os.remove(part)
sz = os.path.getsize(OUT)
print('assembled size=%d expected=%d %s' % (sz, TOTAL, 'OK' if sz == TOTAL else 'MISMATCH!'),
      flush=True)
sys.exit(0 if sz == TOTAL else 2)
