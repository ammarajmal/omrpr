# Generated artifact retention policy

**Decision date:** 2026-08-01
**Applies from:** G0 repository stabilization

## Scientific outputs

`outputs/` and `manuscript/generated/` are reproducible working products and
remain ignored except for directory placeholders. A publication release must
not depend on an untracked working file: locked results are packaged with a
configuration hash, input manifest, software commit, environment report, and
result checksums in a versioned release/archive location defined at G9.

Small human-reviewed evidence summaries may be committed under `docs/` when
they cite the run identity and hashes. Raw data and private records must never
be committed.

## Graphify

Graphify output is a disposable code-navigation index, not scientific evidence.
The current G0 snapshot is retained as a historical architectural map because
it was included in stabilization commit `7e0bc23`. Future use follows these
rules:

- rebuild only at gate boundaries or for a declared impact-analysis task;
- never cite a graph edge as primary evidence;
- do not commit `graphify-out/cache/`;
- retain `GRAPH_REPORT.md`, `manifest.json`, or a graph export only when a
  reviewed gate snapshot materially aids traceability;
- record the Graphify version and source commit in any retained snapshot;
- prefer regeneration over accumulating successive cache trees.

The already-tracked G0 cache is grandfathered for preservation. It may be
removed from version control in a dedicated cleanup commit after the repository
remote and review boundary are established; removal must not delete the local
working copy unless explicitly requested.

## Test and coverage products

`.pytest_cache`, `.ruff_cache`, `.mypy_cache`, coverage databases, and generated
coverage reports are disposable. CI may publish them as short-lived artifacts,
but they are not result evidence.
