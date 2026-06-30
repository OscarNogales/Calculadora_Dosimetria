"""Convert application state into the PDF report schema."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from dosimetry_app.calculator import DosimetryCalculator


def average_readings(readings: Sequence[str], fallback: float) -> tuple[list[float], float]:
    """Return three parsed readings and their mean, or a repeated fallback."""

    cleaned = [value.strip().replace(",", ".") for value in readings]
    if len(cleaned) != 3 or any(not value for value in cleaned):
        values = [fallback, fallback, fallback]
        return values, fallback
    try:
        values = [float(value) for value in cleaned]
    except ValueError:
        values = [fallback, fallback, fallback]
        return values, fallback
    return values, sum(values) / len(values)


def build_report_data(
    calculator: DosimetryCalculator,
    settings: Mapping[str, Any],
    official_readings: Sequence[str],
) -> dict[str, str]:
    """Build the legacy report dictionary from validated application state."""

    result = calculator.last_result
    if result is None:
        raise ValueError(calculator.last_error or "No hay un cálculo válido para reportar.")

    equipment = settings.get("equipment", {})
    measurement_equipment = settings.get("measurement_equipment", {})
    fallback = abs(float(calculator.values["M1"].replace(",", ".")))
    readings, average = average_readings(official_readings, fallback)

    n_dw = float(calculator.values["N_dw"].replace(",", "."))
    k_qq0 = float(calculator.values["k_QQ0"].replace(",", "."))
    dose_at_reference = abs(average) * result.p_q * n_dw * k_qq0
    dose_at_maximum = (
        dose_at_reference / result.normalized_pdd
        if result.normalized_pdd is not None
        else dose_at_reference
    )

    return {
        "marca_equipo": str(equipment.get("brand", "")),
        "modelo_equipo": str(equipment.get("model", "")),
        "serie_equipo": str(equipment.get("serial_number", "")),
        "haz_calibrar": str(equipment.get("beam", "")),
        "energia_calibrar": str(equipment.get("energy", "")),
        "tasa_dosis": str(equipment.get("dose_rate", "")),
        "setup": str(equipment.get("setup", "SSD")),
        "fantoma": str(equipment.get("phantom", "Agua")),
        "distancia_cm": str(equipment.get("distance_cm", "100.0")),
        "campo_cm": str(equipment.get("field_size_cm", "10 x 10")),
        "zref": str(equipment.get("reference_depth", "10.0")),
        "electrometro": str(measurement_equipment.get("electrometer", "")),
        "marca_serie_elec": str(measurement_equipment.get("electrometer_model", "")),
        "modo_medicion": str(measurement_equipment.get("measurement_mode", "")),
        "rango_medicion": str(measurement_equipment.get("measurement_range", "")),
        "camara": str(measurement_equipment.get("ion_chamber", "")),
        "serie_camara": str(measurement_equipment.get("ion_chamber_serial", "")),
        "tipo_radiacion": "FOTONES"
        if str(equipment.get("beam", "")).lower().startswith("fot")
        else "ELECTRONES",
        "factor_calibracion": calculator.values["N_dw"],
        "k_elec": calculator.values["k_elec"],
        "p0": calculator.values["P_ref"],
        "t0": calculator.values["T_ref"],
        "k_qq0": calculator.values["k_QQ0"],
        "presion": calculator.values["P"],
        "temperatura": calculator.values["T"],
        "k_tp": f"{result.k_tp:.4f}",
        "k_pol": f"{result.k_pol:.4f}",
        "k_s": f"{result.k_s:.4f}",
        "p_q": f"{result.p_q:.4f}",
        "m_plus": calculator.values["M+"],
        "m2": calculator.values["M2"],
        "m1": calculator.values["M1"],
        "l1": f"{readings[0]:.3f}",
        "l2": f"{readings[1]:.3f}",
        "l3": f"{readings[2]:.3f}",
        "prom": f"{average:.3f}",
        "dw_q_zref": f"{dose_at_reference:.4f}",
        "dw_q_zmax": f"{dose_at_maximum:.4f}",
        "zmax_sec4": "",
        "pdd20": "",
        "pdd10": calculator.values["PDD"],
        "pdd20_10": "",
        "tpr20_10": "",
        "zmax_sec7": "",
        "pdd_zref": calculator.values["PDD"],
    }
