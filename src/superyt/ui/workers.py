import threading

from PySide6.QtCore import QThread, Signal

from superyt.downloader import Cancelled, download_one, inspect_video
from superyt.releases import UpdateCancelled
from superyt.updater import update_windows


class DownloadWorker(QThread):
    event = Signal(object)

    def __init__(self, items, options, tools, parent=None):
        super().__init__(parent)
        self.items = tuple(items)
        self.options = options
        self.tools = tools
        self.cancel_event = threading.Event()

    def run(self):
        for item in self.items:
            if self.cancel_event.is_set():
                break
            download_one(item, self.options, self.tools, self.cancel_event, self.event.emit)

    def cancel(self):
        self.cancel_event.set()


class InspectWorker(QThread):
    result = Signal(object)
    error = Signal(str)

    def __init__(self, url, tools, parent=None):
        super().__init__(parent)
        self.url = url
        self.tools = tools
        self.cancel_event = threading.Event()

    def run(self):
        try:
            self.result.emit(inspect_video(self.url, self.tools, self.cancel_event))
        except Cancelled:
            pass
        except Exception as exc:
            self.error.emit(str(exc))

    def cancel(self):
        self.cancel_event.set()


class UpdateWorker(QThread):
    progress = Signal(str)
    result = Signal(bool)
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cancel_event = threading.Event()

    def run(self):
        try:
            self.result.emit(update_windows(self.cancel_event, self.progress.emit))
        except UpdateCancelled:
            self.error.emit("Preparación cancelada. Se conserva la versión anterior.")
        except Exception as exc:
            self.error.emit(str(exc))

    def cancel(self):
        self.cancel_event.set()
