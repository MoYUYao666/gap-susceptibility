# -*- coding: utf-8 -*-
r"""生成 `docs/CLOUD_SEEDS_RUNBOOK.md`：云端跑剩余实验的**可照抄命令**（2026-10-09）。

    python tools\_p62_cloud_runbook.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "CLOUD_SEEDS_RUNBOOK.md"

DOC = r"""# 云端 Runbook：补 seed + `Γ_m` 完整测量（2026-10-09）

> 目的：把**本地 8 GB 共享卡跑不动**的剩余实验托管到云端。
> 本地单 run 峰值 **7.9 GB（96%）**，云端 runbook 实测为 **RTX 4080 SUPER 16 GB** 或 A800/A100。
>
> **只做两件事**：① 补 seed（14 个缺口）；② 完整 `Γ_m` 测量（~10 min）。**其余一律不在云端重复跑。**

---

## 0. 为什么值得上云

| 项 | 本地（RTX 4060 Laptop 8 GB，共享） | 云端（16 GB 起） |
|---|---|---|
| 单 run 峰值 | **7.9 GB → 占满，影响共用人** | 有充足余量 |
| `both` 臂单 run | **约 55 min – 3 h** | 显著更快 |
| 剩余量 | **14 缺口 → 15–40 h** | 按云端实测的加速比，**预计数小时** |

---

## 1. 上传代码（**只传代码，0.4 MB**）

本地已生成 `cloud_pack/`（58 文件，**不含模型、不含数据**）。

```bash
# 本地执行（把 <host> <port> 换成实例的 SSH 信息）
scp -P <port> -r cloud_pack/* root@<host>:/root/autodl-tmp/work/
```

**⚠️ 两条硬规则**（来自 `exp/README.md` 与 `AGENTS.md`）：

- **模型一律在服务器下载**（ModelScope 优先），**禁止本地下载后上传**；
- **数据不上传** → 见 §3。

---

## 2. 环境

```bash
cd /root/autodl-tmp/work
pip install -q -r requirements.txt
pip install -q peft modelscope
python -c "import torch, transformers, peft; print(torch.__version__, transformers.__version__)"
```

---

## 3. 数据（Flickr30k，服务器端取）

严格冻结 run 需要：`flickr30k/flickr30k-images/flickr30k_images/`（31,783 张）+ `captions.txt`。

```bash
cd /root/autodl-tmp/work
mkdir -p flickr30k && cd flickr30k

# 标注（13 MB）
curl -sL -o captions.txt "https://raw.githubusercontent.com/jbrownlee/Datasets/master/Flickr30k/flickr30k_images/results.csv" || true

# 若上面 404，用 Kaggle CLI（需 token）或你已有的镜像源
# 图片（4.2 GB，31,783 张）
# 来源与本地用的同一份；若云端已有该数据集，直接软链：
# ln -s /root/autodl-tmp/datasets/flickr30k flickr30k
```

**注意**：`src/dataset.py` 用 `data_dir + "flickr30k"` 拼路径，
故 `--data-dir .` 时它会读 `./flickr30k/`——**与本地一致**。

---

## 4. 模型（**服务器端下载**，ModelScope 优先）

```bash
cd /root/autodl-tmp/work
export MODELSCOPE_CACHE=/root/autodl-tmp/models
python - <<'PY'
from modelscope import snapshot_download
for mid, dst in [
    ("AI-ModelScope/clip-vit-base-patch32", "models/clip-vit-base-patch32"),
    ("AI-ModelScope/clip-vit-base-patch16", "models/clip-vit-base-patch16"),
    ("laion/CLIP-ViT-B-32-laion2B-s34B-b79K", "models/openclip"),
]:
    try:
        p = snapshot_download(mid, local_dir=dst)
        print("OK", mid, "->", p)
    except Exception as e:
        print("FAIL", mid, str(e)[:120])
PY
```

