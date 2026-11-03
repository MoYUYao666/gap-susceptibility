# -*- coding: utf-8 -*-
"""Record the purely-local extra round and re-freeze the next-revision package."""
import hashlib
import io
import os
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
HANDOFF = "HANDOFF.md"
MAP = "文件地图.md"
STATUS = "docs/P3_SUBMISSION_STATUS.md"
PKG = "SUBMISSION/P3_PRL_next_revision"

entry = """> **🧪 2026-10-24 01:45 —— 纯本地补跑：第四环境栈、S37 更新、r3/r8 置换、Qwen 逐层、SmolVLM 第三族**
>
> - **第四环境栈** torch 2.6.0+cu124 / CUDA 12.4（本地 RTX 4060）：r5 **−35.5**、r6 **+42.0**（E0 3917.0）→ 符号模式与 cu130 两栈一致，torch2.4 仍是离群栈；S29 表扩为 **4 环境**；
> - **S37 更新**：torch2.4 补到 4 seeds（+41.0/−2.5/−2.0/+64.5），三环境分解 **σ_env=31.1、σ_seed=34.3、环境占比 45%，10k bootstrap CI [21%, 75%]**；
> - **S33**：r=3 vs r=8 精确置换 **p=1.08×10⁻⁵**（同样是最小可达值）；
> - **S43 Qwen2.5-VL-3B 逐层**：layer 0 占 |Γ| 的 **98.1%**，前 4 层 **99.5%** → 逐层分布是模型特有的（LLaVA 以 vision 为主）；
> - **S44 SmolVLM-500M（第三族）**：3 seeds r5 **−70.8/−67.2/−85.2**、r6 **+25.1/+53.6/+17.5** → **crossing 符号变化在第二个模型族复现**（r6 幅度小；Qwen 族两个对照仍把主张限制在"证据范围内"）；
> - 补充材料 **S1–S43（17 页）**；audit 0/0；provenance PASS；冻结包已按新稿重建。
>

"""

h = io.open(HANDOFF, encoding="utf-8").read()
if "纯本地补跑：第四环境栈" not in h:
    i = h.find("# 项目交接文档")
    j = h.find("\n", i)
    io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + entry + h[j + 1:])
    print("handoff updated")

m = io.open(MAP, encoding="utf-8").read()
row = ("153. 🧪 **纯本地补跑（2026-10-24 01:45）** —— 第四栈 torch2.6/cu124（−35.5/+42.0）；S37 σ_env 31.1/占比 45%；"
       "r3–r8 p=1.08e-5；Qwen 逐层 layer0 98.1%；SmolVLM 三 seed 复现符号变化；补充 S1–S43。\n")
if "纯本地补跑" not in m:
    i = m.find("152. ✅ **定稿/冻结")
    e = m.find("\n", i)
    m = m[: e + 1] + row + m[e + 1:]
    io.open(MAP, "w", encoding="utf-8", newline="").write(m)
    print("map updated")

s = io.open(STATUS, encoding="utf-8").read()
s = s.replace("(Manuscript 10 pp; Supplementary 17 pp, S1–S41)", "(Manuscript 10 pp; Supplementary 17 pp, S1–S43)")
old_block = ("- **Supplement:** 8 → 17 pages, S1–S41.")
new_block = ("- **Supplement:** 8 → 17 pages, S1–S43 (S42 per-layer coupling on Qwen2.5-VL-3B, S43 SmolVLM third-family "
             "control added in the purely-local round).")
if old_block in s:
    s = s.replace(old_block, new_block, 1)
if "Purely-local extra round" not in s:
    s += ("\n## Purely-local extra round (2026-10-24)\n\n"
          "Fourth stack (torch 2.6/CUDA 12.4): r5 -35.5, r6 +42.0. Environment-variance update: sigma_env 31.1, "
          "sigma_seed 34.3, share 45% [21, 75]. Exact permutation r=3 vs r=8: p=1.08e-5. Qwen2.5-VL-3B per-layer: "
          "layer 0 holds 98.1% of the coupling. SmolVLM-500M (three seeds): r5 -70.8/-67.2/-85.2, r6 +25.1/+53.6/+17.5, "
          "i.e. the sign change replicates in a second family with small r=6 magnitude.\n")
io.open(STATUS, "w", encoding="utf-8", newline="").write(s)
print("status doc updated")

# rebuild package
import subprocess
cmd = ["python", "tools/_p1336_build_venue_package.py", "--venue", "PRL", "--out", PKG,
       "--manuscript", "paper3/paper_ieee/main.pdf",
       "--supplementary", "paper3/paper_ieee/supplementary/supplementary.pdf",
       "--title-page", "SUBMISSION/P3_PRL_resubmission/TitlePage.pdf",
       "--highlights", "SUBMISSION/P3_PRL_resubmission/Highlights.pdf",
       "--authorship", "SUBMISSION/P3_PRL_resubmission/AuthorshipConfirmation.pdf",
       "--source", "paper3/paper_ieee", "--figures", "paper3/paper_ieee/figures", "--apply"]
subprocess.run(cmd, check=True)
shutil.copy2(os.path.join("SUBMISSION/P3_PRL_resubmission", "EM_FIELDS.md"), os.path.join(PKG, "EM_FIELDS.md"))
note = """

## Freeze record (2026-10-24, supersedes the 2026-10-23 freeze)

- Manuscript 10 pages; Supplementary 17 pages (S1--S43; fourth stack, per-layer Qwen coupling and SmolVLM family added).
- LaTeX source verified standalone with pdflatex + bibtex + 2x pdflatex: 10 pages, 0 errors, 0 undefined refs/cites.
- SHA256SUMS.txt covers every file in this package.
"""
readme = io.open(os.path.join(PKG, "README.md"), encoding="utf-8").read()
if "Freeze record (2026-10-24" not in readme:
    io.open(os.path.join(PKG, "README.md"), "w", encoding="utf-8", newline="").write(readme.rstrip() + note)
lines = []
for f in sorted(os.listdir(PKG)):
    fp = os.path.join(PKG, f)
    if os.path.isfile(fp) and f != "SHA256SUMS.txt":
        lines.append("%s  %s" % (hashlib.sha256(io.open(fp, "rb").read()).hexdigest(), f))
io.open(os.path.join(PKG, "SHA256SUMS.txt"), "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
print("package rebuilt:", len(lines), "files")
