# A3 - What does the text buy? Controlled text-supervision provenance for remote-sensing vision-language pretraining

Status: **design stage, 2026-10-28**. Labels follow `docs/PAPER_LABELS.md` (A3 = this paper; A2 = the former A23).

## One-sentence thesis

At a matched annotation budget, the *provenance* of the text that supervises a remote-sensing vision-language
model - metadata strings, segmentation-derived descriptions, templated captions or human captions - changes retrieval
and captioning performance by more than doubling the corpus does, and parameter-efficient adaptation cannot recover the
difference.

This is the experimental counterpart of the survey (`paper_rsvlm_survey/`, submitted to Remote Sensing as
`remotesensing-4692108`): the survey argues that the binding resource is the text, and that evaluation is the weak link;
A3 measures both claims under a controlled design.

## Hypotheses (pre-registered before any run)

| id | hypothesis | primary endpoint |
|---|---|---|
| H1 | At equal supervised-pair budget and equal token budget, human captions > segmentation-derived > metadata strings for cross-modal retrieval | R@1 (image-to-text and text-to-image) |
| H2 | The return from extra data depends on provenance: metadata-derived text saturates early, human captions keep improving | R@1 vs corpus size scaling curve |
| H3 | Adapter updates on the text tower preserve the shared space better than vision-tower updates; the modality gap predicts zero-shot retention | modality gap (cosine distance between image/text centroids) vs zero-shot classification accuracy |
| H4 | Templated captions inflate CIDEr without improving retrieval, i.e. the two task families rank the same provenance differently | CIDEr vs R@1 rank disagreement |

H3 is the bridge to A, A1 and A2: those papers characterise where updates should go; A3 tests whether the answer depends
on what the text is.

## Design

**Text-provenance factor (4 levels), all built from the same public annotations so that provenance is the only change:**

1. **metadata** - sensor, resolution, location and class strings assembled from dataset metadata;
2. **segmentation-derived** - descriptions generated from bounding boxes / masks in DIOR, DOTA, LEVIR (object counts,
   sizes, relative positions);
3. **templated** - the same content as (2) but through fixed sentence templates (this is the control that isolates
   template artefacts from information);
4. **human** - RSICD, RSITMD and NWPU-Captions captions filtered to usable pairs.

**Budget factor (matched):** 10k / 50k / 200k supervised pairs, and separately matched total tokens, so that "more
data" and "better data" are separable.

**Adaptation factor:** frozen CLIP-family backbone (RemoteCLIP ViT-B/32) plus LoRA at r=8 inserted in (i) vision tower
only, (ii) text tower only, (iii) both; 3 seeds per cell.

**Tasks and metrics:** retrieval on RSICD/RSITMD/NWPU-Captions (R@1/R@5/R@10, both directions); classification on
AID/UCM (linear probe and zero-shot); captioning on RSICD (CIDEr, BLEU-4, METEOR, SPICE); diversity (unique n-grams,
self-BLEU); modality gap and alignment/uniformity diagnostics; zero-shot retention after adaptation.

**Statistics:** every cell reports mean and standard deviation over 3 seeds; hypotheses tested with paired bootstrap
over query sets; equivalence margins declared in advance (a difference counts only if it exceeds the seed spread, which
is itself the discipline the survey found missing in 0/8 audited papers).

## Work plan and cost

| step | what | time |
|---|---|---|
| 1 | build the four provenance corpora from public annotations; hash and freeze them | 4-5 days |
| 2 | pilot: one cell, verify loader/paths/assertions, measure peak memory | 1 day (cloud) |
| 3 | full grid: 4 provenance x 3 budgets x 3 sites x 3 seeds, parallel by memory | 3-5 days (one 24 GB GPU) |
| 4 | analysis tables and figures (script + JSON provenance, repository rules apply) | 2 days |
| 5 | manuscript (English), internal audit, submission package | 1 week |

## Venue shortlist (subscription route = no APC; SCIE mandatory per `docs/VENUE_SCI_REGISTRY.md`)

| rank | journal | publisher | indexing | APC for us | fit |
|---|---|---|---|---|---|
| 1 | **IEEE JSTARS** (ISSN 1939-1404) | IEEE | SCIE (verify MJL before use) | none (subscription) | strongest fit: applied remote-sensing methods with quantitative evaluation |
| 2 | **Image and Vision Computing** (ISSN 0262-8856) | Elsevier | SCIE **verified 2026-10-26** in registry | none (subscription) | vision-language representation learning; good fallback |
| 3 | **Pattern Recognition** (ISSN 0031-3203) | Elsevier | SCIE **verified 2026-10-26** in registry | none (subscription) | method contribution, higher bar; P1 was rejected there but A3 is a different paper |
| 4 | **ISPRS J. Photogrammetry and Remote Sensing** (ISSN 0924-2716) | Elsevier | SCIE (verify MJL) | none (subscription) | stretch: perfect topical fit, high bar |

Excluded: Remote Sensing (MDPI) - APC; Neurocomputing - Paper A was desk-rejected there; MDPI journals in general.

**Verification status:** JSTARS and ISPRS J are `pending MJL verification`; no submission material may name them as a
target until the row is added to `docs/VENUE_SCI_REGISTRY.md` with the MJL URL and date. Image and Vision Computing is
ready to use today.

## Relation to the other papers

| paper | relation |
|---|---|
| A, A1, A2 | adaptation-site and gradient-flow characterisation; A3 supplies the text-side variable those papers hold fixed |
| P3 | power-law/ODE protocol; A3 reuses its seed-and-dispersion discipline |
| Commentary | argues evaluation practice must change; A3 demonstrates the change on one axis |
| Survey | states the provenance argument; A3 is its experimental test |

## Implementation note after the local pilot (2026-10-28)

The public caption datasets carry no object annotations, so the four arms split into two families:

| family | datasets | human arm | templated / segmented / metadata arms |
|---|---|---|---|
| caption datasets | RSICD (built), NWPU-Captions (downloading) | the dataset's own captions | derived mechanically from those captions, the class labels and computed image statistics (a *degradation ladder*: identical images, decreasing textual richness) |
| annotated dataset | DIOR-RSVG (boxes + referring expressions) | its human expressions | generated from the ground-truth boxes, so these two arms test the template effect with real object annotations |

RSITMD annotations are distributed only through Baidu Netdisk / Google Drive per the authors' repository, so its
extension is marked "operator download" and it does not block the design: RSICD and NWPU-Captions already provide two
human-caption domains, and DIOR-RSVG supplies the annotation-to-text arms.

What is frozen so far (local): RSICD corpus, 10,921 images, four arms with 40,384 (human), 10,921 (templated),
10,921 (segmented), 10,921 (metadata) image-text pairs; hashes in `paper_a3/corpora/rsicd/provenance_manifest.json`.
