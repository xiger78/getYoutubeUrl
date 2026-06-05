#!/bin/bash
# getYoutubeUrl 실행 스크립트
cd "$(dirname "$0")"

if [ "$(uname -s)" = "Darwin" ]; then
  # macOS: VLC를 ~/Applications 또는 /Applications 에서 찾음
  VLC_APP="${VLC_APP:-}"
  if [ -z "${VLC_APP}" ]; then
    if [ -d "${HOME}/Applications/VLC.app" ]; then
      VLC_APP="${HOME}/Applications/VLC.app"
    elif [ -d "/Applications/VLC.app" ]; then
      VLC_APP="/Applications/VLC.app"
    fi
  fi
  if [ -z "${VLC_APP}" ] || [ ! -d "${VLC_APP}" ]; then
    echo "VLC가 필요합니다. 먼저 ./setup-mac.sh 를 실행하세요." >&2
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
