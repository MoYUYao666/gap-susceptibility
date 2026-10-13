
import os, subprocess, sys, time, json, math
from concurrent.futures import ThreadPoolExecutor
os.chdir("/root/autodl-tmp/work")

M = "https://hf-mirror.com/Qwen/Qwen2-VL-7B-Instruct/resolve/main"
DST = "models/qwen2vl7b"
os.makedirs(DST, exist_ok=True)

def log(m):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), m)
    print(line, flush=True)
    with open("outputs_7b.log", "a") as f:
        f.write(line + "\n")

def head_len(url):
    """True length: GET first byte + size_download (follows redirects)"""
    r = subprocess.run(["curl", "-sL", "-o", "/dev/null", "--max-time", "40",
                        "-w", "%{size_download}", "-r", "0-0", url],
                       capture_output=True, text=True)
    try:
        return int((r.stdout or "0").strip())
    except Exception:
        return 0

def seg(url, a, b, out):
    subprocess.run(["curl", "-sL", "--retry", "6", "--retry-delay", "2",
                    "--max-time", "5400", "-r", "%d-%d" % (a, b), "-o", out, url],
                   capture_output=True)

def dl_shard(shard, par=8):
    url = "%s/%s" % (M, shard)
    dst = os.path.join(DST, shard)
    if os.path.exists(dst) and os.path.getsize(dst) > 100e6:
        log("SKIP %s (%d B)" % (shard, os.path.getsize(dst)))
        return dst
    # HEAD is unreliable for the length (returns a redirect page), so take the size declared in the index first
    try:
        idx = json.load(open(os.path.join(DST, "model.safetensors.index.json")))
        # the index has no size, so use curl -I with redirects instead
    except Exception:
        pass
    r = subprocess.run(["curl", "-sL", "-o", "/dev/null", "--max-time", "40",
                        "-w", "%{size_download}", "-r", "0-0", url],
                       capture_output=True, text=True)
    total = 0
    # use --head with redirects to get Content-Length (here -L follows to the CDN and returns the true length)
    r2 = subprocess.run(["curl", "-sL", "-I", "--max-time", "40", url],
                        capture_output=True, text=True)
    for ln in (r2.stdout or "").splitlines():
        if ln.lower().startswith("content-length:"):
            try:
                total = int(ln.split(":")[1].strip())
            except Exception:
                pass
    if total < 100e6:
        log("  %s: no length available (%d) → single-connection retry" % (shard, total))
        subprocess.run(["curl", "-sL", "--retry", "8", "-C", "-", "-o", dst, url],
                       capture_output=True)
        log("  %s → %d B" % (shard, os.path.getsize(dst) if os.path.exists(dst) else 0))
        return dst

    tmp = dst + ".tmp"
    chunk = total // par + 1
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=par) as ex:
        futs = []
        for i in range(par):
            a = i * chunk
            b = min(a + chunk - 1, total - 1)
            if a >= total:
                break
            futs.append(ex.submit(seg, url, a, b, "%s.p%d" % (tmp, i)))
        for f in futs:
            f.result()
    # merge in order
    with open(tmp, "wb") as out:
        for i in range(par):
            p = "%s.p%d" % (tmp, i)
            if os.path.exists(p):
                with open(p, "rb") as fp:
                    while True:
                        buf = fp.read(8 << 20)
                        if not buf:
                            break
                        out.write(buf)
                os.remove(p)
    got = os.path.getsize(tmp) if os.path.exists(tmp) else 0
    dt = time.time() - t0
    if got >= total * 0.999:
        os.replace(tmp, dst)
        log("  ✅ %s %d/%d in %.0fs (%.2f MB/s)" % (shard, got, total, dt, got/1e6/max(dt,1)))
    else:
        log("  ⚠️ %s %d/%d short of target, keeping .tmp" % (shard, got, total))
    return dst

log("=" * 60)
log("parallel download of 7B (5 shards at once, 8 segments per shard)")

# small files
for f in ("config.json", "preprocessor_config.json", "tokenizer.json",
          "tokenizer_config.json", "vocab.json", "merges.txt",
          "generation_config.json", "model.safetensors.index.json"):
    p = os.path.join(DST, f)
    if not os.path.exists(p) or os.path.getsize(p) < 50:
        subprocess.run(["curl", "-sL", "--max-time", "180", "-o", p, "%s/%s" % (M, f)],
                       capture_output=True)

try:
    idx = json.load(open(os.path.join(DST, "model.safetensors.index.json")))
    shards = sorted(set(idx["weight_map"].values()))
except Exception as e:
    log("❌ index read failed: %s" % str(e)[:120]); sys.exit(1)
log("shards: %s" % shards)

t_all = time.time()
with ThreadPoolExecutor(max_workers=len(shards)) as ex:
    list(ex.map(dl_shard, shards))
log("all done in %.0f min" % ((time.time()-t_all)/60))

# verify
big = [f for f in os.listdir(DST) if f.endswith(".safetensors")
       and os.path.getsize(os.path.join(DST, f)) > 100e6]
log("complete shards: %d / %d | total %.1f GB"
    % (len(big), len(shards), sum(os.path.getsize(os.path.join(DST, f)) for f in big)/1e9))
log("SEVENBDONE")
