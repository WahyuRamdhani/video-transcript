from __future__ import annotations

import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .jobs import create_job, get_job, run_pipeline
from .models import CreateJobRequest, CreateJobResponse, JobStatus, JobStatusResponse

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
