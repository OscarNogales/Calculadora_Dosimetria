"""Build the Flet interface as an Android APK using the official CLI."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    flet_command = shutil.which("flet")
    if not flet_command:
        raise SystemExit(
            "No se encontró el comando 'flet'. Instala las dependencias con "
            "'pip install -e .' antes de compilar."
        )

    command = [
        flet_command,
        "build",
        "apk",
        str(project_root),
        "--project",
        "dosimetry_calculator",
        "--product",
        "Dosimetría",
        "--artifact",
        "dosimetry-calculator",
        "--yes",
    ]
    subprocess.run(command, cwd=project_root, check=True)


if __name__ == "__main__":
    main()
