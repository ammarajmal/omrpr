from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.laser.parse_tesolution import (
    CM_TO_MM,
    DP,
    PVOLT,
    ConditionStats,
    compute_condition,
    compute_condition_timeseries,
    load_dn,
    load_rpm_lookup,
    parse_all,
    write_all_timeseries,
    write_condition_timeseries,
    write_csv,
)


def test_compute_condition_applies_bias_calibration_and_channel_formulas() -> None:
    bias = np.array([0.01, 0.02])
    data = np.array(
        [
            [0.02, 0.03],
            [0.03, 0.01],
        ]
    )
    stats = compute_condition(dn=7, rpm=55.0, data=data, bias=bias)

    dat1 = (data - bias) * PVOLT
    expected_bending = (dat1[:, 0] + dat1[:, 1]) / 2 * CM_TO_MM
    expected_torsion = (dat1[:, 1] - dat1[:, 0]) * DP * CM_TO_MM

    assert stats.dn == 7
    assert stats.rpm == 55.0
    assert stats.bending_mean_mm == pytest.approx(float(expected_bending.mean()))
    assert stats.bending_rms_mm == pytest.approx(float(expected_bending.std()))
    assert stats.bending_peak_mm == pytest.approx(
        float(np.max(np.abs(expected_bending - expected_bending.mean())))
    )
    assert stats.torsion_mean_mm == pytest.approx(float(expected_torsion.mean()))
    assert stats.torsion_rms_mm == pytest.approx(float(expected_torsion.std()))
    assert stats.torsion_peak_mm == pytest.approx(
        float(np.max(np.abs(expected_torsion - expected_torsion.mean())))
    )


def test_compute_condition_timeseries_returns_every_converted_sample() -> None:
    bias = np.array([0.01, 0.02])
    data = np.array([[0.02, 0.03], [0.03, 0.01], [0.00, 0.04]])

    bending_mm, torsion_mm = compute_condition_timeseries(data, bias)

    calibrated = (data - bias) * PVOLT
    np.testing.assert_allclose(bending_mm, (calibrated[:, 0] + calibrated[:, 1]) / 2 * CM_TO_MM)
    np.testing.assert_allclose(torsion_mm, (calibrated[:, 1] - calibrated[:, 0]) * DP * CM_TO_MM)


def test_compute_condition_zero_signal_gives_zero_stats() -> None:
    bias = np.array([0.5, 0.5])
    data = np.tile(bias, (10, 1))
    stats = compute_condition(dn=1, rpm=10.0, data=data, bias=bias)
    assert stats.bending_mean_mm == pytest.approx(0.0)
    assert stats.bending_rms_mm == pytest.approx(0.0)
    assert stats.torsion_mean_mm == pytest.approx(0.0)
    assert stats.torsion_rms_mm == pytest.approx(0.0)


def test_compute_condition_pure_side_minus_center_signal_isolated_to_torsion() -> None:
    bias = np.array([0.0, 0.0])
    data = np.array([[1.0, -1.0], [1.0, -1.0]])
    stats = compute_condition(dn=1, rpm=10.0, data=data, bias=bias)
    assert stats.bending_mean_mm == pytest.approx(0.0)
    expected_torsion = (-1.0 - 1.0) * PVOLT[0] * DP * CM_TO_MM
    assert stats.torsion_mean_mm == pytest.approx(expected_torsion)


def test_load_dn_reads_only_first_two_columns(tmp_path) -> None:
    path = tmp_path / "D5"
    path.write_text("0.01\t0.02\t0.99\n0.03\t0.04\t0.88\n")
    data = load_dn(path)
    assert data.shape == (2, 2)
    np.testing.assert_allclose(data, [[0.01, 0.02], [0.03, 0.04]])


def test_load_rpm_lookup_excludes_non_condition_rows_and_missing_rpm(tmp_path) -> None:
    xlsx = tmp_path / "Windspeed.xlsx"
    rows = [
        ["file", "rpm", "u_meas", "u_calc", "note", "a", "b", "c", "d"],
        ["D1", 10, 1.0, 1.1, "", 0, 0, 0, 0],
        ["D2", 20, 2.0, 2.1, "", 0, 0, 0, 0],
        ["D3", None, 3.0, 3.1, "", 0, 0, 0, 0],
        ["notes", "n/a", None, None, "header-like row", 0, 0, 0, 0],
    ]
    pd.DataFrame(rows).to_excel(xlsx, header=False, index=False)

    lookup = load_rpm_lookup(xlsx)

    assert lookup == {1: 10.0, 2: 20.0}
    assert 3 not in lookup
    assert 0 not in lookup


