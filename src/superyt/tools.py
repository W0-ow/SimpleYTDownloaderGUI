import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .settings import app_root


@dataclass(frozen=True)
class Tools:
    yt_dlp: Path
    ffmpeg: Path | None
    deno: Path | None


def executable_name(name: str) -> str:
    return name + (".exe" if sys.platform == "win32" else "")


def resolve_tool(name: str, overrides: dict[str, str], root: Path | None = None) -> Path | None:
    explicit = overrides.get(name, "").strip()
    if explicit:
        candidate = Path(explicit).expanduser()
        return candidate.resolve() if candidate.is_file() else None
    bundled = (root or app_root()) / "bin" / executable_name(name)
    if bundled.is_file():
        return bundled.resolve()
    found = shutil.which(executable_name(name))
    return Path(found).resolve() if found else None


def resolve_tools(overrides: dict[str, str], needs_ffmpeg: bool = True) -> Tools:
    yt_dlp = resolve_tool("yt-dlp", overrides)
    ffmpeg = resolve_tool("ffmpeg", overrides)
    deno = resolve_tool("deno", overrides)
    if yt_dlp is None:
        raise ValueError(
            "No se encuentra yt-dlp. Coloca el ejecutable en bin/ o selecciónalo en Ajustes."
        )
    if needs_ffmpeg:
        if ffmpeg is None:
            raise ValueError(
                "Este modo necesita FFmpeg. Coloca ffmpeg y ffprobe en bin/ o configura su ruta."
            )
        if not ffmpeg.with_name(executable_name("ffprobe")).is_file():
            raise ValueError(
                "Falta ffprobe junto a ffmpeg. Copia ambos ejecutables en la misma carpeta."
            )
    if deno is None:
        raise ValueError(
            "Falta Deno para el soporte de YouTube. Colócalo en bin/ o selecciónalo en Ajustes."
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
        timeout=8,
        encoding="utf-8",
        errors="replace",
        **subprocess_options(),
    )
    lines = result.stdout.strip().splitlines()
    if result.returncode:
        raise ValueError(lines[0] if lines else f"Código de salida {result.returncode}")
    return lines[0][:180] if lines else "Sin información de versión"
