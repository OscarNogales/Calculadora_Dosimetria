"""Shared calculation and user-interface package for the dosimetry app."""

from .calculations import (
    DosimetryCalculationError,
    calculate_dosimetry,
    calculate_polarity_factor,
    calculate_recombination_factor,
    calculate_temperature_pressure_factor,
    normalize_pdd,
)
from .calculator import DosimetryCalculator
from .models import CalibrationConstants, DosimetryInputs, DosimetryResult

__all__ = [
    "CalibrationConstants",
    "DosimetryCalculationError",
    "DosimetryCalculator",
    "DosimetryInputs",
    "DosimetryResult",
    "calculate_dosimetry",
    "calculate_polarity_factor",
    "calculate_recombination_factor",
    "calculate_temperature_pressure_factor",
    "normalize_pdd",
]
