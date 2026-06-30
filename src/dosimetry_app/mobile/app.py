"""Flet entry point for Android, desktop, and web builds."""

from __future__ import annotations

import flet as ft

from dosimetry_app.calculator import DosimetryCalculator
from dosimetry_app.mobile.components import (
    CalibrationSettingsButton,
    DoseResultCard,
    FactorValue,
    MeasurementInputRow,
)
from dosimetry_app.mobile.themes import (
    BORDER_RADIUS,
    DEFAULT_THEME_NAME,
    THEMES,
)
from dosimetry_app.settings import SettingsRepository


def main(page: ft.Page) -> None:
    calculator = DosimetryCalculator()
    settings_repository = SettingsRepository()
    settings = settings_repository.load()
    theme_name = settings.get("theme", DEFAULT_THEME_NAME)
    if theme_name not in THEMES:
        theme_name = DEFAULT_THEME_NAME

    page.title = "Calculadora de Dosimetría"
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.padding = 15

    def render() -> None:
        theme = THEMES[settings["theme"]]
        page.clean()
        page.bgcolor = theme.background
        page.theme_mode = ft.ThemeMode.LIGHT if theme.light_mode else ft.ThemeMode.DARK

        factors = [
            FactorValue(calculator, "k_tp", "tp", theme),
            FactorValue(calculator, "k_pol", "pol", theme),
            FactorValue(calculator, "k_s", "s", theme),
            FactorValue(calculator, "P_Q", "Q", theme),
        ]
        result_card = DoseResultCard(calculator, theme)

        def refresh_results() -> None:
            for factor in factors:
                factor.refresh()
            result_card.refresh()

        settings_button = CalibrationSettingsButton(page, calculator, refresh_results, theme)

        def change_theme(event: ft.Event[ft.Dropdown]) -> None:
            selected = event.control.value or DEFAULT_THEME_NAME
            settings["theme"] = selected if selected in THEMES else DEFAULT_THEME_NAME
            settings_repository.save(settings)
            render()

        theme_selector = ft.Dropdown(
            options=[ft.DropdownOption(key=name, text=name) for name in THEMES],
            value=theme.name,
            width=155,
            text_size=12,
            on_select=change_theme,
            color=theme.text,
            bgcolor=theme.focused_input,
            border_color=theme.accent,
            content_padding=ft.Padding.only(left=10, right=10),
        )

        page.appbar = ft.AppBar(
            title=ft.Text("Dosimetría", size=22, weight=ft.FontWeight.BOLD, color=theme.text),
            bgcolor=theme.background,
            elevation=0,
            force_material_transparency=True,
            actions=[theme_selector, settings_button, ft.Container(width=8)],
        )

        measurements_card = ft.Container(
            content=ft.Column(
                [
                    MeasurementInputRow(
                        calculator,
                        (("T", "Temperatura (°C)"), ("P", "Presión (kPa)")),
                        refresh_results,
                        theme,
                    ),
                    MeasurementInputRow(
                        calculator,
                        (
                            ("M1", "M− (nC)"),
                            ("M+", "M+ (nC)"),
                            ("M2", "M 100 V (nC)"),
                        ),
                        refresh_results,
                        theme,
                    ),
                    MeasurementInputRow(
                        calculator,
                        (("PDD", "PDD (0.67 o 67)"),),
                        refresh_results,
                        theme,
                    ),
                ],
                spacing=15,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=theme.card,
            padding=20,
            border_radius=BORDER_RADIUS,
            width=380,
        )

        factors_tile = ft.ExpansionTile(
            title=ft.Text("Factores de corrección", color=theme.text, weight=ft.FontWeight.BOLD),
            subtitle=ft.Text("Toca para ver los valores", color=ft.Colors.GREY_500, size=12),
            controls=[
                ft.Container(
                    content=ft.Row(
                        factors,
                        wrap=True,
                        spacing=10,
                        run_spacing=10,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    padding=15,
                )
            ],
            text_color=theme.accent,
            collapsed_text_color=theme.text,
            icon_color=theme.accent,
            shape=ft.RoundedRectangleBorder(radius=BORDER_RADIUS),
            collapsed_shape=ft.RoundedRectangleBorder(radius=BORDER_RADIUS),
        )
        factors_card = ft.Container(
            content=factors_tile,
            bgcolor=theme.card,
            border_radius=BORDER_RADIUS,
            width=380,
        )

        scroll_area = ft.Column(
            [measurements_card, factors_card, ft.Container(height=24)],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
        )
        page.add(scroll_area, result_card, ft.Container(height=24))
        page.update()

    settings["theme"] = theme_name
    render()


def run() -> None:
    ft.run(main)


if __name__ == "__main__":
    run()
