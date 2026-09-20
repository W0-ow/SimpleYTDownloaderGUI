"""Validate our CLI protocol and quality filters against real yt-dlp, without networking."""

from pathlib import Path

import pytest
from yt_dlp import YoutubeDL, parse_options

from superyt.formats import download_arguments, format_selector, parse_event
from superyt.models import DownloadOptions
from superyt.tools import Tools


@pytest.mark.parametrize("mode", ["video", "original", "mp3"])
def test_real_ytdlp_accepts_options_and_formats_progress_as_json(tmp_path, mode):
    args = download_arguments(
        "youtu.be/abcdefghijk",
        DownloadOptions(tmp_path, mode=mode),
        Tools(Path("yt-dlp"), None, None),
    )
    parsed = parse_options(args)
    assert parsed.ydl_opts["noplaylist"]
    assert parsed.ydl_opts["simulate"] is False
    template = parsed.ydl_opts["progress_template"]["download"]
    with YoutubeDL({"quiet": True}) as ydl:
        line = ydl.evaluate_outtmpl(
            template, {"progress": {"downloaded_bytes": 50, "total_bytes": 100}}
        )
    kind, data = parse_event(line)
    assert kind == "progress"
    assert data["downloaded"] == 50
    assert data["total"] == 100


@pytest.mark.parametrize(
    "compatible,height,expected", [(True, 1080, 720), (False, 1080, 720), (False, None, 1440)]
)
def test_quality_falls_back_without_upscaling(compatible, height, expected):
    formats = [
        {
            "format_id": "a",
            "ext": "m4a",
            "vcodec": "none",
            "acodec": "mp4a",
            "url": "https://example.test/a",
            "protocol": "https",
        },
        {
            "format_id": "720",
            "height": 720,
            "width": 1280,
            "ext": "mp4",
            "vcodec": "avc1",
            "acodec": "none",
            "url": "https://example.test/720",
            "protocol": "https",
        },
        {
            "format_id": "1440",
            "height": 1440,
            "width": 2560,
            "ext": "webm",
            "vcodec": "vp9",
            "acodec": "none",
            "url": "https://example.test/1440",
            "protocol": "https",
        },
    ]
    selector = format_selector(DownloadOptions(Path("/tmp"), compatible=compatible, height=height))
    with YoutubeDL({"quiet": True}) as ydl:
        selected = list(
            ydl.build_format_selector(selector)(
                {"formats": formats, "incomplete_formats": False, "has_merged_format": False}
            )
        )
    assert selected[0]["height"] == expected
    assert len(selected[0]["requested_formats"]) == 2