**若 ModelScope 上找不到某个 id**，退回 HF 镜像：

```bash
export HF_ENDPOINT=https://hf-mirror.com HF_HUB_DISABLE_X11=1
python -c "from huggingface_hub import snapshot_download; snapshot_download('openai/clip-vit-base-patch32', local_dir='models/clip-vit-base-patch32')"
```

**⚠️ 下载后必须校验 patch size**（防止静默替换，本项目踩过这个坑）：

```bash
python - <<'PY'
import torch
from transformers import CLIPModel
for p, want in [("models/clip-vit-base-patch32", 32),
                ("models/clip-vit-base-patch16", 16),
                ("models/openclip", 32)]:
    try:
        m = CLIPModel.from_pretrained(p, local_files_only=True)
        got = m.config.vision_config.patch_size
        n = sum(x.numel() for x in m.parameters()) / 1e6
        print(f"{p}: patch={got} params={n:.1f}M", "OK" if got == want else "MISMATCH")
    except Exception as e:
        print(p, "FAIL", str(e)[:100])
PY
```

---

## 5. 跑补 seed（**幂等**，已完成的自动跳过）

```bash
cd /root/autodl-tmp/work
nohup python tools/_p56_add_seeds.py --apply > outputs/_seeds_cloud.log 2>&1 &
tail -f outputs/_seeds_cloud.log
```

**它会依次跑**（3 骨干 × 3 臂 × seed 123,456）：

| 骨干 | 模型目录 | 输出目录 |
|---|---|---|
| CLIP B/32 r4 | `models/clip-vit-base-patch32` | `outputs/strict_freeze_b32_r4` |
| CLIP B/16 r4 | `models/clip-vit-base-patch16` | `outputs/strict_freeze_b16/r4` |
| OpenCLIP r4 | `models/openclip` | `outputs/strict_freeze_oclip/r4` |

**跑完后驱动会自动接 `Γ_m` 完整测量**（已在驱动尾部串联，见 `tools/_p60_chain_gamma.py`）。

---

## 6. 单独跑 `Γ_m`（若想先拿到）

```bash
python tools/_p58_gamma_clip.py --apply
# 产出 outputs/analysis/gamma_clip.json
```

---

## 7. 回来核对（**本地执行**）

```bash
# 把云端 outputs/ 里新增的 results.json 拉回本地对应目录后：
python tools/_p59_seed_stability.py --apply   # 排序稳定性 + 逐臂 sd
python tools/_p58_gamma_clip.py --apply       # 若本地也跑
python tools/_claim_ledger.py --apply         # 门禁
```

**判据（已预写）**：
- 补 seed 后**最保护臂不得翻转**；
- 若无翻转 → 结论加固；**若翻转 → 必须如实报告并降级该结论**；
- `Γ_m` 按 `tools/_p58` 输出判断**能否预测最优位置**，据此定论文口径（操作者选 A）。

---

## 8. 成本与风险

| 项 | 说明 |
|---|---|
| **显存** | 严格冻结 run 峰值 7.9 GB（本地 8 GB 卡的 96%）→ **16 GB 卡有充足余量**；若只有 8 GB，须**降 `--batch-size` 到 64** |
| **数据丢失** | 脚本**逐 run 写 `results.json`**，中断可续跑（幂等）；**但驱动把训练 stdout 缓冲在内存**（`capture_output=True`），运行中看不到逐 epoch 进度 |
| **上传量** | 代码 **0.4 MB**；模型与数据均服务器端获取 |
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write(DOC)
    t = io.open(OUT, encoding="utf-8").read()
    for k in ("scp -P <port>", "模型一律在服务器下载", "patch={got}", "幂等",
              "_p60_chain_gamma.py", "若翻转 → 必须如实报告"):
        assert k in t, f"断言失败：缺 {k}"
    print(f"  ✅ 已写 {OUT.relative_to(REPO)}（{len(t.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
