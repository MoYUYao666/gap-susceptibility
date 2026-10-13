
import os, glob, json, time
os.chdir("/root/autodl-tmp/work")
def sz(p):
    try: return os.path.getsize(p)
    except Exception: return -1

print("=== Data bundle ===")
z = "_cloud_data.zip"
print(f"  {z}: {sz(z)} B  (expect ~145,000,000)")
print(f"  flickr30k dir: {'present' if os.path.isdir('flickr30k') else 'absent'}")

print("\n=== Model weights ===")
for d, names in (("models/clip-vit-base-patch32", ["pytorch_model.bin", "model.safetensors"]),
                 ("models/clip-vit-base-patch16", ["pytorch_model.bin", "model.safetensors"]),
                 ("models/openclip", ["open_clip_pytorch_model.bin", "open_clip_model.safetensors"])):
    got = []
    for n in names:
        s = sz(os.path.join(d, n))
        if s >= 0: got.append(f"{n}={s}")
    print(f"  {d}: {', '.join(got) if got else 'no weights'}")

print("\n=== Download log ===")
try:
    with open("outputs_safe.log") as f:
        for ln in f.read().splitlines()[-8:]:
            print("  " + ln[:110])
except Exception as e:
    print("  (none)", e)

print("\n=== Processes ===")
import subprocess
r = subprocess.run(["pgrep", "-fa", "curl|wget|_cloud|_p56|strict_freeze"],
                   capture_output=True, text=True)
out = [l for l in (r.stdout or "").splitlines() if "pgrep" not in l]
print("  " + ("\n  ".join(out[:5]) if out else "none"))

print("\n=== Disk ===")
r = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
print("  " + (r.stdout or "").splitlines()[-1])
