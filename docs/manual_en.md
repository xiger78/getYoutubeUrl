# getYoutubeUrl User Manual (English)

GUI app for YouTube search, playback, lyrics, MP3/MV download, and local MP3 files. No API key required.

![Main window (English)](screenshots/en.png)

---

## Table of Contents

1. [Install & Run](#install--run)
2. [Screen Layout](#screen-layout)
3. [Language](#language)
4. [Search](#search)
5. [Playlist](#playlist)
6. [Music Videos](#music-videos)
7. [Local MP3](#local-mp3)
8. [Playback Controls](#playback-controls)
9. [Lyrics](#lyrics)
10. [Shortcuts](#shortcuts)
11. [Troubleshooting](#troubleshooting)
12. [Other Commands](#other-commands)

---

## Install & Run

```bash
# macOS
./setup-mac.sh && ./run.sh

# Linux
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
sudo apt install -y python3-tk vlc ffmpeg && ./run.sh

# Windows: setup-windows.bat → run-windows.bat
```

---

## Screen Layout

| Area | Description |
|------|-------------|
| Top | Search type, query, count, Search |
| Results | YouTube result list |
| Result buttons | Add, Play MV, resolution, browser, language |
| Playlist | Queued tracks |
| Playlist buttons | MP3/MV download, MIDI, clear playlist |
| Local MP3 | Folder scan & play |
| Controls | Play, delete, clear all, shuffle, copy URLs |
| Right | Lyrics |
| Bottom | Status bar |

---

## Language

Choose **日本語 / 中文 / 한국어 / English** in the language combobox.

- Default: Japanese
- Order: 日本語 → 中文 → 한국어 → English

---

## Search

| Mode | Description |
|------|-------------|
| **🎵 Song search** | Prefer audio tracks |
| **🎬 Music video** | Prefer MVs |

Press **Search** or `Enter`.

| Action | Function |
|--------|----------|
| **Add ↓** | Add to playlist |
| **🎬 Play MV** | Open MV popup |
| **Resolution** | HD–4K for MV |
| **Open in browser** | Default browser |
| **Double-click** | Song → add / MV → play |

---

## Playlist

### Buttons (left to right)

| Button | Function |
|--------|----------|
| **⬇ Download MP3 (all)** | Save entire playlist as MP3 |
| **⬇ Download (MP3)** | Save selected track |
| **⬇ Download MV (all)** | Save all MVs as MP4 |
| **⬇ Download (MV)** | Save selected MV |
| **Create MIDI from selection** | KAR MIDI (mido·numpy) |
| **🗑 Clear all** | **Clear playlist only** |

Double-click a row to play.

---

## Music Videos

Separate popup (800×600). **F11** fullscreen, **Esc** close. High quality uses ffmpeg merge.

---

## Local MP3

1. **📁 Pick folder** — **🔄** to rescan
2. Recursive scan: `.mp3` `.m4a` `.flac` `.ogg` `.wav`
3. **Double-click** to play

---

## Playback Controls

Single row below local MP3:

| Button | Function |
|--------|----------|
| **▶ Play** | Playlist selection, else local MP3 |
| **🗑 Delete** | Remove selected item |
| **🗑 Clear all** | Clear MP3 or playlist (by focus) |
| **🔀 Shuffle** | Random play now |
| **Shuffle: Off** | Toggle shuffle |
| **Copy all URLs** | Clipboard copy |

---

## Lyrics

Right panel shows lyrics via `syncedlyrics` when playing.

---

## Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Search |
| `F11` | MV fullscreen |
| `Esc` | Close MV |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Search fails | `pip install -U yt-dlp` |
| Playback fails | Install VLC |
| Save fails | Install ffmpeg |
| No MP3 list | Check extensions, rescan with 🔄 |

**GitHub:** [https://github.com/xiger78/getYoutubeUrl](https://github.com/xiger78/getYoutubeUrl)

---

## Other Commands

Run from the project root (`getYoutubeUrl/`).

### Clone repository

```bash
git clone https://github.com/xiger78/getYoutubeUrl.git
cd getYoutubeUrl
```

### macOS

| Command / file | Description |
|----------------|-------------|
| `./setup-mac.sh` | Install uv, Python 3.11, VLC, ffmpeg, `.venv` |
| `./run.sh` | Run app (sets VLC·ffmpeg PATH) |
| `VLC_APP=/Applications/VLC.app ./run.sh` | Run with custom VLC path |
| `.venv/bin/python getYoutubeUrl.py` | Direct run (VLC env vars required) |

```bash
VLC_MACOS="$HOME/Applications/VLC.app/Contents/MacOS"
export DYLD_LIBRARY_PATH="$VLC_MACOS/lib"
export VLC_PLUGIN_PATH="$VLC_MACOS/plugins"
export PATH="$HOME/.local/bin:$PATH"
./.venv/bin/python getYoutubeUrl.py
```

### Linux (Debian / Raspberry Pi)

| Command / file | Description |
|----------------|-------------|
| `sudo bash setup-debian.sh` | Full install: apt + `.venv` + pip |
| `bash setup-debian.sh --venv-only` | `.venv`·pip only (no sudo) |
| `sudo bash setup-debian.sh --with-korean` | Install + fcitx5 Korean IME |
| `bash setup-debian.sh --help` | Show options |
| `./run.sh` | Run (`DISPLAY`, fcitx5 settings) |

```bash
python3 -m venv .venv
.venv/bin/pip install -U pip -r requirements.txt
sudo apt install -y python3-tk vlc ffmpeg

DISPLAY=:0 ./.venv/bin/python getYoutubeUrl.py

DISPLAY=:0 XAUTHORITY=$HOME/.Xauthority nohup ./run.sh >> /tmp/getYoutubeUrl.log 2>&1 &

pkill -f getYoutubeUrl.py
```

### Windows

| File | Description |
|------|-------------|
| `setup-windows.bat` | Setup via winget (falls back to manual) |
| `setup-windows.ps1` | PowerShell logic for setup bat |
| `setup-windows-manual.bat` | Manual install without winget |
| `setup-windows-manual.ps1` | PowerShell for manual bat |
| `run-windows.bat` | Launch app |
| `run-windows.ps1` | Run logic (`.venv`, VLC·ffmpeg PATH) |
| `fix-run-windows.bat` | Diagnose and fix run failures |
| `fix-run-windows.ps1` | PowerShell for fix bat |

```text
1. Double-click setup-windows.bat (or setup-windows-manual.bat)
2. Double-click run-windows.bat
   If it fails, run fix-run-windows.bat
```

```powershell
cd getYoutubeUrl
.\run-windows.ps1
```

### Manuals & screenshots

| Command | Description |
|---------|-------------|
| `.venv/bin/python scripts/render_manual_screenshots.py` | Render UI screenshots → `docs/screenshots/{ja,zh,ko,en}.png` |
| `./run.sh scripts/capture_manual_screenshots.py` | Live window capture on macOS (Screen Recording permission) |

```bash
uv pip install pillow
.venv/bin/pip install pillow
```

### Package updates & maintenance

```bash
.venv/bin/pip install -U yt-dlp
.venv/bin/pip install -U pip -r requirements.txt
.venv/bin/pip install syncedlyrics
uv pip install -r requirements.txt
```

Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -U yt-dlp
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Key files

| Path | Description |
|------|-------------|
| `getYoutubeUrl.py` | Main application |
| `i18n.py` | UI translations |
| `kar_maker.py` | KAR MIDI generation |
| `requirements.txt` | Python dependencies |
| `docs/manual_*.md` | Language manuals |
| `docs/screenshots/` | Manual screenshots |
| `scripts/render_manual_screenshots.py` | Screenshot renderer |
| `scripts/capture_manual_screenshots.py` | Screenshot capture |
| `README.md` | Project README |

---

## Other languages

- [日本語](manual_ja.md) · [中文](manual_zh.md) · [한국어](manual_ko.md)
