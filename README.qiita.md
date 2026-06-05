---
title: Python3로 만든 유튜브 노래·뮤직비디오 검색·재생·MP3 저장 GUI (Raspberry Pi)
tags:
  - Python3
  - tkinter
  - yt-dlp
  - VLC
  - RaspberryPi
  - Linux
private: false
updated_at: ''
id: null
organization_url_name: null
slide: false
ignorePublish: false
---

Raspberry Pi(Debian 13 Trixie, arm64)에서 Python3와 tkinter로 **유튜브 노래 검색·재생 리스트·스트리밍 재생·가사 표시·MP3 저장·뮤직비디오 팝업 재생**까지 한 창에서 처리하는 GUI 프로그램 **getYoutubeUrl** 을 만든 과정과 사용법을 정리합니다. **노래 검색**과 **뮤직비디오 검색**을 구분할 수 있고, MV는 **800×600 팝업**에서 **Full HD(1080p)** 로 재생합니다. 유튜브 API 키는 필요 없으며, 검색·다운로드는 `yt-dlp`, 재생은 `libVLC(python-vlc)` 를 사용합니다.

> **스크린샷:** 본문에 넣을 이미지는 프로젝트의 `screenshot.png` 를 Qiita 에디터에서 업로드한 뒤 URL로 교체하세요.

## 1. 개요

| 항목 | 내용 |
|------|------|
| 프로그램명 | getYoutubeUrl |
| 목적 | 유튜브 검색(노래/MV) → 재생 리스트 → 재생·가사·MP3·MV 팝업 |
| MV 팝업 | 초기 800×600, Full HD(1080p), F11 전체화면 |
| GUI | tkinter (`python3-tk`) |
| 검색·다운로드 | `yt-dlp` |
| 재생 | `python-vlc` + 시스템 libVLC |
| 가사 | `syncedlyrics` |
| MP3 변환 | 시스템 `ffmpeg` |
| 프로젝트 경로 | `/home/pi/dev/getYoutubeUrl` |
| 초기 창 크기 | 1240×820 (최소 1000×720) |

## 2. 주요 기능

- **🎵 노래 검색** / **🎬 뮤직비디오** 검색 모드 (기본 20개, 최대 200개)
- 결과·리스트에 **구분** 표시 (`🎵 노래` / `🎬 MV`)
- 재생 리스트 **무제한 누적** (여러 검색, URL 중복 방지)
- **노래**: 메인 창 오디오 스트리밍 (libVLC)
- **MV**: 팝업 **800×600**, **Full HD(1080p)** 영상, F11 전체화면
- 오른쪽 **가사** 패널 (syncedlyrics)
- **MP3(192kbps)** 일괄·선택 저장
- **랜덤 재생**, 자동 다음 곡
- 백그라운드 스레드 (검색·재생·가사·다운로드·MV)

## 3. 개발 환경

| 항목 | 내용 |
|------|------|
| 기기 | Raspberry Pi (aarch64) |
| OS | Debian GNU/Linux 13 (trixie) |
| 데스크톱 | Wayland (labwc) + XWayland |
| Python | 3.13.5 |
| libVLC | 3.0.23 Vetinari |
| 가상환경 | `~/dev/getYoutubeUrl/.venv` |

Wayland 데스크톱에서는 tkinter 가 **XWayland 디스플레이 `:0`** 을 사용합니다. `run.sh` 가 `DISPLAY`·`XAUTHORITY` 를 자동 설정합니다.

### 3-1. 사전 확인

```bash
python3 --version
python3 -c "import tkinter; print('tkinter', tkinter.TkVersion)"
ldconfig -p | grep libvlc
which ffmpeg
ls /tmp/.X11-unix/    # X0 이 있으면 GUI 가능
```

## 4. 의존성 패키지

### 4-1. 시스템 패키지 (apt)

```bash
sudo apt install -y python3 python3-tk python3-venv vlc ffmpeg
```

| 패키지 | 용도 |
|--------|------|
| `python3` / `python3-tk` | 런타임·GUI |
| `vlc` (libvlc) | 오디오 재생 |
| `ffmpeg` | MP3 변환 |

### 4-2. 파이썬 패키지 (venv)

