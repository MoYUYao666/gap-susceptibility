# -*- coding: utf-8 -*-
r"""云端：**实测有多少图片加载失败并回退成随机图像**（2026-10-09）。

## 假设

`src/dataset.py` 的 `__getitem__`：
```python
try: image = Image.open(image_path).convert("RGB")
except Exception as e:
    print(f"⚠️ 无法加载 {image_path}: {e}")
    image = Image.new("RGB", (image_size, image_size))   # ← 静默回退
```

**云端只有前 1000 张图的 JPEG**，而 `results.csv`（完整）会让数据集列出**全部 31783 图** →
`max_samples=5000` 取前 1000 图 → **若这 1000 张都在**，则**无回退**。
**但实测云端 CGΔ 与本地差很多 → 需实测确认是否有回退。**

**判据（先写明）**：
- 若**回退数 > 0** → 云端数据不完整 → **结论不可用**，须补齐图片；
- 若**回退数 = 0** → 数据没问题，差异另有原因（继续查）。

    $env:CLOUD_PW='...'; python tools\_cloud_random_fallback.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

REMOTE = r'''
import os, glob, csv, collections, sys
W = "/root/autodl-tmp/work"
os.chdir(W)

IMG = "flickr30k/flickr30k-images"
have = set(os.path.basename(p) for p in glob.glob(IMG + "/*.jpg"))
print("=== 云端实际拥有的图片 ===")
print("  JPEG 文件数:", len(have))

# 解析 results.csv（与 dataset.py 同法）
csv_path = "flickr30k/results.csv"
by_img = collections.OrderedDict()
with open(csv_path, encoding="utf-8", errors="replace") as f:
    rd = csv.reader(f, delimiter="|")
    try:
        next(rd)   # 跳过表头
    except StopIteration:
        pass
    for row in rd:
        if len(row) >= 3:
            nm = row[0].strip()
            by_img.setdefault(nm, []).append(row[2].strip())
print("  results.csv 图像数:", len(by_img))
print("  results.csv 标注数:", sum(len(v) for v in by_img.values()))

# 数据集取前 1000 图 × 5 标注 = 5000 样本
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
print("=== max_samples=5000 实际取用 ===")
print("  样本数:", len(samples))
print("  唯一图:", len(uniq))
print("  **云端缺失的图**:", len(missing))
print("  → 这些样本会**回退成随机图像**，占样本的 %.1f%%"
      % (100.0 * sum(1 for nm, _ in samples if nm in set(missing)) / len(samples)))
if missing[:3]:
    print("  缺失例:", missing[:3])

# 直接实测 __getitem__ 的回退次数
print()
print("=== 实测 loader 前 200 个样本 ===")
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
    n_warn = captured.count("无法加载")
    print("  数据集样本数:", len(ds.samples))
    print("  **捕获到 %d 条『无法加载』警告**" % n_warn)
    if n_warn:
        for ln in captured.splitlines():
            if "无法加载" in ln:
                print("    " + ln.strip()[:120]); break
except Exception as e:
    sys.stdout = old
    print("  实测失败:", str(e)[:200])
'''


def main() -> int:
    from _cloud_ssh import client, run

    c = client()
    try:
        io.open(REPO / "outputs" / "_remote_rf.py", "w", encoding="utf-8",
                newline="\n").write(REMOTE)
        sftp = c.open_sftp()
        sftp.put(str(REPO / "outputs" / "_remote_rf.py"), "/root/autodl-tmp/work/_rf.py")
        sftp.close()
        run(c, "/root/miniconda3/bin/python /root/autodl-tmp/work/_rf.py", timeout=900)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
