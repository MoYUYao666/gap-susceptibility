# -*- coding: utf-8 -*-
r"""云端：**高成本高价值实验队列**（操作者要求"趁此机会都跑"）（2026-10-09）。

## 队列设计（按 价值/成本 排序，**串行**以免抢当前 GPU）

| 序 | 实验 | 解决哪条 caveat | 显存 | 预估 |
|---|---|---|---|---|
| **Q1** | **CLIP B/32 r4 的 `text_only` 大规模**：`max-samples 20000` × `epochs 20` × 3 seed | C6「训练规模小」 | 小 | ~1.5 h |
| **Q2** | **batch 轴**：B/32 r4 batch 32/64/128/256（各 1 seed × 3 arm） | 支撑「设备约束」的说法 | 小 | ~1 h |
| **Q3** | **OpenCLIP 补 `text_only` 与 `both` 的 seed 3/4/5** | B3 效应量异质 | 小 | ~1.5 h |
| **Q4** | **`Γ_m` 完整量（含 cos）** 于 B/16 与 OpenCLIP 三臂 | 机制层证据（现在只有 B/32） | 小 | ~20 min |
| **Q5** | **Qwen2-VL-7B bf16（原量化）三臂** | **C3 的「4-bit」caveat**（论文最大缺口） | **20–28 GB** | ~2 h（先含下载） |
| **Q6** | **LLaVA-1.5-7B 三臂** | **C3 的「单模型」caveat** | 20–28 GB | ~2 h |
| **Q7** | **生成式目标准确验证**（VQA 而非检索） | **论文明说 "generation-oriented objectives remains untested"** | 20–28 GB | ~2 h |

**先跑 Q1–Q4（小、确定、价值明确），再跑 Q5–Q7（大，需先测显存）。**

**Q5–Q7 的铁律**：**先测单步显存，确认不 OOM 再开跑**（避免"跑到一半挂"）。

    $env:CLOUD_PW='...'; python tools\_cloud_big_queue.py --write      # 生成远端队列脚本
    $env:CLOUD_PW='...'; python tools\_cloud_big_queue.py --start-small  # 启动 Q1-Q4
    $env:CLOUD_PW='...'; python tools\_cloud_big_queue.py --probe-7b     # 测 7B 显存
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"

Q_SMALL = r'''
import os, subprocess, sys, time
PY = "/root/miniconda3/bin/python"
os.chdir("/root/autodl-tmp/work")

def log(m):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), m)
    print(line, flush=True)
    with open("outputs_big.log", "a") as f:
        f.write(line + "\n")

def run(cmd, tag, timeout=6*3600):
    log("RUN %s" % tag)
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    dt = time.time() - t0
    if r.returncode == 0:
        log("  OK %.0fs" % dt)
    else:
        err = next((l for l in (r.stderr or "").splitlines()
                    if "Error" in l or "error" in l), "")
        log("  FAIL rc=%s %.0fs %s" % (r.returncode, dt, err[:150]))
    return r.returncode == 0

BASE = [PY, "experiments/strict_freeze_control.py", "--rank", "4",
        "--alpha-mult", "2", "--skip-frozen"]

log("=" * 60)
log("高成本队列 Q1-Q4 启动")

# ── Q1 大规模：20000 样本 × 20 epoch × 3 seed（B/32 text_only）──
run(BASE + ["--model", "models/clip-vit-base-patch32",
            "--out-dir", "outputs/scale_b32_r4", "--name", "scale_",
            "--tags", "text_only", "--seeds", "42", "123", "456",
            "--epochs", "20", "--max-samples", "20000",
            "--batch-size", "128"],
    "Q1 大规模 B/32 r4 text_only (20000x20, 3 seeds)")

# ── Q2 batch 轴（B/32 r4 text_only，batch 32/64/256）──
for bs in ("32", "64", "256"):
    run(BASE + ["--model", "models/clip-vit-base-patch32",
                "--out-dir", "outputs/batchaxis_b32_r4", "--name", "bs%s_" % bs,
                "--tags", "text_only", "--seeds", "42",
                "--epochs", "10", "--max-samples", "5000",
                "--batch-size", bs],
        "Q2 batch=%s" % bs)

# ── Q3 OpenCLIP 补 seed 3/4/5（text_only + both）──
for arm in ("text_only", "both"):
    run(BASE + ["--model", "models/openclip",
                "--out-dir", "outputs/strict_freeze_oclip/r4", "--name", "oclip_r4_",
                "--tags", arm, "--seeds", "789", "1024",
                "--epochs", "10", "--max-samples", "5000",
                "--batch-size", "128"],
        "Q3 OpenCLIP %s seeds 789/1024" % arm)

log("Q1-Q4 完成")
log("ALLDONE_SMALL")
'''

PROBE_7B = r'''
import os, sys, time, json, subprocess
os.chdir("/root/autodl-tmp/work")
log = lambda m: print("[%s] %s" % (time.strftime("%H:%M:%S"), m), flush=True)

# ① 下载 config 与权重（hf-mirror，后台可断）
os.makedirs("models/qwen2vl7b", exist_ok=True)
M = "https://hf-mirror.com/Qwen/Qwen2-VL-7B-Instruct/resolve/main"
log("下载 7B config/small files")
for f in ("config.json", "preprocessor_config.json", "tokenizer.json",
          "tokenizer_config.json", "vocab.json", "merges.txt",
          "generation_config.json", "chat_template.json"):
    p = "models/qwen2vl7b/" + f
    if not os.path.exists(p):
        subprocess.run(["curl", "-sL", "--max-time", "120", "-o", p, "%s/%s" % (M, f)])

# ② 权重按 shard 下载（Qwen2-VL-7B 用 safetensors 分片）
log("探测权重分片")
idx = "models/qwen2vl7b/model.safetensors.index.json"
if not os.path.exists(idx):
    subprocess.run(["curl", "-sL", "--max-time", "120", "-o", idx,
                    "%s/model.safetensors.index.json" % M])
if os.path.exists(idx):
    try:
        d = json.load(open(idx))
        shards = sorted(set(d["weight_map"].values()))
        log("分片数 %d: %s" % (len(shards), shards[:3]))
        for sh in shards:
            p = "models/qwen2vl7b/" + sh
            if os.path.exists(p) and os.path.getsize(p) > 100e6:
                log("SKIP %s" % sh); continue
            if os.path.exists(p):
                os.remove(p)
            t0 = time.time()
            subprocess.run(["curl", "-sL", "--retry", "5", "--max-time", "1800",
                            "-o", p, "%s/%s" % (M, sh)])
            sz = os.path.getsize(p) if os.path.exists(p) else 0
            log("  %s %.0f MB in %.0fs" % (sh, sz/1e6, time.time()-t0))
    except Exception as e:
        log("index 解析失败: %s" % str(e)[:120])
else:
    log("❌ 拿不到 index.json")

# ③ 实测加载显存（不训练）
log("实测 bf16 加载显存")
try:
    import torch
    from transformers import Qwen2VLForConditionalGeneration
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    t0 = time.time()
    m = Qwen2VLForConditionalGeneration.from_pretrained(
        "models/qwen2vl7b", torch_dtype=torch.bfloat16, device_map="cuda",
        low_cpu_mem_usage=True)
    log("加载成功 %.0fs ｜ 显存 %.2f GB ｜ 峰值 %.2f GB"
        % (time.time()-t0, torch.cuda.memory_allocated()/2**30,
           torch.cuda.max_memory_allocated()/2**30))
    n = sum(p.numel() for p in m.parameters())/1e9
    log("参数量 %.2f B" % n)
except Exception as e:
    log("❌ 加载失败: %s" % str(e)[:250])
log("PROBEDONE")
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--start-small", action="store_true")
    ap.add_argument("--probe-7b", action="store_true")
    a = ap.parse_args()

    from _cloud_ssh import bg, client, run

    c = client()
    try:
        if a.write or a.start_small or a.probe_7b:
            io.open(REPO / "outputs" / "_remote_big.py", "w", encoding="utf-8",
                    newline="\n").write(Q_SMALL)
            io.open(REPO / "outputs" / "_remote_7b.py", "w", encoding="utf-8",
                    newline="\n").write(PROBE_7B)
            sftp = c.open_sftp()
            sftp.put(str(REPO / "outputs" / "_remote_big.py"), f"{WORK}/_big.py")
            sftp.put(str(REPO / "outputs" / "_remote_7b.py"), f"{WORK}/_probe7b.py")
            sftp.close()
            print("  ✅ 已上传队列脚本（_big.py / _probe7b.py）")
        if a.start_small:
            print("=== 启动 Q1–Q4（脱离运行）===")
            bg(c, f"{PY} _big.py", "outputs_big.log")
        if a.probe_7b:
            print("=== 启动 7B 探测（脱离运行；含下载）===")
            bg(c, f"{PY} _probe7b.py", "outputs_probe7b.log")
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
