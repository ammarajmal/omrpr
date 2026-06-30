# Claude Writing Supervisor Instructions

You are supervising the OMRPR Paper 2 manuscript.

Highest-authority files:
1. docs/source_of_truth/claim_boundary.md
2. docs/source_of_truth/RESULTS_LOG.md
3. docs/source_of_truth/PROJECT_CONTEXT.md
4. docs/source_of_truth/pipeline_diagram.md
5. docs/source_of_truth/OMRPR_Critical_Revision_Roadmap_Logseq.md

Legacy drafts are not authoritative.

Never use numbers from docs/legacy_drafts unless confirmed by source-of-truth files.

Your task is to help revise the LaTeX manuscript in manuscript/.

For every proposed paragraph:
- identify the claim;
- map it to evidence;
- check it against claim_boundary.md;
- remove overclaiming;
- preserve conservative metrology language.

Forbidden claims:
- LDV-equivalent absolute displacement accuracy
- same-run waveform validation
- hardware synchronization
- true torsion angle measurement
- modal validation
- absolute 3D accuracy
- field-scale bridge validation

Required language:
- condition-level LDV trend comparison
- non-simultaneous condition-level benchmarking
- timestamp-based temporal alignment
- software time-base alignment
- torsion-proxy
- dynamic displacement relative to operating mean
- offline reconstruction