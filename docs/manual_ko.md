# getYoutubeUrl 사용자 매뉴얼（한국어）

Python + tkinter + yt-dlp + libVLC 기반 GUI입니다.  
유튜브 검색, 재생, 가사, MP3·MV 다운로드, 로컬 MP3 재생을 한 창에서 처리합니다. API 키는 필요 없습니다.

![메인 화면（한국어）](screenshots/ko.png)

---

## 목차

1. [설치 및 실행](#설치-및-실행)
2. [화면 구성](#화면-구성)
3. [언어 변경](#언어-변경)
4. [검색](#검색)
5. [재생 리스트](#재생-리스트)
6. [뮤직비디오(MV)](#뮤직비디오mv)
7. [로컬 MP3](#로컬-mp3)
8. [재생 컨트롤](#재생-컨트롤)
9. [가사 패널](#가사-패널)
10. [단축키](#단축키)
11. [문제 해결](#문제-해결)
12. [기타 명령어](#기타-명령어)

---

## 설치 및 실행

### macOS

```bash
cd getYoutubeUrl
./setup-mac.sh
./run.sh
```

### Linux

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
sudo apt install -y python3-tk vlc ffmpeg
./run.sh
```

### Windows

`setup-windows.bat` → `run-windows.bat`

---

## 화면 구성

| 영역 | 설명 |
|------|------|
| 상단 | 검색 종류, 검색어, 개수, 검색 |
| 검색 결과 | 유튜브 검색 목록 |
| 검색 결과 버튼 | 추가, MV 재생, 해상도, 브라우저, 언어 |
| 재생 리스트 | 재생 대기 곡·MV |
| 재생 리스트 버튼 | MP3/MV 다운로드, MIDI 생성, 전체삭제 |
| 로컬 MP3 | PC 폴더 MP3 불러오기 |
| 재생 컨트롤 | 재생, 삭제, 전체삭제, 랜덤, URL 복사 |
| 오른쪽 | 가사 |
| 하단 | 상태 메시지 |

---

## 언어 변경

검색 결과 아래 **언어** 콤보박스에서 선택합니다.

- **기본:** 일본어
- **순서:** 日本語 → 中文 → 한국어 → English

---

## 검색

| 모드 | 설명 |
|------|------|
| **🎵 노래 검색** | 일반 곡 우선 |
| **🎬 뮤직비디오** | MV 우선 검색 |

**검색** 또는 `Enter`로 실행합니다.

### 검색 결과

| 동작 | 기능 |
|------|------|
| **추가 ↓** | 재생 리스트에 추가 |
| **🎬 MV 재생** | MV 팝업 재생 |
| **해상도** | MV 해상도 (HD~4K) |
| **브라우저로 열기** | 웹 브라우저에서 열기 |
| **더블클릭** | 노래 → 추가 / MV → MV 재생 |

---

## 재생 리스트

### 버튼 (왼쪽부터)

| 버튼 | 기능 |
|------|------|
| **⬇ MP3 다운로드 (전체)** | 리스트 전체 MP3 저장 |
| **⬇ 다운로드(MP3)** | 선택 곡 MP3 저장 |
| **⬇ MV 다운로드 (전체)** | 리스트 MV 전체 MP4 저장 |
| **⬇ 다운로드(MV)** | 선택 MV MP4 저장 |
| **선택곡 MIDI파일 생성** | KAR MIDI 생성 |
| **🗑 전체삭제** | **재생 리스트만** 비우기 |

더블클릭으로 재생합니다.

---

## 뮤직비디오(MV)

- 별도 팝업(800×600), **F11** 전체화면, **Esc** 닫기
- ffmpeg로 고해상도 영상+음성 병합

---

## 로컬 MP3

1. **📁 폴더 선택** — **🔄** 로 재스캔
2. 하위 폴더 포함 `.mp3` `.m4a` `.flac` `.ogg` `.wav` 표시
3. **더블클릭** 으로 재생

---

## 재생 컨트롤

로컬 MP3 아래 **한 줄**:

| 버튼 | 기능 |
|------|------|
| **▶ 재생** | 재생 리스트 → 없으면 로컬 MP3 |
| **🗑 삭제** | 선택 항목 삭제 (리스트 또는 MP3) |
| **🗑 전체삭제** | MP3 포커스 시 MP3 목록 / 아니면 재생·MP3 중 해당 목록 |
| **🔀 랜덤재생** | 랜덤 즉시 재생 |
| **랜덤: 끔** | 랜덤 모드 전환 |
| **전체 URL 복사** | 재생 리스트 URL 복사 |

---

## 가사 패널

`syncedlyrics`로 재생 중 곡의 가사를 오른쪽에 표시합니다.

---

## 단축키

| 키 | 동작 |
|----|------|
| `Enter` | 검색 |
| `F11` | MV 전체화면 |
| `Esc` | MV 팝업 닫기 |

---

## 문제 해결

| 증상 | 해결 |
|------|------|
| 검색 실패 | `pip install -U yt-dlp` |
| 재생 실패 | VLC 확인 |
| 저장 실패 | ffmpeg 설치 |
| MP3 목록 없음 | 확장자·하위 폴더 확인, 🔄 재스캔 |

**GitHub:** [https://github.com/xiger78/getYoutubeUrl](https://github.com/xiger78/getYoutubeUrl)

---

## 기타 명령어

프로젝트 루트(`getYoutubeUrl/`)에서 실행합니다.

### 저장소 받기

```bash
git clone https://github.com/xiger78/getYoutubeUrl.git
cd getYoutubeUrl
```

### macOS

| 명령 / 파일 | 설명 |
|-------------|------|
| `./setup-mac.sh` | uv, Python 3.11, VLC, ffmpeg, `.venv` 자동 설치 |
| `./run.sh` | 프로그램 실행 (VLC·ffmpeg PATH 자동 설정) |
| `VLC_APP=/Applications/VLC.app ./run.sh` | VLC 경로를 직접 지정해 실행 |
| `.venv/bin/python getYoutubeUrl.py` | 스크립트 없이 직접 실행 (VLC 환경 변수 필요) |

```bash
# VLC 환경 변수를 수동 설정할 때 (run.sh 와 동일)
VLC_MACOS="$HOME/Applications/VLC.app/Contents/MacOS"
export DYLD_LIBRARY_PATH="$VLC_MACOS/lib"
export VLC_PLUGIN_PATH="$VLC_MACOS/plugins"
export PATH="$HOME/.local/bin:$PATH"
./.venv/bin/python getYoutubeUrl.py
```

### Linux (Debian / Raspberry Pi 등)

| 명령 / 파일 | 설명 |
|-------------|------|
| `sudo bash setup-debian.sh` | apt 패키지 + `.venv` + pip 전체 설치 |
| `bash setup-debian.sh --venv-only` | `.venv`·pip 만 설치 (sudo 불필요) |
| `sudo bash setup-debian.sh --with-korean` | 설치 + fcitx5 한글 입력기 |
| `bash setup-debian.sh --help` | 옵션 도움말 |
| `./run.sh` | 실행 (`DISPLAY`, XIM·fcitx5 설정 포함) |

```bash
# 수동 설치
python3 -m venv .venv
.venv/bin/pip install -U pip -r requirements.txt
sudo apt install -y python3-tk vlc ffmpeg

# 직접 실행
DISPLAY=:0 ./.venv/bin/python getYoutubeUrl.py

# 백그라운드 실행 (SSH·서버)
DISPLAY=:0 XAUTHORITY=$HOME/.Xauthority nohup ./run.sh >> /tmp/getYoutubeUrl.log 2>&1 &

# 종료
pkill -f getYoutubeUrl.py
```

### Windows

| 파일 | 설명 |
|------|------|
| `setup-windows.bat` | winget 으로 환경 구축 (없으면 manual 로 자동 전환) |
| `setup-windows.ps1` | 위 bat 의 실제 PowerShell 로직 |
| `setup-windows-manual.bat` | winget 없이 python.org·VLC·ffmpeg 수동 설치 |
| `setup-windows-manual.ps1` | manual bat 의 PowerShell 로직 |
| `run-windows.bat` | 프로그램 실행 |
| `run-windows.ps1` | 실행 로직 (`.venv`, VLC·ffmpeg PATH) |
| `fix-run-windows.bat` | 실행 실패 시 진단·복구 후 실행 |
| `fix-run-windows.ps1` | fix bat 의 PowerShell 로직 |

```text
1. setup-windows.bat  더블클릭  (또는 setup-windows-manual.bat)
2. run-windows.bat    더블클릭
   ※ 실패 시 fix-run-windows.bat
```

PowerShell 에서 직접 실행:

```powershell
cd getYoutubeUrl
.\run-windows.ps1
```

### 매뉴얼·스크린샷 생성

| 명령 | 설명 |
|------|------|
| `.venv/bin/python scripts/render_manual_screenshots.py` | 언어별 UI 목업 스크린샷 생성 → `docs/screenshots/{ja,zh,ko,en}.png` |
| `./run.sh scripts/capture_manual_screenshots.py` | macOS 실제 창 캡처 시도 (화면 녹화 권한 필요, 실패 시 render 로 대체) |

Pillow 가 없으면 render 스크립트가 자동 설치를 시도합니다:

```bash
uv pip install pillow    # macOS (uv 사용 시)
.venv/bin/pip install pillow
```

### 패키지 업데이트·유지보수

```bash
# yt-dlp 업데이트 (검색·재생 오류 시)
.venv/bin/pip install -U yt-dlp

# Python 의존성 재설치
.venv/bin/pip install -U pip -r requirements.txt

# 가사 모듈 설치
.venv/bin/pip install syncedlyrics

# macOS — uv 로 venv 재구성
uv pip install -r requirements.txt
```

Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -U yt-dlp
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 주요 파일

| 경로 | 설명 |
|------|------|
| `getYoutubeUrl.py` | 프로그램 본체 |
| `i18n.py` | UI 다국어 문자열 |
| `kar_maker.py` | KAR MIDI 생성 |
| `requirements.txt` | Python 패키지 목록 |
| `docs/manual_*.md` | 언어별 사용자 매뉴얼 |
| `docs/screenshots/` | 매뉴얼용 스크린샷 |
| `scripts/render_manual_screenshots.py` | 스크린샷 렌더 |
| `scripts/capture_manual_screenshots.py` | 스크린샷 캡처 |
| `README.md` | 프로젝트 전체 README |

---

## 다른 언어

- [日本語](manual_ja.md) · [中文](manual_zh.md) · [English](manual_en.md)
