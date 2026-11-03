# -*- coding: utf-8 -*-
r"""**决定性对比 4**：把本地与云端的 `results.json` **并排打印**（2026-10-09）。

## 云端已暴露的硬故障

```
R@1                    = 0.002      ← 随机水平
cosine_separation      = 1.49e-08   ← 正负样本不可区分
mean_cosine_pos        = 0.185680091381073
mean_cosine_neg        = 0.1856800764799118   ← 与 pos 差 1.5e-08
```
**本地归档 `R@1 = 0.68`** → **云端那批结果的评估完全失效，不可用。**

    python tools\_p70_side_by_side.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

FLAT = ["experiment", "seed", "strict_freeze", "n_trainable_params", "epochs",
        "max_samples", "batch_size", "elapsed_sec"]


def flat(d):
    """把 results.json 摊平成 {路径: 值}，便于逐项比对。"""
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            for k2, v2 in v.items():
                if isinstance(v2, dict):
                    continue
                out[f"{k}.{k2}"] = v2
        else:
            out[k] = v
    return out


def main() -> int:
    apply = "--apply" in sys.argv
    from _cloud_ssh import client, run

    local = json.loads(io.open(
        REPO / "outputs/strict_freeze_b32_r4/both/seed123/results.json",
        encoding="utf-8").read())
    c = client()
    try:
        out, _ = run(c, "cat /root/autodl-tmp/work/outputs/strict_freeze_b32_r4/both/"
                        "seed123/results.json", timeout=120, quiet=True)
        cloud = json.loads(out[out.find("{"):out.rfind("}") + 1])
    finally:
        c.close()

    L, C = flat(local), flat(cloud)
    keys = sorted(set(L) | set(C))
    print(f"=== 并排对比（both / seed123 / batch128 / 10ep / max5000）===")
    print(f"  {'字段':<40}{'本地':>20}{'云端':>20}  判定")
    bad = []
    for k in keys:
        lv, cv = L.get(k), C.get(k)
        if isinstance(lv, (int, float)) and isinstance(cv, (int, float)):
            same = abs(lv - cv) < 1e-6
            ratio = (cv / lv) if lv else float("nan")
            mark = "✅" if same else ("⚠️" if abs(ratio - 1) < 0.05 else "❌")
            if not same:
                bad.append((k, lv, cv, ratio))
            print(f"  {k:<40}{lv:>20.6f}{cv:>20.6f}  {mark} ratio={ratio:.4f}")
        else:
            same = str(lv) == str(cv)
            print(f"  {k:<40}{str(lv)[:20]:>20}{str(cv)[:20]:>20}  {'✅' if same else '·'}")

    print(f"\n=== 不一致项 {len(bad)} 个 ===")
    for k, lv, cv, r in bad[:16]:
        print(f"  {k:<40} 本地={lv:>12.6f} 云端={cv:>12.6f} 比值={r:.4f}")

    if apply:
        p = REPO / "outputs" / "analysis" / "side_by_side.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        io.open(p, "w", encoding="utf-8", newline="").write(json.dumps({
            "local": L, "cloud": C,
            "mismatches": [{"key": k, "local": lv, "cloud": cv, "ratio": r}
                           for k, lv, cv, r in bad],
        }, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {p.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
