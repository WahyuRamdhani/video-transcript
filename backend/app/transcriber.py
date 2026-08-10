"""Audio extraction + speech-to-text transcription.

Uses the OpenAI Whisper API when OPENAI_API_KEY is configured, and falls
back to a local, free, open-source Whisper model (via faster-whisper)
otherwise. No code changes needed to switch between them — just whether
the API key is set.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

from .paths import ffmpeg_path, ffprobe_path

# Avoids "[WinError 1314] A required privilege is not held by the client"
# when caching downloaded model files on Windows: creating symlinks there
# needs Administrator rights or Developer Mode enabled, so tell the cache
# to copy files instead. Must be set before faster_whisper/huggingface_hub
# is imported (see _get_local_model, which imports it lazily).
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")

# 24MB stays comfortably under the Whisper API's 25MB upload limit.
_MAX_CHUNK_BYTES = 24 * 1024 * 1024
_CHUNK_SECONDS = 600  # 10 minutes per chunk before compression accounting

# Local model size: tiny/base/small/medium/large-v3/large-v3-turbo. Bigger =
# more accurate, slower, more RAM. "large-v3-turbo" keeps most of large-v3's
# accuracy (same encoder, a much lighter decoder) at close to "small"/"medium"
# speed, so it's the default. Drop to "small" or "base" if it's too slow on
# your machine.
_LOCAL_MODEL_SIZE = os.environ.get("WHISPER_LOCAL_MODEL", "large-v3-turbo")
_local_model = None


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
            ffmpeg_path(), "-y", "-i", str(video_path),
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
            ffprobe_path(), "-v", "error", "-show_entries", "format=duration",
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
                ffmpeg_path(), "-y", "-i", str(audio_path),
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


def _has_openai_key() -> bool:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    return bool(key) and key != "sk-..."


def transcribe(
    audio_path: Path,
    work_dir: Path,
    client: OpenAI | None = None,
    language: str | None = None,
    vocabulary: str | None = None,
) -> list[TranscriptSegment]:
    """Transcribe audio into timestamped segments.

    ``language`` is an ISO-639-1 code (e.g. "id" for Indonesian, "en" for
    English). Leave it None/empty to auto-detect the spoken language.

    ``vocabulary`` is a free-text hint of names/terms likely to appear (e.g.
    a company name, jargon) that biases the model toward recognizing and
    spelling them correctly, instead of guessing phonetically.
    """
    language = language or None
    vocabulary = vocabulary or None
    if client is not None or _has_openai_key():
        return _transcribe_openai(audio_path, work_dir, client, language, vocabulary)
    return _transcribe_local(audio_path, language, vocabulary)


def _transcribe_openai(
    audio_path: Path,
    work_dir: Path,
    client: OpenAI | None,
    language: str | None,
    vocabulary: str | None,
) -> list[TranscriptSegment]:
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
                **({"language": language} if language else {}),
                **({"prompt": vocabulary} if vocabulary else {}),
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


def _get_local_model():
    global _local_model
    if _local_model is None:
        from faster_whisper import WhisperModel
        _local_model = WhisperModel(_LOCAL_MODEL_SIZE, device="cpu", compute_type="int8")
    return _local_model


def _transcribe_local(
    audio_path: Path, language: str | None, vocabulary: str | None
) -> list[TranscriptSegment]:
    """Transcribe using a local, free, open-source Whisper model (no API key)."""
    model = _get_local_model()
    raw_segments, _info = model.transcribe(
        str(audio_path), vad_filter=True, language=language, initial_prompt=vocabulary
    )
    return [
        TranscriptSegment(start=seg.start, end=seg.end, text=seg.text.strip())
        for seg in raw_segments
    ]
