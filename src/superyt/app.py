import logging
import sys
from logging.handlers import RotatingFileHandler

from PySide6.QtWidgets import QApplication

from .settings import Settings, data_dir
from .ui.main_window import MainWindow
from .ui.theme import STYLE


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("SuperYTDownloader")
    app.setOrganizationName("SuperYTDownloader")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    try:
        folder = data_dir()
        folder.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            folder / "superyt.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8"
        )
        logging.basicConfig(
            level=logging.INFO, handlers=[handler], format="%(asctime)s %(levelname)s %(message)s"
        )
    except OSError:
        logging.basicConfig(level=logging.INFO)
    window = MainWindow(Settings.load())
    window.show()
    return app.exec()
