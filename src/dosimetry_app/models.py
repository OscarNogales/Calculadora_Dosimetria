"""Typed domain models used by every interface."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DosimetryInputs:
    """Measurements collected during the calibration workflow.

    ``pdd`` may be written as a fraction (0.67) or as a percentage (67).
    It is optional because the desktop workflow also reports dose at zref.
    """

    temperature_c: float
    pressure_kpa: float
    reference_reading_nc: float
    opposite_polarity_reading_nc: float
    recombination_reading_nc: float
    pdd: float | None = None


@dataclass(frozen=True, slots=True)
class CalibrationConstants:
    """Calibration constants and environmental reference conditions."""

    n_dw_gy_per_nc: float = 0.0532
    k_qq0: float = 0.991
    reference_temperature_c: float = 20.0
    reference_pressure_kpa: float = 101.33
    k_elec: float = 1.0


@dataclass(frozen=True, slots=True)
class DosimetryResult:
    """Calculated correction factors and absorbed-dose estimates."""

    k_tp: float
    k_pol: float
    k_s: float
    p_q: float
    dose_at_reference: float
    dose_at_maximum: float | None
    normalized_pdd: float | None

    @property
    def final_dose(self) -> float:
        """Return the PDD-corrected dose when available, otherwise zref dose."""

        return self.dose_at_maximum or self.dose_at_reference
