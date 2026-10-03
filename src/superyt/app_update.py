"""Release discovery and verified installer handoff (Windows installed builds)."""

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from . import __version__
from .releases import Component, asset, download, read_text, release
from .settings import app_root, data_dir

REPO = "W0-ow/SimpleYTDownloaderGUI"
INSTALLER = "SuperYTDownloader-Setup.exe"


def version_tuple(value):
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        raise ValueError("La publicación no tiene una versión estable válida.")
    return tuple(map(int, match.groups()))


@dataclass(frozen=True)
class AppRelease:
    version: str
    notes: str
    url: str
    sha256: str


def check_release(cancel):
    info = release(REPO, cancel)
    if info.get("draft") or info.get("prerelease"):
        return None
    if version_tuple(info["tag_name"]) <= version_tuple(__version__):
        return None
    entry = asset(info, INSTALLER)
    prefix = f"https://github.com/{REPO}/releases/download/"
    url = entry["browser_download_url"]
    checksum_url = asset(info, "SHA256SUMS.txt")["browser_download_url"]
    if not url.startswith(prefix) or not checksum_url.startswith(prefix):
        raise ValueError("La publicación contiene una dirección de descarga inesperada.")
    sums = read_text(checksum_url, cancel)
    digest = next((line.split()[0] for line in sums.splitlines()
                   if len(line.split()) == 2 and line.split()[1] == INSTALLER), "")
    if not re.fullmatch(r"[a-fA-F0-9]{64}", digest):
        raise ValueError("Falta la suma SHA256 del instalador.")
    return AppRelease(info["tag_name"], info.get("body") or "Sin notas de versión.",
                      url, digest.lower())


def can_install():
    return (sys.platform == "win32" and getattr(sys, "frozen", False)
            and (app_root() / "installed.txt").is_file())


def fetch_installer(info, cancel, progress):
    folder = data_dir() / "updates" / info.version
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / INSTALLER
    partial = target.with_suffix(".partial")
    try:
        download(Component("app", info.version, info.url, info.sha256, (INSTALLER,)),
                 partial, cancel, progress)
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)
    return target


def launch_installer(installer):
    if not can_install():
        raise RuntimeError("La instalación automática requiere la versión instalada de Windows.")
    helper = Path(__file__).parent / "assets" / "apply_update.ps1"
    # No shell interpolation: all paths are passed as separate process arguments.
    subprocess.Popen([
        str(Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"),
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden",
        "-File", str(helper), "-AppProcessId", str(os.getpid()),
        "-Installer", str(installer), "-InstallDir", str(app_root()),
    ], creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
       close_fds=True)
