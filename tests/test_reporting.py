from __future__ import annotations

from pathlib import Path

import pytest

from dosimetry_app.calculator import DosimetryCalculator
from dosimetry_app.reporting import (
    average_readings,
    build_report_data,
    generate_calibration_report,
)
from dosimetry_app.settings import DEFAULT_SETTINGS


def make_calculator(tmp_path: Path) -> DosimetryCalculator:
    calculator = DosimetryCalculator(tmp_path / "state.json", autosave=False)
    calculator.update_values(
        {
            "T": "20",
            "P": "101.33",
            "M1": "10",
            "M+": "10",
            "M2": "10",
            "PDD": "50",
            "N_dw": "0.05",
            "k_QQ0": "1",
            "T_ref": "20",
            "P_ref": "101.33",
            "k_elec": "1",
        }
    )
    return calculator


def test_average_readings_uses_all_three_values() -> None:
    values, average = average_readings(["9", "10", "11"], fallback=5)
    assert values == [9.0, 10.0, 11.0]
    assert average == pytest.approx(10.0)


def test_average_readings_falls_back_when_incomplete() -> None:
    values, average = average_readings(["", "10", "11"], fallback=7)
    assert values == [7, 7, 7]
    assert average == 7


def test_report_data_uses_official_average_for_dose(tmp_path) -> None:
    data = build_report_data(
        make_calculator(tmp_path),
        DEFAULT_SETTINGS,
        ["9", "10", "11"],
    )
    assert data["prom"] == "10.000"
    assert data["dw_q_zref"] == "0.5000"
    assert data["dw_q_zmax"] == "1.0000"


def test_pdf_report_generation(tmp_path) -> None:
    data = build_report_data(
        make_calculator(tmp_path),
        DEFAULT_SETTINGS,
        ["9", "10", "11"],
    )
    output = generate_calibration_report(data, tmp_path / "report.pdf")

    assert output.exists()
    assert output.read_bytes().startswith(b"%PDF")
    assert output.stat().st_size > 1_000
