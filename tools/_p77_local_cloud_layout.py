# -*- coding: utf-8 -*-
r"""**判定实验**：云端失效是"数据打包方式"还是"环境"？（2026-10-09）

## 为什么这是最强的一步

云端与本地**同代码、同权重、同图片、同 CSV**，唯一差别是**我上传时把 `results.csv`
放到了 `flickr30k/results.csv`（而不是本地的 `flickr30k/flickr30k-images/results.csv`）**。

**→ 在本地复刻云端的数据布局跑一次，就能一刀切开两种可能：**

| 本地复刻的结果 | 结论 |
|---|---|
| **也失效**（`R@1 ≈ 0.002`、`loss ≈ 4.85`） | **问题在数据打包方式**（与云端环境无关） |
| **正常**（`R@1 ≈ 0.68`） | **问题在云端环境** |

## 做法（严格复刻云端布局）

```
outputs/_cloud_layout/
├── flickr30k/
│   ├── flickr30k-images/     ← 1000 张 jpg（与云端同一批）
│   └── results.csv           ← **放在 flickr30k/ 下**（与云端相同位置）
```

然后 `--data-dir outputs/_cloud_layout` 跑 `both`，**小规模先快出结果**
（`max_samples 500` → 约 3 min）。

    python tools\_p77_local_cloud_layout.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LAYOUT = REPO / "outputs" / "_cloud_layout"
PY = sys.executable


def build_layout() -> None:
    """复刻云端数据布局（1000 图 + results.csv 在 flickr30k/ 下）。"""
    if LAYOUT.exists():
        shutil.rmtree(LAYOUT)
    root = LAYOUT / "flickr30k"
    imgs = root / "flickr30k-images"
    imgs.mkdir(parents=True, exist_ok=True)

    # 从已保存的清单复制同一批图（与云端相同）
    lst = REPO / "outputs" / "analysis" / "needed_images.txt"
    names = [x.strip() for x in io.open(lst, encoding="utf-8") if x.strip()]
    src = REPO / "flickr30k" / "flickr30k-images"
    n = 0
    for nm in names:
        p = src / nm
        if p.exists():
            shutil.copy2(p, imgs / nm)
            n += 1
    # 关键：results.csv 放在 flickr30k/ 下（**与云端相同**，与本地不同）
    src_csv = src / "results.csv"
    shutil.copy2(src_csv, root / "results.csv")
    print(f"  ✅ 布局就绪：{n} 张图 ｜ results.csv 在 flickr30k/ 下 "
          f"（{src_csv.stat().st_size:,} B）")
    print(f"     {LAYOUT.relative_to(REPO)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--max-samples", type=int, default=500)
    ap.add_argument("--epochs", type=int, default=3)
    a = ap.parse_args()

    if not a.apply:
        print("=== 判定实验：本地复刻云端数据布局 ===")
        print(f"  布局: {LAYOUT.relative_to(REPO)}/flickr30k/{{flickr30k-images, results.csv}}")
        print(f"  参数: both ｜ max_samples {a.max_samples} ｜ epochs {a.epochs}")
        print("  判据: R@1≈0.002 → 数据问题；R@1≈0.68 → 环境问题")
        print("  （预演；加 --apply 实跑）")
        return 0

    build_layout()

    import subprocess
    out_dir = REPO / "outputs" / "_layout_test" / "r4"
    cmd = [PY, "experiments/strict_freeze_control.py",
           "--model", "models/clip-vit-base-patch32",
           "--out-dir", str(out_dir.relative_to(REPO)).replace("\\", "/"),
           "--name", "layout_",
           "--rank", "4", "--alpha-mult", "2", "--tags", "both",
           "--seeds", "42", "--epochs", str(a.epochs),
           "--max-samples", str(a.max_samples), "--batch-size", "64",
           "--data-dir", str(LAYOUT.relative_to(REPO)).replace("\\", "/"),
           "--skip-frozen"]
    print(f"\n=== 运行：{' '.join(cmd[1:])} ===")
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=3600)
    tail = (r.stdout or "").splitlines()[-25:]
    for ln in tail:
        print("  " + ln[:150])
    if r.returncode != 0:
        print(f"  ❌ rc={r.returncode}")
        for ln in (r.stderr or "").splitlines()[-12:]:
            print("  ! " + ln[:150])
        return 1

    import json
    fs = sorted(out_dir.glob("both/seed*/results.json"))
    if not fs:
        print("  ❌ 无 results.json")
        return 1
    d = json.loads(io.open(fs[0], encoding="utf-8").read())
    r1 = d["final_task_metrics"]["R@1"]
    loss = d["final_train_loss"]
    sep = d["initial_gap"]["cosine_separation"]
    cg = d["final_gap"]["centroid_gap"] - d["initial_gap"]["centroid_gap"]
    print("\n=== 判定 ===")
    print(f"  R@1 = {r1:.4f} ｜ loss 末 = {loss:.4f} ｜ "
          f"cosine_separation(init) = {sep:.6f} ｜ CGΔ = {cg:+.4f}")
    print("  云端失效基准: R@1=0.0020 ｜ loss=4.81 ｜ sep=0.000000")
    print("  本地正常基准: R@1=0.685   ｜ loss=0.16 ｜ sep=0.141407")
    if r1 < 0.1 and sep < 1e-6:
        print("\n  → ❌ **本地复刻也失效** ⇒ **问题在数据打包方式**（与云端环境无关）")
    elif r1 > 0.3:
        print("\n  → ✅ **本地复刻正常** ⇒ **问题在云端环境**（数据布局无罪）")
    else:
        print("\n  → ⚠️ 中间态，需再查")

    p = REPO / "outputs" / "analysis" / "layout_verdict.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    io.open(p, "w", encoding="utf-8", newline="").write(json.dumps({
        "R@1": r1, "final_train_loss": loss, "cosine_separation_init": sep,
        "cg_delta": cg, "max_samples": a.max_samples, "epochs": a.epochs,
        "layout": "results.csv at flickr30k/ (cloud layout)",
        "verdict": ("data-packaging" if (r1 < 0.1 and sep < 1e-6) else
                    "cloud-environment" if r1 > 0.3 else "inconclusive"),
    }, ensure_ascii=False, indent=1))
    print(f"\n  ✅ 已写 {p.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
