#!/bin/bash
# getYoutubeUrl macOS 환경 자동 구축 (sudo 불필요)
# Apple Silicon (arm64) / Intel (x86_64) 공통 — VLC Universal 자동 설치
set -euo pipefail
cd "$(dirname "$0")"

echo "==> getYoutubeUrl macOS 환경 구축"

# uv (사용자 로컬 Python 관리)
if ! command -v uv >/dev/null 2>&1; then
  echo "==> uv 설치"
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
# shellcheck disable=SC1091
if [ -f "${HOME}/.local/bin/env" ]; then
  source "${HOME}/.local/bin/env"
fi
export PATH="${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:${PATH}"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv를 찾을 수 없습니다. Homebrew: brew install uv" >&2
  exit 1
fi

echo "==> Python 3.11 설치"
uv python install 3.11

# VLC — Universal binary (Apple Silicon + Intel 共通)
VLC_VERSION="3.0.23"
VLC_DMG="vlc-${VLC_VERSION}-universal.dmg"
VLC_URL="https://download.videolan.org/pub/videolan/vlc/${VLC_VERSION}/macosx/${VLC_DMG}"
VLC_APP="${HOME}/Applications/VLC.app"

vlc_usable() {
  local exe="${VLC_APP}/Contents/MacOS/VLC"
  local lib="${VLC_APP}/Contents/MacOS/lib/libvlccore.dylib"
  local arch
  arch="$(uname -m)"
  [ -x "${exe}" ] && [ -f "${lib}" ] || return 1
  if command -v lipo >/dev/null 2>&1; then
    lipo -info "${lib}" 2>/dev/null | grep -q "${arch}"
  else
    file "${lib}" | grep -q "${arch}"
  fi
}

if ! vlc_usable; then
  echo "==> VLC 다운로드 및 설치 (${VLC_APP}, universal, $(uname -m))"
  TMP_DMG="$(mktemp /tmp/vlc-XXXXXX.dmg)"
  curl -fsSL -o "${TMP_DMG}" "${VLC_URL}"
  mkdir -p "${HOME}/Applications"
  hdiutil attach "${TMP_DMG}" -nobrowse -quiet
  rm -rf "${VLC_APP}"
  cp -R "/Volumes/VLC media player/VLC.app" "${HOME}/Applications/"
  hdiutil detach "/Volumes/VLC media player" -quiet
  rm -f "${TMP_DMG}"
  vlc_usable || {
    echo "VLC 설치 후 현재 Mac($(uname -m))에서 사용할 수 없습니다." >&2
    exit 1
  }
fi

# ffmpeg (MP3 저장용)
FFMPEG_BIN="${HOME}/.local/bin/ffmpeg"
if [ ! -x "${FFMPEG_BIN}" ]; then
  echo "==> ffmpeg 설치 (${FFMPEG_BIN})"
  mkdir -p "${HOME}/.local/bin"
  TMP_ZIP="$(mktemp /tmp/ffmpeg-XXXXXX.zip)"
  curl -fsSL -o "${TMP_ZIP}" "https://evermeet.cx/ffmpeg/getrelease/zip"
  unzip -o "${TMP_ZIP}" -d "${HOME}/.local/bin/"
  chmod +x "${FFMPEG_BIN}"
  rm -f "${TMP_ZIP}"
fi

echo "==> Python 가상환경 (.venv)"
rm -rf .venv
uv venv .venv --python 3.11
uv pip install -r requirements.txt

echo ""
echo "✅ macOS 설치 완료"
echo "   실행: ./run.sh"
echo "   또는: ./.venv/bin/python getYoutubeUrl.py"
echo ""
echo "   VLC:    ${VLC_APP}"
echo "   ffmpeg: ${FFMPEG_BIN}"
echo "   Python: $(.venv/bin/python --version)"
