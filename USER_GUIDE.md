# Using Video Transcript Exporter

Record the audio of a video playing in Chrome and turn it into a written,
timestamped Word document — no installation, no account.

## Before you start

- **Use Google Chrome or Microsoft Edge.** Recording audio from a browser
  tab depends on a feature only those two support well.
- **Keep the black console window open.** When you launch the app, a plain
  black console window appears alongside your browser. That window *is* the
  app running — minimize it if you like, but don't close it until you're
  done.
- **Internet is only needed the first time.** The very first transcription
  downloads a small speech-recognition model (about 150MB). After that,
  everything runs on this computer.

## Step by step

1. **Open the app.** Double-click `VideoTranscriptExporter.exe`.

   If Windows shows a blue "Windows protected your PC" warning, that's
   normal for a small program that isn't from a large registered publisher
   — not a sign of a virus. Click **More info**, then **Run anyway**.

2. **Wait for the browser to open.** A console window appears first,
   followed a few seconds later by your browser opening automatically to
   the app. Leave both open.

3. **Open your video in a new tab.** In a *separate* Chrome tab, open the
   page with the video you want transcribed. Get it paused and ready —
   don't play it yet.

4. **(Optional) Improve accuracy first.** At the top of the app, set
   **Spoken language** if it's not English (e.g. Bahasa Indonesia), and
   type any names or jargon likely to come up — a company name, people's
   names, technical terms — into **Known names/terms**. This helps the
   transcript get them right instead of guessing by sound.

5. **Start recording.** Switch back to the app's tab and click
   **Start recording**.

6. **Share the video's tab with audio.** Chrome shows a sharing window.
   Click **Chrome Tab** at the top, select the tab with your video, and
   check **"Also share tab audio"** before clicking **Share**.

7. **Play the video.** Switch to the video's tab and press play. Let it run
   all the way through.

8. **Stop and transcribe.** Switch back to the app tab and click
   **Stop & transcribe**.

9. **Wait for processing.** The status moves through "Transcribing..." and
   "Building the document...". This roughly tracks the length of the video,
   plus a few extra minutes the very first time, while the speech
   recognition model downloads.

10. **Download the transcript.** Click **Download transcript (.docx)** and
    open it in Word — a title, source info, and the full transcript
    organized into timestamped sections.

## If something looks off

**The sharing window has no "share tab audio" option**
Make sure you clicked **Chrome Tab** at the top of the sharing window, not
"Entire Screen" or "Window" — the audio checkbox only appears for the Tab
option.

**Nothing happened after double-clicking the file**
Check if the console window opened behind your browser windows. If it
flashed and disappeared instead, something failed to start — take a
screenshot and share it for help.

**It's been several minutes with no result**
Normal on the first run of the day, or for long videos — transcription runs
on this computer's own processor rather than a fast server. Expect it to
take about as long as the video itself, sometimes a little more.

**I'm done for now**
Close the console window — that's the correct way to shut the app down.
Nothing needs to be uninstalled or cleaned up.
