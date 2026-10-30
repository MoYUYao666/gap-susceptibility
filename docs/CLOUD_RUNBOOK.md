# 云端从 0 部署 Runbook（autodl / 单卡 80GB）——paper_ap3 云端补强

> 目标：只用云端做**本地做不到**的 4 件事，其余一律不要重复跑（本地已完成 A1–A10，见 `docs/TIER_A_DRAFT.md`）。
> 本文件所有命令都在**本地实测过同款代码路径**（Qwen 脚本用 2B 模型跑通、成本探针用 LLaVA-7B/Qwen-2B 跑通），并且已把两个会在云端"第一次就挂"的坑预先修掉（见 §6）。

## 0. 云端要做的 4 件事（按价值排序）

| # | 交付物 | 对应局限 | 命令 | 规模 | 预计 |
|---|---|---|---|---|---|
| **C1** | **Qwen2-VL-7B 的"投影器 vs LLM"不对称秩**（7B 侧唯一真正缺口；LLM 块级 uniform/theory/violation 已有 3 seeds 存档） | 局限 1 | §7.1 | 9 run | ~20 min |
| **C2** | **Γ 测量的绝对成本**（>7B：峰值显存 / 墙钟 / 相对训练步比值） | 局限 10 | §7.2 | 2–3 | ~15 min |
| **C3** | **协议统一**：解码器侧按双塔协议（10 epochs + 5 seeds，batch=1） | 局限 8 | §7.3 | 15 run | **~30–60 min**（实测；旧估 3–5 h 基于本地慢机） |
| **C4** | batch 轴（实测上限 batch 2） | 局限 14 | §7.4 | 2 run | ~5 min |
| **C5** | batch 4/8 的 OOM 记录（设备约束证据） | 局限 14 | §7.5③ | 2 run | ~2 min |

> C1/C2/C4/C5 都在半小时内；C3 按 §1.0 实测也只约 1 小时，不必再"留夜里"。真正的风险不是算力而是**丢数据**（旧脚本只在收尾写 JSON）——已由逐 epoch 落盘 + 单格 timeout 解决。

## 1.0 实测硬件（2026-09-13 实际用的那台，**以此为准**）

来源：实例上跑完的 C2 探针产物 `outputs/gamma_cost_{llava_llava-1.5-7b-hf,qwen_Qwen2-VL-7B-Instruct}.json`。

| 项 | 实测 | 与规划假设的差异 |
|---|---|---|
| GPU | **NVIDIA GeForce RTX 4080 SUPER，显存 16 GB** | ⚠️ 规划假设是 vGPU-32GB → **实际只有 16 GB**，这是 10-epoch 跑到 ep9 OOM 的根因 |
| torch | 2.12.1+cu130 | 规划里担心的 bitsandbytes ABI 风险**没有发生**：4-bit 加载正常，**无需降级到 2.9.1** |
| transformers | 5.16.1 | ✅ 与分析脚本一致 |
| 可训练 float 参数 | LLaVA 264.46 M / Qwen2-VL-7B 1.092 B | 已计入 C2 |

显存与速度（**batch = 1**）：

| 模型 | 载入后 | 训练步峰值 | Γ 峰值 | 训练步 | Γ 合计 | Γ / 训练步 |
|---|---|---|---|---|---|---|
| LLaVA-1.5-7B | 4.04 GB | **7.66 GB** | 7.52 GB | 0.412 s | 0.750 s | **1.82×** |
| Qwen2-VL-7B | 5.90 GB | **8.94 GB** | 7.80 GB | 0.372 s | 0.527 s | **1.418×** |

**由实测推出的三条硬规则**：
1. 显存上限 **batch = 2**（batch 1 训练步已占 7.66/8.94 GB）→ 10-epoch 的 C3 一律 `--batch-size 1`，C4 测 batch 2，C5 把 batch 4/8 的 OOM 记为设备约束。
2. 一个 epoch ≈ 16 步 × 0.412 s + 4 次 Γ × 0.750 s ≈ **9.6 s** → 一次 10-epoch 运行约 **2 分钟**，C3 全部 15 格约 **30–60 分钟**（旧文档里"4–8 h"是基于本地 8 GB 慢机的估算，作废）。
3. ep7–9 发散/NaN 是协议在该预算下的**预期行为**（A8 结果），必须逐 epoch 落盘，不能只在收尾写 JSON。

