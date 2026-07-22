.PHONY: doctor inventory audit status quality upgrade apriltag

doctor:
	uv run omrpr doctor

inventory:
	uv run omrpr inventory

audit:
	uv run omrpr bag-audit

status:
	uv run omrpr pipeline status

quality:
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy src/omrpr_analysis
	uv run pytest --cov=omrpr_analysis

upgrade:
	bash scripts/02_upgrade_dependencies.sh

apriltag:
	bash scripts/03_install_official_apriltag.sh
