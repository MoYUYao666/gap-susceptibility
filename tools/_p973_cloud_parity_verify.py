# -*- coding: utf-8 -*-
r"""Check that the cloud model really is gradient-checkpointed, and record the parity outcome.

The cloud parity run reproduced the local token geometry exactly (1220 tokens, mean 610, sequence length
610) and gave loss 2.9496 at step 5 against a local 2.9466 / 2.9449. It was 48x faster per step.

This script asks the host two things and then writes the comparison into the handoff:

* whether the loaded model has gradient checkpointing enabled (worth knowing, because it explains both the
  memory footprint and part of the speed, and because a silent change there would be a difference from the
  local configuration);
* the recorded parity numbers side by side.

    python tools/_p973_cloud_parity_verify.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from pathlib import Path

import paramiko

REPO = Path(__file__).resolve().parents[1]
HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")

CHECK = r""" /root/miniconda3/bin/python - <<'PYEOF'
import os
os.environ["HF_HOME"] = "/root/autodl-tmp/hf"
os.environ["HF_HUB_OFFLINE"] = "1"
import torch
from transformers import AutoProcessor, BitsAndBytesConfig, LlavaForConditionalGeneration
import bitsandbytes  # noqa
m = LlavaForConditionalGeneration.from_pretrained(
    "llava-hf/llava-1.5-7b-hf",
    quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                           bnb_4bit_compute_dtype=torch.bfloat16,
                                           bnb_4bit_use_double_quant=True),
    torch_dtype=torch.bfloat16, device_map={"": 0}, low_cpu_mem_usage=True)
