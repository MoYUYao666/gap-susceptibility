# 精确环境与复现说明（2026-10-09）

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
| `torch` | `2.9.1+cu130` |
| `torchvision` | `0.24.1+cu130` |
| `transformers` | `5.16.1` |
| `peft` | `0.20.0` |
| `tokenizers` | `0.23.2` |
| `huggingface_hub` | `1.30.0` |
| `safetensors` | `0.8.0` |
| `accelerate` | `1.14.0` |
| `numpy` | `2.5.2` |
| `tqdm` | `4.70.0` |
| `scipy` | `1.18.1` |
| `matplotlib` | `3.11.1` |

GPU：NVIDIA GeForce RTX 4060 Laptop（8 GB）
Python：3.12.14

## 已知不兼容

| 包 | 版本 | 症状 | 证据 |
|---|---|---|---|
| `transformers` | 5.19.0（实测：R@1=0.002、loss 卡在 ln(128)、初始 cosine_separation=0；同代码在 5.16.1 上 R@1=0.685） | 训练失效 | `outputs/analysis/side_by_side.json` |

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
