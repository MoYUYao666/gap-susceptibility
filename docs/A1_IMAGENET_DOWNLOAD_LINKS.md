# A1 补种子所需：ImageNet-1k 验证集分片下载链接

目标仓库：`ILSVRC/imagenet-1k`（dataset，**gated** → 无 token 会 401/403）

需要 **14 个 parquet**（≈6.4 GB，覆盖 50,000 张验证图），放到 `data/imagenet_hf/`。

文件名模式：`validation-000XX-of-00014.parquet`（HF 官方 parquet 转换的验证集分片）。


## 1. 官方直链（需登录/带 token，否则 401）

```
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00000-of-00014.parquet?download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00001-of-00014.parquet?download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00002-of-00014.parquet?download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00003-of-00014.parquet?download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00004-of-00014.parquet?download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00005-of-00014.parquet?download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00006-of-00014.parquet?download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00007-of-00014.parquet?download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00008-of-00014.parquet?download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00009-of-00014.parquet?download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00010-of-00014.parquet?download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00011-of-00014.parquet?download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00012-of-00014.parquet?download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00013-of-00014.parquet?download=true
```

## 2. hf-mirror 镜像（免登录；gated 仓库可能 403）

```
https://hf-mirror.com/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00000-of-00014.parquet
https://hf-mirror.com/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00001-of-00014.parquet
https://hf-mirror.com/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00002-of-00014.parquet
https://hf-mirror.com/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00003-of-00014.parquet
https://hf-mirror.com/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00004-of-00014.parquet
https://hf-mirror.com/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00005-of-00014.parquet
https://hf-mirror.com/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00006-of-00014.parquet
https://hf-mirror.com/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00007-of-00014.parquet
https://hf-mirror.com/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00008-of-00014.parquet
https://hf-mirror.com/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00009-of-00014.parquet
https://hf-mirror.com/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00010-of-00014.parquet
https://hf-mirror.com/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00011-of-00014.parquet
https://hf-mirror.com/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00012-of-00014.parquet
https://hf-mirror.com/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00013-of-00014.parquet
```

## 3. 若上面 401/403：用 token 拼链接（把 <TOKEN> 换成自己的 hf_... ）

```
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00000-of-00014.parquet?token=<TOKEN>&download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00001-of-00014.parquet?token=<TOKEN>&download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00002-of-00014.parquet?token=<TOKEN>&download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00003-of-00014.parquet?token=<TOKEN>&download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00004-of-00014.parquet?token=<TOKEN>&download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00005-of-00014.parquet?token=<TOKEN>&download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00006-of-00014.parquet?token=<TOKEN>&download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00007-of-00014.parquet?token=<TOKEN>&download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00008-of-00014.parquet?token=<TOKEN>&download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00009-of-00014.parquet?token=<TOKEN>&download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00010-of-00014.parquet?token=<TOKEN>&download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00011-of-00014.parquet?token=<TOKEN>&download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00012-of-00014.parquet?token=<TOKEN>&download=true
https://huggingface.co/datasets/ILSVRC/imagenet-1k/resolve/main/data/validation-00013-of-00014.parquet?token=<TOKEN>&download=true
```

## 4. 先在浏览器里确认文件清单（能打开说明有权限）

```
https://huggingface.co/datasets/ILSVRC/imagenet-1k/tree/main/data
https://hf-mirror.com/datasets/ILSVRC/imagenet-1k/tree/main/data
```

## 5. 放好之后（本机可自动跑完）

```bash
ls data/imagenet_hf/*.parquet | wc -l     # 应为 14
bash tools/a1_supplement_seeds.sh        # 自动：8 次训练 + 端点评测 + 早停曲线
```

## 6. 本机网络实测（2026-09-14）

- `huggingface.co:443` ❌ 超时、`hf-mirror.com:443` ❌ 超时（HF 系域名被阻断）
- `github.com:443` ✅、`modelscope.cn:443` ✅、`baidu.com:443` ✅
- → 所以本机**无法直连重下**，必须走能连 HF 的通道（迅雷/代理/另一台机器）
- 备选：魔搭（modelscope.cn，本机连通）——线索见 <https://www.selectdataset.com/dataset/33a583e7d0c9f04eca2d546e9252a1fa>，dataset id 待核实
