"""Download verified Windows x64 tools into bin/. Run explicitly; never on app startup."""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def request(url):
    headers = {"User-Agent": "SuperYTDownloader-setup"}
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
    try:
        return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=90)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}: {url}") from exc


def read_text(url):
    with request(url) as response:
        return response.read().decode("utf-8")


def release(repo):
    return json.loads(read_text(f"https://api.github.com/repos/{repo}/releases/latest"))


def asset(release_info, name):
    return next(entry for entry in release_info["assets"] if entry["name"] == name)


def download(url, target, expected):
    if not re.fullmatch(r"[a-fA-F0-9]{64}", expected):
        raise ValueError(f"SHA256 no válido para {target.name}")
    print(f"Descargando {target.name}…", flush=True)
    digest = hashlib.sha256()
    downloaded = 0
    with request(url) as response, target.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            digest.update(chunk)
            output.write(chunk)
            downloaded += len(chunk)
            if downloaded % (10 * 1024 * 1024) == 0:
                print(f"  {downloaded // 1024 // 1024} MB", flush=True)
    if digest.hexdigest() != expected.lower():
        raise ValueError(f"La suma SHA256 no coincide: {target.name}")
    return {"url": url, "sha256": digest.hexdigest()}


def github_download(info, name, folder):
    entry = asset(info, name)
    digest = entry.get("digest") or ""
    if digest.startswith("sha256:"):
        expected = digest.removeprefix("sha256:")
    else:
        # Older releases may expose checksum files instead of API asset digests.
        if name == "yt-dlp.exe":
            checksums = read_text(asset(info, "SHA2-256SUMS")["browser_download_url"])
            expected = next(
                line.split()[0]
                for line in checksums.splitlines()
                if line.split()[-1].lstrip("*") == name
            )
        else:
            checksum = asset(
                info, name + (".sha256" if "essentials_build" in name else ".sha256sum")
            )
            expected = read_text(checksum["browser_download_url"]).split()[0]
    return download(entry["browser_download_url"], folder / name, expected)


def unpack_executable(archive, name, target):
    with zipfile.ZipFile(archive) as zip_file:
        entries = [entry for entry in zip_file.infolist() if Path(entry.filename).name == name]
        if len(entries) != 1:
            raise ValueError(f"No se encontró un único {name} en {archive.name}")
        with zip_file.open(entries[0]) as source, (target / name).open("wb") as output:
            shutil.copyfileobj(source, output)


def setup(destination):
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="superyt-tools-") as temporary:
        staging = Path(temporary)
        license_dir = staging / "licenses"
        license_dir.mkdir()
        manifest = {}
        yt = release("yt-dlp/yt-dlp")
        manifest["yt-dlp"] = github_download(yt, "yt-dlp.exe", staging)
        manifest["yt-dlp"]["version"] = yt["tag_name"]
        deno = release("denoland/deno")
        deno_zip = "deno-x86_64-pc-windows-msvc.zip"
        manifest["deno"] = github_download(deno, deno_zip, staging)
        manifest["deno"]["version"] = deno["tag_name"]
        unpack_executable(staging / deno_zip, "deno.exe", staging)
        ffmpeg = release("GyanD/codexffmpeg")
        ffmpeg_zip = next(
            entry["name"]
            for entry in ffmpeg["assets"]
            if entry["name"].endswith("-essentials_build.zip")
        )
        manifest["ffmpeg"] = github_download(ffmpeg, ffmpeg_zip, staging)
        manifest["ffmpeg"]["version"] = ffmpeg["tag_name"]
        for name in ("ffmpeg.exe", "ffprobe.exe"):
            unpack_executable(staging / ffmpeg_zip, name, staging)
        with zipfile.ZipFile(staging / ffmpeg_zip) as archive:
            for entry in archive.infolist():
                basename = Path(entry.filename).name
                if not entry.is_dir() and basename.lower().startswith(
                    ("license", "copying", "readme")
                ):
                    with archive.open(entry) as source:
                        (license_dir / f"ffmpeg-{basename}").write_bytes(source.read())
        for repo, tag, name, filename in (
            ("yt-dlp/yt-dlp", yt["tag_name"], "yt-dlp", "LICENSE"),
            ("denoland/deno", deno["tag_name"], "deno", "LICENSE.md"),
        ):
            license_text = read_text(f"https://raw.githubusercontent.com/{repo}/{tag}/{filename}")
            (license_dir / f"{name}-LICENSE.txt").write_text(license_text, encoding="utf-8")
        # Keep yt-dlp's third party notices alongside its standalone executable.
        notices = read_text(
            f"https://raw.githubusercontent.com/yt-dlp/yt-dlp/{yt['tag_name']}/THIRD_PARTY_LICENSES.txt"
        )
        (license_dir / "yt-dlp-THIRD_PARTY_LICENSES.txt").write_text(notices, encoding="utf-8")
        (staging / "tools-manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        for name in ("yt-dlp.exe", "ffmpeg.exe", "ffprobe.exe", "deno.exe", "tools-manifest.json"):
            shutil.copy2(staging / name, destination / name)
        shutil.copytree(license_dir, destination / "licenses", dirs_exist_ok=True)
    print(f"Herramientas Windows x64 listas en {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=ROOT / "bin")
    args = parser.parse_args()
    try:
        setup(args.destination.resolve())
    except KeyboardInterrupt:
        sys.exit("Preparación cancelada.")
    except Exception as exc:
        sys.exit(f"No se pudieron preparar las herramientas: {exc}")
