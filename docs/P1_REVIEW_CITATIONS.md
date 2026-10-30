# P1 — Citation-integrity review of `paper/` (independent, read-only)

**Manuscript under review**: *Protect, Don't Perturb: Cross-Modal Alignment under PEFT of Vision-Language
Models*, Hongrui Wan (University of Southampton), Pattern Recognition, **PR-D-26-10149**, submitted 2026-08-23.

**Scope of this review**: citation integrity only — mechanical integrity of the `\cite` keys, correctness of
every bibliographic entry against an external record, correctness of the *use* of the load-bearing entries,
missing prior work, and exposure of the paper's explicit novelty claims. Nothing else in the manuscript was
audited (numbers, figures, tables and prose are out of scope here and are covered by other reviews).

**Read-only guarantee**: **no file under `paper/`, `outputs/` or any other manuscript directory was
modified.** No LaTeX build was run (the existing `main_nn.pdf` / `main_nn.log` / `main_nn.bbl` were read, not
regenerated). The only file written is this report.

**Date of review**: 2026-09 (workspace state as of the last commit; `paper/references.bib` self-dates its last
verification as 2026-08-14, `paper/references.bib:4`).

---

## 0. Method, evidence rule, and the limits of this review

**Evidence rule applied throughout.** A citation is a *claim about an external artefact*. No verdict below
rests on the `.bib` file, on `docs/*.md`, or on the workspace's own prior audit. Every entry that carries an
argument was resolved against an external record: the ICML/ICLR/CVF/ACL/IJCAI/ISCA proceedings pages, the
publisher DOI landing page, IEEE Xplore, or the arXiv listing reached through `web_search`. Where only a
search-engine snippet was available, that is stated.

**Environment limits (state once, applies to every "unverifiable" verdict).**

1. `web_fetch` is blocked on this machine: the VPN resolves public hosts to non-public addresses and the fetch
   is refused. **All external evidence below therefore comes from `web_search` result titles/URLs**, which are
   server-side and were reachable. This is one step less direct than opening the record; it is sufficient to
   distinguish *wrong title*, *wrong venue* and *wrong identifier*, which is what this audit is about, but it
   is **not** sufficient to read an abstract's full text.
2. Consequently **one class of verdict could not be settled here**: whether a source actually makes the
   specific claim P1 attaches to it, when the title alone does not decide the question. Those items are marked
   *claim-verification required* rather than passed or failed (findings **F5**, **F12**, and the
   `yi2025decipher` row of §3).
3. `docs/CITATION_INTEGRITY_AUDIT.md` (2026-09-15) audited `paper_a1/` and `paper_a2/` under the same
   constraints. It is **not** used as evidence here; where its conclusions coincide with mine they were
   re-derived independently.

**Verdict vocabulary** (used in the §3 table): **VERIFIED** — exists, and title/first author/venue/year are as
printed. **MISMATCH** — exists but a printed field is wrong. **SUPERSEDED** — real, but the printed version is
not the current/published one. **UNVERIFIABLE** — could not be resolved from this machine. **SUSPECT** —
internally or externally contradicted in a way that makes the entry unusable as printed.

---

## 1. Mechanical integrity — the answer is clean, and it is worth saying so plainly

| Check | Command / source | Result |
|---|---|---|
| Distinct `\cite` keys in the P1 sources | regex over all `paper/**/*.tex` (`\cite`, `\citep`, `\citet`, `\citealp`, `\citeauthor`, `\citeyear`, `\nocite`, starred forms, with optional args) | **44** |
| `@entry` count in `paper/references.bib` | regex over the file | **44** |
| Duplicate bib keys | group-by over the 44 keys | **0** |
| **Undefined keys** (cited but not defined → would print `[?]`) | set difference | **0** |
| **Orphan keys** (defined but never cited) | set difference | **0** |
| `\bibitem` count in the resolved bibliography | regex over `paper/main_nn.bbl` | **44** |
| BibTeX's own count | `paper/main_nn.blg:30` — "You've used 44 entries" | **44** |
| Undefined citation warnings in the build log | `paper/main_nn.log` scanned for `Warning`/`undefined`/`multiply` | **none** (only 4 `Overfull \hbox` and 9 `hyperref` "Token not allowed in a PDF string", all cosmetic) |
| Bibliography order | `paper/main_nn.bbl` `\bibitem` sequence read in full | first-citation order (`elsarticle-num` is an unsorted numeric style) — **no shifted numbering**, every number matches the order in which the key first appears in the text |
| PDF currency | `paper/main_nn.log` tail — `Output written on main_nn.pdf (37 pages, 2611229 bytes)`; `main_nn.bbl` fields match `paper/references.bib` field-for-field | **in sync** — every printed field in the `.bbl` is the field in the `.bib`, so the PDF does not carry stale metadata |

**Conclusion of §1:** there is **no broken citation in P1's PDF**. No `[?]`, no orphan, no duplicate key, no
stale `.bbl`. The defects reported below are all *bibliographic-accuracy* and *usage* defects — the class a
reader or desk editor finds by resolving a DOI, not by compiling.

**One hygiene observation that matters more than it looks.** The bibliography's key naming has drifted far from
its own convention. Nine keys are named after someone who is **not** an author of the entry:
`li2025randlora` (Albert et al.), `wang2025lorattt` (Kojima et al.), `zhao2025dopl` (Guo et al.),
`meszaros2025selective` (Akbarian Bafghi et al.), `zhu2026fi` (Dai et al.), `schiappa2025robust` (Malik et
al.), `amblard2025fill` (Role et al.), `gu2025gtma` (Zhang et al.), `gao2026uniformity` (Yin et al.). With
`elsarticle-num` numeric citations the keys never reach the PDF, so this is **cosmetic** — but it is the visible
fingerprint of a machine-assembled bibliography, and it co-occurs with every one of the hard defects in §2. It
is the reason the entries in §2 were checked by hand rather than sampled.

---

## 2. Findings, ordered by severity

Bracketed tags are this report's finding ids, referenced by the verdict in §7.

### 2.1 Must fix before submission

---

**[F1] — Two arXiv identifiers are transposed: the printed DOI for the sparse-autoencoder paper resolves to the vision-reasoning paper, and vice versa.**

*Evidence chain*
- `paper/references.bib:421–427` (`morelli2026sparse`): title *"Sparse autoencoders enable robust and
  interpretable fine-tuning of {CLIP} models"*, `journal = {arXiv preprint arXiv:2604.16256}`,
  `doi = {10.48550/arXiv.2604.16256}`.
