
import os, json, glob
os.chdir("/root/autodl-tmp/work")

def sf_info(p):
    """Read the safetensors header, returning (n_tensors, first few keys, whether HF style)"""
    try:
        with open(p, "rb") as f:
            n = int.from_bytes(f.read(8), "little")
            if not (0 < n < 50_000_000):
                return None
            meta = json.loads(f.read(n).decode("utf-8"))
        keys = [k for k in meta if k != "__metadata__"]
        hf = any(k.startswith(("vision_model.", "text_model.")) for k in keys)
        return len(keys), keys[:3], hf
    except Exception as e:
        return f"ERR {str(e)[:60]}"

def bin_info(p):
    """Try the key names via torch.load (read the header only, use mmap to save memory)"""
    try:
        import torch
        try:
            sd = torch.load(p, map_location="cpu", mmap=True, weights_only=True)
        except TypeError:
            sd = torch.load(p, map_location="cpu", weights_only=True)
        keys = list(sd.keys())
        hf = any(k.startswith(("vision_model.", "text_model.")) for k in keys)
        return len(keys), keys[:3], hf
    except Exception as e:
        return f"ERR {str(e)[:80]}"

print("=== the two large files in the openclip directory ===")
for p in sorted(glob.glob("models/openclip/*")):
    if not os.path.isfile(p): continue
    s = os.path.getsize(p)
    if s < 1e6: 
        continue
    print(f"  {os.path.basename(p)}  {s} B")
    if p.endswith(".safetensors"):
        print(f"    {sf_info(p)}")
    elif p.endswith(".bin"):
        print(f"    {bin_info(p)}")

print("\n=== can openclip be loaded with CLIPModel ===")
try:
    from transformers import CLIPModel
    m = CLIPModel.from_pretrained("models/openclip", local_files_only=True)
    print(f"  ✅ loadable | patch={m.config.vision_config.patch_size} "
          f"params={sum(x.numel() for x in m.parameters())/1e6:.1f}M")
except Exception as e:
    print(f"  ❌ {str(e)[:200]}")

print("\n=== b32 / b16 download status ===")
for d in ("models/clip-vit-base-patch32", "models/clip-vit-base-patch16"):
    fs = sorted(os.listdir(d)) if os.path.isdir(d) else []
    rows = [(f, os.path.getsize(os.path.join(d, f))) for f in fs]
    big = [r for r in rows if r[1] > 1e6]
    tmp = [r for r in rows if r[0].endswith(".tmp")]
    print(f"  {d}: large files={big} | temp={[(t[0], t[1]) for t in tmp]}")

print("\n=== tail of the download log ===")
if os.path.exists("outputs_safe.log"):
    for ln in open("outputs_safe.log").read().splitlines()[-6:]:
        print("  " + ln[:110])