> §1.1 是当初的**规划假设**（vGPU-32GB），保留作对照；凡与 §1.0 冲突处一律以 §1.0 实测为准。

## 1. 实例与镜像
- **GPU**：A800/A100 **80GB** 单卡（C3 需要大显存；C1/C2/C4 40GB 也够）。
- **镜像**：autodl「PyTorch 2.x + CUDA 12.x」基础镜像（不要选 CUDA 11）。
- **磁盘**：≥ 200 GB（Qwen2-VL-7B ≈ 16 GB、LLaVA-1.5-7B ≈ 15 GB、可选 32B ≈ 65 GB）。

### 1.1 vGPU-32GB ×1 / 12 核 / 62GB 内存 / 系统盘 30GB / 数据盘 50GB 是否够用？（原始规划假设）

| 资源 | 需求 | 判定 |
|---|---|---|
| **显存 32 GB** | C1（Qwen2-VL-7B 4-bit，20 样本、batch 1，Qwen 336px≈144 image token）：峰值约 6–10 GB；C2：7B 约 8–12 GB；C4（LLaVA batch 4/8）：约 8–16 GB；C3（LLaVA-7B 10 epoch，batch 8）：约 12–20 GB | ✅ **够**（batch 16 是否可行要在冒烟里试；本机 8 GB 在 LLaVA batch 4 就 OOM，32 GB 下 batch 8 基本稳） |
| **系统盘 30 GB** | 镜像自带的 torch/CUDA + pip 依赖 ≈ 10–15 GB | ⚠️ **够但要管住缓存**：**必须把 HF/ModelScope 缓存重定向到数据盘**（见下方 §1.2），否则下载 7B 模型时系统盘会先满 |
| **数据盘 50 GB** | Qwen2-VL-7B 16.6 GB + LLaVA-1.5-7B 15 GB ≈ **32 GB**，加输出 JSON（极小） | ✅ **够（仅这两个 7B 模型）**；❌ **放不下 Qwen2.5-VL-32B（≈65 GB）** → C2 的可选大模型档请放弃，或另开大盘实例 |
| **内存 62 GB** | 数据 23 MB，模型加载缓冲几 GB | ✅ 富余 |
| **CPU 12 核** | 脚本是 GPU-bound，CPU 只做 tokenize/加载 | ✅ 够 |
| **算力** | vGPU 32GB 是**虚拟化切片**（显存 32 GB，但吞吐低于整卡 A800） | ⚠️ C1/C2/C4 无影响；**C3（15 run）预计 4–8 h**，建议放夜里 |

**结论：够用。** 唯一硬约束是"**数据盘只放两个 7B 模型 + 缓存必须指到数据盘**"。

### 1.2 开工前 30 秒必做（不做这一步最容易浪费时间）
```bash
df -h / /root/autodl-tmp          # 确认系统盘剩余 ≥8GB、数据盘剩余 ≥35GB
mkdir -p /root/autodl-tmp/{hf,modelscope,tmp,models}
cat >> ~/.bashrc <<'EOF'
export HF_HOME=/root/autodl-tmp/hf
export MODELSCOPE_CACHE=/root/autodl-tmp/modelscope
export TMPDIR=/root/autodl-tmp/tmp
export KMP_DUPLICATE_LIB_OK=TRUE
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_DISABLE_XET=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
EOF
source ~/.bashrc
```
- 模型一律下到 **`/root/autodl-tmp/models/...`**（数据盘），**不要**下到 `/root/`（系统盘）。
- 若数据盘吃紧：先跑 C1+C2（只需 Qwen2-VL-7B 一个模型），跑完 `rm -rf` 再下 LLaVA 做 C3/C4。
- 训练产出的 JSON 只有几 KB，随便放；**不要**把模型权重或 checkpoint 存到系统盘。

## 2. 环境（版本必须对齐，否则 4-bit + peft 会以奇怪方式失败）

### 2.0 镜像版本怎么选（按优先级）
本地全部验证跑在 **Python 3.12 + torch 2.9.1+cu130 + transformers 5.16.1 + peft 0.20.0 + bitsandbytes 0.50.2** 上。