| 패키지 | 버전 (예) | 용도 |
|--------|-----------|------|
| `yt-dlp` | 2026.3.17 | 유튜브 검색·스트림·다운로드 |
| `python-vlc` | 3.0.21203 | libVLC 바인딩 |
| `syncedlyrics` | 1.0.1 | 가사 검색 |

## 5. 구축·설치

### 5-1. 프로젝트·가상환경

```bash
mkdir -p ~/dev/getYoutubeUrl
cd ~/dev/getYoutubeUrl
python3 -m venv .venv
.venv/bin/pip install -U pip yt-dlp python-vlc syncedlyrics
```

### 5-2. 실행 스크립트 (`run.sh`)

```bash
#!/bin/bash
cd "$(dirname "$0")"
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"
exec ./.venv/bin/python getYoutubeUrl.py "$@"
```

```bash
chmod +x ~/dev/getYoutubeUrl/run.sh
```

## 6. 실행 방법

### 6-1. 스크립트 실행 (권장)

```bash
~/dev/getYoutubeUrl/run.sh
```

### 6-2. 직접 실행

```bash
cd ~/dev/getYoutubeUrl
DISPLAY=:0 ./.venv/bin/python getYoutubeUrl.py
```

### 6-3. 백그라운드 (SSH·서버)

```bash
cd ~/dev/getYoutubeUrl
DISPLAY=:0 XAUTHORITY=$HOME/.Xauthority \
  nohup ./run.sh >> /tmp/getYoutubeUrl.log 2>&1 &
```

### 6-4. 종료

```bash
pkill -f getYoutubeUrl.py
```

> **인터넷 연결**이 필요합니다.

## 7. 화면 구성

- **왼쪽:** 검색 · 검색 결과 · 재생 리스트 · MP3 다운로드 · 재생 컨트롤
- **오른쪽:** 가사 패널 (320px)
- **맨 아래:** 상태줄 (진행·오류 메시지)

## 8. 버튼·UI별 기능 설명

### 8-1. 검색 종류·검색어

| UI | 기능 |
|----|------|
| **🎵 노래 검색** | 일반 곡 위주 (MV 제목 우선 제외) |
| **🎬 뮤직비디오** | `검색어 official mv`, MV 제목 우선 |
| **검색어** | 곡명·가수명 |
| **개수** | 1~200 (기본 20) |
| **검색** | 유튜브 검색 (`Enter` 동일) |

### 8-2. 검색 결과

| 컬럼 | 설명 |
|------|------|
| # / 구분 / 제목 / 채널 / 길이 | `🎵 노래` 또는 `🎬 MV` |

| 버튼·동작 | 기능 |
|-----------|------|
| **추가 ↓** | 노래를 재생 리스트에 추가 |
| **🎬 MV 재생** | MV 팝업 재생 (800×600, Full HD) |
| **브라우저로 열기** | 웹 브라우저에서 열기 |
| **더블클릭** | 노래→추가 / MV→팝업 재생 |

### 8-3. 재생 리스트

| 버튼·동작 | 기능 |
|-----------|------|
| **⬇ MP3 다운로드 (전체)** | 전체 MP3 저장 |
| **⬇ 선택 곡 저장** | 선택 곡만 MP3 저장 |
| **더블클릭** | 노래→오디오 재생 / MV→팝업 |
| `▶` 표시 | 현재 재생 중 |

### 8-4. 재생 컨트롤

| 버튼 | 기능 |
|------|------|
| **▶ 재생** | 노래→오디오 / MV→팝업 (없으면 첫 곡) |
| **⏸ 일시정지** | 재생·일시정지 토글 |
| **⏹ 정지** | 정지 |
| **⏭ 다음** | 다음 곡 (랜덤 켬 시 무작위) |
| **🔀 랜덤재생** | 랜덤 켜고 무작위 곡 즉시 재생 |
| **랜덤: 끔/켬** | 다음·자동 넘김을 무작위로 |
| **🗑 삭제** | 선택 곡 제거 |
| **🗑 전체삭제** | 리스트 전체 비우기 |
| **전체 URL 복사** | 리스트 URL 클립보드 복사 |

### 8-5. 가사 패널 (오른쪽)

