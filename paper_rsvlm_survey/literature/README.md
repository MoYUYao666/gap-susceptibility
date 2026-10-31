# Literature pipeline

Two scripts, no manual BibTeX.

```powershell
D:\Anaconda\envs\pytorch\python.exe tools\_p1790_rsvlm_lit_harvest.py --per-query 60
D:\Anaconda\envs\pytorch\python.exe tools\_p1791_rsvlm_verify_bib.py --sleep 0.12
```

The first queries OpenAlex for 16 themes and writes the raw and de-duplicated dumps with provenance. The second resolves
every DOI through CrossRef, requires title similarity >= 0.80, and writes `survey.bib` from the survivors only. Exit code
1 means at least one reference failed: fix or drop it, never edit the .bib by hand.

The numeric claims are gated separately: `tools/_p1797_rsvlm_number_gate.py` reads `provenance.md`, opens the archived
abstract for the DOI each value came from, and requires the value to appear in that abstract. It currently passes 24 of 24
rows.
