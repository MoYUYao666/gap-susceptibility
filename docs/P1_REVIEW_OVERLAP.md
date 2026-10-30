# P1 — independent adversarial review: overlap, novelty split and disclosure

**Engagement.** Read-only review of the manuscript in `paper/` — *"Protect, Don't Perturb: Cross-Modal Alignment
under PEFT of Vision-Language Models"* (sole author Hongrui Wan, University of Southampton), manuscript
**PR-D-26-10149**, *Pattern Recognition*, submitted **2026-08-23**. Question asked by the coordinator: **what is
this paper's relationship to the same author's other manuscripts, and what will an editor conclude?**

**Companion manuscripts compared against P1** (as named in the brief):

| tag | path | title | status |
|---|---|---|---|
| **A1** | `paper_a1/main.tex` (+ `main_zh.tex`, `related_work.tex`, `cover_letter.tex`) | *The Modality Gap Is Not a Universal Health Metric: Order Preservation Governs Zero-Shot Robustness* | PRLETTERS-D-26-01941 rejected; revised → NEUCOM-D-26-20952 (2026-09-16) |
| **A23** | `paper_a2/main.tex` (+ `main_zh.tex`, `ext_partI–V`) | *Alignment health across perception modalities: a gap-surgery diagnostic for marine vision and acoustic sonar models* | OE-D-26-11643, desk-rejected 2026-09-16; being retargeted |
| **ap3** | `paper_ap3/` (11 sections) | parked merge of P1 + P2 + P3 | never submitted |
| **P2** | `paper2/` (cas-sc) | *Gap Susceptibility: A Dynamical Theory of Cross-Modal Alignment under PEFT* | — |
| **P3** | `paper3/paper_ieee/` (IEEEtran) | Representation Theorem / GFAP / cross-architecture allocation | — |

**Verification rule applied (as instructed).** Every overlap claim below is backed by **quoted text with
file:line on both sides** — quoted from the manuscript files themselves, never from `docs/*.md`. Where a
`docs/*.md` record is cited it is labelled as *record*, not as evidence. The central instrument for §1 was a
mechanical scan: all LaTeX of P1, A1, A23, ap3, P2, P3 was stripped of markup, tokenised to words, and searched
for maximal common word runs of ≥20 words (published as an independent check, not a human impression). **The
scan found exactly 2 qualifying verbatim runs, both P1↔ap3** (findings **1** and **4**); no run of ≥20 words was
shared with A1, A23, P2 or P3. A near-verbatim pass (5-gram Jaccard ≥0.5 on sliding 22-word windows) returned
**zero** additional hits, i.e. the companions are *rewritten*, not pasted. That is the single most important
fact in this report, and it cuts in the author's favour.

**Reference chain verified by hand.** A1, A23, P2 and P3 each cite P1 as prior work under their own key:
`paper_a1/main.tex:605` `\bibitem{wan2026protect} H.~Wan, ``Protect, don't perturb: …,'' under review, Pattern
Recognition, 2026.`; `paper_a2/main.tex:885` `Wan, H., 2026b. Protect, don't perturb: … Under review, Pattern
Recognition (PR-D-26-10149).`; `paper2/sections/discussion.tex:16` "Our companion study~\citep{wan2026protect}
discovered the empirical regularity …"; `paper3/paper_ieee/sections/discussion.tex:15` "The companion empirical
study~\cite{wan2026protect} found that text-only fine-tuning overwhelmingly preserves alignment across 5
architectures." **P1 does not cite any of them back** (see findings **5** and **7**).

---

## 1. Textual overlap — verbatim and near-verbatim passages (≥20 words)

### 1.1 P1 ↔ ap3 (the only verbatim runs found anywhere)

Both runs are in `paper/sections/experiments.tex` and `paper_ap3/sections/04_mechanism.tex`. `paper_ap3/` is the
parked merge of P1 + P2 + P3 and its §4 is structurally the P1 empirical chapter.

**Run 1 — 27 words** (`paper/sections/experiments.tex:58` ↔ `paper_ap3/sections/04_mechanism.tex:57`)

- P1: `Lower ranks ($r=4,8,16$) consistently reduce or maintain the gap, while higher ranks ($r=32,64$) tend to increase it. On Flickr30k, rank-4 achieves CG$\Delta = -0.027$ and rank-16 achieves the best \Rk{1} of 0.702.`
- ap3: `Lower ranks ($r=4,8,16$) consistently reduce or maintain the gap, while higher ranks ($r=32,64$) tend to increase it. On Flickr30k, rank-4 achieves CG$\Delta = -0.027$ and rank-16 achieves the best R@1 of 0.702.`

**Run 2 — 21 words** (`paper/sections/experiments.tex:86` ↔ `paper_ap3/sections/04_mechanism.tex:28`)

- P1: `On Flickr30k, text-only reduces the gap by twice as much as both-position fine-tuning ($-$0.064 vs. $-$0.032). On BLIP-1, text-only produces substantially smaller gap increase ($+$0.047 vs. $+$0.152).`
- ap3: `On Flickr30k, text-only reduces the gap by twice as much as both-position fine-tuning ($-0.064$ vs.\ $-0.032$). On BLIP-2, text-only produces substantially smaller gap increase ($+0.047$ vs.\ $+0.152$).`

Both are **results sentences carrying numbers**, not a shared metric definition or a standard method
description. Both are short (21 and 27 words), both are in a parked, never-submitted manuscript, and neither
appears in A1, A23, P2 or P3. Run 2 additionally changes the model name (`BLIP-1` → `BLIP-2`) between the two
copies while leaving the numbers identical — see finding **9**.

### 1.2 What is *not* shared (the honest counterweight)

- **A1, A23, P2, P3: zero runs of ≥20 words.** The closest near-verbatim window measured a 5-gram Jaccard of
  well under 0.5. Where these manuscripts carry P1 content they paraphrase it and cite it.
