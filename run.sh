#!/bin/bash
# getYoutubeUrl 실행 스크립트
cd "$(dirname "$0")"

if [ "$(uname -s)" = "Darwin" ]; then
  # macOS: VLC를 ~/Applications 또는 /Applications 에서 찾음 (현재 CPU와 호환되는 것만)
  vlc_usable() {
    local app="$1"
    local exe="${app}/Contents/MacOS/VLC"
    local lib="${app}/Contents/MacOS/lib/libvlccore.dylib"
    local arch
    arch="$(uname -m)"
    [ -d "${app}" ] && [ -x "${exe}" ] && [ -f "${lib}" ] || return 1
    if command -v lipo >/dev/null 2>&1; then
      lipo -info "${lib}" 2>/dev/null | grep -q "${arch}"
    else
      file "${lib}" | grep -q "${arch}"
    fi
  }

  VLC_APP="${VLC_APP:-}"
  if [ -n "${VLC_APP}" ] && ! vlc_usable "${VLC_APP}"; then
    echo "VLC_APP=${VLC_APP} 가 이 Mac($(uname -m))과 호환되지 않습니다." >&2
    echo "./setup-mac.sh 를 실행하거나 VLC_APP 경로를 바꿔 주세요." >&2
    exit 1
  fi
  if [ -z "${VLC_APP}" ]; then
    for candidate in "${HOME}/Applications/VLC.app" "/Applications/VLC.app"; do
      if vlc_usable "${candidate}"; then
        VLC_APP="${candidate}"
        break
      fi
    done
  fi
  if [ -z "${VLC_APP}" ]; then
    echo "VLC가 필요합니다 (Apple Silicon / Intel 호환)." >&2
    echo "먼저 ./setup-mac.sh 를 실행하세요." >&2
    exit 1
  fi
  VLC_MACOS="${VLC_APP}/Contents/MacOS"
  export DYLD_LIBRARY_PATH="${VLC_MACOS}/lib${DYLD_LIBRARY_PATH:+:${DYLD_LIBRARY_PATH}}"
  export VLC_PLUGIN_PATH="${VLC_MACOS}/plugins"
  # ffmpeg (MP3 저장) — ~/.local/bin 우선
  export PATH="${HOME}/.local/bin:${PATH}"
else
  # Wayland 데스크톱에서 tkinter(XWayland) 디스플레이 지정
  export DISPLAY="${DISPLAY:-:0}"
  export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"
fi

exec ./.venv/bin/python getYoutubeUrl.py "$@"
