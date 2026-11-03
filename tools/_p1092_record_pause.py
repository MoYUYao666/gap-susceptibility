# -*- coding: utf-8 -*-
r"""Record the pause: what the metric recomputation needs, what was learned, and what to run tomorrow.

Written without contacting the host, because the host went away between the last check and this record (SSH
port 43147 unreachable, measured). Everything here comes from the session's own measurements.

    python tools/_p1092_record_pause.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
NOTE = REPO / "docs" / "resume_2026-10-17_llava_metric.md"
MARK = "LLaVA 规范度量重算"

ENT = """> **⏸️ 2026-10-16 21:10 —— LLaVA 规范度量重算：**已开工、主机中途不可达、按操作者指示明天再跑**
>
> 操作者指令：**「明天再跑」**。本节记录**为什么做、做到哪、明天怎么接**，全部为本会话实测。
>
> ### 一、🎯 为什么要重算（这是"要不要重跑实验"的结论）
>
> 归档的 LLaVA 12 条记录用的是 `tools/_p820_llava_sites.py` 里**自写**的 gap 定义；而论文与 ODE 用的是
> **`src/dg_star_tracker.py:compute`**（与 `tools/_p47_qwen_train.py` 一致，其文件头第 18 行明确写了"与
> `src/dg_star_tracker.py:compute` 一致"）：
>
> ```
> DG*  = mean_i || I_i − T_i ||²      （配对、平方、L2 归一化后）
> CG   = || mean_i I_i − mean_i T_i ||
> DG_e = sqrt( CG² + || σ_I − σ_T ||² )
> ```
>
> 而我的脚本算的是 **`mean d(I,T) − ½(mean d(I,I) + mean d(T,T))`**，文本侧取的是 **token 嵌入**（未排除图像 token），
> 并非 `_p47` 的"**最后一层隐状态 → 视觉 token 区间均值池化 / 非 padding 位置均值池化 → 投影 → L2 归一化**"。
>
> ⇒ **不是同一量**。所以我先前对操作者说的"与论文主张有张力"**不成立**，已据此改为补充材料 F 节（**口径不同的负结果**）。
>
> ### 二、✅ 重要结论：**不需要重训**
>
> 12 个 run 的**训练本身没问题**（loss 1.55→0.39、分塔隔离已自检、frozen 三 seed 逐位一致）。
> **7 个 LoRA 适配器已保存在本地**（`outputs/llava_bf16_sites_cloud/*.pt`，773 MB）
> ⇒ 重算**只需前向**，24 GB 卡即可，**分钟级**，不必花 7 小时重训。
>
> ⚠️ **但必须先验证**：若 **frozen**（不训练）在规范定义下**仍移动同样多**，说明该量在 LLaVA 上**分辨率不足**，
> 那么重算也没意义——**先只算 frozen**，再决定是否算其余三臂。
>
> ### 三、📊 新主机（weste:43147，RTX 4080 SUPER 32 GB，全新实例）实测
>
> | 项 | 实测 |
> |---|---|
> | pypi.tuna 镜像 | **3.1–4.6 MB/s** ✅ |
> | `download.pytorch.org` | **0 B/s，卡死**（476 MB 处停住）|
> | `huggingface.co` | **不可达** |
> | `hf-mirror.com`（主机 3 用过的方法）| **~0.5 MB/s**（4 分钟 125 MB）——**与主机 3 的 30–40 MB/s 差 60 倍** |
> | **ModelScope 单连接** | **~1 MB/s（被限速）** |
> | **ModelScope + 32 路分块** | **13–18 MB/s**（已下 **9.9 GB / 15 GB**）✅ |
> | `images.cocodataset.org` 标注包 | **~400 B/s 单连；多连接未起来** |
> | ModelScope 仓库名核实 | `llava-hf/llava-1.5-7b-hf` **存在**（18 文件 14.13 GB）；`AI-ModelScope/llava-1.5-7b-hf` **不存在**（404）|
>
> ### 四、📁 明天可复用的东西（**都在本地**）
>
> | 文件 | 用途 |
> |---|---|
> | `tools/_p1060_recompute_canonical.py` | **规范度量重算**（已写好，只做前向，逐批报告）|
> | `tools/_p1083_parallel_fetch.py` | **多线程分块下载器**（8 MiB/块 × 32 路，断点续传，已验证 13–18 MB/s）|
> | `tools/_p1088_coco_fixture.py` | 取 COCO 标注并按**原顺序**裁到 2000 id、下 500 张保留图 |
> | `tools/_p1059_build_eval_fixture.py` | 本机版同一目的（未跑完）|
> | `tools/_p1061_cloud_eval_fixture.sh` | 云端版同一目的 |
> | `outputs/llava_bf16_sites_cloud/` | **7 个适配器 + 12 条记录**（重算的唯一输入）|
>
> 云端（新实例上）**已装好**：torch 2.9.1+cu130 / torchvision 0.24.1 / transformers 5.16.1 / peft 0.20.0 /
> accelerate 1.14.0 / **modelscope 1.40.2**；适配器已上传 `/root/p3/adapters/`（7 个，773 MB）。
> ⚠️ 但**该实例随主机一起消失**（SSH 43147 现不可达），明天按需重建。
>
> ### 五、⏭️ 明天的执行顺序（照此做即可）
>
> 1. 新主机探速（`tools/_p1063`/`_p1065`）→ 选源；
> 2. 权重：**优先 `tools/_p1083_parallel_fetch.py` 走 ModelScope 多连接**（已验证 13–18 MB/s）；
>    ⚠️ 操作者指示"走镜像"，但本机镜像**只有 0.5 MB/s**，故**以实测为准并回报**；
> 3. 取 COCO 标注 + 500 张保留图（**多连接**）→ 校验 id 顺序与 sha256；
> 4. **先只算 frozen**：`python tools/_p1060_recompute_canonical.py --arms frozen`；
> 5. frozen 稳定 ⇒ 算其余三臂；不稳定 ⇒ **如实报告"该量在 LLaVA 上分辨率不足"**，到此为止；
> 6. 结果过 `tools/_claim_ledger.py` 后，再决定是否更新补充材料 F 节的表述。
>
> ⚠️ **口径提醒**：重算出的数字与归档 12 条**不是同一量**，**不得混用**；两者都必须能指到各自脚本与字段。
>
> **工具**：`_p1058`（定位 Qwen 脚本）｜`_p1060`（重算）｜`_p1083`（多连接下载）｜`_p1088`（COCO 评测集）｜`_p1091`/`_p1092`（暂停记录）。
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
    row = ("45. ⏸️ **LLaVA 规范度量重算：已开工，明天再跑（2026-10-16 21:10）** —— 归档 12 条用的是自写 gap 定义，"
           "而论文/ODE 用 **`src/dg_star_tracker.py:compute`**（`DG*=mean‖I−T‖²`，配对平方）⇒ **不是同一量**"
           "（我先前说的\"与论文有张力\"**已作废**，新闻 `_p1055` 的补充 F 节按\"口径不同的负结果\"写）。"
           "**关键结论：不需重训**——7 个适配器已保存在本地，重算**只做前向**（分钟级，24 GB 卡即可）；"
           "⚠️ **但先只算 frozen 验证分辨率**，若 frozen 仍移动同样多则到此为止。"
           "新机实测：**tuna 3.1–4.6 MB/s**、**hf-mirror 仅 0.5 MB/s**（主机 3 曾是 30–40 MB/s）、"
           "**ModelScope 单连 1 MB/s / 32 路分块 13–18 MB/s**（已下 9.9/15 GB）、COCO 标注 ~400 B/s。"
           "可复用：`_p1060`（重算）、`_p1083`（多连接下载）、`_p1088`（COCO 评测集）；适配器在本地 773 MB。"
           "**主机已随实例消失**（SSH 43147 不可达）。详见 `HANDOFF.md` 顶部条目与 `docs/resume_2026-10-17_llava_metric.md`。\n")
    anchor = "44. 📄 **Paper A 更新：补充 F 节"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(REPO / "文件地图.md", "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")

    NOTE.parent.mkdir(parents=True, exist_ok=True)
    with io.open(NOTE, "w", encoding="utf-8", newline="") as fh:
        fh.write("# Resume note: LLaVA canonical-metric recomputation (2026-10-17)\n\n")
        fh.write("## The task\n\n")
        fh.write("Recompute DG*/CG for the twelve archived LLaVA runs under the canonical definition in "
                 "`src/dg_star_tracker.py:compute` (the one `tools/_p47_qwen_train.py` says it matches), because "
                 "the archived records used a different formula written into `tools/_p820_llava_sites.py`.\n\n")
        fh.write("```\nDG*  = mean_i || I_i - T_i ||^2      (paired, squared, after L2 normalisation)\n"
                 "CG   = || mean_i I_i - mean_i T_i ||\n"
                 "DG_e = sqrt(CG^2 + || sigma_I - sigma_T ||^2)\n```\n\n")
        fh.write("Embeddings as in `_p47`: last hidden state, mean-pooled over non-padding positions (text) and "
                 "over image-token positions (vision). **No training is needed** -- the adapters are saved.\n\n")
        fh.write("## First check before anything else\n\n")
        fh.write("Run the **frozen** arm only. The archived frozen run moves 0.261161 -> 0.261937 under the old "
                 "definition; if the canonical definition moves it comparably, the quantity cannot resolve "
                 "anything on this model and the work stops with an honest report.\n\n")
        fh.write("## Measured on the 2026-10-16 host (weste:43147, RTX 4080 SUPER, fresh instance)\n\n")
        fh.write("| Source / route | Rate |\n|---|---|\n")
        fh.write("| pypi.tuna.tsinghua.edu.cn | 3.1-4.6 MB/s |\n")
        fh.write("| download.pytorch.org | 0 B/s (stalled at 476 MB) |\n")
        fh.write("| huggingface.co | unreachable |\n")
        fh.write("| hf-mirror.com (host 3's method) | ~0.5 MB/s -- host 3 got 30-40 MB/s |\n")
        fh.write("| ModelScope, single connection | ~1 MB/s (throttled) |\n")
        fh.write("| **ModelScope, 32 range connections** | **13-18 MB/s** (reached 9.9 GB of 15 GB) |\n")
        fh.write("| images.cocodataset.org, annotation archive | ~400 B/s single; multi-connection did not start |\n\n")
        fh.write("## Reusable pieces (all local)\n\n")
        for f, why in (("tools/_p1060_recompute_canonical.py", "the recomputation, forward passes only"),
                       ("tools/_p1083_parallel_fetch.py", "multi-connection downloader, resume-safe, proven"),
                       ("tools/_p1088_coco_fixture.py", "fetch and trim the COCO fixture in the original id order"),
                       ("outputs/llava_bf16_sites_cloud/", "the 7 adapters and 12 records -- the only input")):
            fh.write(f"- `{f}` -- {why}\n")
        fh.write("\n## Suggested order tomorrow\n\n")
        fh.write("1. probe the new host's sources (`tools/_p1063`, `tools/_p1065`);\n")
        fh.write("2. weights: prefer `tools/_p1083_parallel_fetch.py` on ModelScope (proven 13-18 MB/s); note the "
                 "operator asked for the mirror, but the mirror measured 0.5 MB/s here, so report the conflict and "
                 "go with what the measurements say;\n")
        fh.write("3. COCO annotations plus the 500 held-out images, obtained with many connections;\n")
        fh.write("4. `python tools/_p1060_recompute_canonical.py --arms frozen`;\n")
        fh.write("5. only if frozen is stable, run the other three arms, then put the numbers through "
                 "`tools/_claim_ledger.py` before touching Section F.\n\n")
        fh.write("**Do not mix** the recomputed numbers with the archived twelve: they are different quantities, "
                 "and each must name its own script and field.\n")
    print(f"  wrote {NOTE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
