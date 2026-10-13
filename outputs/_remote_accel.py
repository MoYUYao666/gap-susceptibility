
import os, sys, subprocess, time, json
os.chdir("/root/autodl-tmp/work")

def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return (r.stdout or "") + (r.stderr or "")

print("=== 1. Current state ===")
print("  huggingface_hub:", sh("/root/miniconda3/bin/pip show huggingface_hub 2>/dev/null | head -2").strip())
for pkg in ("hf_xet", "hf_transfer"):
    out = sh("/root/miniconda3/bin/pip show %s 2>/dev/null | head -2" % pkg).strip()
    print("  %-12s: %s" % (pkg, out if out else "not installed"))

print("\n=== 2. Install hf_xet (Xet backend, the officially recommended acceleration) ===")
print(sh("/root/miniconda3/bin/pip install -q hf_xet 2>&1 | tail -3").strip())
print("  after install:", sh("/root/miniconda3/bin/pip show hf_xet 2>/dev/null | head -2").strip())

print("\n=== 3. Measurement: speed of hf_xet downloading one shard ===")
env = dict(os.environ)
env.pop("HF_HUB_DISABLE_XET", None)        # **key: xet is no longer disabled**
env["HF_ENDPOINT"] = "https://hf-mirror.com"
env["HF_HUB_ENABLE_HF_TRANSFER"] = "1"     # if older versions still honor this
env["HF_HOME"] = "/root/autodl-tmp/work/.hf"

code = r"""
import os, time, sys
from huggingface_hub import hf_hub_download
for repo, fn in [("Qwen/Qwen2-VL-7B-Instruct", "model-00002-of-00005.safetensors")]:
    t0 = time.time()
    try:
        p = hf_hub_download(repo_id=repo, filename=fn,
                            local_dir="models/qwen2vl7b", resume_download=True)
        dt = time.time() - t0
        sz = os.path.getsize(p)
        print("  %s: %.0f MB in %.0fs → %.2f MB/s" % (fn, sz/1e6, dt, sz/1e6/dt))
    except Exception as e:
        print("  FAIL", str(e)[:200])
"""
open("/root/autodl-tmp/work/_xet_test.py", "w").write(code)
r = subprocess.run(["/root/miniconda3/bin/python", "/root/autodl-tmp/work/_xet_test.py"],
                   capture_output=True, text=True, env=env, timeout=1800)
print((r.stdout or "")[-800:])
if r.stderr:
    print("  stderr:", r.stderr[-300:])
