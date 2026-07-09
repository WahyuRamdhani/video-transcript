# Video Transcript Exporter

A small web app that takes the URL of a page containing a video, transcribes
the audio, and exports a structured, timestamped DOCX transcript.

## How it works

1. **Fetch** — given a page URL, the backend tries `yt-dlp` first (covers
   YouTube, Vimeo, Wistia, etc.). If the site isn't recognized, it falls back
   to scraping the page HTML for a direct `<video>`/`og:video` source. Pages
   that require login can be accessed by pasting the browser's `Cookie`
   header value into the optional field in the UI.
2. **Transcribe** — audio is extracted with `ffmpeg` and sent to the OpenAI
   Whisper API (`whisper-1`) for timestamped transcription. Long audio is
   automatically chunked to stay under the API's upload limit.
3. **Export** — the timestamped segments are grouped into paragraphs and
   sections (based on pause length) and rendered into a `.docx` file with
   `python-docx`, including a title, source URL, generation date, and
   per-paragraph timestamps.

## Project layout

```
backend/
  app/
    main.py            FastAPI app + HTTP endpoints
    jobs.py             In-memory job store + background pipeline
    video_extractor.py  URL -> downloaded video file
    transcriber.py       video -> timestamped transcript segments
    doc_builder.py       segments -> structured .docx
    models.py            request/response schemas
  requirements.txt
frontend/
  index.html / app.js / styles.css   Minimal UI, no build step
```

## Setup

### Prerequisites

- Python 3.11+
- [`ffmpeg`](https://ffmpeg.org/) installed and on your `PATH` (used for audio
  extraction and chunking)
- An OpenAI API key with access to the Whisper transcription API

### Install

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
# then edit .env and set OPENAI_API_KEY
```

### Run

```bash
cd backend
export $(cat ../.env | xargs)   # or use your preferred env loader
uvicorn app.main:app --reload
```

Open http://localhost:8000 — the FastAPI app serves the frontend directly.

## Usage

1. Paste the URL of the page that contains the video.
2. If the page requires login, open your browser's dev tools (Network tab),
   reload the page while logged in, find the request to that page, and copy
   its `Cookie` request header value into the "Session cookie" field.
3. Click **Transcribe video** and wait — downloading + transcription can take
   a few minutes depending on video length.
4. Download the generated `.docx` transcript.

## Notes & limitations

- Jobs and generated documents are stored in-memory / on local disk
  (`backend/data/jobs/`) — this is a single-process MVP, not built for
  horizontal scaling or durability across restarts.
- Cookie values are used only to fetch the video for that one job and are not
  persisted to disk.
- Sites that stream video via DRM-protected players generally cannot be
  downloaded by this tool.
