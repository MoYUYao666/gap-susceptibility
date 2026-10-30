# Paper A desk rejection at Neurocomputing and the Elsevier transfer offer

**Recorded**: 2026-10-26. **Source**: editor e-mail forwarded by the author (verbatim quoted below).

## Facts

| Field | Value |
|---|---|
| Manuscript | Paper A, `paper合/` (Neurocomputing variant `main_nc.pdf` 79 pp; Springer variant 56 pp) |
| Journal | Neurocomputing (Elsevier) |
| Reference number | **NEUCOM-D-26-23760** |
| Decision | **Desk rejection** - "not sent for external review" |
| Deciding editor | Ana Carolina Lorena, Associate EIC |
| Date of the e-mail | 2026-10-26 (as forwarded) |
| Offered alternative | **Elsevier article transfer service** (manuscript files and details can be transferred to another journal) |
| **Deadline to accept or decline** | **2026-11-24 23:59** |

**Editor's stated reasons (verbatim)**: "the work does not meet the level of originality, depth of analysis, and overall
scholarly contribution expected for publication in the Neurocomputing journal"; "we are able to advance only those
submissions that demonstrate a clear and substantial contribution to the field, supported by rigorous methodology and
presentation at the highest standard"; "we must decline the manuscript in its current form".

## What this does NOT change

- The manuscript's scientific content is unchanged: every number, control and limitation in the current draft is the
  same material that passed the gate suite (six profiles READY grade A, `_p1454` PASS WITH 13 WARNINGS).
- The frozen submitted package `SUBMISSION/PaperA_Neurocomputing/` stays frozen; the live drafts keep advancing.

## Decision framework (target must be SCIE - standing rule)

The transfer service only offers Elsevier journals. Under the repository rule, a target is admissible only if it is
**SCIE** in the Web of Science Core Collection, registered in `docs/VENUE_SCI_REGISTRY.md` with a real source URL and
verification date. Candidate Elsevier journals worth screening (none verified yet):

| Candidate | Why it could fit | Status |
|---|---|---|
| Pattern Recognition (Elsevier) | methodology + negative results are publishable there; broad readership | **SCIE ✅**（2026-10-26 MJL；20–35 页） |
| Information Fusion (Elsevier) | multimodal alignment/representation analysis | **SCIE ✅**（2026-10-26 MJL；10–35 页、≤50 refs）|
| Knowledge-Based Systems (Elsevier) | theory + empirical characterisation | **SCIE ✅**（2026-10-26 MJL；≤20 双倍行距页）|
| Engineering Applications of Artificial Intelligence (Elsevier) | PEFT/adaptation applications | **SCIE ✅**（2026-10-26 MJL；≤50 页）|
| Image and Vision Computing (Elsevier) | vision-side framing | **SCIE ✅**（2026-10-26 MJL；正文 4500–7500 words）|
| Computer Vision and Image Understanding (Elsevier) | vision-side framing | **SCIE ✅**（2026-10-26 MJL；guide 无页数硬限）|
| Applied Soft Computing (Elsevier) | extra candidate | **SCIE ✅**（2026-10-26 MJL；20–30 页、至多 50）|
| Expert Systems with Applications (Elsevier) | extra candidate | **SCIE ✅**（2026-10-26 MJL；guide 无页数硬限）|
| Neural Networks (Elsevier) | **excluded** - already desk-rejected this same manuscript family as `NEUNET-D-26-09426` | disqualified |

> **2026-10-26 更新（SCIE 核验已完成）**：上表 8 刊均按 registry §2 用 MJL 核实为 **SCIE**，并逐刊记录
> guide for authors 的页数/字数限制与 Paper A 契合度评估 ⇒ 见 `docs/venue_transfer_candidates_2026-10-26.md`
> 与 `docs/VENUE_SCI_REGISTRY.md` §4.4/§4.5。**资格不是区分项，篇幅与 scope 才是。**

