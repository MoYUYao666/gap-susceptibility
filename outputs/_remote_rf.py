
import os, glob, csv, collections, sys
W = "/root/autodl-tmp/work"
os.chdir(W)

IMG = "flickr30k/flickr30k-images"
have = set(os.path.basename(p) for p in glob.glob(IMG + "/*.jpg"))
print("=== Images actually present in the cloud ===")
print("  JPEG files:", len(have))

# Parse results.csv (same way as dataset.py)
csv_path = "flickr30k/results.csv"
by_img = collections.OrderedDict()
with open(csv_path, encoding="utf-8", errors="replace") as f:
    rd = csv.reader(f, delimiter="|")
    try:
        next(rd)   # skip the header
    except StopIteration:
        pass
    for row in rd:
        if len(row) >= 3:
            nm = row[0].strip()
            by_img.setdefault(nm, []).append(row[2].strip())
print("  results.csv images:", len(by_img))
print("  results.csv captions:", sum(len(v) for v in by_img.values()))

# dataset: first 1000 images × 5 captions = 5000 samples
samples = []
for nm, caps in by_img.items():
    for c in caps:
        samples.append((nm, c))
    if len(samples) >= 5000:
        break
samples = samples[:5000]
uniq = sorted(set(nm for nm, _ in samples))
missing = [nm for nm in uniq if nm not in have]
print()
print("=== what max_samples=5000 actually uses ===")
print("  samples:", len(samples))
print("  unique images:", len(uniq))
print("  **images missing in the cloud**:", len(missing))
print("  → these samples **fall back to a random image**, making up %.1f%% of the samples"
      % (100.0 * sum(1 for nm, _ in samples if nm in set(missing)) / len(samples)))
if missing[:3]:
    print("  missing examples:", missing[:3])

# directly measure the number of __getitem__ fallbacks
print()
print("=== Measured: the loader's first 200 samples ===")
sys.path.insert(0, W)
import io as _io
buf = _io.StringIO()
old = sys.stdout
sys.stdout = buf
try:
    from src.dataset import Flickr30kDataset
    ds = Flickr30kDataset(data_dir="flickr30k", split="train", max_samples=5000)
    sys.stdout = old
    captured = buf.getvalue()
    n_warn = captured.count("Failed to load")
    print("  dataset samples:", len(ds.samples))
    print("  **captured %d 'Failed to load' warnings**" % n_warn)
    if n_warn:
        for ln in captured.splitlines():
            if "Failed to load" in ln:
                print("    " + ln.strip()[:120]); break
except Exception as e:
    sys.stdout = old
    print("  measurement failed:", str(e)[:200])