- `paper/references.bib:413–419` (`xu2026vlreasoning`): title *"Do vision-language models truly perform vision
  reasoning? A rigorous study of the modality gap in reasoning"*, `journal = {arXiv preprint
  arXiv:2605.15961}`, `doi = {10.48550/arXiv.2605.15961}`.
- Both are printed in the resolved bibliography: `paper/main_nn.bbl:237–242` (xu → `arXiv.2605.15961`,
  lines 241–242) and `paper/main_nn.bbl:244–249` (Morelli → `arXiv.2604.16256`, lines 248–249).
- External evidence — **`2605.15961` is the sparse-autoencoder paper**:
  `ar5iv.labs.arxiv.org/html/2605.15961` renders *"Sparse Autoencoders enable Robust and Interpretable
  Fine-tuning of CLIP models"* with the corresponding address `fabian.morelli@student.uni-tuebingen.de`
  (returned in two independent searches), and `huggingface.co/papers/2605.15961` is the paper page for the same
  title.
- External evidence — **`2604.16256` is the vision-reasoning paper**:
  `ar5iv.labs.arxiv.org/html/2604.16256` renders *"Do Vision-Language Models Truly Perform Vision Reasoning? A
  Rigorous Study of the Modality Gap"* (also returned twice, and the Semantic Scholar record for that title is
  first-authored `Xu-Wang`, matching the entry's `Xu, Y. and Wang, Y. …`).

*Why it matters*: a referee who resolves either DOI is taken to a paper with a different title and different
authors. Both are load-bearing in `related_work.tex:20`: `morelli2026sparse` is one of the five pillars of the
"vision encoder is the component requiring protection" paragraph, and `xu2026vlreasoning` is the source of the
quantitative "vision-only accuracy dropping from 92.8% to 12.4%" figure.

*Correction*

```bibtex
@article{morelli2026sparse,
  author  = {Morelli, F. and Uselis, A. and Sonthalia, A. and Oh, S. J.},
  title   = {Sparse autoencoders enable robust and interpretable fine-tuning of {CLIP} models},
  journal = {arXiv preprint arXiv:2605.15961},      % was 2604.16256
  year    = {2026},
  doi     = {10.48550/arXiv.2605.15961},            % was 10.48550/arXiv.2604.16256
}

