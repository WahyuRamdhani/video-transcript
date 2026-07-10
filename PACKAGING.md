# Building the distributable .exe

This turns the app into a single `VideoTranscriptExporter.exe` that someone
else can double-click, without installing Python, ffmpeg, or anything else
themselves. Build this **on Windows** (PyInstaller bundles platform-native
binaries, so a build done on another OS will not work on Windows).

## 1. Get ffmpeg binaries to bundle

Download a Windows static ffmpeg build, e.g. from https://www.gyan.dev/ffmpeg/builds/
(the "release essentials" build is fine). Extract it, then copy two files
into a new `backend/bin/` folder:

```
backend/bin/ffmpeg.exe
backend/bin/ffprobe.exe
```

(Both come from the `bin/` folder inside the ffmpeg download.)

## 2. Set up the build environment

From the `backend/` folder, with your existing venv active:

```
pip install -r requirements.txt
pip install -r requirements-build.txt
```

## 3. Build

Still from `backend/`:

```
pyinstaller video_transcript.spec
```

This takes a few minutes — it's bundling a Python runtime, FastAPI, ffmpeg,
and the Whisper inference engine. Expect some warnings in the output; they're
usually fine to ignore unless the build fails outright.

## 4. Find and test the result

The finished file is at:

```
backend/dist/VideoTranscriptExporter.exe
```

Double-click it. A console window opens (showing server logs — that's
expected, this build keeps it visible for debugging), and after a moment
your default browser should open to the app automatically. Try recording and
transcribing something short to confirm it actually works end to end.

The first time you transcribe something, it still downloads the Whisper
model weights (~150MB) into the current Windows user's profile — that step
needs internet access once, same as running from source. Model weights are
not bundled into the exe itself in this version.

## 5. Distribute it

Copy `VideoTranscriptExporter.exe` to the other PC (USB drive, shared
drive, etc.) — it's a single file, several hundred MB. When they run it,
Windows SmartScreen will likely show "Windows protected your PC" since the
file isn't signed by a known publisher. They need to click **"More info"**
→ **"Run anyway"**. This is expected for an unsigned indie tool, not a sign
of a problem — let people you send it to know in advance so it doesn't look
like a virus warning.

## Rebuilding after code changes

Re-run step 3 (`pyinstaller video_transcript.spec`) — no need to repeat
steps 1–2 unless ffmpeg or the build tooling changed.
