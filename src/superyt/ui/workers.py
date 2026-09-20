import threading
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from superyt.downloader import Cancelled, download_one, inspect_video
from superyt.tools import executable_name, resolve_tool, tool_version


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


class ToolWorker(QThread):
    result = Signal(str, str)

    def __init__(self, overrides, parent=None):
        super().__init__(parent)
        self.overrides = dict(overrides)

    def run(self):
        for name in ("yt-dlp", "ffmpeg", "ffprobe", "deno"):
            if self.isInterruptionRequested():
                return
            if name == "ffprobe":
                ffmpeg = resolve_tool("ffmpeg", self.overrides)
                path = ffmpeg.with_name(executable_name(name)) if ffmpeg else None
            else:
                path = resolve_tool(name, self.overrides)
            try:
                version = (
                    tool_version(Path(path), name) if path and path.is_file() else "No encontrado"
                )
                self.result.emit(
                    name,
                    f"{version}\n{path or 'Coloca el ejecutable en bin/ o configura su ruta.'}",
                )
            except Exception as exc:
                self.result.emit(name, f"No se pudo ejecutar: {exc}")
