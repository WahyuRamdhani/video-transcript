#!/bin/bash
# Double-click launcher for macOS. Must sit next to a "VideoTranscriptExporter"
# folder (the PyInstaller build output) when distributed.
cd "$(dirname "$0")/VideoTranscriptExporter" || exit 1
./VideoTranscriptExporter
