# Calculadora de Dosimetría

[English version](README.md)

Aplicación multiplataforma en Python para apoyar cálculos de dosimetría de dosis absoluta. El proyecto incluye una interfaz en español desarrollada con Flet para Android, escritorio y web; una interfaz de escritorio en CustomTkinter; almacenamiento local; generación de reportes PDF; y pruebas automatizadas para la lógica de cálculo.

## Aviso clínico importante

Este repositorio es una herramienta educativa y de apoyo al flujo de trabajo. **No es un dispositivo médico certificado** y no debe utilizarse como la única base para tratamientos de pacientes, calibración de equipos o decisiones clínicas. Cada fórmula, factor de calibración, coeficiente de cámara, corrección ambiental, convención de PDD, unidad y reporte generado debe validarse de manera independiente contra el protocolo vigente de la institución, los certificados de calibración, el programa de garantía de calidad y la revisión de un físico médico calificado.

## Funciones principales

- Motor de cálculo compartido por las interfaces móvil y de escritorio.
- Factor de corrección por temperatura y presión (`k_tp`).
- Factor de corrección por polaridad (`k_pol`).
- Factor de corrección por recombinación iónica (`k_s`).
- Factor combinado de corrección (`P_Q`).
- Dosis a la profundidad de referencia y dosis opcional corregida por PDD.
- PDD aceptado como fracción (`0.67`) o porcentaje (`67`).
- Almacenamiento local de mediciones, constantes de calibración, tema y datos del equipo.
- Reporte de calibración en PDF y en español.
- Seis temas visuales en la interfaz Flet.
- Pruebas automatizadas de fórmulas, persistencia, datos del reporte, PDF e importaciones.

## Estructura del proyecto

```text
dosimetry-calculator/
├── assets/                         # Iconos de la aplicación
├── config/
│   └── example_settings.json       # Ejemplo de configuración sin secretos
├── docs/
│   ├── REFACTOR_NOTES.md           # Cambios principales de arquitectura
│   └── sample_reports/             # PDFs originales de ejemplo
├── scripts/
│   └── build_android.py            # Compilación oficial de APK con Flet
├── src/dosimetry_app/
│   ├── calculations.py             # Cálculos científicos puros
│   ├── calculator.py               # Adaptador con estado para las interfaces
│   ├── models.py                   # Mediciones, constantes y resultados tipados
│   ├── settings.py                 # Configuración y migración de datos antiguos
│   ├── storage.py                  # Persistencia JSON atómica
│   ├── mobile/                     # Interfaz Flet y temas
│   ├── desktop/                    # Interfaz CustomTkinter
│   └── reporting/                  # Preparación de datos y generación del PDF
├── tests/                          # Pruebas automatizadas
├── main.py                         # Entrada para Flet y Android
├── run_desktop.py                  # Entrada para escritorio
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

## Requisitos

- Python 3.11 o posterior.
- Para compilar Android también se necesitan las herramientas que Flet y Flutter descargan y configuran.

Las dependencias principales están fijadas en `pyproject.toml` y `requirements.txt` para que la instalación sea reproducible.

## Instalación

```bash
python -m venv .venv
```

Activa el entorno:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS o Linux
source .venv/bin/activate
```

Instala la aplicación y las herramientas de desarrollo:

```bash
pip install -e ".[dev]"
```

## Ejecutar la interfaz Flet

```bash
python main.py
```

Después de instalar el proyecto en modo editable también puedes usar:

```bash
dosimetry-mobile
```

La interfaz se conserva en español porque está pensada para un flujo de trabajo operativo en español.

## Ejecutar la interfaz de escritorio

```bash
python run_desktop.py
```

O:

```bash
dosimetry-desktop
```

La interfaz de escritorio incluye datos del equipo, tres lecturas oficiales y generación del reporte PDF.

## Compilar el APK de Android

Usa el script incluido:

```bash
python scripts/build_android.py
```

También puedes llamar directamente a la herramienta oficial de Flet:

```bash
flet build apk . --project dosimetry_calculator --product "Dosimetría" --artifact dosimetry-calculator --yes
```

El APK se guarda dentro del directorio de compilación creado por Flet. Antes de distribuir la aplicación debes configurar el identificador final del paquete, la firma, la organización y los metadatos de publicación.

## Ejecutar las pruebas

```bash
pytest
```

Con cobertura:

```bash
pytest --cov=dosimetry_app --cov-report=term-missing
```

Revisión de estilo:

```bash
ruff check .
ruff format --check .
```

Para aplicar el formato automáticamente:

```bash
ruff format .
```

## Flujo de cálculo

Las interfaces reciben:

- Temperatura ambiente `T` en °C.
- Presión ambiente `P` en kPa.
- Lectura de referencia `M1` en nC.
- Lectura con polaridad opuesta `M+` en nC.
- Lectura para recombinación `M2` en nC.
- PDD opcional como fracción o porcentaje.
- `N_D,w,Q0`, `k_Q,Q0`, temperatura de referencia, presión de referencia y `k_elec`.

El motor compartido calcula:

```text
k_tp = ((T + 273.15) / (T_ref + 273.15)) * (P_ref / P)

k_pol = (|M1| + |M+|) / (2 * |M1|)

k_s = a0 + a1 * (M1 / M2) + a2 * (M1 / M2)^2
donde a0 = 2.337, a1 = -3.636 y a2 = 2.299

P_Q = k_tp * k_pol * k_s * k_elec

D(zref) = |M1| * P_Q * N_D,w,Q0 * k_Q,Q0

D(zmax) = D(zref) / PDD
```

Antes de dividir, el motor valida números finitos, denominadores distintos de cero, constantes positivas, presión físicamente válida y límites correctos para el PDD.

## Datos almacenados

La aplicación guarda el estado local fuera del código fuente:

- Flet utiliza `FLET_APP_STORAGE_DATA` cuando el entorno empaquetado lo proporciona.
- Windows utiliza el directorio de datos de aplicación del usuario.
- macOS utiliza `~/Library/Application Support`.
- Linux utiliza `XDG_DATA_HOME` o `~/.local/share`.

Solamente se guardan entradas y configuraciones. Los resultados se vuelven a calcular al iniciar la aplicación.

## Compatibilidad con la versión anterior

El repositorio de configuración migra las claves JSON originales en español, como `tema_usuario`, `marca`, `modelo`, `camara` y `electrometro`, hacia la nueva estructura. Las clases `Calculator` duplicadas ya no se utilizan.

## Contribuciones

Antes de abrir un pull request:

1. Agrega o actualiza pruebas para cualquier cambio en los cálculos.
2. Ejecuta `pytest` y `ruff check .`.
3. Documenta cualquier cambio que afecte unidades, signos, interpretación del PDD, coeficientes o el reporte.
4. Obtén una revisión clínica independiente para cambios en el comportamiento científico.

## Licencia

Todavía no se ha seleccionado una licencia de código abierto. Agrega un archivo de licencia antes de permitir redistribución o contribuciones externas.
