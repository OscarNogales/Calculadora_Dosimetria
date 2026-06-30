"""Application settings shared by the mobile and desktop interfaces."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from .storage import JsonStore, user_data_directory

DEFAULT_SETTINGS: dict[str, Any] = {
    "theme": "Dark Apple",
    "equipment": {
        "brand": "Varian",
        "model": "Clinac iX",
        "serial_number": "",
        "beam": "Fotones",
        "energy": "6 MV",
        "dose_rate": "600",
        "setup": "SSD",
        "phantom": "Agua",
        "distance_cm": "100.0",
        "field_size_cm": "10 x 10",
        "reference_depth": "10.0",
    },
    "measurement_equipment": {
        "electrometer": "PTW",
        "electrometer_model": "Unidos Webline",
        "electrometer_serial": "",
        "measurement_mode": "Carga (nC)",
        "measurement_range": "Low",
        "ion_chamber": "PTW 30013",
        "ion_chamber_serial": "",
    },
}

LEGACY_TOP_LEVEL_KEYS = {
    "tema_usuario": ("theme",),
    "marca": ("equipment", "brand"),
    "modelo": ("equipment", "model"),
    "serie": ("equipment", "serial_number"),
    "haz": ("equipment", "beam"),
    "energia": ("equipment", "energy"),
    "tasa": ("equipment", "dose_rate"),
    "setup": ("equipment", "setup"),
    "campo": ("equipment", "field_size_cm"),
    "zref": ("equipment", "reference_depth"),
    "camara": ("measurement_equipment", "ion_chamber"),
    "serie_camara": ("measurement_equipment", "ion_chamber_serial"),
    "electrometro": ("measurement_equipment", "electrometer"),
}


def _deep_merge(base: dict[str, Any], updates: Mapping[str, Any]) -> dict[str, Any]:
    for key, value in updates.items():
        if isinstance(value, Mapping) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def _migrate_legacy(data: Mapping[str, Any]) -> dict[str, Any]:
    migrated = {
        key: deepcopy(value) for key, value in data.items() if key not in LEGACY_TOP_LEVEL_KEYS
    }
    for legacy_key, path in LEGACY_TOP_LEVEL_KEYS.items():
        if legacy_key not in data:
            continue
        cursor = migrated
        for part in path[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[path[-1]] = data[legacy_key]
    return migrated


class SettingsRepository:
    def __init__(self, path: str | Path | None = None):
        settings_path = Path(path) if path else user_data_directory() / "settings.json"
        self.store = JsonStore(settings_path)

    def load(self) -> dict[str, Any]:
        return _deep_merge(deepcopy(DEFAULT_SETTINGS), _migrate_legacy(self.store.load()))

    def save(self, settings: Mapping[str, Any]) -> None:
        merged = _deep_merge(deepcopy(DEFAULT_SETTINGS), settings)
        self.store.save(merged)
