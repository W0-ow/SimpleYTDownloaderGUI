import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .settings import app_root
from .updater import active_directory


@dataclass(frozen=True)
class Tools:
    yt_dlp: Path
    ffmpeg: Path | None
    deno: Path | None


def executable_name(name: str) -> str:
    return name + (".exe" if sys.platform == "win32" else "")


def resolve_tool(name: str, root: Path | None = None) -> Path | None:
    if sys.platform == "win32":
        managed = active_directory()
        if managed:
            return managed / executable_name(name)
    bundled = (root or app_root()) / "bin" / executable_name(name)
    if bundled.is_file():
        return bundled.resolve()
    # Native tools are a development convenience on macOS/Linux only.
    if sys.platform != "win32":
        local = Path(sys.executable).parent / name
        if local.is_file():
            return local.resolve()
        found = shutil.which(name)
        return Path(found).resolve() if found else None
    return None


def resolve_tools(needs_ffmpeg: bool = True) -> Tools:
    yt_dlp = resolve_tool("yt-dlp")
    ffmpeg = resolve_tool("ffmpeg")
    deno = resolve_tool("deno")
    if yt_dlp is None or deno is None:
        raise ValueError("Faltan componentes. Pulsa Buscar actualizaciones para prepararlos.")
    if needs_ffmpeg and (
        ffmpeg is None or not ffmpeg.with_name(executable_name("ffprobe")).is_file()
    ):
        raise ValueError(
            "Faltan componentes de vídeo. Pulsa Buscar actualizaciones para prepararlos."
        )
    return Tools(yt_dlp, ffmpeg, deno)


def subprocess_options() -> dict:
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NO_WINDOW}
    return {}


def tool_version(path: Path, name: str | None = None) -> str:
    result = subprocess.run(
        [str(path), "-version" if (name or path.stem) in ("ffmpeg", "ffprobe") else "--version"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
        encoding="utf-8",
        errors="replace",
        **subprocess_options(),
    )
    lines = result.stdout.strip().splitlines()
    if result.returncode:
        raise ValueError(lines[0] if lines else f"Código de salida {result.returncode}")
    return lines[0][:180] if lines else "Sin información de versión"
