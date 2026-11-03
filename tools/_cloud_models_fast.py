
import os, sys, time
WORK = "/root/autodl-tmp/work"
os.chdir(WORK)
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"      # 官方 Rust 加速器
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "60"

TARGETS = [
    ("openai/clip-vit-base-patch32",           "models/clip-vit-base-patch32", 32),
    ("openai/clip-vit-base-patch16",           "models/clip-vit-base-patch16", 16),
    ("laion/CLIP-ViT-B-32-laion2B-s34B-b79K",  "models/openclip",              32),
]
SKIP = ["*.msgpack", "*.h5", "flax_model.*", "tf_model.*", "*.onnx", "*.tar.gz"]

def have(dst):
    if not os.path.isdir(dst):
        return False
    for f in os.listdir(dst):
        if f.endswith((".bin", ".safetensors")) and os.path.getsize(os.path.join(dst, f)) > 100e6:
            return True
    return False

try:
    from modelscope import snapshot_download as ms_dl
except Exception as e:
    print("modelscope unavailable:", str(e)[:80]); ms_dl = None
from huggingface_hub import snapshot_download as hf_dl

for repo, dst, want_patch in TARGETS:
    if have(dst):
        print("SKIP", dst, "(weights exist)"); continue
    t0 = time.time(); ok = False
    # ① ModelScope（国内快）
    if ms_dl:
        for mid in (repo, "AI-ModelScope/" + repo.split("/")[-1],
                    repo.replace("openai/", "AI-ModelScope/"),
                    repo.replace("laion/", "AI-ModelScope/")):
            try:
                print(f"  try ms {mid} ...", flush=True)
                ms_dl(mid, local_dir=dst,
                      ignore_file_pattern=[r".*\.msgpack$", r".*\.h5$",
                                           r"flax_model.*", r"tf_model.*"])
                if have(dst):
                    print(f"OK ms {mid} {time.time()-t0:.0f}s"); ok = True; break
            except Exception as e:
                print("  ms fail", str(e)[:90], flush=True)
    # ② HF 镜像 + hf_transfer
    if not ok:
        try:
            print(f"  try hf(mirror+hf_transfer) {repo} ...", flush=True)
            hf_dl(repo, local_dir=dst, ignore_patterns=SKIP,
                  max_workers=8)
            if have(dst):
                print(f"OK hf {repo} {time.time()-t0:.0f}s"); ok = True
        except Exception as e:
            print("  hf fail", str(e)[:90], flush=True)
    if not ok:
        print("FAILED", repo, flush=True)

# ── 校验 patch size（硬性）──
print("\n=== 校验 ===", flush=True)
import torch
from transformers import CLIPModel
bad = 0
for repo, dst, want in TARGETS:
    try:
        m = CLIPModel.from_pretrained(dst, local_files_only=True)
        got = m.config.vision_config.patch_size
        n = sum(p.numel() for p in m.parameters()) / 1e6
        okk = (got == want)
        bad += (not okk)
        print(f"{dst}: patch={got}(want {want}) params={n:.1f}M {'OK' if okk else 'MISMATCH'}",
              flush=True)
    except Exception as e:
        bad += 1
        print(f"{dst}: LOAD FAIL {str(e)[:90]}", flush=True)
print("VERIFY", "PASS" if bad == 0 else f"FAIL({bad})", flush=True)
