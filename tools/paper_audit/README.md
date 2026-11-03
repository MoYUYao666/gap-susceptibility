# Paper Audit Mode

A standardised, evidence-first audit toolkit for manuscripts in this repository.
It turns "check the paper" into a reproducible run: one command produces a
machine-readable JSON report, a human-readable Markdown report, and a
submission verdict derived from a fixed severity policy.

The mode is designed for five situations:

1. pre-submission gate (is the package ready to send?);
2. revision gate (are the reported numbers, references and declarations still consistent?);
3. regression gate (did a rebuild silently break pages, citations or freeze hashes?);
4. independent review (a second agent or a human follows the same protocol);
5. hand-over (the report records what was checked, when, on which commit).

## Quick start

```
python -m tools.paper_audit list-profiles
python -m tools.paper_audit list-checks
python -m tools.paper_audit audit --profile paperA_nc
python -m tools.paper_audit audit --profile paperA_nc --staged
python -m tools.paper_audit audit --profile paperA_nc --out docs/audits --fail-on P1
python -m tools.paper_audit freeze --profile a1_nn --write
python -m tools.paper_audit render-template --kind readiness
```

A run writes two files under `docs/audits/` by default:

- `AUD-<profile>-<UTC>.json` - the complete evidence record (findings, checks,
  commands, environment, hashes); commit this file with the manuscript changes;
- `AUD-<profile>-<UTC>.md` - the same content formatted for human review.

Exit code: 0 when no P0/P1 finding FAILs (configurable with `--fail-on`),
1 otherwise, 2 on an unexpected runner failure.

## Severity and verdict policy

| severity | meaning | release gate |
|---|---|---|
| P0 | a reader/editor can see a factual or compliance defect; the manuscript cannot be submitted | blocks |
| P1 | major: visible defect or inconsistency that must be fixed before submission | blocks |
| P2 | minor: quality / consistency item to fix when feasible | does not block, recorded |
| P3 | informational | recorded only |

Status values: PASS (automated evidence found), FAIL, WARN (review item),
SKIP (not applicable / artefact missing), MANUAL (requires a named sign-off),
ERROR (the check itself failed - treat as a defect in the toolkit).

Verdict: **BLOCKED** if any P0/P1 FAIL/ERROR; **READY-WITH-MINOR** if only P2
failures remain; **READY** otherwise. Grade A/B/D mirrors the verdict.

## Dimensions and registry

The registry lives in `registry.py` and is the single source of truth: every
check has an id, a dimension, a severity, a title and a method description.

| dim | name | examples |
|---|---|---|
| A | Reproducibility and provenance | clean tree, PDF not older than sources, environment recorded |
| B | Build and compilation integrity | errors, undefined refs/cites, overfull, float too large, convergence |
| C | Structure and completeness | required sections, abstract, keywords, figure/table references, declaration order |
| D | Journal / venue compliance | page / abstract / keyword / highlight limits, blinding, portal names, cover-letter claims |
| E | References and citations | missing/unused keys, inline bibliography, duplicate entries, DOI syntax |
| F | Content consistency and number traceability | placeholders, CJK, corrupted tokens, claim-ledger gates, key numbers, stale wording, duplicated sentences |
| G | Typography and PDF rendering | double-numbered headings, HTML artefacts, literal LaTeX, font embedding, metadata, blank pages |
| H | Data, ethics and declarations | data availability, links, AI disclosure, competing interests, funding, CRediT |
| I | Submission package and freeze safety | expected files, hash mapping, staged compile, freeze manifest, sizes, archive integrity, public mirror leaks |
| J | Evidence and hand-off documentation | claim-ledger freshness, archived report, HANDOFF/文件地图 sync, fix evidence |

Print the live registry with `python -m tools.paper_audit list-checks` (add
`--dimension F` to filter).

## Profiles

A profile fixes the manuscript paths, the venue constraints, the claim ledgers,
the consistency gates, the frozen artefacts and the portal package layout.

| profile | manuscript | venue / purpose |
|---|---|---|
| `paperA_nc` | `paper合/` | Paper A, Neurocomputing (elsarticle) |
| `paperA_springer` | `paper合/` | Paper A, Springer sn-jnl variant |
| `p3_prl` | `paper3/paper_ieee/` | P3, Pattern Recognition Letters (IEEEtran) |
| `a1_nn` | `paper_a1/` | A1, Neural Networks (elsarticle review) |
| `a23_joe` | `paper_a2/` | A23, IEEE Journal of Oceanic Engineering |
| `prl_commentary` | `paper_review_prl/` | PRL Commentary (cas-dc) |
| `generic_elsevier`, `generic_ieee`, `generic_prl` | - | templates for a new manuscript |

