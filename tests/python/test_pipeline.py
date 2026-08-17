from pathlib import Path

import pytest

from omrpr_analysis.pipeline import STEPS, approve


def test_all_steps_present() -> None:
    assert sorted(STEPS) == list(range(13))


def test_legacy_gate_approval_is_retired() -> None:
    with pytest.raises(RuntimeError, match="OMRPR-NS-001"):
        approve(0, Path("unused"))
