"""Entry point for the packaged desktop app.

Starts the local server and opens the default browser to it. This is what
gets compiled into the distributable .exe.
"""
from __future__ import annotations

import threading
import time
import webbrowser

import uvicorn

from app.main import app

HOST = "127.0.0.1"
PORT = 8000


def _open_browser_when_ready() -> None:
    time.sleep(1.5)
    webbrowser.open(f"http://{HOST}:{PORT}")


if __name__ == "__main__":
    threading.Thread(target=_open_browser_when_ready, daemon=True).start()
    print(f"Starting Video Transcript Exporter at http://{HOST}:{PORT}")
    print("Keep this window open while using the app. Close it to stop the server.")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
