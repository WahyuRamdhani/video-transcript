const form = document.getElementById("transcribe-form");
const submitBtn = document.getElementById("submit-btn");
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

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  resetPanels();

  const video_url = document.getElementById("video_url").value.trim();
  const title = document.getElementById("title").value.trim();
  const cookie = document.getElementById("cookie").value.trim();

  submitBtn.disabled = true;
  statusPanel.classList.remove("hidden");
  statusText.textContent = "Starting...";
  spinner.classList.remove("hidden");

  try {
    const res = await fetch("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        video_url,
        title: title || null,
        cookie: cookie || null,
      }),
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Request failed (${res.status})`);
    }

    const { job_id } = await res.json();
    pollStatus(job_id);
  } catch (err) {
    showError(err.message);
  }
});

function pollStatus(jobId) {
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
        submitBtn.disabled = false;
      } else if (job.status === "error") {
        clearInterval(pollTimer);
        spinner.classList.add("hidden");
        showError(job.error || "Something went wrong.");
        submitBtn.disabled = false;
      }
    } catch (err) {
      clearInterval(pollTimer);
      spinner.classList.add("hidden");
      showError(err.message);
      submitBtn.disabled = false;
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
