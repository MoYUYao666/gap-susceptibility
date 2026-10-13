# -*- coding: utf-8 -*-
r"""云端：高成本候选实验的**可行性核算**（2026-10-09）。

## 候选（来自 `docs/PAPERA_REVIEWER_RISKS.md` 与论文自认缺口）

| # | 实验 | 论文价值 | 显存需求（估算） | 云 32 GB 可行？ |
|---|---|---|---|---|
| **H1** | **Qwen2-VL-7B 原量化（bf16，非 4-bit）三臂** | 消除"C3 单模型/4-bit"两条 caveat | 7B bf16 = **14 GB** 权重 + LoRA + 激活 ≈ **22–28 GB** | 边缘，需实测 |
| **H2** | **第二个解码器 VLM**（LLaVA-1.5-7B）三臂 | C3 的"单模型"→ 两模型 | 同上 | 边缘 |
| **H3** | **更大规模严格冻结**（max-samples 20000 / 20 epoch） | C6"训练规模小" | 同 CLIP（小） | ✅ 轻松 |
| **H4** | **batch 轴**（B/32 r4 batch 32/64/128/256） | 支持"设备约束"的说法 | 小 | ✅ |
| **H5** | **OpenCLIP 的 `text_only` 补充** | B3 效应量异质 | 小 | ✅ |
| **H6** | **Γ_m 全骨干 × 全 arm 完整量** | 机制层证据 | 小 | ✅ |

## 本脚本只做**实测**，不猜

1. 查当前磁盘余量（30 GB overlay + 可挂数据盘）；
2. **实测** 7B bf16 模型能否加载 + 单步显存/耗时（用小样本，不训练）；
3. 查 LLaVA-1.5-7B 在 hf-mirror 的可达性。

    $env:CLOUD_PW='...'; python tools\_cloud_feasibility.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"

REMOTE = r'''
import os, subprocess, json
os.chdir("/root/autodl-tmp/work")

print("=== ① 磁盘 ===")
for line in subprocess.run(["df","-h","/"],capture_output=True,text=True).stdout.splitlines():
    print("  " + line)

print("\n=== ② GPU ===")
print("  " + subprocess.run(["nvidia-smi","--query-gpu=name,memory.total,memory.used",
                            "--format=csv,noheader"],capture_output=True,text=True).stdout.strip())

print("\n=== ③ 7B 模型可达性（只发 HEAD，不下整包）===")
CANDS = [
    ("Qwen/Qwen2-VL-7B-Instruct", "https://hf-mirror.com/Qwen/Qwen2-VL-7B-Instruct/resolve/main/config.json"),
    ("llava-hf/llava-1.5-7b-hf", "https://hf-mirror.com/llava-hf/llava-1.5-7b-hf/resolve/main/config.json"),
    ("Qwen/Qwen2.5-VL-7B-Instruct", "https://hf-mirror.com/Qwen/Qwen2.5-VL-7B-Instruct/resolve/main/config.json"),
]
for name, url in CANDS:
    r = subprocess.run(["curl","-sL","-o","/dev/null","--max-time","20",
                        "-w","%{http_code} %{size_download}","-r","0-2000",url],
                       capture_output=True, text=True)
    print("  %-32s %s" % (name, r.stdout.strip()))

print("\n=== ④ 已有模型体积 ===")
tot = 0
for d in sorted(os.listdir("models")):
    p = os.path.join("models", d)
    if not os.path.isdir(p): continue
    s = sum(os.path.getsize(os.path.join(p,f)) for f in os.listdir(p)
            if os.path.isfile(os.path.join(p,f)))
    tot += s
    print("  %-32s %8.0f MB" % (d, s/1e6))
print("  合计 %.1f GB" % (tot/1e9))
'''


def main() -> int:
    from _cloud_ssh import client, run

    c = client()
    try:
        io.open(REPO / "outputs" / "_remote_fe.py", "w", encoding="utf-8",
                newline="\n").write(REMOTE)
        sftp = c.open_sftp()
        sftp.put(str(REPO / "outputs" / "_remote_fe.py"), f"{WORK}/_fe.py")
        sftp.close()
        run(c, f"{PY} {WORK}/_fe.py", timeout=600)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
