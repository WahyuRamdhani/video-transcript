from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    BUILDING_DOCUMENT = "building_document"
    DONE = "done"
    ERROR = "error"


class CreateJobRequest(BaseModel):
    video_url: str = Field(..., description="URL of the page or file containing the video")
    cookie: str | None = Field(
        default=None,
        description="Raw Cookie header value, needed if the page requires login",
    )
    title: str | None = Field(default=None, description="Title for the exported document")


class CreateJobResponse(BaseModel):
    job_id: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    error: str | None = None
    download_url: str | None = None
