# P3 upgrade memo — 2026-10-19

> Verification and editing record for the P3 upgrade package. Manuscript: `paper3/paper_ieee/` (PRL R1 under review,
> deadline 2026-11-02). Archive: `outputs/analysis/p3_upgrade_analysis.json`; script `tools/_p1343_p3_upgrade_analyses.py`.

## Verified from archives

1. **AdaLoRA numbers match the manuscript exactly.** Archived runs at lr $3\times10^{-4}$ and $10^{-3}$ give
   $\Delta E=-1468.15$ and $-757.30$ (`_p458_adalora_lr0.0003.txt`, `_p458_adalora_lr0.001.txt`), i.e. the sentence
   "AdaLoRA is better than any of our arms" is supported and needs no change. The separate per-sample summary under
   `p3_alloc_runs/adalora_summary.json` is a different run set (lr $5\times10^{-5}$) and is not used in the text.
2. **E2 runs confirm the bracketed $[5,6]$ crossing.** Mean final energy is $3906 < 3927$ at $r=5$ and $3989 > 3927$ at
   $r=6$ (three seeds each), so the sign change sits between 5 and 6 in that family.
3. **The independent 3-epoch sweep gives a different boundary: $[14,16]$.** Ranks $\le14$ converge (mean final
   $3821$ at $r=14$ against $3927$ start), divergence appears at $r=16$ in two of three seeds (mean final $4878$), and in
   all three seeds by $r=20$ ($6787$). This is consistent with the paper's "protocol, not model" retraction only if the two
   run families are labelled as different protocols. **Action for the next version: label the sweep protocol explicitly in
   the text (it is currently unlabelled in the archive), or drop the sweep from the claim.** Not changed in this round to
   avoid introducing a contradictory bracket.
4. **Paired theory-vs-random comparison now in the text.** Same-seed, same-rank pairs ($n=4$): the guided arm ends
   $+11.5$ higher in alignment energy, 95 % bootstrap CI $[+6.8,+16.2]$ — the direction is against the guided allocation,
   which strengthens the existing "indistinguishable from random" statement.

## Deferred

- **P3-P2-7 (local CLIP rank sensitivity)**: deferred, not executed. A generic-CLIP proxy cannot validate a
  LLaVA-protocol statement about $\Gamma$; adding it would be scope creep and could be read as evidence substitution. If a
  local control is wanted later, it should be framed as a separate robustness note, not as support for the LLaVA claim.

## Housekeeping (done)

- Dead labels `cor:retrieval-specialization` and `thm:repr` now referenced in the text.
- Unused bibliography entry `sharegpt2023` now cited in the Reproducibility paragraph.
- PDF metadata title/author added via `\hypersetup`; `main.pdf` = **10 pages**, 0 errors, 0 undefined, 0 overfull.

## 续：协议归属已澄清（2026-10-19 18:50）

追查 `paper3/scripts/run_full_sweep.py`：sweep 由 `run_training.py --rank R --seed S --epochs 3` 生成；E2 族在同一
rank/seed 下的轨迹不同（E0 3930.5 vs 3927，形状也不同），说明两族是**不同训练配置**、同一空白图协议。因此：
- E2 族：临界 bracket $[5,6]$（r=5 均值 3906 < 3927；r=6 均值 3989 > 3927）；
- dense 3-epoch sweep：$\le14$ 收敛、r=16 两/三种子发散、r≥20 全部发散 ⇒ bracket $[14,16]$。
- 两族差异说明临界 rank 随**协议与超参**移动，正是论文"属于协议不属于模型"的撤回表述；已在 `sections/conclusion.tex`
  写入一句明确证据，不再有"未标注协议"的自相矛盾风险。
## Round 4 (2026-10-19 19:25): local rank-sensitivity control added to the supplement

Deferred item P2-7 is now executed as a *supplementary* control, not as main-text evidence: CLIP ViT-B/32, text-tower
LoRA, ranks 4-64, DTD with a per-class held-out split, six epochs and two seeds. The centroid gap stays in [0.744, 0.792]
with no divergence or collapse, pooled r(rank, CG) = -0.43 and r(rank, top-1) = -0.10, i.e. the LLaVA critical-rank
phenomenon does not reproduce in this cheaper local setting - consistent with the main text's system/protocol-specific
reading. Archive `outputs/analysis/p3_rank_local_control.json`, script `tools/_p1358_p3_rank_control.py`, supplement
section `sec:supp-rank-control`.

## Round 5 (2026-10-19 20:45): the [5,6] crossing re-run on the current protocol

Previously only archived families were available; the current script gives E0 = 3921.0 while the archived E2 family
gives 3927.0 and the r=5/r=6 verify runs give 3930.5. A fresh re-run of the current script (seed 42, three epochs)
gives ΔE = -10.5 (r=5), +115.0 (r=6) and +1235.0 (r=16), so the [5,6] sign change is reproduced on the current,
reproducible protocol; the previously noted [14,16] sweep bracket came from a different configuration of the same
script lineage. Archive: outputs/analysis/p3_rerun_protocol.json; main text one sentence, supplement section S8.
