from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class DownloadOptions:
    destination: Path
    mode: str = "video"
    height: int | None = 1080
    compatible: bool = True
    bitrate: int = 192


@dataclass
class DownloadItem:
    url: str
    id: str = field(default_factory=lambda: uuid4().hex)
    title: str = ""
    status: str = "Pendiente"
    detail: str = ""
    progress: int = 0
    path: str = ""
    options: DownloadOptions = field(
        default_factory=lambda: DownloadOptions(Path.home() / "Downloads")
    )


@dataclass(frozen=True)
class DownloadEvent:
    item_id: str
    kind: str
    value: object
