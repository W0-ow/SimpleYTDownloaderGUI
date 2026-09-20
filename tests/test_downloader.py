import sys
import threading
import time
from pathlib import Path

import pytest

from superyt.downloader import Cancelled, download_one, inspect_video, run_process
from superyt.models import DownloadItem, DownloadOptions
from superyt.tools import Tools


def test_process_captures_unicode_and_real_exit_status():
    lines = []
    code = run_process(
        [sys.executable, "-X", "utf8", "-c", "print('Canción 日本語'); raise SystemExit(7)"],
        threading.Event(),
        lines.append,
    )
    assert code == 7
    assert lines == ["Canción 日本語"]


def test_cancel_silent_process_without_waiting_for_output():
    cancel = threading.Event()
    timer = threading.Timer(0.25, cancel.set)
    timer.start()
    start = time.monotonic()
    try:
        with pytest.raises(Cancelled):
            run_process(
                [sys.executable, "-c", "import time; time.sleep(60)"], cancel, lambda _: None
            )
    finally:
        timer.join()
    assert time.monotonic() - start < 10


def test_timeout_silent_process():
    with pytest.raises(TimeoutError):
        run_process(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            threading.Event(),
            lambda _: None,
            timeout=0.2,
        )


@pytest.mark.parametrize("exit_code,expected", [(0, "Completado"), (1, "Error")])
def test_download_success_and_failure_are_distinct(tmp_path, monkeypatch, exit_code, expected):
    script = tmp_path / "fake.py"
    script.write_text(
        "print('SUPER_YT:title:\"Title\"')\n"
        'print(\'SUPER_YT:progress:{"downloaded":50,"total":100}\')\n'
        f"print('ERROR: unavailable' if {exit_code} else 'SUPER_YT:path:\"out.mp4\"')\n"
        f"raise SystemExit({exit_code})",
        encoding="utf-8",
    )
    monkeypatch.setattr("superyt.downloader.download_arguments", lambda *_: [str(script)])
    events = []
    download_one(
        DownloadItem("youtu.be/abc"),
        DownloadOptions(tmp_path),
        Tools(Path(sys.executable), None, None),
        threading.Event(),
        events.append,
    )
    if expected == "Completado":
        assert events[-1].kind == "status" and events[-1].value == expected
    else:
        assert events[-1].kind == "error"
        assert "unavailable" in events[-1].value
        assert not any(e.value == "Completado" for e in events)
    assert any(e.kind == "progress" for e in events)


def test_metadata_is_parsed_even_with_warnings(monkeypatch):
    def fake_run(command, cancel, on_line, timeout):
        on_line("WARNING: an extractor warning")
        on_line('{"title":"Example","formats":[{"height":720}]}')
        return 0

    monkeypatch.setattr("superyt.downloader.run_process", fake_run)
    result = inspect_video("youtu.be/abc", Tools(Path("yt-dlp"), None, None), threading.Event())
    assert result["formats"][0]["height"] == 720


def test_cancellation_also_stops_child_process(tmp_path):
    marker = tmp_path / "child-survived.txt"
    child_code = (
        f"import time; from pathlib import Path; time.sleep(1.5); Path({str(marker)!r}).touch()"
    )
    parent_code = (
        "import subprocess, sys, time; "
        f"subprocess.Popen([sys.executable, '-c', {child_code!r}]); "
        "print('ready', flush=True); time.sleep(60)"
    )
    cancel = threading.Event()
    with pytest.raises(Cancelled):
        run_process([sys.executable, "-c", parent_code], cancel, lambda _: cancel.set())
    time.sleep(1.7)
    assert not marker.exists()
