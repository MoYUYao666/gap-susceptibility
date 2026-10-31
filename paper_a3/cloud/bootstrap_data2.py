# -*- coding: utf-8 -*-
r"""Download the RSICD and NWPU-Captions parquet shards with plain HTTP and convert them (cloud machine).

The model-hub client refuses these dataset repos on the mirror in some sessions (404 on the API path), while the
resolve URLs work; this script therefore downloads the exact resolve URLs that were recorded in the local data manifest,
then calls the same converters as the local build. The parquet files are deleted after conversion to save disk.

Usage
  python bootstrap_data2.py
"""
import io
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
BASE = "https://hf-mirror.com/datasets"
PY = sys.executable
UA = "a3-cloud/1.0"

FILES = {
    "rsicd": [("%s/arampacha/rsicd/resolve/main/data/train-00000-of-00001.parquet" % BASE, "train.parquet"),
              ("%s/arampacha/rsicd/resolve/main/data/valid-00000-of-00001.parquet" % BASE, "valid.parquet"),
              ("%s/arampacha/rsicd/resolve/main/data/test-00000-of-00001.parquet" % BASE, "test.parquet")],
    "nwpu_captions": [("%s/caglarmert/NWPU-captions/resolve/main/data/train-00000-of-00002.parquet" % BASE, "train0.parquet"),
                      ("%s/caglarmert/NWPU-captions/resolve/main/data/train-00001-of-00002.parquet" % BASE, "train1.parquet"),
                      ("%s/caglarmert/NWPU-captions/resolve/main/data/validation-00000-of-00001.parquet" % BASE, "valid.parquet"),
                      ("%s/caglarmert/NWPU-captions/resolve/main/data/test-00000-of-00001.parquet" % BASE, "test.parquet")],
}


def fetch(url, out, retries=4):
    for attempt in range(retries):
        try:
            t0 = time.time()
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=600) as r, io.open(out, "wb") as f:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
            print("fetched %-60s %.1f MB in %.0f s" % (os.path.basename(out), os.path.getsize(out) / 1e6,
                                                       time.time() - t0), flush=True)
            return
        except Exception as e:
            print("retry %d for %s: %s" % (attempt + 1, url, str(e)[:80]), flush=True)
            time.sleep(5 * (attempt + 1))
    raise SystemExit("failed to fetch " + url)


def main():
    for dataset, files in FILES.items():
        target = os.path.join(DATA, dataset)
        os.makedirs(target, exist_ok=True)
        for url, name in files:
            out = os.path.join(target, name)
            if os.path.exists(out) and os.path.getsize(out) > 1e6:
                print("have", out)
                continue
            fetch(url, out)
    print("== converting RSICD")
    subprocess.run([PY, os.path.join(ROOT, "scripts", "convert_rsicd.py"),
                    "--data-root", os.path.join(DATA, "rsicd"), "--out", os.path.join(DATA, "rsicd.jsonl")],
                   check=True, cwd=ROOT)
    print("== converting NWPU-Captions")
    subprocess.run([PY, os.path.join(ROOT, "scripts", "convert_nwpu.py"),
                    "--data-root", os.path.join(DATA, "nwpu_captions"),
                    "--out", os.path.join(DATA, "nwpu_captions.jsonl")], check=True, cwd=ROOT)
    # parquet no longer needed
    for dataset in FILES:
        for _, name in FILES[dataset]:
            p = os.path.join(DATA, dataset, name)
            if os.path.exists(p):
                os.remove(p)
    print("data ready; parquet removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
