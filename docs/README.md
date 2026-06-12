# getYoutubeUrl Documentation

User manuals with UI screenshots for each supported language.

| Language | Manual | Screenshot |
|----------|--------|------------|
| 日本語 (default) | [manual_ja.md](manual_ja.md) | [screenshots/ja.png](screenshots/ja.png) |
| 中文 | [manual_zh.md](manual_zh.md) | [screenshots/zh.png](screenshots/zh.png) |
| 한국어 | [manual_ko.md](manual_ko.md) | [screenshots/ko.png](screenshots/ko.png) |
| English | [manual_en.md](manual_en.md) | [screenshots/en.png](screenshots/en.png) |

Language order in app: **日本語 → 中文 → 한국어 → English**

Each manual includes an **Other commands** section with OS-specific setup/run scripts, screenshot tools, and maintenance commands.

---

## Quick reference — all platforms

### Run

| OS | Command |
|----|---------|
| macOS / Linux | `./run.sh` |
| Windows | `run-windows.bat` (or `.\run-windows.ps1`) |

### First-time setup

| OS | Command |
|----|---------|
| macOS | `./setup-mac.sh` |
| Linux (Debian) | `sudo bash setup-debian.sh` |
| Linux (venv only) | `bash setup-debian.sh --venv-only` |
| Windows | `setup-windows.bat` or `setup-windows-manual.bat` |
| Windows fix | `fix-run-windows.bat` |

### Regenerate manual screenshots

```bash
.venv/bin/python scripts/render_manual_screenshots.py
```

Live window capture (macOS, Screen Recording permission):

```bash
./run.sh scripts/capture_manual_screenshots.py
```

### Update yt-dlp

```bash
.venv/bin/pip install -U yt-dlp
```

Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -U yt-dlp
```

### Stop background process (Linux)

```bash
pkill -f getYoutubeUrl.py
```

See each [manual](manual_ja.md) for the full command reference.
