# -*- coding: utf-8 -*-
r"""Record that the rented host went away mid-sweep, and what was preserved.

    python tools/_p986_record_host_lost.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "云主机中途失联"

ENT = """> **🔌 2026-10-15 23:55 —— 云主机**中途失联**（sweep 到 step 650/2250）；本机已留存"一键重建"补丁**
>
> 操作者指令原本是：**「结果无误全部跑完之后直接关机」**。执行过程中出现意外：
> **SSH 端口 43746 变为不可达**（`Test-NetConnection` = False，**paramiko 重试 3 次全失败**），
> 说明**主机已不在运行**，而非网络抖动。
>
> ### 一、🔍 失联时云端的状态（最后一条实测，23:38）
>
> | 项 | 值 |
> |---|---|
> | 运行 | bf16 全量 sweep，**step 650/2250**（`text_only_s42`）|
> | loss | **0.796**（step 25 时 1.5498 ⇒ 正常下降）|
> | 速度 | **0.9 s/步**，首 run ETA **00:09** |
> | 显存 | 29,950 / 32,760 MiB（92%）|
> | **12 run 全部完成预计** | **约 2 小时**（≈01:40）⇒ **失联发生在完成前** |
>
> ⚠️ **因此：本轮云端全量**没有跑完**，`outputs/llava_bf16_sites/` 里的部分记录随主机不可访问**。
> 之前通过的**对照结论仍然有效**（那是独立验证：token 几何逐字节一致、同确定性配置下 4e-4），
> 但**全量结果尚未产出**。
>
> ### 二、✅ 已保住的资产（都在本地，与主机无关）
>
> | 资产 | 位置 | 说明 |
> |---|---|---|
> | **一键重建补丁** | `SUBMISSION/cloud_p3_setup.sh`（**85 行，`bash -n` 通过**）| 换任意新主机：装**钉版环境 → 全 import 自检 → 服务器端下模型 → 官方标注+按序下 N 张图 → 清显存 → bf16 全量** |
> | sweep 脚本副本 | `SUBMISSION/_p820_llava_sites.py` | 含 `--precision {4bit,bf16}` / `--coco-root` / `--bench-steps`（已修）/ `--report-every` / `--deterministic` |
> | 云端修复经验 | 见下"四个坑" | **这是本轮最贵的知识** |
> | **本地基准** | `outputs/llava_sites_local_baseline/`、`_p838_llava_full.LOCAL_BASELINE.out` | frozen ×3 + 160 步轨迹 |
> | 对照数据 | `outputs/llava_parity_local*`、`MANIFEST.json → parity_baseline` | 5 步 loss 2.9466 / 2.9449 / 2.9495（deterministic）|
>
> ### 三、🧠 本轮踩到的四个坑（都已固化进补丁，换机器不必重踩）
>
> | # | 坑 | 现象 | 修法 |
> |---|---|---|---|
> | ① | **镜像 torchvision 与 torch 不匹配** | `operator torchvision::nms does not exist` ⇒ **peft/transformers 导入失败**，而**版本号全对** | 钉 **`torchvision==0.24.1+cu130`**（与本地一致）；**必须实测 import，不能只看版本号** |
> | ② | **bf16 下调 `prepare_model_for_kbit_training`** | 它把**所有参数转 fp32** ⇒ 15 GB 模型变 30 GB ⇒ **CUDA OOM**（加载后立刻死） | bf16 分支**跳过它**，改为直接 `gradient_checkpointing_enable()` + `use_cache=False` + `enable_input_require_grads()` |
> | ③ | **`pkill` 后显存没释放** | 旧进程仍占 **29.24 GB** ⇒ 新跑加载时 OOM | **杀掉后轮询 `nvidia-smi` 直到 <2 GB 再启动**（补丁里已写成循环）|
> | ④ | **管道里的 `tee` 缓冲** | 日志 **0 字节**而 GPU 已 100% ⇒ 看不到进度 | 去掉 `tee`，让心跳直写日志 |
>
> ### 四、⏭️ 待操作者（两条路，任选）
>
> | 路 | 动作 | 代价 |
> |---|---|---|
> | **A. 重启原实例** | 在 AutoDL 控制台**开机**（**注意端口会变**，需把新端口给我）| 若选"保留数据盘"，`/root/p3`（含模型 14 GB 与 2000 张图）**可能还在**，几十秒即可接着跑 |
> | **B. 换新实例** | 把 `SUBMISSION/cloud_p3_setup.sh` + `_p820_llava_sites.py` 传上去，`bash cloud_p3_setup.sh 2000` | 约 6–8 分钟重建（模型 14 GB 需重下）|
>
> ⚠️ **请顺便确认**：实例是**被"关机"还是被"释放"**——若已**释放**，数据盘内容一并销毁，只能走 B。
> **另**：若你在控制台**主动关机**是误触，说明即可；我这边**未执行任何关机命令**（补丁里的关机只在校验通过时才触发，而校验从未通过——因为主机先失联了）。
>
> ### 五、✅ 关机这件事的现状
>
> **主机已不可达 ⇒ "关机"实际已发生**（由平台侧或操作者侧），无需我再操作。
> 若你重开实例继续跑，**跑完校验通过后**再执行 `shutdown -h now`（`tools/_p984_verify_cloud_results.py --shutdown`，
> 该脚本**只在全部检查通过时才关机**，任一异常则保留机器并报错）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        print("  handoff entry added")
    mp = io.open(REPO / "文件地图.md", encoding="utf-8").read()
    row = ("36. 🔌 **云主机中途失联（2026-10-15 23:55）** —— SSH 43746 不可达（重试 3 次全败）⇒ 主机已不在运行，"
           "bf16 全量止于 **step 650/2250**（loss 0.796、0.9 s/步、显存 29.95/32.76 GB），**未跑完**。"
           "✅ 已固化本地资产：**`SUBMISSION/cloud_p3_setup.sh`（85 行，一键重建：钉版环境→import 自检→服务器端下模型→"
           "官方标注+按序下 2000 张图→清显存→bf16 全量）** + `_p820_llava_sites.py` 副本；本地基准与对照数据完好。"
           "🧠 四个坑已固化：① 镜像 torchvision 0.27.1 与 torch 不匹配（导入失败而版本号全对）② bf16 下调 k-bit 准备函数"
           "会转 fp32 ⇒ OOM ③ `pkill` 后显存未释放需轮询确认 ④ 管道 `tee` 缓冲导致日志空白。"
           "**未执行任何关机命令**（校验门禁从未通过，因主机先失联）。详见 `HANDOFF.md` 顶部 2026-10-15 23:55 条目。\n")
    anchor = "35. 🔧 **更正 + 端口正确性已证明（2026-10-15 22:50）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(REPO / "文件地图.md", "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
