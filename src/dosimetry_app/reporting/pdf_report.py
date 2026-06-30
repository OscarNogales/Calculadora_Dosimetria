from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

from fpdf import FPDF


def generate_calibration_report(
    data: Mapping[str, object],
    output_path: str | Path = "reporte_final.pdf",
) -> Path:
    """Generate the Spanish absolute-dose calibration report."""
    datos = data
    # Inicializar documento
    pdf = FPDF(format="A4")
    pdf.add_page()

    # Borde principal de toda la hoja
    pdf.rect(10, 10, 190, 278)

    # ---------------------------------------------------------
    # CONFIGURACIÓN DE FUENTE MAESTRA (Tamaño fijo para todo el doc)
    # ---------------------------------------------------------
    pdf.set_font("Times", size=8)

    # ==========================================
    # ENCABEZADO
    # ==========================================
    pdf.set_xy(10, 12)
    pdf.cell(190, 5, "CALIBRACIÓN DE DOSIS ABSOLUTA", align="C")
    pdf.set_xy(10, 12)
    pdf.cell(120, 5, f"Fecha: {datetime.now().strftime('%d-%m-%Y')}")
    pdf.set_xy(10, 17)
    pdf.cell(190, 5, "Centro Estatal de Atención Oncológica, Morelia, Mich.", align="C")

    # Empezamos un poco más abajo para dar aire
    y_pos = 28

    # ==========================================
    # 1. DATOS DEL EQUIPO
    # ==========================================
    pdf.set_text_color(255, 0, 0)
    pdf.set_font("Times", style="B")
    pdf.set_xy(10, y_pos)
    pdf.cell(190, 5, "1. DATOS DEL EQUIPO DE TRATAMIENTO", align="C")

    y_pos += 7  # Más aire
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Times", style="")
    pdf.set_xy(40, y_pos)
    pdf.cell(60, 5, f"Marca: {datos.get('marca_equipo', '')}")
    pdf.set_xy(120, y_pos)
    pdf.cell(80, 5, "Equipo de teleterapia: Acelerador Lineal")

    y_pos += 6
    pdf.set_xy(40, y_pos)
    pdf.cell(60, 5, f"Modelo: {datos.get('modelo_equipo', '')}")
    pdf.set_xy(120, y_pos)
    pdf.cell(80, 5, f"Haz a calibrar: {datos.get('haz_calibrar', '')}")

    y_pos += 6
    pdf.set_xy(40, y_pos)
    pdf.cell(60, 5, f"Serie: {datos.get('serie_equipo', '')}")
    pdf.set_xy(120, y_pos)
    pdf.cell(80, 5, f"Energía a calibrar: {datos.get('energia_calibrar', '')}")

    # ==========================================
    # 2. DATOS DE LA GEOMETRÍA
    # ==========================================
    y_pos += 10  # Salto grande de sección
    pdf.set_text_color(255, 0, 0)
    pdf.set_font("Times", style="B")
    pdf.set_xy(10, y_pos)
    pdf.cell(190, 5, "2. DATOS DE LA GEOMETRÍA DE IRRADIACIÓN", align="C")

    y_pos += 7
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Times", style="")
    pdf.set_xy(40, y_pos)
    pdf.cell(60, 5, f"Tasa de dosis nominal: {datos.get('tasa_dosis', '')} UM/min")
    pdf.set_xy(120, y_pos)
    pdf.cell(80, 5, f"Setup: {datos.get('setup', 'SSD')}")

    y_pos += 6
    pdf.set_xy(40, y_pos)
    pdf.cell(60, 5, f"Fantoma de referencia: {datos.get('fantoma', 'Agua')}")
    pdf.set_xy(120, y_pos)
    pdf.cell(80, 5, f"Distancia a la superficie: {datos.get('distancia_cm', '100.0')} cm")

    y_pos += 6
    pdf.set_xy(40, y_pos)
    pdf.cell(60, 5, f"Tamaño de campo: {datos.get('campo_cm', '10 x 10')} cm²")
    pdf.set_xy(120, y_pos)
    pdf.write_html(
        f"Profundidad de referencia (Z<sub>ref</sub>): {datos.get('zref', '10.0')} g/cm<sup>2</sup>"
    )

    # ==========================================
    # 3. DATOS DEL EQUIPO DE MEDICIÓN
    # ==========================================
    y_pos += 10  # Salto grande de sección
    pdf.set_text_color(255, 0, 0)
    pdf.set_font("Times", style="B")
    pdf.set_xy(10, y_pos)
    pdf.cell(190, 5, "3. DATOS DEL EQUIPO DE MEDICIÓN", align="C")

    y_pos += 7
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Times", style="")
    pdf.set_xy(40, y_pos)
    pdf.cell(70, 5, f"Electrómetro: {datos.get('electrometro', '')}")
    pdf.set_xy(120, y_pos)
    pdf.cell(70, 5, f"Cámara de ionización: {datos.get('camara', '')}")

    y_pos += 6
    pdf.set_xy(40, y_pos)
    pdf.cell(70, 5, f"Marca o serie: {datos.get('marca_serie_elec', '')}")
    pdf.set_xy(120, y_pos)
    pdf.cell(70, 5, f"Serie: {datos.get('serie_camara', '')}")

    y_pos += 6
    pdf.set_xy(40, y_pos)
    pdf.cell(70, 5, f"Modo de medición: {datos.get('modo_medicion', '')}")
    pdf.set_xy(120, y_pos)
    pdf.cell(70, 5, f"Factor de calibración: {datos.get('factor_calibracion', '')} Gy/nC")

    y_pos += 6
    pdf.set_xy(40, y_pos)
    pdf.cell(70, 5, f"Rango de medición: {datos.get('rango_medicion', '')}")
    pdf.set_xy(120, y_pos)
    pdf.cell(70, 5, f"P0: {datos.get('p0', '')}")

    y_pos += 6
    pdf.set_xy(40, y_pos)
    pdf.cell(70, 5, f"Coeficiente calibración: {datos.get('k_elec', '')} k_elec")
    pdf.set_xy(120, y_pos)
    pdf.cell(70, 5, f"T0: {datos.get('t0', '')}")

    # ==========================================
    # 4. OBTENER PDD
    # ==========================================
    y_pos += 10  # Salto grande de sección
    pdf.set_text_color(255, 0, 0)
    pdf.set_font("Times", style="B")
    pdf.set_xy(10, y_pos)
    pdf.cell(190, 5, "4. OBTENER PDD DE CAMPO 10 X 10:", align="C")

    y_pos += 7
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Times", style="")
    pdf.set_xy(40, y_pos)
    pdf.cell(40, 5, f"Zmáx: {datos.get('zmax_sec4', '')} mm")
    pdf.set_xy(40, y_pos + 5)
    pdf.cell(40, 5, f"PDD20: {datos.get('pdd20', '')} %")
    pdf.set_xy(40, y_pos + 10)
    pdf.cell(40, 5, f"PDD10: {datos.get('pdd10', '')} %")
    pdf.set_xy(40, y_pos + 15)
    pdf.cell(40, 5, f"PDD20,10: {datos.get('pdd20_10', '')}")
    pdf.set_xy(40, y_pos + 20)
    pdf.cell(40, 5, f"TPR20,10: {datos.get('tpr20_10', '')}")

    # Caja a la derecha
    pdf.rect(85, y_pos, 100, 24)
    y_pos += 26

    # ==========================================
    # 5. LECTURAS PARA FACTORES
    # ==========================================
    pdf.set_text_color(255, 0, 0)
    pdf.set_font("Times", style="B")
    pdf.set_xy(10, y_pos)
    pdf.cell(190, 5, "5. LECTURAS PARA FACTORES DE CORRECCIÓN", align="C")

    y_pos += 7
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Times", style="")

    pdf.set_xy(40, y_pos)
    pdf.cell(50, 5, f"Presión: {datos.get('presion', '')} kPa")
    pdf.set_xy(117, y_pos + 1.5)
    pdf.write_html("k<sub>TP</sub> = Factor de corrección por presión = ")
    pdf.set_text_color(255, 0, 0)
    pdf.set_xy(165, y_pos)
    pdf.cell(20, 5, f"{datos.get('k_tp', '')}")

    pdf.set_text_color(0, 0, 0)
    y_pos += 6
    pdf.set_xy(40, y_pos)
    pdf.cell(50, 5, f"Temperatura: {datos.get('temperatura', '')} °C")

    y_pos += 7
    pdf.set_xy(40, y_pos)
    pdf.cell(50, 5, "Unidades Monitor: 100")

    y_pos += 7
    pdf.set_xy(40, y_pos)
    pdf.cell(50, 5, f"Electrómetro a +400 V (M+): {datos.get('m_plus', '')} nC")
    pdf.set_xy(130, y_pos + 1)
    pdf.write_html("k<sub>pol</sub> = Factor por polaridad = ")
    pdf.set_text_color(255, 0, 0)
    pdf.set_xy(165, y_pos)
    pdf.cell(20, 5, f"{datos.get('k_pol', '')}")

    pdf.set_text_color(0, 0, 0)
    y_pos += 6
    pdf.set_xy(40, y_pos)
    pdf.cell(50, 5, f"Electrómetro a -150 V (M2): {datos.get('m2', '')} nC")
    pdf.set_xy(126, y_pos + 1)
    pdf.write_html("k<sub>s</sub> = Factor por recombinación = ")
    pdf.set_text_color(255, 0, 0)
    pdf.set_xy(165, y_pos)
    pdf.cell(20, 5, f"{datos.get('k_s', '')}")

    pdf.set_text_color(0, 0, 0)
    y_pos += 6
    pdf.set_xy(40, y_pos)
    pdf.cell(50, 5, f"Electrómetro a -400 V (M1): {datos.get('m1', '')} nC")
    pdf.set_xy(145, y_pos + 3)
    pdf.write_html("donde: a<sub>0</sub>=2.337, a<sub>1</sub>=-3.636, a<sub>2</sub>=2.299")

    y_pos += 10  # Salto más notable para el resultado de P_Q
    pdf.set_text_color(0, 51, 153)
    pdf.set_font("Times", style="B")
    pdf.set_xy(80, y_pos)
    pdf.write_html(
        "P<sub>Q</sub> = k<sub>TP</sub> · k<sub>pol</sub> · k<sub>s</sub> · k<sub>elec</sub> = "
    )
    pdf.set_text_color(255, 0, 0)
    pdf.set_xy(111, y_pos - 1)
    pdf.cell(20, 5, f"{datos.get('p_q', '')}")

    # ==========================================
    # 6. CÁLCULO DE DOSIS
    # ==========================================
    y_pos += 8  # Salto grande de sección
    pdf.set_text_color(255, 0, 0)
    pdf.set_font("Times", style="B")
    pdf.set_xy(10, y_pos)
    pdf.cell(190, 5, "6. CÁLCULO DE DOSIS ABSORBIDA EN AGUA @ Zref", align="C")

    y_pos += 7
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Times", style="")
    pdf.set_xy(25, y_pos)
    pdf.cell(35, 5, "Lecturas para calibración:")

    col_l1, col_l2, col_l3, col_prom = 65, 85, 105, 125
    pdf.set_xy(col_l1, y_pos)
    pdf.cell(20, 4, "L1", align="C")
    pdf.set_xy(col_l2, y_pos)
    pdf.cell(20, 4, "L2", align="C")
    pdf.set_xy(col_l3, y_pos)
    pdf.cell(20, 4, "L3", align="C")
    pdf.set_font("Times", style="B")
    pdf.set_xy(col_prom, y_pos)
    pdf.cell(25, 4, "PROM", align="C")

    y_pos += 5
    pdf.set_font("Times", style="")
    pdf.set_xy(col_l1, y_pos)
    pdf.cell(20, 7, f"{datos.get('l1', '')}", border=1, align="C")
    pdf.set_xy(col_l2, y_pos)
    pdf.cell(20, 7, f"{datos.get('l2', '')}", border=1, align="C")
    pdf.set_xy(col_l3, y_pos)
    pdf.cell(20, 7, f"{datos.get('l3', '')}", border=1, align="C")

    pdf.set_text_color(255, 0, 0)
    pdf.set_font("Times", style="B")
    pdf.set_xy(col_prom, y_pos)
    pdf.cell(25, 7, f"{datos.get('prom', '')} nC", border=1, align="C")

    pdf.set_text_color(0, 51, 153)
    pdf.set_font("Times", style="")
    pdf.set_xy(152, y_pos + 1)
    pdf.write_html("este es M<sub>1</sub> para el cálculo")

    y_pos += 10
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(50, y_pos)
    pdf.write_html("Depende del TPR<sub>20,10</sub>. Tabla 14, p. 84-87: ")
    pdf.set_text_color(255, 0, 0)
    pdf.set_font("Times", style="B")
    pdf.set_xy(97, y_pos - 1)
    pdf.cell(15, 5, f"{datos.get('k_qq0', '')}", align="C")
    pdf.set_text_color(0, 51, 153)
    pdf.set_font("Times", style="")
    pdf.set_xy(110, y_pos)
    pdf.write_html("k<sub>Q,Q0</sub> Factor de Calidad")

    y_pos += 8
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Times", style="I")
    pdf.set_xy(55, y_pos)
    pdf.write_html(
        "D<sub>w,Q</sub>(Z<sub>ref</sub>) = M<sub>1</sub> · P<sub>Q</sub> · N<sub>D,w,Q0</sub> · k<sub>Q,Q0</sub> = "
    )
    pdf.set_text_color(255, 0, 0)
    pdf.set_font("Times", style="B")
    pdf.set_xy(95, y_pos - 1)
    pdf.cell(20, 5, f"{datos.get('dw_q_zref', '')}", align="C")
    pdf.set_text_color(0, 51, 153)
    pdf.set_font("Times", style="")
    pdf.set_xy(110, y_pos)
    pdf.write_html("cGy/UM Dosis Absorbida a Z<sub>ref</sub>")

    # ==========================================
    # 7. CÁLCULO DE DOSIS ZMAX
    # ==========================================
    y_pos += 8  # Salto grande de sección
    pdf.set_text_color(255, 0, 0)
    pdf.set_font("Times", style="B")
    pdf.set_xy(10, y_pos)
    pdf.cell(190, 5, "7. CÁLCULO DE DOSIS ABSORBIDA EN AGUA @ Zmáx", align="C")

    y_pos += 7
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Times", style="")
    pdf.set_xy(65, y_pos)
    pdf.cell(40, 5, f"Zmáx = {datos.get('zmax_sec7', '')} mm")
    pdf.set_xy(120, y_pos)
    pdf.cell(40, 5, f"PDD @ Zref = {datos.get('pdd_zref', '')}")

    # === APAGAR EL SALTO DE PÁGINA AUTOMÁTICO ===
    pdf.set_auto_page_break(False)

    y_pos += 8
    box_x, box_y, box_w, box_h = 57, y_pos, 100, 14  # Tu caja
    pdf.set_line_width(0.5)
    pdf.rect(box_x, box_y, box_w, box_h)
    pdf.set_line_width(0.2)

    pdf.set_text_color(180, 0, 0)
    pdf.set_font("Times", style="B")

    # --- Fórmula y resultado ---
    pdf.set_font("Times", size=7, style="B")
    pdf.set_xy(box_x + 5, box_y + 2)
    pdf.write_html("D<sub>w,Q</sub>(Zmax) = D<sub>w,Q</sub>(Zref) / PDD =")
    pdf.set_xy(box_x + 67, box_y + 2)
    pdf.cell(16, 5, f"{datos.get('dw_q_zmax', '')}", align="C")
    pdf.set_xy(box_x + 83, box_y + 2)
    pdf.cell(14, 5, "cGy/UM", align="C")

    # --- TIPO DE RADIACIÓN (FOTONES o ELECTRONES) ---
    pdf.set_text_color(255, 0, 0)
    pdf.set_xy(box_x, box_y + 8)
    pdf.cell(box_w, 5, f"{datos.get('tipo_radiacion', 'FOTONES')}", align="C")

    # --- Letras azules a la derecha ---
    pdf.set_text_color(0, 51, 153)
    pdf.set_font("Times", style="")
    pdf.set_xy(box_x + box_w + 3, box_y + 1)
    pdf.cell(40, 4, "Dosis Absorbida a la")
    pdf.set_xy(box_x + box_w + 3, box_y + 5)
    pdf.cell(40, 4, "prof. de máxima")
    pdf.set_xy(box_x + box_w + 3, box_y + 9)
    pdf.cell(40, 4, "ionización")

    # Volver a activarlo
    pdf.set_auto_page_break(True, margin=15)

    # Guardar documento
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output))
    return output


def generar_reporte(
    datos: Mapping[str, object], nombre_archivo: str | Path = "reporte_final.pdf"
) -> Path:
    """Backward-compatible Spanish alias."""

    return generate_calibration_report(datos, nombre_archivo)
