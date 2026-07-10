# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec for macOS. Build with: pyinstaller video_transcript_mac.spec

Run from the backend/ directory on a Mac. Requires backend/bin/ffmpeg and
backend/bin/ffprobe to exist first (see PACKAGING.md). Produces a folder at
dist/VideoTranscriptExporter/ — pair it with mac/Launch VideoTranscriptExporter.command
for a Finder-double-clickable launcher.
"""
from PyInstaller.utils.hooks import collect_all

datas = [("../frontend", "frontend")]
binaries = [("bin/ffmpeg", "bin"), ("bin/ffprobe", "bin")]
hiddenimports = []

for pkg in ("faster_whisper", "ctranslate2", "tokenizers", "huggingface_hub", "uvicorn"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VideoTranscriptExporter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="VideoTranscriptExporter",
)
