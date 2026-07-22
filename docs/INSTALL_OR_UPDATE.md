# Install or Update

The installer is idempotent. It may be rerun after partial setup or on an
existing project. It never deletes raw data.

## 1. Extract the kit

```bash
cd ~/Downloads
unzip -o omrpr-cleanroom-starter-v2.0.0.zip
cd omrpr-cleanroom-starter-v2.0.0
```

## 2. Run preflight

```bash
bash scripts/00_preflight.sh
```

## 3. Update/create the project

```bash
bash scripts/01_bootstrap_or_update.sh
```

Useful options:

```bash
bash scripts/01_bootstrap_or_update.sh --recreate-env
bash scripts/01_bootstrap_or_update.sh --commit
bash scripts/01_bootstrap_or_update.sh --project-root /custom/project --data-root /custom/data
```

## 4. Activate and validate

```bash
cd /mnt/space/adev/projects/active/omrpr-analysis
source scripts/activate-project.sh
make quality
uv run omrpr doctor
```

## 5. Install official AprilTag

```bash
bash scripts/03_install_official_apriltag.sh
uv run omrpr verify-apriltag
```

## 6. Place or verify data

```bash
bash scripts/04_data_placement_assistant.sh
uv run omrpr inventory
```
