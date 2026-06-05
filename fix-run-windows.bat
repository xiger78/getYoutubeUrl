@echo off
setlocal
cd /d "%~dp0"

echo.
echo getYoutubeUrl run-windows.bat problem check and auto-fix...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0fix-run-windows.ps1"
set "ERR=%ERRORLEVEL%"

echo.
if not "%ERR%"=="0" (
    echo [ERROR] Auto-fix failed. See messages above.
    pause
    exit /b %ERR%
)

pause
