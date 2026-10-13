
import os, csv, glob, collections, hashlib, json
os.chdir("/root/autodl-tmp/work")

def summarize(tag, img_dir, csv_path):
    have = sorted(os.path.basename(p) for p in glob.glob(img_dir + "/*.jpg"))
    print("=== %s ===" % tag)
    print("  JPEG count:", len(have))
    by = collections.OrderedDict()
    with open(csv_path, encoding="utf-8", errors="replace") as f:
        rd = csv.reader(f, delimiter="|")
        try: next(rd)
        except StopIteration: pass
        for row in rd:
            if len(row) >= 3:
                by.setdefault(row[0].strip(), []).append(row[2].strip())
    print("  CSV images:", len(by), "| captions:", sum(len(v) for v in by.values()))
    # dataset takes the first 5000 captions → which images
    samples = []
    for nm, caps in by.items():
        for c in caps:
            samples.append(nm)
        if len(samples) >= 5000:
            break
    uniq = sorted(set(samples[:5000]))
    print("  images covered by the first 5000 captions:", len(uniq))
    print("  first 10 images:", uniq[:10])
    print("  first 1000 images md5:", hashlib.md5("".join(uniq).encode()).hexdigest()[:16])
    print("  first 3 CSV images:", list(by.keys())[:3])
    print("  CSV md5:", hashlib.md5(open(csv_path,'rb').read()).hexdigest()[:16])
    return uniq

u = summarize("cloud", "flickr30k/flickr30k-images", "flickr30k/results.csv")
json.dump({"uniq1000": u, "n_jpeg": len(glob.glob("flickr30k/flickr30k-images/*.jpg"))},
          open("_data_parity.json", "w"))
print()
print("=== are all cloud images within the first 1000 ===")
have = set(os.path.basename(p) for p in glob.glob("flickr30k/flickr30k-images/*.jpg"))
print("  cloud images missing from the first 1000:", len([x for x in u if x not in have]))
