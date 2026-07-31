# Codex development workflow and tooling decision

**Decision date:** 2026-07-31

## Recommended stack now

1. **Codex + repository `AGENTS.md`** for scoped implementation and review.
2. **Git + small gate-scoped commits**; use a remote as the recovery and review
   boundary once configured.
3. **`uv`, pytest, Ruff, mypy, and pre-commit** as the executable quality layer.
4. **RTK** for compact test, Git, Ruff, and pytest output when logs are large.
5. **Graphify, code-only and local**, as the existing architectural map until
   the repository stabilizes. Rebuild it at gate boundaries, not continuously.
6. **Ollama** for bounded offline extraction/classification and draft assistance;
   never for scientific adjudication, threshold selection, or locked claims.

## MCP decision

MCP is a connector protocol, not an automatic quality improvement. Add a server
only when Codex needs a capability it cannot get safely from the repository or
CLI.

Recommended later:

- GitHub MCP/app after a remote exists, for pull-request and CI state.
- A read-only local provenance/results server only after the observation,
  result, and configuration schemas are stable.

Do not add now:

- a filesystem MCP (Codex already has scoped filesystem access);
- a database/vector MCP before stable schemas exist;
- an internet research MCP for raw/private experimental data;
- an Ollama MCP merely to call local models when a small versioned CLI/API
  adapter is easier to audit.

Every future MCP must have least-privilege scope, pinned version/configuration,
an explicit data-egress statement, and reproducible fallbacks.

## Tool-by-tool verdict

| Tool | Verdict | Reason |
|---|---|---|
| RTK 0.43.0 | USE NOW | Reduces noisy command output; does not alter scientific computation. Keep raw logs as artifacts when needed. |
| Graphify 0.9.28 | KEEP, BOUNDED | A graph already exists and is useful for navigation/impact questions. Use code-only/local extraction and treat generated graphs as disposable indexes. |
| CodeGraph 1.5.0 | PILOT LATER | Its symbol/caller/affected-test queries overlap Graphify. Pilot on three real tasks and adopt only if it outperforms the existing graph; do not maintain both by default. |
| Headroom 0.32.1 | DEFER | A proxy/compression layer complicates provenance and can hide omitted context. Evaluate only after baseline tests, with an A/B accuracy audit. |
| gstack workflow | SELECTIVE LATER | Useful product/review roles, but the full opinionated delivery system is excessive for a single-researcher scientific pipeline. Borrow review/checklist skills only if they respect `AGENTS.md`. |
| GNU `gstack` 17.1 | NOT THE AI TOOL | The installed `/usr/bin/gstack` is the GNU process stack-dump utility, not Garry Tan's workflow. |
| Caveman | DO NOT ADOPT | It optimizes terse interaction/token use, not scientific correctness or provenance; it is not installed and would duplicate RTK/Headroom goals. |
| Ollama | USE OFFLINE, BOUNDED | Suitable for metadata classification, document chunking, test-case brainstorming, and summaries with source pointers. Human/Codex validation remains required. |

## Evaluation protocol for any new agent tool

Run the candidate on three representative tasks:

1. trace an affected pipeline path;
2. identify tests affected by a change;
3. explain a provenance-sensitive result.

Score correctness, missed files, false relationships, wall time, context/token
volume, reproducibility, data egress, and maintenance cost. Adoption requires no
scientific-evidence mutation, no missed critical dependency versus the baseline,
and a material time/context improvement. Record the decision in
`docs/DECISION_LOG.md`.

## Daily Codex loop

1. Read `ai-context/PROJECT_STATE.yaml` and the current gate/task.
2. Confirm the worktree and preserve unrelated changes.
3. Implement one bounded task with tests and provenance.
4. Run the smallest relevant checks, then the gate suite.
5. Update current state, task queue, decision log, and machine-readable state.
6. Commit one coherent change and push/open review when the remote is available.

## Research safeguards

- Never send raw/private experimental data to an external MCP or hosted tool.
- Never accept a graph edge, RAG answer, or local-model summary as primary
  evidence.
- Never allow output compression to replace stored raw diagnostics.
- Pin tool versions used for a release and include them in environment evidence.
