# -*- coding: utf-8 -*-
r"""解码器 VLM 的 **bf16 统一 3-seed** 研究（C3 缺口）（2026-10-10）。

## 为什么用 bf16 而不是 4-bit

**实测的非确定性来源**（`tools/_p155_determinism_source.py`）：

| 精度 | 同 seed 42 跑两次 | 可逐位复现 |
|---|---|---|
| **bf16** | `cg_span` = 0.110064 / 0.110064 | ✅ **是** |
| **4-bit** | 0.3470 / 0.2849（另测 0.3041 / 0.4073） | ❌ 否（**bitsandbytes 非确定**） |

**且两者量级差很大**（bf16 ~0.11–0.58 vs 4-bit ~0.28–0.41）→ **精度必须统一**。

**归档的不一致**：`both`/`vision_only` 是 **4-bit**，`text_only` 是 **bf16**（`4bit=False`）
→ 此前三臂**精度不齐**且**各只 1 seed**。

## 本驱动

**配置**：`--maxsamples 400 --epochs 3 --batch 2`（**无 `--4bit`** = bf16）
**seed**：42 / 123 / 456 × 3 臂 = **9 run** → `outputs/vlm_seeds_bf16/`
**逐位可复现**（同 seed 同进程参数 → 相同结果，已实测）

**耗时实测**：`text_only` 204 s ｜ `vision_only` 937 s ｜ `both` 485 s → **单 seed 27 min**
→ **9 run ≈ 1.7 h**（含模型加载开销）

    python tools\_p156_vlm_bf16_seeds.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import statistics as st
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = sys.executable
LOG = REPO / "outputs" / "_vlm_bf16_seeds.log"
OUTDIR = "outputs/vlm_seeds_bf16"
SEEDS = ("42", "123", "456", "789", "1011", "1313", "1616", "1919", "2323",
         "2727", "3131", "3737", "4141")
ARMS = ("text_only", "vision_only", "both")
CFG = ["--maxsamples", "400", "--epochs", "3", "--batch", "2"]


def log(m: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {m}"
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(seed: str, arm: str) -> bool:
    cmd = [PY, "-u", "tools/_p47_qwen_train.py", "--apply", *CFG,
           "--seed", seed, "--arms", arm, "--outdir", OUTDIR]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=4 * 3600, cwd=str(REPO))
    dt = time.time() - t0
    if r.returncode == 0:
        log(f"   ✅ {arm}/seed{seed}（{dt:.0f}s）")
        return True
    err = next((l.strip() for l in (r.stderr or "").splitlines()
                if "Error" in l or "error" in l), "")
    log(f"   ❌ {arm}/seed{seed} rc={r.returncode} {err[:120]}")
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    n = len(SEEDS) * len(ARMS)
    print(f"=== 计划：{n} run（{' × '.join(SEEDS)} × {len(ARMS)} 臂）===")
    print(f"  配置 {' '.join(CFG)}（bf16） → {OUTDIR}/")
    print("  预计约 1.7 h")
    if not a.apply:
        print("  （预演）")
        return 0

    log("=" * 60)
    log(f"解码器 VLM bf16 多种子研究启动（{n} run）")
    ok = fail = skip = 0
    for seed in SEEDS:
        for arm in ARMS:
            f = REPO / OUTDIR / f"{arm}_seed{seed}.json"
            if f.exists():
                skip += 1
                log(f"· 已有 {f.name}，跳过")
                continue
            if run(seed, arm):
                ok += 1
            else:
                fail += 1
    log(f"完成：成功 {ok} ｜ 失败 {fail} ｜ 跳过 {skip}")

    # 汇总
    print("\n=== 汇总（mean ± sd，ΔCG 跨度越大 = 保护越弱）===")
    res = {}
    for arm in ARMS:
        xs, dgs = [], []
        for s in SEEDS:
            f = REPO / OUTDIR / f"{arm}_seed{s}.json"
            if not f.exists():
                continue
            d = json.loads(io.open(f, encoding="utf-8").read())
            xs.append(d["cg_span"]); dgs.append(d["dg_span"])
        if xs:
            res[arm] = {"n": len(xs), "cg": [round(v, 5) for v in xs],
                        "cg_mean": round(st.mean(xs), 5),
                        "cg_sd": round(st.stdev(xs), 5) if len(xs) > 1 else None,
                        "dg_mean": round(st.mean(dgs), 5),
                        "dg_sd": round(st.stdev(dgs), 5) if len(dgs) > 1 else None}
            sd = res[arm]["cg_sd"]
            print(f"  {arm:<12} n={len(xs)}  CG 跨度 {res[arm]['cg_mean']:.4f}"
                  + (f" ± {sd:.4f}" if sd else "") + f"  ｜ 逐 seed {res[arm]['cg']}")
    if len(res) >= 2:
        order = sorted(res, key=lambda k: res[k]["cg_mean"])
        print(f"\n  由保护强到弱：{' < '.join(order)}")
        for i in range(len(order) - 1):
            a1, a2 = order[i], order[i + 1]
            d = abs(res[a1]["cg_mean"] - res[a2]["cg_mean"])
            s1, s2 = res[a1]["cg_sd"], res[a2]["cg_sd"]
            if s1 and s2:
                psd = (s1 ** 2 + s2 ** 2) ** 0.5
                k = d / psd if psd else float("nan")
                print(f"    {a1} vs {a2}: |Δ|={d:.4f} pooled_sd={psd:.4f} → "
                      f"**{k:.2f} sd** " + ("✅ 显著" if k >= 2 else
                                            ("⚠️ 边缘" if k >= 1 else "🔴 不显著")))
    out = REPO / "outputs" / "analysis" / "vlm_bf16_seeds_verdict.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    io.open(out, "w", encoding="utf-8", newline="").write(json.dumps(
        {"per_arm": res, "config": " ".join(CFG), "precision": "bf16",
         "seeds": list(SEEDS)}, ensure_ascii=False, indent=1))
    log(f"✅ 已写 {out.relative_to(REPO)}")
    log("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
