# -*- coding: utf-8 -*-
r"""云端：**对齐 transformers 版本**（5.19 → 本地同版），修复失效的训练（2026-10-09）。

## 实测故障（已定量）

| 指标 | 本地 | 云端 | 判定 |
|---|---|---|---|
| `R@1` | **0.685** | **0.002** | ❌ 随机 |
| `final_train_loss` | 0.157 | **4.809** | ❌ 未下降 |
| `cosine_separation`（初始） | **0.1414** | **0.0000** | ❌ 正负样本不可区分 |
| `elapsed_sec` | 1562.8 | **186.2** | ❌ 快 8.4 倍 |

**初始 `effective_rank` 全部一致（ratio=1.0000）→ 模型与数据等价；
训练后完全不同 → 故障在训练/评估路径。**

**首要嫌疑：transformers 版本**（云端 **5.19.0** vs 本地 **5.16.1**）。

## 本脚本

1. 查本地确切版本；
2. 在云端装**同版**；
3. 跑 `both` 单 seed 验证 `R@1` 是否回到 ~0.68。

    $env:CLOUD_PW='...'; python tools\_cloud_fix_versions.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"


def main() -> int:
    apply = "--apply" in sys.argv

    # ① 本地版本
    import importlib
    import subprocess
    print("=== 本地版本 ===")
    v = subprocess.run([sys.executable, "-c",
                        "import transformers,peft,torch;"
                        "print(transformers.__version__, peft.__version__, torch.__version__)"],
                       capture_output=True, text=True)
    print("  transformers / peft / torch =", (v.stdout or "").strip())
    parts = (v.stdout or "").strip().split()
    if len(parts) < 2:
        print("  ❌ 拿不到本地版本")
        return 1
    tf_ver, peft_ver = parts[0], parts[1]

    if not apply:
        print(f"\n  （预演）将在云端安装 transformers=={tf_ver} peft=={peft_ver}")
        return 0

    from _cloud_ssh import bg, client, run

    c = client()
    try:
        print("=== 云端现状 ===")
        run(c, f"{PY} -c \"import transformers,peft;"
               f"print(transformers.__version__, peft.__version__)\"", timeout=120)

        print(f"\n=== 装 transformers=={tf_ver} peft=={peft_ver}（脱离运行）===")
        cmd = (f"{PY} -m pip install -q 'transformers=={tf_ver}' 'peft=={peft_ver}' "
               f"2>&1 | tail -5; {PY} -c \"import transformers,peft;"
               f"print('AFTER', transformers.__version__, peft.__version__)\"")
        run(c, f"cd {WORK} && {cmd}", timeout=1800)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
