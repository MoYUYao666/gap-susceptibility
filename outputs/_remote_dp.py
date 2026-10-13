
import os, csv, glob, collections, hashlib, json
os.chdir("/root/autodl-tmp/work")

def summarize(tag, img_dir, csv_path):
    have = sorted(os.path.basename(p) for p in glob.glob(img_dir + "/*.jpg"))
    print("=== %s ===" % tag)
    print("  JPEG 数:", len(have))
    by = collections.OrderedDict()
    with open(csv_path, encoding="utf-8", errors="replace") as f:
        rd = csv.reader(f, delimiter="|")
        try: next(rd)
        except StopIteration: pass
        for row in rd:
            if len(row) >= 3:
                by.setdefault(row[0].strip(), []).append(row[2].strip())
    print("  CSV 图数:", len(by), "｜ 标注数:", sum(len(v) for v in by.values()))
    # 数据集取前 5000 条标注 → 哪些图
    samples = []
    for nm, caps in by.items():
        for c in caps:
            samples.append(nm)
        if len(samples) >= 5000:
            break
    uniq = sorted(set(samples[:5000]))
    print("  前 5000 标注覆盖的图数:", len(uniq))
    print("  前 10 图:", uniq[:10])
    print("  前 1000 图 md5:", hashlib.md5("".join(uniq).encode()).hexdigest()[:16])
    print("  CSV 首 3 图:", list(by.keys())[:3])
    print("  CSV md5:", hashlib.md5(open(csv_path,'rb').read()).hexdigest()[:16])
    return uniq

u = summarize("云端", "flickr30k/flickr30k-images", "flickr30k/results.csv")
json.dump({"uniq1000": u, "n_jpeg": len(glob.glob("flickr30k/flickr30k-images/*.jpg"))},
          open("_data_parity.json", "w"))
print()
print("=== 云端图片是否都在前 1000 ===")
have = set(os.path.basename(p) for p in glob.glob("flickr30k/flickr30k-images/*.jpg"))
print("  前 1000 图中云端缺失:", len([x for x in u if x not in have]))
