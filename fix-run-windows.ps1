# getYoutubeUrl run-windows.bat 진단 및 자동 복구
# - 가상환경/패키지/VLC/ffmpeg/run-windows.bat 인코딩 문제를 점검하고 수정
param(
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Set-Location $PSScriptRoot

$VlcVersion = "3.0.21"
$VlcUrl = "https://download.videolan.org/pub/videolan/vlc/$VlcVersion/win64/vlc-$VlcVersion-win64.exe"
$FfmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$FfmpegBin = Join-Path $env:LOCALAPPDATA "getYoutubeUrl\bin"
$DownloadDir = Join-Path $env:TEMP "getYoutubeUrl-setup"

Write-Host "==> getYoutubeUrl 실행 문제 진단 및 자동 복구" -ForegroundColor Cyan
Write-Host ""

$issues = New-Object System.Collections.Generic.List[string]
$fixed = New-Object System.Collections.Generic.List[string]

function Has-Command {
    param([Parameter(Mandatory = $true)][string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Ensure-DownloadDir {
    if (-not (Test-Path $DownloadDir)) {
        New-Item -ItemType Directory -Force -Path $DownloadDir | Out-Null
    }
}

function Download-File {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $true)][string]$Destination
    )
    Write-Host "   download: $Url"
    if (Has-Command "curl.exe") {
        & curl.exe -fsSL -o $Destination $Url
        if ($LASTEXITCODE -ne 0) { throw "download failed: $Url" }
        return
    }
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $Url -OutFile $Destination -UseBasicParsing
}

function Refresh-SessionPath {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($machinePath -and $userPath) {
        $env:Path = "$machinePath;$userPath"
    } elseif ($machinePath) {
        $env:Path = $machinePath
    } elseif ($userPath) {
        $env:Path = $userPath
    }
}

function Add-Fixed {
    param([string]$Message)
    $script:fixed.Add($Message)
    Write-Host "   [OK] $Message" -ForegroundColor Green
}

function Add-Issue {
    param([string]$Message)
    $script:issues.Add($Message)
    Write-Host "   [!!] $Message" -ForegroundColor Yellow
}

function Find-PythonLauncher {
    $candidates = @(
        @{ Cmd = "py"; Args = @("-3") },
        @{ Cmd = "python"; Args = @() }
    )
    foreach ($candidate in $candidates) {
        if (-not (Has-Command $candidate.Cmd)) { continue }
        & $candidate.Cmd @($candidate.Args + @("-c", "import sys; print(sys.version_info >= (3, 10))")) | Out-Null
        if ($LASTEXITCODE -ne 0) { continue }
        return $candidate
    }
    return $null
}

function Repair-RunWindowsBat {
    $batPath = Join-Path $PSScriptRoot "run-windows.bat"
    $expected = @(
        '@echo off',
        'setlocal',
        'cd /d "%~dp0"',
        '',
        'set "VENV_PY=%~dp0.venv\Scripts\python.exe"',
        'if not exist "%VENV_PY%" goto NO_VENV',
        '',
        'if exist "%ProgramFiles%\VideoLAN\VLC" set "PATH=%ProgramFiles%\VideoLAN\VLC;%PATH%"',
        'if exist "%ProgramFiles(x86)%\VideoLAN\VLC" set "PATH=%ProgramFiles(x86)%\VideoLAN\VLC;%PATH%"',
        '',
        'set "FFMPEG_BIN=%LOCALAPPDATA%\getYoutubeUrl\bin"',
        'if exist "%FFMPEG_BIN%\ffmpeg.exe" set "PATH=%FFMPEG_BIN%;%PATH%"',
        '',
        'rem Avoid %Y% expansion in getYoutubeUrl.py (cmd parses %Y as a variable)',
        'set "MAIN=g"',
        'set "MAIN=%MAIN%etYoutubeUrl.py"',
        '',
        '"%VENV_PY%" "%~dp0%MAIN%" %*',
        'exit /b %ERRORLEVEL%',
        '',
        ':NO_VENV',
        'echo [.venv missing] Run setup-windows-manual.bat or fix-run-windows.bat first. 1>&2',
        'exit /b 1',
        ''
    ) -join "`r`n"

    $needsRepair = $false
    if (-not (Test-Path $batPath)) {
        $needsRepair = $true
        Add-Issue "run-windows.bat 파일이 없습니다."
    } else {
        $raw = [IO.File]::ReadAllBytes($batPath)
        if ($raw -contains 0x0A -and ($raw -notcontains 0x0D)) {
            $needsRepair = $true
            Add-Issue "run-windows.bat 줄바꿈이 LF 전용입니다 (Windows cmd 호환 문제)."
        }
        $text = [Text.Encoding]::UTF8.GetString($raw).TrimStart([char]0xFEFF)
        if ($text -match '[\uAC00-\uD7A3]' -and $text -match 'if not exist .*\(') {
            $needsRepair = $true
            Add-Issue "run-windows.bat 한글+괄호 if 블록으로 cmd 파싱 오류 가능."
        }
        if ($text -notmatch 'FFMPEG_BIN') {
            $needsRepair = $true
            Add-Issue "run-windows.bat 에 ffmpeg PATH 설정이 없습니다."
        }
    }

    if ($needsRepair) {
        [IO.File]::WriteAllText($batPath, $expected, (New-Object Text.UTF8Encoding $false))
        Add-Fixed "run-windows.bat 을 Windows 호환 형식(CRLF, ASCII)으로 복구"
    } else {
        Write-Host "   [--] run-windows.bat 형식 정상"
    }
}

function Ensure-Venv {
    $venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        Write-Host "   [--] 가상환경 (.venv) 존재"
        return $venvPython
    }

    Add-Issue "가상환경 (.venv) 없음"
    $launcher = Find-PythonLauncher
    if (-not $launcher) {
        Add-Issue "Python 3.10+ 없음 - setup-windows-manual.ps1 실행 필요"
        return $null
    }

    Write-Host "==> 가상환경 생성 (.venv)"
    & $launcher.Cmd @($launcher.Args + @("-m", "venv", ".venv"))
    if ($LASTEXITCODE -ne 0) {
        throw "가상환경 생성 실패"
    }
    Add-Fixed "가상환경 (.venv) 생성"
    return $venvPython
}

