# Commentary: compression proposal and "two decisions x method families" table (DRAFTS ONLY)

**Deliverable language:** English (manuscript-facing draft, as specified for this task).
**Date:** 2026-10-24.
**Status:** drafts for the author's decision. Nothing was written to `paper_review_prl/MANUSCRIPT.md`,
to `paper_review_prl/main_prl.tex` or to any other `.tex` file, and no PDF was rebuilt. Every cut and
every table cell below is a proposal with its evidence attached.

**Submission context that constrains these drafts.** The Commentary is under review at PRL as
`PRLETTERS-D-26-02402`; the submitted package is frozen (`paper_review_prl/UPLOAD/`,
`SUBMISSION/Review_PRL/`). Anything in this document is therefore revision-round material and must not
be applied to the frozen package.

**Machine verification.** `python tools/_p1500_commentary_compression_probe.py` (exit 0) proves that
each quoted `OLD` string occurs **exactly once** in `MANUSCRIPT.md`, that the markdown line numbers
recorded here match the measured line span, that no `[citation key]`, no number and no `§` cross-reference
is dropped except where an exemption is declared and justified, that every citation key used by the draft
table is already cited in `MANUSCRIPT.md` and already present in `_refs_used.json`, and it prints the
LaTeX fragment below from the manuscript's own builder (`tools/_build_prl_tex.py`, function `table_tex`).

---

## 1. The measured length budget (facts, not impressions)

Sources: `pdfinfo` / `pdftotext` on `paper_review_prl/main_prl.pdf` (built 2026-10-24 14:57, 7 pages) and
pypdf text-matrix extraction of per-column baselines.

| Fact | Value | How it was measured |
|---|---|---|
| Page count | **7** (limit 7) | `pdfinfo main_prl.pdf` |
| Page size | 595.3 x 793.7 pt | `pdfinfo` |
| Text column height | 676.9 pt (top baseline 728.5, bottom baseline 51.6) | pages 4-6, both columns full |
| Words per page (pdftotext) | p.2 820 · p.3 636 · p.4 981 · p.5 871 · p.6 858 · p.7 981 | `pdftotext -f i -l i` |
| Body prose density | **0.6743 words per column-pt** = 456 words per column = **913 words per page** | pdftotext words / used column-pt on pages 4-6 |
| Free column-pt per page | p.2 65.5 · p.3 6.4 · p.4 8.1 · p.5 34.5 · **p.6 0.0** · **p.7 438.2** | per-column baselines, running head and footer excluded |
| Only slack that can absorb additions | **438.2 column-pt on page 7** (right column, references end at y=489.4) ~ **295 words** | same; 438.2 x 0.6743 |
| Corroboration of the recorded "~6% slack" | 552.7 free of 8,122.8 column-pt on pages 2-7 = **6.8%** | sum of the free column-pt above |
| Words that would take the paper to 6 pages | ~915 column-pt ~ **617 words** | the 49 references occupy 915 column-pt and must fit on page 6 |
| Figure 1 block on page 3 | drawing y~60-245, caption y~255-300 ~ **240 pt of page height** (page origin at the top) | `pdftotext -bbox -f 3 -l 3` word boxes |

Page 6 is exactly full (0.0 free column-pt): the body currently ends flush with the bottom of page 6, and
the whole document is 7 pages only because the references (915 column-pt) end inside page 7. That is why
the "6%" slack and the "295 absorbable words" are two different numbers: 6.8% is all free space in the
document, but the buffer that prevents an eighth page is only the page-7 tail.

### Section word counts of `MANUSCRIPT.md` (prose / pipe-table words)

| Section | MD lines | prose | table |
|---|---|---|---|
| Abstract | 8-29 | 234 | 0 |
| 1. Introduction | 30-92 | 551 | 51 |
| 2.1 The first decision | 95-125 | 337 | 0 |
| 2.2 The second decision | 126-154 | 292 | 0 |
| 2.3 Why the two decisions must be separated | 155-179 | 249 | 0 |
| 3 (opening) | 180-188 | 92 | 0 |
| 3.1-3.5 (five instances) | 189-243 | 633 | 0 |
| 3.6 The freeze is an assumption | 244-269 | 193 | 44 |
| 3.7 What a practitioner can still conclude | 270-291 | 198 | 0 |
| 4. A reporting checklist | 292-357 | 580 | 82 |
| 5. Conclusions | 358-374 | 157 | 0 |
| Declarations + generative-AI statement | 375-395 | 137 | 0 |
| **all headings** | | **3,653** | **177** |

Protected material inside those counts: the **twelve checklist items** (lines 300-326) are 169 words and
**no cut touches them**; the reference list is 49 entries and **the draft table adds no reference**.

---

## 2. Compression proposal: 13 edits, **198 words** saved (core subset: 124 words)

