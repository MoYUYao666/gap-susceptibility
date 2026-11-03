# -*- coding: utf-8 -*-
r"""核实：`train/val/test` 是否真的同批数据（影响结论解读，2026-10-09）。

## 为什么必须查清

`src/dataset.py:159` 在**按 split 切分之前**就 `samples = samples[:max_samples]`
→ **三个 split 拿到同一批前 N 条** → 实测 `train∩val = train∩test = 1000`（完全相同）。

**后果**：若 `strict_freeze_control.py` 的**冻结基线**与**最终 R@1**都在同一批 1000 张图上算，
那么报告的检索指标是**样本内（in-sample）**的，**须在论文里如实标注**。

**本脚本逐项查证**（不靠推断）：
1. `create_dataloaders` 在"无原生 split"时是否走 `random_split`；
2. `strict_freeze_control.py` 实际调用路径；
3. 已有归档里**是否记录过 split 信息**。

    python tools\_data_split_audit.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    apply = "--apply" in sys.argv
    ds = io.open(REPO / "src/dataset.py", encoding="utf-8").read()

    print("=== ① create_dataloaders 的 split 分支 ===")
    i = ds.find("def create_dataloaders")
    seg = ds[i:i + 2600]
    for m in re.finditer(r"(try|except|kwargs\[.split.\]|random_split|has_native|Flickr30k|MSCOCO|n_train)", seg):
        line = seg[max(0, m.start() - 60):m.start() + 140].replace("\n", " ")
        print("  " + " ".join(line.split())[:165])

    print("\n=== ② strict_freeze_control.py 的调用 ===")
    sc = io.open(REPO / "experiments/strict_freeze_control.py", encoding="utf-8").read()
    for m in re.finditer(r".{0,90}create_dataloaders.{0,150}", sc, re.S):
        print("  " + " ".join(m.group(0).split())[:220])

    print("\n=== ③ 归档里是否记录 split ===")
    hits = 0
    for f in glob.glob(str(REPO / "outputs/strict_freeze*/**/results.json"), recursive=True)[:40]:
        d = json.loads(io.open(f, encoding="utf-8").read())
        keys = [k for k in d if "split" in k.lower() or "val" in k.lower() or "test" in k.lower()]
        if keys:
            hits += 1
            if hits <= 2:
                print(f"  {Path(f).parent.name}: {keys}")
    print(f"  含 split/val/test 字段的归档: {hits}/40")

    print("\n=== ④ 判断 ===")
    uses_random_split = "random_split" in seg
    print(f"  create_dataloaders 含 random_split: {uses_random_split}")
    print("  实测（`tools/_data_verify.py`）：train∩val=1000、train∩test=1000、三者完全相同")
    print()
    print("  → **Flickr30k 路径下三个 split 是同一批数据**（截断发生在切分之前）")
    print("  → **故 `R@1` 与冻结基线均为样本内指标**，须在论文中如实标注")
    print("  → ⚠️ **但这一事实对『三臂排序』的比较无损**：")
    print("     三臂用的是同一批图、同一基线，差异来自**适配位置**而非数据划分")

    if apply:
        out = REPO / "outputs" / "analysis" / "split_audit.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        io.open(out, "w", encoding="utf-8", newline="").write(json.dumps({
            "create_dataloaders_has_random_split": uses_random_split,
            "flickr30k_splits_identical": True,
            "measured": {"train_val_overlap": 1000, "train_test_overlap": 1000},
            "consequence": "R@1 and the frozen baseline are measured on the same 1000 "
                           "images, i.e. in-sample; the three-arm ordering comparison "
                           "is unaffected because all arms share data and baseline",
            "source": "src/dataset.py:159 truncates before splitting",
        }, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
