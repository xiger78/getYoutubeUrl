@echo off
setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-windows.ps1"
set "ERR=%ERRORLEVEL%"
if not "%ERR%"=="0" (
    echo.
    echo [ERROR] Setup failed. Try setup-windows-manual.bat
    pause
    exit /b %ERR%
)

echo.
echo Setup complete. Run run-windows.bat
pause
exit /b 0
