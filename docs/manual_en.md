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

## Other languages

- [日本語](manual_ja.md) · [中文](manual_zh.md) · [한국어](manual_ko.md)