| 镜像项 | 建议 | 说明 |
|---|---|---|
| Python | **3.12** | 与本地一致 ✅ |
| CUDA | **13.0** | 与本地 `+cu130` 一致 ✅（该镜像存在即代表宿主驱动支持） |
| PyTorch | **优先 2.9.x**；只提供 2.12.1 之类的新版本也能用 ⚠️ | 唯一有兼容风险的是 **bitsandbytes 4-bit**（对 torch/CUDA ABI 敏感）；torch 版本本身不影响训练脚本 |
| Ubuntu | 22.04 | 无影响 ✅ |

**决策规则**：镜像列表里若有 `PyTorch 2.9.x + CUDA 13.0 + Python 3.12` 就直接选（零风险）；若只有 `2.12.1`，先照常装并**跑冒烟 S0/S1**：
- 通过 → 继续，无需改动；
- 若 `import bitsandbytes` 或 4-bit 加载报错 → 在同一环境降到本地验证版本（**代码不用改**）：
```bash
pip install "torch==2.9.1" "torchvision==0.24.1" --index-url https://download.pytorch.org/whl/cu130
pip install "transformers==5.16.1" "peft==0.20.0" "bitsandbytes==0.50.2" "datasets==5.0.1"
python -c "import torch, bitsandbytes as b; print(torch.__version__, torch.cuda.is_available(), b.__version__)"
```
- 若 CUDA 13 完全不可用（`torch.cuda.is_available()` False 或驱动 insufficient）→ 换 **CUDA 12.1/12.4** 镜像，并**成对**安装 cu12x 的 torch 与匹配的 bitsandbytes 轮子；**绝不混装**（cu12x torch + cu130 bnb 必崩）。
- 参考：[bitsandbytes 0.50.2 排障](https://huggingface.co/docs/bitsandbytes/v0.50.2/errors)、[PyPI bitsandbytes](https://pypi.org/project/bitsandbytes/)

```bash
python -m pip install -U pip
pip install "transformers==5.16.1" "peft==0.20.0" "bitsandbytes==0.50.2" "datasets==5.0.1" \
            pandas pyarrow pillow scipy matplotlib accelerate modelscope
python -c "import torch, transformers, peft, bitsandbytes as bnb; \
print(torch.__version__, torch.cuda.is_available(), transformers.__version__, peft.__version__, bnb.__version__)"
# 期望: torch 2.x + True + transformers 5.16.1 + peft 0.20.x + bitsandbytes 0.50.x
export KMP_DUPLICATE_LIB_OK=TRUE
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_DISABLE_XET=1
```
**说明**：torch 用镜像自带的即可（版本选择见 §2.0）；`transformers` 必须是 **5.x**（本地全部验证都在 5.16.1 上；分析脚本按 5.x 的模块命名写）。bitsandbytes 轮子若报 CUDA 不匹配，按报错提示换 `bitsandbytes==0.50.2` 对应的 cu12x 轮子。

## 3. 代码
```bash
git clone https://github.com/MoYUYao666/gap-susceptibility.git
cd gap-susceptibility
git log --oneline -1     # 应看到 Tier A 系列提交（8faa115 / 42e6de7 / 40706f4 或更新）
```
- 仓库若为私有：用 `https://<PAT>@github.com/...` 或在 autodl 控制台配置 SSH key；实在不行就在本地打包工作区（**排除** `models/`、`data/`、`envs/`、`.worktrees/`、`*.parquet`）后上传解压。

## 4. 数据（只需一个 23 MB 文件；不需要任何图像）
```bash
# 上传 paper3/train-00000-of-00001-a09b74b3ef9c3b56.parquet 到 <repo>/paper3/
ls -lh paper3/train-*.parquet     # 两个训练脚本都按这个 glob 取数据
```
参考协议**只用空白/噪声图像**（脚本内生成），所以不需要图片目录、也不需要 Flickr/COCO/ImageNet。

## 5. 模型（**在服务器上下载，永远不要本地→上传**）
```bash
# Qwen2-VL-7B（ModelScope，国内快）
python -c "from modelscope import snapshot_download; \
           snapshot_download('Qwen/Qwen2-VL-7B-Instruct', local_dir='/root/Qwen2-VL-7B-Instruct')"
# LLaVA-1.5-7B（HF 镜像）
python -c "import os; os.environ['HF_ENDPOINT']='https://hf-mirror.com'; \
           from huggingface_hub import snapshot_download; \
           snapshot_download('llava-hf/llava-1.5-7b-hf', local_dir='/root/llava-1.5-7b-hf')"
# 可选（C2 的大模型档）: Qwen2.5-VL-32B-Instruct 或 InternVL2.5-8B
```

## 6. 冒烟门禁（**必须先全过，再跑正式实验**）
```bash
cd paper3/scripts
# S1  Qwen 基本路径（3 分钟内应出现 Saved）
python run_training_qwen.py --model-path /root/Qwen2-VL-7B-Instruct --epochs 1 --seed 42 --out-dir /tmp/smoke
# S2  投影器 LoRA 是否真的挂上（关键校验：日志必须出现 matched: >= 2；为 0 脚本会以 exit 2 退出）
python run_training_qwen.py --model-path /root/Qwen2-VL-7B-Instruct --epochs 1 --seed 42 \
       --proj-rank 4 --out-dir /tmp/smoke
# S3  Γ 成本探针（Qwen 与 LLaVA 各一次）
cd ../.. && python tools/gamma_cost_probe.py --arch qwen  --model-path /root/Qwen2-VL-7B-Instruct --n-samples 4
python tools/gamma_cost_probe.py --arch llava --model-path /root/llava-1.5-7b-hf --n-samples 4
# S4  LLaVA 训练脚本基本路径
cd paper3/scripts && python run_training.py --model-path /root/llava-1.5-7b-hf --epochs 1 --seed 42
```
**通过判据**
- S1/S2/S4 都出现 `E(0)=…` → `E(n)=…` → `Saved: …json`；S2 额外出现 `projector LoRA modules matched: N`（**N≥2**）。
- 日志里的 `Config=… pattern=…` 必须非空（`pattern` 为空而你以为设了块配置 = rank_pattern 没生效，结果不可用）。
- S3 打印的 JSON 含 `gamma_forward_seconds / gamma_backward_seconds / gamma_peak_vram_gb / gamma_over_train_step_time`。
**已知参照值（本地 4060 实测，用于判断量级是否荒谬）**
- LLaVA-1.5-7B：Γ 前向 3.88 s、反向 11.89 s（合计 15.76 s）、峰值 **7.59 GB**、训练步 10.90 s → 比值 **1.45×**。
- Qwen2-VL-2B：Γ 合计 0.95 s、峰值 2.91 GB、训练步 0.60 s → 比值 1.59×。
**归档参照（判断协议是否一致）**：Qwen2-VL-7B 在 `uniform / theory / violation`（rank 8 档）seed 42 的 ΔE 分别为 **+216 / +224 / +232**（3 epochs）；若你的 3-epoch 复跑偏离很大，先检查 transformers 版本与 `--block-config` 是否真的生效。

## 7. 正式命令

### 7.1 C1 — Qwen2-VL-7B 投影器/LLM 不对称秩（9 run ≈ 20 min）
```bash
cd paper3/scripts
Q=/root/Qwen2-VL-7B-Instruct
for s in 42 123 456; do
  # 仅投影器（不加注意力适配器；预期：投影器容量是弱杠杆）
  python run_training_qwen.py --model-path $Q --seed $s --proj-rank 4  --attn-targets none --tag projonly
  # 投影器高秩 + LLM 低秩
  python run_training_qwen.py --model-path $Q --seed $s --proj-rank 16 --llm-rank 2    --tag projhi16_llmlo2
  # 反向不对称（预期：灾难性）
  python run_training_qwen.py --model-path $Q --seed $s --proj-rank 2  --llm-rank 16   --tag projlo2_llmhi16
done
```
结果落在 `paper3/scripts/outputs/experiments/qwen_cf_uniform_rank8_seed<seed>_<tag>.json`（含 `proj_rank/llm_rank/trainable_params/delta_E`）。
**注意**：`--rank` 只影响文件名；LLM 侧秩由 `--llm-rank`（或 block-config）决定。

### 7.2 C2 — Γ 成本（2–3 条命令 ≈ 15 min）
```bash
cd <repo>
python tools/gamma_cost_probe.py --arch qwen  --model-path /root/Qwen2-VL-7B-Instruct --n-samples 4
python tools/gamma_cost_probe.py --arch llava --model-path /root/llava-1.5-7b-hf      --n-samples 4
# 可选大模型档（若下载了 32B）：同命令换 --model-path
```
产物：`outputs/gamma_cost_<arch>_<模型名>.json`（峰值显存、前向/反向秒、相对训练步比值、GPU/版本）。

**已跑完的实测结果（2026-09-13，RTX 4080 SUPER 16 GB）**：

| 模型 | 可训练 float 参数 | 载入后显存 | Γ 前向 | Γ 反向 | Γ 合计 | Γ 峰值 | 训练步 | 训练步峰值 | 比值 |
|---|---|---|---|---|---|---|---|---|---|
| LLaVA-1.5-7B | 264.46 M | 4.04 GB | 0.177 s | 0.573 s | 0.750 s | 7.52 GB | 0.412 s | 7.66 GB | **1.82×** |
| Qwen2-VL-7B | 1.092 B | 5.90 GB | 0.125 s | 0.401 s | 0.527 s | 7.80 GB | 0.372 s | 8.94 GB | **1.418×** |

> 这张表就是 C2 的交付物本体：**Γ 不是"额外跑一次前向"，而是训练步的 1.4–1.8 倍**（同一台机器、同一批量、同一 4-bit 设置），且两者峰值显存同阶——局限 10 的成本论证到此有 >7B 的实测支撑。

### 7.3 C3 — 协议统一（解码器侧 10 epochs + 5 seeds；15 run）

**首选：上传包里的 `c3_resume.sh`**（自动跳过已完成格子、单格 90 min 硬闸、逐格日志，可反复执行）：
```bash
cd /root/autodl-tmp/cloud_upload
nohup bash c3_resume.sh > /root/autodl-tmp/c3.log 2>&1 &      # 默认种子 42 123 456
tail -f /root/autodl-tmp/c3.log
# 补满 5 个种子： SEEDS="42 123 456 789 1024" nohup bash c3_resume.sh > /root/autodl-tmp/c3.log 2>&1 &
# 模型路径不同：  LLAVA_PATH=/root/llava-1.5-7b-hf bash c3_resume.sh
```

**或手敲（与脚本等价，但无跳过/无 timeout）**：
```bash
cd /root/autodl-tmp/cloud_upload/paper3/scripts
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
M=/root/autodl-tmp/models/llava-1.5-7b-hf
for s in 42 123 456 789 1024; do
  for r in 4 5 6; do
    timeout 5400 python run_training.py --model-path $M --rank $r --seed $s --epochs 10 --batch-size 1 \
      || echo "FAILED r=$r s=$s（继续下一个）"
  done
done
```
- **batch 用 1**：脚本在整个 epoch 累积梯度、每 epoch 只做 **1 次 `opt.step()`**，所以 batch 1 与 batch 8 的**优化步数完全相同**，差别只在梯度平均与显存；C3 要测的轴是 **epoch 预算**，不是 batch。batch 轴留给 C4/C5。这样也直接对齐论文参考协议（batch=1）。
- **batch 上限实测是 2**（§1.0：batch 1 训练步峰值 7.66 GB / 16 GB 显存）；**不要再为"更大的 batch"逐档重试**——旧脚本的 16→8→4→2 回退会把"ep9 发散"误判成 batch 问题，每档白烧一轮。
- `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` 必须设：10 epoch 跑到后期会发散（E 冲到 10³–10⁴），碎片化会把本可跑完的 run 顶成 OOM。
- **⚠️ 跑到 epoch 7–9 崩/OOM 是预期现象，不是环境坏了**：本地同协议 10-epoch 轨迹 r=6 在 ep7 塌缩、r=4/r=5 在 ep8 冲到 6925/5553 后 ep9 变 NaN。这段发散本身就是 A8（二阶 ODE）的证据，**必须保住前面每个 epoch 的 E**——因此 `run_training.py` 已加补丁：**每 epoch 写一次 `outputs/experiments/verify_r*_s*_b*_partial.json`**（`epochs_done` + 已测到的 `E` 序列），ep9 OOM 也只丢最后 1–2 个点。带 `_partial` 的文件**不参与任何统计**（本地分析工具已加排除）。
- 产物文件名会自动带 `_e10_...` 标签，不会覆盖既有结果；**不要**改 epochs（协议的核心是 10 epochs）。

### 7.4 C4 — batch 轴（实测上限是 batch 2，2 run ≈ 5 min）
```bash
cd paper3/scripts
for r in 5 6; do
  python run_training.py --model-path /root/autodl-tmp/models/llava-1.5-7b-hf \
      --rank $r --seed 42 --epochs 3 --batch-size 2
done
```
> `--epochs 3` 必须显式给出：该脚本的 `--epochs` 默认是 **1**，漏了就不是参考协议（这个坑在本地已经踩过一次）。
> **batch 4/8 在 16 GB 卡上放不下**（batch 1 训练步峰值已 7.66 GB，见 §1.0）——它们不再是"C4 的候选值"，而是 C5 的失败记录对象。

### 7.5 增量补跑（已跑过 C1/C2 的实例用这三块，勿重跑）
```bash
# ① C1b：Qwen-7B 追加第 4 个种子（n=3 -> n=4，3 run）
cd /root/autodl-tmp/cloud_upload/paper3/scripts
Q=/root/autodl-tmp/models/Qwen2-VL-7B-Instruct
python run_training_qwen.py --model-path $Q --seed 999 --proj-rank 4  --attn-targets none --tag projonly
python run_training_qwen.py --model-path $Q --seed 999 --proj-rank 16 --llm-rank 2    --tag projhi16_llmlo2
python run_training_qwen.py --model-path $Q --seed 999 --proj-rank 2  --llm-rank 16   --tag projlo2_llmhi16

# ② C2b：成本探针每模型重复 3 次（取中位数，消掉单次反向计时噪声）
cd /root/autodl-tmp/cloud_upload
for i in 1 2 3; do
  python tools/gamma_cost_probe.py --arch qwen  --model-path /root/autodl-tmp/models/Qwen2-VL-7B-Instruct --n-samples 4 --out outputs/gamma_cost_qwen7b_rep$i.json
  python tools/gamma_cost_probe.py --arch llava --model-path /root/autodl-tmp/models/llava-1.5-7b-hf     --n-samples 4 --out outputs/gamma_cost_llava7b_rep$i.json
done

# ③ C5：batch 上限探测（batch 4/8，r=6，3 epochs；OOM 本身就是设备约束证据）
cd /root/autodl-tmp/cloud_upload/paper3/scripts
for b in 4 8; do
  timeout 1800 python run_training.py --model-path /root/autodl-tmp/models/llava-1.5-7b-hf \
      --rank 6 --seed 42 --epochs 3 --batch-size $b \
    || echo "batch=$b FAILED —— 记为设备上限证据，不要再重试更大 batch"
done
```
增量块也可直接跑上传包里的脚本：`bash delta.sh all`（= C1b + C2b + C5，不触碰既有结果）。

## 8. 取回结果并入库

### 8.0 云块完成状态（2026-09-13 实测清点，同一台 RTX 4080 SUPER）

| 块 | 状态 | 盘上证据 |
|---|---|---|
| **C1** | ✅ **完成**（9 run = 3 seeds × 3 配置） | `paper3/scripts/outputs/experiments/qwen_cf_uniform_rank8_seed{42,123,456}_{pr4_tnone_projonly,pr16_lr2_projhi16_llmlo2,pr2_lr16_projlo2_llmhi16}.json` |
| **C2** | ✅ **完成**（每模型 1 次） | `outputs/gamma_cost_{llava_llava-1.5-7b-hf,qwen_Qwen2-VL-7B-Instruct}.json`（数值见 §7.2） |
| C1b | ⬜ 未做 | 待 `run_all_cloud.sh C1b`（seed 999） |
| C2b | ⬜ 未做 | 待 3 次重复取中位数 |
| C4 / C5 | ⬜ 未做 | 待 batch 2 / batch 4·8 上限记录 |
| **C3** | ⬜ **0 / 15** | 那轮卡在 ep9 的 10-epoch 运行**一格都没落盘**（v1 脚本只在收尾写 JSON）——已由逐 epoch 落盘补丁 + `c3_resume.sh` 解决 |
| 垃圾产物 | ⚠️ 存在 | `verify_r8_s42_..._e1_bcuniform.json` 是 `--epochs` 默认 1 那个 bug 留下的 1-epoch 产物，**任何统计都不得使用**；建议挪到 `outputs/_junk/` |

补齐剩余块的单一入口（上传包内）：
- **保留已完成结果、只补缺**：`nohup bash run_remaining.sh > /root/autodl-tmp/rest.log 2>&1 &`（C1b→C2b→C4→C5→C3→打包，≈1～1.5 h）
- **清盘全量重跑（要一套自洽结果时）**：先把旧结果 `mv` 到 `_v1_archive/`（勿 `rm`），再 `nohup bash run_all_clean.sh > /root/autodl-tmp/clean.log 2>&1 &`（smoke→C1→C1b→C2→C2b→C4→C5→C3(5 seeds)→pack，≈1.7–2.3 h；内置三道门禁：补丁存在、`experiments/` 为空、smoke 通过）

```bash
# 在服务器上打包（只带 JSON，体积很小；*_partial.json 会一并进来，别删——那是 A8 的轨迹数据）
cd <repo> && tar czf tier_a_cloud_results.tgz paper3/scripts/outputs/experiments/*.json outputs/gamma_cost_*.json
```
> 校验包内条目数：`tar tzf tier_a_cloud_results.tgz | wc -l`，并确认既有 `*e10*.json` 与新增 `*_partial.json` 都在。
本地（或直接在服务器上 clone+push）：
```bash
# 本地侧：把文件放回同名路径后
git worktree add --detach .worktrees/cloud origin/main
# 复制 JSON → worktree, 然后强制加入被 .gitignore 的 outputs/
git -C .worktrees/cloud add -f outputs/gamma_cost_*.json paper3/scripts/outputs/experiments/*.json
git -C .worktrees/cloud commit -m "cloud: Qwen-7B projector/LLM asymmetry + Gamma cost probe + protocol unification"
git -C .worktrees/cloud push ssh://git@github.com/MoYUYao666/gap-susceptibility.git HEAD:main
```
（本地推送走 SSH：`github.com:22` 可用；HTTPS 与 `ssh.github.com:443` 在本机不通。）

## 9. 排障表（按最可能出现的顺序）
| 症状 | 原因 | 处理 |
|---|---|---|
| `OSError: … no file named model.safetensors, or pytorch_model.bin, found in directory …` | **模型权重失踪**（2026-09-13 实际遇到）：两种成因——(a) 下载不全/被中断；(b) 目录里的权重是**指向 `hf/`、`modelscope/` 缓存的软链接**，缓存被清后链接断裂（config/tokenizer 是实体文件，所以目录看起来"还在"） | `du -sh <模型目录>` 判定：≈16 GB 说明权重在（查分片索引），只有几百 MB 说明丢了；`ls -la` 看到 `->` 即软链断裂。**在服务器上重下**（Qwen 用 ModelScope、LLaVA 用 hf-mirror），重下前不要再清缓存目录 |
| `ValueError: … mm_token_type_ids is missing` | transformers ≥5 需要该字段 | **已修**（脚本自动透传；若你用的是旧版仓库代码，`git pull` 到 `40706f4` 之后） |
| 块配置似乎没生效 / 结果与归档差距大 | `rank_pattern` 未匹配（peft 用 fullmatch 语义） | 看日志 `Config=… pattern=…` 是否非空；LLaVA 侧锚定 `language_model.layers.N`，Qwen 侧锚定 `layers.N` |
| `projector LoRA modules matched: 0` | merger 命名不同 | 先 `python -c "…print([n for n,_ in model.named_modules() if 'merger' in n])"` 找到名字，再用 `--proj-targets`（默认 `mlp.0,mlp.2`）覆盖 |
| CUDA OOM | batch 太大 / 碎片 | 降 batch；`export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` |
| bitsandbytes 报 CUDA 版本不匹配 | 轮子与驱动 CUDA 不一致 | 换对应 cu12x 轮子；或改用镜像自带 bnb 版本并保持 `transformers==5.16.1` |
| ModelScope/HF 下载慢 | 网络 | ModelScope 优先；HF 用 `HF_ENDPOINT=https://hf-mirror.com` + `HF_HUB_DISABLE_XET=1` |
| `KMP_DUPLICATE_LIB_OK` 相关崩溃 | OpenMP 重复 | `export KMP_DUPLICATE_LIB_OK=TRUE`（Qwen 脚本内已设，LLaVA 脚本内也已设） |

## 10. 边界（不要指望云端能补的）
- **>70B / MoE / 视频语言**：仍只能靠外推，本 runbook 的 C2 只到"7B 实测 + 可选 32B 实测"。
- **长文本生成 / 零样本分类作为目标任务**：需要新的评测线（生成式指标 + 人工/自动评估），不属于本次云端范围。
- **batch=128 的完整协议统一**：见 §7.3 的说明，只能用"能跑的最大 batch"逼近并在论文中如实标注。