Profile fields are documented in `profiles.py`. The most important ones:

- `tex` / `pdfs` / `logs` - paths relative to the manuscript directory;
- `limits` - `pages_max`, `abstract_words_max`, `keywords_min/max`,
  `highlights_min/max`, `highlight_chars_max`, `blinded`;
- `required_sections` / `required_declarations`;
- `forbidden_strings` - retired counts or wording that must not reappear;
- `key_numbers` - values that must remain present in named sources;
- `commands` - claim ledgers and consistency gates (kind = ledger / gate);
- `freeze_paths` - submitted artefacts that must never change;
- `package` / `package_expected` / `package_map` - portal package layout;
- `package_frozen` - true when the package is the submitted artefact (skip
  live-hash comparisons; use the freeze manifest instead);
- `build_command` / `staged_command` - the documented build and the
  independent clean-room compile.

## Freeze workflow (under-review manuscripts)

While a manuscript is under review, the submitted artefacts must not change.
Record a baseline once:

```
python -m tools.paper_audit freeze --profile p3_prl --write
```

This writes `freeze/<profile>.json` with one SHA-256 per file. Every later
audit recomputes the tree and reports added / removed / changed files as a P0
failure. Re-freeze only after an explicit decision to issue a replacement
version; note the decision in `HANDOFF.md` and `文件地图.md`.

## Number traceability

The mode does not invent numbers; it verifies that the numbers in the paper are
covered by evidence. Two mechanisms are used:

1. `commands`: run the existing claim ledgers and consistency gates
   (`_claim_ledger*.py`, `_p1181_verify_paperA_consistency.py`,
   `audit_check.py` / `audit_pdf.py`, `verify_a23_fix.py`,
   `_final_check_prl.py`) and require the expected pass string;
2. `key_numbers`: each configured value must still occur in the named sources,
   together with `forbidden_strings` which must not occur anywhere
   in sources, cover letter or PDF.

This keeps the audit aligned with the repository rule that every number must be
traceable to an archived JSON, while the audit itself stays offline.

## Extending the mode

- New venue / manuscript: add a profile in `profiles.py` (copy a nearby one,
  fill the limits and commands, run `list-checks` and `audit --fail-on NONE`).
- New check: add the `Check` entry in `registry.py`, add a handler in
  `checks.py` (or leave it MANUAL), then run `list-checks`.
- New template: add a file under `templates/` and register it in
  `cli.py:cmd_render_template`.
- The report schema is produced by `model.py:Report.as_dict`; keep it stable so
  archived reports can be compared over time.

## Limitations (by design, stated honestly)

- The checks are text heuristics over LaTeX and PDF text; they do not render
  pages or understand mathematics. MANUAL checks are the reviewer's evidence.
- E-04 (numeric citation contiguity) is manual: marker extraction from PDF text
  cannot distinguish citation brackets from other bracketed numbers.
- Claim-ledger commands run with `--apply` where the repository convention
  requires it; this may refresh evidence JSON under `outputs/analysis/`.
- The audit never edits a manuscript. Fixes belong to a separate fix round with
  its own evidence file (see `templates/FIX_EVIDENCE_TEMPLATE.md`).
- PDF text extraction depends on `pdftotext` / `pdftotext -layout` and
  `pdffonts` from TeX Live; missing tools turn the affected checks into SKIP.

## Files

```
tools/paper_audit/
  __init__.py  __main__.py  cli.py
  model.py      data model (Check / Finding / Report, severity, verdict)
  registry.py   the check registry (single source of truth)
  profiles.py   manuscript and venue profiles
  texutil.py    LaTeX helpers (citations, abstracts, keywords, DOIs, ...)
  checks.py     context builder + one handler per check + freeze helpers
  report.py     Markdown / JSON renderer
  templates/    audit report, fix evidence, submission readiness
  freeze/       SHA-256 baselines for the frozen submitted artefacts
```

See `docs/PAPER_AUDIT_MODE.md` for the full operating protocol (phases, roles,
reviewer sign-off, escalation), and `docs/audits/` for the archived reports.
