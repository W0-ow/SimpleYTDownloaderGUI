import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from superyt.settings import Settings
from superyt.tools import executable_name, resolve_tool, resolve_tools


def test_settings_roundtrip_and_migrates_away_from_manual_tools(tmp_path):
    path = tmp_path / "settings.json"
    settings = Settings(destination="C:/Música", mode="mp3", bitrate=320)
    settings.save(path)
    assert Settings.load(path) == settings
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["tools"] = {"yt-dlp": "C:/old/broken.exe"}
    path.write_text(json.dumps(raw), encoding="utf-8")
    assert Settings.load(path) == settings
    Settings.load(path).save(path)
    assert "tools" not in json.loads(path.read_text(encoding="utf-8"))
    path.write_text(
        json.dumps({"mode": [], "height": {}, "bitrate": [], "tools": None}), encoding="utf-8"
    )
    assert Settings.load(path) == Settings()
    path.write_text("{broken", encoding="utf-8")
    assert Settings.load(path) == Settings()


def test_windows_uses_managed_components_before_bundle_and_ignores_path(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "superyt.tools.sys", SimpleNamespace(platform="win32", executable=sys.executable)
    )
    monkeypatch.setattr("superyt.tools.active_directory", lambda: None)
    monkeypatch.setattr("superyt.tools.shutil.which", lambda _: "/unrelated/program")
    assert resolve_tool("yt-dlp", tmp_path) is None
    bundled = tmp_path / "bin/yt-dlp.exe"
    bundled.parent.mkdir()
    bundled.touch()
    assert resolve_tool("yt-dlp", tmp_path) == bundled
    managed = tmp_path / "managed"
    monkeypatch.setattr("superyt.tools.active_directory", lambda: managed)
    assert resolve_tool("yt-dlp", tmp_path) == managed / "yt-dlp.exe"


def test_local_native_tools_are_detected_for_mac_development(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "superyt.tools.sys", SimpleNamespace(platform="darwin", executable=str(tmp_path / "python"))
    )
    monkeypatch.setattr("superyt.tools.shutil.which", lambda _: "/usr/local/bin/ffmpeg")
    assert resolve_tool("ffmpeg", tmp_path) == Path("/usr/local/bin/ffmpeg").resolve()
    local = tmp_path / "yt-dlp"
    local.touch()
    assert resolve_tool("yt-dlp", tmp_path) == local


def test_ffprobe_is_required_for_converting(tmp_path, monkeypatch):
    paths = {}
    for name in ("yt-dlp", "ffmpeg", "deno"):
        paths[name] = tmp_path / executable_name(name)
        paths[name].touch()
    monkeypatch.setattr("superyt.tools.resolve_tool", lambda name: paths[name])
    with pytest.raises(ValueError, match="vídeo"):
        resolve_tools()
    assert resolve_tools(needs_ffmpeg=False).yt_dlp == paths["yt-dlp"]
    (tmp_path / executable_name("ffprobe")).touch()
    assert resolve_tools().ffmpeg == paths["ffmpeg"]
