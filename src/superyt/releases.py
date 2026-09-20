"""Fixed download sources shared by the Windows updater and development scripts."""

import hashlib
import json
import os
import re
import shutil
import threading
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path


class UpdateCancelled(Exception):
    pass


def check_cancel(cancel: threading.Event):
    if cancel.is_set():
        raise UpdateCancelled("Preparación cancelada.")


def request(url: str):
    if not url.startswith("https://"):
        raise ValueError("Las descargas deben usar HTTPS.")
    headers = {"User-Agent": "SuperYTDownloader"}
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
    try:
        return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15)
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 429):
            raise RuntimeError(
                "El servidor ha limitado las consultas. Inténtalo más tarde."
            ) from exc
        raise RuntimeError(f"HTTP {exc.code}: {url}") from exc


def read_text(url: str, cancel: threading.Event) -> str:
    check_cancel(cancel)
    with request(url) as response:
        text = response.read().decode("utf-8")
    check_cancel(cancel)
    return text


def release(repo: str, cancel: threading.Event) -> dict:
    return json.loads(read_text(f"https://api.github.com/repos/{repo}/releases/latest", cancel))


def asset(info: dict, name: str) -> dict:
    for entry in info["assets"]:
        if entry["name"] == name:
            return entry
    raise RuntimeError(f"La publicación no contiene {name}.")


@dataclass(frozen=True)
class Component:
    name: str
    version: str
    url: str
    sha256: str
    files: tuple[str, ...]
    zipped: bool = False
    licenses: tuple[tuple[str, str], ...] = ()


def github_component(repo, info, filename, files, cancel, *, zipped=False, license_files=()):
    entry = asset(info, filename)
    digest = entry.get("digest") or ""
    if digest.startswith("sha256:"):
        expected = digest.removeprefix("sha256:")
    elif repo == "yt-dlp/yt-dlp":
        checksums = read_text(asset(info, "SHA2-256SUMS")["browser_download_url"], cancel)
        expected = next(
            (
                line.split()[0]
                for line in checksums.splitlines()
                if len(line.split()) == 2 and line.split()[-1].lstrip("*") == filename
            ),
            "",
        )
    else:
        suffix = ".sha256" if repo == "GyanD/codexffmpeg" else ".sha256sum"
        expected = read_text(
            asset(info, filename + suffix)["browser_download_url"], cancel
        ).split()[0]
    if not re.fullmatch(r"[a-fA-F0-9]{64}", expected):
        raise RuntimeError(f"No se dispone de una suma SHA256 válida para {filename}.")
    tag = info["tag_name"]
    licenses = tuple(
        (name, f"https://raw.githubusercontent.com/{repo}/{tag}/{name}") for name in license_files
    )
    return Component(
        {"yt-dlp/yt-dlp": "yt-dlp", "denoland/deno": "deno", "GyanD/codexffmpeg": "ffmpeg"}[repo],
        tag,
        entry["browser_download_url"],
        expected.lower(),
        tuple(files),
        zipped,
        licenses,
    )


def windows_components(cancel: threading.Event) -> list[Component]:
    yt = release("yt-dlp/yt-dlp", cancel)
    deno = release("denoland/deno", cancel)
    ffmpeg = release("GyanD/codexffmpeg", cancel)
    archive = next(
        (a["name"] for a in ffmpeg["assets"] if a["name"].endswith("-essentials_build.zip")), None
    )
    if not archive:
        raise RuntimeError("No se encontró el paquete de vídeo para Windows.")
    return [
        github_component(
            "yt-dlp/yt-dlp",
            yt,
            "yt-dlp.exe",
            ("yt-dlp.exe",),
            cancel,
            license_files=("LICENSE", "THIRD_PARTY_LICENSES.txt"),
        ),
        github_component(
            "denoland/deno",
            deno,
            "deno-x86_64-pc-windows-msvc.zip",
            ("deno.exe",),
            cancel,
            zipped=True,
            license_files=("LICENSE.md",),
        ),
        github_component(
            "GyanD/codexffmpeg", ffmpeg, archive, ("ffmpeg.exe", "ffprobe.exe"), cancel, zipped=True
        ),
    ]


def file_hash(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def download(component: Component, path: Path, cancel: threading.Event, progress):
    digest = hashlib.sha256()
    downloaded = 0
    reported = 0
    check_cancel(cancel)
    with request(component.url) as response, path.open("wb") as output:
        while chunk := response.read(256 * 1024):
            check_cancel(cancel)
            digest.update(chunk)
            output.write(chunk)
            downloaded += len(chunk)
            if downloaded - reported >= 10 * 1024 * 1024:
                progress(f"Descargando componentes · {downloaded // 1024 // 1024} MB")
                reported = downloaded
    check_cancel(cancel)
    if digest.hexdigest() != component.sha256:
        raise RuntimeError("La descarga no pasó la verificación. Se conserva la versión anterior.")


def install_component(component: Component, destination: Path, cancel, progress) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    package = destination / f"{component.name}.download"
    download(component, package, cancel, progress)
    licenses_dir = destination / "licenses"
    licenses_dir.mkdir(exist_ok=True)
    if component.zipped:
        with zipfile.ZipFile(package) as archive:
            for filename in component.files:
                check_cancel(cancel)
                entries = [e for e in archive.infolist() if Path(e.filename).name == filename]
                if len(entries) != 1:
                    raise RuntimeError(f"El paquete no contiene un único {filename}.")
                with (
                    archive.open(entries[0]) as source,
                    (destination / filename).open("wb") as output,
                ):
                    shutil.copyfileobj(source, output)
            for entry in archive.infolist():
                basename = Path(entry.filename).name
                if not entry.is_dir() and basename.lower().startswith(
                    ("license", "copying", "readme")
                ):
                    (licenses_dir / f"{component.name}-{basename}").write_bytes(archive.read(entry))
        package.unlink()
    else:
        package.replace(destination / component.files[0])
    for name, url in component.licenses:
        (licenses_dir / f"{component.name}-{name}").write_text(
            read_text(url, cancel), encoding="utf-8"
        )
    check_cancel(cancel)
    return {
        "version": component.version,
        "url": component.url,
        "sha256": component.sha256,
        "files": {name: file_hash(destination / name) for name in component.files},
    }
