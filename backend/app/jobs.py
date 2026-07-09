"""In-memory job store and background processing pipeline."""
from __future__ import annotations

import logging
import shutil
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from .doc_builder import build_document
from .models import JobStatus
from .transcriber import extract_audio, transcribe
from .video_extractor import VideoExtractionError, download_video

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
JOBS_DIR = DATA_DIR / "jobs"


@dataclass
class Job:
    id: str
    status: JobStatus = JobStatus.PENDING
    error: str | None = None
    document_path: Path | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def set_status(self, status: JobStatus) -> None:
        with self._lock:
            self.status = status

    def set_error(self, message: str) -> None:
        with self._lock:
            self.status = JobStatus.ERROR
            self.error = message


_jobs: dict[str, Job] = {}
_jobs_lock = threading.Lock()


def create_job() -> Job:
    job = Job(id=uuid.uuid4().hex)
    with _jobs_lock:
        _jobs[job.id] = job
    return job


def get_job(job_id: str) -> Job | None:
    with _jobs_lock:
        return _jobs.get(job_id)


def run_pipeline(job_id: str, video_url: str, cookie: str | None, title: str | None) -> None:
    job = get_job(job_id)
    if job is None:
        return

    work_dir = JOBS_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        job.set_status(JobStatus.DOWNLOADING)
        video_path = download_video(video_url, cookie, work_dir)

        job.set_status(JobStatus.TRANSCRIBING)
        audio_path = extract_audio(video_path, work_dir)
        segments = transcribe(audio_path, work_dir)

        job.set_status(JobStatus.BUILDING_DOCUMENT)
        doc_title = title or "Video Transcript"
        out_path = work_dir / "transcript.docx"
        build_document(segments, video_url, doc_title, out_path)

        job.document_path = out_path
        job.set_status(JobStatus.DONE)
    except VideoExtractionError as exc:
        logger.warning("Video extraction failed for job %s: %s", job_id, exc)
        job.set_error(str(exc))
    except Exception as exc:  # noqa: BLE001 - surface any failure to the client
        logger.exception("Pipeline failed for job %s", job_id)
        job.set_error(f"Transcription failed: {exc}")
    finally:
        _cleanup_media_files(work_dir)


def _cleanup_media_files(work_dir: Path) -> None:
    """Remove intermediate audio/video files, keeping only the final document."""
    for item in work_dir.glob("*"):
        if item.name != "transcript.docx":
            try:
                item.unlink()
            except IsADirectoryError:
                shutil.rmtree(item, ignore_errors=True)
