#!/bin/bash
# getYoutubeUrl macOS 환경 자동 구축 (sudo 불필요)
set -euo pipefail
cd "$(dirname "$0")"

echo "==> getYoutubeUrl macOS 환경 구축"

# uv (사용자 로컬 Python 관리)
if ! command -v uv >/dev/null 2>&1; then
  echo "==> uv 설치"
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
# shellcheck disable=SC1091
source "${HOME}/.local/bin/env"

echo "==> Python 3.11 설치"
uv python install 3.11

# VLC (mp3player와 동일 — ~/Applications)
VLC_APP="${HOME}/Applications/VLC.app"
if [ ! -x "${VLC_APP}/Contents/MacOS/VLC" ]; then
  echo "==> VLC 다운로드 및 설치 (${VLC_APP})"
  TMP_DMG="$(mktemp /tmp/vlc-XXXXXX.dmg)"
  curl -fsSL -o "${TMP_DMG}" \
    "https://download.videolan.org/pub/videolan/vlc/3.0.21/macosx/vlc-3.0.21-intel64.dmg"
  mkdir -p "${HOME}/Applications"
  hdiutil attach "${TMP_DMG}" -nobrowse -quiet
  rm -rf "${VLC_APP}"
  cp -R "/Volumes/VLC media player/VLC.app" "${HOME}/Applications/"
  hdiutil detach "/Volumes/VLC media player" -quiet
  rm -f "${TMP_DMG}"
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
