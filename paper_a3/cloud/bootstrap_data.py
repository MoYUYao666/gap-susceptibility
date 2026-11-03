# -*- coding: utf-8 -*-
r"""Download the two parquet dataset releases and convert them to images + annotation JSONL (cloud machine).

The converters are the same scripts used locally (convert_rsicd.py, convert_nwpu.py), so the cloud data is built by the
same code path and can be checked against the local manifests.

Usage
  python bootstrap_data.py
"""
import os
import subprocess
import sys
import time

from huggingface_hub import hf_hub_download

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
PY = sys.executable

SHARDS = {
    "rsicd": [("arampacha/rsicd", "data/train-00000-of-00001.parquet", "train.parquet"),
              ("arampacha/rsicd", "data/valid-00000-of-00001.parquet", "valid.parquet"),
              ("arampacha/rsicd", "data/test-00000-of-00001.parquet", "test.parquet")],
    "nwpu_captions": [("caglarmert/NWPU-captions", "data/train-00000-of-00002.parquet", "train0.parquet"),
                      ("caglarmert/NWPU-captions", "data/train-00001-of-00002.parquet", "train1.parquet"),
                      ("caglarmert/NWPU-captions", "data/validation-00000-of-00001.parquet", "valid.parquet"),
                      ("caglarmert/NWPU-captions", "data/test-00000-of-00001.parquet", "test.parquet")],
}


def download():
    for dataset, shards in SHARDS.items():
        target = os.path.join(DATA, dataset)
        os.makedirs(target, exist_ok=True)
        for repo, filename, dest in shards:
            out = os.path.join(target, dest)
            if os.path.exists(out) and os.path.getsize(out) > 1e6:
                print("have", out)
                continue
            t0 = time.time()
            path = hf_hub_download(repo_id=repo, filename=filename, cache_dir=os.environ.get("HF_HOME"))
            os.replace(path, out)
            print("fetched %-28s -> %s (%.1f MB, %.0f s)" % (filename, dest, os.path.getsize(out) / 1e6,
                                                             time.time() - t0))


def convert():
    for script, data_root, out in (
            ("convert_rsicd.py", os.path.join(DATA, "rsicd"), os.path.join(DATA, "rsicd.jsonl")),
            ("convert_nwpu.py", os.path.join(DATA, "nwpu_captions"), os.path.join(DATA, "nwpu_captions.jsonl"))):
        print("==", script)
        subprocess.run([PY, os.path.join(ROOT, "scripts", script), "--data-root", data_root, "--out", out],
                       check=True, cwd=ROOT)


def main():
    download()
    convert()
    print("data ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
