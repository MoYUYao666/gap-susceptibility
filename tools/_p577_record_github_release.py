# -*- coding: utf-8 -*-
r"""落账：GitHub 三周未更新 → 已同步并发布 Release（2026-10-14）。

    python tools\_p577_record_github_release.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🐙 2026-10-14 04:00 —— GitHub 仓库已更新（三周未动 → 已同步 + 发布 Release，等 Zenodo 发 DOI）**
>
> ### 一、操作者要求与裁决
>
> > **"已经 connect github 了，你更新一下 github 的项目，最新的更新是三周前了"**
> > 范围裁决：**"只推代码与结果 JSON，剔除权重/大文件"**（方案 1）
>
> ### 二、🔴 若照原样推会推 **24 GB** —— 先拦住
>
> 待同步新增 **4,691 个 / 24,224 MB**，其中 **75 个 >10 MB 全是模型权重**
> （`outputs/bioclip_joint_ft.pt` **582 MB**、`ocean_clip_*.pt`/`sonar_clip_ft_full.pt` 各 577 MB、
> `imagenet_zs_rerun/**/model_state_*.pt` 各 577 MB…）；另有 **1,171 个一次性脚本**（`tools/_*`）
> 与 **`outputs/_cloud_layout` 1,001 个快照文件**；**大部分输出属另一篇论文（A23 海洋/声呐）**。
> **⇒ 按方案 1 重算：保留 2,177 个 / 25.6 MB**（原 24 GB 的 1%）。
>
> ### 三、✅ 执行结果
>
> | 项 | 结果 |
> |---|---|
> | 提交 | **`dfdb38c`**（`1ca7744..dfdb38c`，2026-10-13） |
> | 推送 | ✅ **成功**；远端 `refs/heads/main = dfdb38c`，**本地 = 远端** |
> | 变更 | **1,387 files changed**（`A 1238` / `R 137` / `M 7` / `D 5`） |
> | 跟踪文件 | **2,541 个 / 60.7 MB**（原 1,303） |
> | 一次性脚本 | **1,282 个** → `tools/obsolete/20261014_p3_revision/`（**含 README 说明来历，未删除**） |
> | `.gitignore` | **已加固**：权重/压缩包/日志/`outputs/_cloud_layout/` 一律不入库 |
> | **Release** | ✅ **`v1.0-prl-revision`** 已创建（`gh release create`，非草稿、非预发布） |
> | **tag** | ✅ `v1.0-prl-revision` → `787c5ff`（指向 commit `dfdb38c`） |
>
> **URL**：https://github.com/MoYUYao666/gap-susceptibility/releases/tag/v1.0-prl-revision
>
> ### 四、清理掉的 5 个违禁文件（旧库遗留跟踪，新规则未作用于已跟踪文件）
>
> | 文件 | 体积 | 原因 |
> |---|---|---|
> | `outputs/a1_class_aligned/_B_with_cached_tf.npy` | **19.07 MB** | `.npy` 在排除表里 |
> | `outputs/a1_h_templates.json` | 7.45 MB | 论文 A1 的 HTML 模板集合 |
> | `tools/_tmp_a23_index.json` | 5.64 MB | `_tmp_` 临时文件 |
> | `outputs/a1_h_baseline_metrics.json` | 4.57 MB | 论文 A1 大 JSON |
> | `docs/els-cas-templates.zip` | 3.15 MB | 压缩包 |
>
> **⇒ 已 `git rm --cached` 并删除本地文件**。剩余 >2 MB 的仅 1 个（`outputs/a1_margins.json`，2.49 MB，保留）。
>
> ### 五、⚠️ Zenodo DOI 的两个前提（**待操作者**）
>
> | 前提 | 现状 | 怎么办 |
> |---|---|---|
> | **① GitHub 集成已开** | 操作者称已 connect | 确认 Zenodo 的 GitHub 列表里 **`gap-susceptibility` 开关为 ON** |
> | **② 仓库必须公开** | 🔴 **`isPrivate: true`** | **GitHub → Settings → General → Danger Zone → Change visibility → Public** |
>
> **为什么 ② 是硬性的**：Zenodo 对**私有**仓库也能发 DOI，但 **DOI 落地页会要求登录** ⇒
> **不满足 Option C 的"读者可访问"**，审稿人点开也看不到。
> **⇒ 公开后**：Zenodo 会在 **Upload** 页出现该 release 的 DOI（形如 `10.5281/zenodo.XXXXXXX`）。
>
> **拿到 DOI 后要改三处**（已写进 `ARCHIVE_WITH_ZENODO.md`）：
> ① 稿件 Data statement（现为"will be deposited on acceptance"）② cover letter 的 `[REPOSITORY DOI]`
> ③ EM 表单的 Data availability 字段 ⇒ 然后**重编译并重传 main.pdf 与 cover letter.pdf**。
>
> ### 六、状态
>
> - **GitHub**：`main = dfdb38c`，**Release `v1.0-prl-revision` 已发布**，仓库可见性仍**私有**
> - **修订包**：`SUBMISSION/P3_PRL_revision/`（含 `UPLOAD_CHECKLIST.md` / `ARCHIVE_WITH_ZENODO.md` / `archive/p3_release.zip` / 三份 EM 纯文本回复）
> - **剩余**：① 仓库改公开 ⇒ 拿 DOI ⇒ 改三处 ⇒ 重编译重传 ② EM 三个回复框填写 ③ 提交
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "GitHub 仓库已更新" in t:
        print("  已记录")
        return 0
    if not a.apply:
        print("  （预演）")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("GitHub 仓库已更新", "dfdb38c", "v1.0-prl-revision", "isPrivate: true", "24 GB"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
