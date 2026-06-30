"""Reusable Flet controls for the Spanish mobile interface."""

from __future__ import annotations

from collections.abc import Callable, Sequence

import flet as ft

from dosimetry_app.calculator import DosimetryCalculator
from dosimetry_app.mobile.themes import BORDER_RADIUS, AppTheme

UpdateCallback = Callable[[], None]


class MeasurementInputRow(ft.Row):
    """A responsive row of numeric measurement fields."""

    def __init__(
        self,
        calculator: DosimetryCalculator,
        fields: Sequence[tuple[str, str]],
        on_values_changed: UpdateCallback,
        theme: AppTheme,
    ) -> None:
        self.calculator = calculator
        self.on_values_changed = on_values_changed
        controls = [self._build_field(key, label, theme) for key, label in fields]
        super().__init__(
            controls=controls,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            run_spacing=10,
            wrap=True,
        )

    def _build_field(self, key: str, label: str, theme: AppTheme) -> ft.TextField:
        saved_value = self.calculator.values[key]
        field = ft.TextField(
            label=label,
            value="" if saved_value == "0.0" else saved_value,
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor=theme.background,
            border=ft.InputBorder.NONE,
            filled=True,
            border_radius=10,
            color=theme.text,
            cursor_color=theme.accent,
            label_style=ft.TextStyle(color=ft.Colors.GREY_500),
            content_padding=ft.Padding.symmetric(vertical=14, horizontal=14),
        )

        def update_value(event: ft.Event[ft.TextField]) -> None:
            value = event.control.value or "0.0"
            self.calculator.update_value(key, value)
            self.on_values_changed()

        def focus(event: ft.Event[ft.TextField]) -> None:
            event.control.bgcolor = theme.focused_input
            event.control.update()

        def blur(event: ft.Event[ft.TextField]) -> None:
            event.control.bgcolor = theme.background
            event.control.update()

        field.on_change = update_value
        field.on_focus = focus
        field.on_blur = blur
        return field


class FactorValue(ft.Container):
    """Display one calculated correction factor."""

    def __init__(
        self,
        calculator: DosimetryCalculator,
        key: str,
        subscript: str,
        theme: AppTheme,
    ) -> None:
        self.calculator = calculator
        self.key = key
        self.value_text = ft.Text(
            self._formatted_value(),
            size=17,
            italic=True,
            color=theme.text,
        )
        label = ft.Row(
            [
                ft.Text("k", size=18, italic=True, color=theme.text),
                ft.Text(subscript, size=10, italic=True, color=theme.text),
                ft.Text(" = ", size=18, italic=True, color=theme.text),
                self.value_text,
            ],
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )
        super().__init__(content=label, bgcolor=theme.card, padding=8, border_radius=10)

    def _formatted_value(self) -> str:
        return "----" if self.calculator.last_result is None else self.calculator.get(self.key)

    def refresh(self) -> None:
        self.value_text.value = self._formatted_value()
        self.value_text.update()


class CalibrationSettingsButton(ft.IconButton):
    """Open a dialog for calibration constants."""

    FIELDS = (
        ("N_dw", "N D,w,Q0 (Gy/nC)"),
        ("k_elec", "k elec"),
        ("k_QQ0", "k Q,Q0"),
        ("T_ref", "Temperatura de referencia (°C)"),
        ("P_ref", "Presión de referencia (kPa)"),
    )

    def __init__(
        self,
        page: ft.Page,
        calculator: DosimetryCalculator,
        on_values_changed: UpdateCallback,
        theme: AppTheme,
    ) -> None:
        self.page = page
        self.calculator = calculator
        self.on_values_changed = on_values_changed
        controls = [self._build_field(key, label, theme) for key, label in self.FIELDS]
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Configuración de calibración", color=theme.accent),
            content=ft.Column(controls, spacing=12, tight=True, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Cerrar", on_click=self._close_dialog),
            ],
            bgcolor=theme.card,
            shape=ft.RoundedRectangleBorder(radius=BORDER_RADIUS),
        )
        super().__init__(
            icon=ft.Icons.SETTINGS_OUTLINED,
            icon_color=theme.accent,
            icon_size=28,
            tooltip="Configuración",
            on_click=self._open_dialog,
        )

    def _build_field(self, key: str, label: str, theme: AppTheme) -> ft.TextField:
        field = ft.TextField(
            label=label,
            value=self.calculator.values[key],
            keyboard_type=ft.KeyboardType.NUMBER,
            color=theme.text,
            bgcolor=theme.background,
            filled=True,
            border=ft.InputBorder.NONE,
            border_radius=8,
        )

        def update(event: ft.Event[ft.TextField]) -> None:
            self.calculator.update_value(key, event.control.value or "0.0")
            self.on_values_changed()

        field.on_change = update
        return field

    def _open_dialog(self, _event: ft.Event[ft.IconButton]) -> None:
        self.page.show_dialog(self.dialog)

    def _close_dialog(self, _event: ft.Event[ft.TextButton]) -> None:
        self.page.pop_dialog()


class DoseResultCard(ft.Container):
    """Display dose at zref and the optional PDD-corrected result."""

    def __init__(self, calculator: DosimetryCalculator, theme: AppTheme) -> None:
        self.calculator = calculator
        self.reference_text = ft.Text("----", size=13, color=ft.Colors.GREY_500)
        self.final_text = ft.Text("----", size=28, weight=ft.FontWeight.BOLD, color=theme.accent)
        self.error_text = ft.Text(
            "", size=11, color=ft.Colors.RED_400, text_align=ft.TextAlign.CENTER
        )
        content = ft.Column(
            [
                ft.Text("Dosis absorbida en agua", size=14, color=ft.Colors.GREY_500),
                self.final_text,
                self.reference_text,
                self.error_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=3,
        )
        super().__init__(
            content=content,
            bgcolor=theme.result_background,
            padding=24,
            border_radius=BORDER_RADIUS,
            border=ft.Border.all(2, theme.accent),
            width=380,
            alignment=ft.Alignment.CENTER,
        )
        self.refresh(initial=True)

    def refresh(self, *, initial: bool = False) -> None:
        result = self.calculator.last_result
        if result is None:
            self.final_text.value = "----"
            self.reference_text.value = "Completa las mediciones para calcular"
            self.error_text.value = self.calculator.last_error or ""
        else:
            self.final_text.value = f"{result.final_dose:.4f}"
            self.reference_text.value = f"D(zref): {result.dose_at_reference:.4f}"
            if result.dose_at_maximum is not None:
                self.reference_text.value += f"  ·  PDD: {result.normalized_pdd:.4f}"
            self.error_text.value = ""
        if not initial:
            self.final_text.update()
            self.reference_text.update()
            self.error_text.update()
