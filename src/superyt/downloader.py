"""Process execution independent of Qt. All commands use argument lists, never a shell."""

import json
import os
import queue
import signal
import subprocess
import threading
import time
from collections import deque
from collections.abc import Callable

from .formats import base_arguments, download_arguments, normalize_url, parse_event
from .models import DownloadEvent, DownloadItem, DownloadOptions
from .tools import Tools, subprocess_options


class Cancelled(Exception):
    pass


def terminate_tree(process: subprocess.Popen) -> None:
    if os.name == "nt":
        # /T also stops FFmpeg and JavaScript runtime children.
        try:
            subprocess.run(
                ["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=8,
                **subprocess_options(),
            )
        except (OSError, subprocess.TimeoutExpired):
            pass
        if process.poll() is None:
            process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=5)


def run_process(
    command: list[str],
    cancel: threading.Event,
    on_line: Callable[[str], None],
    timeout: float | None = None,
) -> int:
    if cancel.is_set():
        raise Cancelled
    extra = subprocess_options()
    if os.name != "nt":
        extra["start_new_session"] = True
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        **extra,
    )
    lines: queue.Queue[str | None] = queue.Queue()

    def read_output():
        try:
            for line in process.stdout:
                lines.put(line.rstrip("\r\n"))
        finally:
            lines.put(None)

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    start = time.monotonic()
    ended = False
    try:
        while not ended or process.poll() is None:
            if cancel.is_set():
                raise Cancelled
            if timeout is not None and time.monotonic() - start > timeout:
                raise TimeoutError(
                    "La consulta tardó demasiado. Comprueba la conexión y vuelve a intentarlo."
                )
            try:
                line = lines.get(timeout=0.1)
            except queue.Empty:
                continue
            if line is None:
                ended = True
            else:
                on_line(line)
        return process.wait()
    finally:
        # Also kill descendants if a timeout/cancellation happened after the parent exited.
        if not ended or process.poll() is None:
            terminate_tree(process)
        reader.join(timeout=2)
        process.stdout.close()


def download_one(
    item: DownloadItem,
    options: DownloadOptions,
    tools: Tools,
    cancel: threading.Event,
    emit: Callable[[DownloadEvent], None],
) -> None:
    def event(kind, value):
        emit(DownloadEvent(item.id, kind, value))

    errors: deque[str] = deque(maxlen=8)

    def on_line(line):
        parsed = parse_event(line)
        if parsed:
            event(*parsed)
        elif line:
            errors.append(line)
            event("log", line)
            if line.startswith(("[Merger]", "[ExtractAudio]", "[VideoConvertor]", "[Fixup")):
                event("status", "Procesando")

    event("status", "Consultando")
    try:
        result = run_process(
            [str(tools.yt_dlp), *download_arguments(item.url, options, tools)], cancel, on_line
        )
        if cancel.is_set():
            raise Cancelled
        if result:
            raise RuntimeError("\n".join(errors) or f"yt-dlp terminó con código {result}.")
    except Cancelled:
        event("status", "Cancelado")
    except Exception as exc:
        event("error", str(exc))
    else:
        event("status", "Completado")


def inspect_video(url: str, tools: Tools, cancel: threading.Event) -> dict:
    metadata = None
    errors: deque[str] = deque(maxlen=6)

    def on_line(line):
        nonlocal metadata
        if line.startswith("{"):
            try:
                metadata = json.loads(line)
            except ValueError:
                errors.append(line[:500])
        elif line:
            errors.append(line)

    result = run_process(
        [
            str(tools.yt_dlp),
            *base_arguments(tools),
            "--dump-single-json",
            "--skip-download",
            "--",
            normalize_url(url),
        ],
        cancel,
        on_line,
        timeout=90,
    )
    if result or not isinstance(metadata, dict):
        raise RuntimeError("\n".join(errors) or "No se pudieron consultar los formatos.")
    return metadata
