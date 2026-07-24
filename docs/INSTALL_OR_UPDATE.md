# Install or Update

## 1. Extract outside the project

```bash
cd ~/Downloads
unzip omrpr-cleanroom-starter-v3.0.0.zip
cd omrpr-cleanroom-starter-v3.0.0
```

## 2. Verify archive

```bash
sha256sum --check SHA256SUMS.txt
```

## 3. Preflight

```bash
bash scripts/00_preflight.sh
```

## 4. Install or update

```bash
bash scripts/01_bootstrap_or_update.sh --recreate-env
```

The installer backs up the current project, replaces framework-controlled
files, preserves research-controlled paths, repairs data links, installs Python
3.12.13 through `uv`, creates or uses `uv.lock`, and runs every quality gate.

## 5. Validate

```bash
cd /mnt/space/adev/projects/active/omrpr-analysis
source scripts/activate-project.sh
make quality
make readiness
```

## 6. Commit the initial lockfile

On the first successful installation:

```bash
git add uv.lock .python-version pyproject.toml
git commit -m "build: lock Mastery-aligned Python environment"
```

## 7. Dependency upgrades

Do not upgrade dependencies during normal bootstrap. Use a maintenance branch:

```bash
git switch -c maintenance/dependency-upgrade-$(date +%Y-%m)
make upgrade
```
