# OMRPR analysis governance

## Authority

This repository is the active implementation and derived-output workspace for
OMRPR Paper 2. It does not independently determine scientific completion.

The controlling plan is:

`/mnt/space/adev/projects/active/structural-vision-research/10_PROJECT_MANAGEMENT/RESEARCH_NORTH_STAR_SUPERVISORY_SYSTEM.md`

Machine state is controlled by that repository's `RESEARCH_MASTER_PLAN.json`,
progress ledger, deviation log, and decision register.

## Current aligned state — 2026-08-08

- Score: 24/100.
- S00--S02: foundation mostly accepted; host GPU readiness remains to be checked.
- S03: dataset identity and bounded audit work accepted; final admitted-observation
  manifest still belongs to S05.
- S04: in progress. Official detector provenance is accepted; primary raw pixel
  tracks, stationary-background compensation, and failure-case validation remain.
- S05--S10: existing artifacts are provisional, historical, or scaffolding and do
  not yet earn checkpoint points.
- S11--S12: not started.

## Retired mechanisms

The former `state/gates/step_00.json` through `step_12.json` files were retired
to `/mnt/space/adev/backups/omrpr-analysis/retired-gates-20260808` because they
prematurely represented provisional reviews as completed science. The CLI
approval command is disabled. Step numbers remain engineering labels only.

The competing `docs/NORTHSTAR_PROGRESS_AND_WORKTREE.md` is preserved under
`docs/archive/superseded-20260808/` and has no operational authority.

## Session start

```bash
cd /mnt/space/adev/projects/active/structural-vision-research
python3 scripts/research_supervisor.py validate
python3 scripts/research_supervisor.py status

cd /mnt/space/adev/projects/active/omrpr-analysis
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest tests/python -q
```

Only accepted evidence entered in the sibling ledger changes the score.
