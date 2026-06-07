@echo off
setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-windows-manual.ps1"
if errorlevel 1 goto SETUP_FAIL

echo.
echo Setup complete. Run run-windows.bat
pause
exit /b 0

:SETUP_FAIL
echo.
echo [ERROR] Setup failed. See messages above.
pause
exit /b 1
