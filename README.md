# Dosimetry Calculator

[Versión en español](README_ES.md)

A cross-platform Python application for supporting absolute-dose dosimetry calculations. The project includes a Spanish Flet interface for Android/desktop/web, a Spanish CustomTkinter desktop interface, local persistence, PDF report generation, and automated tests for the calculation layer.

## Important clinical disclaimer

This repository is an educational and workflow-support tool. It is **not a certified medical device** and must not be used as the sole basis for patient treatment, machine calibration, or clinical decision-making. Every formula, calibration factor, chamber coefficient, environmental correction, PDD convention, unit, and generated report must be independently validated against the institution's current protocol, calibration certificates, quality-assurance program, and review by a qualified medical physicist.

## Main features

- Shared calculation engine for the mobile and desktop interfaces.
- Temperature-pressure correction factor (`k_tp`).
- Polarity correction factor (`k_pol`).
- Ion-recombination correction factor (`k_s`).
- Combined correction factor (`P_Q`).
- Dose at the reference depth and optional PDD-corrected dose.
- PDD input accepted as either a fraction (`0.67`) or percentage (`67`).
- Local storage for measurements, calibration constants, theme, and equipment data.
- Spanish PDF calibration report.
- Six visual themes in the Flet interface.
- Automated unit, persistence, report-data, PDF, and import tests.

## Project structure

```text
dosimetry-calculator/
├── assets/                         # Application icons
├── config/
│   └── example_settings.json       # Example non-secret settings
├── docs/
│   ├── REFACTOR_NOTES.md           # Main architectural and behavior changes
│   └── sample_reports/             # Original sample PDFs
├── scripts/
│   └── build_android.py            # Official Flet APK build command
├── src/dosimetry_app/
│   ├── calculations.py             # Pure scientific calculations
│   ├── calculator.py               # Stateful adapter for the interfaces
│   ├── models.py                   # Typed measurements, constants, and results
│   ├── settings.py                 # Shared settings and legacy migration
│   ├── storage.py                  # Atomic JSON persistence
│   ├── mobile/                     # Flet interface and themes
│   ├── desktop/                    # CustomTkinter interface
│   └── reporting/                  # Report data mapping and PDF rendering
├── tests/                          # Automated tests
├── main.py                         # Flet/mobile entry point
├── run_desktop.py                  # Desktop entry point
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

## Requirements

- Python 3.11 or newer.
- Android builds additionally require the tools downloaded and configured by Flet/Flutter.

The repository pins the main dependencies to reproducible versions in `pyproject.toml` and `requirements.txt`.

## Installation

```bash
python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS or Linux
source .venv/bin/activate
```

Install the application and development tools:

```bash
pip install -e ".[dev]"
```

## Run the Flet interface

```bash
python main.py
```

After editable installation, the same interface can be launched with:

```bash
dosimetry-mobile
```

The interface text remains in Spanish because the intended operational workflow is Spanish-speaking.

## Run the desktop interface

```bash
python run_desktop.py
```

Or:

```bash
dosimetry-desktop
```

The desktop interface includes equipment metadata, three official readings, and PDF report generation.

## Build the Android APK

Use the included script:

```bash
python scripts/build_android.py
```

Or call the official Flet CLI directly:

```bash
flet build apk . --project dosimetry_calculator --product "Dosimetría" --artifact dosimetry-calculator --yes
```

The APK is written under the build output directory created by Flet. Configure the final bundle ID, signing keystore, organization, and release metadata before distributing the application.

## Run the tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=dosimetry_app --cov-report=term-missing
```

Run the linter and formatter checks:

```bash
ruff check .
ruff format --check .
```

To apply formatting:

```bash
ruff format .
```

## Calculation flow

The interfaces collect:

- Ambient temperature `T` in °C.
- Ambient pressure `P` in kPa.
- Reference reading `M1` in nC.
- Opposite-polarity reading `M+` in nC.
- Recombination reading `M2` in nC.
- Optional PDD as a fraction or percentage.
- `N_D,w,Q0`, `k_Q,Q0`, reference temperature, reference pressure, and `k_elec`.

The shared engine calculates:

```text
k_tp = ((T + 273.15) / (T_ref + 273.15)) * (P_ref / P)

k_pol = (|M1| + |M+|) / (2 * |M1|)

k_s = a0 + a1 * (M1 / M2) + a2 * (M1 / M2)^2
where a0 = 2.337, a1 = -3.636, and a2 = 2.299

P_Q = k_tp * k_pol * k_s * k_elec

D(zref) = |M1| * P_Q * N_D,w,Q0 * k_Q,Q0

D(zmax) = D(zref) / PDD
```

The calculation engine validates finite numbers, non-zero denominators, positive reference constants, physically valid pressure, and PDD bounds before performing divisions.

## Stored data

The app stores local user state outside the source tree:

- Flet uses `FLET_APP_STORAGE_DATA` when the packaged environment provides it.
- Windows uses the user's application-data directory.
- macOS uses `~/Library/Application Support`.
- Linux uses `XDG_DATA_HOME` or `~/.local/share`.

Only inputs and settings are persisted. Calculated values are recomputed when the application starts.

## Legacy compatibility

The settings repository migrates the original Spanish JSON keys such as `tema_usuario`, `marca`, `modelo`, `camara`, and `electrometro` into the new nested settings structure. The old duplicated `Calculator` classes are no longer used.

## Contributing

Before opening a pull request:

1. Add or update tests for calculation changes.
2. Run `pytest` and `ruff check .`.
3. Document any change that may affect units, signs, PDD interpretation, coefficients, or the report.
4. Obtain independent clinical review for scientific behavior changes.

## License

No open-source license has been selected yet. Add a license file before inviting external redistribution or contributions.
