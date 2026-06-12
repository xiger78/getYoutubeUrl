#!/bin/bash
# getYoutubeUrl — 현재 OS에 맞는 설치 파일 빌드
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
case "$(uname -s)" in
    Darwin) exec "${SCRIPT_DIR}/build-mac.sh" "$@" ;;
    Linux)  exec "${SCRIPT_DIR}/build-linux.sh" "$@" ;;
    *)
        echo "Windows: PowerShell에서 .\\scripts\\build\\build-windows.ps1 실행" >&2
        exit 1
        ;;
esac
