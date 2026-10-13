
import os, json, glob, subprocess
W = "/root/autodl-tmp/work"
os.chdir(W)

print("=== (1) Config check for each model (confirm which model is loaded) ===")
for d in ("models/clip-vit-base-patch32", "models/clip-vit-base-patch16", "models/openclip"):
    p = os.path.join(d, "config.json")
    if not os.path.exists(p):
        print("  %-34s no config.json" % d); continue
    c = json.load(open(p))
    v = c.get("vision_config", {})
    t = c.get("text_config", {})
    print("  %-34s patch=%s vision_hidden=%s layers=%s | text_hidden=%s | arch=%s"
          % (d, v.get("patch_size"), v.get("hidden_size"), v.get("num_hidden_layers"),
             t.get("hidden_size"), c.get("architectures")))

print("\n=== (2) Actual weight loading (compare first-layer weight statistics)===")
import torch
from transformers import CLIPModel
for d in ("models/clip-vit-base-patch32", "models/clip-vit-base-patch16", "models/openclip"):
    try:
        m = CLIPModel.from_pretrained(d, local_files_only=True)
        vw = m.vision_model.embeddings.patch_embedding.weight
        tw = m.text_model.embeddings.token_embedding.weight
        print("  %-34s patch_embed mean=%+.5f std=%.5f | tok_emb mean=%+.5f std=%.5f"
              % (d, vw.mean().item(), vw.std().item(), tw.mean().item(), tw.std().item()))
    except Exception as e:
        print("  %-34s FAIL %s" % (d, str(e)[:90]))

print("\n=== (3) Data scale (locally all 31783 images vs only 1000 uploaded to the cloud)===")
n = len(glob.glob("flickr30k/flickr30k-images/*.jpg"))
print("  cloud images: %d" % n)
print("  → ⚠️ locally 31783; in the cloud only 1000 (the first 1000)")
print("     with max_samples=5000, locally 5000 items are available (1000 images × 5 captions)")
print("     the cloud also yields 1000 images × 5 = 5000 items — the **counts match**, but")

print("\n=== (4) Key point: why text_only is close while both/vision_only differ a lot ===")
print("  read the full results.json fields of the cloud B/32 three arms; examine how baseline and arm relate")
for arm in ("text_only", "both", "vision_only"):
    f = "outputs/strict_freeze_b32_r4/%s/seed123/results.json" % arm
    if not os.path.exists(f):
        continue
    d = json.load(open(f))
    print("  --- %s" % arm)
    for k in ("initial_gap", "final_gap", "frozen_baseline"):
        if k in d:
            print("      %-16s %s" % (k, json.dumps(d[k], ensure_ascii=False)[:150]))
    for k in sorted(d):
        if "r@" in k.lower() or "recall" in k.lower() or "n_trainable" in k:
            print("      %-16s %s" % (k, d[k]))
