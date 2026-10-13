
import os
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.makedirs("models", exist_ok=True)
targets = [
    ("openai/clip-vit-base-patch32", "models/clip-vit-base-patch32"),
    ("openai/clip-vit-base-patch16", "models/clip-vit-base-patch16"),
    ("laion/CLIP-ViT-B-32-laion2B-s34B-b79K", "models/openclip"),
]
try:
    from modelscope import snapshot_download as ms_dl
except Exception:
    ms_dl = None
from huggingface_hub import snapshot_download as hf_dl
for repo, dst in targets:
    if os.path.isdir(dst) and os.listdir(dst):
        print("SKIP exists", dst); continue
    ok = False
    if ms_dl:
        for mid in (repo, repo.replace("openai/", "AI-ModelScope/"),
                    "AI-ModelScope/" + repo.split("/")[-1]):
            try:
                ms_dl(mid, local_dir=dst, ignore_file_pattern=[r".*\.msgpack$", r".*\.h5$"])
                print("OK ms", mid, "->", dst); ok = True; break
            except Exception as e:
                print("ms fail", mid, str(e)[:90])
    if not ok:
        try:
            hf_dl(repo, local_dir=dst,
                  ignore_patterns=["*.msgpack", "*.h5", "flax_model.*", "tf_model.*"])
            print("OK hf", repo, "->", dst); ok = True
        except Exception as e:
            print("hf fail", repo, str(e)[:90])
    if not ok:
        print("FAILED", repo)
print("done")
