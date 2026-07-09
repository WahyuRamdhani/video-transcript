"""Audio extraction + speech-to-text transcription."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

# 24MB stays comfortably under the Whisper API's 25MB upload limit.
_MAX_CHUNK_BYTES = 24 * 1024 * 1024
_CHUNK_SECONDS = 600  # 10 minutes per chunk before compression accounting


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str


def extract_audio(video_path: Path, out_dir: Path) -> Path:
    """Extract a mono 16kHz mp3 track from the given video/audio file."""
    out_path = out_dir / f"{video_path.stem}.mp3"
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(video_path),
            "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k",
            str(out_path),
        ],
        check=True,
        capture_output=True,
    )
    return out_path


def _get_duration_seconds(audio_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def _split_audio(audio_path: Path, out_dir: Path) -> list[Path]:
    """Split audio into chunks small enough for the Whisper API, if needed."""
    if audio_path.stat().st_size <= _MAX_CHUNK_BYTES:
        return [audio_path]

    duration = _get_duration_seconds(audio_path)
    chunks: list[Path] = []
    start = 0.0
    index = 0
    while start < duration:
        chunk_path = out_dir / f"{audio_path.stem}_part{index}.mp3"
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(audio_path),
                "-ss", str(start), "-t", str(_CHUNK_SECONDS),
                "-ac", "1", "-ar", "16000", "-b:a", "64k",
                str(chunk_path),
            ],
            check=True,
            capture_output=True,
        )
        chunks.append(chunk_path)
        start += _CHUNK_SECONDS
        index += 1
    return chunks


def transcribe(audio_path: Path, work_dir: Path, client: OpenAI | None = None) -> list[TranscriptSegment]:
    """Transcribe audio into timestamped segments using the OpenAI Whisper API."""
    client = client or OpenAI()
    chunks = _split_audio(audio_path, work_dir)

    segments: list[TranscriptSegment] = []
    time_offset = 0.0

    for chunk_path in chunks:
        with open(chunk_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )
        for seg in response.segments or []:
            segments.append(
                TranscriptSegment(
                    start=seg.start + time_offset,
                    end=seg.end + time_offset,
                    text=seg.text.strip(),
                )
            )
        time_offset += _get_duration_seconds(chunk_path)

    return segments
