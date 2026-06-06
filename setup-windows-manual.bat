@echo off
setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-windows-manual.ps1"
set "ERR=%ERRORLEVEL%"
if not "%ERR%"=="0" (
    echo.
    echo [ERROR] Setup failed. See messages above.
    pause
    exit /b %ERR%
)

echo.
pause
exit /b 0
