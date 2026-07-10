# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec. Build with: pyinstaller video_transcript.spec

Run from the backend/ directory. Requires backend/bin/ffmpeg.exe and
backend/bin/ffprobe.exe to exist first (see PACKAGING.md).
"""
from PyInstaller.utils.hooks import collect_all

datas = [("../frontend", "frontend")]
binaries = [("bin/ffmpeg.exe", "bin"), ("bin/ffprobe.exe", "bin")]
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
    a.binaries,
    a.datas,
    [],
    name="VideoTranscriptExporter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    icon=None,
)