Restatements and redundancy only; no substantive claim, no checklist item, no citation and no reported
number is dropped. Cuts are distributed as S1 11, S2.1-S2.2 30, S3 51, S4 81, S5 25 words.

| id | Section | MD lines | Words saved | Risk | What is removed |
|---|---|---|---|---|---|
| C1 | 2.1 | 97-98 | 17 | low | topic sentence whose two halves survive elsewhere |
| C2 | 2.1 | 110-111 | 7 | low | clause repeating S1's "different questions" |
| C3 | 2.2 | 148-149 | 6 | low | a forward pointer to §3.6 that does not resolve |
| C4 | 3 (opening) | 185-186 | 14 | low | duplicate of S1's "checkable against its source" |
| C5 | 3.1 | 195-200 | 16 | low | three sentences merged, all six claims kept |
| C6 | 3.5 | 240-242 | 14 | low | second sentence restating the first |
| C7 | 3.6 | 250-252 | 7 | low | compression only |
| C8 | 4 | 334-335 | 32 | medium | bold lead-in that repeats the table caption verbatim |
| C9 | 4 | 350 | 7 | low | compression only, all item numbers kept |
| C10 | 4 | 354 | 42 | medium | item-by-item re-statement of checklist items 1, 4, 5, 9 |
| C11 | 5 | 366-367 | 15 | low | tail restating the S4 opening |
| C12 | 5 | 362-364 | 10 | low | consequence clause already stated in S3 and the abstract |
| C13 | 1 | 71-72 | 11 | medium | scope caveat shortened, restated at length in 3.7 |
| | | **total** | **198** | | core subset without C8 and C10: **124 words** |

### C1 - §2.1, lines 97-98, -17 words (low risk)

OLD (verbatim):
> The sites available for adaptation are not interchangeable; the choice is constrained by architecture and task data.

NEW: *(sentence deleted; the subsection opens with "Adaptation of the language backbone is the most common choice ...")*

Why nothing is lost: "not interchangeable" survives as "They are not [alternatives]" (§2.1, lines 123-124)
and "are not two answers to the same question" (§1, lines 52-53); "constrained by architecture and task data"
survives as "The first follows architecture and data volume" (§2.3, line 164) and in the abstract.

### C2 - §2.1, lines 110-111, -7 words (low risk)

OLD:
> The two settings answer different questions and their results do not transfer: a method that improves ImageNet transfer has not thereby been shown to improve instruction following.

NEW:
> Their results do not transfer: a method that improves ImageNet transfer has not thereby been shown to improve instruction following.

Why nothing is lost: "answer different questions" repeats §1's "they are answers to different questions"
(lines 52-53). The ImageNet claim, which is the instance's substance, is kept word for word.

### C3 - §2.2, lines 148-149, -6 words (low risk; also fixes a defect)

OLD:
> This strategy is attractive because it is the only one that can in principle transfer across base models; the evidence that it does so remains thin, and we return to this in §3.6.

NEW:
> This strategy is attractive because it is the only one that can in principle transfer across base models, though the evidence that it does so remains thin.

Declared exemptions: the numeral `3.6` and the cross-reference `§3.6` disappear, because both occur only
inside the deleted pointer. The pointer does not resolve: §3.6 is "The freeze is an assumption, not a
neutral baseline", and no part of §3 returns to transfer across base models (see finding F3). If the author
prefers to keep a pointer, `... remains thin (§3.7).` saves 5 words and resolves to the section that does
discuss what survives.

### C4 - §3 opening, lines 185-186, -14 words (low risk)

OLD:
> Each is stated so that a reader can check it against the cited sources; where our reading rests on an inference rather than on data, we say so.

NEW:
> Where our reading rests on an inference rather than on data, we say so.

