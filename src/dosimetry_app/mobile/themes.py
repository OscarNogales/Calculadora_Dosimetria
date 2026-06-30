"""Theme definitions for the Flet interface."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AppTheme:
    name: str
    background: str
    card: str
    focused_input: str
    accent: str
    text: str
    result_background: str
    light_mode: bool = False


THEMES: dict[str, AppTheme] = {
    "Dark Apple": AppTheme(
        "Dark Apple", "#0A0A0A", "#141414", "#252525", "#FF9F0A", "#FFFFFF", "#1E1305"
    ),
    "Clinical Light": AppTheme(
        "Clinical Light", "#F5F5F7", "#FFFFFF", "#E8E8ED", "#0066CC", "#1D1D1F", "#E3F2FD", True
    ),
    "Cyberpunk": AppTheme(
        "Cyberpunk", "#000000", "#0D1117", "#161B22", "#39FF14", "#E6EDF3", "#001A00"
    ),
    "Nordic Frost": AppTheme(
        "Nordic Frost", "#1A1F2C", "#252D3D", "#343E54", "#86C1EE", "#ECEFF4", "#1F3547"
    ),
    "Retro Amber": AppTheme(
        "Retro Amber", "#110B00", "#1A1200", "#2D1F00", "#FFB000", "#FFCC66", "#3D2500"
    ),
    "Dracula": AppTheme(
        "Dracula", "#282A36", "#343746", "#44475A", "#FF79C6", "#F8F8F2", "#412234"
    ),
}

DEFAULT_THEME_NAME = "Dark Apple"
BORDER_RADIUS = 15
