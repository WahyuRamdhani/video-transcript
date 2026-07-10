# Building the distributable app

This turns the app into something someone else can double-click, without
installing Python, ffmpeg, or anything else themselves. There's a build for
Windows (a single `.exe`) and one for macOS (a folder + double-click
launcher). **Build each one on that same OS** — PyInstaller bundles
platform-native binaries, so a build done on one OS will not run on another.

## Windows

### 1. Get ffmpeg binaries to bundle

Download a Windows static ffmpeg build, e.g. from https://www.gyan.dev/ffmpeg/builds/
(the "release essentials" build is fine). Extract it, then copy two files
into a new `backend/bin/` folder:

```
backend/bin/ffmpeg.exe
backend/bin/ffprobe.exe
```

(Both come from the `bin/` folder inside the ffmpeg download.)

### 2. Set up the build environment

From the `backend/` folder, with your existing venv active:

```
pip install -r requirements.txt
pip install -r requirements-build.txt
```

### 3. Build

Still from `backend/`:

```
pyinstaller video_transcript.spec
```

This takes a few minutes — it's bundling a Python runtime, FastAPI, ffmpeg,
and the Whisper inference engine. Expect some warnings in the output; they're
usually fine to ignore unless the build fails outright.

### 4. Find and test the result

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

### 5. Distribute it

Copy `VideoTranscriptExporter.exe` to the other PC (USB drive, shared
drive, etc.) — it's a single file, several hundred MB. When they run it,
Windows SmartScreen will likely show "Windows protected your PC" since the
file isn't signed by a known publisher. They need to click **"More info"**
→ **"Run anyway"**. This is expected for an unsigned indie tool, not a sign
of a problem — let people you send it to know in advance so it doesn't look
like a virus warning.

### Rebuilding after code changes

Re-run step 3 (`pyinstaller video_transcript.spec`) — no need to repeat
steps 1–2 unless ffmpeg or the build tooling changed.

## macOS

Unlike the Windows build, this doesn't produce a single file — it produces a
folder plus a double-click `.command` launcher, because macOS doesn't
automatically show a visible log window for double-clicked apps the way
Windows does. The `.command` file opens Terminal and runs the app inside it,
which gives the same "see it running, close the window to stop it" behavior
as the Windows console.

### 1. Get ffmpeg binaries to bundle

```
brew install ffmpeg
which ffmpeg
which ffprobe
```

Copy both into a new `backend/bin/` folder (no `.exe` extension on macOS):

```
mkdir -p backend/bin
cp "$(which ffmpeg)" backend/bin/ffmpeg
cp "$(which ffprobe)" backend/bin/ffprobe
```

### 2. Set up the build environment

From the `backend/` folder, with your venv active:

```
pip install -r requirements.txt
pip install -r requirements-build.txt
```

### 3. Build

Still from `backend/`:

```
pyinstaller video_transcript_mac.spec
```

### 4. Assemble the distributable folder

```
cp "mac/Launch VideoTranscriptExporter.command" dist/
chmod +x "dist/Launch VideoTranscriptExporter.command"
```

You should now have, inside `backend/dist/`:

```
VideoTranscriptExporter/              (folder — the built app)
Launch VideoTranscriptExporter.command   (the launcher)
```

These two must stay next to each other — the `.command` file expects the
`VideoTranscriptExporter` folder right beside it.

### 5. Test it

Double-click `Launch VideoTranscriptExporter.command` in Finder. macOS will
likely refuse to run it the first time ("cannot be opened because it is from
an unidentified developer"). Right-click (or Control-click) the file instead,
choose **Open**, then confirm **Open** again in the dialog — this only needs
to be done once. If it's still blocked, run this in Terminal, then try again:

```
xattr -cr "dist/Launch VideoTranscriptExporter.command" "dist/VideoTranscriptExporter"
```

A Terminal window opens showing server logs, and shortly after, the default
browser opens to the app. Try recording and transcribing something short to
confirm it works end to end. Closing the Terminal window stops the app.

### 6. Distribute it

Zip the two items from step 4 together and send the zip (several hundred MB,
mostly the bundled Whisper engine and ffmpeg). Whoever receives it should
unzip it first, keep both items in the same folder, then follow the same
right-click → Open step from step 5 the first time they run it.

### Rebuilding after code changes

Re-run step 3 (`pyinstaller video_transcript_mac.spec`) — no need to repeat
steps 1–2 or re-copy the `.command` launcher unless it changed.
