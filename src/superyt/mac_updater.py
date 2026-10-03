"""Native component updates for the local Mac development build."""

import json
import platform
import re
import shutil
import tempfile

from .releases import check_cancel, github_component, install_component, read_text, release
from .settings import app_root
from .tools import resolve_tool, tool_version
from .updater import read_json, reusable, update_lock, write_json


def update_macos(cancel, progress):
    destination = app_root() / 'bin'
    destination.mkdir(exist_ok=True)
    arch = {'arm64': 'aarch64', 'x86_64': 'x86_64'}.get(platform.machine())
    if not arch:
        raise RuntimeError('Procesador Mac no compatible.')
    with update_lock(destination / '.mac-update'):
        progress('Buscando actualizaciones de yt-dlp y Deno…')
        components = [
            github_component('yt-dlp/yt-dlp', release('yt-dlp/yt-dlp', cancel),
                             'yt-dlp_macos', ('yt-dlp',), cancel,
                             license_files=('LICENSE', 'THIRD_PARTY_LICENSES.txt')),
            github_component('denoland/deno', release('denoland/deno', cancel),
                             f'deno-{arch}-apple-darwin.zip', ('deno',), cancel,
                             zipped=True, license_files=('LICENSE.md',)),
        ]
        old = read_json(destination / 'mac-tools-manifest.json')
        manifest = dict(old)
        changed = []
        with tempfile.TemporaryDirectory(prefix='.mac-dev-', dir=destination) as temporary:
            from pathlib import Path

            staging = Path(temporary)
            for component in components:
                if reusable(component, old.get(component.name), destination):
                    progress(f'{component.name}: actualizado ({component.version}).')
                    continue
                progress(f'Actualizando {component.name} a {component.version}…')
                manifest[component.name] = install_component(component, staging, cancel, progress)
                path = staging / component.files[0]
                path.chmod(0o755)
                tool_version(path, component.files[0])
                changed.append(component.files[0])
            check_cancel(cancel)
            for name in changed:
                (staging / name).replace(destination / name)
            if (staging / 'licenses').exists():
                shutil.copytree(staging / 'licenses', destination / 'licenses-mac-dev',
                                dirs_exist_ok=True)
            write_json(destination / 'mac-tools-manifest.json', manifest)
    # Homebrew owns the Mac FFmpeg installation; never replace it with Windows tools.
    progress('Comprobando FFmpeg para Mac…')
    try:
        info = json.loads(read_text('https://formulae.brew.sh/api/formula/ffmpeg.json', cancel))
        latest = info['versions']['stable']
        path = resolve_tool('ffmpeg')
        installed = tool_version(path, 'ffmpeg') if path else ''
        match = re.search(r'ffmpeg version (\d+(?:\.\d+)+)', installed)
        current = match.group(1) if match else 'desconocida'
        progress(f'FFmpeg Mac: instalado {current}; Homebrew {latest}. '
                 'Para actualizar FFmpeg/FFprobe en este Mac: brew upgrade ffmpeg')
    except Exception as exc:
        check_cancel(cancel)
        progress(f'No se pudo comprobar FFmpeg de Homebrew: {exc}')
    return bool(changed)
