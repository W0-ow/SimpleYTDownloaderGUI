import threading

import pytest

from superyt import mac_updater
from superyt.releases import Component


def prepare(monkeypatch, tmp_path):
    monkeypatch.setattr(mac_updater, 'app_root', lambda: tmp_path)
    monkeypatch.setattr(mac_updater.platform, 'machine', lambda: 'arm64')
    monkeypatch.setattr(mac_updater, 'release', lambda *_: {})
    monkeypatch.setattr(mac_updater, 'github_component',
                        lambda repo, info, filename, files, *args, **kwargs:
                        Component(files[0], '1', '', 'a' * 64, files))
    monkeypatch.setattr(mac_updater, 'read_text', lambda *_: '{"versions":{"stable":"8.0"}}')
    monkeypatch.setattr(mac_updater, 'resolve_tool', lambda _: None)


def test_failed_mac_validation_keeps_previous_tools(monkeypatch, tmp_path):
    prepare(monkeypatch, tmp_path)
    folder = tmp_path / 'bin'
    folder.mkdir()
    for name in ('yt-dlp', 'deno'):
        (folder / name).write_text('old')

    def install(component, staging, *args):
        (staging / component.name).write_text('new')
        return {}

    monkeypatch.setattr(mac_updater, 'install_component', install)

    def validate(path, name):
        if name == 'deno':
            raise ValueError('invalid executable')

    monkeypatch.setattr(mac_updater, 'tool_version', validate)
    with pytest.raises(ValueError, match='invalid'):
        mac_updater.update_macos(threading.Event(), lambda _: None)
    assert (folder / 'yt-dlp').read_text() == 'old'
    assert (folder / 'deno').read_text() == 'old'


def test_mac_reuses_verified_components_and_checks_ffmpeg(monkeypatch, tmp_path):
    prepare(monkeypatch, tmp_path)
    monkeypatch.setattr(mac_updater, 'reusable', lambda *_: True)
    messages = []
    assert not mac_updater.update_macos(threading.Event(), messages.append)
    assert any('Homebrew 8.0' in message for message in messages)
