import io, os, shutil, sys
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HOME"] = os.path.abspath("local_runs/hf")
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
from huggingface_hub import hf_hub_download
p = hf_hub_download("nlphuji/flickr30k", "flickr30k-images.zip", repo_type="dataset")
print("downloaded:", p, os.path.getsize(p) / 2**30, "GB", flush=True)
dst = os.path.abspath("local_runs/real/flickr30k-images.zip")
os.makedirs(os.path.dirname(dst), exist_ok=True)
shutil.copy2(p, dst)
print("copied to", dst, os.path.getsize(dst) / 2**30, "GB", flush=True)
