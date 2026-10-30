# New paper B: target journal decision (2026-10-27)

## Topic

**Where to adapt a vision-language model for the marine domain.** A controlled study of adaptation-site selection
(full fine-tuning / linear probe / LoRA on the vision tower / text tower / both) for CLIP-family backbones applied to
marine imagery, measured by retrieval accuracy and by the distribution gap the parent programme already characterises.
Deliverable: a measured rule rather than a leaderboard entry, plus the zero-shot transfer boundary of existing backbones.

## Assets already on disk (no new download needed to start)

| dataset | files | role |
|---|---|---|
| `data/NKSID` | 2617 | marine species classification/retrieval |
| `data/marinelife16k` | 11127 | large marine species corpus |
| `data/marine_captions` | 537 | image-caption pairs for retrieval |
| `data/fathomnet8` | 344 | deep-sea imagery |
| `data/rare-species` | 28 | long-tail check |

`data/second_sonar` (22478 files) is **excluded**: it belongs to the A23 sonar paper (under review at IEEE JOE) and
reusing it here would invite an overlap question.

## Target: Journal of Marine Science and Engineering (JMSE, MDPI)

| field | value |
|---|---|
| publisher | MDPI |
| ISSN | **2077-1312** |
| indexing | **SCIE (Web of Science)** - publisher page states "indexed with Scopus, SCIE (Web of Science), Ei Compendex, GeoRef, Inspec, AGRIS" |
| source (verified 2026-10-27) | https://www.mdpi.com/journal/jmse |
| journal rank (page, 2026-10-27) | JCR Q2 (Oceanography) / CiteScore Q1 (Ocean Engineering) |
| review speed (publisher stats, 2026-10-27) | **16 days submission to first decision**, 3 days acceptance to publication |
| source for speed | https://www.mdpi.com/journal/jmse/stats |
| cost | open access, **APC applies** (amount to be confirmed on the APC page before submission) |
| why this one | fastest verified route that is also SCIE and in-scope for marine applications; the editor pool is used to applied ML papers |

## Alternates (not yet verified as targets - marked pending)

| journal | ISSN | status |
|---|---|---|
| Remote Sensing (MDPI) | 2072-4292 | SCIE line to be confirmed on its journal page; only sensible if the paper is framed around remote-sensing marine imagery |
| Ecological Informatics (Elsevier) | 1574-9541 | index line to be confirmed; official statistics: 42 days submission-to-decision-after-review, 154 days submission-to-acceptance, i.e. **much slower** than JMSE |
| Scientific Reports (Nature Portfolio) | 2045-2322 | indexing page redirected during this check; treat as pending |

Rule reminder: nothing is written into a cover letter or a submission plan until its registry row exists with a source URL
and a date (see `docs/VENUE_SCI_REGISTRY.md`).

## Conflict check

- Paper A / revision: image-text mechanism, general backbones. B is a domain-application study on marine data; the shared
  machinery is the DG diagnostic, which is cited, not reused as a result.
- A23 (IEEE JOE, under review): sonar. B excludes the sonar corpus and does not cite the under-review manuscript.
- Commentary (PRL, under review): opinion piece, no overlap with marine applications.

## First-cut experiment plan (3 blocks, ~2 GPU-days)

1. **Zero-shot boundary**: CLIP B/32, B/16, SigLIP, OpenCLIP zero-shot on NKSID / marinelife16k / fathomnet8; report
   accuracy and retrieval, plus the frozen-backbone distribution gap per dataset.
2. **Site selection under a fixed budget**: full FT vs linear probe vs LoRA on vision / text / both, three seeds, same
   budget; primary metric retrieval R@1 and secondary DG shift. Hypothesis from Paper A: the text tower is the stronger
   lever and the vision tower can widen the gap; B tests whether that transfer holds in a specialised domain.
3. **Long-tail and cross-dataset transfer**: rare-species and deep-sea splits; train on NKSID, test on marinelife16k.

## Open questions for the operator

1. Confirm JMSE as the target (fast, APC cost) or prefer the slower no-APC Elsevier route.
2. Approve the topic framing (marine application study vs a methods paper with marine data as the testbed).

## UPDATE 2026-10-27 22:45 - blocked by the A23 overlap (operator's objection)

The operator pointed out that **A23 already is the marine paper**. Checked: A23 is
*"Alignment health across perception modalities: a gap-surgery diagnostic for marine vision and acoustic sonar models"*
(IEEE Journal of Oceanic Engineering, under review), covering **marine optical imagery and sonar** with **the same
distribution-gap diagnostic** that paper B was going to use. So the topic as written is too close: same domain, same
diagnostic, same team. A "marine VLM adaptation" submission would invite an overlap question from the editor and would
weaken both papers.

Status: **JMSE row in the registry is marked pending, not a target.** Paper B needs a different domain or a different
question before a venue can be fixed.