Decision options:
1. **Accept the transfer** to an SCIE-verified Elsevier journal that the service actually lists for this manuscript.
   Pros: no reformatting, fast. Cons: the transfer keeps the current framing, which is exactly what the editor judged
   as insufficient contribution; a second desk rejection is the likely outcome unless the framing is fixed first.
2. **Decline and resubmit after a reframing pass** to an SCIE target chosen for fit (possibly non-Elsevier).
   Pros: addresses the actual criticism (framing, length, contribution statement). Cons: reformatting work.

**Recommendation**: any transfer should be preceded by the same fix that a fresh submission would need - the desk
rejection is a *framing/length* signal, not a data signal: 79 pages, theory-first structure, and a large negative-result
section read as "no clear contribution". Before answering the transfer offer, do a reframing pass that (a) states the
contribution on the first page in one sentence a non-specialist editor can accept, (b) moves the negative results into
a clearly labelled section rather than threading them through, (c) cuts the Neurocomputing variant's length
substantially, and (d) picks the target by fit. Then use the transfer (if it lists that journal) or a fresh submission.

## Verbatim editor mail

```
Ms. Ref. No.: NEUCOM-D-26-23760
Title: Adaptation Site and the Modality Gap: Empirical Regularities and a Gradient-Flow Theory for PEFT of Contrastive Dual-Encoders
Journal: Neurocomputing

Dear Mr Wan,

Thank you for your interest and submission to "Neurocomputing". Unfortunately, after an initial evaluation, I feel your manuscript is not appropriate for this journal's readership.

However, I do think it could be considered by another journal, and I would like to suggest that you take advantage of the article transfer service that "Neurocomputing" is part of. ...

Please confirm by Nov 24 2026 11:59PM whether you would like to accept this transfer offer ...

Comments to Authors:
After careful editorial evaluation, we regret to inform you that the manuscript will not be sent for external review. While the topic falls within the general area of interest of the journal, the work does not meet the level of originality, depth of analysis, and overall scholarly contribution expected for publication in the Neurocomputing journal. ...

For these reasons, we must decline the manuscript in its current form.
```

## Decision (2026-10-26, operator)

**Decline the Elsevier transfer offer; reframe the manuscript first and submit it fresh.**

Rationale: the transfer preserves the current framing, which is exactly what the editor rejected; a second desk
rejection is the likely outcome. The deadline is 2026-11-24, so there is room for a reframing pass before any decision
has to be defended.

Plan:
1. Reframing pass (started 2026-10-26): new title, a one-sentence contribution statement a non-specialist editor can
   accept on page 1, negative results promoted to their own labelled section, main text cut from 79 to roughly 30-40
   pages with the detailed tables and ablations moved into the existing supplement. No number, claim or limitation is
   dropped - the mapping is recorded section by section.
2. Target selection only from journals verified as SCIE in `docs/VENUE_SCI_REGISTRY.md` (verification in progress for the
   candidate list). Neural Networks is disqualified (same manuscript family already desk-rejected there as
   `NEUNET-D-26-09426`).
3. The transfer offer will be declined before 2026-11-24 unless the reframed paper turns out to fit a journal the
   transfer service actually offers and that is SCIE-verified.

## Target and title chosen (2026-10-26, operator)

**Target journal: Computer Vision and Image Understanding (CVIU, Elsevier, ISSN 1077-3142)** - SCIE per MJL on
2026-10-26 (`docs/VENUE_SCI_REGISTRY.md` section 4.4), and its guide has no hard page limit, so the 39-page reframed
main text needs no further compression. Pattern Recognition was the runner-up but requires 20-35 pages of main text.

**Title:**
> Adaptation-Site Selection for PEFT of Contrastive Dual-Encoders: A Gradient-Flow Characterisation of Cross-Modal
> Alignment and Its Measured Bounds

**Actions**: decline the Elsevier transfer offer before 2026-11-24 23:59 (author action - the link carries a personal
token); build the CVIU submission package from `paper合/reframed/`; disclose in the cover letter that the manuscript was
declined without review at Neurocomputing (`NEUCOM-D-26-23760`) and has been restructured since (main text 48 -> 39 pages,
negative results promoted to their own section).

