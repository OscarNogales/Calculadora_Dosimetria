"""Interfaz de escritorio de la calculadora de dosimetría.

Esta interfaz conserva el flujo de cálculo y reporte del proyecto refactorizado,
pero presenta todos los campos necesarios en un diseño de escritorio amplio,
ordenado y desplazable.
"""

from __future__ import annotations

from tkinter import filedialog, messagebox
from typing import Any, Callable

import customtkinter as ctk

from dosimetry_app.calculator import DosimetryCalculator
from dosimetry_app.reporting import build_report_data, generate_calibration_report
from dosimetry_app.settings import SettingsRepository


class DosimetryDesktopApp:
    """Aplicación de escritorio basada en CustomTkinter."""

    # Paleta
    BLUE = "#1976D2"
    BLUE_HOVER = "#155FA8"
    BLUE_SOFT = ("#EAF3FC", "#18324A")
    NAVY = ("#123B5D", "#D9ECFF")
    CARD = ("#FFFFFF", "#20252B")
    PAGE = ("#F3F6F9", "#111418")
    BORDER = ("#D9E1E8", "#343B43")
    TEXT = ("#17212B", "#F2F5F7")
    MUTED = ("#65717C", "#A9B2BA")
    SUCCESS = "#2E9D52"
    SUCCESS_HOVER = "#247E42"
    WARNING = "#C77C16"
    DANGER = "#C84444"

    MEASUREMENT_KEYS = ("T", "P", "PDD", "M1", "M+", "M2")
    CALIBRATION_KEYS = ("N_dw", "k_elec", "k_QQ0", "P_ref", "T_ref")

    FACTOR_FIELDS = (
        ("k_tp", "kTP", "Presión y temperatura"),
        ("k_pol", "kpol", "Polaridad"),
        ("k_s", "ks", "Recombinación iónica"),
        ("k_elec", "kelec", "Electrómetro"),
        ("k_QQ0", "kQ,Q0", "Calidad del haz"),
        ("P_Q", "PQ", "Producto de correcciones"),
    )

    def __init__(self) -> None:
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.calculator = DosimetryCalculator()
        self.settings_repository = SettingsRepository()
        self.settings = self.settings_repository.load()

        # Garantiza que las secciones existan aunque se use un archivo antiguo.
        self.settings.setdefault("equipment", {})
        self.settings.setdefault("measurement_equipment", {})
        self.settings.setdefault("report", {})
        self.settings.setdefault("calibration", {})

        saved_calibration = {
            key: str(value)
            for key, value in self.settings["calibration"].items()
            if key in self.CALIBRATION_KEYS and str(value).strip()
        }
        if saved_calibration:
            self.calculator.update_values(saved_calibration)

        self.root = ctk.CTk()
        self.root.title("Dosis LINAC · Calculadora de dosimetría")
        self.root.geometry("1180x820")
        self.root.minsize(980, 700)
        self.root.configure(fg_color=self.PAGE)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

        self.calculator_vars: dict[str, ctk.StringVar] = {}
        for key in (*self.MEASUREMENT_KEYS, *self.CALIBRATION_KEYS):
            value = str(self.calculator.values.get(key, ""))
            if key in self.MEASUREMENT_KEYS and value in {"0", "0.0", "0.00"}:
                value = ""
            self.calculator_vars[key] = ctk.StringVar(value=value)

        self.factor_vars = {
            key: ctk.StringVar(value="—") for key, _symbol, _description in self.FACTOR_FIELDS
        }
        self.reference_dose_var = ctk.StringVar(value="—")
        self.maximum_dose_var = ctk.StringVar(value="—")
        self.status_var = ctk.StringVar(
            value="Ingresa las lecturas del electrómetro para comenzar."
        )

        self.equipment_vars: dict[tuple[str, str], ctk.StringVar] = {}
        saved_readings = self.settings["report"].get("official_readings", ["", "", ""])
        if not isinstance(saved_readings, list) or len(saved_readings) != 3:
            saved_readings = ["", "", ""]
        self.official_readings = [
            ctk.StringVar(value=str(value)) for value in saved_readings
        ]

        self.report_vars = {
            key: ctk.StringVar(value=str(self.settings["report"].get(key, "")))
            for key in (
                "zmax_sec4",
                "pdd20",
                "pdd10",
                "pdd20_10",
                "tpr20_10",
                "zmax_sec7",
            )
        }

        self.status_label: ctk.CTkLabel | None = None
        self.theme_switch: ctk.CTkSwitch | None = None

        self._build_ui()

        # Los traces se agregan al final para evitar cálculos parciales
        # mientras se construyen los controles.
        for variable in self.calculator_vars.values():
            variable.trace_add("write", self._on_calculation_change)

        self._refresh_results(initial=True)

    # ------------------------------------------------------------------
    # Construcción general
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        self._build_header()

        tabs = ctk.CTkTabview(
            self.root,
            corner_radius=18,
            border_width=1,
            border_color=self.BORDER,
            fg_color=self.PAGE,
            segmented_button_selected_color=self.BLUE,
            segmented_button_selected_hover_color=self.BLUE_HOVER,
            segmented_button_unselected_color=("#CBD3DA", "#3B434B"),
            segmented_button_unselected_hover_color=("#B8C2CA", "#4A535C"),
            text_color=self.TEXT,
        )
        tabs.grid(row=1, column=0, padx=24, pady=(0, 24), sticky="nsew")

        measurements_tab = tabs.add("Mediciones y resultados")
        calibration_tab = tabs.add("Calibración")
        equipment_tab = tabs.add("Equipo y reporte")

        self._build_measurements_tab(measurements_tab)
        self._build_calibration_tab(calibration_tab)
        self._build_equipment_tab(equipment_tab)

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self.root, fg_color="transparent")
        header.grid(row=0, column=0, padx=28, pady=(22, 14), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_group = ctk.CTkFrame(header, fg_color="transparent")
        title_group.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            title_group,
            text="Dosis LINAC",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.NAVY,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            title_group,
            text="Cálculo de dosis absoluta y generación de reporte",
            font=ctk.CTkFont(size=13),
            text_color=self.MUTED,
        ).grid(row=1, column=0, pady=(2, 0), sticky="w")

        self.theme_switch = ctk.CTkSwitch(
            header,
            text="Modo oscuro",
            command=self._toggle_theme,
            progress_color=self.BLUE,
            button_color=self.BLUE,
            button_hover_color=self.BLUE_HOVER,
        )
        self.theme_switch.grid(row=0, column=1, rowspan=2, padx=(16, 0), sticky="e")

    # ------------------------------------------------------------------
    # Pestaña de mediciones
    # ------------------------------------------------------------------
    def _build_measurements_tab(self, parent: ctk.CTkFrame) -> None:
        page = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=("#AEB8C1", "#4B545D"),
            scrollbar_button_hover_color=("#929EA8", "#5B6570"),
        )
        page.pack(fill="both", expand=True, padx=8, pady=8)
        page.grid_columnconfigure(0, weight=3)
        page.grid_columnconfigure(1, weight=2)

        intro = ctk.CTkFrame(page, fg_color="transparent")
        intro.grid(row=0, column=0, columnspan=2, padx=8, pady=(6, 14), sticky="ew")

        ctk.CTkLabel(
            intro,
            text="Mediciones de referencia",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.TEXT,
        ).pack(anchor="w")

        ctk.CTkLabel(
            intro,
            text=(
                "Captura las condiciones ambientales y las lecturas del electrómetro. "
                "Los factores y la dosis se actualizan automáticamente."
            ),
            font=ctk.CTkFont(size=12),
            text_color=self.MUTED,
            wraplength=850,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        left = ctk.CTkFrame(page, fg_color="transparent")
        left.grid(row=1, column=0, padx=(8, 9), pady=(0, 8), sticky="nsew")
        left.grid_columnconfigure(0, weight=1)
        left.grid_columnconfigure(1, weight=1)

        right = ctk.CTkFrame(page, fg_color="transparent")
        right.grid(row=1, column=1, padx=(9, 8), pady=(0, 8), sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        environment_card = self._create_card(
            left,
            "Condiciones ambientales",
            "Valores registrados durante la medición.",
        )
        environment_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        self._add_labeled_entry(
            environment_card,
            row=2,
            label="Temperatura ambiente",
            variable=self.calculator_vars["T"],
            unit="°C",
            placeholder="Ej. 22.5",
        )
        self._add_labeled_entry(
            environment_card,
            row=3,
            label="Presión ambiente",
            variable=self.calculator_vars["P"],
            unit="kPa",
            placeholder="Ej. 80.1",
        )
        self._add_labeled_entry(
            environment_card,
            row=4,
            label="PDD en zref",
            variable=self.calculator_vars["PDD"],
            unit="% o fracción",
            placeholder="Ej. 67 o 0.67",
        )

        readings_card = self._create_card(
            left,
            "Lecturas del electrómetro",
            "Estas tres lecturas son indispensables para kpol y ks.",
        )
        readings_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        self._add_labeled_entry(
            readings_card,
            row=2,
            label="Lectura de referencia M−",
            variable=self.calculator_vars["M1"],
            unit="nC",
            placeholder="No puede ser cero",
            accent=True,
        )
        self._add_labeled_entry(
            readings_card,
            row=3,
            label="Polaridad opuesta M+",
            variable=self.calculator_vars["M+"],
            unit="nC",
            placeholder="Ej. 20.05",
        )
        self._add_labeled_entry(
            readings_card,
            row=4,
            label="Voltaje reducido M₂",
            variable=self.calculator_vars["M2"],
            unit="nC",
            placeholder="Ej. 19.80",
        )

        action_card = ctk.CTkFrame(
            left,
            fg_color=self.CARD,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER,
        )
        action_card.grid(
            row=1,
            column=0,
            columnspan=2,
            padx=0,
            pady=(16, 0),
            sticky="ew",
        )
        action_card.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            action_card,
            textvariable=self.status_var,
            font=ctk.CTkFont(size=12),
            text_color=self.MUTED,
            justify="left",
            anchor="w",
            wraplength=620,
        )
        self.status_label.grid(row=0, column=0, padx=18, pady=16, sticky="ew")

        ctk.CTkButton(
            action_card,
            text="Recalcular",
            command=self._recalculate,
            width=120,
            height=36,
            fg_color=self.BLUE,
            hover_color=self.BLUE_HOVER,
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=1, padx=(8, 8), pady=12)

        ctk.CTkButton(
            action_card,
            text="Limpiar lecturas",
            command=self._clear_measurements,
            width=135,
            height=36,
            fg_color="transparent",
            hover_color=("#E9EEF2", "#31373D"),
            border_width=1,
            border_color=self.BORDER,
            text_color=self.TEXT,
        ).grid(row=0, column=2, padx=(0, 14), pady=12)

        factors_card = self._create_card(
            right,
            "Factores de corrección",
            "Resultados calculados con las lecturas actuales.",
        )
        factors_card.grid(row=0, column=0, sticky="ew")
        factors_card.grid_columnconfigure(0, weight=1)

        factor_list = ctk.CTkFrame(factors_card, fg_color="transparent")
        factor_list.grid(row=2, column=0, padx=18, pady=(4, 14), sticky="ew")
        factor_list.grid_columnconfigure(1, weight=1)

        for row, (key, symbol, description) in enumerate(self.FACTOR_FIELDS):
            ctk.CTkLabel(
                factor_list,
                text=symbol,
                font=ctk.CTkFont(family="Cambria Math", size=17, weight="bold"),
                text_color=self.TEXT,
                anchor="w",
            ).grid(row=row, column=0, padx=(0, 12), pady=9, sticky="w")

            ctk.CTkLabel(
                factor_list,
                text=description,
                font=ctk.CTkFont(size=11),
                text_color=self.MUTED,
                anchor="w",
            ).grid(row=row, column=1, padx=(0, 12), pady=9, sticky="w")

            ctk.CTkLabel(
                factor_list,
                textvariable=self.factor_vars[key],
                width=92,
                height=30,
                corner_radius=8,
                fg_color=self.BLUE_SOFT,
                font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
                text_color=self.NAVY,
            ).grid(row=row, column=2, pady=7, sticky="e")

        dose_card = ctk.CTkFrame(
            right,
            fg_color=self.CARD,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER,
        )
        dose_card.grid(row=1, column=0, pady=(16, 0), sticky="ew")
        dose_card.grid_columnconfigure(0, weight=1)
        dose_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            dose_card,
            text="Dosis calculada",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.TEXT,
        ).grid(row=0, column=0, columnspan=2, padx=18, pady=(18, 4), sticky="w")

        ctk.CTkLabel(
            dose_card,
            text="Los resultados se muestran únicamente cuando todas las entradas son válidas.",
            font=ctk.CTkFont(size=11),
            text_color=self.MUTED,
            wraplength=400,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, padx=18, pady=(0, 14), sticky="w")

        self._add_result_panel(
            dose_card,
            column=0,
            title="D w,Q (zref)",
            subtitle="Dosis a profundidad de referencia",
            variable=self.reference_dose_var,
        )
        self._add_result_panel(
            dose_card,
            column=1,
            title="D w,Q (zmax)",
            subtitle="Dosis a profundidad de máxima",
            variable=self.maximum_dose_var,
        )

    # ------------------------------------------------------------------
    # Pestaña de calibración
    # ------------------------------------------------------------------
    def _build_calibration_tab(self, parent: ctk.CTkFrame) -> None:
        page = ctk.CTkScrollableFrame(parent, fg_color="transparent", corner_radius=0)
        page.pack(fill="both", expand=True, padx=8, pady=8)
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            page,
            text="Constantes de calibración",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.TEXT,
        ).grid(row=0, column=0, columnspan=2, padx=8, pady=(8, 4), sticky="w")

        ctk.CTkLabel(
            page,
            text=(
                "Verifica estos valores contra el certificado de la cámara, el electrómetro "
                "y el protocolo dosimétrico vigente antes de generar un reporte."
            ),
            font=ctk.CTkFont(size=12),
            text_color=self.MUTED,
            wraplength=900,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, padx=8, pady=(0, 16), sticky="w")

        chamber_card = self._create_card(
            page,
            "Cámara y calidad del haz",
            "Coeficientes que intervienen directamente en la dosis absorbida.",
        )
        chamber_card.grid(row=2, column=0, padx=(8, 9), pady=(0, 8), sticky="nsew")

        self._add_labeled_entry(
            chamber_card,
            row=2,
            label="Factor N D,w,Q0",
            variable=self.calculator_vars["N_dw"],
            unit="Gy/nC",
            placeholder="Certificado de calibración",
            accent=True,
        )
        self._add_labeled_entry(
            chamber_card,
            row=3,
            label="Factor k Q,Q0",
            variable=self.calculator_vars["k_QQ0"],
            unit="adimensional",
            placeholder="Calidad del haz",
        )
        self._add_labeled_entry(
            chamber_card,
            row=4,
            label="Factor k elec",
            variable=self.calculator_vars["k_elec"],
            unit="adimensional",
            placeholder="Corrección del electrómetro",
        )

        reference_card = self._create_card(
            page,
            "Condiciones de referencia",
            "Valores de referencia usados en la corrección kTP.",
        )
        reference_card.grid(row=2, column=1, padx=(9, 8), pady=(0, 8), sticky="nsew")

        self._add_labeled_entry(
            reference_card,
            row=2,
            label="Presión de referencia P₀",
            variable=self.calculator_vars["P_ref"],
            unit="kPa",
            placeholder="Ej. 101.325",
        )
        self._add_labeled_entry(
            reference_card,
            row=3,
            label="Temperatura de referencia T₀",
            variable=self.calculator_vars["T_ref"],
            unit="°C",
            placeholder="Ej. 20",
        )

        note = ctk.CTkFrame(
            page,
            fg_color=self.BLUE_SOFT,
            corner_radius=14,
            border_width=1,
            border_color=self.BORDER,
        )
        note.grid(
            row=3,
            column=0,
            columnspan=2,
            padx=8,
            pady=(12, 8),
            sticky="ew",
        )
        note.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            note,
            text="Importante",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.NAVY,
        ).grid(row=0, column=0, padx=18, pady=(14, 2), sticky="w")

        ctk.CTkLabel(
            note,
            text=(
                "La aplicación ayuda a organizar y calcular los datos, pero no sustituye "
                "la validación clínica independiente ni la revisión del protocolo institucional."
            ),
            font=ctk.CTkFont(size=12),
            text_color=self.TEXT,
            wraplength=920,
            justify="left",
        ).grid(row=1, column=0, padx=18, pady=(0, 14), sticky="w")

        ctk.CTkButton(
            page,
            text="Guardar constantes",
            command=self._save_settings,
            height=42,
            width=190,
            fg_color=self.BLUE,
            hover_color=self.BLUE_HOVER,
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=4, column=1, padx=8, pady=(12, 20), sticky="e")

    # ------------------------------------------------------------------
    # Pestaña de equipo y reporte
    # ------------------------------------------------------------------
    def _build_equipment_tab(self, parent: ctk.CTkFrame) -> None:
        page = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=("#AEB8C1", "#4B545D"),
            scrollbar_button_hover_color=("#929EA8", "#5B6570"),
        )
        page.pack(fill="both", expand=True, padx=8, pady=8)
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            page,
            text="Datos para el reporte",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.TEXT,
        ).grid(row=0, column=0, columnspan=2, padx=8, pady=(8, 4), sticky="w")

        ctk.CTkLabel(
            page,
            text=(
                "Completa la información del LINAC, la geometría, el equipo de medición "
                "y las lecturas oficiales antes de generar el PDF."
            ),
            font=ctk.CTkFont(size=12),
            text_color=self.MUTED,
            wraplength=900,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, padx=8, pady=(0, 16), sticky="w")

        treatment_card = self._create_card(
            page,
            "1. Equipo de tratamiento",
            "Identificación del acelerador y del haz.",
        )
        treatment_card.grid(row=2, column=0, padx=(8, 9), pady=(0, 16), sticky="nsew")

        self._add_setting_combo(
            treatment_card,
            2,
            "equipment",
            "brand",
            "Marca",
            ["Varian", "Elekta", "Accuray", "Siemens", "Otro"],
        )
        self._add_setting_combo(
            treatment_card,
            3,
            "equipment",
            "model",
            "Modelo",
            ["Clinac iX", "TrueBeam", "Halcyon", "Synergy", "Versa HD", "Otro"],
        )
        self._add_setting_entry(
            treatment_card, 4, "equipment", "serial_number", "Número de serie"
        )
        self._add_setting_combo(
            treatment_card,
            5,
            "equipment",
            "beam",
            "Haz a calibrar",
            ["Fotones", "Electrones"],
        )
        self._add_setting_combo(
            treatment_card,
            6,
            "equipment",
            "energy",
            "Energía",
            ["6 MV", "10 MV", "15 MV", "18 MV", "6 MeV", "9 MeV", "12 MeV", "Otro"],
        )

        geometry_card = self._create_card(
            page,
            "2. Geometría de irradiación",
            "Condiciones geométricas usadas durante la calibración.",
        )
        geometry_card.grid(row=2, column=1, padx=(9, 8), pady=(0, 16), sticky="nsew")

        self._add_setting_entry(
            geometry_card, 2, "equipment", "dose_rate", "Tasa nominal", "UM/min"
        )
        self._add_setting_combo(
            geometry_card, 3, "equipment", "setup", "Setup", ["SSD", "SAD"]
        )
        self._add_setting_combo(
            geometry_card, 4, "equipment", "phantom", "Fantoma", ["Agua", "Sólido", "Otro"]
        )
        self._add_setting_entry(
            geometry_card, 5, "equipment", "distance_cm", "Distancia", "cm"
        )
        self._add_setting_entry(
            geometry_card, 6, "equipment", "field_size_cm", "Tamaño de campo", "cm²"
        )
        self._add_setting_entry(
            geometry_card, 7, "equipment", "reference_depth", "Profundidad de referencia", "cm"
        )

        measurement_card = self._create_card(
            page,
            "3. Equipo de medición",
            "Cámara de ionización y electrómetro.",
        )
        measurement_card.grid(
            row=3,
            column=0,
            columnspan=2,
            padx=8,
            pady=(0, 16),
            sticky="ew",
        )
        measurement_card.grid_columnconfigure(0, weight=1)
        measurement_card.grid_columnconfigure(1, weight=1)

        measurement_left = ctk.CTkFrame(measurement_card, fg_color="transparent")
        measurement_left.grid(row=2, column=0, padx=(18, 9), pady=(4, 16), sticky="nsew")
        measurement_left.grid_columnconfigure(0, weight=1)

        measurement_right = ctk.CTkFrame(measurement_card, fg_color="transparent")
        measurement_right.grid(row=2, column=1, padx=(9, 18), pady=(4, 16), sticky="nsew")
        measurement_right.grid_columnconfigure(0, weight=1)

        self._add_setting_combo(
            measurement_left,
            0,
            "measurement_equipment",
            "ion_chamber",
            "Cámara de ionización",
            ["PTW 30013", "IBA FC65-G", "Exradin A12", "Otro"],
        )
        self._add_setting_entry(
            measurement_left,
            1,
            "measurement_equipment",
            "ion_chamber_serial",
            "Serie de la cámara",
        )
        self._add_setting_combo(
            measurement_left,
            2,
            "measurement_equipment",
            "electrometer",
            "Electrómetro",
            ["PTW", "IBA", "Standard Imaging", "Otro"],
        )
        self._add_setting_entry(
            measurement_left,
            3,
            "measurement_equipment",
            "electrometer_model",
            "Modelo del electrómetro",
        )

        self._add_setting_entry(
            measurement_right,
            0,
            "measurement_equipment",
            "electrometer_serial",
            "Serie del electrómetro",
        )
        self._add_setting_combo(
            measurement_right,
            1,
            "measurement_equipment",
            "measurement_mode",
            "Modo de medición",
            ["Carga (nC)", "Corriente (nA)", "Otro"],
        )
        self._add_setting_combo(
            measurement_right,
            2,
            "measurement_equipment",
            "measurement_range",
            "Rango de medición",
            ["Low", "Medium", "High", "Auto"],
        )

        quality_card = self._create_card(
            page,
            "4. Calidad del haz y PDD",
            "Campos usados por las secciones 4 y 7 del reporte.",
        )
        quality_card.grid(row=4, column=0, padx=(8, 9), pady=(0, 16), sticky="nsew")

        self._add_report_entry(quality_card, 2, "zmax_sec4", "Zmáx", "mm")
        self._add_report_entry(quality_card, 3, "pdd20", "PDD20", "%")
        self._add_report_entry(quality_card, 4, "pdd10", "PDD10", "%")
        self._add_report_entry(quality_card, 5, "pdd20_10", "PDD20,10")
        self._add_report_entry(quality_card, 6, "tpr20_10", "TPR20,10")
        self._add_report_entry(quality_card, 7, "zmax_sec7", "Zmáx para resultado", "mm")

        readings_card = self._create_card(
            page,
            "5. Lecturas oficiales",
            "El promedio de L1, L2 y L3 se utiliza para el cálculo mostrado en el PDF.",
        )
        readings_card.grid(row=4, column=1, padx=(9, 8), pady=(0, 16), sticky="nsew")
        readings_card.grid_columnconfigure(0, weight=1)

        reading_grid = ctk.CTkFrame(readings_card, fg_color="transparent")
        reading_grid.grid(row=2, column=0, padx=18, pady=(8, 12), sticky="ew")

        for column, variable in enumerate(self.official_readings):
            reading_grid.grid_columnconfigure(column, weight=1)
            ctk.CTkLabel(
                reading_grid,
                text=f"L{column + 1}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=self.TEXT,
            ).grid(row=0, column=column, padx=5, pady=(0, 6))
            ctk.CTkEntry(
                reading_grid,
                textvariable=variable,
                height=40,
                justify="center",
                placeholder_text="nC",
                border_color=self.BORDER,
                fg_color=("#F8FAFC", "#181D22"),
            ).grid(row=1, column=column, padx=5, sticky="ew")

        ctk.CTkLabel(
            readings_card,
            text=(
                "Si alguna lectura queda vacía o no es válida, se utilizará M− "
                "como valor de respaldo para las tres lecturas."
            ),
            font=ctk.CTkFont(size=11),
            text_color=self.MUTED,
            wraplength=420,
            justify="left",
        ).grid(row=3, column=0, padx=18, pady=(0, 16), sticky="w")

        actions = ctk.CTkFrame(
            page,
            fg_color=self.CARD,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER,
        )
        actions.grid(
            row=5,
            column=0,
            columnspan=2,
            padx=8,
            pady=(0, 24),
            sticky="ew",
        )
        actions.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            actions,
            text="Guarda la configuración o genera el reporte cuando el cálculo sea válido.",
            font=ctk.CTkFont(size=12),
            text_color=self.MUTED,
        ).grid(row=0, column=0, padx=18, pady=18, sticky="w")

        ctk.CTkButton(
            actions,
            text="Guardar configuración",
            command=self._save_settings,
            height=42,
            width=180,
            fg_color="transparent",
            hover_color=("#E9EEF2", "#31373D"),
            border_width=1,
            border_color=self.BORDER,
            text_color=self.TEXT,
        ).grid(row=0, column=1, padx=(8, 8), pady=12)

        ctk.CTkButton(
            actions,
            text="Generar reporte PDF",
            command=self._generate_pdf,
            height=42,
            width=190,
            fg_color=self.SUCCESS,
            hover_color=self.SUCCESS_HOVER,
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=2, padx=(0, 14), pady=12)

    # ------------------------------------------------------------------
    # Componentes reutilizables
    # ------------------------------------------------------------------
    def _create_card(
        self,
        parent: ctk.CTkFrame,
        title: str,
        subtitle: str,
    ) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent,
            fg_color=self.CARD,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER,
        )
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=self.TEXT,
        ).grid(row=0, column=0, padx=18, pady=(17, 2), sticky="w")

        ctk.CTkLabel(
            card,
            text=subtitle,
            font=ctk.CTkFont(size=11),
            text_color=self.MUTED,
            wraplength=460,
            justify="left",
        ).grid(row=1, column=0, padx=18, pady=(0, 12), sticky="w")

        return card

    def _add_labeled_entry(
        self,
        parent: ctk.CTkFrame,
        row: int,
        label: str,
        variable: ctk.StringVar,
        unit: str = "",
        placeholder: str = "",
        accent: bool = False,
    ) -> None:
        field = ctk.CTkFrame(parent, fg_color="transparent")
        field.grid(row=row, column=0, padx=18, pady=7, sticky="ew")
        field.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            field,
            text=label,
            font=ctk.CTkFont(size=12, weight="bold" if accent else "normal"),
            text_color=self.NAVY if accent else self.TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        if unit:
            ctk.CTkLabel(
                field,
                text=unit,
                font=ctk.CTkFont(size=10),
                text_color=self.MUTED,
                anchor="e",
            ).grid(row=0, column=1, sticky="e")

        ctk.CTkEntry(
            field,
            textvariable=variable,
            height=40,
            justify="center",
            placeholder_text=placeholder,
            border_width=2 if accent else 1,
            border_color=self.BLUE if accent else self.BORDER,
            fg_color=("#F8FAFC", "#181D22"),
            font=ctk.CTkFont(size=14),
        ).grid(row=1, column=0, columnspan=2, pady=(5, 0), sticky="ew")

    def _add_result_panel(
        self,
        parent: ctk.CTkFrame,
        column: int,
        title: str,
        subtitle: str,
        variable: ctk.StringVar,
    ) -> None:
        panel = ctk.CTkFrame(
            parent,
            fg_color=self.BLUE_SOFT,
            corner_radius=12,
            border_width=1,
            border_color=self.BORDER,
        )
        panel.grid(
            row=2,
            column=column,
            padx=(18 if column == 0 else 7, 7 if column == 0 else 18),
            pady=(0, 18),
            sticky="nsew",
        )

        ctk.CTkLabel(
            panel,
            text=title,
            font=ctk.CTkFont(family="Cambria Math", size=15, weight="bold"),
            text_color=self.NAVY,
        ).pack(anchor="w", padx=14, pady=(13, 2))

        ctk.CTkLabel(
            panel,
            text=subtitle,
            font=ctk.CTkFont(size=10),
            text_color=self.MUTED,
            wraplength=170,
            justify="left",
        ).pack(anchor="w", padx=14)

        ctk.CTkLabel(
            panel,
            textvariable=variable,
            font=ctk.CTkFont(family="Consolas", size=20, weight="bold"),
            text_color=self.BLUE,
        ).pack(anchor="w", padx=14, pady=(10, 14))

    def _setting_variable(self, section: str, key: str) -> ctk.StringVar:
        variable_key = (section, key)
        if variable_key not in self.equipment_vars:
            self.equipment_vars[variable_key] = ctk.StringVar(
                value=str(self.settings.get(section, {}).get(key, ""))
            )
        return self.equipment_vars[variable_key]

    def _add_setting_entry(
        self,
        parent: ctk.CTkFrame,
        row: int,
        section: str,
        key: str,
        label: str,
        unit: str = "",
    ) -> None:
        self._add_form_control(
            parent,
            row,
            label,
            unit,
            lambda container: ctk.CTkEntry(
                container,
                textvariable=self._setting_variable(section, key),
                height=38,
                border_color=self.BORDER,
                fg_color=("#F8FAFC", "#181D22"),
            ),
        )

    def _add_setting_combo(
        self,
        parent: ctk.CTkFrame,
        row: int,
        section: str,
        key: str,
        label: str,
        values: list[str],
    ) -> None:
        self._add_form_control(
            parent,
            row,
            label,
            "",
            lambda container: ctk.CTkComboBox(
                container,
                variable=self._setting_variable(section, key),
                values=values,
                height=38,
                border_color=self.BORDER,
                button_color=self.BLUE,
                button_hover_color=self.BLUE_HOVER,
                dropdown_hover_color=self.BLUE_SOFT,
            ),
        )

    def _add_report_entry(
        self,
        parent: ctk.CTkFrame,
        row: int,
        key: str,
        label: str,
        unit: str = "",
    ) -> None:
        self._add_form_control(
            parent,
            row,
            label,
            unit,
            lambda container: ctk.CTkEntry(
                container,
                textvariable=self.report_vars[key],
                height=38,
                border_color=self.BORDER,
                fg_color=("#F8FAFC", "#181D22"),
            ),
        )

    def _add_form_control(
        self,
        parent: ctk.CTkFrame,
        row: int,
        label: str,
        unit: str,
        factory: Callable[[ctk.CTkFrame], ctk.CTkBaseClass],
    ) -> None:
        field = ctk.CTkFrame(parent, fg_color="transparent")
        field.grid(row=row, column=0, padx=18, pady=6, sticky="ew")
        field.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            field,
            text=label,
            font=ctk.CTkFont(size=12),
            text_color=self.TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        if unit:
            ctk.CTkLabel(
                field,
                text=unit,
                font=ctk.CTkFont(size=10),
                text_color=self.MUTED,
                anchor="e",
            ).grid(row=0, column=1, sticky="e")

        control = factory(field)
        control.grid(row=1, column=0, columnspan=2, pady=(5, 0), sticky="ew")

    # ------------------------------------------------------------------
    # Cálculo y estado
    # ------------------------------------------------------------------
    def _on_calculation_change(self, *_args: Any) -> None:
        self._recalculate(show_neutral_if_incomplete=True)

    def _recalculate(self, show_neutral_if_incomplete: bool = False) -> None:
        values = {
            key: variable.get().strip() or "0.0"
            for key, variable in self.calculator_vars.items()
        }
        self.calculator.update_values(values)
        self._refresh_results(
            initial=show_neutral_if_incomplete and not self._all_required_fields_present()
        )

    def _all_required_fields_present(self) -> bool:
        return all(
            self.calculator_vars[key].get().strip()
            for key in ("T", "P", "M1", "M+", "M2", "PDD")
        )

    def _refresh_results(self, initial: bool = False) -> None:
        result = self.calculator.last_result

        if result is None:
            for variable in self.factor_vars.values():
                variable.set("—")
            self.reference_dose_var.set("—")
            self.maximum_dose_var.set("—")

            if initial or not self._all_required_fields_present():
                self.status_var.set(
                    "Completa T, P, M−, M+, M₂ y PDD. "
                    "El campo M− es la lectura de referencia para kpol."
                )
                self._set_status_style("neutral")
            else:
                self.status_var.set(
                    self.calculator.last_error
                    or "Revisa los valores ingresados para completar el cálculo."
                )
                self._set_status_style("error")
            return

        for key, variable in self.factor_vars.items():
            variable.set(self.calculator.get(key))

        self.reference_dose_var.set(f"{result.dose_at_reference:.4f} Gy")
        self.maximum_dose_var.set(f"{result.final_dose:.4f} Gy")
        self.status_var.set(
            "Cálculo válido. El PDD puede escribirse como porcentaje (67) "
            "o como fracción (0.67)."
        )
        self._set_status_style("success")

    def _set_status_style(self, state: str) -> None:
        if self.status_label is None:
            return

        color = {
            "neutral": self.MUTED,
            "success": self.SUCCESS,
            "error": self.DANGER,
        }.get(state, self.MUTED)
        self.status_label.configure(text_color=color)

    def _clear_measurements(self) -> None:
        for key in ("M1", "M+", "M2", "PDD"):
            self.calculator_vars[key].set("")
        self.status_var.set("Las lecturas fueron limpiadas.")
        self._set_status_style("neutral")

    # ------------------------------------------------------------------
    # Configuración y reporte
    # ------------------------------------------------------------------
    def _collect_settings(self) -> None:
        for (section, key), variable in self.equipment_vars.items():
            self.settings.setdefault(section, {})[key] = variable.get().strip()

        self.settings["calibration"] = {
            key: self.calculator_vars[key].get().strip()
            for key in self.CALIBRATION_KEYS
        }

        self.settings["report"].update(
            {key: variable.get().strip() for key, variable in self.report_vars.items()}
        )
        self.settings["report"]["official_readings"] = [
            variable.get().strip() for variable in self.official_readings
        ]

    def _save_settings(self) -> None:
        try:
            self._collect_settings()
            self.settings_repository.save(self.settings)
        except Exception as error:
            messagebox.showerror(
                "No se pudo guardar",
                f"Ocurrió un error al guardar la configuración:\n\n{error}",
                parent=self.root,
            )
            return

        messagebox.showinfo(
            "Configuración guardada",
            "La configuración se guardó correctamente.",
            parent=self.root,
        )

    def _generate_pdf(self) -> None:
        self._recalculate()
        if self.calculator.last_result is None:
            messagebox.showerror(
                "Cálculo incompleto",
                self.calculator.last_error
                or "Completa las mediciones antes de generar el reporte.",
                parent=self.root,
            )
            return

        destination = filedialog.asksaveasfilename(
            parent=self.root,
            defaultextension=".pdf",
            initialfile="Reporte_Calibracion.pdf",
            filetypes=[("Archivos PDF", "*.pdf")],
            title="Guardar reporte de calibración",
        )
        if not destination:
            return

        try:
            self._collect_settings()
            self.settings_repository.save(self.settings)

            report_data = build_report_data(
                self.calculator,
                self.settings,
                [variable.get() for variable in self.official_readings],
            )

            # Completa los campos que el esquema base deja vacíos.
            report_data.update(
                {
                    "zmax_sec4": self.report_vars["zmax_sec4"].get().strip(),
                    "pdd20": self.report_vars["pdd20"].get().strip(),
                    "pdd10": (
                        self.report_vars["pdd10"].get().strip()
                        or self.calculator.values["PDD"]
                    ),
                    "pdd20_10": self.report_vars["pdd20_10"].get().strip(),
                    "tpr20_10": self.report_vars["tpr20_10"].get().strip(),
                    "zmax_sec7": (
                        self.report_vars["zmax_sec7"].get().strip()
                        or self.report_vars["zmax_sec4"].get().strip()
                    ),
                    "pdd_zref": self.calculator.values["PDD"],
                }
            )

            generate_calibration_report(report_data, destination)
        except Exception as error:
            messagebox.showerror(
                "No se pudo generar el reporte",
                f"Ocurrió un error al generar el PDF:\n\n{error}",
                parent=self.root,
            )
            return

        messagebox.showinfo(
            "Reporte generado",
            f"El reporte se guardó correctamente en:\n\n{destination}",
            parent=self.root,
        )

    # ------------------------------------------------------------------
    # Ventana
    # ------------------------------------------------------------------
    def _toggle_theme(self) -> None:
        if self.theme_switch is None:
            return

        dark = bool(self.theme_switch.get())
        ctk.set_appearance_mode("Dark" if dark else "Light")
        self.theme_switch.configure(text="Modo claro" if dark else "Modo oscuro")

    def _close(self) -> None:
        try:
            self._collect_settings()
            self.settings_repository.save(self.settings)
        finally:
            self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def run() -> None:
    """Inicia la interfaz de escritorio."""

    DosimetryDesktopApp().run()


if __name__ == "__main__":
    run()
