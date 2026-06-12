#!/bin/bash
# getYoutubeUrl — macOS 설치 파일(.dmg) 빌드
# Apple Silicon(arm64) / Intel(x86_64) Universal VLC 번들 포함
#
# 사용법:
#   ./scripts/build/build-mac.sh
#
# 출력:
#   dist/getYoutubeUrl-<version>-mac-<arch>.dmg  (arch: x86_64 또는 arm64)
#   VLC는 Universal 번들 — Intel·Apple Silicon 공통

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${ROOT}"

VERSION="$(tr -d '[:space:]' < VERSION)"
VLC_VERSION="3.0.23"
VLC_DMG="vlc-${VLC_VERSION}-universal.dmg"
VLC_URL="https://download.videolan.org/pub/videolan/vlc/${VLC_VERSION}/macosx/${VLC_DMG}"
CACHE="${ROOT}/build/cache"
STAGING="${ROOT}/build/dmg-staging"
ARCH="$(uname -m)"
OUT_DMG="${ROOT}/dist/getYoutubeUrl-${VERSION}-mac-${ARCH}.dmg"
APP_NAME="getYoutubeUrl.app"

log() { echo "==> $*"; }

ensure_venv() {
    if [[ ! -x "${ROOT}/.venv/bin/python" ]]; then
        log "가상환경 없음 — setup-mac.sh 실행"
        bash "${ROOT}/setup-mac.sh"
    fi
    if command -v uv >/dev/null 2>&1; then
        uv pip install -q -r "${ROOT}/requirements-build.txt"
    else
        "${ROOT}/.venv/bin/python" -m ensurepip --upgrade
        "${ROOT}/.venv/bin/python" -m pip install -q -r "${ROOT}/requirements-build.txt"
    fi
}

fetch_vlc() {
    local vlc_app="${CACHE}/VLC.app"
    if [[ -d "${vlc_app}/Contents/MacOS/VLC" ]]; then
        return 0
    fi
    log "VLC ${VLC_VERSION} universal 다운로드"
    mkdir -p "${CACHE}"
    local tmp_dmg
    tmp_dmg="$(mktemp /tmp/vlc-build-XXXXXX.dmg)"
    curl -fsSL -o "${tmp_dmg}" "${VLC_URL}"
    hdiutil attach "${tmp_dmg}" -nobrowse -quiet
    rm -rf "${vlc_app}"
    cp -R "/Volumes/VLC media player/VLC.app" "${vlc_app}"
    hdiutil detach "/Volumes/VLC media player" -quiet || true
    rm -f "${tmp_dmg}"
}

fetch_ffmpeg() {
    local ff="${CACHE}/bin/ffmpeg"
    if [[ -x "${ff}" ]]; then
        return 0
    fi
    log "ffmpeg 다운로드 (evermeet.cx)"
    mkdir -p "${CACHE}/bin"
    local tmp_zip
    tmp_zip="$(mktemp /tmp/ffmpeg-build-XXXXXX.zip)"
    curl -fsSL -o "${tmp_zip}" "https://evermeet.cx/ffmpeg/getrelease/zip"
    unzip -o -j "${tmp_zip}" "ffmpeg" -d "${CACHE}/bin/"
    chmod +x "${ff}"
    rm -f "${tmp_zip}"
}

run_pyinstaller() {
    log "PyInstaller 빌드"
    rm -rf "${ROOT}/build/pyinstaller" "${ROOT}/dist/${APP_NAME}" "${ROOT}/dist/getYoutubeUrl"
    "${ROOT}/.venv/bin/pyinstaller" \
        --noconfirm \
        --distpath "${ROOT}/dist" \
        --workpath "${ROOT}/build/pyinstaller" \
        "${ROOT}/getYoutubeUrl.spec"
}

bundle_deps() {
    local app="${ROOT}/dist/${APP_NAME}"
    if [[ ! -d "${app}" ]]; then
        echo "오류: ${app} 없음" >&2
        exit 1
    fi
    log "VLC·ffmpeg 앱 번들에 복사"
    mkdir -p "${app}/Contents/Resources"
    rm -rf "${app}/Contents/Resources/VLC.app"
    cp -R "${CACHE}/VLC.app" "${app}/Contents/Resources/VLC.app"
    mkdir -p "${app}/Contents/MacOS/bin"
    cp "${CACHE}/bin/ffmpeg" "${app}/Contents/MacOS/bin/ffmpeg"
    chmod +x "${app}/Contents/MacOS/bin/ffmpeg"
}

create_dmg() {
    log "DMG 생성 → ${OUT_DMG}"
    rm -rf "${STAGING}" "${OUT_DMG}"
    mkdir -p "${STAGING}"
    cp -R "${ROOT}/dist/${APP_NAME}" "${STAGING}/"
    ln -s /Applications "${STAGING}/Applications"
    mkdir -p "${ROOT}/dist"
    hdiutil create \
        -volname "getYoutubeUrl ${VERSION}" \
        -srcfolder "${STAGING}" \
        -ov \
        -format UDZO \
        "${OUT_DMG}"
    rm -rf "${STAGING}"
}

log "getYoutubeUrl macOS 설치 파일 빌드 (v${VERSION})"
ensure_venv
fetch_vlc
fetch_ffmpeg
run_pyinstaller
bundle_deps
create_dmg

echo ""
echo "✅ macOS 설치 파일: ${OUT_DMG}"
echo "   Applications 폴더로 getYoutubeUrl.app 을 드래그하여 설치"
