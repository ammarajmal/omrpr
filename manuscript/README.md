# Paper 2 manuscript package

This directory is the manuscript-facing layer for the reviewed OMRPR evidence
chain. It is intentionally separate from `outputs/`, which remains the
reproducible pipeline-output layer.

## Current assembly status

- The pipeline passes the project readiness check (`PASS=31`, `WARN=1`,
  `FAIL=0` on 2026-08-04).
- The first reviewed figure and table have been transferred without altering
  their content.
- `drafts/paper-outline.md` provides a claim-controlled writing scaffold.
- `results/evidence-and-claim-register.md` records the evidence source and
  permitted language for the first manuscript claims.
- Final prose, captions, authorship decisions, journal formatting, and the
  submission archive remain pending.

## Directory roles

- `drafts/`: paper text and author-review notes.
- `figures/`: reviewed, manuscript-facing figures.
- `tables/`: reviewed, manuscript-facing tables.
- `results/`: evidence registers and manuscript-facing result summaries.
- `submission/`: final author-approved submission files only.

Do not edit transferred figures or tables in place. Regenerate upstream,
review the new artifact, and then replace the manuscript copy while updating
the evidence register.
