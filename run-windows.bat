@echo off
setlocal
cd /d "%~dp0"

set "VENV_PY=%~dp0.venv\Scripts\python.exe"
if not exist "%VENV_PY%" goto NO_VENV

if exist "%ProgramFiles%\VideoLAN\VLC" set "PATH=%ProgramFiles%\VideoLAN\VLC;%PATH%"
if exist "%ProgramFiles(x86)%\VideoLAN\VLC" set "PATH=%ProgramFiles(x86)%\VideoLAN\VLC;%PATH%"

set "FFMPEG_BIN=%LOCALAPPDATA%\getYoutubeUrl\bin"
if exist "%FFMPEG_BIN%\ffmpeg.exe" set "PATH=%FFMPEG_BIN%;%PATH%"

"%VENV_PY%" "%~dp0getYoutubeUrl.py" %*
exit /b %ERRORLEVEL%

:NO_VENV
echo [.venv missing] Run setup-windows-manual.bat or fix-run-windows.bat first. 1>&2
exit /b 1