function Ensure-PythonPackages {
    param([Parameter(Mandatory = $true)][string]$VenvPython)

    $checks = @(
        @{ Module = "tkinter"; Code = "import tkinter" },
        @{ Module = "vlc"; Code = "import vlc" },
        @{ Module = "yt_dlp"; Code = "import yt_dlp" }
    )
    $missing = @()
    foreach ($check in $checks) {
        & $VenvPython -c $check.Code 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            $missing += $check.Module
        }
    }

    if ($missing.Count -eq 0) {
        Write-Host "   [--] Python 패키지 정상 (tkinter, vlc, yt_dlp)"
        return
    }

    Add-Issue ("Python 패키지 누락: " + ($missing -join ", "))
    Write-Host "==> pip 패키지 설치"
    & $VenvPython -m pip install -U pip | Out-Null
    & $VenvPython -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        throw "pip 패키지 설치 실패"
    }
    Add-Fixed "requirements.txt 패키지 설치"
}

function Is-VlcInstalled {
    @(
        (Join-Path $env:ProgramFiles "VideoLAN\VLC\libvlc.dll"),
        (Join-Path ${env:ProgramFiles(x86)} "VideoLAN\VLC\libvlc.dll")
    ) | ForEach-Object { if (Test-Path $_) { return $true } }
    return $false
}

function Install-VlcDirect {
    Ensure-DownloadDir
    $installer = Join-Path $DownloadDir "vlc-$VlcVersion-win64.exe"
    Write-Host "==> VLC $VlcVersion download and install"
    Download-File -Url $VlcUrl -Destination $installer
    if ((Get-Item $installer).Length -lt 1000000) {
        throw "VLC installer file looks invalid"
    }
    $proc = Start-Process -FilePath $installer -ArgumentList "/S" -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        throw "VLC install failed (exit code $($proc.ExitCode))"
    }
}

function Ensure-Vlc {
    if (Is-VlcInstalled) {
        Write-Host "   [--] VLC installed"
        return
    }

    Add-Issue "VLC missing - playback unavailable"
    Install-VlcDirect
    if (-not (Is-VlcInstalled)) {
        Add-Issue "libvlc.dll still not found after VLC install"
        return
    }
    Add-Fixed "VLC installed"
}

function Add-UserPathEntry {
    param([Parameter(Mandatory = $true)][string]$Directory)
    if (-not (Test-Path $Directory)) {
        New-Item -ItemType Directory -Force -Path $Directory | Out-Null
    }
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -and ($userPath -split ';' | Where-Object { $_ -eq $Directory })) {
        return
    }
    if ($userPath) {
        [Environment]::SetEnvironmentVariable("Path", "$Directory;$userPath", "User")
    } else {
        [Environment]::SetEnvironmentVariable("Path", $Directory, "User")
    }
    Refresh-SessionPath
}

