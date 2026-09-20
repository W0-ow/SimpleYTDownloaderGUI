import json
from pathlib import Path

import pytest

from superyt.settings import Settings
from superyt.tools import executable_name, resolve_tool, resolve_tools


def test_settings_roundtrip_and_invalid_fields(tmp_path):
    path = tmp_path / "settings.json"
    settings = Settings(
        destination="C:/Música", mode="mp3", bitrate=320, tools={"yt-dlp": "C:/bin/yt-dlp.exe"}
    )
    settings.save(path)
    assert Settings.load(path) == settings
    path.write_text(
        json.dumps({"mode": [], "height": {}, "bitrate": [], "tools": None}), encoding="utf-8"
    )
    assert Settings.load(path) == Settings()
    path.write_text("{broken", encoding="utf-8")
    assert Settings.load(path) == Settings()


def test_explicit_tool_then_bundle_then_path(tmp_path, monkeypatch):
    monkeypatch.setattr("superyt.tools.shutil.which", lambda _: "/usr/local/bin/yt-dlp")
    assert resolve_tool("yt-dlp", {}, tmp_path) == Path("/usr/local/bin/yt-dlp").resolve()
    bundled = tmp_path / "bin" / executable_name("yt-dlp")
    bundled.parent.mkdir()
    bundled.touch()
    assert resolve_tool("yt-dlp", {}, tmp_path) == bundled
    custom = tmp_path / "custom.exe"
    custom.touch()
    assert resolve_tool("yt-dlp", {"yt-dlp": str(custom)}, tmp_path) == custom
    assert resolve_tool("yt-dlp", {"yt-dlp": str(tmp_path / "missing")}, tmp_path) is None


def test_ffprobe_is_required_for_converting(tmp_path, monkeypatch):
    paths = {}
    for name in ("yt-dlp", "ffmpeg", "deno"):
        paths[name] = tmp_path / executable_name(name)
        paths[name].touch()
    monkeypatch.setattr("superyt.tools.resolve_tool", lambda name, _: paths[name])
    with pytest.raises(ValueError, match="ffprobe"):
        resolve_tools({})
    assert resolve_tools({}, needs_ffmpeg=False).yt_dlp == paths["yt-dlp"]
    (tmp_path / executable_name("ffprobe")).touch()
    assert resolve_tools({}).ffmpeg == paths["ffmpeg"]
