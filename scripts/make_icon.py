"""Render the repository SVG as a multi-size Windows executable icon."""

from io import BytesIO
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

root = Path(__file__).resolve().parents[1]
source = root / "src/superyt/assets/app.svg"
image = QImage(256, 256, QImage.Format.Format_ARGB32)
image.fill(0)
renderer = QSvgRenderer(str(source))
if not renderer.isValid():
    raise SystemExit(f"No se pudo leer el icono: {source}")
painter = QPainter(image)
renderer.render(painter)
painter.end()

png = QByteArray()
buffer = QBuffer(png)
if not buffer.open(QIODevice.OpenModeFlag.WriteOnly) or not image.save(buffer, "PNG"):
    raise SystemExit("No se pudo generar el PNG del icono")
buffer.close()
(root / "build").mkdir(exist_ok=True)
Image.open(BytesIO(png.data())).save(
    root / "build/app.ico",
    format="ICO",
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
