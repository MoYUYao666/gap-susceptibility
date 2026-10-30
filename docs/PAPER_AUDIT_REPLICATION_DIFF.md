# Paper Audit Mode - replication, conformance and hardening note

- Date: 2026-10-18 (Asia/Shanghai)
- Reference implementation: `tools/paper_audit/` as committed in `dce8c16`
  (the repository already contained a complete v1.0 implementation).
- This round: read the reference implementation and the specification
  (`docs/PAPER_AUDIT_CREATION_PROMPT.md`, `docs/PAPER_AUDIT_MODE_HANDOVER.md`),
  compared them file by file, commissioned an independent read-only verifier,
  then hardened the toolkit and re-ran the whole acceptance suite.
- No manuscript, submission package or frozen artefact was modified by the
  audit round.

## 1. File-by-file comparison (reference `dce8c16` -> this round)

| file | reference | this round | difference |
|---|---|---|---|
| `__init__.py` | 3 lines, 127 B | unchanged | none |
| `__main__.py` | 4 lines, 103 B | unchanged | none |
| `cli.py` | 176 lines | + freeze-drift exit code, runner error -> exit 2 | `freeze --profile` now returns 1 on added/removed/changed; unexpected runner errors return 2 |
| `model.py` | 110 lines | + `audit_id` field, any ERROR blocks | schema field; verdict hardening (no severity/limit change) |
| `registry.py` | 224 lines, 86 checks | 9 always-MANUAL checks marked `automated=False`, A-03 method text aligned | registry metadata only; 86 ids, dimensions, severities unchanged |
| `profiles.py` | 238 lines, 9 profiles | generic-* note corrected | templates now say "copy this entry and fill it"; no runnable-CLI claim |
| `texutil.py` | 204 lines, stdlib only | unchanged | none |
| `checks.py` | 1092 lines | B-10 string message + false-PASS hardening | I-08 prefix match; B-08/C-02/D-01/I-06 require their evidence; J-02 archives, J-05 environment; no severity changed |
| `report.py` | 130 lines | audit_id fallback only | JSON contract unchanged |
| `README.md` | 139 lines | unchanged | none |
| `templates/AUDIT_REPORT_TEMPLATE.md` | 44 lines | grade set A/B/D | was A/B/C/D (C does not exist) |
| `templates/FIX_EVIDENCE_TEMPLATE.md` | 21 lines | unchanged | check id + file:line before/after + verification + frozen hash |
| `templates/SUBMISSION_READINESS_TEMPLATE.md` | 19 lines | unchanged | none |
| `freeze/p3_prl.json` | 10 files | unchanged | 10/10 hashes match |
| `freeze/a1_nn.json` | 16 files | unchanged | 16/16 hashes match |
| `freeze/a23_joe.json` | 37 files | unchanged | 37/37 hashes match |
| `freeze/prl_commentary.json` | 28 files | unchanged | 28/28 hashes match |

Outside the package, `tools/_p1169_refresh_nc_submission.py` (Paper A
`staged_command`) used `pypdf` for its page count. It now uses TeX Live
`pdfinfo`, so the audited pipeline needs only the standard library plus TeX
Live. The staged rebuild result is identical: `pages=70`, `expected 70`.

## 2. Independent verifier findings and disposition

The verifier ran read-only (no audit/compile/write) at HEAD `baf1233`.

| # | finding | disposition |
|---|---|---|
| 1 | `freeze --profile` verify always exited 0 | **fixed**: exit 1 when added/removed/changed non-empty (cli.py) |
| 2 | I-08 regex missed `main_nc.*`, `main_prl.*`, `main_ieee.*` ... | **fixed**: prefix match with suffixes (checks.py) |
| 3 | any ERROR / SKIP-only / MANUAL-unsigned runs can look READY | **partially fixed**: any ERROR now blocks; SKIP/MANUAL-only READY follows the written verdict rule, and MANUAL sign-off is still a reviewer action (documented, not forged) |
| 4 | J-02 / J-05 unconditional PASS | **fixed**: J-02 checks archived reports; J-05 checks environment fields + lists profile commands |
| 5 | B-08 / C-02 / D-01 / I-06 PASS without the evidence they compare | **fixed**: B-08 WARN without `Output written`, C-02/D-01 FAIL without abstract/PDF, I-06 WARN without a measurable claim |
| 6 | `Report.as_dict()` omitted `audit_id` | **fixed**: `audit_id` is a dataclass field |
| 7 | profile field gaps (only 1/9 has `staged_command`; a1/a23/p3/prl lack ledger commands; p3 `required_declarations=[]`; generic templates not runnable) | **partially fixed**: generic-* note corrected. The other gaps are documented below; no fake commands were invented |
| 8 | 9 always-MANUAL checks advertised as automated | **fixed**: `automated=False` in the registry |
| 9 | template grade A/B/C/D, skill section reference, runner exit-2 drift | **fixed**: template, skill text, exit-2 implemented |
| 10 | E-07 title-dedupe / I-06 ledger claims / I-07 entry count / C-10 / C-01 / F-06 heuristics | **deferred** (documented, non-blocking P1/P2 heuristics) |

## 3. Registry conformance

| dimension | name | checks |
|---|---|---|
| A | Reproducibility and provenance | 8 |
| B | Build and compilation integrity | 10 |
| C | Structure and completeness | 10 |
| D | Journal / venue compliance | 10 |
| E | References and citations | 10 |
| F | Content consistency and number traceability | 10 |
| G | Typography and PDF rendering | 8 |
| H | Data, ethics and declarations | 7 |
| I | Submission package and freeze safety | 8 |
| J | Evidence and hand-off documentation | 5 |
| **total** | | **86** |

