"""Path resolution that works both running from source and frozen into an .exe."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_dir() -> Path:
    """Base directory for bundled, read-only resources (frontend files, ffmpeg)."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent.parent


def data_dir() -> Path:
    """Base directory for writable runtime data (job files, generated documents)."""
    if is_frozen():
        base = os.environ.get("LOCALAPPDATA") or str(Path.home())
        directory = Path(base) / "VideoTranscriptExporter"
    else:
        directory = Path(__file__).resolve().parent.parent / "data"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _bundled_binary(name: str) -> str:
    candidate = resource_dir() / "bin" / name
    if candidate.exists():
        return str(candidate)
    return name[:-4] if name.endswith(".exe") else name  # fall back to PATH lookup


def ffmpeg_path() -> str:
    return _bundled_binary("ffmpeg.exe" if os.name == "nt" else "ffmpeg")


def ffprobe_path() -> str:
    return _bundled_binary("ffprobe.exe" if os.name == "nt" else "ffprobe")
