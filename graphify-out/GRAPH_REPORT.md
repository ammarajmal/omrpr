# Graph Report - .  (2026-07-28)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 210 nodes · 270 edges · 50 communities (41 shown, 9 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `77c79b4f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- omrpr_analysis/cli.py
- image_audit.py
- bag_audit.py
- activate-project.sh
- run_step00.sh
- 01_bootstrap_or_update.sh
- 00_preflight.sh
- markdown_table
- classify
- newest_run
- decision
- camera_from_path
- test_with_fixture.sh
- run_step01.sh
- 01_preflight.sh
- 03_summarize_audit.py
- run_pipeline.sh
- 04_data_placement_assistant.sh
- 07_backup_project.sh
- 02_run_audit.sh
- VERIFY_DOWNLOAD.sh
- omrpr-analysis

## God Nodes (most connected - your core abstractions)
1. `audit_tree()` - 13 edges
2. `_audit_short_topic()` - 8 edges
3. `_audit_topic()` - 8 edges
4. `audit_bag()` - 8 edges
5. `FrameMetric` - 7 edges
6. `audit_tree()` - 6 edges
7. `decode_compressed()` - 6 edges
8. `decode_raw()` - 6 edges
9. `decode_message()` - 6 edges
10. `frame_metric()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `audit_tree()`  [EXTRACTED]
  scripts/steps/step01_image_decode_sampling_audit.py → src/omrpr_analysis/image_audit.py
- `test_decode_compressed_jpeg()` --calls--> `decode_compressed()`  [EXTRACTED]
  tests/python/test_image_audit.py → src/omrpr_analysis/image_audit.py
- `test_decode_bgr8_with_row_padding()` --calls--> `decode_raw()`  [EXTRACTED]
  tests/python/test_image_audit.py → src/omrpr_analysis/image_audit.py
- `test_timing_gates()` --calls--> `classify()`  [EXTRACTED]
  tests/python/test_bag_audit.py → src/omrpr_analysis/bag_audit.py
- `test_deterministic_indices_include_boundaries()` --calls--> `deterministic_indices()`  [EXTRACTED]
  tests/python/test_image_audit.py → src/omrpr_analysis/image_audit.py

## Import Cycles
- None detected.

## Communities (50 total, 9 thin omitted)

### Community 0 - "omrpr_analysis/cli.py"
Cohesion: 0.13
Nodes (20): command, bag_audit(), doctor(), inventory(), pipeline_approve(), pipeline_status(), Path, verify_apriltag() (+12 more)

### Community 1 - "image_audit.py"
Cohesion: 0.18
Nodes (25): Any, Exception, main(), audit_tree(), _data_bytes(), decode_compressed(), decode_message(), decode_raw() (+17 more)

### Community 2 - "bag_audit.py"
Cohesion: 0.14
Nodes (21): Connection, int64, Nanoseconds, Reader, audit_bag(), _audit_short_topic(), _audit_topic(), audit_tree() (+13 more)

### Community 3 - "activate-project.sh"
Cohesion: 0.11
Nodes (17): 02_upgrade_dependencies.sh script, LD_LIBRARY_PATH, 03_install_official_apriltag.sh script, bad(), ok(), section(), 06_project_readiness.sh script, warnf() (+9 more)

### Community 4 - "run_step00.sh"
Cohesion: 0.17
Nodes (11): OMRPR_EXPECTED_BAGS, OMRPR_EXPECTED_STATIC, OMRPR_EXPECTED_WTT_5SEC, OMRPR_EXPECTED_WTT_MAIN, OMRPR_GAP_THRESHOLD_S, OMRPR_PROJECT_ROOT, OMRPR_RUN_DIR, OMRPR_VENV (+3 more)

### Community 5 - "01_bootstrap_or_update.sh"
Cohesion: 0.29
Nodes (9): backup_existing_project(), ensure_link(), OMRPR_DATA_ROOT, OMRPR_PROJECT_ROOT, replace_tree(), 01_bootstrap_or_update.sh script, usage(), UV_LINK_MODE (+1 more)

### Community 6 - "00_preflight.sh"
Cohesion: 0.70
Nodes (4): bad(), ok(), 00_preflight.sh script, warnf()

### Community 7 - "markdown_table"
Cohesion: 0.67
Nodes (3): DataFrame, main(), markdown_table()

### Community 8 - "classify"
Cohesion: 0.83
Nodes (3): classify(), main(), Path

### Community 9 - "newest_run"
Cohesion: 0.67
Nodes (3): main(), newest_run(), Path

### Community 10 - "decision"
Cohesion: 0.67
Nodes (3): Series, decision(), main()

### Community 12 - "camera_from_path"
Cohesion: 0.83
Nodes (3): camera_from_path(), main(), Path

### Community 13 - "test_with_fixture.sh"
Cohesion: 0.50
Nodes (3): OMRPR_EXPECTED_BAGS, OMRPR_RUN_DIR, test_with_fixture.sh script

## Knowledge Gaps
- **37 isolated node(s):** `VERIFY_DOWNLOAD.sh script`, `omrpr-analysis`, `run_pipeline.sh script`, `OMRPR_PROJECT_ROOT`, `OMRPR_DATA_ROOT` (+32 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `audit_tree()` connect `bag_audit.py` to `omrpr_analysis/cli.py`?**
  _High betweenness centrality (0.007) - this node is a cross-community bridge._
- **What connects `VERIFY_DOWNLOAD.sh script`, `omrpr-analysis`, `run_pipeline.sh script` to the rest of the system?**
  _37 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `omrpr_analysis/cli.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13118279569892474 - nodes in this community are weakly interconnected._
- **Should `bag_audit.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1422924901185771 - nodes in this community are weakly interconnected._
- **Should `activate-project.sh` be split into smaller, more focused modules?**
  _Cohesion score 0.10822510822510822 - nodes in this community are weakly interconnected._