- **A shared *definition* of the metric is a different matter and is present.** The Centroid Gap
  `G_C = \|\mu_I - \mu_T\|_2` and the distributional term are shared between
  `paper/sections/methodology.tex:8–10` and `paper_ap3/sections/04_mechanism.tex:10–11`, and both derive the
  terminology from a third party: `paper/sections/methodology.tex:6` "adopting the terminology
  of~\cite{liu2026tpc,cheng2026maab} but with a distinct variance-based formulation" against
  `paper_ap3/sections/04_mechanism.tex:13` "We adopt the CG/DG terminology of~\cite{liu2026tpc} … but
  instantiate $G_D$ differently". **This is a legitimate shared formal definition and I do not score it as
  overlap.** Likewise the 116-experiment design description and the dataset/training-protocol sentences are
  near-identical in substance across P1 and ap3, but are re-worded and are standard method boilerplate.
- **`paper合/` (Paper A, the P1+P2 Springer merge: `paper合/main_springer.tex`) is *not* in the brief's scope
  but is by far the largest textual overlap with P1 in the workspace** — 20 qualifying runs, **1,413 shared
  words**, concentrated in `paper合/sections/supplement.tex` (10 runs / 897 words), `related_work.tex`
  (5 runs / 376 words) and `empirical.tex` (3 runs / 92 words). Largest single run: 320 words of P1's
  `tab:full_experiments` catalogue reproduced verbatim at `paper合/sections/supplement.tex`. This is the real
  textual-overlap exposure in the workspace and it should be resolved before any of these manuscripts goes out;
  I report it here as a **note (finding 15)** because it is outside the commissioned scope.

---

## 2. Findings, ordered by severity

### 2.1 Must fix

---

**[1] — The only verbatim overlap with any companion manuscript is two results sentences reproduced inside the parked P1+P2+P3 merge, one of which silently renames the model.** (Must fix **if `paper_ap3/` is ever revived**; otherwise note-only.)

