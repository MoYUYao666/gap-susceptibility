# Editorial Manager fields for the Machine Learning submission

Paste these values into the submission system. Extracted from `Manuscript.pdf` (58 pages, built 2026-10-26).

## Title

Adaptation-Site Selection for PEFT of Contrastive Dual-Encoders: A Gradient-Flow Characterisation of Cross-Modal Alignment and Its Measured Bounds

## Abstract (236 words)

Fine-tuning a vision-language model on a small corpus often widens the image– text gap. We first characterize when this happens. Acrossn= 204archived runs, the Distribution Gap is more strongly associated with retrieval degradation (r=−0.71) than the Centroid Gap is (r=−0.59), and which part of the model is adapted matters more than how its adapters are configured. We then deriveGap Susceptibilityfrom gradient flow: with the alignment energy as the state variable, the rate of gap change is the task gradient projected onto the alignment gradient, yielding an ODE with a PEFT-stable restoring coefficient that reproduces the measured gap trajectory at meanR 2 = 0.949over LoRA, against0.00for a constant baseline. Validation spans six backbones and three adaptation methods (LoRA, Adapter and full fine-tuning). A strict-freezing control that trains only adapter matrices confirms the predicted ordering on CLIP and reverses it on SigLIP, so the text-only advantage is architectural, not universal. Tuning each method to its own learning rate removes the adapter methods’ apparent advantage: LoRA and full fine-tuning then agree on zero-shot accuracy (60.69%against60.87%). Because the runs are nested rather than independent, we report the gap–retrieval association with cluster-robust inference: the slope is−1.05(CR1 standard error0.29,p= 0.016), the family-clustered bootstrap interval is[−0.89,−0.62], and a mixed model with random dataset, backbone and configuration intercepts givesβ=−0.95±0.08, far less precision than 204independent runs: we report an association, not a predictor, and show that its coefficients are protocol functionals, not model constants. 1

## Keywords (6; journal allows 4-6)

Modality gap, Parameter-efficient fine-tuning, Gap susceptibility, Cross-modal alignment, Gradient flow, Distribution Gap

## Author / affiliation

Hongrui Wan (corresponding author), University of Southampton, Southampton SO17 1BJ, United Kingdom, hw4c24@soton.ac.uk

## Declaration answers for the system forms

- Previously submitted elsewhere: **yes, disclosed** - Neurocomputing, manuscript number NEUCOM-D-26-23760, declined
  without external review; the manuscript was then restructured (main text 48 -> 39 pages, negative results promoted to
  their own section) and the offered Elsevier transfer was declined. This is a new submission.
- Not under consideration elsewhere.
- Data and code: archived, version DOI 10.5281/zenodo.23632347 (stated in the Data availability statement).
- Competing interests: none. Funding: none. Generative-AI use: declared in the manuscript.

## Upload list (Editorial Manager item types)

| order | file | item type |
|---|---|---|
| 1 | `CoverLetter.pdf` | Cover Letter |
| 2 | `TitlePage.pdf` | Title Page |
| 3 | `Manuscript.pdf` | Manuscript |
| 4 | `Artwork/*.pdf` (18 files) | Figure |
| 5 | `LaTeXSource.zip` | LaTeX Source |

Not uploaded: `README.md`, `SHA256SUMS.txt`, the auxiliary `.tex` sources of the cover letter and title page.

## Local checks before uploading

- Manuscript: 58 pages, main text 27 + appendix 31; 0 errors, 0 undefined references, 0 undefined citations, 0 overfull.
- `LaTeXSource.zip`: 33 entries, flat (no subdirectories), independently compiled to the same 58 pages.
- Upload filenames contain no underscore; `SHA256SUMS.txt` lists 25 files and all hashes verify.
- Figures: 18 vector PDFs, Times/STIX CID TrueType, no Type 3 fonts.
