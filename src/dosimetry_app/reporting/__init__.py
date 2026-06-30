"""PDF report generation."""

from .data import average_readings, build_report_data
from .pdf_report import generar_reporte, generate_calibration_report

__all__ = [
    "average_readings",
    "build_report_data",
    "generate_calibration_report",
    "generar_reporte",
]
