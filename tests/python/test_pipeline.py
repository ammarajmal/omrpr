from omrpr_analysis.pipeline import STEPS


def test_all_steps_present() -> None:
    assert sorted(STEPS) == list(range(13))