function Install-FfmpegDirect {
    Ensure-DownloadDir
    $zipPath = Join-Path $DownloadDir "ffmpeg-release-essentials.zip"
    $extractDir = Join-Path $DownloadDir "ffmpeg-extract"
    Write-Host "==> ffmpeg download and install ($FfmpegBin)"
    Download-File -Url $FfmpegUrl -Destination $zipPath
    if (Test-Path $extractDir) {
        Remove-Item -Recurse -Force $extractDir
    }
    Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force
    $ffmpegExe = Get-ChildItem -Path $extractDir -Filter "ffmpeg.exe" -Recurse |
        Select-Object -First 1 -ExpandProperty FullName
    if (-not $ffmpegExe) {
        throw "ffmpeg.exe not found in archive"
    }
    New-Item -ItemType Directory -Force -Path $FfmpegBin | Out-Null
    Copy-Item $ffmpegExe (Join-Path $FfmpegBin "ffmpeg.exe") -Force
    $ffprobeExe = Join-Path (Split-Path $ffmpegExe) "ffprobe.exe"
    if (Test-Path $ffprobeExe) {
        Copy-Item $ffprobeExe (Join-Path $FfmpegBin "ffprobe.exe") -Force
    }
    Add-UserPathEntry -Directory $FfmpegBin
}

function Ensure-FfmpegPath {
    if (Has-Command "ffmpeg") {
        Write-Host "   [--] ffmpeg available"
        return
    }
    if (Test-Path (Join-Path $FfmpegBin "ffmpeg.exe")) {
        Add-UserPathEntry -Directory $FfmpegBin
        Add-Fixed "ffmpeg PATH registered ($FfmpegBin)"
        return
    }

    Add-Issue "ffmpeg missing - MP3 save unavailable"
    Install-FfmpegDirect
    Refresh-SessionPath
    if (Has-Command "ffmpeg") {
        Add-Fixed "ffmpeg installed"
    }
}

function Test-AppLaunch {
    param([Parameter(Mandatory = $true)][string]$VenvPython)

    $vlcDir = Join-Path $env:ProgramFiles "VideoLAN\VLC"
    if (-not (Test-Path $vlcDir)) {
        $vlcDir = Join-Path ${env:ProgramFiles(x86)} "VideoLAN\VLC"
    }
    if (Test-Path $vlcDir) {
        $env:Path = "$vlcDir;$env:Path"
    }
    $ffBin = Join-Path $env:LOCALAPPDATA "getYoutubeUrl\bin"
    if (Test-Path (Join-Path $ffBin "ffmpeg.exe")) {
        $env:Path = "$ffBin;$env:Path"
    }

    & $VenvPython -c "import tkinter; import vlc; import yt_dlp; vlc.Instance('--quiet'); print('launch-check-ok')"
    if ($LASTEXITCODE -ne 0) {
        throw "실행 사전 검사 실패"
    }
    Write-Host "   [--] 실행 사전 검사 통과 (tkinter, vlc, yt_dlp)"
}

# --- main ---

Refresh-SessionPath
Repair-RunWindowsBat

$venvPython = Ensure-Venv
if (-not $venvPython) {
    Write-Host ""
    Write-Host "Python이 없습니다. setup-windows-manual.bat 을 먼저 실행하세요." -ForegroundColor Red
    exit 1
}

Ensure-PythonPackages -VenvPython $venvPython
Ensure-Vlc
Ensure-FfmpegPath
Refresh-SessionPath
Test-AppLaunch -VenvPython $venvPython

Write-Host ""
if ($issues.Count -gt 0) {
    Write-Host "발견된 문제:" -ForegroundColor Yellow
    foreach ($item in $issues) { Write-Host "   - $item" }
}
if ($fixed.Count -gt 0) {
    Write-Host "자동 복구:" -ForegroundColor Green
    foreach ($item in $fixed) { Write-Host "   - $item" }
}

Write-Host ""
Write-Host "복구 완료. run-windows.bat 으로 프로그램을 실행합니다..." -ForegroundColor Cyan
Write-Host ""

if ($NoLaunch) {
    Write-Host "(-NoLaunch) GUI 실행은 건너뜁니다."
    exit 0
}

$runBat = Join-Path $PSScriptRoot "run-windows.bat"
& cmd.exe /c "`"$runBat`""
