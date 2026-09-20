"""Render the repository's SVG icon for the Windows executable."""

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

app = QApplication([])
root = Path(__file__).resolve().parents[1]
(root / "build").mkdir(exist_ok=True)
icon = QIcon(str(root / "src/superyt/assets/app.svg"))
if not icon.pixmap(128, 128).save(str(root / "build/app.ico"), "ICO"):
    raise SystemExit("No se pudo generar el icono ICO")
