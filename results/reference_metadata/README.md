# Bibliography evidence

Run `python -B replay.py` here to check hashes, rebuild the counts and groups, and
verify that field rates are not authorized. Python 3.9+; no dependencies or network.

- **Harvest and DOI screen:** `harvest.json` preserves all query hits, including
  repeated hits. `deduplicated.json` keeps the first hit by DOI (or OpenAlex ID
  when no DOI is present) and merges its query tags. `doi_screen.json` joins on
  the same key and contains every archived outcome for DOI-bearing records.
  Missing DOIs are not failures. Passes are archived resolver/title checks,
  not relevance or full-text checks; failure summaries do not include resolver
  bodies. Author lists are as archived and may be truncated.
- **Trends:** `summary.json` groups the DOI passes by indexed year and the
  theme matching the most harvest queries (ties follow the order in
  `replay.py`). The capped search is not exhaustive; 2026 is partial, and
  citation counts are snapshots. `selection.json` keeps archived keyword-group
  memberships, not full-text eligibility. `dataset_mentions.json` contains
  precomputed title/abstract name hits, including rows outside the DOI-pass
  set. Mentions (including ambiguous tokens such as AID) do not prove use or
  non-use. Replay counts the labels; the text is not distributed.
- **Fixed sample:** `fixed_sample.json` preserves the 40 indexed IDs in draw
  order and the final edition-specific eligibility decisions. The linked
  repository/preprint identifiers are not interchangeable. Retrospective
  screening and lack of independent recoding mean that no reporting-rate
  denominator is established. No field codes or rates are included.

`provenance.json` maps repository-relative source locators and SHA-256 digests
to the public outputs. Some sources are identified by digest only, not
distributed. Offline replay does not repeat registry queries, inspect PDFs,
redraw the sample, or independently adjudicate eligibility. Separate curated
bibliographies and administrative or textual materials are outside scope.
