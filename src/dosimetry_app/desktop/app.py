"""CustomTkinter desktop application."""

from __future__ import annotations

from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

from dosimetry_app.calculator import DosimetryCalculator
from dosimetry_app.reporting import build_report_data, generate_calibration_report
from dosimetry_app.settings import SettingsRepository


class DosimetryDesktopApp:
    """Desktop UI backed by the same calculator used by the mobile app."""

    MEASUREMENT_FIELDS = (
        ("T", "Temperatura ambiente (°C)"),
        ("P", "Presión ambiente (kPa)"),
        ("M1", "Lectura M− (nC)"),
        ("M+", "Lectura M+ (nC)"),
        ("M2", "Lectura a 100 V (nC)"),
        ("PDD", "PDD (0.67 o 67)"),
    )
    CALIBRATION_FIELDS = (
        ("N_dw", "N D,w,Q0 (Gy/nC)"),
        ("k_QQ0", "k Q,Q0"),
        ("T_ref", "Temperatura de referencia (°C)"),
        ("P_ref", "Presión de referencia (kPa)"),
        ("k_elec", "k elec"),
    )
    EQUIPMENT_FIELDS = (
        ("equipment", "brand", "Marca"),
        ("equipment", "model", "Modelo"),
        ("equipment", "serial_number", "Serie del equipo"),
        ("equipment", "beam", "Haz"),
        ("equipment", "energy", "Energía"),
        ("equipment", "dose_rate", "Tasa de dosis (UM/min)"),
        ("equipment", "setup", "Setup"),
        ("equipment", "phantom", "Fantoma"),
        ("equipment", "distance_cm", "Distancia (cm)"),
        ("equipment", "field_size_cm", "Campo (cm)"),
        ("equipment", "reference_depth", "Profundidad de referencia"),
        ("measurement_equipment", "electrometer", "Electrómetro"),
        ("measurement_equipment", "electrometer_model", "Modelo del electrómetro"),
        ("measurement_equipment", "electrometer_serial", "Serie del electrómetro"),
        ("measurement_equipment", "measurement_mode", "Modo de medición"),
        ("measurement_equipment", "measurement_range", "Rango de medición"),
        ("measurement_equipment", "ion_chamber", "Cámara de ionización"),
        ("measurement_equipment", "ion_chamber_serial", "Serie de la cámara"),
    )

    def __init__(self) -> None:
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("dark-blue")

        self.calculator = DosimetryCalculator()
        self.settings_repository = SettingsRepository()
        self.settings = self.settings_repository.load()
        self.root = ctk.CTk()
        self.root.title("Calculadora de Dosimetría")
        self.root.geometry("560x790")
        self.root.minsize(520, 700)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

        self.measurement_vars: dict[str, ctk.StringVar] = {}
        self.factor_vars = {
            key: ctk.StringVar(value="----")
            for key in ("k_tp", "k_pol", "k_s", "P_Q", "Dosis_Referencia", "Dosis_Final")
        }
        self.equipment_vars: dict[tuple[str, str], ctk.StringVar] = {}
        self.official_readings = [ctk.StringVar(value="") for _ in range(3)]

        self._build_ui()
        self._refresh_result()

    def _build_ui(self) -> None:
        tabs = ctk.CTkTabview(self.root)
        tabs.pack(padx=18, pady=18, fill="both", expand=True)
        measurements_tab = tabs.add("Mediciones")
        calibration_tab = tabs.add("Calibración")
        equipment_tab = tabs.add("Equipo y reporte")

        self._build_measurements_tab(measurements_tab)
        self._build_calibration_tab(calibration_tab)
        self._build_equipment_tab(equipment_tab)

    def _build_measurements_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure(1, weight=1)
        for row, (key, label) in enumerate(self.MEASUREMENT_FIELDS):
            ctk.CTkLabel(parent, text=label, anchor="w").grid(
                row=row, column=0, padx=16, pady=8, sticky="w"
            )
            variable = ctk.StringVar(
                value="" if self.calculator.values[key] == "0.0" else self.calculator.values[key]
            )
            self.measurement_vars[key] = variable
            entry = ctk.CTkEntry(parent, textvariable=variable)
            entry.grid(row=row, column=1, padx=16, pady=8, sticky="ew")
            variable.trace_add("write", self._on_calculation_change)

        factors = ctk.CTkFrame(parent)
        factors.grid(
            row=len(self.MEASUREMENT_FIELDS), column=0, columnspan=2, padx=16, pady=18, sticky="ew"
        )
        for index, (key, label) in enumerate(
            (
                ("k_tp", "kTP"),
                ("k_pol", "kpol"),
                ("k_s", "ks"),
                ("P_Q", "PQ"),
                ("Dosis_Referencia", "D(zref)"),
                ("Dosis_Final", "Dosis final"),
            )
        ):
            ctk.CTkLabel(factors, text=f"{label}:").grid(
                row=index, column=0, padx=14, pady=5, sticky="w"
            )
            ctk.CTkLabel(
                factors, textvariable=self.factor_vars[key], font=ctk.CTkFont(weight="bold")
            ).grid(row=index, column=1, padx=14, pady=5, sticky="e")
        factors.grid_columnconfigure(1, weight=1)

    def _build_calibration_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure(1, weight=1)
        for row, (key, label) in enumerate(self.CALIBRATION_FIELDS):
            ctk.CTkLabel(parent, text=label, anchor="w").grid(
                row=row, column=0, padx=16, pady=10, sticky="w"
            )
            variable = ctk.StringVar(value=self.calculator.values[key])
            self.measurement_vars[key] = variable
            ctk.CTkEntry(parent, textvariable=variable).grid(
                row=row, column=1, padx=16, pady=10, sticky="ew"
            )
            variable.trace_add("write", self._on_calculation_change)

        ctk.CTkLabel(
            parent,
            text=(
                "Los valores se guardan localmente. Verifica siempre los factores de calibración "
                "contra el certificado y el protocolo vigente."
            ),
            wraplength=430,
            justify="left",
            text_color=("#555555", "#B0B0B0"),
        ).grid(
            row=len(self.CALIBRATION_FIELDS), column=0, columnspan=2, padx=16, pady=18, sticky="w"
        )

    def _build_equipment_tab(self, parent: ctk.CTkFrame) -> None:
        scroll = ctk.CTkScrollableFrame(parent)
        scroll.pack(fill="both", expand=True, padx=6, pady=6)
        scroll.grid_columnconfigure(1, weight=1)
        for row, (section, key, label) in enumerate(self.EQUIPMENT_FIELDS):
            ctk.CTkLabel(scroll, text=label, anchor="w").grid(
                row=row, column=0, padx=12, pady=6, sticky="w"
            )
            variable = ctk.StringVar(value=str(self.settings[section][key]))
            self.equipment_vars[(section, key)] = variable
            ctk.CTkEntry(scroll, textvariable=variable).grid(
                row=row, column=1, padx=12, pady=6, sticky="ew"
            )

        reading_row = len(self.EQUIPMENT_FIELDS)
        ctk.CTkLabel(scroll, text="Lecturas oficiales L1, L2 y L3").grid(
            row=reading_row, column=0, columnspan=2, padx=12, pady=(18, 8), sticky="w"
        )
        readings_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        readings_frame.grid(row=reading_row + 1, column=0, columnspan=2, padx=12, sticky="ew")
        for index, variable in enumerate(self.official_readings):
            readings_frame.grid_columnconfigure(index, weight=1)
            ctk.CTkEntry(
                readings_frame, textvariable=variable, placeholder_text=f"L{index + 1}"
            ).grid(row=0, column=index, padx=4, sticky="ew")

        ctk.CTkButton(scroll, text="Guardar configuración", command=self._save_settings).grid(
            row=reading_row + 2, column=0, padx=12, pady=18, sticky="ew"
        )
        ctk.CTkButton(scroll, text="Generar reporte PDF", command=self._generate_pdf).grid(
            row=reading_row + 2, column=1, padx=12, pady=18, sticky="ew"
        )

    def _on_calculation_change(self, *_args: Any) -> None:
        values = {key: variable.get() or "0.0" for key, variable in self.measurement_vars.items()}
        self.calculator.update_values(values)
        self._refresh_result()

    def _refresh_result(self) -> None:
        if self.calculator.last_result is None:
            for variable in self.factor_vars.values():
                variable.set("----")
            return
        for key, variable in self.factor_vars.items():
            variable.set(self.calculator.get(key))

    def _collect_settings(self) -> None:
        for (section, key), variable in self.equipment_vars.items():
            self.settings[section][key] = variable.get().strip()

    def _save_settings(self) -> None:
        self._collect_settings()
        self.settings_repository.save(self.settings)
        messagebox.showinfo("Configuración", "La configuración se guardó correctamente.")

    def _generate_pdf(self) -> None:
        if self.calculator.last_result is None:
            messagebox.showerror(
                "Cálculo incompleto",
                self.calculator.last_error
                or "Completa las mediciones antes de generar el reporte.",
            )
            return
        destination = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile="Reporte_Calibracion.pdf",
            filetypes=[("Archivos PDF", "*.pdf")],
            title="Guardar reporte",
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
            generate_calibration_report(report_data, destination)
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo generar el reporte:\n\n{error}")
            return
        messagebox.showinfo("Reporte generado", f"El reporte se guardó en:\n{destination}")

    def _close(self) -> None:
        self._collect_settings()
        self.settings_repository.save(self.settings)
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def run() -> None:
    DosimetryDesktopApp().run()


if __name__ == "__main__":
    run()
