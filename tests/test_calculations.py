from __future__ import annotations

import math

import pytest

from dosimetry_app.calculations import (
    DosimetryCalculationError,
    calculate_dosimetry,
    calculate_polarity_factor,
    calculate_recombination_factor,
    calculate_temperature_pressure_factor,
    normalize_pdd,
)
from dosimetry_app.models import CalibrationConstants, DosimetryInputs


def test_temperature_pressure_factor_is_one_at_reference_conditions() -> None:
    assert calculate_temperature_pressure_factor(20.0, 101.33) == pytest.approx(1.0)


def test_temperature_pressure_factor_rejects_zero_pressure() -> None:
    with pytest.raises(DosimetryCalculationError, match="presión"):
        calculate_temperature_pressure_factor(20.0, 0.0)


def test_polarity_factor_uses_reading_magnitudes() -> None:
    assert calculate_polarity_factor(-10.0, 9.8) == pytest.approx(0.99)


def test_polarity_factor_rejects_zero_reference_reading() -> None:
    with pytest.raises(DosimetryCalculationError, match="referencia"):
        calculate_polarity_factor(0.0, 10.0)


def test_recombination_factor_is_one_when_readings_match() -> None:
    assert calculate_recombination_factor(10.0, 10.0) == pytest.approx(1.0)


def test_recombination_factor_rejects_zero_second_reading() -> None:
    with pytest.raises(DosimetryCalculationError, match="recombinación"):
        calculate_recombination_factor(10.0, 0.0)


@pytest.mark.parametrize(
    ("raw", "expected"), [(0.67, 0.67), (67.0, 0.67), (1.0, 1.0), (100.0, 1.0)]
)
def test_pdd_accepts_fraction_or_percentage(raw: float, expected: float) -> None:
    assert normalize_pdd(raw) == pytest.approx(expected)


@pytest.mark.parametrize("raw", [0.0, -1.0, 100.1, math.inf, math.nan])
def test_pdd_rejects_invalid_values(raw: float) -> None:
    with pytest.raises(DosimetryCalculationError):
        normalize_pdd(raw)


def test_full_calculation_returns_reference_and_pdd_corrected_dose() -> None:
    result = calculate_dosimetry(
        DosimetryInputs(20.0, 101.33, 10.0, 10.0, 10.0, pdd=50.0),
        CalibrationConstants(n_dw_gy_per_nc=0.05, k_qq0=1.0, k_elec=1.0),
    )

    assert result.k_tp == pytest.approx(1.0)
    assert result.k_pol == pytest.approx(1.0)
    assert result.k_s == pytest.approx(1.0)
    assert result.p_q == pytest.approx(1.0)
    assert result.dose_at_reference == pytest.approx(0.5)
    assert result.dose_at_maximum == pytest.approx(1.0)
    assert result.final_dose == pytest.approx(1.0)


def test_negative_reference_reading_produces_positive_reported_dose() -> None:
    result = calculate_dosimetry(
        DosimetryInputs(20.0, 101.33, -10.0, 10.0, -10.0),
        CalibrationConstants(n_dw_gy_per_nc=0.05, k_qq0=1.0),
    )
    assert result.dose_at_reference == pytest.approx(0.5)
