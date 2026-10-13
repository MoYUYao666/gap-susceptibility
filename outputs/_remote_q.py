
import os, glob, json, time
os.chdir("/root/autodl-tmp/work")
def sz(p):
    try: return os.path.getsize(p)
    except Exception: return -1

print("=== 数据包 ===")
z = "_cloud_data.zip"
print(f"  {z}: {sz(z)} B  (期望 145,000,000 左右)")
print(f"  flickr30k 目录: {'存在' if os.path.isdir('flickr30k') else '不存在'}")

print("\n=== 模型权重 ===")
for d, names in (("models/clip-vit-base-patch32", ["pytorch_model.bin", "model.safetensors"]),
                 ("models/clip-vit-base-patch16", ["pytorch_model.bin", "model.safetensors"]),
                 ("models/openclip", ["open_clip_pytorch_model.bin", "open_clip_model.safetensors"])):
    got = []
    for n in names:
        s = sz(os.path.join(d, n))
        if s >= 0: got.append(f"{n}={s}")
    print(f"  {d}: {', '.join(got) if got else '无权重'}")

print("\n=== 下载日志 ===")
try:
    with open("outputs_safe.log") as f:
        for ln in f.read().splitlines()[-8:]:
            print("  " + ln[:110])
except Exception as e:
    print("  (无)", e)

print("\n=== 进程 ===")
import subprocess
r = subprocess.run(["pgrep", "-fa", "curl|wget|_cloud|_p56|strict_freeze"],
                   capture_output=True, text=True)
out = [l for l in (r.stdout or "").splitlines() if "pgrep" not in l]
print("  " + ("\n  ".join(out[:5]) if out else "无"))

print("\n=== 磁盘 ===")
r = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
print("  " + (r.stdout or "").splitlines()[-1])
