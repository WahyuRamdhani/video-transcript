const statusPanel = document.getElementById("status-panel");
const statusText = document.getElementById("status-text");
const spinner = document.getElementById("spinner");
const downloadLink = document.getElementById("download-link");
const errorPanel = document.getElementById("error-panel");
const errorText = document.getElementById("error-text");

const STATUS_LABELS = {
  pending: "Queued...",
  downloading: "Downloading video...",
  transcribing: "Transcribing audio (this can take a few minutes)...",
  building_document: "Building the document...",
  done: "Done!",
  error: "Failed",
};

let pollTimer = null;

const languageSelect = document.getElementById("language-select");
const vocabularyInput = document.getElementById("vocabulary-input");

// ---------- Tabs ----------
const tabButtons = document.querySelectorAll(".tab-btn");
const tabPanels = {
  record: document.getElementById("tab-record"),
  url: document.getElementById("tab-url"),
};

tabButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    tabButtons.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    Object.entries(tabPanels).forEach(([key, panel]) => {
      panel.classList.toggle("hidden", key !== btn.dataset.tab);
    });
    resetPanels();
  });
});

// ---------- URL form ----------
const form = document.getElementById("transcribe-form");
const submitBtn = document.getElementById("submit-btn");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  resetPanels();

  const video_url = document.getElementById("video_url").value.trim();
  const title = document.getElementById("title").value.trim();
  const cookie = document.getElementById("cookie").value.trim();

  if (!video_url) return;

  submitBtn.disabled = true;
  beginStatus();

  try {
    const res = await fetch("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        video_url,
        title: title || null,
        cookie: cookie || null,
        language: languageSelect.value || null,
        vocabulary: vocabularyInput.value.trim() || null,
      }),
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Request failed (${res.status})`);
    }

    const { job_id } = await res.json();
    pollStatus(job_id, () => { submitBtn.disabled = false; });
  } catch (err) {
    submitBtn.disabled = false;
    showError(err.message);
  }
});

// ---------- Record while it plays ----------
const startRecordBtn = document.getElementById("start-record-btn");
const stopRecordBtn = document.getElementById("stop-record-btn");
const recordTimer = document.getElementById("record-timer");
const recordTitleInput = document.getElementById("record-title");

let mediaRecorder = null;
let recordedChunks = [];
let captureStream = null;
let recordingSeconds = 0;
let recordingInterval = null;

startRecordBtn.addEventListener("click", async () => {
  resetPanels();

  if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
    showError("Your browser doesn't support tab/screen audio capture. Try Chrome or Edge on desktop.");
    return;
  }

  try {
    captureStream = await navigator.mediaDevices.getDisplayMedia({
      video: true,
      audio: true,
    });
  } catch (err) {
    showError("Screen/tab sharing was cancelled or denied.");
    return;
  }

  const audioTracks = captureStream.getAudioTracks();
  if (audioTracks.length === 0) {
    captureStream.getTracks().forEach((t) => t.stop());
    showError('No audio was shared. When prompted, choose the browser tab playing the video and check "Share tab audio".');
    return;
  }

  // Stop the video track immediately — we only need audio.
  captureStream.getVideoTracks().forEach((t) => t.stop());

  const audioOnlyStream = new MediaStream(audioTracks);
  recordedChunks = [];
  mediaRecorder = new MediaRecorder(audioOnlyStream);
  mediaRecorder.ondataavailable = (event) => {
    if (event.data.size > 0) recordedChunks.push(event.data);
  };
  mediaRecorder.onstop = handleRecordingStopped;

  // If the user revokes sharing from the browser's own UI, stop cleanly.
  audioTracks[0].addEventListener("ended", () => {
    if (mediaRecorder && mediaRecorder.state !== "inactive") mediaRecorder.stop();
  });

  mediaRecorder.start();
  recordingSeconds = 0;
  recordTimer.textContent = "00:00";
  recordTimer.classList.remove("hidden");
  recordingInterval = setInterval(() => {
    recordingSeconds += 1;
    const m = String(Math.floor(recordingSeconds / 60)).padStart(2, "0");
    const s = String(recordingSeconds % 60).padStart(2, "0");
    recordTimer.textContent = `${m}:${s}`;
  }, 1000);

  startRecordBtn.classList.add("hidden");
  stopRecordBtn.classList.remove("hidden");
});

stopRecordBtn.addEventListener("click", () => {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }
  if (captureStream) {
    captureStream.getTracks().forEach((t) => t.stop());
  }
  clearInterval(recordingInterval);
  stopRecordBtn.classList.add("hidden");
  recordTimer.classList.add("hidden");
});

async function handleRecordingStopped() {
  startRecordBtn.classList.remove("hidden");
  startRecordBtn.disabled = true;

  if (recordedChunks.length === 0) {
    startRecordBtn.disabled = false;
    showError("No audio was captured.");
    return;
  }

  beginStatus();
  statusText.textContent = "Uploading recording...";

  const blob = new Blob(recordedChunks, { type: mediaRecorder.mimeType || "audio/webm" });
  const formData = new FormData();
  formData.append("audio", blob, "recording.webm");
  const title = recordTitleInput.value.trim();
  if (title) formData.append("title", title);
  if (languageSelect.value) formData.append("language", languageSelect.value);
  if (vocabularyInput.value.trim()) formData.append("vocabulary", vocabularyInput.value.trim());

  try {
    const res = await fetch("/api/jobs/upload", { method: "POST", body: formData });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Upload failed (${res.status})`);
    }
    const { job_id } = await res.json();
    pollStatus(job_id, () => { startRecordBtn.disabled = false; });
  } catch (err) {
    startRecordBtn.disabled = false;
    showError(err.message);
  }
}

// ---------- Shared status polling ----------
function beginStatus() {
  statusPanel.classList.remove("hidden");
  statusText.textContent = "Starting...";
  spinner.classList.remove("hidden");
  downloadLink.classList.add("hidden");
}

function pollStatus(jobId, onSettled) {
  pollTimer = setInterval(async () => {
    try {
      const res = await fetch(`/api/jobs/${jobId}`);
      if (!res.ok) throw new Error("Lost track of the job.");
      const job = await res.json();

      statusText.textContent = STATUS_LABELS[job.status] || job.status;

      if (job.status === "done") {
        clearInterval(pollTimer);
        spinner.classList.add("hidden");
        downloadLink.href = job.download_url;
        downloadLink.classList.remove("hidden");
        onSettled();
      } else if (job.status === "error") {
        clearInterval(pollTimer);
        spinner.classList.add("hidden");
        showError(job.error || "Something went wrong.");
        onSettled();
      }
    } catch (err) {
      clearInterval(pollTimer);
      spinner.classList.add("hidden");
      showError(err.message);
      onSettled();
    }
  }, 3000);
}

function showError(message) {
  errorPanel.classList.remove("hidden");
  errorText.textContent = message;
  spinner.classList.add("hidden");
}

function resetPanels() {
  if (pollTimer) clearInterval(pollTimer);
  errorPanel.classList.add("hidden");
  downloadLink.classList.add("hidden");
  statusPanel.classList.add("hidden");
}
