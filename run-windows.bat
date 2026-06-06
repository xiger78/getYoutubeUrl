@echo off
setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-windows.ps1" %*
set "ERR=%ERRORLEVEL%"
if not "%ERR%"=="0" (
    echo.
    echo [ERROR] getYoutubeUrl start failed. Try fix-run-windows.bat
    pause
    exit /b %ERR%
)
exit /b 0
