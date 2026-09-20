from pathlib import Path

import pytest

from superyt.formats import download_arguments, normalize_url, parse_event, progress_detail
from superyt.models import DownloadOptions
from superyt.tools import Tools


@pytest.fixture
def tools():
    return Tools(
        Path("C:/App/bin/yt-dlp.exe"), Path("C:/App/bin/ffmpeg.exe"), Path("C:/App/bin/deno.exe")
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://youtu.be/abcdefghijk?t=15",
        "https://www.youtube.com/watch?v=abcdefghijk&list=PL123",
        "youtube.com/shorts/abcdefghijk",
        "https://m.youtube.com/watch?v=abcdefghijk",
        "https://music.youtube.com/watch?v=abcdefghijk",
        "https://youtube.com/live/abcdefghijk",
    ],
)
def test_normalizes_video_urls_and_removes_playlist(url):
    assert normalize_url(url) == "https://www.youtube.com/watch?v=abcdefghijk"


@pytest.mark.parametrize(
    "url",
    [
        "https://youtube.com.evil.test/watch?v=abc",
        "file:///tmp/video",
        "https://evil@youtube.com/watch?v=abc",
        "https://youtube.com/playlist?list=abc",
        'https://youtu.be/abc" & calc.exe & "',
        "https://youtu.be/a b",
        "https://youtu.be:443/abc",
        "https://youtube.com/watch",
        "https://youtube.com/@channel",
    ],
)
def test_rejects_invalid_links(url):
    with pytest.raises(ValueError):
        normalize_url(url)


def test_video_limits_both_fallbacks_and_passes_destination_separately(tmp_path, tools):
    destination = tmp_path / "Música & vídeos"
    args = download_arguments(
        "https://youtu.be/abc", DownloadOptions(destination, compatible=False), tools
    )
    assert args[args.index("--format") + 1] == "bv*[height<=1080]+ba/b[height<=1080]"
    assert args[args.index("--paths") + 1] == str(destination.resolve())
    assert args[-2:] == ["--", "https://www.youtube.com/watch?v=abc"]
    assert "--ignore-config" in args
    assert "--no-playlist" in args
    assert "--no-simulate" in args


def test_compatible_format_filters_codec_not_just_extension(tmp_path, tools):
    args = download_arguments("youtu.be/abc", DownloadOptions(tmp_path), tools)
    selection = args[args.index("--format") + 1]
    assert all("[vcodec^=avc1]" in alternative for alternative in selection.split("/"))
    assert args[args.index("--merge-output-format") + 1] == "mp4"


def test_original_audio_does_not_convert(tmp_path, tools):
    args = download_arguments("youtu.be/abc", DownloadOptions(tmp_path, mode="original"), tools)
    assert args[args.index("--format") + 1] == "bestaudio"
    assert "--extract-audio" not in args
    assert "--merge-output-format" not in args


def test_mp3_quality_is_bitrate(tmp_path, tools):
    args = download_arguments(
        "youtu.be/abc", DownloadOptions(tmp_path, mode="mp3", bitrate=320), tools
    )
    assert args[args.index("--audio-quality") + 1] == "320K"
    assert args[args.index("--audio-format") + 1] == "mp3"


def test_protocol_handles_unicode_missing_totals_and_malformed_output():
    assert parse_event('SUPER_YT:title:"Canción 日本語"') == ("title", "Canción 日本語")
    assert parse_event("SUPER_YT:progress:{broken") is None
    assert parse_event("SUPER_YT:progress:5") is None
    percent, detail = progress_detail(
        {"downloaded": 500, "total": "NA", "estimate": 1000, "speed": None, "eta": 65}
    )
    assert percent == 50
    assert "1:05" in detail
    assert progress_detail({"total": float("nan"), "speed": "NA"}) == (0, "Tamaño desconocido")
