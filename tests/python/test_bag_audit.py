from omrpr_analysis.bag_audit import classify


def test_timing_gates() -> None:
    assert classify(60.0, 0.02)[0] == "PASS"
    assert classify(58.5, 0.02)[0] == "WARN"
    assert classify(54.9, 0.02)[0] == "FAIL"
    assert classify(60.0, 0.6)[0] == "FAIL"
