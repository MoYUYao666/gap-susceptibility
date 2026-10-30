# -*- coding: utf-8 -*-
r"""Replace the synthetic local corpus with the real Flickr30k slice, then rerun the nine SigLIP arms on it.

The local mirror became reachable again (hf-mirror returns 200 through its redirect), so the real image pack can be
fetched. The download uses eight ranged connections with resume; after extraction the synthetic pilot outputs are moved
aside (never deleted) and the same nine-arm protocol runs on the real corpus.

Stages, all logged to local_runs/logs/b1_real.log:
  1. parallel download of flickr30k-images.zip (~4.4 GB) into local_runs/real/
  2. build local_runs/work/flickr30k/ from the real annotations (1000 images, five captions each = 5000 pairs)
  3. archive the synthetic pilot results, then run the smoke and the nine arms
"""
import io
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import zipfile

import requests

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
REAL = os.path.join("local_runs", "real")
LOGS = os.path.join("local_runs", "logs")
WORK = os.path.join("local_runs", "work")
os.makedirs(REAL, exist_ok=True)
os.makedirs(LOGS, exist_ok=True)
LOG = os.path.join(LOGS, "b1_real.log")
ZIP = os.path.join(REAL, "flickr30k-images.zip")
CSV = os.path.join(REAL, "flickr_annotations_30k.csv")
BASE = "https://hf-mirror.com/datasets/nlphuji/flickr30k/resolve/main/"
THREADS = 8


def log(msg):
    line = time.strftime("[%H:%M:%S] ") + msg
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def head_size(url):
    r = requests.head(url, allow_redirects=True, timeout=60)
    return int(r.headers.get("content-length", "0"))


def fetch_csv():
    if os.path.isfile(CSV) and os.path.getsize(CSV) > 10_000_000:
        log("annotations cached")
        return
    r = requests.get(BASE + "flickr_annotations_30k.csv", timeout=600, stream=True)
    with open(CSV, "wb") as fh:
        for chunk in r.iter_content(1 << 20):
            fh.write(chunk)
    log("annotations: %.1f MB" % (os.path.getsize(CSV) / 2 ** 20))


def fetch_zip():
    url = BASE + "flickr30k-images.zip"
    total = head_size(url)
    if not total:
        raise SystemExit("cannot determine size of the image pack")
    if os.path.isfile(ZIP) and os.path.getsize(ZIP) == total:
        log("image pack already complete: %.2f GB" % (total / 2 ** 30))
        return
    log("image pack size %.2f GB, %d ranged connections" % (total / 2 ** 30, THREADS))
    part = total // THREADS
    ranges = []
    for i in range(THREADS):
        start = i * part
        end = (total - 1) if i == THREADS - 1 else (start + part - 1)
        ranges.append((i, start, end))

    lock = threading.Lock()
    done = {"bytes": 0}

    def worker(i, start, end):
        tmp = ZIP + ".part%d" % i
        have = os.path.getsize(tmp) if os.path.isfile(tmp) else 0
        target = end - start + 1
        if have >= target:
            with lock:
                done["bytes"] += target
            return
        headers = {"Range": "bytes=%d-%d" % (start + have, end)}
        with requests.get(BASE + "flickr30k-images.zip", headers=headers, stream=True,
                          timeout=1800) as r:
            r.raise_for_status()
            with open(tmp, "ab") as fh:
                for chunk in r.iter_content(1 << 20):
                    fh.write(chunk)
                    with lock:
                        done["bytes"] += len(chunk)

    threads = [threading.Thread(target=worker, args=rg, daemon=True) for rg in ranges]
    t0 = time.time()
    for t in threads:
        t.start()
    last = 0
    while any(t.is_alive() for t in threads):
        time.sleep(20)
        pct = 100.0 * done["bytes"] / total
        rate = done["bytes"] / max(1e-9, time.time() - t0) / 2 ** 20
        log("download %.1f%% (%.2f GB) at %.1f MB/s" % (pct, done["bytes"] / 2 ** 30, rate))
    for t in threads:
        t.join()
    with open(ZIP, "wb") as out:
        for i, _, _ in ranges:
            tmp = ZIP + ".part%d" % i
            with open(tmp, "rb") as src:
                shutil.copyfileobj(src, out, 1 << 22)
            os.remove(tmp)
    log("assembled image pack: %.2f GB" % (os.path.getsize(ZIP) / 2 ** 30))


def build_corpus():
    import pandas as pd
    root = os.path.join(WORK, "flickr30k")
    img = os.path.join(root, "flickr30k-images")
    js = os.path.join(root, "flickr30k.json")
    if os.path.isfile(js) and os.path.isdir(img) and len(os.listdir(img)) >= 1000:
        first = json.load(io.open(js, encoding="utf-8"))[0]["image"]
        if not first.startswith("synth"):
            log("real corpus already built")
            return
    if os.path.isdir(img):
        shutil.rmtree(img)
    os.makedirs(img, exist_ok=True)
    csv_path = CSV
    if not (os.path.isfile(csv_path) and os.path.getsize(csv_path) > 1_000_000):
        import glob as _glob
        cands = _glob.glob(os.path.join("local_runs", "hf", "hub", "datasets--nlphuji--flickr30k",
                                        "snapshots", "*", "flickr_annotations_30k.csv"))
        if not cands:
            raise SystemExit("annotations missing; run the fetch stage first")
        csv_path = cands[0]
    log("annotations used: %s (%.1f MB)" % (csv_path, os.path.getsize(csv_path) / 2 ** 20))
    df = pd.read_csv(csv_path)
    rows = []
    for fn, raw in zip(df["filename"].tolist(), df["raw"].tolist()):
        raw = str(raw)
        try:
            caps = json.loads(raw) if raw.strip().startswith("[") else [raw]
        except Exception:
            caps = [raw]
        rows.append({"image": str(fn), "captions": [str(c) for c in caps]})
        if len(rows) >= 1000:
            break
    need = {r["image"] for r in rows}
    done = set()
    with zipfile.ZipFile(ZIP) as z:
        for name in z.namelist():
            base = os.path.basename(name)
            if base in need and base not in done:
                with z.open(name) as src, open(os.path.join(img, base), "wb") as dst:
                    dst.write(src.read())
                done.add(base)
    json.dump([r for r in rows if r["image"] in done], io.open(js, "w", encoding="utf-8"), indent=0)
    log("real corpus built: %d images, %d pairs" % (len(done), 5 * len(done)))


def run_arms():
    out = os.path.join(WORK, "outputs", "c_prereg_siglip")
    if os.path.isdir(out):
        arch = os.path.join("local_runs", "synthetic_pilot_results")
        if not os.path.isdir(arch):
            shutil.move(out, arch)
            log("synthetic pilot results archived to %s" % arch)
        else:
            shutil.rmtree(out)
    r = subprocess.run([sys.executable, "tools/_p1771_local_b1_siglip.py"], cwd=REPO)
    log("arm runner exit code %d" % r.returncode)


if __name__ == "__main__":
    skip_download = "--skip-download" in sys.argv
    if not skip_download:
        io.open(LOG, "w", encoding="utf-8").close()
        log("stage 1: annotations + image pack")
        fetch_csv()
        fetch_zip()
    else:
        log("stage 1 skipped: using the file already on disk")
        if not os.path.isfile(ZIP):
            raise SystemExit("image pack missing: %s" % ZIP)
        log("image pack on disk: %.2f GB" % (os.path.getsize(ZIP) / 2 ** 30))
    log("stage 2: corpus")
    build_corpus()
    log("stage 3: nine arms on the real corpus")
    run_arms()
    log("REAL_B1_DONE")
