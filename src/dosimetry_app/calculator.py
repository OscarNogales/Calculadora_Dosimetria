"""Stateful adapter used by the graphical interfaces."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .calculations import DosimetryCalculationError, calculate_dosimetry
from .models import CalibrationConstants, DosimetryInputs, DosimetryResult
from .storage import JsonStore, user_data_directory

DEFAULT_VALUES: dict[str, str] = {
    "T": "0.0",
    "P": "0.0",
    "M1": "0.0",
    "M+": "0.0",
    "M2": "0.0",
    "PDD": "0.0",
    "N_dw": "0.0532",
    "k_QQ0": "0.991",
    "T_ref": "20.0",
    "P_ref": "101.33",
    "k_elec": "1.0",
    "k_tp": "0.0",
    "k_pol": "0.0",
    "k_s": "0.0",
    "P_Q": "0.0",
    "Dosis_Referencia": "0.0",
    "Dosis_Final": "0.0",
}

INPUT_KEYS = frozenset(
    {"T", "P", "M1", "M+", "M2", "PDD", "N_dw", "k_QQ0", "T_ref", "P_ref", "k_elec"}
)
COMPUTED_KEYS = frozenset(DEFAULT_VALUES) - INPUT_KEYS


class DosimetryCalculator:
    """Maintain UI state while delegating all formulas to pure functions."""

    def __init__(self, state_path: str | Path | None = None, *, autosave: bool = True):
        path = Path(state_path) if state_path else user_data_directory() / "state.json"
        self.store = JsonStore(path)
        self.autosave = autosave
        self.values = DEFAULT_VALUES.copy()
        self.last_error: str | None = None
        self.last_result: DosimetryResult | None = None
        self.load(self.store.load())

    @property
    def datos(self) -> dict[str, str]:
        """Compatibility alias for the original Spanish UI code."""

        return self.values

    def load(self, values: Mapping[str, object]) -> None:
        for key in INPUT_KEYS:
            if key in values:
                self.values[key] = str(values[key])
        self.recalculate(save=False)

    def snapshot(self) -> dict[str, str]:
        return {key: self.values[key] for key in INPUT_KEYS}

    def save(self) -> None:
        self.store.save(self.snapshot())

    def update_value(self, key: str, val: str | float) -> None:
        if key not in INPUT_KEYS:
            raise KeyError(f"Campo desconocido: {key}")
        self.values[key] = str(val).strip() or "0.0"
        self.recalculate(save=self.autosave)

    def update_values(self, values: Mapping[str, str | float]) -> None:
        unknown = set(values) - INPUT_KEYS
        if unknown:
            raise KeyError(f"Campos desconocidos: {', '.join(sorted(unknown))}")
        for key, value in values.items():
            self.values[key] = str(value).strip() or "0.0"
        self.recalculate(save=self.autosave)

    def recalculate(self, *, save: bool = False) -> DosimetryResult | None:
        try:
            measurements = DosimetryInputs(
                temperature_c=self._float("T"),
                pressure_kpa=self._float("P"),
                reference_reading_nc=self._float("M1"),
                opposite_polarity_reading_nc=self._float("M+"),
                recombination_reading_nc=self._float("M2"),
                pdd=self._optional_pdd(),
            )
            constants = CalibrationConstants(
                n_dw_gy_per_nc=self._float("N_dw"),
                k_qq0=self._float("k_QQ0"),
                reference_temperature_c=self._float("T_ref"),
                reference_pressure_kpa=self._float("P_ref"),
                k_elec=self._float("k_elec"),
            )
            result = calculate_dosimetry(measurements, constants)
        except (ValueError, DosimetryCalculationError) as error:
            self.last_error = str(error)
            self.last_result = None
            for key in COMPUTED_KEYS:
                self.values[key] = "0.0"
        else:
            self.last_error = None
            self.last_result = result
            self.values.update(
                {
                    "k_tp": str(result.k_tp),
                    "k_pol": str(result.k_pol),
                    "k_s": str(result.k_s),
                    "P_Q": str(result.p_q),
                    "Dosis_Referencia": str(result.dose_at_reference),
                    "Dosis_Final": str(result.final_dose),
                }
            )
        if save:
            self.save()
        return self.last_result

    def get(self, key: str, decimals: int = 4) -> str:
        if key not in self.values:
            raise KeyError(f"Campo desconocido: {key}")
        try:
            return f"{float(self.values[key]):.{decimals}f}"
        except ValueError:
            return self.values[key]

    def _float(self, key: str) -> float:
        raw_value = self.values[key].strip().replace(",", ".")
        if not raw_value:
            raise DosimetryCalculationError(f"El campo {key} está vacío.")
        try:
            return float(raw_value)
        except ValueError as error:
            raise DosimetryCalculationError(
                f"El campo {key} debe contener un número válido."
            ) from error

    def _optional_pdd(self) -> float | None:
        pdd = self._float("PDD")
        return None if pdd == 0 else pdd
