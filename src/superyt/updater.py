"""Windows tool installation: stage, verify, validate, then atomically activate."""

import json
import logging
import math
import os
import platform
import re
import shutil
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from .releases import check_cancel, file_hash, install_component, windows_components
from .settings import data_dir

WINDOWS_FILES = ("yt-dlp.exe", "ffmpeg.exe", "ffprobe.exe", "deno.exe")


def store_root() -> Path:
    return data_dir() / "tools"


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def write_json(path: Path, value: dict):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def active_directory(root: Path | None = None) -> Path | None:
    root = root or store_root()
    generation = read_json(root / "current.json").get("generation", "")
    if not isinstance(generation, str) or not re.fullmatch(r"[a-f0-9]{32}", generation):
        return None
    folder = root / "versions" / generation
    return folder if all((folder / name).is_file() for name in WINDOWS_FILES) else None


def update_due(root: Path | None = None, now: float | None = None) -> bool:
    root = root or store_root()
    if active_directory(root) is None:
        return True
    last = read_json(root / "checked.json").get("time", 0)
    if not isinstance(last, (int, float)) or not math.isfinite(last):
        return True
    elapsed = (time.time() if now is None else now) - last
    return elapsed < 0 or elapsed >= 24 * 60 * 60


@contextmanager
def update_lock(root: Path):
    """OS lock is released even if an updater crashes. Serializes GUI and scripts."""
    root.mkdir(parents=True, exist_ok=True)
    with (root / "update.lock").open("a+b") as lock:
        lock.seek(0, os.SEEK_END)
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RuntimeError(
                "Ya hay otra actualización en curso. Inténtalo al terminar."
            ) from exc
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == "nt":
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_UN)


def reusable(component, info, previous):
    if not previous or not isinstance(info, dict):
        return False
    if info.get("version") != component.version or info.get("sha256") != component.sha256:
        return False
    hashes = info.get("files", {})
    try:
        return all(
            isinstance(hashes.get(name), str) and file_hash(previous / name) == hashes[name]
            for name in component.files
        )
    except (OSError, AttributeError):
        return False


def validate_windows(folder: Path):
    # Import here to avoid a cycle with tool resolution.
    from .tools import tool_version

    for name in WINDOWS_FILES:
        tool_version(folder / name, Path(name).stem)


def prepare_windows(
    destination: Path, cancel: threading.Event, progress, *, previous=None, validate=False
) -> bool:
    """Populate a staging directory. Never alter the previous installation."""
    progress("Buscando actualizaciones…")
    components = windows_components(cancel)
    old = read_json(previous / "tools-manifest.json") if previous else {}
    choices = [(c, reusable(c, old.get(c.name), previous)) for c in components]
    if all(reuse for _, reuse in choices):
        return False
    destination.mkdir(parents=True, exist_ok=True)
    if previous and (previous / "licenses").is_dir():
        shutil.copytree(previous / "licenses", destination / "licenses", dirs_exist_ok=True)
    manifest = {}
    for index, (component, reuse) in enumerate(choices, start=1):
        check_cancel(cancel)
        progress(f"Preparando componentes · {index}/{len(choices)}")
        if reuse:
            for name in component.files:
                shutil.copy2(previous / name, destination / name)
            manifest[component.name] = old[component.name]
        else:
            manifest[component.name] = install_component(component, destination, cancel, progress)
    if not all((destination / name).is_file() for name in WINDOWS_FILES):
        raise RuntimeError("La preparación está incompleta. Se conserva la versión anterior.")
    check_cancel(cancel)
    if validate:
        progress("Comprobando los componentes descargados…")
        validate_windows(destination)
    write_json(destination / "tools-manifest.json", manifest)
    return True


def update_windows(cancel: threading.Event, progress, *, root: Path | None = None) -> bool:
    if sys.platform != "win32" or platform.machine().lower() not in ("amd64", "x86_64"):
        raise RuntimeError("La preparación automática está disponible para Windows x64.")
    root = root or store_root()
    with update_lock(root):
        previous = active_directory(root)
        with tempfile.TemporaryDirectory(prefix=".staging-", dir=root) as temporary:
            staging = Path(temporary) / "ready"
            changed = prepare_windows(staging, cancel, progress, previous=previous, validate=True)
            check_cancel(cancel)
            if changed:
                generation = uuid4().hex
                versions = root / "versions"
                versions.mkdir(exist_ok=True)
                staging.replace(versions / generation)
                # This is the only activation step. Downloads keep using their captured paths.
                write_json(root / "current.json", {"generation": generation})
                # Keep the previous installation for recovery. Locked files are left alone.
                keep = {generation, previous.name if previous else ""}
                for folder in versions.iterdir():
                    if (
                        folder.is_dir()
                        and re.fullmatch(r"[a-f0-9]{32}", folder.name)
                        and folder.name not in keep
                    ):
                        shutil.rmtree(folder, ignore_errors=True)
            try:
                write_json(root / "checked.json", {"time": time.time()})
            except OSError:
                logging.getLogger(__name__).warning("No se pudo guardar la fecha de comprobación.")
    return changed
