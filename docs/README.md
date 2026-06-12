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

---

## Install file build (설치 파일 만들기)

PyInstaller로 앱을 묶고, 플랫폼별 설치 파일을 `dist/`에 생성합니다.

| OS | Build command | Output |
|----|---------------|--------|
| macOS (Intel / Apple Silicon) | `./scripts/build/build-mac.sh` | `dist/getYoutubeUrl-<ver>-mac-<arch>.dmg` |
| Windows | `.\scripts\build\build-windows.ps1` | `dist/getYoutubeUrl-<ver>-win64-setup.exe` (Inno Setup) or `.zip` |
| Linux (Debian/Ubuntu/RPi) | `./scripts/build/build-linux.sh [amd64\|arm64]` | `dist/getYoutubeUrl_<ver>_<arch>.deb` |

macOS DMG에는 **Universal VLC**와 **ffmpeg**가 포함됩니다. Windows 빌드는 VLC·ffmpeg portable을 함께 번들합니다. Linux `.deb`는 `python3-tk`, `vlc`, `ffmpeg` apt 의존성을 사용합니다.

Windows Inno Setup 6: https://jrsoftware.org/isinfo.php (없으면 ZIP으로 대체)

```bash
# 현재 OS 자동 선택
./scripts/build/build.sh
```
