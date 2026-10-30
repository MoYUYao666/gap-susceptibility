# Fix evidence - <manuscript> - <date>

One line per defect. Every row must point at the audit check id that found it,
the file and line changed, and the command whose output proves the fix.

## 1. Scope and constraints

- Audit source: <report file / audit id>
- Frozen artefacts that must not change: <paths + hash manifest>
- Write scope of this fix round: <paths>
- Baseline git commit: <commit>

## 2. Changes

| # | check id | severity | file:line | before | after | why |
|---|---|---|---|---|---|---|
| 1 |  |  |  |  |  |  |

## 3. Verification

| command | expected | observed | pass |
|---|---|---|---|
|  |  |  |  |

Include: page counts (pdfinfo), build log counters (errors / undefined / overfull),
claim-ledger counts, consistency gates, PDF text assertions (pdftotext), and the
frozen-artefact hash comparison.

## 4. Residual items and judgement calls

- <item> - <why it is deferred> - <who decides>
