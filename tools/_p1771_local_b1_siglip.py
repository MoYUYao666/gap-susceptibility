# -*- coding: utf-8 -*-
r"""Local run B1: the SigLIP arms on the 8 GB laptop GPU.

Bootstrap once (weights + a 1000-image Flickr30k slice), then a one-arm smoke test, then the nine arms
(3 adaptation sites x 3 seeds) at batch 32, single process. The point of B1 is to find out whether the
attention-mask / sequence-length fixes actually remove the `device-side assert` that killed all fifteen SigLIP arms
on the cloud instances.

Everything lives under `local_runs/` so the manuscript packages stay untouched. Logs go to `local_runs/logs/`.
"""
import glob
import io
import json
import os
import shutil
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
WORK = os.path.join(REPO, "local_runs", "work")
LOGS = os.path.join(REPO, "local_runs", "logs")
PY = sys.executable

os.makedirs(WORK, exist_ok=True)
os.makedirs(LOGS, exist_ok=True)


def log(msg):
    print(time.strftime("[%H:%M:%S] ") + msg, flush=True)


def ensure_code():
    for name in ("src", "experiments"):
        dst = os.path.join(WORK, name)
        if not os.path.isdir(dst):
            shutil.copytree(os.path.join(REPO, name), dst)
            log("copied %s" % name)
    log("code present")


def ensure_weights():
    dest = os.path.join(WORK, "models", "siglip-base-patch16-224")
    if glob.glob(os.path.join(dest, "*.safetensors")) or glob.glob(os.path.join(dest, "*.bin")):
        log("weights present")
        return dest
    os.makedirs(dest, exist_ok=True)
    os.environ.setdefault("MODELSCOPE_CACHE", os.path.join(REPO, "local_runs", "ms"))
    from modelscope.hub.snapshot_download import snapshot_download
    for repo_id in ("AI-ModelScope/siglip-base-patch16-224", "google/siglip-base-patch16-224"):
        try:
            local = snapshot_download(repo_id, cache_dir=os.path.join(REPO, "local_runs", "ms"))
        except Exception as e:
            log("weight source failed: %s (%s)" % (repo_id, str(e)[:80]))
            continue
        n = 0
        for f in glob.glob(os.path.join(local, "*")):
            if os.path.isfile(f):
                shutil.copy2(f, dest)
                n += 1
        log("copied %d files from %s" % (n, repo_id))
        if glob.glob(os.path.join(dest, "*.safetensors")) or glob.glob(os.path.join(dest, "*.bin")):
            return dest
    raise SystemExit("could not obtain siglip weights")


def ensure_corpus():
    root = os.path.join(WORK, "flickr30k")
    img = os.path.join(root, "flickr30k-images")
    js = os.path.join(root, "flickr30k.json")
    if os.path.isfile(js) and os.path.isdir(img) and len(os.listdir(img)) >= 1000:
        log("corpus present")
        return
    os.makedirs(img, exist_ok=True)
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    os.environ.setdefault("HF_HOME", os.path.join(REPO, "local_runs", "hf"))
    from huggingface_hub import hf_hub_download
    import pandas as pd
    import zipfile

    csv = hf_hub_download("nlphuji/flickr30k", "flickr_annotations_30k.csv", repo_type="dataset")
    log("annotations: %s" % csv)
    df = pd.read_csv(csv)
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
    log("annotation rows selected: %d (%d captions)" % (len(rows), sum(len(r["captions"]) for r in rows)))

    zp = hf_hub_download("nlphuji/flickr30k", "flickr30k-images.zip", repo_type="dataset")
    log("images zip: %.1f MB" % (os.path.getsize(zp) / 2 ** 20))
    need = {r["image"] for r in rows}
    done = set()
    with zipfile.ZipFile(zp) as z:
        for name in z.namelist():
            base = os.path.basename(name)
            if base in need and base not in done:
                with z.open(name) as src, open(os.path.join(img, base), "wb") as dst:
                    dst.write(src.read())
                done.add(base)
    json.dump([r for r in rows if r["image"] in done], io.open(js, "w", encoding="utf-8"), indent=0)
    log("corpus built: %d images" % len(done))


def run_arm(model, tag, seed, epochs, samples, batch, name_prefix, out_dir):
    env = dict(os.environ)
    env["HF_HOME"] = os.path.join(REPO, "local_runs", "hf")
    env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    cmd = [PY, "experiments/strict_freeze_control.py", "--model", model, "--out-dir", out_dir,
           "--name", name_prefix, "--rank", "8", "--alpha-mult", "2", "--tags", tag, "--seeds", str(seed),
           "--epochs", str(epochs), "--max-samples", str(samples), "--batch-size", str(batch),
           "--skip-frozen", "--dg-star"]
    logfile = os.path.join(LOGS, "%s_%s_%s.log" % (name_prefix.strip("_"), tag, seed))
    with io.open(logfile, "w", encoding="utf-8") as fh:
        r = subprocess.run(cmd, cwd=WORK, stdout=fh, stderr=subprocess.STDOUT, env=env)
    return r.returncode, logfile


def main():
    ensure_code()
    model = ensure_weights()
    ensure_corpus()
    model_rel = os.path.relpath(model, WORK)
    log("model dir: %s" % model_rel)

    log("smoke (1 epoch, 200 samples, batch 16)")
    rc, lf = run_arm(model_rel, "both", 42, 1, 200, 16, "smoke_", "outputs/_local_smoke")
    text = io.open(lf, encoding="utf-8", errors="replace").read()
    if rc != 0 or "device-side assert" in text or "Traceback" in text:
        log("SMOKE FAILED rc=%d" % rc)
        for key in ("device-side assert", "Error", "Traceback"):
            for ln in text.splitlines():
                if key in ln:
                    log("  " + ln.strip()[:180])
                    break
        raise SystemExit(1)
    log("smoke passed - the mask/sequence-length fixes work")

    log("nine arms: 3 sites x 3 seeds, batch 32, 10 epochs, 5000 samples")
    results = []
    for tag in ("text_only", "both", "vision_only"):
        for seed in (42, 123, 456):
            t0 = time.time()
            rc, lf = run_arm(model_rel, tag, seed, 10, 5000, 32, "siglip_", "outputs/c_prereg_siglip")
            ok = rc == 0
            results.append({"tag": tag, "seed": seed, "rc": rc, "minutes": round((time.time() - t0) / 60, 1), "log": lf})
            log("arm %s/%s rc=%d in %.1f min" % (tag, seed, rc, results[-1]["minutes"]))
    json.dump(results, io.open(os.path.join(LOGS, "b1_arms.json"), "w", encoding="utf-8"), indent=2)
    found = glob.glob(os.path.join(WORK, "outputs", "c_prereg_siglip", "**", "results.json"), recursive=True)
    log("results.json produced: %d" % len(found))
    log("B1_DONE")


if __name__ == "__main__":
    main()
