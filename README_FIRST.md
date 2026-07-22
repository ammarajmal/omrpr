# OMRPR Clean-Room Starter Kit v2.0.0

This package updates or creates the OMRPR analysis project without deleting raw
research data. It is designed to be rerunnable: existing directories, stubs,
Git history, external datasets, and pipeline gates are preserved unless you
explicitly request replacement.

## First command

```bash
cd ~/Downloads/omrpr-cleanroom-starter-v2.0.0
bash scripts/00_preflight.sh
```

Then perform the update/install:

```bash
bash scripts/01_bootstrap_or_update.sh
```

The default locations are:

- project: `/mnt/space/adev/projects/active/omrpr-analysis`
- data: `/mnt/space/adev/datasets/omrpr`
- virtual environment: `$HOME/.venvs/omrpr-analysis`

The installer:

1. backs up existing project-controlled files;
2. updates template code and documentation;
3. preserves `.git`, raw data, generated results, local configuration, and gates;
4. recreates missing directories and repairs symlinks;
5. installs the newest compatible Python with `uv`;
6. resolves the latest compatible dependencies and writes `uv.lock`;
7. runs formatting, linting, type checking, tests, and project diagnostics;
8. does not commit unless `--commit` is supplied.

Install the official detector after the project passes:

```bash
cd /mnt/space/adev/projects/active/omrpr-analysis
source scripts/activate-project.sh
bash scripts/03_install_official_apriltag.sh
```

Never install or use `pupil_apriltags`, and never use `cv2.aruco` for tag
detection. OpenCV is permitted only for calibration, image I/O, visualization,
and optional pose cross-checking.
