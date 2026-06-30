from __future__ import annotations

import json

from dosimetry_app.settings import SettingsRepository
from dosimetry_app.storage import JsonStore


def test_json_store_round_trip(tmp_path) -> None:
    store = JsonStore(tmp_path / "nested" / "data.json")
    store.save({"value": 3, "name": "dosimetría"})
    assert store.load() == {"value": 3, "name": "dosimetría"}


def test_json_store_returns_empty_dictionary_for_corrupt_file(tmp_path) -> None:
    path = tmp_path / "data.json"
    path.write_text("not-json", encoding="utf-8")
    assert JsonStore(path).load() == {}


def test_settings_repository_migrates_legacy_keys(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps(
            {
                "tema_usuario": "Cyberpunk",
                "marca": "Test Brand",
                "modelo": "Test Model",
                "camara": "Test Chamber",
            }
        ),
        encoding="utf-8",
    )

    settings = SettingsRepository(path).load()
    assert settings["theme"] == "Cyberpunk"
    assert settings["equipment"]["brand"] == "Test Brand"
    assert settings["equipment"]["model"] == "Test Model"
    assert settings["measurement_equipment"]["ion_chamber"] == "Test Chamber"
