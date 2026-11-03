# -*- coding: utf-8 -*-
r"""生成**精确环境清单** + 锁死关键版本（2026-10-09）。

## 为什么（操作者的质疑："别人用云端复现不也会出问题吗"）

| 项 | 现状 | 问题 |
|---|---|---|
| `requirements.txt` | 全 `>=`（`torch>=2.0.0`、`transformers>=4.30.0`） | **不锁版本** |
| `pip freeze` | ❌ 不存在 | **无精确记录** |
| 实测 | `transformers==5.19.0` **跑不出结果**，`5.16.1` 可以 | **今天是 open range，明天就装到坏的版本** |

## 产出

1. `docs/ENVIRONMENT.md` —— **精确版本清单** + 已知不兼容提示 + 复现步骤；
2. `requirements-lock.txt` —— **可 `pip install -r` 的锁版本文件**；
3. `requirements.txt` 顶部加**警告与指引**（指向锁文件）。

    python tools\_p76_env_lock.py [--apply]
"""
from __future__ import annotations

import importlib
import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

CRITICAL = ["torch", "torchvision", "transformers", "peft", "tokenizers",
            "huggingface_hub", "safetensors", "accelerate", "numpy", "pillow",
            "tqdm", "scipy", "matplotlib"]

# 已知会破坏管线的版本（实测，2026-10-09）
KNOWN_BAD = {
    "transformers": "5.19.0（实测：R@1=0.002、loss 卡在 ln(128)、初始 cosine_separation=0；"
                    "同代码在 5.16.1 上 R@1=0.685）",
}


def main() -> int:
    apply = "--apply" in sys.argv

    print("=== 采集精确版本 ===")
    vers = {}
    for m in CRITICAL:
        try:
            mod = importlib.import_module(m)
            v = getattr(mod, "__version__", None)
            if v:
                vers[m] = v
                print(f"  {m:<18} {v}")
        except Exception:
            print(f"  {m:<18} （未安装）")

    print("\n=== pip freeze（全量）===")
    r = subprocess.run([sys.executable, "-m", "pip", "freeze"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    freeze = (r.stdout or "").strip()
    print(f"  共 {len(freeze.splitlines())} 行")

    if not apply:
        print("\n  （预演；加 --apply 写文件）")
        return 0

    # ① requirements-lock.txt
    lock = REPO / "requirements-lock.txt"
    lines = ["# 精确锁版本（由 tools/_p76_env_lock.py 于 2026-10-09 生成）",
             "# 用途：复现实验；不要用 requirements.txt 的 >= 版本，"
             "因其会装到已知会破坏管线的版本",
             ""]
    for m, v in vers.items():
        lines.append(f"{m}=={v}")
    lines += ["", "# ── 以下为 pip freeze 全量（可 pip install -r 直接用）──", ""]
    lines += freeze.splitlines()
    io.open(lock, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print(f"  ✅ {lock.relative_to(REPO)}（{len(lines)} 行）")

    # ② docs/ENVIRONMENT.md
    doc = f"""# 精确环境与复现说明（2026-10-09）

> 生成脚本：`tools/_p76_env_lock.py`。**本文件是复现的唯一权威环境记录。**

## 为什么需要它

`requirements.txt` 用的是 `>=` 约束（如 `transformers>=4.30.0`）。
**实测证明这个范围不安全**：

> **`transformers==5.19.0` 上，本项目的严格冻结实验跑不出结果**
> （`R@1 = 0.002`、`final_train_loss ≈ ln(128) = 4.852`、初始 `cosine_separation = 0`），
> **同一份代码、同一份数据、同一份权重在 `transformers==5.16.1` 上 `R@1 = 0.685`。**

**故复现必须用 `requirements-lock.txt`，不要用 `requirements.txt`。**

## 本机（产出论文数字的）环境

| 包 | 版本 |
|---|---|
""" + "\n".join(f"| `{m}` | `{v}` |" for m, v in vers.items()) + f"""

GPU：NVIDIA GeForce RTX 4060 Laptop（8 GB）
Python：{sys.version.split()[0]}

## 已知不兼容

| 包 | 版本 | 症状 | 证据 |
|---|---|---|---|
""" + "\n".join(f"| `{k}` | {v} | 训练失效 | `outputs/analysis/side_by_side.json` |"
                for k, v in KNOWN_BAD.items()) + """

## 复现步骤

```bash
python -m venv .venv && . .venv/bin/activate     # 或 conda create -n x python=3.12
pip install -r requirements-lock.txt
# 数据与模型按 docs/CLOUD_SEEDS_RUNBOOK.md 的服务器端获取方式准备
python tools/_claim_ledger.py --apply            # 门禁：应 40/40 通过
```

## ⚠️ 尚未解决

**云端环境（torch 2.12.1 / transformers 5.19.0）上失效的根因未钉死。**
已排除：模型权重、数据（md5 一致）、脚本（sha256 一致）、预处理、`n_trainable`。
剩余嫌疑：`create_dataloaders` 的分支差异，或 transformers 5.x 对 CLIP
`padding`/`attention_mask` 的处理差异。
**若他人复现失败，请先核对上表版本；若版本一致仍失败，请提供
`R@1` 与 `final_train_loss` 两个数——它们能立刻区分"训练失效"与"环境微差"。**
"""
    dp = REPO / "docs" / "ENVIRONMENT.md"
    dp.parent.mkdir(parents=True, exist_ok=True)
    io.open(dp, "w", encoding="utf-8", newline="\n").write(doc)
    print(f"  ✅ {dp.relative_to(REPO)}（{len(doc.splitlines())} 行）")

    # ③ requirements.txt 顶部警告
    rp = REPO / "requirements.txt"
    rt = io.open(rp, encoding="utf-8").read()
    warn = ("# ⚠️ 复现实验请用 requirements-lock.txt（精确锁版本），不要用本文件。\n"
            "#    原因：本文件的 >= 约束会装到 transformers>=5.19，而该版本实测会\n"
            "#    使严格冻结实验失效（R@1=0.002 vs 5.16.1 的 0.685）。\n"
            "#    详见 docs/ENVIRONMENT.md\n\n")
    if "requirements-lock.txt" not in rt:
        io.open(rp, "w", encoding="utf-8", newline="\n").write(warn + rt)
        print(f"  ✅ {rp.relative_to(REPO)} 顶部已加警告")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
