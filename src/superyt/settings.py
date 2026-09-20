import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    if sys.platform == "win32":
        return (
            Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
            / "SuperYTDownloader"
        )
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/SuperYTDownloader"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "SuperYTDownloader"


@dataclass
class Settings:
    destination: str = field(default_factory=lambda: str(Path.home() / "Downloads"))
    mode: str = "video"
    height: int | None = 1080
    compatible: bool = True
    bitrate: int = 192
    tools: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | None = None) -> "Settings":
        try:
            raw = json.loads((path or data_dir() / "settings.json").read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return cls()
        except (OSError, ValueError):
            return cls()
        settings = cls()
        if isinstance(raw.get("destination"), str) and raw["destination"].strip():
            settings.destination = raw["destination"]
        if raw.get("mode") in ("video", "original", "mp3"):
            settings.mode = raw["mode"]
        if raw.get("height", 1080) in (None, 360, 480, 720, 1080, 1440, 2160):
            settings.height = raw.get("height", 1080)
        if isinstance(raw.get("compatible"), bool):
            settings.compatible = raw["compatible"]
        if raw.get("bitrate") in (128, 192, 256, 320):
            settings.bitrate = raw["bitrate"]
        if isinstance(raw.get("tools"), dict):
            settings.tools = {
                k: v
                for k, v in raw["tools"].items()
                if k in ("yt-dlp", "ffmpeg", "deno") and isinstance(v, str)
            }
        return settings

    def save(self, path: Path | None = None) -> None:
        target = path or data_dir() / "settings.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(target)
