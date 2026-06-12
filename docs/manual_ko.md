# getYoutubeUrl — YouTube 검색 · 재생 · MP3 저장

Python3 + tkinter + yt-dlp + libVLC 기반 GUI 프로그램입니다.  
곡명으로 YouTube를 검색하고 **재생 리스트**에 넣어 **재생**, **가사 표시**, **MP3·MV 다운로드**, **로컬 MP3 재생**, **KAR MIDI 생성**까지 한 창에서 처리합니다.  
**노래 검색**과 **뮤직비디오 검색**을 선택할 수 있으며, MV는 **800×600 팝업**에서 선택한 해상도(HD~4K)로 재생합니다.  
(YouTube API 키 불필요 · **기본 UI 언어: 일본어**)

![메인 화면（한국어）](screenshots/ko.png)

---

## 목차

- [주요 기능](#주요-기능)
- [개발 환경](#개발-환경)
- [의존 패키지](#의존-패키지)
- [설치 및 실행](#설치-및-실행)
- [언어 변경](#언어-변경)
- [화면 구성과 버튼](#화면-구성과-버튼)
- [단축키](#단축키)
- [프로젝트 구성](#프로젝트-구성)
- [동작 원리](#동작-원리)
- [변경 이력](#변경-이력)
- [문제 해결](#문제-해결)
- [기타 명령어](#기타-명령어)
- [다른 언어 매뉴얼](#다른-언어-매뉴얼)

---

## 주요 기능

- **🎵 노래 검색** / **🎬 뮤직비디오** 검색 모드 (기본 20건, 최대 200건)
- 검색 결과·재생 리스트에 **구분** 표시 (`🎵 노래` / `🎬 MV` / `💾 로컬`)
- 검색 결과를 재생 리스트에 **무제한 누적** (여러 번 검색 가능, URL 중복 방지)
- **노래**: 메인 창에서 libVLC 오디오 스트리밍 재생
- **MV**: 별도 **팝업**(초기 800×600)에서 HD~4K 재생, F11 전체화면
- 오른쪽 패널 **가사** 표시 (syncedlyrics)
- 재생 리스트 **MP3(192kbps) 일괄·선택 저장**
- 재생 리스트 **MV MP4 일괄·선택 저장** (해상도 선택 가능)
- **MP3 저장 폴더 내 전체 곡**에서 **KAR MIDI** 일괄 생성
- **로컬 MP3 폴더** 불러오기·재생 (하위 폴더 포함)
- **UI 다국어**: 日本語 · 中文 · 한국어 · English
- **랜덤 재생**, 곡 종료 후 자동 다음 곡
- **Linux / macOS / Windows**용 설치·실행 스크립트
- 검색·재생·가사·다운로드·MV 로딩은 **백그라운드 스레드** (GUI 멈춤 방지)

---

## 개발 환경

### Raspberry Pi (기본 개발·테스트 환경)

| 항목 | 내용 |
|------|------|
| 기기 | Raspberry Pi (aarch64 / arm64) |
| OS | Debian GNU/Linux 13 (trixie) |
| 데스크톱 | Wayland (labwc) + XWayland |
| Python | 3.13.5 |
| GUI | tkinter (`python3-tk`) |
| 미디어 | libVLC 3.0.23 "Vetinari" |
| 가상 환경 | `.venv/` |
| 초기 창 크기 | 1240×900 (최소 1000×780) |

> tkinter는 XWayland 디스플레이(`:0`)를 사용합니다. `run.sh`가 `DISPLAY`·`XAUTHORITY`를 자동 설정합니다.

### macOS / Windows

| OS | Python | VLC | ffmpeg | 설치 |
|----|--------|-----|--------|------|
| macOS | uv + Python 3.11 | `~/Applications/VLC.app` | `~/.local/bin/ffmpeg` | `setup-mac.sh` |
| Windows | Python 3.12 | VideoLAN VLC | `%LOCALAPPDATA%\getYoutubeUrl\bin` | `setup-windows.bat` 등 |

---

## 의존 패키지

### 시스템 패키지 (apt 예)

| 패키지 | 용도 |
|--------|------|
| `python3` | 런타임 |
| `python3-tk` | tkinter GUI |
| `libvlc5` / `vlc-bin` | libVLC 재생 |
| `ffmpeg` | MP3/MV 변환·병합 |

### Python 패키지 (`.venv`)

| 패키지 | 용도 |
|--------|------|
| `yt-dlp` | YouTube 검색·스트림·다운로드 |
| `python-vlc` | libVLC Python 바인딩 |
| `syncedlyrics` | 가사 검색 |
| `mido` · `numpy` | KAR MIDI 생성 (선택) |

> `syncedlyrics`가 없어도 가사 외 기능은 동작합니다. `mido`·`numpy`가 없으면 KAR 버튼은 오류를 표시합니다.

---

## 설치 및 실행

### Linux (Raspberry Pi 등)

```bash
cd getYoutubeUrl
sudo bash setup-debian.sh          # 권장 (apt + .venv)
# 또는
python3 -m venv .venv
.venv/bin/pip install -U pip -r requirements.txt
sudo apt install -y python3-tk vlc ffmpeg

./run.sh
```

직접 실행:

```bash
DISPLAY=:0 ./.venv/bin/python getYoutubeUrl.py
```

백그라운드 (SSH 등):

```bash
DISPLAY=:0 XAUTHORITY=$HOME/.Xauthority nohup ./run.sh >> /tmp/getYoutubeUrl.log 2>&1 &
pkill -f getYoutubeUrl.py   # 종료
```

### macOS

```bash
cd getYoutubeUrl
./setup-mac.sh
./run.sh
```

### Windows

| 스크립트 | 용도 |
|----------|------|
| `setup-windows.bat` | winget 구축 (없으면 manual로 자동 전환) |
| `setup-windows-manual.bat` | 수동 설치 |
| `run-windows.bat` | 실행 |
| `fix-run-windows.bat` | 실행 실패 시 진단·복구 |

```text
1. setup-windows.bat 더블클릭
2. run-windows.bat 더블클릭
```

> `.bat`은 ASCII + CRLF입니다. 실제 처리는 `.ps1`이 담당합니다. 인터넷 연결이 필요합니다.

---

## 언어 변경

검색 결과 아래 **「언어」** 콤보박스에서 선택:

**日本語 → 中文 → 한국어 → English** (기본: **일본어**)

---

## 화면 구성과 버튼

왼쪽(검색·리스트·조작) + 오른쪽(가사 320px). 아래에 **상태 줄**.

### 상단 — 검색

| UI | 기능 |
|----|------|
| **🎵 노래 검색** | 일반 곡 우선 (MV 제목은 후순위) |
| **🎬 뮤직비디오** | `검색어 + official mv`, MV 우선 |
| **검색어** | 곡명·아티스트 |
| **개수** | 1~200 (기본 20) |
| **검색** | 백그라운드 검색 (`Enter` 동일) |

### 검색 결과

| 열 | 설명 |
|----|------|
| # · 구분 · 제목 · 채널 · 길이 | |

| 버튼 / 조작 | 기능 |
|-------------|------|
| **추가 ↓** | 재생 리스트에 추가 (URL 중복은 건너뜀) |
| **🎬 MV 재생** | MV 팝업 재생 |
| **해상도** | MV 재생·저장 최대 해상도 (HD / FHD / QHD / 2K / 4K) |
| **브라우저로 열기** | 기본 브라우저에서 YouTube 열기 |
| **언어** | UI 언어 전환 |
| **더블클릭** | 노래 → 추가 / MV → MV 재생 |

### 재생 리스트

| 열 | 설명 |
|----|------|
| # · 구분 · 제목 · 채널 · 길이 | `▶` = 재생 중 |

| 버튼 (왼쪽부터) | 기능 |
|-----------------|------|
| **⬇ MP3 다운로드 (전체)** | 리스트 전체 MP3(192kbps) 저장 |
| **⬇ 다운로드(MP3)** | 선택 1곡 MP3 저장 |
| **⬇ MV 다운로드 (전체)** | 리스트 내 전체 MV MP4 저장 |
| **⬇ 다운로드(MV)** | 선택 MV MP4 저장 |
| **전체곡 MIDI파일 작성** | **MP3 저장 시 지정한 폴더** 내 전체 `.mp3`에서 `.kar` 생성 |
| **🗑 전체삭제** | **재생 리스트만** 전체 삭제 |

저장 시 폴더 선택. 상태 줄에 진행 표시. **ffmpeg** 필요 (MP3·MV·KAR 공통).

**더블클릭**: 노래 → 음성 재생 / MV → 팝업.

### 로컬 MP3

| UI | 기능 |
|----|------|
| **📁 폴더 선택** | PC 내 MP3 폴더 지정 |
| **🔄** | 재스캔 |
| 목록 | `.mp3` `.m4a` `.flac` `.ogg` `.wav` (하위 폴더 포함) |
| **더블클릭** | 로컬 MP3 재생 |

### 재생 컨트롤 (1줄)

| 버튼 | 기능 |
|------|------|
| **▶ 재생** | 재생 리스트 선택 → 없으면 로컬 MP3 |
| **🗑 삭제** | 선택 항목을 리스트 또는 MP3 목록에서 삭제 |
| **🗑 전체삭제** | 포커스에 따라 MP3 목록 또는 재생 리스트 전체 삭제 |
| **🔀 랜덤재생** | 랜덤 ON으로 즉시 재생 |
| **랜덤: 끔/켬** | 다음 곡·자동 다음 곡 랜덤 전환 |
| **전체 URL 복사** | 재생 리스트 URL을 클립보드로 |

### 오른쪽 — 가사 패널

재생 중인 곡의 가사를 `syncedlyrics`로 표시 (스크롤 가능).

### MV 팝업

| 항목 | 내용 |
|------|------|
| 초기 크기 | 800×600 (최소 640×480) |
| 해상도 | 검색 결과 옆 **해상도**에서 선택 (ffmpeg로 영상+음성 병합) |
| **F11** / 영상 더블클릭 | 전체화면 |
| **Esc** | 전체화면 해제 또는 닫기 |
| 자동 | MV 재생 중 메인 음성 정지 |

---

## 단축키

| 키 | 동작 | 대상 |
|----|------|------|
| `Enter` | 검색 | 메인 |
| `F11` | 전체화면 | MV 팝업 |
| `Esc` | 전체화면 해제 / 닫기 | MV 팝업 |

---

## 프로젝트 구성

| 파일 / 폴더 | 설명 |
|-------------|------|
| `getYoutubeUrl.py` | 본체 (tkinter GUI) |
| `i18n.py` | UI 다국어 문자열 |
| `kar_maker.py` | MP3 → KAR MIDI 변환 |
| `requirements.txt` | Python 의존성 |
| `run.sh` | Linux/macOS 실행 |
| `setup-mac.sh` | macOS 환경 구축 |
| `setup-debian.sh` | Debian/Raspberry Pi 환경 구축 |
| `setup-windows*.bat/ps1` | Windows 환경 구축 |
| `run-windows*.bat/ps1` | Windows 실행 |
| `fix-run-windows*.bat/ps1` | Windows 실행 복구 |
| `docs/manual_*.md` | 언어별 사용자 매뉴얼 |
| `docs/screenshots/` | 매뉴얼용 스크린샷 |
| `scripts/render_manual_screenshots.py` | 스크린샷 렌더 |
| `scripts/capture_manual_screenshots.py` | 스크린샷 캡처 |
| `.venv/` | 가상 환경 |

---

## 동작 원리

### 검색

- **노래 모드:** `ytsearch{N}:검색어` — MV 제목 우선 제외
- **MV 모드:** `ytsearch{N}:검색어 official mv` — MV 우선
- `extract_flat`으로 메타데이터만 가져옴

### 재생 리스트

- 메모리상 `list[dict]`, 곡 수 무제한, URL 중복 방지

### 재생 (노래)

1. `yt-dlp`로 오디오 URL 획득
2. libVLC로 스트리밍

### 재생 (MV)

1. `MvPlayerWindow` 팝업
2. 선택 해상도 이하로 yt-dlp + ffmpeg 병합
3. VLC를 `video_panel`에 임베드

### 가사

- `syncedlyrics.search()`를 백그라운드 실행

### MP3 저장

- yt-dlp + FFmpegExtractAudio → mp3 192kbps
- 저장 폴더는 **전체곡 MIDI 작성**에서도 참조

### MV 저장

- 재생 리스트의 `media_type == "mv"`만
- 선택 해상도 이하 MP4

### KAR MIDI

- MP3 다운로드로 지정한 폴더 내 `.mp3`를 순차 `.kar`로 변환 (같은 폴더에 출력)

### 랜덤 재생

- `shuffle=True`일 때 다음 곡·곡 종료 후 자동 넘김이 랜덤

---

## 변경 이력

| 버전 | 내용 |
|------|------|
| v1 | YouTube 검색 상위 10 + URL 표시 |
| v2 | 재생 리스트·VLC 스트리밍 |
| v3 | 여러 검색 누적·랜덤·삭제 |
| v4 | 가사 패널 |
| v5 | MP3 일괄 저장 |
| v6 | 검색 건수 1~200·선택 곡 MP3 저장 |
| v7 | 창 1240×820 |
| v8 | 노래/MV 검색 구분·MV 팝업 |
| v9 | MV 800×600·Full HD·F11/Esc |
| v10 | Windows 스크립트 |
| v11 | Windows manual·fix-run |
| v12 | MV MP4 일괄·선택 저장 |
| v13 | Windows bat/ps1 분리 |
| v14 | UI 다국어(ja/zh/ko/en)·해상도 선택·로컬 MP3 |
| v15 | MP3 저장 폴더 전체 KAR MIDI·UI 버튼 정리 |

---

## 문제 해결

- **GitHub:** [https://github.com/xiger78/getYoutubeUrl](https://github.com/xiger78/getYoutubeUrl)
- 지역·YouTube 정책에 따라 일부 동영상은 실패할 수 있습니다
- 검색 불가 → `.venv/bin/pip install -U yt-dlp`
- 재생 불가 → VLC 설치 확인
- MP3/MV/KAR 실패 → **ffmpeg** 확인
- KAR 불가 → `pip install mido numpy`
- 가사 없음 → `pip install syncedlyrics`
- 로컬 MP3 미표시 → 확장자·🔄 재스캔
- Windows 설치 → `setup-windows.bat` 또는 `setup-windows-manual.bat`
- Windows 실행 → `fix-run-windows.bat`
- Linux 한글 입력 → `setup-debian.sh --with-korean` (fcitx5)

---

## 기타 명령어

프로젝트 루트에서 실행.

### 저장소

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

### 매뉴얼용 스크린샷

```bash
.venv/bin/python scripts/render_manual_screenshots.py
./run.sh scripts/capture_manual_screenshots.py   # macOS·화면 녹화 권한
```

### 패키지 업데이트

```bash
.venv/bin/pip install -U yt-dlp
.venv/bin/pip install -U pip -r requirements.txt
uv pip install -r requirements.txt
```

---

## 다른 언어 매뉴얼

- [日本語](manual_ja.md) · [中文](manual_zh.md) · [English](manual_en.md)
