# -*- coding: utf-8 -*-
r"""Score the two retrieved pre-registered sets (P2 OpenCLIP, P4 CLIP B/16) and record the outcome.

Rules frozen in docs/PaperA_preregistered_predictions.md before the runs:
  P2/P4 both predicted: text-only DeltaCG negative; ordering by |DeltaCG| (smallest first) = text_only, both,
  vision_only; text-only R@1 below frozen.
The signed-DeltaCG reading (the paper's own metric) is reported alongside, because the frozen wording used |DeltaCG|
and that ambiguity was disclosed when P1 was scored. P3 (SigLIP) is recorded as deferred with its concrete blocker.
"""
import glob
import io
import json
import os
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)


def num(d, *keys):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur if isinstance(cur, (int, float)) else None


def collect(set_name, label):
    rows = []
    for p in sorted(glob.glob("outputs/paperA_c_prereg_%s/*.json" % set_name)):
        d = json.load(io.open(p, encoding="utf-8"))
        site = None
        for s in ("text_only", "both", "vision_only"):
            if s in p:
                site = s
        if site is None:
            site = d.get("tag") or "unknown"
        cg0, cg1 = num(d, "initial_gap", "centroid_gap"), num(d, "final_gap", "centroid_gap")
        if cg0 is None or cg1 is None:
            continue
        rows.append({"set": label, "site": site, "dcg": cg1 - cg0,
                     "r1": num(d, "final_task_metrics", "R@1"),
                     "r1_0": num(d, "initial_task_metrics", "R@1")})
    return rows


all_rows = collect("openclip", "P2") + collect("b16", "P4")
by = {}
for r in all_rows:
    by.setdefault((r["set"], r["site"]), []).append(r)

summary = {}
for (s, site), rs in by.items():
    n = len(rs)
    summary[(s, site)] = {
        "n": n,
        "mean_dcg": sum(r["dcg"] for r in rs) / n,
        "mean_abs": sum(abs(r["dcg"]) for r in rs) / n,
        "mean_r1": (sum(r["r1"] for r in rs if r["r1"] is not None) /
                    max(1, sum(1 for r in rs if r["r1"] is not None))),
    }

lines = ["", "## Results, P2 (OpenCLIP B/32) and P4 (CLIP B/16), measured 2026-10-26", "",
         "Fifteen arms each (three sites x five seeds 42/123/456/789/1012), strict freezing, rank 8, alpha = 2*rank,",
         "10 epochs, 5000 samples, batch 128, DG* per epoch. Archive: `outputs/paperA_c_prereg_openclip/`,",
         "`outputs/paperA_c_prereg_b16/`.", "",
         "| set | site | n | mean signed DeltaCG | mean abs(DeltaCG) | mean R@1 |",
         "|---|---|---|---|---|---|"]
verdicts = {}
for s in ("P2", "P4"):
    order_abs, order_signed = [], []
    for site in ("text_only", "both", "vision_only"):
        v = summary.get((s, site))
        if v:
            lines.append("| %s | %s | %d | %+.4f | %.4f | %.4f |"
                         % (s, site, v["n"], v["mean_dcg"], v["mean_abs"], v["mean_r1"]))
    sites = [site for site in ("text_only", "both", "vision_only") if (s, site) in summary]
    order_abs = sorted(sites, key=lambda x: summary[(s, x)]["mean_abs"])
    order_signed = sorted(sites, key=lambda x: summary[(s, x)]["mean_dcg"])
    sign_ok = summary.get((s, "text_only"), {}).get("mean_dcg", 0) < 0
    holds_abs = order_abs[:2] == ["text_only", "both"]
    verdicts[s] = {"sign": sign_ok, "order_abs": order_abs, "order_signed": order_signed,
                   "holds_abs": holds_abs,
                   "verdict": "holds" if (sign_ok and holds_abs) else ("partially holds" if sign_ok else "fails")}

