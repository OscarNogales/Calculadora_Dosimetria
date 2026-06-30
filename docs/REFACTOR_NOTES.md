# Refactor notes

## Main changes

- Moved every formula into `src/dosimetry_app/calculations.py`.
- Replaced the duplicated `Calculator` classes with one `DosimetryCalculator`.
- Added typed dataclasses for measurements, constants, and results.
- Added explicit validation before division and before persistence.
- Fixed the zero-PDD bug in the Android implementation.
- PDD now accepts either a fraction (`0.67`) or a percentage (`67`).
- Separated mobile UI, desktop UI, persistence, settings, PDF data mapping, and PDF rendering.
- Replaced the machine-specific Flet build workaround with the official CLI.
- Added automated tests for formulas, persistence, report data, and PDF generation.

## Calculation behavior that must be reviewed clinically

The shared core uses the magnitude of the reference electrometer reading when reporting absorbed dose. This prevents a negative dose when a signed reading is entered, while polarity is still handled by `k_pol`. Confirm this convention against the institution's active protocol before clinical use.

The generated report remains a software aid. It is not a substitute for an independently validated worksheet, chamber certificate, local quality-assurance program, or qualified medical physicist review.
