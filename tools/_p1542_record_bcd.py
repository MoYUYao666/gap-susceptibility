# -*- coding: utf-8 -*-
"""Fix the real-image archive path in the manifest and record the B/C/D round."""
import glob
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
AN = os.path.join(REPO, "outputs", "analysis")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")
HANDOFF = os.path.join(REPO, "HANDOFF.md")
MAP = os.path.join(REPO, "文件地图.md")
GAPS = os.path.join(REPO, "docs", "P3_REMAINING_GAPS_2026-10-22.md")


def main() -> int:
    m = json.load(io.open(MANIFEST, encoding="utf-8"))
    real = sorted(glob.glob(os.path.join(EXP, "cloud_verify_r5_s42_imgs_cap*.json")))
    chosen = os.path.relpath(real[0], REPO).replace(os.sep, "/") if real else None
    for f in m["manuscripts"]["P3"]["floats"]:
        if f["label"] == "tab:realimage" and chosen:
            f["archive"] = chosen
    json.dump(m, io.open(MANIFEST, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("realimage archive ->", chosen)
    entry = """> **🧪 2026-10-23 01:10 —— B/C/D 轮全部本地/云端跑完（除 D1 第三族）**
>
> | 项 | 结果 |
> |---|---|
> | **B1 可加性残差** | 六对 block 的残差全部 **< 0.05%**（最大 +0.05%）→ R3′ 在探针上被实测支持（S30）|
> | **B2 高秩曲率** | r=5/6 为负，**r=24/64 翻正**（share@lr +0.17%~+0.35%）→ 一阶近似在高秩不再符号稳定（S34）|
> | **B3 signed-Γ / β** | signed-Γ(β=1) arm **+232.5**；β 网格显示 signed 规则把 rank 移到 shallow/mid（S32）|
> | **C1 10 seeds × r=4–7** | 每个 rank 10 seeds：r4 均值 −97.7、r5 −43.7、r6 +87.3、r7 +195.0；**完全分离**，r5 vs r6 精确置换 **p≈1.1×10⁻⁵**（S33）|
> | **C2 逐层 Γ** | 32 层 + vision，全部带 bootstrap 95% CI（S31）|
> | **C3 稳健统计** | r5: median −27.0/MAD 16.5；r6: median +62.0/MAD 31.0（S31）|
> | **D2 非 CLIP 源** | SigLIP Γ → 分配 2/7/5/2，arm **+165.5**（不同源给不同排序）（S32）|
> | **D3 真实图像 rank sweep** | r=4–8：+105/+153.5/+510.5/+479.5/+629.5，**全正、无 crossing**（S35）|
> | **A2 VQA 规模** | 400 训练对/per-step/eval 200：base 0.325/0.353、r5 0.350/0.378、r6 0.360/0.384（S28）|
>
> **未完成**：D1 第三 VLM 族（目前仅 Qwen2.5 族 3B/7B）；A1 的 HALoRA/ShapLoRA 官方代码仍不可得。
> 补充材料现 **S1–S35（15 页）**；正文 10 页；audit_check/audit_pdf 0/0；provenance gate PASS。
>

"""
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "B/C/D 轮全部本地/云端跑完" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + entry + h[j + 1:])
        print("handoff updated")
    mp = io.open(MAP, encoding="utf-8").read()
    row = "150. 🧪 **B/C/D 轮（2026-10-23 01:10）** —— S30–S35：可加性<0.05%、高秩曲率翻正、10-seed 完全分离 p=1.1e-5、逐层 Γ、SigLIP 源、真实图像无 crossing；D1 第三族未做。\n"
    if "B/C/D 轮" not in mp:
        i = mp.find("149. 🧩 **A 组本地完成")
        assert i >= 0
        end = mp.find("\n", i)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
        print("map updated")
    g = io.open(GAPS, encoding="utf-8").read()
    add = """

## 十二、B/C/D 轮状态（2026-10-23 01:10）

- 完成：B1/B2/B3、C1/C2/C3、D2/D3、A2（VQA 400）。证据：`outputs/analysis/p3_additivity_residual.json`、
  `p3_perlayer_gamma.json`、`p3_robust_stats.json`、`p3_signed_gamma_beta.json`、`p3_siglip_gamma.json`、
  `cloud_p3_hessian_probe_r24/r64.json`、`cloud_p3_vqa_downstream_*.json`、`cloud_verify_r*_s*.json`。
- 未完成：D1 第三 VLM 族；A1 的 HALoRA/ShapLoRA 官方代码仍不可得。
"""
    if "## 十二、B/C/D 轮状态" not in g:
        io.open(GAPS, "w", encoding="utf-8", newline="").write(g.rstrip() + add)
        print("gaps updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
