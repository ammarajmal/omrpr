.PHONY: doctor inventory audit status test quality upgrade apriltag readiness env-report backup

doctor:
	uv run omrpr doctor

inventory:
	uv run omrpr inventory

audit:
	uv run omrpr bag-audit

status:
	uv run omrpr pipeline status

test:
	env -u PYTHONPATH \
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
	uv run python -m pytest \
		-p pytest_cov \
		-vv

quality:
	uv run ruff format --check .
	uv run ruff check .
	uv run python -m mypy src/omrpr_analysis
	env -u PYTHONPATH \
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
	uv run python -m pytest \
		-p pytest_cov \
		--cov=omrpr_analysis \
		--cov-report=term-missing \
		--cov-report=xml:outputs/reports/coverage.xml

upgrade:
	bash scripts/02_upgrade_dependencies.sh

apriltag:
	bash scripts/03_install_official_apriltag.sh

readiness:
	bash scripts/06_project_readiness.sh

env-report:
	uv run python scripts/write_environment_report.py

backup:
	bash scripts/07_backup_project.sh