## Target change (2026-10-26, operator: "换期刊吧")

CVIU is dropped. Reason: CVIU's article structure requires a **Vitae** (each author's biography of at most 100 words
plus a passport-type photograph as a separate figure, in an editable format), which the author has not supplied and
which is an unusual requirement for this manuscript family.

**Proposed new target: Pattern Recognition (Elsevier, ISSN 0031-3203)** - verified SCIE against MJL on 2026-10-26
(`docs/VENUE_SCI_REGISTRY.md` section 4.4). Reasons: closest methodological fit for a theory-plus-negative-results
paper, stronger visibility than Neurocomputing, no biography/photo requirement known. Known cost: its guide states a
main-text length rule of roughly 20-35 pages while the reframed main text is 39 pages, so about four pages move into
the existing Appendix I (the reframing builder supports block-level reassignment).

Status: the guide for authors is being verified item by item (length wording, review type, abstract/keywords/highlights,
vitae, file formats, declarations, data statement option). The package is rebuilt only after that verification returns
and the operator confirms the journal.

## Journal conflict matrix for the paper family (2026-10-26)

The operator pointed out that Pattern Recognition is not a valid target: **P1 was submitted to Pattern Recognition
(`PR-D-26-10149`) and rejected on 2026-10-12**, and Paper A is the merged P1 + P2 manuscript, so resubmitting it to the
same journal invites a duplicate-consideration rejection. The full matrix across the family:

| Journal | Why it is excluded for Paper A | Evidence |
|---|---|---|
| Pattern Recognition | P1 submitted there (`PR-D-26-10149`, rejected 2026-10-12); Paper A carries P1 content | `HANDOFF.md` line ~2114 |
| Pattern Recognition Letters | P3 is under review there (`PRLETTERS-D-26-02671`) and the Commentary too (`PRLETTERS-D-26-02402`) | submission records |
| Pattern Analysis and Applications | A1 is under review there (Submission ID `0a4629f0-...`) | venue registry, HANDOFF |
| Neurocomputing | Paper A desk-rejected there (this rejection); A1 also rejected earlier (`NEUCOM-D-26-20952`) | editor mail, HANDOFF |
| Neural Networks | A1 desk-rejected there (`NEUNET-D-26-09426`) | HANDOFF |
| IEEE TNNLS | P3 was rejected there before moving to PRL | HANDOFF |
| IEEE Journal of Oceanic Engineering | A23 is under review there (`26-0663`) | submission records |
| CVIU | its guide requires an author Vitae with a passport-type photograph; author decided to change journal | `docs/cviu_guide_quotes_2026-10-26.txt` |

**Still available** (all Elsevier candidates below were verified SCIE against MJL on 2026-10-26):
Information Fusion (<= 50 refs, 10-35 pp), Knowledge-Based Systems (<= 20 double-spaced pp), EAAI (<= 50 pp),
Image and Vision Computing (4500-7500 words), Applied Soft Computing (20-30 pp), Expert Systems with Applications
(no hard limit).

**New candidates proposed for verification** (no family history, plausible fit for a theory-plus-negative-results paper):
1. **Information Sciences** (Elsevier, ISSN 0020-0255) - broad AI/information science, publishes theory plus empirical
   characterisation, no known hard page limit. **First choice pending verification.**
2. **International Journal of Computer Vision** (Springer, ISSN 0920-5691) - vision-side framing; very selective but
   this manuscript's representation-analysis content is in scope.
3. **Applied Intelligence** (Springer, ISSN 0924-669X) - broad applied-AI scope, moderate selectivity.
4. **Cognitive Computation** (Springer, ISSN 1866-9956) - could host a theory-plus-analysis paper on representation
   dynamics.

Selection rule stays: SCIE verified against MJL with a recorded URL and date before the target is fixed; no journal that
has seen any member of this manuscript family.

## Target decided: Applied Intelligence (Springer, ISSN 0924-669X)

Four further candidates were verified SCIE against MJL on 2026-10-26 (Information Sciences 0020-0255, IJCV 0920-5691,
Applied Intelligence 0924-669X, Cognitive Computation 1866-9956; see `docs/VENUE_SCI_REGISTRY.md` section 4.6).