def test_parse_all_covers_full_real_condition_set_and_matches_legacy_reference() -> None:
    from omrpr_analysis.paths import ProjectPaths

    paths = ProjectPaths.discover()
    dataset_root = paths.raw / "laser/csv/tunnel-a-2024/2D_WTT"
    if not dataset_root.exists():
        pytest.skip("2024 tunnel-a LDV raw dataset not present on this workstation")

    rows = parse_all(dataset_root)
    by_dn = {row.dn: row for row in rows}

    assert sorted(by_dn) == list(range(1, 39))

    d38 = by_dn[38]
    assert d38.rpm == pytest.approx(310.0)
    assert d38.torsion_rms_mm == pytest.approx(17.08, abs=0.05)


def test_write_csv_round_trips_all_fields(tmp_path) -> None:
    rows = [
        ConditionStats(
            dn=1,
            rpm=10.0,
            bending_mean_mm=0.1,
            bending_rms_mm=0.2,
            bending_peak_mm=0.3,
            torsion_mean_mm=0.4,
            torsion_rms_mm=0.5,
            torsion_peak_mm=0.6,
        )
    ]
    out_path = tmp_path / "out" / "laser.csv"
    write_csv(rows, out_path)

    read_back = pd.read_csv(out_path)
    assert list(read_back.columns) == list(ConditionStats.__dataclass_fields__)
    assert read_back.iloc[0]["dn"] == 1
    assert read_back.iloc[0]["torsion_rms_mm"] == pytest.approx(0.5)


def test_write_condition_timeseries_uses_raw_sample_indices(tmp_path) -> None:
    out_path = write_condition_timeseries(
        4,
        np.array([0.1, 0.2, 0.3]),
        np.array([-0.1, -0.2, -0.3]),
        tmp_path / "timeseries",
    )

    assert out_path == tmp_path / "timeseries" / "D4.csv"
    read_back = pd.read_csv(out_path)
    assert list(read_back.columns) == ["sample_index", "bending_mm", "torsion_mm"]
    assert read_back["sample_index"].tolist() == [0, 1, 2]
    np.testing.assert_allclose(read_back["bending_mm"], [0.1, 0.2, 0.3])
    np.testing.assert_allclose(read_back["torsion_mm"], [-0.1, -0.2, -0.3])


def test_write_all_timeseries_uses_condition_fixture_and_skips_missing_files(
    tmp_path,
) -> None:
    dataset_root = tmp_path / "dataset"
    dataset_root.mkdir()
    np.savetxt(dataset_root / "D0", np.array([[0.1, 0.2], [0.1, 0.2]]))
    data = np.array([[0.2, 0.4], [0.3, 0.1]])
    np.savetxt(dataset_root / "D1", data)
    rows = [
        ["file", "rpm", "u_meas", "u_calc", "note", "a", "b", "c", "d"],
        ["D1", 10, 1.0, 1.1, "condition", 0, 0, 0, 0],
        ["D2", 20, 2.0, 2.1, "missing file", 0, 0, 0, 0],
    ]
    pd.DataFrame(rows).to_excel(dataset_root / "Windspeed.xlsx", header=False, index=False)

    out_dir = tmp_path / "interim" / "condition-matched" / "timeseries"
    assert write_all_timeseries(dataset_root, out_dir) == 1

    read_back = pd.read_csv(out_dir / "D1.csv")
    expected_bending, expected_torsion = compute_condition_timeseries(data, np.array([0.1, 0.2]))
    assert read_back["sample_index"].tolist() == [0, 1]
    np.testing.assert_allclose(read_back["bending_mm"], expected_bending)
    np.testing.assert_allclose(read_back["torsion_mm"], expected_torsion)
    assert not (out_dir / "D2.csv").exists()
