"""Native tools for local development only; this does not build/distribute a Mac app."""

import platform
import shutil
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from superyt.releases import github_component, install_component, release  # noqa: E402
from superyt.tools import tool_version  # noqa: E402


def main():
    if sys.platform != "darwin":
        raise RuntimeError("Este script es solo para pruebas locales en macOS.")
    for name in ("ffmpeg", "ffprobe"):
        path = shutil.which(name)
        if not path:
            raise RuntimeError("Para las pruebas locales, instala FFmpeg: brew install ffmpeg")
        print(tool_version(Path(path), name))
    cancel = threading.Event()
    yt = release("yt-dlp/yt-dlp", cancel)
    deno = release("denoland/deno", cancel)
    arch = {"arm64": "aarch64", "x86_64": "x86_64"}.get(platform.machine())
    if not arch:
        raise RuntimeError("Procesador no compatible con estas pruebas.")
    components = [
        github_component(
            "yt-dlp/yt-dlp",
            yt,
            "yt-dlp_macos",
            ("yt-dlp",),
            cancel,
            license_files=("LICENSE", "THIRD_PARTY_LICENSES.txt"),
        ),
        github_component(
            "denoland/deno",
            deno,
            f"deno-{arch}-apple-darwin.zip",
            ("deno",),
            cancel,
            zipped=True,
            license_files=("LICENSE.md",),
        ),
    ]
    destination = ROOT / "bin"
    destination.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".mac-dev-", dir=destination) as temporary:
        staging = Path(temporary)
        for component in components:
            install_component(component, staging, cancel, print)
            path = staging / component.files[0]
            path.chmod(0o755)
            print(tool_version(path, component.files[0]))
        for name in ("yt-dlp", "deno"):
            (staging / name).replace(destination / name)
        shutil.copytree(staging / "licenses", destination / "licenses-mac-dev", dirs_exist_ok=True)
    print("Pruebas locales preparadas. Ejecuta: .venv/bin/python -m superyt")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("Preparación cancelada.")
    except Exception as exc:
        sys.exit(f"No se pudieron preparar las pruebas: {exc}")
