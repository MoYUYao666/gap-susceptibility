
import os, glob, zipfile, shutil, time
os.chdir("/root/autodl-tmp/work")

z = "_cloud_data.zip"
print(f"=== zip 校验 ===\n  大小 {os.path.getsize(z)} B")
try:
    with zipfile.ZipFile(z) as zf:
        bad = zf.testzip()
        n = len(zf.namelist())
        print(f"  ✅ 可读，{n} 项，损坏项: {bad}")
        if bad:
            raise SystemExit("zip 损坏")
        # 解压到 flickr30k/
        if os.path.isdir("flickr30k"):
            shutil.rmtree("flickr30k")
        os.makedirs("flickr30k", exist_ok=True)
        zf.extractall("flickr30k")
except Exception as e:
    print(f"  ❌ {str(e)[:150]}")
    raise SystemExit(1)

print("\n=== 解压结果 ===")
print("  flickr30k/:", sorted(os.listdir("flickr30k"))[:6])
img = "flickr30k/flickr30k-images"
csv = "flickr30k/results.csv"
print(f"  {img}: {len(glob.glob(img + '/*.jpg'))} 张")
print(f"  {csv}: {'有 ' + str(os.path.getsize(csv)) + ' B' if os.path.exists(csv) else '无'}")
if os.path.exists("flickr30k/flickr30k.json"):
    print(f"  flickr30k.json: {os.path.getsize('flickr30k/flickr30k.json')} B")

print("\n=== 用真实 loader 验证（须无随机图回退）===")
import sys
sys.path.insert(0, "/root/autodl-tmp/work")
try:
    from src.dataset import create_dataloaders
    tr, va, te = create_dataloaders(dataset_name="flickr30k", data_dir=".",
                                    batch_size=8, max_samples=200)
    b = next(iter(tr))
    print(f"  train/val/test = {len(tr.dataset)}/{len(va.dataset)}/{len(te.dataset)}")
    print(f"  一个批次: image {tuple(b['image'].shape)} ｜ captions {len(b['caption'])}")
    print(f"  例 caption: {str(b['caption'][0])[:80]}")
except Exception as e:
    print(f"  ❌ loader 失败: {str(e)[:200]}")

print("\n=== 模型权重 ===")
for d in ("models/clip-vit-base-patch32", "models/clip-vit-base-patch16", "models/openclip"):
    fs = sorted(f for f in os.listdir(d)) if os.path.isdir(d) else []
    big = [(f, os.path.getsize(os.path.join(d, f))) for f in fs
           if f.endswith((".bin", ".safetensors")) and os.path.getsize(os.path.join(d, f)) > 1e6]
    tmp = [f for f in fs if f.endswith(".tmp")]
    print(f"  {d}: {big if big else '无大权重'}{' ｜ 下载中 ' + str(tmp) if tmp else ''}")