`selftest` checks unique ids, dimensions, severities, non-empty title/method,
the three templates and every freeze manifest. All 86 ids have handlers.

## 4. CLI and report schema

All required commands exist. Round 3 was run with:

```text
python -m tools.paper_audit selftest
python -m tools.paper_audit audit --profile <6 profiles> --fail-on NONE
python -m tools.paper_audit audit --profile paperA_nc --staged
python -m tools.paper_audit freeze --profile <4 frozen profiles>
python -m tools.paper_audit list-checks --json
python -m tools.paper_audit render-template --kind audit|fix|readiness
```

The JSON contains `audit_id`, `profile`, `profile_label`, `manuscript`,
`generated_at`, `git_commit`, `git_branch`, `git_dirty`, `verdict`, `grade`,
`counts`, `environment`, `commands`, `artifacts` (SHA-256), `findings`
(check_id / dimension / severity / title / status / message / evidence /
remediation) and the 86-entry `checks` snapshot. The Markdown report has the
verdict, blockers, the ten-dimension coverage table, every finding, commands,
environment and artefact hashes.

Verdict: any P0/P1 FAIL or ERROR -> BLOCKED (D); only P2 FAIL ->
READY-WITH-MINOR (B); otherwise READY (A). SKIP is not PASS; MANUAL needs a
named sign-off.

## 5. Freeze

`freeze --write` records one SHA-256 per file. I-04 recomputes the tree and
reports added/removed/changed as P0. This round: 91/91 files unchanged for
`p3_prl` (10), `a1_nn` (16), `a23_joe` (37), `prl_commentary` (28).
`paperA_nc` / `paperA_springer` have no frozen submission package, so I-04 is
SKIP with that reason. The verify command was tested to return 1 on drift by
code inspection; no frozen file was touched to produce a live drift test.

## 6. Final acceptance (Round 3, 2026-10-18T04:42Z)

| profile | audit id | verdict | pass | fail | warn | manual | skip |
|---|---|---|---|---|---|---|---|
| paperA_nc (staged) | AUD-paperA_nc-20261018T044244Z | READY (A) | 66 | 0 | 2 | 10 | 8 |
| paperA_springer | AUD-paperA_springer-20261018T044217Z | READY (A) | 53 | 0 | 3 | 9 | 21 |
| p3_prl | AUD-p3_prl-20261018T044219Z | READY (A) | 47 | 0 | 3 | 9 | 27 |
| a1_nn | AUD-a1_nn-20261018T044223Z | **BLOCKED (D)** | 58 | 1 | 2 | 9 | 16 |
| a23_joe | AUD-a23_joe-20261018T044231Z | READY (A) | 55 | 0 | 3 | 9 | 19 |
| prl_commentary | AUD-prl_commentary-20261018T044232Z | READY (A) | 53 | 0 | 3 | 9 | 21 |

**A1 regression**: the 04:35Z round audited A1 at 42 pages / 231-word
abstract (READY, `AUD-a1_nn-20261018T043515Z`). At 12:38 local another work
stream added the matched-gap paragraph to `paper_a1/main.tex`; the abstract is
now **264 words** (limit 250). The 04:42Z re-audit reproduces D-02 as a P0
FAIL. The audit round did not edit the manuscript; the fix belongs to a
separate fix round (cut >= 15 words, rebuild the PDF, re-run `a1_nn`, write
`FIXES_<date>.md`).

## 7. Deliberate deviations from a literal reading of the prompt

1. Profiles configure frozen packages / package maps / staged builds only
   where those artefacts exist. `paperA_nc` has a package and a staged
   command; the other five manuscript profiles and the three generic templates
   do not, so the corresponding checks are SKIP with an explicit reason.
   `p3_prl`, `a1_nn`, `a23_joe`, `prl_commentary` do have freeze paths.
2. `p3_prl` uses `required_declarations=[]`; the manuscript carries competing-
   interest and generative-AI declarations but no data-availability statement.
   Adding a declaration the venue does not visibly require (or that the
   manuscript lacks) would silently create a P0; this is recorded as a
   profile review item instead.
3. `a1_nn`, `a23_joe`, `p3_prl` and `prl_commentary` have no claim-ledger
   command in the profile, so F-04 is SKIP; their existing gates run under F-05.
   No script was invented to make the check pass.
4. B-10 stays MANUAL on a staged run even when the staged compile passed; the
   automated PASS is I-03. This is conservative and does not block the verdict.
5. Several PASS findings carry their measured evidence in `message` (counts,
   pages, paths). The registry snapshot plus recorded commands keep each PASS
   reproducible.
6. MANUAL sign-off is a reviewer action, not a field the tool can verify; the
   report lists every MANUAL item and the reports are READY only under the
   written rule "MANUAL allowed, sign-off required".

## 8. Reproduce

```bash
python -m tools.paper_audit selftest
foreach ($p in @('paperA_nc','paperA_springer','p3_prl','a1_nn','a23_joe','prl_commentary')) {
  python -m tools.paper_audit audit --profile $p --out docs/audits --fail-on NONE
}
python -m tools.paper_audit audit --profile paperA_nc --staged --out docs/audits --fail-on NONE
for ($p in @('p3_prl','a1_nn','a23_joe','prl_commentary')) { python -m tools.paper_audit freeze --profile $p }
```
