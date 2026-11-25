# Order diagnostics: recorded evidence and offline replay

Run from the repository root with Python 3.12 and the pinned NumPy/SciPy versions:

```bash
python -B results/order_preservation/replay.py --output ../order_replay
```

The output must be new and outside this group. The command validates the three
archives, recomputes scalar summaries, reconstructs 24 recorded recipes, validates
input identities and runs 48 component tests. It writes the derived tables and
command logs to the chosen output. No GPU, data download or training is used.

`ScalarRecords.zip` includes scalar operands, numerical reduction code, 66 paired
YAML/JSON configurations, checkpoint metadata and archived producer code.
`RecordedRecipes.zip` adds source-bound spectral recipes; unknown environment
fields remain explicitly unresolved. `InputIdentities.zip` contains identifiers,
hashes and an offline validator, not images or captions. `Records.json` binds every
included archive and member to its exact content. Raw input access is separate.

Native-backend validation covered 42 fixed core/spectral trajectories, 252 forward
states and 42 epoch3-to4 resumes. These are recorded acceptance facts, not jobs
performed by this replay. They do not certify full retraining, cross-hardware
equivalence or the separate 24 source-method trajectories. No state binaries,
feature/score arrays, base weights, images or captions are distributed here.

The historical exact-numeric failure remains a failure. The canonical successor
has its separately defined arithmetic and acceptance scope; the replay does not
convert one into the other. Mixed, unfavorable and undefined results are retained.
Three paired seeds and dependent views are not independent checkpoint replicates.

Inner archive prose records earlier preparation status and provenance. Its local
paths are historical identifiers, not runnable paths or public download promises.
Use the current command above. The current scoped software grant is the root
`LICENSE_SCOPE.json`, including its archive-member hashes; earlier licensing
statements inside the unchanged archives describe the earlier preparation stage.
Third-party inputs, factual records and models are not relicensed by that grant.

This current group supersedes the older group for new use. The old files remain
available under the unchanged v3.3 tag; no historical DOI or tag has been modified.
