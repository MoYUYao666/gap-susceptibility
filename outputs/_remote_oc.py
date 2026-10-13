
import os, json, zipfile, glob
os.chdir("/root/autodl-tmp/work")

print("=== ① openclip 文件头校验 ===")
p = "models/openclip/open_clip_model.safetensors"
if os.path.exists(p):
    with open(p, "rb") as f:
        head = f.read(8)
        n = int.from_bytes(head, "little")
        print(f"  大小 {os.path.getsize(p)} B ｜ 头 8 字节={head!r} ｜ 声明 header 长度={n}")
        if 0 < n < 100_000_000:
            js = f.read(n)
            try:
                meta = json.loads(js.decode("utf-8"))
                keys = [k for k in meta if k != "__metadata__"]
                print(f"  ✅ header 可解析：{len(keys)} 个张量")
                print(f"     前 4 个 key: {keys[:4]}")
                biggest = max(keys, key=lambda k: meta[k].get("data_offsets",[0,0])[1])
                print(f"     最大张量: {biggest} shape={meta[biggest].get('shape')}")
                # 文件名对应关系
                print("     → 可用于 CLIPModel? ", "visual_projection.weight" in meta or
                      "text_projection.weight" in meta)
            except Exception as e:
                print(f"  ❌ header 解析失败: {str(e)[:120]}")
        else:
            print("  ❌ header 长度不合理 → 文件损坏")
else:
    print("  文件不存在")

print("\n=== ② 解压数据包 ===")
z = "_cloud_data.zip"
if os.path.exists(z):
    os.makedirs("flickr30k", exist_ok=True)
    with zipfile.ZipFile(z) as zf:
        names = zf.namelist()
        print(f"  包内 {len(names)} 项，例: {names[:3]}")
        zf.extractall("flickr30k")
    n_img = len(glob.glob("flickr30k/flickr30k-images/*.jpg"))
    print(f"  解压后图片: {n_img} 张")
    print(f"  results.csv: {'有' if os.path.exists('flickr30k/results.csv') else '无'}")
else:
    print("  数据包不存在")

print("\n=== ③ 结构核对（dataset.py 期望 data_dir/flickr30k-images）===")
for cand in ("flickr30k/flickr30k-images", "flickr30k"):
    if os.path.isdir(cand):
        sub = os.listdir(cand)[:4]
        print(f"  {cand}: {len(os.listdir(cand))} 项 例 {sub}")
