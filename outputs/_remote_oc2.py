
import os, time
os.chdir("/root/autodl-tmp/work")
import subprocess, json, urllib.request

M = "https://hf-mirror.com"
REPO_ID = "laion/CLIP-ViT-B-32-laion2B-s34B-b79K"

print("=== listing this repo's files (via the HF API) ===")
try:
    url = f"{M}/api/models/{REPO_ID}"
    with urllib.request.urlopen(url, timeout=30) as r:
        d = json.loads(r.read().decode())
    for s in d.get("siblings", []):
        print("   ", s.get("rfilename"))
except Exception as e:
    print("  API fail:", str(e)[:140])

print("\n=== trying the HF-format weights ===")
dest = "models/openclip"
for f in ("model.safetensors", "pytorch_model.bin"):
    url = f"{M}/{REPO_ID}/resolve/main/{f}"
    hdr = subprocess.run(["curl", "-sL", "-o", "/dev/null", "--max-time", "20",
                          "-w", "%{http_code} %{size_download}", "-r", "0-0", url],
                         capture_output=True, text=True)
    print(f"  {f}: {hdr.stdout.strip()}")
