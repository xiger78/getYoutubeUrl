#!/bin/bash
# getYoutubeUrl — Linux 설치 파일(.deb) 빌드
# Debian / Ubuntu / Raspberry Pi OS (arm64·amd64)
#
# 사용법:
#   ./scripts/build/build-linux.sh              # amd64 (기본)
#   ./scripts/build/build-linux.sh arm64        # Raspberry Pi 등
#
# 출력:
#   dist/getYoutubeUrl_<version>_<arch>.deb

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${ROOT}"

VERSION="$(tr -d '[:space:]' < VERSION)"
ARCH="${1:-amd64}"
PKG_NAME="getYoutubeUrl"
DEB_ROOT="${ROOT}/build/deb-root"
OUT_DEB="${ROOT}/dist/${PKG_NAME}_${VERSION}_${ARCH}.deb"

log() { echo "==> $*"; }

if ! command -v dpkg-deb >/dev/null 2>&1; then
    echo "오류: dpkg-deb 가 필요합니다 (Debian/Ubuntu/Linux)." >&2
    exit 1
fi

log "Linux .deb 패키지 빌드 (v${VERSION}, ${ARCH})"

rm -rf "${DEB_ROOT}"
mkdir -p "${DEB_ROOT}/DEBIAN"
mkdir -p "${DEB_ROOT}/opt/${PKG_NAME}"
mkdir -p "${DEB_ROOT}/usr/share/applications"
mkdir -p "${DEB_ROOT}/usr/share/doc/${PKG_NAME}"
mkdir -p "${DEB_ROOT}/usr/bin"

if command -v rsync >/dev/null 2>&1; then
    rsync -a \
        --exclude '.venv' \
        --exclude '.git' \
        --exclude 'build' \
        --exclude 'dist' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude '.DS_Store' \
        "${ROOT}/" "${DEB_ROOT}/opt/${PKG_NAME}/"
else
    tar -C "${ROOT}" \
        --exclude='.venv' --exclude='.git' --exclude='build' --exclude='dist' \
        --exclude='__pycache__' --exclude='.DS_Store' \
        -cf - . | tar -C "${DEB_ROOT}/opt/${PKG_NAME}" -xf -
fi

cat > "${DEB_ROOT}/DEBIAN/control" <<EOF
Package: ${PKG_NAME}
Version: ${VERSION}
Section: sound
Priority: optional
Architecture: ${ARCH}
Depends: python3 (>= 3.10), python3-venv, python3-tk, vlc, ffmpeg
Maintainer: xiger78 <https://github.com/xiger78/getYoutubeUrl>
Description: YouTube search, playback, MP3/MV download GUI
 getYoutubeUrl searches YouTube, plays audio/MV, shows lyrics,
 and downloads MP3/MV files. Requires VLC and ffmpeg (apt packages).
EOF

cat > "${DEB_ROOT}/DEBIAN/postinst" <<'EOF'
#!/bin/bash
set -e
APP=/opt/getYoutubeUrl
cd "$APP"
if [[ ! -x .venv/bin/python ]]; then
    python3 -m venv .venv
    .venv/bin/pip install -U pip -q
    .venv/bin/pip install -r requirements.txt -q
fi
chmod +x /usr/bin/getYoutubeUrl
update-desktop-database 2>/dev/null || true
exit 0
EOF

cat > "${DEB_ROOT}/DEBIAN/prerm" <<'EOF'
#!/bin/bash
exit 0
EOF

cat > "${DEB_ROOT}/usr/bin/getYoutubeUrl" <<'EOF'
#!/bin/bash
APP=/opt/getYoutubeUrl
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"
export XMODIFIERS="${XMODIFIERS:-@im=fcitx}"
export GTK_IM_MODULE="${GTK_IM_MODULE:-fcitx}"
export QT_IM_MODULE="${QT_IM_MODULE:-fcitx}"
export SDL_IM_MODULE="${SDL_IM_MODULE:-fcitx}"
exec "${APP}/.venv/bin/python" "${APP}/getYoutubeUrl.py" "$@"
EOF

cat > "${DEB_ROOT}/usr/share/applications/getYoutubeUrl.desktop" <<EOF
[Desktop Entry]
Name=getYoutubeUrl
Comment=YouTube search and playback
Exec=/usr/bin/getYoutubeUrl
Icon=applications-multimedia
Terminal=false
Type=Application
Categories=AudioVideo;Player;
EOF

cp "${ROOT}/docs/README.md" "${DEB_ROOT}/usr/share/doc/${PKG_NAME}/README.md" 2>/dev/null || true

chmod 755 "${DEB_ROOT}/DEBIAN/postinst" "${DEB_ROOT}/DEBIAN/prerm"
chmod 755 "${DEB_ROOT}/usr/bin/getYoutubeUrl"

mkdir -p "${ROOT}/dist"
rm -f "${OUT_DEB}"
dpkg-deb --root-owner-group --build "${DEB_ROOT}" "${OUT_DEB}"
rm -rf "${DEB_ROOT}"

echo ""
echo "✅ Linux 설치 파일: ${OUT_DEB}"
echo "   설치: sudo dpkg -i ${OUT_DEB}"
echo "   의존성: sudo apt install -f"
