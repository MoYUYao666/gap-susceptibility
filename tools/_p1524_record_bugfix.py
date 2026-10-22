# -*- coding: utf-8 -*-
r"""Record the Qwen rank-bug finding and its correction.

    python tools/_p1524_record_bugfix.py
"""
import glob
import hashlib
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(REPO, "outputs", "analysis")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")
OUT = os.path.join(AN, "p3_code_audit.json")


def main() -> int:
    qwen = []
    for f in sorted(glob.glob(os.path.join(EXP, "qwen_cf_uniform_rank*_q25_r*.json"))):
        d = json.load(io.open(f, encoding="utf-8"))
        qwen.append({"file": os.path.basename(f), "rank": d.get("rank"), "seed": d.get("seed"),
                     "trainable_params": d.get("trainable_params"), "delta_E": d.get("delta_E")})
    audit = {"meta": {"script": "tools/_p1524_record_bugfix.py", "date": "2026-10-22",
                      "finding": "run_training_qwen25.py ignored --rank; every 2026-10-22 Qwen2.5 record had the default "
                                 "rank 4 (trainable_params=1,843,200). Fixed by using args.rank for uniform block config; "
                                 "invalid records moved to outputs/analysis/_invalid_qwen25_rank_bug/."},
             "corrected_qwen": qwen,
             "checks": {
                 "adapters": "p3_vqa/instr/caption adapters have r=5/6 and alpha=10/12; probe r=8",
                 "baseline_arms": "trainable counts differ across explicit block allocations (verified)",
                 "vqa_metrics": "stored accuracy reproduces under the script's own normalisation",
                 "hessian": "stored share at 1e-3 probe = 0.5*1e-3*gHg/g2 (recomputed); share at lr = 0.5*5e-5*gHg/g2",
                 "gamma": "CV values reproduce from the stored conditions",
             }}
    io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(audit, indent=1))
    print("wrote", os.path.relpath(OUT, REPO))
    # HANDOFF
    h = io.open("HANDOFF.md", encoding="utf-8").read()
    entry = """> **🐞 2026-10-22 17:30 —— 代码审计发现并修复一个真 bug：Qwen2.5 的 `--rank` 无效**
>
> - `paper3/scripts/run_training_qwen25.py` 中 `--rank` 只进文件名/日志，实际 LoRA 秩来自 block_config（默认 4）；
>   2026-10-22 的首批 6 个 Qwen2.5 记录 trainable_params 全为 1,843,200，即全用 rank 4 → 这批"r5 vs r6"结论无效；
> - 已修复（uniform 时用 args.rank），无效记录移到 `outputs/analysis/_invalid_qwen25_rank_bug/`，并用正确的 r=5/6
>   重跑 3 seeds；修正后：r5 = +448/+384/−64，r6 = +432/−32/−80 → **r5/r6 无符号变化，r5 符号随 seed 变化**；
> - S20/S26/S17 已按修正结果重写："新族不复现 crossing"成立，但"稳定反向符号"的说法**撤回**；
> - 其余近期脚本已核查：adapter rank/alpha 正确、基线 arm 的 trainable 数随分配变化、VQA/Hessian/Gamma 指标可复算；
> - 审计证据：`outputs/analysis/p3_code_audit.json`（脚本 `tools/_p1521`、`_p1522`、`_p1523`、`_p1524`）。
>

"""
    if "Qwen2.5 的 `--rank` 无效" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open("HANDOFF.md", "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + entry + h[j + 1:])
        print("handoff updated")
    m = io.open("文件地图.md", encoding="utf-8").read()
    row = ("147. 🐞 **代码审计/修 bug（2026-10-22 17:30）** —— Qwen2.5 的 `--rank` 无效（全用 rank 4）已修复并重跑；"
           "S20/S26/S17 按修正结果改写（无 crossing、r5 符号随 seed 变）；审计 JSON `p3_code_audit.json`。\n")
    anchor = "146. 🧾 **本地完成/云端待实例"
    if "代码审计/修 bug" not in m:
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        m = m[: end + 1] + row + m[end + 1:]
        io.open("文件地图.md", "w", encoding="utf-8", newline="").write(m)
        print("map updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