| Candidate | Verdict |
|---|---|
| Information Sciences | **excluded** - its guide carries the *same* Elsevier "Vitae" template paragraph as CVIU (biography of at most 100 words plus a passport-type photograph as a separate figure, editable format); also 40/45-page and 8/10-figure/table caps and a 200-word abstract limit |
| Cognitive Computation | **excluded** - Word-only submission, main text <= 10,000 words, structured abstract, scope mismatch |
| IJCV | **viable** but high desk-rejection risk after the Neurocomputing rejection; needs the `[iicol]` class and APA references |
| **Applied Intelligence** | **chosen** - no page limit, no Vitae/photo, no highlights requirement, abstract limit 150-250 words (we have 246), keywords 4-6 (we have 6), scope explicitly covers learning methodologies, neural networks, modelling, pattern recognition and computer vision; no family submission history; **zero compression needed** (39-page main text) |

Mechanical work to convert the reframed tree: Springer `sn-jnl` class with the `smallcondensed` option, numeric
`sn-basic` bibliography style, source tree without subdirectories, and artwork supplied as separate files.

**Lesson recorded for future venue screening**: several Elsevier journals (and the standard Elsevier guide template)
require an author Vitae with a passport-type photograph. Screening a candidate venue must therefore check the Vitae
clause early, together with page/word caps and the abstract limit, before any package work starts.

## Layout fixes on the reframed tree (2026-10-26)

Two layout defects were fixed and wired into the builders so a rebuild cannot reintroduce them:
1. **Over-wide figures**: every figure in `paper合/reframed/sections/` was 0.80-0.95 of the text width, which in the
   single-column builds pushed two figures per page and left the lower half of appendix pages empty (pages 31-34 of the
   Applied Intelligence manuscript). Widths are now normalised to 0.70-0.80 (`norm_figure_widths` in
   `tools/_pa_reframe_build.py`; the Applied Intelligence build inherits the normalised sources).
2. **Float density**: relaxed top/bottom/text/float-page fractions and raised the float counters in both preambles.
Result: the Applied Intelligence manuscript is still 58 pages with **no page having more than 25 % bottom whitespace**
(previously several appendix pages were half empty), 0 errors, 0 overfull; the elsarticle reframed build is still 83
pages. The package was regenerated (25 hashes consistent, upload names underscore-free, zip round-trip 58 pages).

## Applied Intelligence fit scan (2026-10-26)

OpenAlex (`primary_location.source.issn:0924-669X`) reports **493 works published since 2026-01-01** (56 since
2026-10-01), i.e. roughly 50-70 papers a month. The twelve most recent titles are all of the form "a <new method /
framework / network> for <application task>": urban rail traffic classification, head-and-neck cancer survival
prediction, multimodal continual federated learning for activity recognition, salient object detection in remote
sensing, IIoT event mining, video anomaly detection, scattering-pressure-field prediction, gas-pipeline risk
assessment, drug-resistance prediction, graph recommendation, agricultural detection.

