@echo off
setlocal
cd /d "%~dp0"

echo.
echo getYoutubeUrl Windows 수동 환경 구축을 시작합니다...
echo winget 없이 python.org / VideoLAN / gyan.dev 에서 직접 설치합니다.
echo.
echo [참고] Python, VLC 설치 시 관리자 권한이 필요할 수 있습니다.
echo        UAC 창이 뜨면 허용해 주세요.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-windows-manual.ps1"
if errorlevel 1 (
    echo.
    echo [오류] 설치에 실패했습니다. 위 메시지를 확인하세요.
    pause
    exit /b 1
)

echo.
pause
