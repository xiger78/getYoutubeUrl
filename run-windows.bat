@echo off
setlocal
cd /d "%~dp0"

set "VENV_PY=%~dp0.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
    echo 가상환경이 없습니다. 먼저 setup-windows.bat 을 실행하세요. 1>&2
    exit /b 1
)

rem VLC libvlc.dll 경로 (python-vlc / libVLC)
if exist "%ProgramFiles%\VideoLAN\VLC" (
    set "PATH=%ProgramFiles%\VideoLAN\VLC;%PATH%"
)
if exist "%ProgramFiles(x86)%\VideoLAN\VLC" (
    set "PATH=%ProgramFiles(x86)%\VideoLAN\VLC;%PATH%"
)

"%VENV_PY%" "%~dp0getYoutubeUrl.py" %*
