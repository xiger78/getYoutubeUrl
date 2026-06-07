#!/bin/bash
# getYoutubeUrl — Debian GNU/Linux 환경 구축 스크립트
#
# 시스템 패키지(apt) + Python 가상환경(.venv) + pip 의존성을 설치합니다.
#
# 사용법:
#   sudo bash setup-debian.sh              # 전체 설치 (권장)
#   bash setup-debian.sh --venv-only       # venv·pip 만 (apt 권한 없을 때)
#   sudo bash setup-debian.sh --with-korean # 한글 입력기(fcitx5) 포함
#   bash setup-debian.sh --help
#
# 설치 후 실행:
#   ./run.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

INSTALL_APT=true
INSTALL_KOREAN=false

usage() {
    sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
}

for arg in "$@"; do
    case "$arg" in
        --venv-only)
            INSTALL_APT=false
            ;;
        --with-korean)
            INSTALL_KOREAN=true
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "알 수 없는 옵션: $arg" >&2
            usage
            exit 1
            ;;
    esac
done

log() { echo "==> $*"; }

need_root() {
    if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
        echo "오류: 이 단계는 root 권한이 필요합니다.  sudo bash setup-debian.sh" >&2
        exit 1
    fi
}

check_debian() {
    if [[ -r /etc/os-release ]]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        if [[ "${ID:-}" != "debian" && "${ID_LIKE:-}" != *debian* ]]; then
            echo "경고: Debian 계열이 아닐 수 있습니다 (${PRETTY_NAME:-unknown}). apt 패키지명이 다를 수 있습니다."
        fi
    fi
}

install_apt_packages() {
    need_root
    log "패키지 목록 갱신"
    apt-get update

    log "getYoutubeUrl 시스템 패키지 설치"
    apt-get install -y \
        "$PYTHON_BIN" \
        python3-venv \
        python3-tk \
        ffmpeg \
        vlc \
        libvlc5 \
        vlc-bin \
        x11-utils

    if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
        echo "오류: $PYTHON_BIN 을 찾을 수 없습니다." >&2
        exit 1
    fi
    if ! "$PYTHON_BIN" -c "import tkinter" 2>/dev/null; then
        echo "오류: python3-tk(tkinter) 설치를 확인하세요." >&2
        exit 1
    fi
}

install_korean_input() {
    need_root
    log "한글 입력기(fcitx5) 설치"
    apt-get install -y \
        fcitx5 \
        fcitx5-hangul \
        fcitx5-configtool \
        fcitx5-frontend-gtk3 \
        fcitx5-frontend-gtk4 \
        fcitx5-frontend-qt5 \
        fcitx5-frontend-all

    if ! locale -a 2>/dev/null | grep -qi 'ko_KR.utf8'; then
        log "한국어 로케일(ko_KR.UTF-8) 생성"
        if grep -q '^# *ko_KR.UTF-8 UTF-8' /etc/locale.gen 2>/dev/null; then
            sed -i 's/^# *ko_KR.UTF-8 UTF-8/ko_KR.UTF-8 UTF-8/' /etc/locale.gen
            locale-gen ko_KR.UTF-8 || true
        fi
    fi

    local env_file=/etc/environment
    if [[ -f "$env_file" ]] && ! grep -q 'XMODIFIERS=@im=fcitx' "$env_file" 2>/dev/null; then
        log "IME 환경변수를 $env_file 에 추가"
        {
            echo 'GTK_IM_MODULE=fcitx'
            echo 'QT_IM_MODULE=fcitx'
            echo 'XMODIFIERS=@im=fcitx'
            echo 'SDL_IM_MODULE=fcitx'
        } >> "$env_file"
    fi
}

create_venv() {
    if [[ ! -d "$VENV_DIR" ]]; then
        log "가상환경 생성: $VENV_DIR"
        "$PYTHON_BIN" -m venv "$VENV_DIR"
    else
        log "기존 가상환경 사용: $VENV_DIR"
    fi

    log "pip 패키지 설치"
    "$VENV_DIR/bin/pip" install -U pip
    "$VENV_DIR/bin/pip" install -U \
        yt-dlp \
        python-vlc \
        syncedlyrics \
        mido \
        numpy
}

make_executable() {
    chmod +x "$SCRIPT_DIR/run.sh" 2>/dev/null || true
    chmod +x "$SCRIPT_DIR/setup-debian.sh" 2>/dev/null || true
}

verify_install() {
    log "설치 검증"
    local ok=true

    for cmd in ffmpeg cvlc xprop; do
        if command -v "$cmd" >/dev/null 2>&1; then
            echo "  OK  $cmd"
        else
            echo "  --  $cmd (없음 — GUI/IME 기능 일부 제한)"
        fi
    done

    "$VENV_DIR/bin/python" - <<'PY' || ok=false
import sys
mods = ["yt_dlp", "vlc", "syncedlyrics", "mido", "numpy", "tkinter"]
failed = []
for m in mods:
    try:
        __import__(m)
    except ImportError:
        failed.append(m)
if failed:
    print("  FAIL:", ", ".join(failed))
    sys.exit(1)
print("  OK  Python 모듈:", ", ".join(mods))
try:
    from kar_maker import create_kar_from_mp3
    print("  OK  kar_maker (KAR MIDI)")
except ImportError as e:
    print("  --  kar_maker:", e)
PY

    if [[ "$ok" != true ]]; then
        echo "오류: 설치 검증에 실패했습니다." >&2
        exit 1
    fi
}

print_done() {
    echo
    echo "========================================"
    echo " getYoutubeUrl 환경 구축 완료"
    echo "========================================"
    echo
    echo " 실행:"
    echo "   cd $SCRIPT_DIR"
    echo "   ./run.sh"
    echo
    if [[ "$INSTALL_KOREAN" == true ]]; then
        echo " 한글 입력: 로그아웃 후 다시 로그인 → Ctrl+Space 로 한/영 전환"
        echo
    fi
    echo " 업데이트(yt-dlp 등):"
    echo "   $VENV_DIR/bin/pip install -U yt-dlp"
    echo
}

main() {
    check_debian

    if [[ "$INSTALL_APT" == true ]]; then
        install_apt_packages
        if [[ "$INSTALL_KOREAN" == true ]]; then
            install_korean_input
        fi
    else
        log "apt 설치 건너뜀 (--venv-only)"
        if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
            echo "오류: $PYTHON_BIN 이 필요합니다." >&2
            exit 1
        fi
    fi

    create_venv
    make_executable
    verify_install
    print_done
}

main
