import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from superyt.models import DownloadEvent
from superyt.settings import Settings
from superyt.tools import Tools
from superyt.ui.main_window import MainWindow
from superyt.ui.theme import STYLE


@pytest.fixture(scope="module")
def app():
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(STYLE)
    return app


@pytest.fixture
def window(app, tmp_path, monkeypatch):
    monkeypatch.setattr(Settings, "save", lambda *_: None)
    widget = MainWindow(Settings(destination=str(tmp_path)))
    yield widget
    widget.close()
    widget.deleteLater()
    app.processEvents()


def test_removing_rows_removes_actual_downloads(window):
    window.add_links(["youtu.be/abc", "youtu.be/def"])
    window.table.selectRow(0)
    window.remove_selected()
    assert len(window.items) == window.table.rowCount() == 1
    assert window.items[0].url.endswith("v=def")


def test_deduplicates_different_youtube_link_forms(window):
    window.add_links(["youtu.be/abc", "https://youtube.com/watch?v=abc&list=123"])
    assert len(window.items) == 1


def test_mode_controls_and_error_recovery(window):
    window.mode.setCurrentIndex(window.mode.findData("mp3"))
    assert window.bitrate.isEnabled()
    assert not window.height.isEnabled()
    window.add_links(["youtu.be/abc"])
    window.on_event(DownloadEvent(window.items[0].id, "error", "Video unavailable"))
    window.update_controls()
    assert window.items[0].status == "Error"
    assert window.retry_button.isEnabled()
    assert "Video unavailable" in window.table.item(0, 2).toolTip()


def test_full_queue_continues_after_failed_item(app, window, tmp_path, monkeypatch):
    script = tmp_path / "fake_downloader.py"
    script.write_text(
        "import sys\n"
        "if sys.argv[1].endswith('v=bad'):\n"
        "    print('ERROR: unavailable')\n"
        "    sys.exit(1)\n"
        "print('SUPER_YT:title:\"Example\"')\n"
        "print('SUPER_YT:path:\"output.mp4\"')\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "superyt.ui.main_window.resolve_tools",
        lambda *a, **kw: Tools(Path(sys.executable), None, None),
    )
    monkeypatch.setattr("superyt.downloader.download_arguments", lambda url, *_: [str(script), url])
    window.add_links(["youtu.be/bad", "youtu.be/good"])
    window.start_downloads()
    deadline = time.monotonic() + 10
    while window.worker is not None and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert window.worker is None
    assert [i.status for i in window.items] == ["Error", "Completado"]
    assert window.retry_button.isEnabled()
    assert window.table.cellWidget(1, 3).value() == 100


@pytest.fixture
def update_ui(window, monkeypatch):
    from types import SimpleNamespace

    from PySide6.QtCore import QObject, Signal

    class ControlledUpdateWorker(QObject):
        progress = Signal(str)
        result = Signal(bool)
        error = Signal(str)
        finished = Signal()

        def __init__(self, parent):
            super().__init__(parent)
            import threading

            self.cancel_event = threading.Event()

        def start(self):
            self.progress.emit("Buscando actualizaciones…")

        def cancel(self):
            self.cancel_event.set()

    monkeypatch.setattr("superyt.ui.main_window.sys", SimpleNamespace(platform="win32"))
    monkeypatch.setattr("superyt.ui.main_window.UpdateWorker", ControlledUpdateWorker)
    yield window
    if window.updater is not None:
        window.updater.finished.emit()
    window.worker = None
    window.probe = None


def test_update_disables_media_actions_but_keeps_queue_editing_available(update_ui):
    window = update_ui
    window.add_links(["youtu.be/one"])
    window.request_update()
    assert window.updater is not None
    assert not window.download_button.isEnabled()
    assert not window.update_button.isEnabled()
    window.add_links(["youtu.be/two"])
    assert len(window.items) == 2
    window.updater.result.emit(True)
    window.updater.finished.emit()
    assert window.updater is None
    assert window.download_button.isEnabled()
    assert window.update_button.isEnabled()


def test_update_is_deferred_until_download_ends(update_ui, app):
    from PySide6.QtCore import QObject

    window = update_ui
    window.worker = QObject(window)
    window.request_update()
    assert window.update_pending
    assert window.updater is None
    window.downloads_finished()
    app.processEvents()
    assert window.updater is not None
    assert not window.update_pending


def test_missing_components_trigger_preparation_then_resume_requested_download(
    update_ui, monkeypatch, app
):
    window = update_ui
    window.add_links(["youtu.be/one"])

    def missing(**kwargs):
        raise ValueError("missing")

    monkeypatch.setattr("superyt.ui.main_window.resolve_tools", missing)
    window.start_downloads()
    assert window.updater is not None
    assert window.start_after_update
    resumed = []
    monkeypatch.setattr(window, "start_downloads", lambda: resumed.append(True))
    window.updater.result.emit(True)
    window.updater.finished.emit()
    app.processEvents()
    assert resumed == [True]


def test_failed_update_keeps_download_action_usable(update_ui, monkeypatch):
    window = update_ui
    window.add_links(["youtu.be/one"])
    monkeypatch.setattr("superyt.ui.main_window.resolve_tools", lambda: object())
    window.request_update()
    window.updater.error.emit("offline")
    window.updater.finished.emit()
    assert "versión instalada" in window.notice.text()
    assert window.download_button.isEnabled()


def test_startup_respects_daily_check(update_ui, monkeypatch):
    window = update_ui
    monkeypatch.setattr("superyt.ui.main_window.update_due", lambda: False)
    window.startup_update()
    assert window.updater is None
    monkeypatch.setattr("superyt.ui.main_window.update_due", lambda: True)
    window.startup_update()
    assert window.updater is not None
