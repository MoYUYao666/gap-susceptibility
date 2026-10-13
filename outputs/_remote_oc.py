
import os, json, zipfile, glob
os.chdir("/root/autodl-tmp/work")

print("=== (1) openclip file header check ===")
p = "models/openclip/open_clip_model.safetensors"
if os.path.exists(p):
    with open(p, "rb") as f:
        head = f.read(8)
        n = int.from_bytes(head, "little")
        print(f"  size {os.path.getsize(p)} B | first 8 bytes={head!r} | declared header length={n}")
        if 0 < n < 100_000_000:
            js = f.read(n)
            try:
                meta = json.loads(js.decode("utf-8"))
                keys = [k for k in meta if k != "__metadata__"]
                print(f"  ✅ header parses: {len(keys)} tensors")
                print(f"     first 4 keys: {keys[:4]}")
                biggest = max(keys, key=lambda k: meta[k].get("data_offsets",[0,0])[1])
                print(f"     largest tensor: {biggest} shape={meta[biggest].get('shape')}")
                # filename correspondence
                print("     → usable for CLIPModel? ", "visual_projection.weight" in meta or
                      "text_projection.weight" in meta)
            except Exception as e:
                print(f"  ❌ header parse failed: {str(e)[:120]}")
        else:
            print("  ❌ unreasonable header length → corrupted file")
else:
    print("  file does not exist")

print("\n=== (2) Extract the data archive ===")
z = "_cloud_data.zip"
if os.path.exists(z):
    os.makedirs("flickr30k", exist_ok=True)
    with zipfile.ZipFile(z) as zf:
        names = zf.namelist()
        print(f"  archive has {len(names)} entries, e.g. {names[:3]}")
        zf.extractall("flickr30k")
    n_img = len(glob.glob("flickr30k/flickr30k-images/*.jpg"))
    print(f"  extracted {n_img} images")
    print(f"  results.csv: {'yes' if os.path.exists('flickr30k/results.csv') else 'no'}")
else:
    print("  data archive does not exist")

print("\n=== (3) Structure check (dataset.py expects data_dir/flickr30k-images)===")
for cand in ("flickr30k/flickr30k-images", "flickr30k"):
    if os.path.isdir(cand):
        sub = os.listdir(cand)[:4]
        print(f"  {cand}: {len(os.listdir(cand))} entries e.g. {sub}")
