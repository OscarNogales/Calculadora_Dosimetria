from __future__ import annotations

import json

import pytest

from dosimetry_app.calculator import DosimetryCalculator


def valid_values() -> dict[str, str]:
    return {
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


def test_calculator_updates_all_results(tmp_path) -> None:
    calculator = DosimetryCalculator(tmp_path / "state.json", autosave=False)
    calculator.update_values(valid_values())

    assert calculator.last_error is None
    assert calculator.get("k_tp") == "1.0000"
    assert calculator.get("P_Q") == "1.0000"
    assert calculator.get("Dosis_Referencia") == "0.5000"
    assert calculator.get("Dosis_Final") == "1.0000"


def test_calculator_accepts_decimal_comma(tmp_path) -> None:
    calculator = DosimetryCalculator(tmp_path / "state.json", autosave=False)
    values = valid_values()
    values["PDD"] = "50,0"
    calculator.update_values(values)
    assert calculator.get("Dosis_Final") == "1.0000"


def test_calculator_rejects_unknown_fields(tmp_path) -> None:
    calculator = DosimetryCalculator(tmp_path / "state.json", autosave=False)
    with pytest.raises(KeyError):
        calculator.update_value("not_a_field", "1")


def test_calculator_persists_only_input_values(tmp_path) -> None:
    state_path = tmp_path / "state.json"
    calculator = DosimetryCalculator(state_path)
    calculator.update_values(valid_values())

    saved = json.loads(state_path.read_text(encoding="utf-8"))
    assert "Dosis_Final" not in saved
    assert saved["M1"] == "10"

    restored = DosimetryCalculator(state_path, autosave=False)
    assert restored.get("Dosis_Final") == "1.0000"


def test_invalid_measurement_resets_results_and_exposes_error(tmp_path) -> None:
    calculator = DosimetryCalculator(tmp_path / "state.json", autosave=False)
    values = valid_values()
    values["P"] = "0"
    calculator.update_values(values)

    assert calculator.last_result is None
    assert calculator.last_error is not None
    assert calculator.get("Dosis_Final") == "0.0000"
