"""Resolve a webpage URL to a downloaded video/audio file.

Handles two cases:
1. Sites yt-dlp already knows how to extract (YouTube, Vimeo, Wistia, ...).
2. Arbitrary/private sites that simply embed an HTML5 <video> tag or an
   og:video meta tag, optionally behind a login (cookie-gated).
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


class VideoExtractionError(RuntimeError):
    """Raised when no downloadable video could be found at the given URL."""


def download_video(page_url: str, cookie_header: str | None, work_dir: Path) -> Path:
    """Download the video found at ``page_url`` into ``work_dir``.

    Returns the path to the downloaded media file.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    file_stem = f"video_{uuid.uuid4().hex}"

    try:
        return _download_with_ytdlp(page_url, cookie_header, work_dir, file_stem)
    except DownloadError:
        pass  # fall through to the generic HTML scraper

    direct_url = _find_direct_video_url(page_url, cookie_header)
    if not direct_url:
        raise VideoExtractionError(
            "Could not find a downloadable video on that page. "
            "If the page requires login, provide the session cookie."
        )
    return _download_direct(direct_url, page_url, cookie_header, work_dir, file_stem)


def _download_with_ytdlp(page_url: str, cookie_header: str | None, work_dir: Path, file_stem: str) -> Path:
    ydl_opts = {
        "outtmpl": str(work_dir / f"{file_stem}.%(ext)s"),
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "http_headers": _headers(cookie_header),
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(page_url, download=True)
        filename = ydl.prepare_filename(info)
        return Path(filename)


def _headers(cookie_header: str | None) -> dict:
    headers = {"User-Agent": USER_AGENT}
    if cookie_header:
        headers["Cookie"] = cookie_header
    return headers


def _find_direct_video_url(page_url: str, cookie_header: str | None) -> str | None:
    resp = requests.get(page_url, headers=_headers(cookie_header), timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    candidates: list[str] = []

    for video_tag in soup.find_all("video"):
        if video_tag.get("src"):
            candidates.append(video_tag["src"])
        for source_tag in video_tag.find_all("source"):
            if source_tag.get("src"):
                candidates.append(source_tag["src"])

    og_video = soup.find("meta", property="og:video")
    if og_video and og_video.get("content"):
        candidates.append(og_video["content"])
    og_video_url = soup.find("meta", property="og:video:url")
    if og_video_url and og_video_url.get("content"):
        candidates.append(og_video_url["content"])

    for match in re.findall(r"https?://[^\s\"'<>]+\.(?:mp4|m4v|mov|webm|m3u8)(?:\?[^\s\"'<>]*)?", resp.text):
        candidates.append(match)

    if not candidates:
        return None

    return urljoin(page_url, candidates[0])


def _download_direct(direct_url: str, page_url: str, cookie_header: str | None, work_dir: Path, file_stem: str) -> Path:
    headers = _headers(cookie_header)
    headers["Referer"] = page_url
    ext = _guess_extension(direct_url)
    out_path = work_dir / f"{file_stem}{ext}"

    with requests.get(direct_url, headers=headers, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)

    return out_path


def _guess_extension(url: str) -> str:
    match = re.search(r"\.(mp4|m4v|mov|webm|m3u8)(?:\?|$)", url)
    return f".{match.group(1)}" if match else ".mp4"
