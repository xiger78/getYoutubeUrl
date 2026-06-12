# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — macOS / Windows / Linux 공통."""

import sys
from pathlib import Path

ROOT = Path(SPEC).resolve().parent
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

block_cipher = None

a = Analysis(
    [str(ROOT / "getYoutubeUrl.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "docs"), "docs"),
    ],
    hiddenimports=[
        "runtime_env",
        "i18n",
        "kar_maker",
        "syncedlyrics",
        "mido",
        "mido.midifiles",
        "mido.midifiles.midifiles",
        "numpy",
        "vlc",
        "yt_dlp",
        "yt_dlp.extractor",
        "yt_dlp.postprocessor",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="getYoutubeUrl",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="getYoutubeUrl",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="getYoutubeUrl.app",
        icon=None,
        bundle_identifier="com.github.xiger78.getYoutubeUrl",
        version=VERSION,
        info_plist={
            "CFBundleName": "getYoutubeUrl",
            "CFBundleDisplayName": "getYoutubeUrl",
            "CFBundleVersion": VERSION,
            "CFBundleShortVersionString": VERSION,
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "10.13.0",
        },
    )