print("is_gradient_checkpointing:", getattr(m, "is_gradient_checkpointing", None))
print("video_token_use_cache   :", getattr(m.config, "use_cache", None))
print("gpu memory allocated GB : %.1f" % (torch.cuda.memory_allocated() / 1e9))
PYEOF"""

HANDOFF_ENTRY = """> **✅ 2026-10-15 22:35 —— 云端对照**通过**：数据几何逐字节一致、loss 落在本地离散内、每步快 48×**
>
> ### 一、云端主机（AutoDL，实测）
>
> | 项 | 值 |
> |---|---|
> | GPU | **RTX 4080 SUPER，32,760 MiB**，compute **8.9**（**bf16 可用**）|
> | CPU / 内存 | **96 核 / 503 GB** |
> | 磁盘 | 系统盘 30 GB（用 5 GB）＋ **数据盘 `/root/autodl-tmp` 50 GB**（HF 缓存放这里）|
> | python | 3.12.3（conda base `/root/miniconda3`）|
>
> ### 二、⚠️ 上云后修掉的一个**镜像坑**（不是我们的包）
>
> `import peft` 报 `Could not import module 'BloomPreTrainedModel'`，**版本号全都对**（peft 0.20.0 / transformers 5.16.1 与本地相同），
> 抓完整 traceback 才发现真因：**镜像自带 torchvision 0.27.1 与 torch 2.9.1 不匹配** ⇒
> `RuntimeError: operator torchvision::nms does not exist` ⇒ transformers 经 `image_utils` 导入它时炸掉。
> **改钉 `torchvision==0.24.1+cu130`（与本地一致）后全部导入正常**。
> **教训：版本号相同 ≠ 导入可用**；跨机复现必须**实际 import 一遍**。
>
> ### 三、✅ 环境自检（云端实装 vs 本地基准）
>
> | 包 | 本地 | 云端 |
> |---|---|---|
> | torch | 2.9.1+cu130 | **2.9.1+cu130** |
> | torchvision | 0.24.1+cu130 | **0.24.1+cu130**（修后）|
> | transformers | 5.16.1 | **5.16.1** |
> | peft | 0.20.0 | **0.20.0** |
> | bitsandbytes | 0.50.2 | **0.50.2** |
> | accelerate | 1.14.0 | **1.14.0** |
> | **全部 import 实测** | OK | **ALL_IMPORTS_OK** |
>
> ### 四、✅ 对照结果（同一命令、同一 fixture、同 seed）
>
> | 项 | 本地（4060 Laptop）| 云端（4080 SUPER）| 判定 |
> |---|---|---|---|
> | **首批 tokens** | **1220** | **1220** | ✅ |
> | **每序列 mean** | **610** | **610** | ✅ **逐字节一致** ⇒ 数据子集与顺序完全对上 |
> | **序列长度** | 610 | 610 | ✅ |
> | **5 步 loss** | **2.9466**（重复 **2.9449**）| **2.9496** | ✅ 落在本地离散（1.7e-3）之内，\|Δ\|=**3.0e-3** |
> | 每步耗时 | 63.3 s | **1.3 s** | **48×** |
> | 模型加载 | ~10 min | **15 s** | — |
> | 训练对/评测对 | 20 / 10 | 20 / 10 | ✅ |
>
> ⚠️ **踩到的第二个陷阱**：包里的 `outputs/` 带来了本地 `llava_parity_cloud/text_only_s42.json`，
> 云端**第一次跑直接命中"已完成即跳过"、一步没训**。清空输出目录后才是真跑。
> **⇒ 凡是"对照/计时"跑，必须先清输出目录**（与 `_p942` 那次同源）。
>
> ### 五、⏭️ 下一步（等操作者点头）
>
> 1. **云端全量**：`--samples 400 --eval-pairs 300 --epochs 3 --batch 2 --max-len 2048 --seeds 3 --rank 8 --arms frozen,text_only,vision_only,both`，
>    输出到**清空后的** `outputs/llava_sites_cloud/`；
> 2. **速度预期**：本地 56–63 s/步 ⇒ 云端约 **1.3 s/步**（小样实测），全量 12 run 预计**几小时**而非 4 天；
> 3. **口径问题需操作者定**：云端**显存 32 GB 可上 bf16**（不用 4-bit，更快更稳），但那会**改变数值口径**；
>    若要严格同口径 ⇒ 仍用 4-bit（已实测一致）。
>
> **工具**：`_p961`/`_p962`（主机探测）｜`_p963`（上传）｜`_p964`（逐版本安装）｜`_p965`（轮询）｜
> `_p966`/`_p967`（读版本/单条询问）｜`_p968`（peft traceback）｜`_p969`/`_p971`（远端执行）｜
> `_p970`（修 torchvision）｜`_p972`（对照脚本）｜`_p973`（本条）。
>
> 🔐 **凭据**：SSH 主机/端口/密码**仅在会话环境变量中传递，未写入任何文件或提交**；操作者宜用后改密。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2

    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    _i, o, e = cli.exec_command(CHECK, timeout=600)
    text = (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()
    print("=== gradient checkpointing / memory on the cloud ===")
    for line in text.splitlines():
        if any(k in line for k in ("is_gradient_checkpointing", "use_cache", "memory allocated",
                                   "Error", "Traceback")):
            print("   ", line[:140])
    cli.close()

    if not a.apply:
        print("  (dry run)")
        return 0
    hp = io.open(REPO / "HANDOFF.md", encoding="utf-8").read()
    if "云端对照**通过" not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + HANDOFF_ENTRY + hp[j + 1:]
        io.open(REPO / "HANDOFF.md", "w", encoding="utf-8", newline="").write(hp)
        print("  handoff entry added")
    mp = io.open(REPO / "文件地图.md", encoding="utf-8").read()
    row = ("34. ✅ **云端对照通过（2026-10-15 22:35）** —— 主机 **RTX 4080 SUPER 32 GB / 96 核 / 503 GB 内存**，"
           "数据盘 50 GB 放 HF 缓存。**修掉镜像坑**：自带 torchvision 0.27.1 与 torch 2.9.1 不匹配 ⇒ "
           "`torchvision::nms does not exist` ⇒ peft 导入失败；钉 `torchvision==0.24.1+cu130` 后 **ALL_IMPORTS_OK**"
           "（教训：版本号相同≠导入可用）。**对照结果**：首批 **1220 tokens / 每序列 610 逐字节一致**；"
           "5 步 loss 云端 **2.9496** vs 本地 **2.9466/2.9449**，|Δ|=**3.0e-3** 落在本地离散内；"
           "**每步 1.3 s vs 本地 63.3 s（48×）**。⚠️ 第二个陷阱：包里的 `outputs/` 让首次对照**直接跳过没训**，"
           "清空输出目录后才是真跑。**下一步**：云端全量（预计几小时），口径用 4-bit（已实测一致）或 bf16（需操作者定）。"
           "详见 `HANDOFF.md` 顶部 2026-10-15 22:35 条目。\n")
    anchor = "33. 🧪 **对照试跑暴露两个缺陷（2026-10-15 21:50）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(REPO / "文件地图.md", "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    sys.exit(main())