Why nothing is lost: checkability is already stated in §1, lines 71-72 ("chosen because each is checkable
against its source"), and again in §3.7. The disclosure commitment survives in the new sentence and in
§3.7 ("those cases are flagged where they occur").

### C5 - §3.1, lines 195-200, -16 words (low risk)

OLD:
> The two papers may be reporting the same quantity, or different quantities; the published text does not determine which. We deliberately do not claim that the values disagree, because that claim would require knowing the evaluation protocol of the second paper, which is precisely what is missing. The instance is useful for what it demonstrates: comparing these numbers across papers is not a legitimate operation, and the reason is a reporting omission rather than an error.

NEW:
> The two papers may be reporting the same quantity or different quantities; the published text does not determine which. We do not claim that the values disagree: that would require the second paper's evaluation protocol, which is precisely what is missing. Comparing these numbers across papers is therefore not a legitimate operation, for a reason of omission rather than error.

Why nothing is lost: all six claims of the original survive in order - (i) same or different quantity,
(ii) the published text does not determine which, (iii) we do not claim disagreement, (iv) because the
second paper's protocol is what is missing, (v) cross-paper comparison is not legitimate, (vi) the cause is
omission rather than error. Numbers reported earlier in the paragraph (87.3, 86.1, 84.2, 85.9, 86.4, 87.2)
are in untouched sentences.

### C6 - §3.5, lines 240-242, -14 words (low risk)

OLD:
> The remedy is trivial — state the number of runs and the convention — and its absence is a common reason why otherwise careful results cannot be re-used. A comparison whose dispersion convention is unstated cannot be combined with another.

NEW:
> The remedy is trivial — state the number of runs and the convention — and without it an otherwise careful comparison cannot be combined with another.

Why nothing is lost: the second sentence restates the first in the negative. Both the remedy (state runs
and convention) and the consequence (cannot be combined / re-used) are kept; "cannot be combined with
another" is the stronger of the two.

### C7 - §3.6, lines 250-252, -7 words (low risk)

OLD:
> This instance is a direct consequence of the siting decision of §2.1: without a stated site, the description of what was adapted is incomplete.

NEW:
> This instance follows from the siting decision of §2.1: without a stated site, the description is incomplete.

Why nothing is lost: compression only; the cross-reference and both claims are kept.

### C8 - §4, lines 334-335, -32 words (medium risk)

OLD:
> **How the items map onto the failures of §3.** The correspondence is one to one, which is the justification for each item's inclusion rather than an appeal to good practice in general.

NEW: *(paragraph deleted)*

Why nothing is lost: the bold lead-in repeats the following table caption word for word ("How the
checklist items map onto the failures of §3", line 337), and the justification is already in the first
remark, lines 329-330 ("every item corresponds to a specific inability that its absence creates, as
documented in §3"). Declared exemptions: the `3` of `§3` and the cross-reference `§3` leave the edited
span but survive verbatim in that caption and in lines 329-330.
Note for the author: the deleted sentence also asserts "the correspondence is one to one", which the table
beneath it does not literally satisfy (items 2,3 share §3.6; 5,6 share §3.3; 9,10 share §3.5). The deletion
therefore also removes a claim a reviewer could challenge (finding F6).

### C9 - §4, line 350, -7 words (low risk)

OLD:
> The list cannot be shortened much further: items 5 and 6 look like one until one notices that a paper can state its rank while leaving the division unstated, and items 9 and 10 separate a design fact from a reporting convention.

NEW:
> The list cannot be shortened much further: a paper can state its rank while leaving the division unstated (items 5 and 6), and items 9 and 10 separate a design fact from a reporting convention.

Why nothing is lost: every item number and both claims are kept; only the "look like one until one notices"
phrasing goes.

### C10 - §4, line 354, -42 words (medium risk)

OLD:
> **From aspiration to acceptance test.** Each item can be checked by a reader in a minute: item 1 requires the exact checkpoint (not just the model family); item 4 an absolute parameter count as well as a fraction; item 5 the rank array or the word ``uniform''; item 9 the number of runs and the dispersion convention. A paper that passes these tests enters a comparison table without correspondence with its authors, which is the operational meaning of the reporting standard.

NEW:
> **From aspiration to acceptance test.** Each item can be checked by a reader in a minute; a paper that passes them enters a comparison table without correspondence with its authors, which is the operational meaning of the reporting standard.

Why nothing is lost: the deleted middle clause re-states checklist items 1, 4, 5 and 9, all of which remain
intact in the twelve-item list, and "without access to code" is already in the section opening (lines
295-296: "phrased so a reader can check compliance without access to code"). The acceptance-test claim (a
paper that passes enters a comparison table without correspondence) is kept in full.
Declared exemption: the numerals `1`, `4`, `5`, `9` are **checklist-item pointers, not reported
quantities**; their targets are untouched. No measured number appears in this paragraph.
If the author prefers to keep the concrete examples, keep the item numbers and drop only the explanatory
clauses (saves ~20 words instead of 42).

### C11 - §5, lines 366-367, -15 words (low risk)

OLD:
> The instances are not allegations of error: in each case the information needed for comparison is absent rather than wrong, and the checklist in §4 is the minimum that removes these obstacles.

NEW:
> The instances are not allegations of error: the information needed for comparison is absent rather than wrong.

Why nothing is lost: the non-accusatory claim and the "absent rather than wrong" formulation are kept; the
deleted tail restates the §4 opening (lines 294-296, "the remedy is a reporting standard. The twelve items
below are the minimum needed ..."). Declared exemptions: the `4` of `§4` and the `§4` cross-reference leave
this sentence but survive in §1, lines 66-67.

### C12 - §5, lines 362-364, -10 words (low risk)

OLD:
> The two are governed by different variables — architecture and data volume for the first, the target metric for the second — and they are routinely conflated, which is why many published numbers cannot share a table.

NEW:
> The two are governed by different variables — architecture and data volume for the first, the target metric for the second — and they are routinely conflated.

Why nothing is lost: the consequence clause repeats §3's opening ("a substantial part of its numerical
content cannot be compared", lines 182-183) and the abstract ("it is why much of the published evidence
cannot be compared"). The conflation claim and the two governing variables are kept.

### C13 - §1, lines 71-72, -11 words (medium risk)

OLD:
> And it is argumentative rather than systematic: the instances in §3 are individual cases chosen because each is checkable against its source, not a sample from which frequencies can be estimated.

NEW:
> It is argumentative rather than systematic: the instances in §3 are cases checkable against their sources, not a sample (§3.7).

Why nothing is lost: the scope limitation ("argumentative rather than systematic", "not a sample") is kept,
the checkability that C4 relies on is kept here, and §3.7 states the same limit at greater length
("the instances are checkable illustrations rather than a systematic sample"). The only weakened element is
the explicit "frequencies can be estimated" clause, which "not a sample" carries implicitly; if the author
wants it explicit, keep the longer form at zero saving, or write "not a sample from which frequencies can
be estimated (§3.7)" for a saving of 4 words.

### Considered and rejected (do not cut)

- §3.2 "The magnitude of this effect is larger than is commonly assumed." - an assertoric claim; the
  section's numbers support it, so it is substance, not restatement.
- §3.3 "Two problems arise." and §2.3's "The separation matters for three reasons." - structural signposts
  whose removal would make the paragraph order harder to follow.
- §2.3's "and no amount of careful reading will attribute the difference" - rhetoric, but it carries the
  unattributability claim that §2.3 exists to establish.
- The abstract (234 of the 250 allowed words) - outside the requested sections, and near its own ceiling.
- The twelve checklist items - protected by the task and by the build gate.

### Expected page effect (approximate, not compiled)

Arithmetic basis: 1 page = 1,353.8 column-pt; 1 word = 1.48 column-pt (from the measured 0.6743
words/column-pt).

| Scenario | Page-7 tail (column-pt) | Absorbable body words before an 8th page | Pages |
|---|---|---|---|
| today (measured) | 438 | ~295 | 7 |
| 13 cuts only (198 words = 294 column-pt) | ~732 | ~490 | 7 |
| 13 cuts + new table, keeping Figure 1 | ~410-470 | ~275-315 | 7 |
| **13 cuts + new table replacing Figure 1 (recommended)** | **~870-930** | **~585-625** | **7** |
| core cuts (124 words) + new table replacing Figure 1 | ~760-840 | ~510-570 | 7 |

Table cost estimate: the draft table is 7 rows (header + 6) and 4 columns; as a full-width `table*` it
should set in ~11-14 footnote-size lines plus a 2-line caption, i.e. ~130-160 pt of page height
(~260-320 column-pt, ~0.19-0.24 page). Figure 1 costs ~240 pt of page height (~480 column-pt, ~0.35 page),
measured above.

**No scenario in this band reduces the PDF below 7 pages**, and none is close: reaching 6 pages requires
~617 words (~915 column-pt) removed. The point of the cuts is margin, not a shorter paper: they convert the
present "exactly full page 6 next to a 438 column-pt tail" into roughly a third of a page (cuts alone) or
about two-thirds of a page (recommended package) of headroom for reviewer-requested additions.

Two caveats, both real: (i) float placement moves content in whole steps, so an insertion or deletion near
a float boundary can shift a table or a page's worth of text at once; (ii) the table cost is an estimate
from row and line counts - it cannot be confirmed without recompiling, which this task deliberately did
not do.

---

## 3. Draft table: adaptation families on the two decisions

### 3.1 Design constraints found in the manuscript's builder

`tools/_build_prl_tex.py` converts a markdown pipe table into a `tabularx` float with the rule
`full = ncol >= 4` (line 210), and column 1 is always the *unwrapped* `l` column while the remaining
columns are `X` (line 213). Two consequences for this table:

1. **The first column must stay short** (family labels only). Citation keys must go into a wrappable `X`
   column, otherwise the `l` column would be ~150-240 pt wide and crush the rest of the table.
2. **Four columns are required** to obtain the full-width `table*` that this table needs; with three
   columns the builder emits a single-column `table`, in which a family cell such as
   "AdaptFormer [chen2022adaptformer]; Convpass [jie2022convpass]; CLIP-Adapter [gao2024clipadapter]" would
   wrap over seven lines in a 244 pt column.

Hence the shape below: 7 rows, 4 columns, keys collected in a final "Cited as" column.

### 3.2 Markdown draft (paste-ready for `MANUSCRIPT.md`)

> **Table 2.** Adaptation families on the two decisions. Placements follow the sources cited in the last
> column and the statements of §2.1 and §2.2; where a family defines no rule for dividing a parameter
> budget, the third column says so rather than assigning a strategy.

| Family | Where capacity goes | How the budget is divided | Cited as |
|---|---|---|---|
| LoRA / DoRA | Language backbone; vision encoder frozen | Uniform rank across the targeted projections | [hu2021lora; liu2024dora] |
| AdaLoRA / ARD-LoRA | Language backbone, the low-rank family's usual site | Estimated importance: rank raised where updates are large | [zhang2023adalora; shinwari2026ardlora] |
| VPT / SSF | Visual encoder: prompt vectors; feature scaling and shifting | Uniform: the same configuration in every module | [jia2022vpt; lian2022ssf] |
| Encoder-side bottlenecks | Encoder feed-forward path; feature side of either branch | Not determinable from the cited sources: no allocation rule | [chen2022adaptformer; jie2022convpass; gao2024clipadapter] |
| Projector redesign | Projector | Not a parameter division: the knob is the visual-token count | [cha2024honeybee; li2025tokenpacker] |
| Search-based | Selected by the search, so it spans sites | Search over the configuration | [zhou2024autopeft; liu2022ia3] |

Rows: 6 data rows + header = 7 (within the 8-row limit). Keys: 13, every one already cited in
`MANUSCRIPT.md` and present in `_refs_used.json` (verified), so the table adds **no new reference and no
new reference lines** to the 7-page budget.

### 3.3 LaTeX-ready fragment

Emitted by the manuscript's own builder, so it is exactly what `tools/_build_prl_tex.py` would produce if
the markdown above were pasted into `MANUSCRIPT.md` (it uses the `booktabs` and `tabularx` packages that
`main_prl.tex` already loads):

```latex
\begin{table*}[t]
\centering
\footnotesize
\caption{Adaptation families on the two decisions. Placements follow the sources cited in the last column and the statements of §2.1 and §2.2; where a family defines no rule for dividing a parameter budget, the third column says so rather than assigning a strategy.}
\begin{tabularx}{\textwidth}{@{}l >{\raggedright\arraybackslash}X >{\raggedright\arraybackslash}X >{\raggedright\arraybackslash}X @{}}
\toprule
Family & Where capacity goes & How the budget is divided & Cited as \\
\midrule
LoRA / DoRA & Language backbone; vision encoder frozen & Uniform rank across the targeted projections & \cite{hu2021lora,liu2024dora} \\
AdaLoRA / ARD-LoRA & Language backbone, the low-rank family's usual site & Estimated importance: rank raised where updates are large & \cite{zhang2023adalora,shinwari2026ardlora} \\
VPT / SSF & Visual encoder: prompt vectors; feature scaling and shifting & Uniform: the same configuration in every module & \cite{jia2022vpt,lian2022ssf} \\
Encoder-side bottlenecks & Encoder feed-forward path; feature side of either branch & Not determinable from the cited sources: no allocation rule & \cite{chen2022adaptformer,jie2022convpass,gao2024clipadapter} \\
Projector redesign & Projector & Not a parameter division: the knob is the visual-token count & \cite{cha2024honeybee,li2025tokenpacker} \\
Search-based & Selected by the search, so it spans sites & Search over the configuration & \cite{zhou2024autopeft,liu2022ia3} \\
\bottomrule
\end{tabularx}
\end{table*}
```

If the author prefers the citation keys directly beside the family names (the more conventional layout),
the first column can be widened by hand, e.g.
`{@{}>{\raggedright\arraybackslash}p{0.26\textwidth} >{\raggedright\arraybackslash}X >{\raggedright\arraybackslash}X@{}}`
with the family cell "AdaLoRA / ARD-LoRA [zhang2023adalora; shinwari2026ardlora]" and the "Cited as" column
dropped; that variant does not come out of the builder unchanged and would have to be maintained by hand.

### 3.4 Provenance for every table cell

The rule applied: **no cell asserts anything that is not already asserted by the Commentary's own prose or
by its Figure 1, or by the cited source's own title/abstract.** Section and line numbers are
`MANUSCRIPT.md` positions. "Fig. 1" positions are read from the generator that produced the figure in the current working build,
`tools/_make_prl_figure.py` lines 35-47 (x: 0 encoder, 1 projector, 2 backbone, 3 full
stack; y: 0 uniform, 1 estimated importance, 2 structural quantity, 3 search).

| Table row | "Where" cell: evidence | "How" cell: evidence | Placement status |
|---|---|---|---|
| LoRA / DoRA | "LoRA [hu2021lora] and its weight-decomposed variant [liu2024dora] inject trainable low-rank matrices into the backbone's projections, leaving the vision encoder frozen" (§2.1, lines 101-104); Fig. 1 at x=2 | "Uniform allocation ... is the default in most applications of the low-rank family" (§2.2, lines 131-133); Fig. 1 label "LoRA / DoRA (uniform rank)" | site explicit; division is the family default, not a per-paper statement |
| AdaLoRA / ARD-LoRA | no per-method site statement; inherited from "the low-rank family is most often applied [to the language backbone]" (§2.1, lines 100-101) and Fig. 1 at x=2 | "from adaptive criteria that raise rank where updates are large [zhang2023adalora]" (§2.2, lines 137-138); Fig. 1 label "AdaLoRA / ARD-LoRA (adaptive rank)" | site inherited; division explicit. See finding F5: §2.2 also lists `shinwari2026ardlora` under "initialise from principal or minor singular components" (lines 140-141), i.e. a second sub-family |
| VPT / SSF | "Visual prompt tuning [jia2022vpt], feature scaling and shifting [lian2022ssf] ... all modify how images are represented" (§2.1, lines 107-109); Fig. 1 at x=0 | Fig. 1 label "VPT / SSF (uniform)" plus §2.2's definition of uniform, "assigns the same configuration ... to every module" (lines 131-132) | site explicit; division supported by the figure only |
| Encoder-side bottlenecks | "bottleneck modules in the encoder's feed-forward path [chen2022adaptformer; jie2022convpass]" (§2.1, lines 107-109); for CLIP-Adapter: the cited source's own abstract - "feature adapters on either visual or language branch", "an additional bottleneck layer ... residual-style feature blending" (arXiv:2110.04544, published as IJCV 2024) | **not determinable**: neither §2.1/§2.2 nor the source states a rule for dividing a parameter budget among modules | where explicit for AdaptFormer/Convpass; CLIP-Adapter's site is not fixed by its own method. Finding F4 applies |
| Projector redesign | "the point of work that trains only the projector and finds this sufficient [iskandar2026projector], and of work that redesigns the projector for locality or token efficiency [cha2024honeybee; li2025tokenpacker]" (§2.1, lines 116-119); Fig. 1 at x=1 | **not a parameter division**: what the family varies is the visual-token count, which the Commentary already treats as a different organising axis in Table 1 ("[shao2025tokencompression] ... the token budget axis", line 83) | division axis does not apply as defined; Fig. 1 plots it at y=0 (uniform) |
| Search-based | **not stated by the Commentary**: §2.2 says only that the search treats "the configuration" as a hyperparameter (lines 151-152), and §4 item 7 asks for "the search space and the selection criterion" (lines 311-312) without naming a site. Corroboration outside the Commentary: the source's title ("AutoPEFT: Automatic Configuration Search") and the internal survey's description of the search space as "architecture, trainable parameter count, insertion position" (`弃用/06_归档稿件/paper_review/sections/taxonomy.md`, lines 313-314) - an internal evidence file, not part of the submitted Commentary | "Search-based allocation treats the configuration as a hyperparameter to be optimised [zhou2024autopeft; liu2022ia3]" (§2.2, lines 151-152); Fig. 1 at y=3 | division explicit; site not stated by the Commentary |

### 3.5 Families that could not be placed (stated explicitly, not guessed)

1. **Encoder-side bottlenecks (CLIP-Adapter, Convpass, AdaptFormer) - Decision 2 cannot be placed.**
   §2.1 describes them by mechanism ("bottleneck modules in the encoder's feed-forward path"), and the
   CLIP-Adapter source describes a single bottleneck layer with residual-style feature blending on either
   branch. Neither defines a rule for dividing a fixed parameter budget among modules, so the row says
   "not determinable" instead of assigning uniform or importance-driven. **This matters:** Figure 1 of the
   current working build plots "Convolutional bypass" and "CLIP-Adapter" at y=1, i.e. *estimated importance*
   (`tools/_make_prl_figure.py`, lines 38-39), which neither the body text nor the cited source supports -
   see finding F4.
2. **Projector redesign (Honeybee, TokenPacker) - Decision 2 does not apply as defined.** The family's
   design knob is the visual-token count, not the division of a trainable-parameter budget; the Commentary
   itself lists the token budget as a different review's organising axis (Table 1, line 83). Assigning it a
   position on the division axis would invent one. (Figure 1 plots it at y=0.)
3. **Search-based (AutoPEFT, IA3) - Decision 1 is not stated by the Commentary.** The prose places it on
   the division axis only; the search-based row's "where" cell is therefore phrased as "selected by the
   search, so it spans sites", which rests on the source's title and on the internal survey, not on the
   Commentary's text. If the author wants the table to rest only on the Commentary, this cell must be
   reduced to "not stated".
4. **AdaLoRA / ARD-LoRA - Decision 1 is inherited, not stated per method**, and the two keys are put in two
   different sub-families inside the same §2.2 paragraph (importance-driven vs spectral initialisation).
   The row follows Figure 1's grouping ("adaptive rank") but the author should decide which sub-family
   ARD-LoRA belongs to.
5. **VPT / SSF - Decision 2 rests on Figure 1 alone** (its "(uniform)" label) plus §2.2's definition of
   uniform; §2.1 states only the site and the mechanism. This is defensible but should be stated in the
   caption if the figure is retired.

### 3.6 Placement recommendation

**Recommended:** insert the table at the end of §2.2's opening, i.e. in `MANUSCRIPT.md` after line 129
("Given a site, a second and separable decision remains: how to distribute a fixed number of trainable
parameters within it. Four strategies recur.") and before line 131, **and retire Figure 1**.

Why:

1. **The table and Figure 1 carry the same content.** The figure's own caption calls it "a qualitative
   sketch, not measured coordinates" (`tools/_build_prl_tex.py`, FIGURE constant); the table states the
   same placements with a source named per row. In a paper whose thesis is that placements must be
   evidenced, the table is the stronger object and the sketch is the weaker one.
2. **Two of the figure's placements are unsupported** (finding F4). Withdrawing the figure removes the
   exposure; keeping it means either sourcing those two points or redrawing them.
3. **Space.** Figure 1 costs ~480 column-pt (~0.35 page); the table costs ~260-320 column-pt
   (~0.19-0.24 page), measured/estimated in §2. Combined with the 13 cuts, the paper's prevention buffer
   against an eighth page grows from ~295 to ~585-625 absorbable words.

What the package changes, in order (none of it done here):

1. `MANUSCRIPT.md`: paste the caption and the pipe table after line 129; apply the cuts of §2; replace the
   two sentences at lines 173-176 that reference Figure 1 with one sentence carrying the same claim in
   words, e.g. *"The table makes the independence visible: one site admits four divisions, and one division
   appears at more than one site."* (+22 words, ~33 column-pt, already allowed for in the scenario table).
2. `MANUSCRIPT.md` captions: with the new table as Table 2, the six-instance table caption at line 254
   keeps its current label "**Table 3.**" - which then matches the compiled numbering for the first time -
   and the checklist-mapping caption at line 337 (labelled "**Table 2.**" today) becomes "**Table 4.**".
   No prose cross-reference breaks: the only numbered table reference in prose is to Table 1 (line 74).
3. `tools/_build_prl_tex.py`: delete the `FIGURE` constant (lines 364-375) and the line
   `body = body.replace("Figure 1", BS + "ref{fig:decision}")` (line 516), which is also the source of
   finding F1.
4. Re-run `python tools/_build_prl_tex.py` and confirm its own gate: 7 pages, 0 errors, 0 undefined
   references, 0 overfull hboxes, checklist 1..12, keywords, and no `??` in the PDF text.
5. Leave the frozen submission untouched: `SUBMISSION/Review_PRL/figures/fig1_decision_space.pdf` and its
   pinned hash in `tools/paper_audit/freeze/prl_commentary.json` (sha256 700818cc...) describe the
   *submitted* package and remain valid; only the working copy loses the figure. (The frozen figure is
   already not the working figure: the working `figures/fig1_decision_space.pdf` hashes to 7CCB1FF0...,
   because it was regenerated during the 2026-10-18 font fix. The freeze file documents what was
   submitted, not what is on disk now.)
6. Provenance manifest: this is a literature-placement table reporting no result of ours, so per
   `docs/PROVENANCE_MANIFEST_2026-10-20.md` it needs one entry marked `exempt` with the reason
   ("literature placement table, no measured values; sources cited in the last column"); the gate
   `python tools/_p1428_provenance_gate.py` is otherwise unaffected.

**Alternative (space-neutral, if a figure must be kept):** keep Figure 1 and insert the table in the same
position. The table then costs about what the cuts save (~260-320 column-pt against 294), the PDF stays at
7 pages with roughly today's margin, and the paper carries two presentations of one set of placements -
which reviewers may read as redundancy, and which leaves finding F4 unresolved.

**Not recommended:** inserting the table without either the cuts or the figure removal. That consumes
~60-70% of the 438 column-pt tail and leaves ~100-175 column-pt, i.e. room for about two or three more
sentences before the references spill onto an eighth page.

---

## 4. Findings beyond compression (each with its evidence; none of them fixed here)

**F1 - Figure 1 is referred to as a bare number in the compiled PDF.** `tools/_build_prl_tex.py` line 516
replaces the string "Figure 1" with `\ref{fig:decision}`, which prints only "1". Page 4 of the current
working build (`main_prl.pdf`, 2026-10-24 14:57) reads "... becomes expressible only once placement is separated from parameterisation. **1** sketches the two
decisions as a plane ...". The builder's own checks cannot see this: the reference resolves, so there is no
"undefined reference" warning. Suggested fix: emit `Figure~\ref{fig:decision}` (or `Fig.~\ref{...}`).
Evidence: `pdftotext -f 4 -l 4 paper_review_prl/main_prl.pdf`.

**F2 - The manual table labels in `MANUSCRIPT.md` do not match the compiled numbering.** The six-instance
table is labelled "**Table 3.**" at line 254 but is Table 2 in the PDF (page 5); the checklist-mapping table
is labelled "**Table 2.**" at line 337 but is Table 3 in the PDF (page 6). The builder drops the manual
numbers (`TABLE_CAPTION_RE`, line 141) and numbers floats in order, so the PDF is self-consistent and no
cross-reference is wrong - but the markdown is misleading, and inserting the new table makes it worse unless
the labels are brought to 2/3/4. Evidence: `pdftotext` pages 5-6.

**F3 - §2.2's forward pointer to §3.6 does not resolve.** "the evidence that it does so remains thin, and we
return to this in §3.6" (lines 148-149); §3.6 is "The freeze is an assumption, not a neutral baseline" and no
section returns to transfer of structural allocations across base models. Cut C3 removes it; if a pointer is
wanted, §3.7 is the section that discusses what survives.

**F4 - Figure 1 places two families under "estimated importance" without support.** The generator puts
"Convolutional bypass" at (0.80, 1.0) and "CLIP-Adapter" at (1.45, 1.0)
(`tools/_make_prl_figure.py`, lines 38-39), i.e. at y = estimated importance. §2.1 describes both as
feature-side/feed-forward bottleneck or bypass modules; the CLIP-Adapter source describes a single bottleneck
layer with residual blending; and the internal survey's grid puts feature-side bottleneck adaptation under
the *uniform* (default) row (`弃用/06_归档稿件/paper_review/sections/taxonomy.md`, line 361). Either the figure is redrawn or
the sources are named for those two points.

**F5 - CLIP-Adapter is cited for spectral initialisation.** §2.2 lists `[gao2024clipadapter]` among methods
"that initialise from principal or minor singular components" (lines 138-140). The cited source's own
description is a bottleneck feature adapter with residual-style blending on either branch, with no singular
value initialisation (arXiv:2110.04544 abstract; IJCV 2024). Candidate citation misplacement - worth
checking against the full text before the revision.

**F6 - "The correspondence is one to one" is not literally satisfied by the table beneath it.** In §4, items
2,3 share §3.6; items 5,6 share §3.3; items 9,10 share §3.5. Cut C8 deletes the sentence, which resolves the
tension; if C8 is not taken, the sentence should be reworded (e.g. "the correspondence is item-by-item").

**F7 - "our survey found none for multimodal models" (§5, lines 369-371) sits oddly with the paper's
self-description as "argumentative rather than systematic" with instances that are "not a sample" (§1,
lines 71-72). Suggested rewording, which is claim-preserving: "we found none among the works reviewed here".

**F8 - An observation for the author's own judgement, not a defect:** the paper's most citable object, the
twelve-item checklist, is 169 words of the manuscript's 3,653 prose words (3,830 including table text),
while the prose around those items is 411 words (§4 totals 580 words including the items themselves). C8 and
C10 (74 of the 198 saved words) are the part of this proposal that acts on that ratio.

---

## 5. Verification

```
python tools/_p1500_commentary_compression_probe.py
```

Expected output (abridged; exit code 0):

```
Section word counts: paper_review_prl\MANUSCRIPT.md      (table in section 1 above)
PDF layout probe: 7 pages, 595.3 x 793.7 pt
  column geometry (from pages 4-6, both columns full):
    top baseline 728.5 pt, bottom baseline 51.6 pt, column height 676.9 pt
  body density from pages 4, 5, 6: 0.6743 words per column-pt (456 words per full column, 913 per page)
  last page (7) free column-pt: 438.2  -> absorbable body text before an 8th page: 295 words
Table key coverage: 13 keys (...)
  all cited in MANUSCRIPT.md: yes
  all in _refs_used.json:     yes
Cut-list validation (13 proposed edits)
  ... all rows "ok" ...
  total words saved: 198  (target band 120-200)
  core subset (C1, C2, C3, C4, C5, C6, C7, C9, C11, C12, C13): 124 words
  status: all edits verified against MANUSCRIPT.md
```

The script is read-only: it opens `MANUSCRIPT.md`, `main_prl.pdf` and `_refs_used.json`, imports
`tools/_build_prl_tex.py` only to call its `table_tex()` renderer, and writes nothing.

---

## 6. What was deliberately not done

- `paper_review_prl/MANUSCRIPT.md`, `paper_review_prl/main_prl.tex` and every other `.tex` file are
  unmodified (mtime 2026-10-24 14:57 before and after this work).
- No PDF was rebuilt, so every page effect in §2 is an estimate from measured word and column geometry,
  marked approximate, and not a compiled result.
- The frozen submission (`paper_review_prl/UPLOAD/`, `SUBMISSION/Review_PRL/`) was not touched.
- No new reference was added: the 13 keys of the draft table were already cited in the manuscript.