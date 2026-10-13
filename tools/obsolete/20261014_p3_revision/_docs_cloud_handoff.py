# -*- coding: utf-8 -*-
r"""落账：云端托管方案就绪（2026-10-09 11:15）。

    python tools\_docs_cloud_handoff.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **☁️ 2026-10-09 11:15 —— 剩余实验改**云端托管**：部署包与 runbook 已就绪**
>
> ### 动机（操作者提议"跑云端"）
>
> 本地是 **8 GB 共享卡**，单 run 峰值 **7.9 GB（96%）** → **会占满、影响共用人**；
> 且 `both` 臂 **55 min–3 h/run** → 剩余 14 缺口需 **15–40 h**。
> 云端 runbook 实测为 **RTX 4080 SUPER 16 GB**（`docs/CLOUD_RUNBOOK.md`），**余量充足且更快**。
>
> ### ⚠️ 一个必须先说清的限制
>
> **我无法从这里直接驱动云端**：
> - SSH 配置里**没有云端主机**（只有 `192.168.1.103` 与 `github.com`）；
> - `192.168.1.103` **实测不可达**（`Test-Connection` 失败）。
>
> **→ 需要操作者：① 连上 autodl 实例；② 把实例 SSH 信息给我（或自行照 runbook 执行）。**
>
> ### 已交付（**本会话可直接使用**）
>
> | 交付件 | 内容 |
> |---|---|
> | **`cloud_pack/`** | **58 文件 ｜ 0.4 MB**（`src/`、`experiments/`、`tools/audit/`、3 个关键脚本、`requirements.txt`、`configs/`）——**不含模型、不含数据** |
> | **`cloud_pack/manifest.txt`** | 逐文件大小清单，便于核对上传完整性 |
> | **`docs/CLOUD_SEEDS_RUNBOOK.md`** | **168 行可照抄命令**：上传 → 环境 → **数据（服务器端取）** → **模型（服务器端下载 + patch size 校验）** → 跑 seed（幂等）→ `Γ_m` → 回传核对 → 成本与风险 |
>
> ### runbook 里的两条硬规则（来自项目既有约定）
>
> 1. **模型一律服务器端下载**（ModelScope 优先，HF 镜像兜底）——**禁止本地下载后上传**；
> 2. **数据不上传**：Flickr30k 在服务器用 `curl` 取。
>
> **并强制"下载后校验 patch size"**——本项目曾因静默替换踩过坑（ModelScope 默认拉 flax 权重）。
>
> ### 关键路径（与本地一致，避免云端路径分歧）
>
> | 项 | 值 |
> |---|---|
> | 数据 | `./flickr30k/flickr30k-images/flickr30k_images/`（31,783 张）+ `captions.txt` |
> | 注意 | `src/dataset.py` 用 `data_dir + "flickr30k"` 拼路径 → `--data-dir .` 时读 `./flickr30k/` |
> | 模型 | `models/clip-vit-base-patch32`、`models/clip-vit-base-patch16`、`models/openclip` |
> | 输出 | `outputs/strict_freeze_{b32_r4,b16/r4,oclip/r4}` |
>
> ### 云端执行顺序（runbook §5–§6）
>
> ```
> python tools/_p56_add_seeds.py --apply        # 幂等，跳过已有；跑完自动接 Γ_m
> python tools/_p58_gamma_clip.py --apply       # 单独跑 Γ_m（~10 min）
> ```
>
> ### 回传后本地要做
>
> `tools/_p59_seed_stability.py`（排序稳定性 + 逐臂 sd）→ `tools/_claim_ledger.py`（门禁）。
> **判据已预写**：**若某骨干排序翻转 → 必须如实报告并降级该结论。**
>
> ### 本轮**本地已释放**（不再占共享资源）
>
> python 进程 0 ｜ **GPU 524 / 8188 MiB（19%）**
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "剩余实验改**云端托管**" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("剩余实验改**云端托管**", "58 文件 ｜ 0.4 MB", "无法从这里直接驱动云端",
              "CLOUD_SEEDS_RUNBOOK.md", "若某骨干排序翻转"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")

    mp = REPO / "文件地图.md"
    m = io.open(mp, encoding="utf-8").read()
    if "0R." not in m:
        add = """
**0R. ☁️ 剩余实验改云端托管：部署包 + runbook 已就绪（2026-10-09 11:15）**

- **动机**：本地 8 GB 共享卡，单 run 峰值 7.9 GB（96%）→ 占满且影响共用人；剩余 14 缺口需 15–40 h。
- **交付件**：`cloud_pack/`（**58 文件 0.4 MB**，仅代码）｜ `cloud_pack/manifest.txt` ｜ **`docs/CLOUD_SEEDS_RUNBOOK.md`（168 行可照抄命令）**。
- **硬规则**：模型**服务器端下载**（ModelScope 优先）+ **下载后校验 patch size**；**数据不上传**。
- ⚠️ **我无法从这里驱动云端**（SSH 无云端主机；`192.168.1.103` 不可达）→ **需操作者提供实例接入方式或自行执行**。
- **本地已释放**：python 进程 0 ｜ GPU 524 MiB。
- **回传后**：`_p59_seed_stability.py` → `_claim_ledger.py`；**判据：排序若翻转必须如实报告并降级**。

"""
        anchor = "## 七、当前真正待办（按优先级）\n"
        m2 = m.replace(anchor, anchor + add, 1)
        io.open(mp, "w", encoding="utf-8", newline="").write(m2)
        print(f"  ✅ 文件地图.md 已更新（{len(m2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