재생 시작 시 `syncedlyrics` 로 가사를 조회해 표시합니다. 유튜브 제목의 `(Official MV)`, `[가사]` 등은 검색 전에 제거합니다.

### 8-6. MV 팝업 (뮤직비디오)

| 항목 | 내용 |
|------|------|
| 초기 크기 | **800×600** |
| 해상도 | **Full HD (1080p 이하)** |
| **F11** / 영상 더블클릭 | 전체화면 |
| **Esc** | 전체화면 해제 또는 닫기 |
| **닫기** | 팝업 종료 |

MV 재생 시 메인 창 오디오는 자동 정지합니다.

### 8-7. 단축키

| 키 | 동작 | 적용 |
|----|------|------|
| `Enter` | 검색 | 메인 창 |
| `F11` | 전체화면 | MV 팝업 |
| `Esc` | 전체화면 해제/닫기 | MV 팝업 |

## 9. 동작 원리

### 검색

- **노래:** `ytsearch{N}:검색어` — MV 제목 우선 제외
- **MV:** `ytsearch{N}:검색어 official mv` — MV 제목 우선
- `extract_flat` + `media_type` (`song` / `mv`)

### 재생 (노래)

`bestaudio/best` → 메인 창 libVLC 오디오 재생

### 재생 (MV)

`best[height<=1080]` → `MvPlayerWindow` 팝업(800×600)에 libVLC 영상 임베드

### UI

`queue` + `after(100ms)` 폴링 (GUI 스레드 안전)

### MP3 저장

`yt-dlp` 다운로드 + `FFmpegExtractAudio` → mp3 192kbps, 파일명 `%(title)s.mp3`.

### 가사

`syncedlyrics.search()` — 백그라운드, 최신 곡만 패널 갱신.

## 10. 프로젝트 구성

| 파일 | 설명 |
|------|------|
| `getYoutubeUrl.py` | GUI 본체 |
| `run.sh` | 실행 스크립트 |
| `README.md` | 상세 문서 |
| `README.qiita.md` | Qiita용 문서 |
| `screenshot.png` | 실행 화면 |
| `.venv/` | 가상환경 |

## 11. 트러블슈팅

| 증상 | 대처 |
|------|------|
| 검색 실패 | `.venv/bin/pip install -U yt-dlp` |
| MP3 저장 실패 | `sudo apt install ffmpeg` |
| MV 재생 실패·끊김 | `pip install -U yt-dlp`, 네트워크·CPU 부하 확인 |
| GUI 안 뜸 | `DISPLAY=:0` 설정, XWayland 확인 |
| 가사 없음 | `pip install syncedlyrics`, 제목·네트워크 확인 |
| 한글 입력 안 됨 | fcitx5 + hangul 설치 (`setup-korean-input.sh` 등) |

## 12. 변경 이력

| 버전 | 내용 |
|------|------|
| v1 | 유튜브 검색 10개 + URL 표시 |
| v2 | 재생 리스트·VLC 재생 |
| v3 | 검색 누적·랜덤·삭제 |
| v4 | 가사 패널 |
| v5 | MP3 일괄 저장 |
| v6 | 검색 개수 1~200·선택 곡 MP3·다운로드 버튼 |
| v7 | 창 크기 1240×820·README 정리 |
| v8 | 노래/MV 검색·MV 팝업·구분 열 |
| v9 | MV 팝업 800×600·Full HD 1080p |

## 13. 참고·GitHub

- 유튜브 정책·지역에 따라 일부 영상은 재생·다운로드가 제한될 수 있습니다.
- 소스: `~/dev/getYoutubeUrl` (GitHub 등에 올릴 경우 `getYoutubeUrl.py`, `run.sh`, `README.md` 포함)

## 14. 마무리

`getYoutubeUrl` 은 API 키 없이 유튜브를 검색(노래/MV)하고, 재생 리스트로 곡을 모은 뒤 오디오 재생·MV 팝업·가사·MP3 저장까지 처리하는 라즈베리파이용 데스크톱 도구입니다. `yt-dlp` 는 유튜브 변경에 맞춰 주기적으로 업데이트하는 것을 권장합니다.

```bash
cd ~/dev/getYoutubeUrl && .venv/bin/pip install -U yt-dlp
```
