import json
import math
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from .models import DownloadOptions
from .tools import Tools

EVENT_PREFIX = "SUPER_YT:"


def normalize_url(value: str) -> str:
    value = value.strip()
    if any(c.isspace() or ord(c) < 32 for c in value) or any(c in value for c in '\\"<>'):
        raise ValueError("El enlace contiene caracteres no válidos.")
    if "://" not in value:
        value = "https://" + value
    try:
        parsed = urlsplit(value)
        if (
            parsed.scheme not in ("http", "https")
            or parsed.username
            or parsed.password
            or parsed.port
        ):
            raise ValueError
        host = (parsed.hostname or "").lower()
        if host not in (
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
            "music.youtube.com",
            "youtu.be",
        ):
            raise ValueError
        query = parse_qs(parsed.query)
        parts = parsed.path.strip("/").split("/")
        video_id = ""
        if host == "youtu.be" and len(parts) == 1:
            video_id = parts[0]
        elif parsed.path == "/watch":
            video_id = query.get("v", [""])[0]
        elif len(parts) == 2 and parts[0] in ("shorts", "live", "embed"):
            video_id = parts[1]
        if not video_id or not all(c.isascii() and (c.isalnum() or c in "-_") for c in video_id):
            raise ValueError
    except ValueError:
        raise ValueError(
            "Introduce un enlace a un vídeo de YouTube (watch, Shorts, live o youtu.be)."
        ) from None
    return urlunsplit(("https", "www.youtube.com", "/watch", urlencode({"v": video_id}), ""))


def base_arguments(tools: Tools) -> list[str]:
    args = [
        "--ignore-config",
        "--no-playlist",
        "--no-color",
        "--encoding",
        "utf-8",
        "--no-js-runtimes",
        "--socket-timeout",
        "20",
        "--retries",
        "3",
    ]
    if tools.deno:
        args += ["--js-runtimes", f"deno:{tools.deno}"]
    if tools.ffmpeg:
        args += ["--ffmpeg-location", str(tools.ffmpeg.parent)]
    return args


def format_selector(options: DownloadOptions) -> str:
    cap = f"[height<={options.height}]" if options.height else ""
    if options.compatible:
        return f"bv{cap}[vcodec^=avc1]+ba[ext=m4a]/b{cap}[vcodec^=avc1][ext=mp4]"
    return f"bv*{cap}+ba/b{cap}"


def download_arguments(url: str, options: DownloadOptions, tools: Tools) -> list[str]:
    args = base_arguments(tools) + [
        "--newline",
        "--progress",
        "--progress-delta",
        "0.3",
        "--no-simulate",
        "--windows-filenames",
        "--trim-filenames",
        "180",
        "--continue",
        "--no-overwrites",
        "--paths",
        str(options.destination.resolve()),
        "--output",
        "%(title)s [%(id)s].%(ext)s",
        "--print",
        f"before_dl:{EVENT_PREFIX}title:%(title)j",
        "--print",
        f"after_move:{EVENT_PREFIX}path:%(filepath)j",
        "--progress-template",
        f'download:{EVENT_PREFIX}progress:{{"downloaded":%(progress.downloaded_bytes|0)j,'
        '"total":%(progress.total_bytes|0)j,"estimate":%(progress.total_bytes_estimate|0)j,'
        '"speed":%(progress.speed|0)j,"eta":%(progress.eta|0)j}',
        "--progress-template",
        f"postprocess:{EVENT_PREFIX}postprocess:%(progress.status)j",
    ]
    if options.mode == "video":
        args += [
            "--format",
            format_selector(options),
            "--merge-output-format",
            "mp4" if options.compatible else "mkv",
        ]
    elif options.mode == "original":
        args += ["--format", "bestaudio"]
    elif options.mode == "mp3":
        args += [
            "--format",
            "bestaudio",
            "--extract-audio",
            "--audio-format",
            "mp3",
            "--audio-quality",
            f"{options.bitrate}K",
        ]
    else:
        raise ValueError("Modo de descarga desconocido")
    return args + ["--", normalize_url(url)]


def parse_event(line: str) -> tuple[str, object] | None:
    if not line.startswith(EVENT_PREFIX):
        return None
    kind, separator, payload = line[len(EVENT_PREFIX) :].partition(":")
    if not separator or kind not in ("title", "path", "progress", "postprocess"):
        return None
    try:
        value = json.loads(payload)
    except ValueError:
        return None
    if kind == "progress" and not isinstance(value, dict):
        return None
    if kind != "progress" and not isinstance(value, str):
        return None
    return kind, value


def positive_number(value: object) -> float:
    if isinstance(value, (int, float)) and math.isfinite(value) and value > 0:
        return float(value)
    return 0.0


def progress_detail(data: dict) -> tuple[int, str]:
    total = positive_number(data.get("total")) or positive_number(data.get("estimate"))
    downloaded = positive_number(data.get("downloaded"))
    percent = min(100, int(downloaded / total * 100)) if total else 0
    speed = positive_number(data.get("speed"))
    eta = positive_number(data.get("eta"))
    parts = [f"{speed / 1024 / 1024:.1f} MB/s"] if speed else []
    if eta:
        parts.append(f"{int(eta) // 60}:{int(eta) % 60:02d} restantes")
    if not total:
        parts.append("Tamaño desconocido")
    return percent, " · ".join(parts)
