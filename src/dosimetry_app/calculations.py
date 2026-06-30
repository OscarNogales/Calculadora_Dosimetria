"""Pure, testable dosimetry calculations.

The functions in this module do not read files and do not know anything about
Flet or CustomTkinter. This makes the scientific logic reusable and testable.
"""

from __future__ import annotations

import math

from .models import CalibrationConstants, DosimetryInputs, DosimetryResult

RECOMBINATION_COEFFICIENTS = (2.337, -3.636, 2.299)
ABSOLUTE_ZERO_C = -273.15


class DosimetryCalculationError(ValueError):
    """Raised when a measurement cannot produce a valid calculation."""


def _require_finite(name: str, value: float) -> float:
    if not math.isfinite(value):
        raise DosimetryCalculationError(f"{name} debe ser un número finito.")
    return value


def calculate_temperature_pressure_factor(
    temperature_c: float,
    pressure_kpa: float,
    reference_temperature_c: float = 20.0,
    reference_pressure_kpa: float = 101.33,
) -> float:
    """Calculate the temperature-pressure correction factor ``k_tp``."""

    temperature_c = _require_finite("La temperatura", temperature_c)
    pressure_kpa = _require_finite("La presión", pressure_kpa)
    reference_temperature_c = _require_finite(
        "La temperatura de referencia", reference_temperature_c
    )
    reference_pressure_kpa = _require_finite("La presión de referencia", reference_pressure_kpa)

    if temperature_c <= ABSOLUTE_ZERO_C:
        raise DosimetryCalculationError("La temperatura debe ser mayor que el cero absoluto.")
    if reference_temperature_c <= ABSOLUTE_ZERO_C:
        raise DosimetryCalculationError(
            "La temperatura de referencia debe ser mayor que el cero absoluto."
        )
    if pressure_kpa <= 0:
        raise DosimetryCalculationError("La presión debe ser mayor que cero.")
    if reference_pressure_kpa <= 0:
        raise DosimetryCalculationError("La presión de referencia debe ser mayor que cero.")

    return (
        (temperature_c + 273.15)
        / (reference_temperature_c + 273.15)
        * (reference_pressure_kpa / pressure_kpa)
    )


def calculate_polarity_factor(
    reference_reading_nc: float,
    opposite_polarity_reading_nc: float,
) -> float:
    """Calculate the polarity correction factor ``k_pol``."""

    reference_reading_nc = _require_finite("La lectura de referencia", reference_reading_nc)
    opposite_polarity_reading_nc = _require_finite(
        "La lectura de polaridad opuesta", opposite_polarity_reading_nc
    )
    if reference_reading_nc == 0:
        raise DosimetryCalculationError(
            "La lectura de referencia no puede ser cero para calcular k_pol."
        )

    return (abs(reference_reading_nc) + abs(opposite_polarity_reading_nc)) / (
        2 * abs(reference_reading_nc)
    )


def calculate_recombination_factor(
    reference_reading_nc: float,
    recombination_reading_nc: float,
    coefficients: tuple[float, float, float] = RECOMBINATION_COEFFICIENTS,
) -> float:
    """Calculate the ion-recombination correction factor ``k_s``."""

    reference_reading_nc = _require_finite("La lectura de referencia", reference_reading_nc)
    recombination_reading_nc = _require_finite(
        "La lectura de recombinación", recombination_reading_nc
    )
    if recombination_reading_nc == 0:
        raise DosimetryCalculationError(
            "La lectura de recombinación no puede ser cero para calcular k_s."
        )

    a0, a1, a2 = coefficients
    ratio = reference_reading_nc / recombination_reading_nc
    return a0 + a1 * ratio + a2 * ratio**2


def normalize_pdd(pdd: float) -> float:
    """Convert PDD written as a fraction or percentage to a 0-1 fraction."""

    pdd = _require_finite("El PDD", pdd)
    if pdd <= 0:
        raise DosimetryCalculationError("El PDD debe ser mayor que cero.")
    if pdd <= 1:
        return pdd
    if pdd <= 100:
        return pdd / 100
    raise DosimetryCalculationError(
        "El PDD debe escribirse como fracción (0.67) o porcentaje (67)."
    )


def calculate_dosimetry(
    measurements: DosimetryInputs,
    constants: CalibrationConstants,
    *,
    use_reading_magnitude: bool = True,
) -> DosimetryResult:
    """Calculate correction factors and dose values.

    ``use_reading_magnitude`` defaults to ``True`` because the app accepts
    electrometer readings from either polarity while absorbed dose is reported
    as a positive magnitude. Set it to ``False`` only for explicit signed-value
    investigations.
    """

    k_tp = calculate_temperature_pressure_factor(
        measurements.temperature_c,
        measurements.pressure_kpa,
        constants.reference_temperature_c,
        constants.reference_pressure_kpa,
    )
    k_pol = calculate_polarity_factor(
        measurements.reference_reading_nc,
        measurements.opposite_polarity_reading_nc,
    )
    k_s = calculate_recombination_factor(
        measurements.reference_reading_nc,
        measurements.recombination_reading_nc,
    )

    for name, value in (
        ("N_D,w", constants.n_dw_gy_per_nc),
        ("k_Q,Q0", constants.k_qq0),
        ("k_elec", constants.k_elec),
    ):
        _require_finite(name, value)
        if value <= 0:
            raise DosimetryCalculationError(f"{name} debe ser mayor que cero.")

    p_q = k_tp * k_pol * k_s * constants.k_elec
    reading = (
        abs(measurements.reference_reading_nc)
        if use_reading_magnitude
        else measurements.reference_reading_nc
    )
    dose_at_reference = reading * p_q * constants.n_dw_gy_per_nc * constants.k_qq0

    normalized_pdd: float | None = None
    dose_at_maximum: float | None = None
    if measurements.pdd is not None:
        normalized_pdd = normalize_pdd(measurements.pdd)
        dose_at_maximum = dose_at_reference / normalized_pdd

    return DosimetryResult(
        k_tp=k_tp,
        k_pol=k_pol,
        k_s=k_s,
        p_q=p_q,
        dose_at_reference=dose_at_reference,
        dose_at_maximum=dose_at_maximum,
        normalized_pdd=normalized_pdd,
    )
