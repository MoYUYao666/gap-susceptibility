
import os, json, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
os.chdir("/root/autodl-tmp/work")
M = "https://hf-mirror.com/Qwen/Qwen2-VL-7B-Instruct/resolve/main"
DST = "models/qwen2vl7b"
PAR = 8

idx = json.load(open(os.path.join(DST, "model.safetensors.index.json")))
shards = sorted(set(idx["weight_map"].values()))

def total_len(url):
    r = subprocess.run(["curl", "-sL", "-I", "--max-time", "40", url],
                       capture_output=True, text=True)
    for ln in (r.stdout or "").splitlines():
        if ln.lower().startswith("content-length:"):
            try: return int(ln.split(":")[1].strip())
            except Exception: pass
    return 0

print("=== per-shard segment progress ===")
todo = []
for sh in shards:
    dst = os.path.join(DST, sh)
    if os.path.exists(dst) and os.path.getsize(dst) > 100e6:
        print("  ✅ %s complete %d B" % (sh, os.path.getsize(dst)))
        continue
    url = "%s/%s" % (M, sh)
    tot = total_len(url)
    parts = []
    for i in range(PAR):
        p = "%s.tmp.p%d" % (dst, i)
        parts.append(os.path.getsize(p) if os.path.exists(p) else 0)
    chunk = tot // PAR + 1 if tot else 0
    have = sum(parts)
    print("  %s total=%d have=%d (%.1f%%) parts=%s"
          % (sh, tot, have, 100.0*have/max(tot,1), parts))
    if tot and have < tot * 0.999:
        todo.append((sh, url, tot, chunk, parts))

print("\n=== to fetch: %d shard ===" % len(todo))
if "--fix" in sys.argv and todo:
    def fetch(sh, url, tot, chunk, i):
        a = i * chunk
        b = min(a + chunk - 1, tot - 1)
        if a >= tot: return
        p = "%s.tmp.p%d" % (os.path.join(DST, sh), i)
        cur = os.path.getsize(p) if os.path.exists(p) else 0
        need = b - a + 1 - cur
        if need <= 0: return
        # resume this segment (-C - needs to start from an offset → re-downloading the exact range with -r is simpler)
        subprocess.run(["curl", "-sL", "--retry", "8", "--retry-delay", "2",
                        "--max-time", "7200", "-r", "%d-%d" % (a, b), "-o", p, url],
                       capture_output=True)
    jobs = []
    for sh, url, tot, chunk, parts in todo:
        for i in range(PAR):
            a = i * chunk
            if a >= tot: break
            b = min(a + chunk - 1, tot - 1)
            got = parts[i] if i < len(parts) else 0
            if got < (b - a + 1) * 0.999:
                jobs.append((sh, url, tot, chunk, i))
    print("  re-requesting %d segments" % len(jobs))
    with ThreadPoolExecutor(max_workers=min(40, len(jobs) or 1)) as ex:
        list(ex.map(lambda t: fetch(*t), jobs))
    print("  segment fill complete")

    # merge
    for sh, url, tot, chunk, parts in todo:
        dst = os.path.join(DST, sh)
        tmp = dst + ".tmp"
        with open(tmp, "wb") as out:
            for i in range(PAR):
                p = "%s.p%d" % (tmp, i)
                if os.path.exists(p):
                    with open(p, "rb") as fp:
                        while True:
                            b = fp.read(8 << 20)
                            if not b: break
                            out.write(b)
                    os.remove(p)
        got = os.path.getsize(tmp)
        if got >= tot * 0.999:
            os.replace(tmp, dst)
            print("  ✅ merged %s %d/%d" % (sh, got, tot))
        else:
            print("  ⚠️ %s %d/%d insufficient" % (sh, got, tot))
