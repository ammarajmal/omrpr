# Changelog

## 3.0.0

- Align Python with validated Engineering Mastery baseline 3.12.13.
- Move runtime environment to `~/Projects-runtime/research/omrpr-analysis/.venv`.
- Preserve and use committed `uv.lock` during normal bootstrap.
- Restrict broad dependency upgrades to maintenance branches.
- Replace template-controlled trees to prevent stale scripts and stubs.
- Isolate pytest from ROS/global plugin contamination.
- Add Mastery-style readiness, environment evidence, Git-bundle backups, and release backups.
- Strengthen official AprilTag source, build, linkage, and provenance verification.
- Remove build caches and bytecode from the distributed starter kit.
