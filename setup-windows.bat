@echo off
setlocal
cd /d "%~dp0"

echo.
echo getYoutubeUrl Windows 환경 구축을 시작합니다...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-windows.ps1"
if errorlevel 1 (
    echo.
    echo [오류] 설치에 실패했습니다. 위 메시지를 확인하세요.
    pause
    exit /b 1
)

echo.
pause