lines += ["", "### Scoring (verbatim against the frozen rules)", ""]
for s in ("P2", "P4"):
    v = verdicts[s]
    lines.append("- **%s**: sign holds = **%s**; literal |DeltaCG| ordering = %s (predicted text_only, both, "
                 "vision_only) -> %s; signed ordering = %s. **Verdict: %s**."
                 % (s, v["sign"], " -> ".join(v["order_abs"]), "matches" if v["holds_abs"] else "does not match",
                    " -> ".join(v["order_signed"]), v["verdict"]))
lines += ["", "### P3 (SigLIP) - deferred, not scored", "",
          "The fifteen SigLIP arms produced no results: the SigLIP text tower caps `max_position_embeddings` at 64,",
          "while the shared pipeline pads to CLIP's 77, so every arm raised",
          "`ValueError: Sequence length must be less than max_position_embeddings (got 77, max 64)` before training.",
          "The fix is a backbone-aware tokenizer length (64 for siglip) in the data pipeline; P3 will be re-run after",
          "that change and is recorded here as deferred, never as measured.", ""]

P = "docs/PaperA_preregistered_predictions.md"
t = io.open(P, encoding="utf-8").read()
marker = "## Results, P2 (OpenCLIP B/32) and P4 (CLIP B/16), measured 2026-10-26"
if marker not in t:
    io.open(P, "w", encoding="utf-8", newline="").write(t.rstrip() + "\n" + "\n".join(lines))
    print("pre-registration updated with P2/P4 results and the P3 deferral")
for s in ("P2", "P4"):
    v = verdicts[s]
    print(s, "sign", v["sign"], "| abs order", v["order_abs"], "| signed order", v["order_signed"], "|", v["verdict"])

H = "HANDOFF.md"
th = io.open(H, encoding="utf-8").read()
if "C 批 P2/P4 已结算" not in th:
    entry = ("## 🧪 2026-10-26 — C 批 P2/P4 已结算，P3 延后（含原因）\n\n"
             "OpenCLIP(B/32) 15/15 与 CLIP B/16 15/15 已跑完并取回（`outputs/paperA_c_prereg_openclip/`、"
             "`outputs/paperA_c_prereg_b16/`），实例已关机（端口 39308 复验 False）。\n"
             "打分（详见 `docs/PaperA_preregistered_predictions.md`）：\n"
             + "".join("- **%s**：符号 %s，字面 |ΔCG| 排序 %s，签名排序 %s ⇒ **%s**\n"
                       % (s, verdicts[s]["sign"], " -> ".join(verdicts[s]["order_abs"]),
                          " -> ".join(verdicts[s]["order_signed"]), verdicts[s]["verdict"]) for s in ("P2", "P4"))
             + "\n**P3（SigLIP）未测**：SigLIP 文本塔 `max_position_embeddings=64`，管线按 CLIP 的 77 补齐 ⇒ "
               "`ValueError: Sequence length must be less than max_position_embeddings (77 vs 64)`，15 臂全部在训练前失败。"
               "修法：数据管线按 backbone 选 tokenizer 长度（siglip=64）。**已如实记为延后，不当作已测**。\n"
             "\n**并发教训（写进规则回忆）**：B/16 的 `both` 臂单臂约 20 GB（patch 16×16 ⇒ token 4 倍），"
             "2 并行 = 31.4 GB 撞上 31.48 GB 卡上限 ⇒ OOM；最终以 **单臂串行 + expandable_segments** 跑完。\n")
    lines_h = th.splitlines(keepends=True)
    idx = 0
    for i, ln in enumerate(lines_h):
        if ln.startswith("## "):
            idx = i
            break
    io.open(H, "w", encoding="utf-8", newline="").write("".join(lines_h[:idx]) + entry + "\n" + "".join(lines_h[idx:]))
    print("HANDOFF updated")

subprocess.run(["git", "add", "-A"], check=False)
subprocess.run(["git", "commit", "-q", "-m",
                "Paper A pre-registration: score P2 (OpenCLIP) and P4 (CLIP B/16); record P3 (SigLIP) as deferred with its tokenizer blocker"],
               check=False)
print(subprocess.run(["git", "log", "--oneline", "-1"], capture_output=True, text=True).stdout.strip())