@article{xu2026vlreasoning,
  author  = {Xu, Y. and Wang, Y. and Wu, Z. and Song, K. and Lin, J. and Shen, Z.},
  title   = {Do vision-language models truly perform vision reasoning? {A} rigorous study of the modality gap in reasoning},
  journal = {arXiv preprint arXiv:2604.16256},      % was 2605.15961
  year    = {2026},
  doi     = {10.48550/arXiv.2604.16256},            % was 10.48550/arXiv.2605.15961
}
```

---

**[F2] — `gao2026uniformity` carries an arXiv id that belongs to a different paper; the workspace's own second copy of the same entry names a different (and externally corroborated) id.**

*Evidence chain*
- `paper/references.bib:363–370`: title *"Towards Uniformity and Alignment for Multimodal Representation
  Learning"*, `booktitle = {International Conference on Machine Learning (ICML)}, year = {2026}`,
  `doi = {10.48550/arXiv.2501.00984}`; printed at `paper/main_nn.bbl:255–256` as
  `doi:10.48550/arXiv.2501.00984`.
- External: `ar5iv.labs.arxiv.org/html/2602.09507` renders exactly that title;
  `fugumt.com/fugumt/paper_check/2602.09507v1_enmode` is a paper-check record for the same title at the same id;
  and `icml.cc/virtual/2026/poster/62197` is the ICML 2026 poster page for the title (venue therefore **VERIFIED**
  — only the identifier is wrong).
- Internal corroboration that this is a mistake rather than a versioning artefact: the **same workspace** holds
  the same entry with a different identifier — `paper_ap3/refs.bib:96–103` gives
  `note = {Preprint: arXiv:2602.09507}` for the identical title/author list/venue. Two files in one repository
  cannot both be right, and the external records side with `paper_ap3`.
- `arXiv:2501.00984` could not be matched to this title by any query run here.

*Why it matters*: the printed DOI resolves to something other than the cited work; and this is the paper P1
cites at `related_work.tex:24` for "a unified theoretical treatment of uniformity and alignment objectives".

*Correction*: change `doi` to `10.48550/arXiv.2602.09507` (or drop the arXiv DOI entirely and print the ICML
2026 record, which is the version being cited).

---

**[F3] — `niss2025reviving` is wrong in its year and is not supported in its author list; the claim attached to it does not fit the work it names.**

*Evidence chain*
- `paper/references.bib:334–341`:
  ```bibtex
  @article{niss2025reviving,
    title   = {Reviving In-Domain Fine-Tuning Methods for Source-Free Cross-Domain Few-Shot Learning},
    author  = {Niss, Laura and Vogt-Lowell, Kevin and Tsiligkaridis, Theodoros},
    journal = {arXiv preprint arXiv:2605.11659},
    year    = {2025},
    doi     = {10.48550/arXiv.2605.11659},
  }
  ```
  Printed at `paper/main_nn.bbl:169–174` as "… arXiv preprint arXiv:2605.11659 **(2025)**".
- **Year**: the arXiv identifier scheme encodes `YYMM`; `2605` is **May 2026**, not 2025. Externally corroborated:
  `github.com/advanced-cs/arXiv_daily/blob/main/daily_papers/20260513_Wed/daily_papers/…` lists the paper in the
  **2026-05-13** daily batch, and `ar5iv.labs.arxiv.org/html/2605.11659` serves the v1 HTML. The printed year is
  off by one and the key (`niss2025reviving`) repeats the error.
- **Authors**: neither external record for this exact title supports the printed list. The Semantic Scholar
  record slug is `…-Source-Free-Cross-domain-Few-shot-Zhao-Liu/6940d6eb…` (implying **Zhao, Liu** as the first two
  authors) and the `ar5iv` rendering of v1 is preceded by "**Guo et al**". Neither names Niss, Vogt-Lowell or
  Tsiligkaridis. *This part is unresolved, not settled* — the two external signals disagree with each other as
  well as with P1 — but the entry as printed is not supported by any record found.
- **Claim fit**: `related_work.tex:14` uses it for "found LoRA outperforms prompt methods **by rectifying
  collapsed attention**". A source-free cross-domain few-shot-learning paper is an implausible home for a
  LoRA-vs-prompt attention-collapse result; that sentence needs its own source.

*Why it matters*: this is the entry a referee is most likely to check, because the claim it carries
("LoRA outperforms prompt methods") is one of the positions P1 stakes out in §2.2.

*Action*: replace the entry with the real record — resolve the title on arXiv, take the author list and year
from the record itself, and re-attach the "rectifying collapsed attention" claim to whichever paper actually
makes it (or delete the clause).

---

**[F4] — `zhu2025connector` cites an arXiv preprint for a paper that is published at IJCAI 2025.**

*Evidence chain*
- `paper/references.bib:395–403`: *"Connector-{S}: A Survey of Connectors in Multi-modal Large Language
  Models"*, `journal = {arXiv preprint arXiv:2502.11453}, year = {2025}`, printed at
  `paper/main_nn.bbl:272–277` with `doi:10.48550/arXiv.2502.11453`.
- External: the paper is **IJCAI 2025** — `ijcai.org/proceedings/2025/1202` and
  `dl.acm.org/doi/10.24963/ijcai.2025/1202` ("Proceedings of the Thirty-Fourth International Joint Conference
  on Artificial Intelligence"). The venue is not in doubt.

*Why it matters*: P1's own venue, Pattern Recognition, expects the published record; and A1/A2 in this
workspace were already faulted for exactly this defect class (`docs/CITATION_INTEGRITY_AUDIT.md` §§2.2/3, items
`luo2023empirical` and `zhai2023forgetting`).

*Correction*

```bibtex
@inproceedings{zhu2025connector,
  author    = {Zhu, Xun and Zhang, Zheng and Chen, Xi and Shi, Yiming and Li, Miao and Wu, Ji},
  title     = {Connector-{S}: A Survey of Connectors in Multi-modal Large Language Models},
  booktitle = {Proceedings of the Thirty-Fourth International Joint Conference on Artificial Intelligence (IJCAI)},
  year      = {2025},
  doi       = {10.24963/ijcai.2025/1202},
}
```

---

**[F5] — The named precedent: P1 cites the superseded arXiv version of the modality-gap work whose ICML 2026 version is retitled, and attributes a "first proof" to it that the printed title does not carry.**

*Evidence chain*
- `paper/references.bib:146–153` (`yi2025decipher`): *"Decipher the Modality Gap in Multimodal Contrastive
  Learning: From Convergent Representations to Pairwise Alignment"*, `journal = {arXiv preprint
  arXiv:2510.03268}, year = {2025}`. Printed at `paper/main_nn.bbl:31–36`.
- External: the preprint is real and exactly as titled — `ui.adsabs.harvard.edu/abs/2025arXiv251003268Y/abstract`
  and the Semantic Scholar record `…Decipher-the-Modality-Gap-in-Multimodal-Contrastive-Yi-Douady…` both carry
  the printed title with **Yi, Douady, Chen**. So the *title and authors are right*.
- External: the **ICML 2026 version exists and is retitled** —
  `icml.cc/virtual/2026/poster/66630` is *"The Convergent Representation of Contrastive Vision-Language Models:
  Geometry, Modality Gap and Shared Space Alignment"* (same three authors). P1 therefore cites a preprint that
  has been superseded by a peer-reviewed version with a different title.
- The claim attached is stronger than the printed title supports. P1 states, three times, that this work
  *proved* a specific mechanism: `related_work.tex:6` — "provided the **first proof** that dimension collapse is
  the fundamental origin of the modality gap"; `visual_fragility.tex:8` — "**proved** that dimension collapse
  causes the modality gap"; `discussion.tex:8` — "showed that dimension collapse is the root cause, and that
  under subspace constraints, perfect alignment is impossible"; `introduction.tex:31` — "**proved** that
  dimension collapse is the root cause". Nothing in the two titles (preprint or ICML) is about dimension
  collapse as the origin; both titles are about convergent representations / geometry / shared-space alignment.
  **Whether the paper's body establishes the "dimension collapse is the root cause" theorem could not be
  confirmed from this machine** (§0 limit 2) — the abstract text was not retrievable. This is flagged as
  *claim-verification required*, not as a proven mis-citation.

*Why it matters*: this is precisely the defect class the review brief names, and it is the same work that was
mis-cited in `paper_a1`/`paper_a2`. It is load-bearing: the "dimensional collapse asymmetry" argument at
`visual_fragility.tex:8` is one of the three sources of asymmetry that the Visual Fragility Interpretation
rests on, and `discussion.tex:8` uses it to argue the gap "should be *preserved*" — the paper's thesis.

*Correction*

```bibtex
@inproceedings{yi2026convergent,
  author    = {Yi, Lingjie and Douady, Raphael and Chen, Chao},
  title     = {The Convergent Representation of Contrastive Vision-Language Models: Geometry, Modality Gap and Shared Space Alignment},
  booktitle = {International Conference on Machine Learning (ICML)},
  year      = {2026},
  note      = {arXiv:2510.03268 (preprint title: ``Decipher the Modality Gap in Multimodal Contrastive Learning: From Convergent Representations to Pairwise Alignment'')},
}
```
— then re-check each of the four in-text claims against the **ICML 2026** text, and in particular confirm
before printing that the paper contains a proof of "dimension collapse is the fundamental origin of the
modality gap". If it does not, `related_work.tex:6`, `visual_fragility.tex:8`, `discussion.tex:8` and
`introduction.tex:31` must be rewritten as P1's own reading rather than as the source's theorem.

---

**[F6] — `gu2025gtma` cites an arXiv-only preprint for a paper that has an IEEE Xplore published version under a different title.**

*Evidence chain*
- `paper/references.bib:343–350`: *"{GTMA}: Dynamic Representation Optimization for Out-of-Distribution
  Vision-Language Models"*, `journal = {arXiv preprint arXiv:2512.18504}, year = {2025}`; printed at
  `paper/main_nn.bbl:195–200`.
- External: an IEEE Xplore record exists for the work — `ieeexplore.ieee.org/abstract/document/11463397`,
  titled **"GTMA: Dynamic Representation Optimization for OOD VLMs"** (short title, i.e. a different version
  string from the preprint's). Semantic Scholar holds a matching paper record
  (`…GTMA-Dynamic-Representation-Optimization-for-OOD-…`).

*Why it matters*: P1's `related_work.tex:18` offers this as one of the "gap-aware fine-tuning" works it
positions against; citing the preprint when the published version exists is the defect the brief calls out, and
it is the same class as F4.

*Action*: resolve the IEEE record, take its exact title, venue, year and DOI, and cite that; keep the arXiv
note only as a secondary identifier. (The author order printed in P1 — Zhang, Liu, Wang — could not be
confirmed against the published version from this machine: two Semantic Scholar slugs returned for the title
disagree on whether the first author is Zhang or Liu. Confirm off-box.)

---

**[F7] — A published prior work that pre-empts a central claim is missing: gap *preservation* during CLIP adaptation, including asymmetric gap change during training, was published at ICCV 2025.**

*Evidence chain*
- P1's novelty claim: `paper/main_nn.tex:41` (abstract) — "we conduct the **first** systematic study of modality
  gap evolution during fine-tuning"; `introduction.tex:8` — "we provide the **first** systematic study of how
  these metrics evolve *dynamically* during fine-tuning"; `conclusion.tex:4` — "We conducted the **first**
  systematic study of modality gap evolution during parameter-efficient fine-tuning".
- P1's *thesis* is gap preservation: `discussion.tex:8` — "the gap is not a defect to be fixed, but a
  fundamental property of the embedding geometry that should be *preserved*"; `conclusion.tex:14` — "protect
  the visual encoder's parameters".
- The missing work: **Huang et al., "Mind the Gap: Preserving and Compensating for the Modality Gap in
  CLIP-Based Continual Learning", ICCV 2025** — evidence: the CVF open-access record
  `openaccess.thecvf.com/content/ICCV2025/html/Huang_Mind_the_Gap_Preserving_and_Compensating_for_the_Modality_Gap_ICCV_2025_paper.html`;
  the ICCV 2025 poster page `iccv.thecvf.com/virtual/2025/poster/664` with slides at
  `iccv.thecvf.com/media/iccv-2025/Slides/664.pdf`; and IEEE Xplore document `11444362`. The paper's own
  material additionally carries a section on **"训练过程中模态间隔变化的不对称现象"** — *the asymmetric
  phenomenon of modality-gap change during training* (`mmcheng.net/wp-content/uploads/2025/09/25ICCV_MG.pdf`,
  surfaced by search) — i.e. it studies gap evolution during adaptation **and** an inter-modal asymmetry in
  that evolution, which is the empirical core of P1's contribution 1 and of the Visual Fragility asymmetry
  argument.

*Why it matters*: this is a should-cite-turned-must-cite. It is (a) a direct competitor on gap preservation as
an objective during CLIP adaptation, (b) evidence against the unqualified word **"first"** in three places
including the abstract, and (c) a mandatory citation for a Pattern Recognition referee who works on CLIP
continual learning. Note P1 already cites the *same authors' group* neighbouring literature
(`zhou2025proof` at `related_work.tex:14` is the "Learning without Forgetting" line of work), so the omission
is not a scope argument.

*Action*: (i) add the reference; (ii) scope the novelty claim to what remains true — the **PEFT configuration
space** (LoRA rank / position / α / target modules, Adapter, 116 experiments) and the **CG/DG decomposition
applied as a training-time monitor** — rather than "modality gap evolution during fine-tuning" as such. A
defensible replacement for `main_nn.tex:41` is: "we conduct the first systematic study of modality gap evolution
**across the PEFT configuration space**". Unguarded "first" will be read as claiming the ICCV 2025 paper does
not exist.

```bibtex
@inproceedings{huang2025mindgap,
  author    = {Huang, Linglan and Cao, Xusheng and Liu, Xialei and Cheng, Ming-Ming},
  title     = {Mind the Gap: Preserving and Compensating for the Modality Gap in {CLIP}-Based Continual Learning},
  booktitle = {IEEE/CVF International Conference on Computer Vision (ICCV)},
  year      = {2025},
}
```
*(The four-author list is inferred from the CVF filename `Huang_Mind_the_Gap…`, the Nankai/`mmcheng.net` host of
the slide PDF, and the co-author names surfaced alongside it; **confirm the exact author list and page range
from the CVF record before pasting it in**.)*

---

### 2.2 Should fix (a reviewer is likely to raise these)

---

**[F8] — `zhu2026fi` is a paper about **large language models**, cited as independent evidence about the **vision encoder**; and the entry omits the venue at which the work was actually first presented.**

*Evidence chain*
- `paper/references.bib:273–280` (`zhu2026fi`): *"Breach in the Shield: Unveiling the Vulnerabilities of Large
  Language Models"*, `author = {Dai, Runpeng and Yang, Run and Zhou, Fan and Zhu, Hongtu}`,
  `booktitle = {Conference of the European Chapter of the ACL (EACL)}, year = {2026}`,
  `doi = {10.18653/v1/2026.eacl-long.161}`.
- Venue/author **VERIFIED**: `aclanthology.org/2026.eacl-long.161/` exists, and Semantic Scholar's record for
  the title is first-authored `Dai-Yang`, matching the entry. (Note the printed entry's `\bibitem` label is
  `zhu2026fi`, after the **last** author — cosmetic, see §1.)
- Use in P1: `related_work.tex:20` — "~\cite{zhu2026fi} identified that a small subset of parameters
  disproportionately contributes to **model brittleness**", inside a paragraph whose thesis is "the visual
  modality is the bottleneck"; and `visual_fragility.tex:12` — "a small subset of high-sensitivity parameters
  contributing disproportionately to brittleness" as a pillar of **parameter distribution asymmetry** in the
  **vision encoder**, then again as one of only four "independent evidence from multiple sources" at
  `visual_fragility.tex:37`.
- The title says *Large Language Models*; the printed DOI resolves to an EACL 2026 paper on LLM vulnerability.
  Nothing in the record establishes a result about vision encoders. P1 itself concedes the transfer at
  `discussion.tex:34` ("the parameter-distribution asymmetry evidence comes from continual-learning settings,
  and while SEA provides single-task evidence, a direct measurement … would strengthen the interpretation") —
  a concession absent from the two places where the citation actually carries the argument.
- Secondary: the same work also appears on the NeurIPS 2025 virtual site
  (`neurips.cc/virtual/2025/loc/mexico-city/133258`), i.e. a workshop presentation predates the EACL version.
  The printed entry names neither.

*Action*: at `related_work.tex:20` and `visual_fragility.tex:12`, either (i) state the transfer explicitly
("in LLMs; the analogous measurement for vision encoders is P1's contribution"), or (ii) replace with a
vision-encoder-specific parameter-sensitivity source. Additionally the entry should name the NeurIPS 2025
workshop appearance, and its key should be renamed from `zhu2026fi` to `dai2026breach`.

---

**[F9] — Seventeen entries name a peer-reviewed venue but print an arXiv DataCite DOI, so the DOI in the PDF resolves to a preprint rather than to the publication being cited.**

*Evidence chain*: computed over `paper/references.bib`; the entries whose `booktitle`/`journal` names a
conference or workshop while `doi = {10.48550/arXiv.…}` are:

`radford2021clip`, `li2022blip`, `hu2021lora`, `liang2022mind`, `cai2026geometric`, `schrodi2025two`,
`levi2025double`, `fahim2024contrastive`, `mistretta2025cross`, `yamaguchi2025cliprefine`, `albert2025kradapter`,
`li2025randlora`, `wang2025lorattt`, `niss2025iimm`, `jiang2026flow`, `sun2026narrow`, `gao2026uniformity`.

All 17 are printed as `doi:10.48550/arXiv.…` in `paper/main_nn.bbl` (e.g. `main_nn.bbl:13–14`, `:20–21`,
`:56–57`, `:96–97`, `:103–104`, `:118–119`, `:124–125`, `:132–133`, `:139–140`, `:185–186`, `:206–207`,
`:255–256`). By contrast the eleven entries with publisher DOIs (`zhang2026halora` AAAI `10.1609/…`,
`zhao2025dopl` ACL `10.18653/…`, `yang2026upm`/`wang2026ftp`/`yang2026missing` Elsevier `10.1016/j.patcog.…`,
`guo2026spectral` ACM `10.1145/…`, `cheng2026maab`/`chen2025vlmft` Elsevier, `zhu2026fi` ACL, `zhou2025proof`
IEEE `10.1109/…`, `vlm2026survey` Elsevier) are the correct pattern — so the fix is a consistency fix, not a
rewrite.

*Why it matters*: not a false statement (the arXiv DOI does resolve, and the venue is separately verified for
the entries checked in §3), but every one of these printed DOIs sends an editor to the wrong artefact, and the
pattern is what makes a bibliography read as unverified. `niss2025iimm` is the sharpest case: the ICCV 2025
version is verified published (`iccv.thecvf.com/virtual/2025/poster/647`,
`openaccess.thecvf.com/content/ICCV2025/html/Niss_The_Inter-Intra_Modal_Measure…`,
IEEE Xplore `11445077`), yet the entry prints the arXiv DOI `10.48550/arXiv.2407.15731`.

*Action*: for each of the 17, print the publisher DOI (or drop the DOI and keep the venue + pages). A
`\bibitem` with no DOI is better than one whose DOI points at a preprint of the cited paper.

---

**[F10] — Missing citation: the canonical modality-gap-*reduction* paper is absent from a related-work section that reviews gap-reduction methods.**

*Evidence chain*: `related_work.tex:8` names three gap methods (`mistretta2025cross`, `yamaguchi2025cliprefine`,
`guo2026spectral`) and `related_work.tex:18` a fourth (`amblard2025fill`), then `methodology.tex:6` builds the
CG/DG decomposition around them. The omitted work is **Sofer, A., Goldman, Y., Chazan, S. E., "Pull It
Together: Reducing the Modality Gap in Contrastive Learning", Interspeech 2025** — verified at
`isca-archive.org/interspeech_2025/sofer25_interspeech.pdf` and in Semantic Scholar
(`…Pull-It-Together-Reducing-the-Modality-Gap-in-Sofer-Goldman…`), pages 196–200, DOI
`10.21437/interspeech.2025-1664`. It is the paper whose title *is* the problem P1 defines, and it is already
cited as `sofer2025` in the companion manuscripts of this workspace, which makes the omission look like an
oversight rather than a judgement.

*Action*: add it to `related_work.tex:8`, with one clause on what it does (post-hoc alignment of the two
modalities) versus what P1 does (PEFT-time gap evolution).

---

**[F11] — Missing citation: the closest published statement of P1's "the text side is the safe side to adapt" thesis.**

*Evidence chain*: **"The Dominance of Text Space: Unveiling the Asymmetric Nature of Cross-Modal Alignment in
Large Language Models"**, ACL 2026 — `aclanthology.org/2026.acl-long.1699/`. P1's conclusion
(`conclusion.tex:14`) generalises exactly this asymmetry — "protect the visual encoder's parameters, fine-tune
the text modality" — and its Visual Fragility argument rests on text/visual asymmetry
(`visual_fragility.tex:6–12`), yet the only asymmetry sources cited are `schrodi2025two` (information
imbalance) and `yi2025decipher`. The ACL 2026 paper is the nearest independent statement of the same
asymmetry, in a *different* modality stack (LLMs), which both strengthens P1's generality claim and needs
distinguishing from it.

*Action*: cite at `related_work.tex:20` or in the Discussion, framed as corroborating asymmetry with a
different mechanism.

---

**[F12] — The "zero-overhead alignment monitoring" contribution is presented without a prior-art scope, although a published predictor exists and P1 already cites it for something else.**

*Evidence chain*: `methodology.tex:22–30` introduces DG-based alignment monitoring and DG-ES, and
`conclusion.tex:12` states "the Distribution Gap can serve as a **zero-overhead** training-time signal for
alignment health"; `paper/main_nn.tex:56` and `highlights.tex:12` repeat "zero-overhead". The nearest published
prior art is `niss2025iimm` — *"The Inter-Intra Modal Measure: A Predictive Lens on Fine-Tuning Outcomes in
Vision-Language Models"* — which P1 cites at `related_work.tex:18` **only** for "predicts fine-tuning outcomes
from a single forward pass" and never returns to when claiming the monitoring signal. Two further candidates
surfaced but could not be confirmed from this machine: "Modality Gap-Driven Subspace Alignment Training
Paradigm for Multimodal Large Language Models" (`arxiv.org/pdf/2602.07026v2`) and "DeepAlign: Mitigating
Modality Conflict through Modality-Specific Alignment" (CVPR 2026).

*Action*: not a defect of fact — I found **no** published zero-overhead gap-based early-stopping method, and
the honest reading of the searches below is that this sub-claim is not pre-empted. But the claim should be
scoped explicitly, e.g. "to our knowledge no published monitor uses a distribution-level gap statistic without
a validation split; the closest prior predictor operates post hoc on a single forward pass
\citep{niss2025iimm}". Note also that P1's own `discussion.tex:38` already establishes DG-ES is not
production-ready, so the abstract/highlights' flat "zero-overhead" is the paper's most exposed operational
claim — see §5, N4.

---

**[F13] — The bibliography's own provenance header makes a verification claim that the entries do not support.**

*Evidence chain*: `paper/references.bib:1–5` asserts "44 entries, all cited in-text" and "**Last verified:
2026-08-14**". The first half is **true** (verified in §1: 44/44 cited, 0 orphans). The second half is not
sustainable: at least F1–F6 are identifier/year/venue errors that a verification pass against the record would
have caught, and `paper_ap3/refs.bib:102` names a *different* arXiv id for the entry in F2. This is the same
class of defect that `docs/CITATION_INTEGRITY_AUDIT.md` §6.3 recorded for `paper_a1/related_work_bibitems.tex`
— a provenance comment that a referee reading the source will check.

*Action*: delete "Last verified: 2026-08-14", or re-date it after the F1–F6 corrections are actually made.
Do not leave a dated verification claim standing over an unverified file in a source-available submission.

---

### 2.3 Notes (hygiene; no reviewer is likely to open these, but they should not ship)

**[N1] — Key naming has drifted off its own convention in nine places** (`li2025randlora`, `wang2025lorattt`,
`zhao2025dopl`, `meszaros2025selective`, `zhu2026fi`, `schiappa2025robust`, `amblard2025fill`, `gu2025gtma`,
`gao2026uniformity` are all named after non-first-authors). Invisible in the PDF under `elsarticle-num`; rename
for maintainability, and because it is the tell that correlates with §2.1.

**[N2] — `zhao2026gapinit` is the only entry with no DOI and `zhang2026imod`/`dayal2026duaa` have neither DOI
nor pages.** `paper/references.bib:429–435` prints `note = {arXiv:2602.01522}` for the ICML 2026 Gap-Init paper
(verified: `icml.cc/virtual/2026/poster/63669`, `huggingface.co/papers/2602.01522`); `zhang2026imod` (CVPR 2026,
verified at `openaccess.thecvf.com/content/CVPR2026/html/Zhang_Parameter-Efficient_Adaptation_for_MLLMs…`) and
`dayal2026duaa` (WACV 2026, verified at `wacv.thecvf.com/virtual/2026/poster/622`) print neither. Add CVF page
numbers, since CVF assigns them and P1 cites both as evidence.

**[N3] — Entries that could not be independently resolved from this machine** (see §0 limit 1):
`cheng2026maab` (Information Fusion, `doi:10.1016/j.inffus.2025.102834` — no external hit returned; the DOI
shape and the journal are plausible but unconfirmed), `chen2025vlmft` (Information Fusion,
`doi:10.1016/j.inffus.2025.103623` — same), `vlm2026survey` (the paper is confirmed — ScienceDirect
`S2590005626000627`, i.e. *Array*, matching `10.1016/j.array.2026.100739` and the printed title exactly — but
the **single-author attribution "Rahman, Arifur"** was not confirmed; note the same title is discussed in
Korean press coverage of a *Sejong University* group, which is a reason to check the author list rather than
assume), and the author lists of `yu2026aniso` (title/id verified via `huggingface.co/papers/2605.07825`;
authors unverified) and `gu2025gtma` (see F6). None of these is asserted to be wrong; all five are asserted to
be *unchecked here*.

**[N4] — Cross-manuscript propagation: the same defective entries are carried by other manuscripts in this
workspace, so fixing P1 alone will not close the issue.** Read-only inspection of the sibling bibliographies:
`paper_ap3/refs.bib:232–238` and `paper合/references.bib` repeat the F1 transposition (`morelli2026sparse` →
`2604.16256`); `paper_ap3/refs.bib:357–363` and `paper合/references.bib` repeat `xu2026vlreasoning` →
`2605.15961`; `paper合/references.bib` and `paper2/references.bib:40–45` carry the F5 preprint form of
`yi2025decipher`. Two further defects exist **only** in the siblings and are reported here because the brief
asked for shared-entry defects: (i) `paper_ap3/refs.bib:385–390` gives the ICML 2026 modality-gap paper with
the **wrong author initials** — `author={Yi, X. and Douady, S. and Chen, F.}` where the record is
**L.** Yi, **R.** Douady, **C.** Chen; (ii) `paper3/paper_ieee/references.bib:22–23`,
`paper3/paper/references.bib:22–23` and `paper3/paper_ICLR_backup/references.bib:22–23` give the ICML 2026
paper with the **wrong title** — "The Convergent Representation of **Vision-Language Contrastive Learning**"
where the ICML 2026 record reads "The Convergent Representation of **Contrastive Vision-Language Models**"
(`icml.cc/virtual/2026/poster/66630`). Fix all three bibliographies from one corrected source.

---

## 3. Every reference checked, with verdict

44 entries; all 44 were checked for mechanical integrity (§1). The verdict column records what was resolved
**externally**. "Verified" fields are listed first/author/venue/year where they were checked.

| # | key | first author / year / venue as printed | external record used | verdict |
|---|---|---|---|---|
| 1 | `radford2021clip` | Radford, 2021, ICML | `proceedings.mlr.press` V139 (well-known; DOI pattern only) | VERIFIED (venue/year); DOI is arXiv (F9) |
| 2 | `li2022blip` | Li, 2022, ICML | BLIP, ICML 2022 / PMLR 162 | VERIFIED (venue/year); DOI is arXiv (F9) |
| 3 | `hu2021lora` | Hu, 2022, ICLR | LoRA, ICLR 2022 | VERIFIED; DOI is arXiv (F9); key says 2021 (N1) |
| 4 | `zhang2026halora` | Zhang, 2026, AAAI | `ojs.aaai.org/…/40056`, `dl.acm.org/doi/10.1609/aaai.v40i33.40056` | VERIFIED |
| 5 | `zhang2026imod` | Zhang, 2026, CVPR | `openaccess.thecvf.com/content/CVPR2026/html/Zhang_Parameter-Efficient_Adaptation_for_MLLMs…` | VERIFIED (no DOI/pages — N2) |
| 6 | `albert2025kradapter` | Albert, 2025, ICCV | `iccv.thecvf.com/virtual/2025/poster/2100`, CVF ICCV2025 PDF | VERIFIED; DOI is arXiv (F9) |
| 7 | `li2025randlora` | Albert, 2025, ICLR | `proceedings.iclr.cc` 2025 hash `382b95a6…` | VERIFIED; key named after non-author (N1) |
| 8 | `wang2025lorattt` | Kojima, 2025, ICML | `icml.cc/virtual/2025/48084` | VERIFIED; key named after non-author (N1) |
| 9 | `zhao2025dopl` | Guo, 2025, ACL | `aclanthology.org/2025.acl-long.1514/` | VERIFIED; key named after non-author (N1) |
| 10 | `meszaros2025selective` | Akbarian Bafghi, 2025, arXiv:2501.15377 | Semantic Scholar `…Selective-Low-Bafghi-Bagwell…` | VERIFIED; key named after non-author (N1) |
| 11 | `yang2026upm` | Yang, 2026, Pattern Recognition 172:112484 | `sciencedirect.com/…/S0031320325011471`, `github.com/EdenGabriel/UPM` | VERIFIED |
| 12 | `wang2026ftp` | Wang, 2026, Pattern Recognition 179:113794 | `dl.acm.org/doi/10.1016/j.patcog.2026.113794`, ScienceDirect `S0031320326007594` | VERIFIED |
| 13 | `yang2026missing` | Yang, 2026, Pattern Recognition 177:113320 | `dl.acm.org/doi/abs/10.1016/j.patcog.2026.113320`, ScienceDirect `S0031320326002852` | VERIFIED |
| 14 | `liang2022mind` | Liang, 2022, NeurIPS | `proceedings.neurips…` 2022 hash `702f4db7…` (also ACM `10.5555/3600270.3601550`) | VERIFIED; DOI is arXiv (F9) |
| 15 | `yi2025decipher` | Yi, 2025, arXiv:2510.03268 | ADS `2025arXiv251003268Y`, Semantic Scholar `…Yi-Douady…`; ICML 2026 retitled at `icml.cc/virtual/2026/poster/66630` | **SUPERSEDED (F5)**; in-text "dimension collapse" claims: *claim-verification required* |
| 16 | `cai2026geometric` | Cai, 2026, ICML | `icml.cc/virtual/2026/poster/63447`; authors Y. Cai, Z. Zhang, Y. Liu, J. Q. Shi | VERIFIED; DOI is arXiv (F9) |
| 17 | `schrodi2025two` | Schrodi, 2025, ICLR | `proceedings.iclr.cc` 2025 hash `4572bc2f…` (title as printed matches the ICLR record) | VERIFIED; DOI is arXiv (F9) |
| 18 | `levi2025double` | Levi (M. Y. Levi), 2025, ICML | `cris.technion.ac.il` record, ACM `10.5555/3780338.3781669` (42nd ICML) | VERIFIED; DOI is arXiv (F9) |
| 19 | `fahim2024contrastive` | Fahim, 2024, NeurIPS | `arxiv.org/pdf/2405.18570`, `huggingface.co/papers/2405.18570` | VERIFIED; DOI is arXiv (F9) |
| 20 | `amblard2025fill` | Role, 2025, arXiv:2505.03703 | `ar5iv.labs.arxiv.org/html/2505.03703`, `export.arxiv.org/pdf/2505.03703v1` | VERIFIED; key named after non-author (N1) |
| 21 | `liu2026tpc` | Liu, 2026, arXiv:2604.00279 | `ar5iv.labs.arxiv.org/html/2604.00279`, Semantic Scholar `…Liu-Yang…` | VERIFIED (CG/DG terminology source; `R²=0.986` claim not re-read here) |
| 22 | `yu2026aniso` | Yu, 2026, arXiv:2605.07825 | `huggingface.co/papers/2605.07825` | title+id VERIFIED; author list unchecked (N3) |
| 23 | `mistretta2025cross` | Mistretta, 2025, ICLR | `proceedings.iclr.cc` 2025 hash `c15da559…` | VERIFIED; DOI is arXiv (F9) |
| 24 | `yamaguchi2025cliprefine` | Yamaguchi, 2025, CVPR | `openaccess.thecvf.com/content/CVPR2025/html/Yamaguchi_Post-pre-training…` | VERIFIED; DOI is arXiv (F9) |
| 25 | `guo2026spectral` | Guo, 2026, WWW | `dl.acm.org/doi/10.1145/3774904.3792528` (ACM Web Conference 2026) | VERIFIED |
| 26 | `cheng2026maab` | Cheng, 2026, Information Fusion | **no external hit returned** | UNVERIFIABLE here (N3) |
| 27 | `wang2025sea` | Wang, 2025, arXiv:2508.01741 | `ar5iv.labs.arxiv.org/html/2508.01741` (title exact) | VERIFIED |
| 28 | `zhu2026fi` | Dai, 2026, EACL | `aclanthology.org/2026.eacl-long.161/`; also `neurips.cc/virtual/2025/loc/mexico-city/133258` | VERIFIED bibliographically — **usage wrong (F8)** |
| 29 | `schiappa2025robust` | Malik, 2025, arXiv:2502.01576 | Semantic Scholar `…Robust-LLaVA…-Malik-Shamshad…` | VERIFIED; key named after non-author (N1) |
| 30 | `niss2025iimm` | Niss, 2025, ICCV | `iccv.thecvf.com/virtual/2025/poster/647`, CVF ICCV2025, IEEE Xplore `11445077` | VERIFIED; published DOI replaced by arXiv DOI (F9) |
| 31 | `jiang2026flow` | Jiang, 2026, ICLR | `iclr.cc/virtual/2026/poster/10007742`, HKUST research portal | VERIFIED; DOI is arXiv (F9) |
| 32 | `zhou2025proof` | Zhou, 2025, TPAMI 47(6):4489–4504 | `dl.acm.org/doi/10.1109/TPAMI.2025.3540889`, `ar5iv…/2305.19270` | VERIFIED |
| 33 | `dayal2026duaa` | Dayal, 2026, WACV | `wacv.thecvf.com/virtual/2026/poster/622`, `computer.org/csdl/…/2ggOK7HfwaY` | VERIFIED (no DOI/pages — N2) |
| 34 | `niss2025reviving` | Niss, **2025**, arXiv:2605.11659 | arXiv id is **May 2026** (arXiv_daily 2026-05-13 batch); author list contradicted by both records found | **MISMATCH / SUSPECT (F3)** |
| 35 | `gu2025gtma` | Zhang, 2025, arXiv:2512.18504 | IEEE Xplore `11463397` ("…for OOD VLMs"); SS slugs disagree on author order | **SUPERSEDED (F6)**; authors unchecked (N3) |
| 36 | `sun2026narrow` | Sun, 2026, ICLR Workshop | `ar5iv.labs.arxiv.org/html/2507.03662` (title exact) | VERIFIED as arXiv; workshop venue not independently confirmed; DOI is arXiv (F9) |
| 37 | `gao2026uniformity` | Yin, 2026, ICML | `icml.cc/virtual/2026/poster/62197`; id at `ar5iv…/2602.09507`; sibling `paper_ap3/refs.bib:102` says 2602.09507 | **MISMATCH on identifier (F2)**; venue VERIFIED; key named after non-author (N1) |
| 38 | `vlm2026survey` | Rahman, 2026, Array 30:100739 | ScienceDirect `S2590005626000627` (title exact, *Array* 2026) | VERIFIED (title/journal/year); sole-author claim **unchecked** (N3) |
| 39 | `chen2025vlmft` | Chen, 2025, Information Fusion | **no external hit returned** | UNVERIFIABLE here (N3) |
| 40 | `zhu2025connector` | Zhu, 2025, arXiv:2502.11453 | `ijcai.org/proceedings/2025/1202`, `dl.acm.org/doi/10.24963/ijcai.2025/1202` | **SUPERSEDED (F4)** |
| 41 | `zhou2026shortcut` | Zhou, 2026, arXiv:2604.17217 | `ar5iv.labs.arxiv.org/html/2604.17217` (title exact) | VERIFIED |
| 42 | `xu2026vlreasoning` | Xu, 2026, arXiv:2605.15961 | `2605.15961` = the **sparse-autoencoder** paper; vision-reasoning title is at `2604.16256` | **MISMATCH — id transposed (F1)** |
| 43 | `morelli2026sparse` | Morelli, 2026, arXiv:2604.16256 | `2604.16256` = the **vision-reasoning** paper; SAE title is at `2605.15961` (`ar5iv`, `huggingface.co/papers/2605.15961`) | **MISMATCH — id transposed (F1)** |
| 44 | `zhao2026gapinit` | Zhao, 2026, ICML | `icml.cc/virtual/2026/poster/63669`, `huggingface.co/papers/2602.01522` | VERIFIED (no DOI — N2) |

*(44 data rows, one per `\bibitem` in `paper/main_nn.bbl`.)*

**Tally** (44 entries, one verdict each): **VERIFIED 35** (of which 17 additionally carry the arXiv-DOI defect
F9, and 3 have unchecked sub-fields, N3) · **MISMATCH 4** — `xu2026vlreasoning` and `morelli2026sparse` (the
transposed identifier pair, F1), `gao2026uniformity` (F2), `niss2025reviving` (F3) · **SUPERSEDED 3** —
`yi2025decipher` (F5), `gu2025gtma` (F6), `zhu2025connector` (F4) · **UNVERIFIABLE from this machine 2** —
`cheng2026maab`, `chen2025vlmft` (N3) · **SUSPECT 0** in the strong sense: **no entry is fabricated** — every
identifier that was resolved resolved to a real publication. The defects are wrong-field defects.

---

## 4. Missing prior work

Searches run for this section: modality-gap evolution during fine-tuning; gap-aware / gap-preserving
fine-tuning; PEFT effects on cross-modal alignment; gap monitoring during training; "first systematic study"
formulations. **Where the searches found nothing, that is recorded as such** — a null result is the honest
input to a novelty claim.

| # | reference | why it matters | grade |
|---|---|---|---|
| M1 | Huang et al., *Mind the Gap: Preserving and Compensating for the Modality Gap in CLIP-Based Continual Learning*, **ICCV 2025** (CVF OA; `iccv.thecvf.com/virtual/2025/poster/664`; slides `iccv.thecvf.com/media/iccv-2025/Slides/664.pdf`; IEEE `11444362`) | Preserves the gap *during* CLIP adaptation and analyses **asymmetric gap change during training**. Pre-empts (a) the gap-preservation objective and (b) the asymmetry observation that the Visual Fragility Interpretation rests on. Directly contradicts the unqualified "first systematic study of modality gap evolution during fine-tuning". | **must cite** (F7) |
| M2 | Sofer, Goldman, Chazan, *Pull It Together: Reducing the Modality Gap in Contrastive Learning*, **Interspeech 2025**, pp. 196–200, DOI `10.21437/interspeech.2025-1664` (`isca-archive.org/interspeech_2025/sofer25_interspeech.pdf`) | The canonical named modality-gap-reduction method; absent from a related-work section that surveys gap-reduction methods and from the CG/DG positioning in `methodology.tex:6`. | **should cite** (F10) |
| M3 | *The Dominance of Text Space: Unveiling the Asymmetric Nature of Cross-Modal Alignment in Large Language Models*, **ACL 2026** (`aclanthology.org/2026.acl-long.1699/`) | Nearest published statement of "the text side is the safe/dominant side"; P1 concludes exactly this (`conclusion.tex:14`) with only `schrodi2025two` and `yi2025decipher` as asymmetry sources. | **should cite** (F11) |
| M4 | *Modality Gap-Driven Subspace Alignment Training Paradigm for Multimodal Large Language Models*, arXiv `2602.07026` (`arxiv.org/pdf/2602.07026v2`) | A gap-driven training objective — the nearest thing found to "use the gap as a training signal", the space P1 claims for DG monitoring. | **optional / verify** (could not confirm its venue from this machine) |
| M5 | Li et al., *DeepAlign: Mitigating Modality Conflict through Modality-Specific Alignment*, **CVPR 2026** (CVF OA `Li_DeepAlign_Mitigating_Modality_Conflict…`) | Second modality-specific-alignment method; P1 cites only `zhang2026imod` for that position (`related_work.tex:12`). | **optional** |
| M6 | *MLAN: Language-Based Instruction Tuning Preserves and Transfers Knowledge in Multimodal Language Models*, ACL KnowLLM 2025 (`aclanthology.org/2025.knowllm-1.6/`) | Independent "preservation" framing for language-side adaptation. | **optional** |
| M7 | Liao & So, *Multimodal Unsupervised Domain Generalization by Retrieving Across the Modality Gap* (Semantic Scholar record) | Retrieval *across* the gap; adjacent to P1's retrieval framing. | **optional** |

**Null results (recorded because they support the novelty claims that survive).** No published work was found
that (a) measures CG/DG **per checkpoint across a PEFT configuration sweep**, or (b) uses a distribution-level
gap statistic as a **training-time stopping signal**. What is pre-empted is the *general* claim about gap
evolution during fine-tuning (M1) and the general gap-preservation objective (M1) — not the specific
DG-as-monitor contribution. That is the boundary the novelty wording should respect (§5, N1–N4).

---

## 5. Novelty-claim exposure

Every explicit novelty/"first" claim in the P1 sources, and whether the searched literature supports it.

| # | claim (file:line) | supported? |
|---|---|---|
| N1 | "we conduct the **first systematic study of modality gap evolution during fine-tuning**" — `paper/main_nn.tex:41` (abstract) | **NO, as written.** M1 (ICCV 2025) studies gap change during CLIP adaptation, including asymmetry. The claim must be scoped to the PEFT configuration space / the CG–DG monitor. *Must-fix wording.* |
| N2 | "we provide the **first systematic study of how these metrics evolve dynamically** during fine-tuning" — `introduction.tex:8` | **NO, as written** — same reason as N1; the "static properties on pre-trained models" contrast with `liu2026tpc` is true of `liu2026tpc` but not of the field (M1). |
| N3 | "We conducted the **first systematic study of modality gap evolution** during parameter-efficient fine-tuning" — `conclusion.tex:4` | **NO, as written.** The PEFT qualifier helps but does not exclude M1's gap-preservation analysis; scope further or drop "first". |
| N4 | "DG-based Alignment Monitoring … **zero-overhead** training-time signal" — `conclusion.tex:12`; `discussion.tex:38`; `main_nn.tex:56`; `highlights.tex:12` | **NOT PRE-EMPTED** by anything found (null result, §4), but unscoped. Nearest prior predictor is `niss2025iimm` (`related_work.tex:18`). Add "to our knowledge" and cite the neighbour. Note `discussion.tex:38` concedes DG-ES is unreliable, so the unqualified "zero-overhead" in the abstract/highlights over-reads the paper's own result. |
| N5 | "~\cite{yi2025decipher} provided the **first proof** that dimension collapse is the fundamental origin of the modality gap" — `related_work.tex:6`; repeated `visual_fragility.tex:8`, `discussion.tex:8`, `introduction.tex:31` | **UNRESOLVED — requires the abstract/body.** The printed preprint and ICML titles are about convergent representations and shared-space alignment, not dimension collapse. If the body does prove it, the citation must point at the **ICML 2026** version (F5) and P1 should say *which* theorem. If it does not, all four sentences are P1's own synthesis and must be reworded. |
| N6 | "**first** systematic characterization" of the modality gap attributed to `liang2022mind` — `related_work.tex:6` | **Supported.** The NeurIPS 2022 paper is the standard origin attribution and nothing found displaces it. |
| N7 | CG/DG decomposition presented as adopted, not invented — `introduction.tex:8` and `methodology.tex:6` credit `liu2026tpc` and `cheng2026maab` explicitly and state the variance-based reformulation as P1's | **Supported and correctly attributed.** This is the cleanest priority statement in the paper and the model the N1–N3 sentences should follow. |
| N8 | Visual Fragility "novelty" | **Not over-claimed.** `visual_fragility.tex:4` and `:37`, `discussion.tex:40` and `conclusion.tex:10` all state it as a parsimonious *interpretation*, not a theorem, and enumerate alternatives. No "first" claim. |

**Pattern to fix**: P1 is disciplined about priority in N7/N8 and careless about it in N1–N3. The fix is the same
sentence shape in all three places — name the configuration space, not the phenomenon.

---

## 6. Verdict

**Citations are mechanically clean and bibliographically unsafe.**

*Clean*: all 44 `\cite` keys resolve, all 44 entries are cited, there are no duplicate keys, the resolved
bibliography carries 44 `\bibitem`s in first-citation order, and the build log reports no undefined citation
or reference — so **there is no `[?]` and no shifted numbering anywhere in `paper/main_nn.pdf`**, and the PDF's
metadata is in sync with `paper/references.bib`. Nothing in P1's bibliography is fabricated: every identifier
that could be resolved resolved to a real publication with a real author list.

*Unsafe*: four entries are wrong in a field a reader can check in one click — two transposed arXiv identifiers
(F1, affecting the SAE-CLIP and vision-reasoning citations, both load-bearing in `related_work.tex:20`), a
wrong identifier on the ICML 2026 uniformity paper (F2, contradicted by the workspace's own second copy), a
wrong year plus an unsupported author list on `niss2025reviving` (F3), and three entries that cite a preprint
where the published version exists (F4 IJCAI 2025, F5 the ICML 2026 retitled version of the modality-gap work,
F6 an IEEE version of GTMA). Seventeen further entries print an arXiv DOI next to a conference venue (F9), and
the file's own "Last verified: 2026-08-14" claim (F13) is not sustainable over that set. One citation is used
for a claim its title cannot support (F8: an LLM-vulnerability paper marshalled as evidence about vision
encoders). One closely competing published work is missing and three novelty claims — including the word
"first" in the abstract — are exposed by it (F7, M1, N1–N3).

**Minimum set of changes:**
1. Fix F1, F2, F3, F4, F6 — five identifier/venue/author corrections, all verifiable in minutes.
2. Re-point `yi2025decipher` at the ICML 2026 version and re-check the four "dimension collapse" claims against
   that text (F5, N5).
3. Scope the three "first systematic study" sentences to the PEFT configuration space, and add Huang et al.
   (ICCV 2025) (F7, N1–N3).
4. Add Sofer et al. (Interspeech 2025) and the ACL 2026 text-dominance paper (F10, F11).
5. Fix the `zhu2026fi` usage and add the LLM→vision-encoder transfer caveat (F8).
6. Either print publisher DOIs for the 17 entries in F9 or remove the DOIs; delete the "Last verified" line
   (F13).
7. Propagate the corrected entries to `paper_a1/`, `paper_a2/`, `paper3/`, `paper2/`, `paper_ap3/` and
   `paper合/` from one source (N4).

Items 1–3 are reviewer-visible in the abstract and in §2 of the manuscript. With 1–7 done, the residual risk in
P1's bibliography is ordinary copy-editing rather than a credibility gap.

---

## 7. Files read / written

**Read (P1, read-only — no build run, no file touched)**: `paper/main_nn.tex`, `paper/main_nn.bbl` (310 lines,
read in full), `paper/main_nn.log`, `paper/main_nn.blg`, `paper/references.bib` (435 lines, read in full),
`paper/sections/{introduction,related_work,methodology,experiments,visual_fragility,discussion,conclusion,
supplementary}.tex`, `paper/highlights.tex`.

**Read (for cross-manuscript propagation only)**: `paper_ap3/refs.bib` (lines 92–121, 226–245, 352–373,
380–399), `paper3/paper_ieee/references.bib`, `paper3/paper/references.bib`,
`paper3/paper_ICLR_backup/references.bib`, `paper合/references.bib`, `paper2/references.bib` (by search index
over `*.bib`).

**Read (register/methodology reference only — not used as evidence)**:
`docs/A23_ROUND3_REVIEW.md`, `docs/CITATION_INTEGRITY_AUDIT.md`.

**Written**: `docs/P1_REVIEW_CITATIONS.md` (this file) — only.

**Not modified**: every file under `paper/`, `paper_a1/`, `paper_a2/`, `paper2/`, `paper3/`, `paper_ap3/`,
`paper合/`, `outputs/` and `docs/`. No LaTeX, BibTeX or PDF artefact was regenerated.
