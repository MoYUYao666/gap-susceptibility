
import os, json, glob, subprocess
W = "/root/autodl-tmp/work"
os.chdir(W)

print("=== ① 各模型 config 核对（确认加载的是哪个模型）===")
for d in ("models/clip-vit-base-patch32", "models/clip-vit-base-patch16", "models/openclip"):
    p = os.path.join(d, "config.json")
    if not os.path.exists(p):
        print("  %-34s 无 config.json" % d); continue
    c = json.load(open(p))
    v = c.get("vision_config", {})
    t = c.get("text_config", {})
    print("  %-34s patch=%s vision_hidden=%s layers=%s ｜ text_hidden=%s ｜ arch=%s"
          % (d, v.get("patch_size"), v.get("hidden_size"), v.get("num_hidden_layers"),
             t.get("hidden_size"), c.get("architectures")))

print("\n=== ② 权重实际加载（比对首层权重的统计量）===")
import torch
from transformers import CLIPModel
for d in ("models/clip-vit-base-patch32", "models/clip-vit-base-patch16", "models/openclip"):
    try:
        m = CLIPModel.from_pretrained(d, local_files_only=True)
        vw = m.vision_model.embeddings.patch_embedding.weight
        tw = m.text_model.embeddings.token_embedding.weight
        print("  %-34s patch_embed mean=%+.5f std=%.5f ｜ tok_emb mean=%+.5f std=%.5f"
              % (d, vw.mean().item(), vw.std().item(), tw.mean().item(), tw.std().item()))
    except Exception as e:
        print("  %-34s FAIL %s" % (d, str(e)[:90]))

print("\n=== ③ 数据规模（本地是全部 31783 图 vs 云端只上传 1000 图）===")
n = len(glob.glob("flickr30k/flickr30k-images/*.jpg"))
print("  云端图片数: %d" % n)
print("  → ⚠️ 本地有 31783 张；云端只有 1000 张（前 1000 张）")
print("     max_samples=5000 时，本地能取到 5000 条（1000 图 × 5 标注）")
print("     云端取到的也是 1000 图 × 5 = 5000 条 —— **数量相同**，但")

print("\n=== ④ 关键：text_only 为何接近而 both/vision_only 差很多 ===")
print("  读云端 B/32 三臂的完整 results.json 字段，看 baseline 与 arm 的关系")
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
