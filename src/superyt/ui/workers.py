import sys
import threading

from PySide6.QtCore import QThread, Signal

from superyt.downloader import Cancelled, download_one, inspect_video
from superyt.releases import UpdateCancelled
from superyt.updater import update_windows


class DownloadWorker(QThread):
    event = Signal(object)

    def __init__(self, items, tools, parent=None):
        super().__init__(parent)
        self.items = tuple(items)
        self.tools = tools
        self.cancel_event = threading.Event()

    def run(self):
        for item in self.items:
            if self.cancel_event.is_set():
                break
            download_one(item, item.options, self.tools, self.cancel_event, self.event.emit)

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
            if sys.platform == "darwin":
                from superyt.mac_updater import update_macos

                changed = update_macos(self.cancel_event, self.progress.emit)
            else:
                changed = update_windows(self.cancel_event, self.progress.emit)
            self.result.emit(changed)
        except UpdateCancelled:
            self.error.emit("Preparación cancelada. Se conserva la versión anterior.")
        except Exception as exc:
            self.error.emit(str(exc))

    def cancel(self):
        self.cancel_event.set()


class AppUpdateWorker(QThread):
    result = Signal(object)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, info=None, parent=None):
        super().__init__(parent)
        self.info = info
        self.cancel_event = threading.Event()

    def run(self):
        from superyt.app_update import check_release, fetch_installer

        try:
            value = (fetch_installer(self.info, self.cancel_event, self.progress.emit)
                     if self.info else check_release(self.cancel_event))
            self.result.emit(value)
        except Exception as exc:
            self.error.emit(str(exc))

    def cancel(self):
        self.cancel_event.set()
