# getYoutubeUrl — YouTube Search · Playback · MP3 Save

A GUI app built with Python3 + tkinter + yt-dlp + libVLC.  
Search YouTube by song name, add tracks to a **playlist**, then **play**, **show lyrics**, **download MP3/MV**, **play local MP3 files**, and **generate KAR MIDI** — all in one window.  
Choose **song search** or **music video search**; MVs play in an **800×600 popup** at your selected resolution (HD–4K).  
(No YouTube API key · **Default UI language: Japanese**)

![Main window (English)](screenshots/en.png)

---

## Table of Contents

- [Key Features](#key-features)
- [Development Environment](#development-environment)
- [Dependencies](#dependencies)
- [Install & Run](#install--run)
- [Language](#language)
- [Screen Layout & Buttons](#screen-layout--buttons)
- [Shortcuts](#shortcuts)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Change History](#change-history)
- [Troubleshooting](#troubleshooting)
- [Other Commands](#other-commands)
- [Other Language Manuals](#other-language-manuals)

---

## Key Features

- **🎵 Song search** / **🎬 Music video** modes (default 20 results, max 200)
- **Type** labels in results and playlist (`🎵 Song` / `🎬 MV` / `💾 Local`)
- **Double-click search results** to play immediately (song · MV, not added to playlist)
- **Unlimited playlist accumulation** via **Add ↓** (duplicate URLs skipped)
- **Songs**: libVLC audio streaming in the main window
- **MVs**: separate **popup** (800×600) at HD–4K, F11 fullscreen
- Right panel **lyrics** via syncedlyrics
- Playlist **MP3 (192kbps) batch & selected save**
- Playlist **MV MP4 batch & selected save** (resolution selectable)
- **Batch KAR MIDI** from **all tracks in the MP3 save folder**
- **Local MP3 folder** load & play (includes subfolders)
- **UI languages**: 日本語 · 中文 · 한국어 · English
- **Shuffle play**, auto-advance after each track
- Install/run scripts for **Linux / macOS / Windows**
- Search, playback, lyrics, downloads, and MV loading run on **background threads** (no GUI freeze)

---

## Development Environment

### Raspberry Pi (primary dev/test)

| Item | Value |
|------|-------|
| Hardware | Raspberry Pi (aarch64 / arm64) |
| OS | Debian GNU/Linux 13 (trixie) |
| Desktop | Wayland (labwc) + XWayland |
| Python | 3.13.5 |
| GUI | tkinter (`python3-tk`) |
| Media | libVLC 3.0.23 "Vetinari" |
| Virtual env | `.venv/` |
| Initial window | 1240×900 (min 1000×780) |

> tkinter uses the XWayland display (`:0`). `run.sh` sets `DISPLAY` and `XAUTHORITY` automatically.

### macOS / Windows

| OS | Python | VLC | ffmpeg | Setup |
|----|--------|-----|--------|-------|
| macOS | uv + Python 3.11 | `~/Applications/VLC.app` | `~/.local/bin/ffmpeg` | `setup-mac.sh` |
| Windows | Python 3.12 | VideoLAN VLC | `%LOCALAPPDATA%\getYoutubeUrl\bin` | `setup-windows.bat` etc. |

---

## Dependencies

### System packages (apt example)

| Package | Purpose |
|---------|---------|
| `python3` | Runtime |
| `python3-tk` | tkinter GUI |
| `libvlc5` / `vlc-bin` | libVLC playback |
| `ffmpeg` | MP3/MV transcode & merge |

### Python packages (`.venv`)

| Package | Purpose |
|---------|---------|
| `yt-dlp` | YouTube search, stream, download |
| `python-vlc` | libVLC Python bindings |
| `syncedlyrics` | Lyrics lookup |
| `mido` · `numpy` | KAR MIDI generation (optional) |

> Works without `syncedlyrics` except lyrics. Without `mido`·`numpy`, the KAR button shows an error.

---

## Install & Run

### Linux (Raspberry Pi etc.)

```bash
cd getYoutubeUrl
sudo bash setup-debian.sh          # recommended (apt + .venv)
# or
python3 -m venv .venv
.venv/bin/pip install -U pip -r requirements.txt
sudo apt install -y python3-tk vlc ffmpeg

./run.sh
```

Direct run:

```bash
DISPLAY=:0 ./.venv/bin/python getYoutubeUrl.py
```

Background (SSH etc.):

```bash
DISPLAY=:0 XAUTHORITY=$HOME/.Xauthority nohup ./run.sh >> /tmp/getYoutubeUrl.log 2>&1 &
pkill -f getYoutubeUrl.py   # quit
```

### macOS

```bash
cd getYoutubeUrl
./setup-mac.sh
./run.sh
```

### Windows

| Script | Purpose |
|--------|---------|
| `setup-windows.bat` | Setup via winget (falls back to manual) |
| `setup-windows-manual.bat` | Manual install |
| `run-windows.bat` | Launch app |
| `fix-run-windows.bat` | Diagnose & fix run failures |

```text
1. Double-click setup-windows.bat
2. Double-click run-windows.bat
```

> `.bat` files are ASCII + CRLF; logic lives in `.ps1`. Internet required.

---

## Language

Select in the **Language** combobox below search results:

**日本語 → 中文 → 한국어 → English** (default: **Japanese**)

---

## Screen Layout & Buttons

Left (search, lists, controls) + right (lyrics, 320px). **Status bar** at the bottom.

### Top — Search

| UI | Function |
|----|----------|
| **🎵 Song search** | Prefer audio tracks (MV titles deprioritized) |
| **🎬 Music video** | `query + official mv`, MV-first |
| **Query** | Song title · artist |
| **Count** | 1–200 (default 20) |
| **Search** | Background search (same as `Enter`) |

### Search Results

| Column | Description |
|--------|-------------|
| # · Type · Title · Channel · Length | |

| Button / action | Function |
|-----------------|----------|
| **Add ↓** | Add to playlist (skip duplicate URLs). **Use this button only for playlist add** |
| **🎬 Play MV** | Play selected MV in popup |
| **Resolution** | Max MV play/save resolution (HD / FHD / QHD / 2K / 4K) |
| **Open in browser** | Open YouTube in default browser |
| **Language** | Switch UI language |
| **Double-click** | **Play immediately** (song · MV). Does not add to playlist |

### Playlist

| Column | Description |
|--------|-------------|
| # · Type · Title · Channel · Length | `▶` = now playing |

| Buttons (left to right) | Function |
|-------------------------|----------|
| **⬇ Download MP3 (all)** | Save entire playlist as MP3 (192kbps) |
| **⬇ Download (MP3)** | Save selected track as MP3 |
| **⬇ Download MV (all)** | Save all MVs in list as MP4 |
| **⬇ Download (MV)** | Save selected MV as MP4 |
| **Create MIDI for all tracks** | Generate `.kar` from all `.mp3` in the **MP3 save folder** |
| **🗑 Clear all** | **Clear playlist only** |

Folder picker on save. Progress in status bar. **ffmpeg** required (MP3, MV, KAR).

**Double-click**: song → audio / MV → popup.

### Local MP3

| UI | Function |
|----|----------|
| **📁 Pick folder** | Choose local MP3 folder |
| **🔄** | Rescan |
| List | `.mp3` `.m4a` `.flac` `.ogg` `.wav` (subfolders included) |
| **Double-click** | Play local file |

### Playback Controls (single row)

| Button | Function |
|--------|----------|
| **▶ Play** | Playlist selection, else local MP3 |
| **🗑 Delete** | Remove selected item from list or MP3 tree |
| **🗑 Clear all** | Clear MP3 list or playlist depending on focus |
| **🔀 Shuffle** | Enable shuffle and play now |
| **Shuffle: Off/On** | Toggle shuffle for next/auto-advance |
| **Copy all URLs** | Copy playlist URLs to clipboard |

### Right — Lyrics Panel

Shows lyrics for the playing track via `syncedlyrics` (scrollable).

### MV Popup

| Item | Details |
|------|---------|
| Initial size | 800×600 (min 640×480) |
| Resolution | **Resolution** combo next to results (ffmpeg merges A/V) |
| **F11** / video double-click | Fullscreen |
| **Esc** | Exit fullscreen or close |
| Auto | Main audio stops while MV plays |

---

## Shortcuts

| Key | Action | Target |
|-----|--------|--------|
| `Enter` | Search | Main window |
| `F11` | Fullscreen | MV popup |
| `Esc` | Exit fullscreen / close | MV popup |

---

## Project Structure

| File / folder | Description |
|---------------|-------------|
| `getYoutubeUrl.py` | Main app (tkinter GUI) |
| `i18n.py` | UI translation strings |
| `kar_maker.py` | MP3 → KAR MIDI conversion |
| `requirements.txt` | Python dependencies |
| `run.sh` | Linux/macOS launcher |
| `setup-mac.sh` | macOS setup |
| `setup-debian.sh` | Debian/Raspberry Pi setup |
| `setup-windows*.bat/ps1` | Windows setup |
| `run-windows*.bat/ps1` | Windows launcher |
| `fix-run-windows*.bat/ps1` | Windows run recovery |
| `docs/manual_*.md` | Language-specific manuals |
| `docs/screenshots/` | Manual screenshots |
| `scripts/render_manual_screenshots.py` | Screenshot renderer |
| `scripts/capture_manual_screenshots.py` | Screenshot capture |
| `.venv/` | Virtual environment |

---

## How It Works

### Search

- **Song mode:** `ytsearch{N}:query` — deprioritize MV titles
- **MV mode:** `ytsearch{N}:query official mv` — MV-first
- `extract_flat` for metadata only

### Search result play vs add

- **Double-click**: play immediately without adding to playlist (song in main window, MV in popup)
- **Add ↓**: add to playlist only (does not start playback)

### Playlist

- In-memory `list[dict]`, unlimited tracks, duplicate URL prevention

### Playback (song)

1. `yt-dlp` fetches audio URL
2. libVLC streams playback

### Playback (MV)

1. `MvPlayerWindow` popup
2. yt-dlp + ffmpeg merge at or below selected resolution
3. VLC embedded in `video_panel`

### Lyrics

- `syncedlyrics.search()` on a background thread

### MP3 save

- yt-dlp + FFmpegExtractAudio → mp3 192kbps
- Save folder also used for **Create MIDI for all tracks**

### MV save

- Only items with `media_type == "mv"` in playlist
- MP4 at or below selected resolution

### KAR MIDI

- Convert each `.mp3` in the MP3 download folder to `.kar` (same folder output)

### Shuffle

- When `shuffle=True`, next track and auto-advance are random

---

## Change History

| Ver | Summary |
|-----|---------|
| v1 | Top 10 YouTube search + URL display |
| v2 | Playlist + VLC streaming |
| v3 | Multi-search accumulation, shuffle, delete |
| v4 | Lyrics panel |
| v5 | Batch MP3 save |
| v6 | Search count 1–200, selected MP3 save |
| v7 | Window 1240×820 |
| v8 | Song/MV search types, MV popup |
| v9 | MV 800×600, Full HD, F11/Esc |
| v10 | Windows scripts |
| v11 | Windows manual, fix-run |
| v12 | Batch & selected MV MP4 save |
| v13 | Windows bat/ps1 split |
| v14 | UI i18n (ja/zh/ko/en), resolution, local MP3 |
| v15 | Folder-wide KAR MIDI, UI button cleanup |
| v16 | Search result double-click plays immediately; playlist add via **Add ↓** only |

---

## Troubleshooting

- **GitHub:** [https://github.com/xiger78/getYoutubeUrl](https://github.com/xiger78/getYoutubeUrl)
- Some videos may fail due to region or YouTube policy
- Search fails → `.venv/bin/pip install -U yt-dlp`
- Playback fails → check VLC install
- MP3/MV/KAR fails → check **ffmpeg**
- KAR fails → `pip install mido numpy`
- No lyrics → `pip install syncedlyrics`
- Local MP3 missing → check extensions, rescan with 🔄
- Windows install → `setup-windows.bat` or `setup-windows-manual.bat`
- Windows run → `fix-run-windows.bat`
- Linux Korean IME → `setup-debian.sh --with-korean` (fcitx5)

---

## Other Commands

Run from the project root.

### Repository

```bash
git clone https://github.com/xiger78/getYoutubeUrl.git
cd getYoutubeUrl
```

### macOS

```bash
./setup-mac.sh
./run.sh
VLC_APP=/Applications/VLC.app ./run.sh
```

### Linux

```bash
sudo bash setup-debian.sh
sudo bash setup-debian.sh --with-korean
bash setup-debian.sh --venv-only
./run.sh
pkill -f getYoutubeUrl.py
```

### Windows

```powershell
.\run-windows.ps1
```

### Manual screenshots

```bash
.venv/bin/python scripts/render_manual_screenshots.py
./run.sh scripts/capture_manual_screenshots.py   # macOS, Screen Recording permission
```

### Package updates

```bash
.venv/bin/pip install -U yt-dlp
.venv/bin/pip install -U pip -r requirements.txt
uv pip install -r requirements.txt
```

---

## Other Language Manuals

- [日本語](manual_ja.md) · [中文](manual_zh.md) · [한국어](manual_ko.md)
