import hashlib
import io
import json
import threading
from dataclasses import replace
from types import SimpleNamespace

import pytest

from superyt import releases, updater
from superyt.releases import Component, UpdateCancelled, file_hash


@pytest.fixture
def installation(tmp_path, monkeypatch):
    monkeypatch.setattr(updater, "sys", SimpleNamespace(platform="win32"))
    monkeypatch.setattr(updater.platform, "machine", lambda: "AMD64")
    components = [
        Component("yt-dlp", "1", "https://example.test/yt", "a" * 64, ("yt-dlp.exe",)),
        Component("deno", "1", "https://example.test/deno", "b" * 64, ("deno.exe",)),
        Component(
            "ffmpeg", "1", "https://example.test/ffmpeg", "c" * 64, ("ffmpeg.exe", "ffprobe.exe")
        ),
    ]
    calls = []

    def install(component, destination, cancel, progress):
        calls.append(component.name)
        for name in component.files:
            (destination / name).write_bytes(f"{component.name}:{component.version}".encode())
        return {
            "version": component.version,
            "url": component.url,
            "sha256": component.sha256,
            "files": {name: file_hash(destination / name) for name in component.files},
        }

    monkeypatch.setattr(updater, "windows_components", lambda _: components)
    monkeypatch.setattr(updater, "install_component", install)
    monkeypatch.setattr(updater, "validate_windows", lambda _: None)
    return tmp_path / "store", components, calls


def run(root):
    return updater.update_windows(threading.Event(), lambda _: None, root=root)


def test_first_install_and_unchanged_versions_do_not_download_again(installation):
    root, _, calls = installation
    assert run(root)
    current = updater.active_directory(root)
    assert current and all((current / name).is_file() for name in updater.WINDOWS_FILES)
    assert calls == ["yt-dlp", "deno", "ffmpeg"]
    calls.clear()
    assert not run(root)
    assert calls == []
    assert updater.active_directory(root) == current
    assert not updater.update_due(root)


def test_only_changed_component_is_downloaded_and_previous_is_retained(installation):
    root, components, calls = installation
    run(root)
    previous = updater.active_directory(root)
    components[0] = replace(components[0], version="2", sha256="d" * 64)
    calls.clear()
    assert run(root)
    current = updater.active_directory(root)
    assert current != previous and previous.exists()
    assert calls == ["yt-dlp"]
    assert (current / "yt-dlp.exe").read_bytes() == b"yt-dlp:2"
    assert (current / "ffmpeg.exe").read_bytes() == (previous / "ffmpeg.exe").read_bytes()


def test_corrupted_local_binary_is_repaired_even_at_same_version(installation):
    root, _, calls = installation
    run(root)
    (updater.active_directory(root) / "deno.exe").write_bytes(b"corrupt")
    calls.clear()
    assert run(root)
    assert calls == ["deno"]


@pytest.mark.parametrize(
    "failure", [OSError("offline"), RuntimeError("invalid executable"), UpdateCancelled()]
)
def test_failed_update_never_activates_partial_installation(installation, monkeypatch, failure):
    root, components, _ = installation
    run(root)
    old_pointer = (root / "current.json").read_bytes()
    old_check = (root / "checked.json").read_bytes()
    components[0] = replace(components[0], version="2", sha256="d" * 64)

    def fail(_):
        raise failure

    monkeypatch.setattr(updater, "validate_windows", fail)
    with pytest.raises(type(failure)):
        run(root)
    assert (root / "current.json").read_bytes() == old_pointer
    assert (root / "checked.json").read_bytes() == old_check
    assert (updater.active_directory(root) / "yt-dlp.exe").read_bytes() == b"yt-dlp:1"
    assert not list(root.glob(".staging-*"))


def test_cancellation_before_activation_preserves_previous(installation, monkeypatch):
    root, components, _ = installation
    run(root)
    previous = updater.active_directory(root)
    components[0] = replace(components[0], version="2", sha256="d" * 64)
    cancel = threading.Event()
    monkeypatch.setattr(updater, "validate_windows", lambda _: cancel.set())
    with pytest.raises(UpdateCancelled):
        updater.update_windows(cancel, lambda _: None, root=root)
    assert updater.active_directory(root) == previous


def test_daily_check_and_invalid_pointer(installation):
    root, _, _ = installation
    assert updater.update_due(root)
    run(root)
    updater.write_json(root / "checked.json", {"time": 100})
    assert not updater.update_due(root, now=101)
    assert updater.update_due(root, now=100 + 86400)
    assert updater.update_due(root, now=99)
    updater.write_json(root / "current.json", {"generation": "../../unexpected"})
    assert updater.active_directory(root) is None


def test_simultaneous_updaters_are_rejected_and_lock_is_released(tmp_path):
    with updater.update_lock(tmp_path):
        with pytest.raises(RuntimeError, match="otra actualización"):
            with updater.update_lock(tmp_path):
                pass
    with updater.update_lock(tmp_path):
        pass


def test_bad_download_hash_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(releases, "request", lambda _: io.BytesIO(b"bad download"))
    component = Component(
        "test", "1", "https://example.test/tool", hashlib.sha256(b"expected").hexdigest(), ("tool",)
    )
    with pytest.raises(RuntimeError, match="verificación"):
        releases.download(component, tmp_path / "download", threading.Event(), lambda _: None)


def test_unusable_first_install_does_not_create_current_pointer(installation, monkeypatch):
    root, _, _ = installation

    def fail(_):
        raise RuntimeError("cannot execute")

    monkeypatch.setattr(updater, "validate_windows", fail)
    with pytest.raises(RuntimeError):
        run(root)
    assert updater.active_directory(root) is None
    assert not (root / "current.json").exists()


def test_bounded_storage_keeps_current_and_previous(installation):
    root, components, _ = installation
    for version in ("1", "2", "3"):
        components[0] = replace(components[0], version=version)
        run(root)
    assert len(list((root / "versions").iterdir())) == 2
    assert (
        json.loads((root / "current.json").read_text())["generation"]
        == updater.active_directory(root).name
    )
