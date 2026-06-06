# getYoutubeUrl Windows 환경 자동 구축
# 사용: PowerShell에서 .\setup-windows.ps1
#       또는 setup-windows.bat 더블클릭
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Set-Location $PSScriptRoot

Write-Host "==> getYoutubeUrl Windows 환경 구축" -ForegroundColor Cyan
Write-Host ""

function Has-Command {
    param([Parameter(Mandatory = $true)][string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
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

function Install-WithWinget {
    param(
        [Parameter(Mandatory = $true)][string]$Id,
        [Parameter(Mandatory = $true)][string]$Label
    )

    if (-not (Has-Command "winget")) {
        Write-Host "   winget 없음 - $Label 수동 설치 필요" -ForegroundColor Yellow
        return $false
    }

    Write-Host "==> $Label 설치 (winget: $Id)"
    winget install --id $Id -e `
        --accept-package-agreements `
        --accept-source-agreements `
        --disable-interactivity
    Refresh-SessionPath
    return $true
}

function Find-Python {
    $candidates = @(
        @{ Cmd = "py"; Args = @("-3") },
        @{ Cmd = "python"; Args = @() },
        @{ Cmd = "python3"; Args = @() }
    )

    foreach ($candidate in $candidates) {
        if (-not (Has-Command $candidate.Cmd)) { continue }
        try {
            $versionText = & $candidate.Cmd @($candidate.Args + @("-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"))
            if ($LASTEXITCODE -ne 0) { continue }
            $parts = $versionText.Trim().Split(".")
            $major = [int]$parts[0]
            $minor = [int]$parts[1]
            if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) { continue }

            & $candidate.Cmd @($candidate.Args + @("-c", "import tkinter")) | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-Host "   $($candidate.Cmd): tkinter 없음 - python.org 설치본 사용 권장" -ForegroundColor Yellow
                continue
            }

            return @{
                Cmd  = $candidate.Cmd
                Args = $candidate.Args
            }
        } catch {
            continue
        }
    }
    return $null
}

function Ensure-Python {
    $python = Find-Python
    if ($python) { return $python }

    Write-Host "==> Python 3.10+ 미설치 - winget으로 설치 시도"
    Install-WithWinget -Id "Python.Python.3.12" -Label "Python 3.12" | Out-Null
    Refresh-SessionPath

    $python = Find-Python
    if (-not $python) {
        throw @"
Python 3.10 이상(tkinter 포함)을 찾을 수 없습니다.
https://www.python.org/downloads/ 에서 설치 후
'Add python.exe to PATH' 와 'tcl/tk and IDLE' 옵션을 선택하세요.
"@
    }
    return $python
}

function Is-VlcInstalled {
    $paths = @(
        (Join-Path $env:ProgramFiles "VideoLAN\VLC\libvlc.dll"),
        (Join-Path ${env:ProgramFiles(x86)} "VideoLAN\VLC\libvlc.dll")
    )
    foreach ($path in $paths) {
        if (Test-Path $path) { return $true }
    }
    return $false
}

function Ensure-Vlc {
    if (Is-VlcInstalled) {
        Write-Host "==> VLC 이미 설치됨"
        return
    }

    Write-Host "==> VLC 미설치 - winget으로 설치 시도"
    $installed = Install-WithWinget -Id "VideoLAN.VLC" -Label "VLC media player"
    if (-not $installed -or -not (Is-VlcInstalled)) {
        throw @"
VLC media player가 필요합니다.
https://www.videolan.org/vlc/ 에서 설치하거나
winget install VideoLAN.VLC
"@
    }
}

function Is-FfmpegInstalled {
    if (-not (Has-Command "ffmpeg")) { return $false }
    try {
        & ffmpeg -version | Out-Null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Ensure-Ffmpeg {
    if (Is-FfmpegInstalled) {
        Write-Host "==> ffmpeg 이미 설치됨"
        return
    }

    Write-Host "==> ffmpeg 미설치 - winget으로 설치 시도"
    Install-WithWinget -Id "Gyan.FFmpeg" -Label "ffmpeg" | Out-Null
    Refresh-SessionPath

    if (-not (Is-FfmpegInstalled)) {
        Write-Host "   ffmpeg 없음 - MP3 저장만 비활성화될 수 있습니다." -ForegroundColor Yellow
        Write-Host "   수동 설치: winget install Gyan.FFmpeg" -ForegroundColor Yellow
    }
}

function Get-VenvPython {
    $venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        throw "가상환경 Python을 찾을 수 없습니다: $venvPython"
    }
    return $venvPython
}

# --- 본체 ---

if (-not (Has-Command "winget")) {
    Write-Host "   winget 없음 - setup-windows-manual.ps1 로 전환합니다." -ForegroundColor Yellow
    Write-Host ""
    $manualScript = Join-Path $PSScriptRoot "setup-windows-manual.ps1"
    if (-not (Test-Path $manualScript)) {
        throw "winget 이 없고 setup-windows-manual.ps1 도 찾을 수 없습니다."
    }
    & $manualScript
    exit $LASTEXITCODE
}

$pythonInfo = Ensure-Python
$pythonCmd = $pythonInfo.Cmd
$pythonArgs = $pythonInfo.Args

Write-Host "==> Python: $(& $pythonCmd @($pythonArgs + @("--version")))"
Ensure-Vlc
Ensure-Ffmpeg

Write-Host "==> Python 가상환경 (.venv)"
$venvPath = Join-Path $PSScriptRoot ".venv"
if (Test-Path $venvPath) {
    Remove-Item -Recurse -Force $venvPath
}

& $pythonCmd @($pythonArgs + @("-m", "venv", ".venv"))
if ($LASTEXITCODE -ne 0) {
    throw "가상환경 생성 실패"
}

$venvPython = Get-VenvPython
& $venvPython -m pip install -U pip
if ($LASTEXITCODE -ne 0) { throw "pip 업그레이드 실패" }

& $venvPython -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "패키지 설치 실패" }

Write-Host ""
Write-Host "Windows 설치 완료" -ForegroundColor Green
Write-Host "   실행: .\run-windows.bat"
Write-Host "   또는: .\.venv\Scripts\python getYoutubeUrl.py"
Write-Host ""
Write-Host "   Python: $(& $venvPython --version)"
if (Is-VlcInstalled) {
    $vlcDir = Join-Path $env:ProgramFiles "VideoLAN\VLC"
    if (-not (Test-Path $vlcDir)) {
        $vlcDir = Join-Path ${env:ProgramFiles(x86)} "VideoLAN\VLC"
    }
    Write-Host "   VLC:    $vlcDir"
}
if (Is-FfmpegInstalled) {
    $ffmpegPath = (Get-Command ffmpeg).Source
    Write-Host "   ffmpeg: $ffmpegPath"
}
Write-Host ""
