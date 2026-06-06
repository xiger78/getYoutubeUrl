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

function Write-TextFileLf {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content,
        [switch]$Utf8BOM
    )
    $encoding = if ($Utf8BOM) {
        New-Object Text.UTF8Encoding $true
    } else {
        New-Object Text.UTF8Encoding $false
    }
    [IO.File]::WriteAllText($Path, ($Content -replace "`r?`n", "`r`n"), $encoding)
}

function Repair-RunWindowsBat {
    $batPath = Join-Path $PSScriptRoot "run-windows.bat"
    $ps1Path = Join-Path $PSScriptRoot "run-windows.ps1"

    $expectedBat = @'
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
'@

    $expectedPs1 = @'
# getYoutubeUrl Windows run (called from run-windows.bat)
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[.venv missing] Run setup-windows-manual.bat or fix-run-windows.bat first." -ForegroundColor Red
    exit 1
}

$vlcPaths = @(
    (Join-Path $env:ProgramFiles "VideoLAN\VLC"),
    (Join-Path ${env:ProgramFiles(x86)} "VideoLAN\VLC")
)
foreach ($vlcDir in $vlcPaths) {
    if (Test-Path $vlcDir) {
        $env:Path = "$vlcDir;$env:Path"
    }
}

$ffmpegBin = Join-Path $env:LOCALAPPDATA "getYoutubeUrl\bin"
if (Test-Path (Join-Path $ffmpegBin "ffmpeg.exe")) {
    $env:Path = "$ffmpegBin;$env:Path"
}

$mainPy = Join-Path $PSScriptRoot "getYoutubeUrl.py"
& $venvPython $mainPy @Args
exit $LASTEXITCODE
'@

    $needsRepair = $false
    if (-not (Test-Path $ps1Path)) {
        $needsRepair = $true
        Add-Issue "run-windows.ps1 파일이 없습니다."
    }
    if (-not (Test-Path $batPath)) {
        $needsRepair = $true
        Add-Issue "run-windows.bat 파일이 없습니다."
    } else {
        $raw = [IO.File]::ReadAllBytes($batPath)
        if ($raw -contains 0x0A -and ($raw -notcontains 0x0D)) {
            $needsRepair = $true
            Add-Issue "run-windows.bat 줄바꿈이 LF 전용입니다 (Windows cmd 호환 문제)."
        }
        for ($i = 0; $i -lt $raw.Length - 2; $i++) {
            if ($raw[$i] -eq 0x0D -and $raw[$i + 1] -eq 0x0D -and $raw[$i + 2] -eq 0x0A) {
                $needsRepair = $true
                Add-Issue "run-windows.bat 줄바꿈이 CR+CR+LF(이중 CR) 입니다."
                break
            }
        }
        $text = [Text.Encoding]::UTF8.GetString($raw).TrimStart([char]0xFEFF)
        if ($text -notmatch 'run-windows\.ps1') {
            $needsRepair = $true
            Add-Issue "run-windows.bat 이 run-windows.ps1 을 호출하지 않습니다."
        }
        if ($text -match 'getYoutubeUrl\.py') {
            $needsRepair = $true
            Add-Issue "run-windows.bat 에 getYoutubeUrl.py 직접 호출(%Y% 파싱 위험)이 있습니다."
        }
    }

    if ($needsRepair) {
        Write-TextFileLf -Path $batPath -Content $expectedBat
        Write-TextFileLf -Path $ps1Path -Content $expectedPs1 -Utf8BOM
        Add-Fixed "run-windows.bat / run-windows.ps1 을 Windows 호환 형식으로 복구"
    } else {
        Write-Host "   [--] run-windows.bat / run-windows.ps1 형식 정상"
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
        $oldEap = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        & $VenvPython -c $check.Code 2>&1 | Out-Null
        $ErrorActionPreference = $oldEap
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

    $oldEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $VenvPython -c "import tkinter; import vlc; import yt_dlp; vlc.Instance('--quiet'); print('launch-check-ok')" 2>&1 | Out-Null
    $ErrorActionPreference = $oldEap
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

$runPs1 = Join-Path $PSScriptRoot "run-windows.ps1"
& powershell -NoProfile -ExecutionPolicy Bypass -File $runPs1
