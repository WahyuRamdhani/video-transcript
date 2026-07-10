from __future__ import annotations

import threading
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .jobs import JOBS_DIR, create_job, get_job, run_audio_pipeline, run_pipeline
from .models import CreateJobRequest, CreateJobResponse, JobStatus, JobStatusResponse

_AUDIO_EXTENSION_BY_CONTENT_TYPE = {
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
    "audio/mp4": ".m4a",
    "audio/mpeg": ".mp3",
}

app = FastAPI(title="Video Transcript Exporter")

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@app.post("/api/jobs", response_model=CreateJobResponse)
def create_transcription_job(payload: CreateJobRequest) -> CreateJobResponse:
    job = create_job()
    thread = threading.Thread(
        target=run_pipeline,
        args=(job.id, payload.video_url, payload.cookie, payload.title),
        daemon=True,
    )
    thread.start()
    return CreateJobResponse(job_id=job.id)


@app.post("/api/jobs/upload", response_model=CreateJobResponse)
async def create_transcription_job_from_upload(
    audio: UploadFile = File(...),
    title: str | None = Form(default=None),
) -> CreateJobResponse:
    job = create_job()
    work_dir = JOBS_DIR / job.id
    work_dir.mkdir(parents=True, exist_ok=True)

    extension = _AUDIO_EXTENSION_BY_CONTENT_TYPE.get(audio.content_type, ".webm")
    raw_audio_path = work_dir / f"recording{extension}"
    with open(raw_audio_path, "wb") as f:
        f.write(await audio.read())

    thread = threading.Thread(
        target=run_audio_pipeline,
        args=(job.id, raw_audio_path, title),
        daemon=True,
    )
    thread.start()
    return CreateJobResponse(job_id=job.id)


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str) -> JobStatusResponse:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    download_url = f"/api/jobs/{job_id}/download" if job.status == JobStatus.DONE else None
    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        error=job.error,
        download_url=download_url,
    )


@app.get("/api/jobs/{job_id}/download")
def download_transcript(job_id: str) -> FileResponse:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.DONE or job.document_path is None:
        raise HTTPException(status_code=409, detail="Transcript is not ready yet")

    return FileResponse(
        path=job.document_path,
        filename="transcript.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