Reading: Applied Intelligence is a **high-volume applied-method venue**. Its typical paper proposes a new method and
demonstrates empirical superiority on benchmarks inside an application domain. Paper A is the opposite shape: a
characterisation theorem plus an unusually complete set of negative controls, with no "our method beats the baselines"
claim (the paper's own controls say the allocation rule does not).

Consequence: keeping Applied Intelligence means accepting a real risk of a second desk rejection on the same grounds
as Neurocomputing. Fit-first alternatives worth verifying (SCIE check required before use): **Machine Learning**
(Springer, ISSN 0885-6125), **Neural Computation** (MIT Press, ISSN 0899-7667), **IJCV** (already SCIE-verified),
**Data Mining and Knowledge Discovery** (Springer, ISSN 1384-5810). All of these publish analysis and negative results
alongside methods. JMLR is excluded because it is not in the Web of Science Core Collection.

## Candidate comparison by publication profile (OpenAlex, 2026-10-26)

| Journal | Works published since 2026-01-01 | Shape of the recent titles |
|---|---|---|
| Applied Intelligence (0924-669X) | **493** (about 50-70/month) | uniformly "a <new method/framework/network> for <application task>" |
| Machine Learning (0885-6125) | **258** (about 25/month) | analysis and theory flavoured: "Weighted UnLearning ... for Improved Spurious Correlation Robustness", "Beyond Likelihood Ratio Bias: ...", "The Challenges of Hyperparameter Tuning for Accurate Causal Effect Estimation", "On Kernel Eigen-Alignments of KRR: Reconstruction and Generalization" |

Reading: Machine Learning publishes exactly the kind of paper Paper A now is - a characterisation plus a careful
account of when the claim fails - while Applied Intelligence expects a new method that wins on application benchmarks.
Machine Learning is therefore the better target on fit grounds; Neural Computation (MIT Press, 0899-7667) and Data
Mining and Knowledge Discovery (Springer, 1384-5810) remain untested alternatives.

**Blocker recorded**: the SCIE verification for the new candidates (MJL, or the Springer abstracting-and-indexing page)
could not be completed on 2026-10-26 because the Clarivate Master Journal List is a JavaScript application and the
browser CDP proxy needs a one-time "allow remote debugging" confirmation in the browser; without it only the page
title is retrievable. No candidate can be adopted before that verification is recorded, per the standing rule.

## Target switched to Machine Learning (Springer) - 2026-10-26

Reason: the Applied Intelligence profile scan (493 works since 2026-01-01, all "a new method for an application task")
shows that journal expects a method that wins on benchmarks, while Paper A is a characterisation plus negative
controls. Machine Learning publishes exactly that shape (258 works since 2026-01-01; recent titles include
"The Challenges of Hyperparameter Tuning for Accurate Causal Effect Estimation" and "On Kernel Eigen-Alignments of KRR:
Reconstruction and Generalization").

**SCIE verification (publisher abstracting-and-indexing page, 2026-10-26)**: the Clarivate Master Journal List could not
be read this round (it is a JavaScript application and the browser CDP proxy needs a one-time "allow remote debugging"
confirmation that did not appear), so the second authoritative route from the standing rule was used: the publisher's
journal page fetched with a browser user agent, which lists the indexing databases verbatim:

| Journal | ISSN | Page read | SCIE listed |
|---|---|---|---|
| **Machine Learning** | 0885-6125 | `https://link.springer.com/journal/10994` | **Science Citation Index Expanded (SCIE)** |
| Data Mining and Knowledge Discovery | 1384-5810 | `https://link.springer.com/journal/10618` | SCIE |
| International Journal of Computer Vision | 0920-5691 | `https://link.springer.com/journal/11263` | SCIE (corroborates the MJL result of 2026-10-25) |

Honest caveat: this is the publisher's index list, not the MJL card. The rule allows it as the second source; if the MJL
card is required for the record, it still needs a browser session.

**Machine Learning guide requirements read the same day**: abstract 150-250 words (manuscript has 246), keywords 4-6
(manuscript has 6), no page limit found, no Vitae/biography and no highlights requirement, LaTeX via the Springer Nature
template (already in use), Statements and Declarations section required (already present).

**Package**: `SUBMISSION/PaperA_MachineLearning/` - 58-page manuscript (27 main + 31 appendix), cover letter, title page,
flat LaTeX source with independent compile check, 18 artwork files, README and a self-consistent 25-entry hash list.
Built by `tools/_p1720_build_ml_package.py` (derived from the Applied Intelligence builder). It supersedes
`SUBMISSION/PaperA_AppliedIntelligence/` and `SUBMISSION/PaperA_CVIU/`, which stay on disk as superseded artefacts.

## Elsevier transfer declined (2026-10-26, author confirmed)

The author clicked "decline the transfer offer" for NEUCOM-D-26-23760. Paper A is therefore a fresh submission to
Machine Learning (Springer); no files will move through the Elsevier article transfer service. The deadline of
2026-11-24 is now closed out.