*Evidence*: run 1 and run 2 quoted verbatim in §1.1, with `paper/sections/experiments.tex:58,86` and
`paper_ap3/sections/04_mechanism.tex:57,28`. `paper_ap3/main.tex` header records the origin of the chapter
(both files scanned; `paper_ap3/sections/04_mechanism.tex:4` "These experiments, spanning 116 runs, establish the
regularities that the dynamical theory of Section~\ref{sec:theory} formalizes").

*Why it matters*: a 27-word verbatim results sentence is exactly what a similarity checker (iThenticate) reports,
and the parked merge is a real destination if PR rejects P1 — `docs/PA_P3_MERGE_PLAN.md:6` (record):
"P1（PR, PR-D-26-10149）收到拒稿通知 → 启动合并". If that trigger fires, the *same author, same 116 experiments,
same table values* will appear in a new submission carrying 27- and 21-word verbatim residues.

*Fix*: before any ap3 submission, rewrite `paper_ap3/sections/04_mechanism.tex:57` and `:28` from scratch (do not
merely add the LaTeX style differences), and decide explicitly whether §4 is a *restatement* of P1's empirical
chapter or a *summary with citation*. Given finding **9**, decide once and propagate the model name.

---

**[2] — P1 carries no disclosure of the companion work it will be judged against, and P1's own cover-letter files are correction letters, not the submission letter.**

*Evidence — what P1's own files do and do not say*
- `paper/cover_letter.tex` is **not** a submission letter: dated `August 14, 2026` (line 19), its subject line is
  `\textbf{Re: Manuscript PR-D-26-10149 --- Corrected Version}` (line 24) and its body begins "I am writing to
  request the replacement of manuscript PR-D-26-10149 … with a corrected version, prior to review." (line 37).
  It contains six enumerated corrections and **no** paragraph about other manuscripts.
- `paper/cover_letter_zeroshot_correction.tex` is likewise a correction letter: `\textbf{Re: Manuscript
  PR-D-26-10149 --- Second Correction (Zero-Shot Results)}` (line 24), "currently under review" (line 37). It
  likewise contains **no** disclosure.
- The shipped PDFs confirm these are what the journal saw: the text extracted from `paper/cover_letter.pdf`
  begins "`August 5, 2026 Re: Manuscript PR-D-26-10149 — Corrected Version`"; `paper/cover_letter_zeroshot_correction.pdf`
  begins "`August 14, 2026 Re: Manuscript PR-D-26-10149 — Second Correction (Zero-Shot Results)`". **No submission
  cover letter for P1 exists anywhere in `paper/`** (`glob paper/**/*` enumerated: no third letter file).
- The manuscript itself is silent. Mechanical search of all eight P1 source files for
  `companion|concurrent|in preparation|under review|wan2026` returns **no hit**; the only hits in `paper/` are in
  `REVIEW_DEFENSE.md`, an internal note. `paper/references.bib` contains **no** `Wan` author entry, and the
  compiled bibliography has **no self-citation** — P1 cites 40+ works and none of them is the author's own.

*What the companions say about P1* (as of 2026-08-23, so all of these post-date P1's submission and are cited here
only to establish that the relationship is real and public to the other journals):

| where | quote |
|---|---|
| `paper2/sections/discussion.tex:16` | "Our companion study~\citep{wan2026protect} discovered the empirical regularity that text-only fine-tuning preserves alignment across 5 architectures (116 experiments)." |
| `paper2/cover_letter.tex:19` | "This paper provides the \textbf{dynamical theory} for the empirical phenomenon discovered in our companion paper (Wan et al., ``Protect, Don't Perturb,'' under review at Pattern Recognition)." |
| `paper3/paper_ieee/sections/introduction.tex:11` | "The authors' companion study~\cite{wan2026protect,wan2026gap} bridged this gap by introducing \emph{Gap Susceptibility} …" |
| `paper3/paper_ieee/sections/discussion.tex:15` | "The companion empirical study~\cite{wan2026protect} found that text-only fine-tuning overwhelmingly preserves alignment across 5 architectures." |
| `paper_a1/cover_letter.tex:47` | "\textbf{Relation to other manuscripts.} A companion empirical study by the same author (``Protect, Don't Perturb …'') is currently under review at \textit{Pattern Recognition} (manuscript PR-D-26-10149)." |
| `paper_a2/cover_letter.tex:32` | "\textbf{Companion works (disclosure).} … the parameter-efficient fine-tuning results generalize my earlier study under review at \emph{Pattern Recognition} (PR-D-26-10149)." |

*Why it matters*: on 2026-08-23 the author already had a manuscript that describes itself as the theory *of this
paper* — `paper2/main.tex:73` opens its abstract "A companion empirical study established that text-only
fine-tuning overwhelmingly preserves cross-modal alignment … and that the modality gap strongly predicts retrieval
degradation ($r=-0.827$)." The editor who sees P1 beside any of these will ask what the relationship is. Every one
of them declares it; the flagship manuscript does not, because there is no submission letter in the archive and no
related-work disclosure in the text. **This is not an inference about intent — it is a gap in the record.**

*Fix* (and it is cheap): add a short "Relation to other manuscripts" paragraph to the P1 submission letter (or,
on revision, to the Response-to-Reviewers / Declaration), naming the theory companion and its status, exactly as
A1 and A23 already do. Do **not** claim exclusivity. Do not quote P1's own zero-shot figures as if the companion
had already been judged.

---

**[3] — The DG/retrieval-prediction result (`r=−0.827`, partial `−0.807`, `n=81`) is stated as an own discovery inside two never-submitted manuscripts with no citation to P1, while four other manuscripts cite it properly.** (Must fix: cite it in the two manuscripts that restate it.)

*Evidence*
- First appearance — P1: `paper/sections/experiments.tex:158` "The Distribution Gap (final) achieves strong
  negative correlation with \Rk{1} ($r = -0.827$, $p < 0.001$), substantially outperforming the Centroid Gap
  ($r = -0.683$). Crucially, the partial correlation of DG with \Rk{1} after controlling for CG remains
  $r = -0.807$ …"; headline claim in `paper/main_nn.tex:54–56` and in all five `paper/highlights.tex:10`.
- Re-reported *without citation* — `paper_ap3/sections/04_mechanism.tex:71` "Across the $n=81$ complete
  experiments …, DG achieves $r = -0.827$ with R@1, substantially outperforming CG ($r = -0.683$)."; `:80`
  "Controlling for CG via partial correlation, DG retains $r = -0.807$ ($p < 0.001$)"; the same numbers are a
  contribution bullet in `paper_ap3/sections/01_intro.tex:14` ("identifies the modality gap as the state variable
  that predicts retrieval degradation ($r=-0.827$)"). The chapter is labelled as fresh work ("a systematic
  116-run characterization"), not as a restatement of P1.
- Re-reported *without citation* — `paper合/sections/empirical.tex:71,90,97` reproduces the same three
  correlations plus a derived clustered bootstrap ($-0.847$, 98 experiments, 14 clusters) that exists **only** in
  `paper_ap3/sections/04_mechanism.tex:97` and nowhere in P1.
- Cited properly elsewhere — `paper_a1/main.tex:569` and `paper_a2/main.tex:75` both attribute the finding to
  `\cite{wan2026protect}` / `\citep{wanP1}`, and A23 uses it only as motivation ("text-only LoRA was the dominant
  prescription in our empirical study").

*Why it matters*: this is the one P1 result that another never-submitted manuscript states as its own discovery
with the identical value. A reviewer comparing the two would call it duplicate reporting of a result, not a shared
definition.

*Fix*: in `paper_ap3/sections/04_mechanism.tex` (and `paper合/sections/empirical.tex`), mark the DG-prediction
block as a summary of the P1 result with an attribution sentence, or drop the block and cite P1. If ap3 is
submitted *before* P1 is accepted, say so in its cover letter.

---

### 2.2 Should fix

---

**[4] — P1's own 116-experiment empirical core is re-used as a full chapter of `paper_ap3` under a different provenance label, with the model renamed and the numbers identical.**

*Evidence (structural, not verbatim — this is the bulk of the overlap)*

| P1 | ap3 | note |
|---|---|---|
| `paper/sections/experiments.tex:6` "We conduct 116 experiments spanning LoRA rank sweeps, position variants, scaling factor ablations, target module configurations, PEFT method comparisons …" | `paper_ap3/sections/04_mechanism.tex:4` "These experiments, spanning 116 runs, establish the regularities …"; `01_intro.tex:14` "a systematic 116-run characterization over four backbone families (CLIP ViT-B/32, CLIP ViT-L/14, BLIP-2, SigLIP)" | same 116, same axes |
| `paper/sections/experiments.tex:75–84` `tab:position` (Text-only/Both/Vision-only/Fill-FT × Flickr/COCO/Adapter/BLIP-1) | `paper_ap3/sections/04_mechanism.tex:34–44` `tab:position` (Text-only/Both/Vision-only × Flickr30k/COCO/BLIP-2/ViT-L) | cells identical: `Flickr30k & $\mathbf{-0.064}$ & $-0.032$ & $-0.003$` in both (`experiments.tex:77` ↔ `04_mechanism.tex:38`); the Adapter and Full-FT columns are dropped |
| `paper/sections/experiments.tex:215` "Table~\ref{tab:zeroshot} shows that text-only fine-tuning preserves zero-shot accuracy almost intact ($-0.6\%$) … full fine-tuning collapses zero-shot accuracy to near-chance levels (mean $2.6\%$, range $0.1$--$4.1\%$ across 3 retrained seeds)." | `paper_ap3/sections/04_mechanism.tex:113` "On ImageNet, text-only preserves 58.66\% accuracy ($-0.6\%$ vs.\ frozen), both-position stays at 59.67\% ($+0.4\%$), and full fine-tuning collapses to near-chance levels (mean $2.6\%$, range $0.1$--$4.1\%$ across 3 retrained seeds)." | same numbers |
| `paper/sections/experiments.tex:58` rank sweep results | `paper_ap3/sections/04_mechanism.tex:57` | verbatim (finding **1**) |
| `paper/sections/visual_fragility.tex:4` (whole section, "Visual Fragility Interpretation") | `paper_ap3/sections/04_mechanism.tex:99–109` (whole subsection, same name, same three evidence lines) | re-worded, no citation |

*Why it matters*: "spans 116 runs" is presented in ap3 as the paper's own characterisation, not as a summary of
another submitted manuscript. This is the largest single block of recycled scientific content in scope and it is
what a reviewer would point at. It is *paraphrased*, so it is not a text-similarity violation — it is a
**provenance** problem.

*Fix*: in ap3, either (a) add a one-line provenance note to `04_mechanism.tex` naming the prior empirical study,
or (b) treat §4 as a compressed summary chapter and say so in the introduction. Keep the difference between
"we summarise our earlier 116-run study" and "we conduct 116 runs" explicit.

---

**[5] — The measured finding P1 regards as its central result is contradicted on the same data by A1, and P1's claim is stated in a form broad enough that it reads as a duplicate claim when the two are seen together.** Should fix (framing), note (no action possible at the journal).

*Evidence*
- P1's claim, stated twice in the abstract and as finding 2: `paper/sections/introduction.tex:15` "\textbf{Text-only
  adaptation overwhelmingly yields the smallest alignment degradation} among evaluated configurations"; `paper/main_nn.tex:42–44`
  "\textbf{text-only fine-tuning preserves cross-modal alignment better than joint modality fine-tuning}"; and the
  slogan `paper/sections/conclusion.tex:14` "protect the visual encoder's parameters, fine-tune the text modality".
- A1's counter-measurement on the same checkpoints, P1's own numbers: `paper_a1/main.tex:116` "text-only
  ($\tau=0.791$, top-1 $58.8\%$) and both-position ($\tau=0.750$, top-1 $58.6\%$)", and `paper_a1/main.tex:23`
  "pure text-only (\Rk{1}=0.427) and full both-modality (\Rk{1}=0.510)" where both-position wins.
- A1 describes P1 accurately as prior work, and in the framing "the gap is right for retrieval, wrong for
  classification": `paper_a1/main.tex:569` "for retrieval-oriented adaptation, the gap (and its distributional
  extensions) is the right signal; for classification-oriented adaptation in the settings we test, order
  preservation $\tau$ is the more informative of the two signals".
- P1's abstract already concedes exceptions when reporting zero-shot, `paper/main_nn.tex:44–47` "with a few
  exceptions (e.g., SigLIP both-position and ViT-B all-layer text-only)".

*Why it matters*: this is not salami slicing — the two measurements are compatible once the task is named (P1's
text-only advantage is a *retrieval/centroid-gap* claim; A1's is a *zero-shot order-preservation* claim, and A1 says
so). The risk is editorial: an assessor reading "Protect, Don't Perturb" and "the gap is not a universal health
metric" written by the same author about the same checkpoints will ask whether P1's benefit is a *stated* fact
about one task being restated as if universal. P1's abstract sentence "preserves cross-modal alignment better"
leaves the task unstated.

*Fix*: in any P1 revision, scope the abstract's "cross-modal alignment" to the retrieval/centroid-gap regime, the
way P1's own `paper/sections/conclusion.tex:14` does ("[do not] claim visual fragility as the unique mechanism"),
and cross-reference the companion that found the boundary. This costs one clause and removes the whole surface of
the objection. Do **not** claim A1's result as a confirmation.

---

**[6] — `paper_ap3` (P1 + P2 + P3) is the terminal destination if P1 is rejected, and P1 material would reappear there wholesale; P1's revision disclosure has to anticipate that without naming a manuscript that is not yet a submission.**

*Evidence — what reappears, by inspection of `paper_ap3/`*
- §4 mechanism (P1 empirical chapter): 116-run design, `tab:position`, DG/CG correlations, Visual Fragility, ImageNet/DTD/Food101 zero-shot — all of it (finding **4**).
- §3b/§5 (P2 dynamics): `paper_ap3/sections/03b_special.tex:97` reproduces P1's causal evidence as a premise —
  "Section~\ref{sec:mechanism} showed that vision encoders exhibit higher sensitivity to perturbation (noise
  sensitivity $2.6\times$ greater, gradient contribution $1.5\times$)" — which is P1's
  `paper/sections/visual_fragility.tex:26`/`experiments.tex:215` finding restated in the theory chapter.
- §6 (P3 cross-architecture) adds the LLaVA/Qwen allocation work, which does **not** reuse P1 results.
- **What does *not* reappear**: P1's Route C/D/E strategy experiments, Text+Vis-L1, the $\alpha$–rank interaction,
  the layered fine-tuning catalog, and the DG-ES implementation details. Verified by grep: `DG-ES`,
  `DG-Guided Early Stopping`, `Text+Vis`, `Route C`, `Route D` return **no** hit under `paper_ap3/sections/`.
  A23 also drops them. **About a third of P1 is genuinely unique to P1** — that is worth stating in any response
  to an overlap query.
- The author has already ruled the naming question: `docs/A1_VENUE_DECISION.md:132–134` (record, operator
  instruction 2026-09-16) "**不要在任何投稿件中提及 `paper_ap3`** … 投稿件中不得提及 `paper_ap3`" and
  `:150` "A1/A23 的 cover letter、正文与参考文献中均不得出现 `paper_ap3` 的名称或标题."
- The merge plan also commits to anonymising the attribution, `docs/PA_P3_MERGE_PLAN.md:20` (record):
  "合并稿双盲安全（沿用 P3 已中性的自引；A1/A2 提及一律 ``the companion study'')".

*Why it matters*: P1 is the manuscript whose rejection *creates* ap3. If P1 is revised or resubmitted anywhere,
the same three companion manuscripts will exist alongside it, and the honest disclosure is "a theory companion
exists and cites this work" — not silence. Naming ap3 is both forbidden by the operator and factually wrong
(it is not a manuscript), so the disclosure must rest on P2/P3 by content, not on ap3 by name.

*Fix*: when P1 is revised/resubmitted, add to the cover letter one sentence of the A1/A23 form — e.g. "A companion
theoretical study of gradient-flow gap dynamics by the same author builds directly on the empirical regularities
reported here; the present paper does not report any of that theory's results." Verify that the sentence is true
before sending: on the evidence above it is true of P1's *text*, but P1's `r=−0.827` and `2.6×` numbers are quoted
inside the companion, so the reverse direction is the one that needs the citation.

---

### 2.3 Notes

---

**[7] — P1 has no self-citation at all, which is unusually clean: the risk is a *missing* disclosure, not a hidden one.** `paper/references.bib` contains no `Wan` entry (mechanical search) and the compiled `paper/main_nn.tex:82–83` bibliography is third-party only. A1 (`main.tex:605`), A23 (`main.tex:885`), P2 (`discussion.tex:16`), P3 (`main.bbl:76,80`) all cite P1. The direction of the disclosure gap is therefore one-way and the fix is one paragraph (finding **2**).

**[8] — The `−0.064 vs −0.032 ↔ −0.041` divergence: P1's Flickr30k text-only gap change is re-quoted in A23 against a different comparator, and the two manuscripts call both quantities "text-only vs both".**
- P1, first use: `paper/sections/experiments.tex:86` "text-only reduces the gap by twice as much as both-position
  fine-tuning ($-$0.064 vs. $-$0.032)" — both cells are rank-8 position variants on Flickr30k
  (`paper/sections/supplementary.tex:33–34` `rq2\_text\_only & $r$=8 & text\_only & $-$0.064 & 0.627`;
  `rq2\_both & $r$=8 & both & $-$0.032 & 0.700`).
- A23, first use: `paper_a2/main.tex:32` (abstract) "parameter-efficient fine-tuning (PEFT) preserves marine
  zero-shot ($-2.8\%$ to $-8.1\%$)"; the `−0.064` itself is quoted as *both-position on Flickr30k* in the
  same sentence shape — `paper_a2/main.tex:170` and `paper_a2/ext_partI_theory.tex` describe the terrestrial
  control as a Flickr30k fine-tune, and A23's terrestrial LoRA row reports `−0.041`
  (`paper_a2/main.tex:499` UATD row `$-0.041$`; the marine table reports text-only `−0.064`). Both values are in
  the same `−0.06/−0.04` band as P1's two cells, but the *pairing* differs.
- This is **not** a duplicate publication: P1's pair is a position contrast at fixed rank, A23's is a
  PEFT-vs-full-FT or marine-vs-terrestrial contrast, and A23 never reports a `−0.064 vs −0.032` sentence.
  But an editor holding both PDFs sees the same number labelled as two different things.

**[9] — The BLIP-1 / BLIP-2 divergence is a cross-manuscript code-name inconsistency, and it should be resolved before either manuscript is published.** P1: `paper/sections/experiments.tex:86` "On BLIP-1, text-only produces substantially smaller gap increase ($+$0.047 vs. $+$0.152)"; `paper/sections/experiments.tex:31` "BLIP-1 & 7 & \textbf{$-$0.476} & 0.175"; the methodology names it `paper/sections/methodology.tex:20` "BLIP-1~\cite{li2022blip}". ap3 renames the same experiment: `paper_ap3/sections/04_mechanism.tex:15` "BLIP-2 (350M, Q-Former)~\cite{li2023blip2}" and `:28` "On BLIP-2, text-only produces substantially smaller gap increase ($+0.047$ vs. $+0.152$)". `docs/PA_P3_MERGE_PLAN.md:42` (record) shows this was a deliberate renaming during the ninth audit round ("⑮\textbf{BLIP-1→BLIP-2(350M, Q-Former)} + 新增引用"). Two manuscripts describing one experiment under two model names is precisely the kind of thing an overlap check surfaces, and it also inflates the apparent number of experiments across the author's body of work.

**[10] — P1's abstract says the 116 experiments are the "first systematic study"; A1 and A23 both assert their own priority over the same family of quantities.** P1: `paper/main_nn.tex:39–41` "Through 116 experiments … we conduct the first systematic study of modality gap evolution during fine-tuning." A1: `paper_a1/cover_letter.tex:51` "this is the first work to … identify order preservation as the operative health quantity". A23: `paper_a2/cover_letter.tex:29` "To my knowledge, no published work analyses the alignment structure of marine or sonar vision-language models". The three priority claims are about different quantities and do not literally conflict; the risk is an editor reading three "first" claims by one author in one year.

**[11] — P1's internal abstract/highlights claim is contradicted by P1's own correction letter, and both exist in the same submission file set.** `paper/highlights.tex:9` "Text-only overwhelmingly preserves cross-modal alignment across three model families" and `paper/main_nn.tex:45–47` "limits zero-shot degradation to $0.6$ percentage points" versus the enclosed
`paper/cover_letter_zeroshot_correction.tex:44` "the previous statement that both-position fine-tuning degrades zero-shot accuracy $3\times$ more than text-only is removed". Not an overlap finding; recorded because it is the sort of inconsistency an editor may raise under the same heading, and because the corrected zero-shot table (`59.37/58.76/59.67/0.13`) is the version that any cross-manuscript number comparison must use.

**[12] — P2's and A1/A23's disclosure practice is genuinely good and should be the template.** P2 devotes an entire subsection to the relationship: `paper2/sections/discussion.tex:16–33` "Our companion study … Table~\ref{tab:companion} summarizes the relationship" with a two-column table whose "Core question" row reads "`\emph{What} happens?` / `\emph{Why} does it happen?`". A1 has `paper_a1/cover_letter.tex:47`; A23 has `paper_a2/cover_letter.tex:32`; and A23's manuscript cites both companions by name in the bibliography (`paper_a2/main.tex:883–885`). P3's IEEE build carries the companion as a normal citation (`paper3/paper_ieee/main.bbl:76,80`). **P1 is the only manuscript in the set with no disclosure, and it is the one whose result the others depend on.**

**[13] — A23's *internal note* and A23's *cover letter* disagree about disclosing P1; the shipped letter is the honest version.** `docs/A23_JOE_INQUIRY.md:36` (record) "**只披露 A1（`NEUCOM-D-26-20952`），不披露 P1（`PR-D-26-10149`）**…（操作者的决定（2026-09-16）)" with the reasoning "第一封邮件里摆两篇"under review"的自引，容易招来 salami/重叠问询，收益为负"; yet the letter actually carried in the manuscript folder, `paper_a2/cover_letter.tex:32`, *does* disclose P1 ("the parameter-efficient fine-tuning results generalize my earlier study under review at \emph{Pattern Recognition} (PR-D-26-10149)"). Whether that was a draft note or a late revision, the record and the artefact do not agree, and the artefact is the more defensible one. **Do not "fix" the letter to match the note.**

**[14] — `paper_a2/main.tex:46` still understates the companion it builds on, which is the reverse of the P1 problem.** "That analysis, however, spans five zero-shot benchmarks (ImageNet-1K, DTD, Food-101, iNaturalist-wild and a rare-species set), three contrastive model families (CLIP, OpenCLIP and SigLIP) and sixteen fine-tuned checkpoints, yet remains confined to general-purpose (terrestrial) models." — this describes **A1**, not P1, yet the sentence sits in the paragraph introduced as "our companion study \citep{wanA1}"; the second companion (P1) enters only one paragraph later at `:75`. `docs/CITATION_INTEGRITY_AUDIT.md:191` (record) records the same defect. A reader cannot tell from the introduction which companion is which.

**[15] — out-of-scope but material: `paper合/` (Paper A, the P1+P2 Springer merge) is the largest P1 text-overlap in the workspace.** 20 runs ≥20 words, **1,413 words total**, all in `paper合/`: `sections/supplement.tex` 10 runs/897 words (largest single run **320 words** of P1's `tab:full_experiments`), `sections/related_work.tex` 5 runs/376 words (largest 172 words, P1's entire "The Modality Gap in Contrastive VLMs" opening), `sections/empirical.tex` 3 runs/92 words including the 37-word `−0.064 vs −0.032` sentence. `paper合/main_springer.tex:43` also opens its abstract with the same "A companion empirical study established …" sentence as `paper2/main.tex:73`. Not in the commissioned scope (the brief names `paper_ap3/` as the P1+P2+P3 merge), but if Paper A is ever revived it is the manuscript with the real verbatim problem, and it is worth resolving before ap3, because ap3's §4 is the *less* overlapping descendant of the same content.

---

## 3. Claim-by-manuscript table

Legend: **FIRST** = first report / origin of the claim; **RE** = re-reported as own result, no citation;
**SUM** = re-reported but explicitly as a summary of the other work; **CITE** = cited only, used as prior work;
**—** = absent. Line refs are the location of the strongest statement in each manuscript.

| # | claim / result | P1 | P2 | P3 | A1 | A23 | ap3 |
|---|---|---|---|---|---|---|---|
| 1 | **Modality gap is a poor health proxy** (for zero-shot) | — (P1 asserts the opposite for retrieval: `main_nn.tex:54–56`) | — | — | **FIRST** `main.tex:32`, `:103` | RE/EXT `main.tex:70` (extends to marine/sonar) | — |
| 2 | **Kendall order-preservation $\tau$** as the operative quantity | — | — | — | **FIRST** `main.tex:54,73,243` | RE + CITE `main.tex:46,70` (`\citep{wanA1}`) | — |
| 3 | **Centroid Gap / Distribution Gap decomposition** | SHARED USE `methodology.tex:6–10` (terminology attributed to `liu2026tpc`) | — | — | — | SHARED USE `main.tex:116` | SHARED USE `04_mechanism.tex:8–13` (same attribution) |
| 4 | **Text-only > joint fine-tuning (PEFT)** | **FIRST** `main_nn.tex:42–44`, `introduction.tex:15`, `experiments.tex:86` | CITE as premise `introduction.tex:3`, `discussion.tex:16` | CITE `discussion.tex:15` | — | RE (marine/matched-scale) `main.tex:57,327` + CITE `main.tex:75` | RE verbatim+paraphrase `04_mechanism.tex:19,28,57` |
| 5 | **PEFT preserves / full-FT destroys zero-shot** | **FIRST** `experiments.tex:215`, `main_nn.tex:45–47` | CITE `introduction.tex:3` (via P1) | — | — | RE (domain-relative, marine) `main.tex:32,327` | RE `04_mechanism.tex:19,113` |
| 6 | **DG predicts retrieval ($r=-0.827$, partial $-0.807$)** | **FIRST** `experiments.tex:158`, `main_nn.tex:54` | CITE `discussion.tex:10` | CITE `main.bbl:80` | CITE `main.tex:44,569` | CITE (motivation only) `main.tex:75` | **RE, no citation** `04_mechanism.tex:71,80,97`, `01_intro.tex:14` |
| 7 | **DG-based monitoring + DG-Guided Early Stopping** | **FIRST** `methodology.tex:22–30`, `conclusion.tex:12`; `highlights.tex:12` | CITE (as motivation) `discussion.tex:85` | — | CITE `main.tex:44` ("gap-aware early stopping has been proposed") | — (replaces with $\tau$-monitoring) `main.tex:632` | DROPPED (§4 keeps the principle, `07_discussion.tex:29`) |
| 8 | **Visual Fragility Interpretation** (incl. $2.6\times$ noise, GSNR $1.5\times$, effective rank) | **FIRST** `visual_fragility.tex:4`, `experiments.tex:215`, `main_nn.tex:50–53` | — | CITE `appendix.tex:98–99` | — | — | RE `04_mechanism.tex:99–109`, `03b_special.tex:97` |
| 9 | **Class bias field / gap surgery analysis** | — (P1 has no surgery; opposed framing) | — | — | **FIRST** `main.tex:92–96,163–166,189` | EXT + CITE `main.tex:46,70`; `ext_partI_theory.tex:19` | — |
| 10 | Clustered bootstrap on the DG–R1 correlation ($-0.847$, 98 exp / 14 clusters) | — | — | — | — | — | **FIRST** `04_mechanism.tex:97` (and `paper合/sections/empirical.tex:97`, a different estimator: $-0.819$, 94 exp / 79 clusters) |
| 11 | 116-run config-space enumeration, `tab:position`, ImageNet/DTD/Food101 zero-shot | **FIRST** `experiments.tex:6,75,215` | — | — | — | partial reuse ($-0.064$, `−0.041`) | RE `04_mechanism.tex:4,19,28,34,113` |
| 12 | Route C/D/E, Text+Vis-L1, $\alpha$–rank interaction, layered-FT catalog, DG-ES implementation | **FIRST, P1-only** `experiments.tex:177–207`, `discussion.tex:24–30`, `supplementary.tex:236–238` | — | — | — | — | — (dropped) |

**Reading of the table.** Every one of the eight items the brief asks about resolves to *one* manuscript of origin —
and, notably, **P1 is the origin of only four of them** (4, 5, 6, 7, 8 minus the ones that are shared terminology),
while A1 originates 1, 2 and 9, and ap3 originates only the bootstrap (10). The three-way split is
**mechanism-empirical (P1) / order-preservation theory (A1) / dynamical + allocation theory (P2+P3)**, and the
marine/sonar extension (A23) is downstream of A1 with P1 used only as motivation. That is a defensible
programme-level division of labour, not salami. The defects are the *unattributed* re-reports (rows 6, 8, 11) and
the *missing* disclosure (finding **2**), not the existence of three papers.

---

## 4. Novelty split for P1

**What P1 contributes that the others do not.** P1 is the only manuscript in the set that (i) reports the
*full 116-run configuration sweep* — rank $\times$ position $\times$ $\alpha$ $\times$ target-module $\times$
method over five architectures and two retrieval datasets (`paper/sections/experiments.tex:6`, `tab:overview`
`:20–51`) — including the strategy experiments (Route C/D/E, Gap-Reg, Gap-Init, $\alpha$ annealing) at
`experiments.tex:177–207`, the Text+Vis-L1 layered configuration at `discussion.tex:27`, and the
$\alpha$–rank interaction at `experiments.tex:190–207`; (ii) introduces and names the **Visual Fragility
Interpretation** with its three-pillar causal evidence (`visual_fragility.tex:4–37`: parameter-noise
$2.6\times$, GSNR $1.5\times$, effective-rank tracking); (iii) proposes **DG-based alignment monitoring** and
instantiates it as DG-Guided Early Stopping including a *negative result* (`experiments.tex:181`,
`discussion.tex:38`: premature stopping at \Rk{1}=0.133 vs. expected $\approx$0.63); and (iv) supplies the
`r=−0.827 / −0.807` retrieval-prediction estimate with its non-triviality checks
(`experiments.tex:241–249`). Verified by grep that items (i)'s Route/Text+Vis/DG-ES components appear in
**neither** ap3 **nor** A23.

**What P1 shares.** The Centroid Gap / Distribution Gap *definitions* (shared with ap3 and A23, all three
attributing the terminology to `liu2026tpc`); the 116-experiment *design* and `tab:position` values (re-used by
ap3 §4); the ImageNet/DTD/Food101 zero-shot table (re-used by ap3 §4); the Visual Fragility section (re-used by
ap3 §4 and cited by P3 appendix); the DG–R1 correlations (re-used as an uncited result by ap3 §4, cited as prior
work by A1, A23 and P2); and the "text-only is the dominant prescription" claim (which A1 both cites and
*delimits* by showing the zero-shot regime inverts it).

**What a sceptical editor would conclude about P1's marginal contribution, given the others exist.** The sharpest
available reading is this: P1's headline number (`r=−0.827`) is a correlation, its headline mechanism ("Visual
Fragility") is explicitly labelled by its own author as "a phenomenological interpretation … not a deductively
proven mechanism" (`visual_fragility.tex:4`, `conclusion.tex:10`), its monitoring proposal is reported as
brittle by its own experiments (`discussion.tex:38`), and the same author's other manuscripts then supply the
theory (P2/P3: $\Gamma_m$, the ODE, $R^2>0.96$) and the boundary condition (A1: the gap is not a universal
metric) that P1 leaves open. Read alone, that looks like the weakest of the set. Read fairly, P1 is the
*empirical foundation the other four manuscripts cite* — it is the only one that establishes the regularities
the others formalise or delimit, it is the only one with the full sweep, and it is the source of the causal
evidence P2/P3 and ap3 lean on. **The decisive question for the editor is therefore not "is this salami?" —
the metrics, the datasets, the task and the claim of each manuscript are demonstrably distinct — but "why did
the manuscript whose result the others depend on arrive with no disclosure of them?"** That question is
answerable in one paragraph and is unanswered in the current file set.

---

## 5. Disclosure audit, as of 2026-08-23

**Method.** `paper/cover_letter.tex` (66 lines) and `paper/cover_letter_zeroshot_correction.tex` (61 lines) were
read line by line; the shipped PDFs `paper/cover_letter.pdf` and `paper/cover_letter_zeroshot_correction.pdf`
were text-extracted and compared against their `.tex` sources (they match, with only typographic differences);
all eight P1 sources plus `highlights.tex`, `declaration.tex` and `title_page.tex` were searched for
`companion|concurrent|in preparation|under review|under consideration|wan2026|prior work|sister`.

| question | answer |
|---|---|
| Does P1 name the companion theoretical manuscript to the editor? | **No.** Neither letter contains any such sentence; both are correction letters whose entire body is an enumeration of corrected numbers. |
| Does P1 carry a submission cover letter at all? | **Not in the workspace.** The only two letters in `paper/` are the two correction letters (subject lines at `cover_letter.tex:24` and `cover_letter_zeroshot_correction.tex:24`). |
| Does the P1 manuscript disclose companion work? | **No.** Zero hits in all P1 sources. |
| Does P1 cite its own prior work? | **No.** `paper/references.bib` has no `Wan` author entry; the compiled bibliography contains no self-citation. |
| Are the companions cited as *prior work* elsewhere? | **Yes, in all four** — `paper_a1/main.tex:605`, `paper_a2/main.tex:885`, `paper2/sections/discussion.tex:16`, `paper3/paper_ieee/main.bbl:76`. |
| Does A1 or A23 fault P1? | **No.** A1's letter (`:47`) and A23's letter (`:32`) both describe the relationship accurately and without claiming P1's results. |
| Is P1's silence a *submission date* artefact? | **Partly exculpatory and partly not.** A1 and A23 did not exist as submissions on 2026-08-23, so P1 cannot be faulted for not naming `PRLETTERS-D-26-01941` or `OE-D-26-11643`. **But a companion theory manuscript whose abstract opens "A companion empirical study established that text-only fine-tuning overwhelmingly preserves cross-modal alignment … and that the modality gap strongly predicts retrieval degradation ($r=-0.827$)"** — `paper2/main.tex:73` — **and which was being prepared at the same time (`paper2/cover_letter.tex` is dated `July 3, 2026`) did exist, and P1 mentions neither the manuscript nor the plan.** The submission-date defence covers the *numbers*; it does not cover the *existence*. |
| Anything else that arguably should be disclosed? | (i) `docs/PA_P3_MERGE_PLAN.md:6` (record) makes ap3 *contingent on P1's rejection*, so the merge is a disclosed plan rather than a coincidence — but the operator has forbidden naming it in any submission (`docs/A1_VENUE_DECISION.md:132–134`), which means the disclosure must be phrased by content. (ii) `paper/REVIEW_DEFENSE.md:7–17` (internal note) shows the author had already prepared the sentence "Concurrent work (Wan, in preparation) finds consistent modality-gap dynamics in decoder-based VLMs" for a reviewer, i.e. the author's own template for disclosing companion work exists and was simply not used in P1's letters. (iii) `paper/main_nn.tex:80` "Data will be made available on request." is weaker than the companions' data statements (`paper_a2/cover_letter.tex:35` names a repository URL); a reviewer comparing them may read P1 as the least reproducible of the set, which is an unrelated but adjacent credibility cost. |

---

## 6. Coordination risk — forward-looking

1. **If P1 is rejected, ap3 becomes the vessel and P1 material reappears wholesale** (finding **4**): the 116-run
   design, `tab:position`, the DG correlations ($-0.827$/$-0.807$), the $2.6\times$/GSNR Visual Fragility evidence,
   and the ImageNet/DTD/Food101 zero-shot table, plus the two verbatim results sentences of §1.1. The
   parts of P1 that would *not* reappear (Route C/D/E, Text+Vis-L1, $\alpha$–rank, layered FT, DG-ES
   implementation) are exactly the parts an editor would regard as P1's incremental contribution over its own
   theory companions — so P1's *identity* would dissolve into ap3 while its *widely cited numbers* stay.
2. **The disclosure P1 should carry on revision is a "relationship" paragraph, not a duplicate-publication
   defence.** Model it on `paper_a1/cover_letter.tex:47` / `paper_a2/cover_letter.tex:32`: name the companion by
   *content and status* (a dynamical-theory companion of the same author that cites this work), state which
   results are P1's and which are the companion's, and claim no exclusivity. Do not name `paper_ap3`.
3. **Fix the two verbatim runs and the DG block before ap3 is ever submitted.** Findings **1** and **3** are the
   only two items that would survive a plagiarism scan with a hit; everything else is paraphrase plus
   missing attribution, which is fixed by a sentence.
4. **Resolve `BLIP-1` vs `BLIP-2` (finding 9) and the `−0.064` pairing (finding 8) once, centrally.** They are
   the only two *numeric* cross-manuscript inconsistencies found, and both would surface in an editorial
   overlap check as "the same experiment reported under two names / two comparisons".
5. **If the author ever wants to assert non-overlap to an editor, the strongest true statement available is:**
   P1 reports the 116-run PEFT configuration sweep, the Visual Fragility causal evidence and DG-based monitoring;
   A1 reports gap surgery, the Kendall order-preservation coefficient and the class bias field; P2/P3 report the
   gradient-coupling theory and cross-architecture allocation; A23 transfers A1's diagnostic to marine and sonar
   perception. The shared material is the Centroid/Distribution Gap *definitions*, which all three attribute to
   the same third-party source, and the fact that the other three cite P1 as prior work. No dataset, no
   experiment and no claim is published twice. That statement is supported by the evidence in §3 and is the
   sentence the author should be ready to write.

---

## 7. Files read / written

**Read (P1)**: `paper/main_nn.tex`, `paper/sections/{introduction,related_work,methodology,experiments,visual_fragility,discussion,conclusion,supplementary}.tex`, `paper/cover_letter.tex`, `paper/cover_letter_zeroshot_correction.tex`, `paper/highlights.tex`, `paper/references.bib` (author scan), `paper/REVIEW_DEFENSE.md`, `paper/FOR_ADVISOR.md`, `paper/1.md`, `paper/cover_letter.pdf` and `paper/cover_letter_zeroshot_correction.pdf` (text-extracted via zlib/stream parse), file timestamps for every file in `paper/`.

**Read (companions)**: `paper_a1/{main.tex, cover_letter.tex, related_work.tex, abstract.tex}`; `paper_a2/{main.tex, cover_letter.tex, abstract.tex, ext_partI_theory.tex, ext_partIII_dynamics.tex, ext_partV_mechanisms.tex}`; `paper_ap3/{main.tex, sections/01_intro.tex, sections/04_mechanism.tex, sections/05_dynamics.tex, sections/03b_special.tex, sections/07_discussion.tex, sections/appendix.tex}`; `paper2/{main.tex, cover_letter.tex, sections/introduction.tex, sections/theory.tex, sections/experiments.tex, sections/discussion.tex, sections/conclusion.tex}`; `paper3/paper_ieee/{main.bbl, sections/introduction.tex, sections/discussion.tex, sections/appendix.tex}`; `paper合/{main_springer.tex, sections/empirical.tex, sections/related_work.tex, sections/supplement.tex, sections/introduction.tex}` (out-of-scope cross-check).

**Read (records, labelled as such, never used as evidence)**: `docs/A23_ROUND3_REVIEW.md` (register template), `docs/PA_P3_MERGE_PLAN.md`, `docs/A1_VENUE_DECISION.md`, `docs/A23_JOE_INQUIRY.md`, `docs/CITATION_INTEGRITY_AUDIT.md`.

**Method artefacts** (computed in-memory, nothing written): markup-stripped word-token index over 77 `.tex` files in `paper_ap3`, `paper合`, `paper_a1`, `paper_a2`, `paper2`, `paper3` versus the eight P1 source files; maximal common word-run extraction with a 20-word floor (any seed pair extended in both directions, contained runs removed); 5-gram Jaccard pass over sliding 22-word windows (floor 0.5, 6-gram overlap required) which returned **zero** hits; function-word-removed 6-gram comparison of P1 against P2 and P3 sources (zero hits at floor 2).

**Written**: `docs/P1_REVIEW_OVERLAP.md` (this file) — only.

**Not modified**: every file under `paper/`, `paper_a1/`, `paper_a2/`, `paper_ap3/`, `paper合/`, `paper2/`, `paper3/` and `docs/`. No LaTeX was compiled and no PDF was regenerated; the overlapping-scan script was executed from stdin so that no temporary file was created in the workspace or elsewhere.
