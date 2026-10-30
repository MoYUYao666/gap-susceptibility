# A3 competitor landscape (search of 2026-10-29)

Does anyone else do a controlled text-provenance comparison for remote-sensing vision-language models? Search strategy:
CrossRef/arXiv queries on text provenance, synthetic captions, caption quality and data quality for remote-sensing
image-text retrieval, plus general-domain caption-design literature. DOIs below were resolved through CrossRef (or DataCite
for the arXiv DOI) at search time.

| work | venue | doi | what it adds | overlap with A3 |
|---|---|---|---|---|
| GAIA | IEEE Geoscience and Remote Sensing Magazine, 2026 | 10.1109/MGRS.2025.3650613 | 201,005 RS image-text pairs with five GPT-4o captions; fine-tuning CLIP/BLIP2 improves classification, retrieval, captioning | strongest: shows rich *generated* text can beat existing text |
| Exploring Synthetic Captions for RS Vision-Text Foundational Models | M2GARSS 2024 | 10.1109/M2GARSS57310.2024.10537354 | explores synthetic captions for RS vision-text foundation models | same direction, small-scale |
| OSM-CLIP | Applied Sciences, 2026 | 10.3390/app16147002 | 265,000 satellite images paired with OpenStreetMap annotations; +10.81% zero-shot, +5.06% t2i R@1 | shows rich *metadata* works - contradicts a naive "metadata is weak" reading |
| PMPGuard | AAAI 2026 | 10.1609/aaai.v40i10.37767 | detects and mitigates pseudo-matched pairs; SOTA on RSICD/RSITMD/RS5M | data-quality side of the same problem |
| Improving CLIP Training with Language Rewrites (LaCLIP) | NeurIPS 2023 | 10.48550/arXiv.2305.20088 | LLM caption rewrites improve CLIP | general-domain precedent for provenance effects |
| Precision or Recall? Image captions for T2I | EMNLP Findings 2024 | 10.18653/v1/2024.findings-emnlp.211 | controlled analysis of caption precision/recall | methodological precedent |
| How to Train Your T2I Model (synthetic captions) | ICCVW 2025 | 10.1109/ICCVW69036.2025.00711 | design choices for synthetic training captions | general-domain caption design |
| LuoJiaHOG | ISPRS J. P&RS, 2025 | 10.1016/j.isprsjprs.2025.02.009 | hierarchy-aware, geo-aware human captions | community response on the data side |

## Verdict

No work found that holds images, backbone, adapter, pair budget and seeds fixed and varies only the text provenance. The
novelty is therefore the controlled identification and the boundary conditions, not the claim that text matters. The
manuscript is adjusted accordingly: a related-work paragraph citing the works above, a discussion subsection that
reconciles our result with GAIA and OSM-CLIP through information density rather than provenance labels, and a human-rich
arm that tests that reconciliation directly.

## Second sweep, 2026-10-29 (after the cloud supplements)

Queries: human vs synthetic captions for RS retrieval; text-supervision provenance ablation; caption quality ablation
for CLIP; LLM-curated captions for RS image-text matching. Sources: CrossRef + arXiv through the academic-search MCP.

| work | venue / DOI | what it does | why it is not the same question |
|---|---|---|---|
| Ma et al., *From LLMs-curated captions to cross-modal retrieval* (2026) | SSRN preprint, 10.2139/ssrn.7412573 | builds a farm-RS benchmark with LLM-curated + manually verified descriptions and a parameter-efficient retrieval method | text is a resource for a new benchmark and method; no matched-budget comparison of provenance |
| Wang et al., *MLLM-assisted hierarchical image-caption fusion for RS ITR* (2026) | IEEE TMM 28, 10.1109/TMM.2026.3675936 | uses a multimodal LLM to build/fuse captions, then retrieves | fusion method; never isolates where the text came from |
| *A review of cross-modal image-text retrieval in RS* (2025) | Remote Sensing 17(24), 10.3390/rs17243995 | review of ITR methods | review of methods, not a controlled measurement |
| Ricci et al., *Exploring synthetic captions* (2024) | M2GARSS, 10.1109/M2GARSS57310.2024.10537354 | generated vs existing captions, single corpus | one generated source, no matched budget/schedule/seeds, no derived arms |
| GAIA (2026) | GRSM, 10.1109/MGRS.2025.3650613 | 201k GPT-4o captions dataset + fine-tuning gains | dataset paper; generation compared to existing data, not four provenances under control |

**Verdict:** no head-on competitor for "hold everything except the text and measure four provenances across corpora,
backbones, sites, budgets and schedules". The two 2026 works closest in spirit were added as citations and positioned
explicitly in Related Work; the remaining risk is unindexed preprints, not a published competitor.
