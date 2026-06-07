# getYoutubeUrl Windows 수동 환경 구축 (winget 불필요)
# python.org / VideoLAN / gyan.dev 에서 직접 다운로드·설치
# 사용: .\setup-windows-manual.ps1  또는 setup-windows-manual.bat
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Set-Location $PSScriptRoot

$PythonVersion = "3.12.10"
$PythonUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-amd64.exe"
$VlcVersion = "3.0.21"
$VlcUrl = "https://download.videolan.org/pub/videolan/vlc/$VlcVersion/win64/vlc-$VlcVersion-win64.exe"
$FfmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$FfmpegBin = Join-Path $env:LOCALAPPDATA "getYoutubeUrl\bin"
$DownloadDir = Join-Path $env:TEMP "getYoutubeUrl-setup"

Write-Host "==> getYoutubeUrl Windows 수동 환경 구축 (winget 불필요)" -ForegroundColor Cyan
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

    Write-Host "   다운로드: $Url"
    if (Has-Command "curl.exe") {
        & curl.exe -fsSL -o $Destination $Url
        if ($LASTEXITCODE -ne 0) {
            throw "curl 다운로드 실패: $Url"
        }
        return
    }

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $Url -OutFile $Destination -UseBasicParsing -MaximumRedirection 10
}

function Test-PythonExe {
    param(
        [Parameter(Mandatory = $true)][string]$Exe,
        [string[]]$Args = @()
    )

    $isPath = $Exe -match '[\\/]' -or $Exe -match '\.exe$'
    if ($isPath) {
        if (-not (Test-Path $Exe)) { return $null }
    } elseif (-not (Has-Command $Exe)) {
        return $null
    }
    try {
        $versionText = & $Exe @($Args + @("-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"))
        if ($LASTEXITCODE -ne 0) { return $null }
        $parts = $versionText.Trim().Split(".")
        $major = [int]$parts[0]
        $minor = [int]$parts[1]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) { return $null }

        & $Exe @($Args + @("-c", "import tkinter")) | Out-Null
        if ($LASTEXITCODE -ne 0) { return $null }

        return @{
            Cmd  = $Exe
            Args = $Args
        }
    } catch {
        return $null
    }
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

    $versionParts = $PythonVersion.Split(".")
    $pythonTag = "Python$($versionParts[0])$($versionParts[1])"
    $pathCandidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python\$pythonTag\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\$pythonTag-32\python.exe"),
        (Join-Path ${env:ProgramFiles} "$pythonTag\python.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "$pythonTag\python.exe")
    )
    foreach ($exe in $pathCandidates) {
        $found = Test-PythonExe -Exe $exe
        if ($found) { return $found }
    }

    return $null
}

function Install-PythonDirect {
    Ensure-DownloadDir
    $installer = Join-Path $DownloadDir "python-$PythonVersion-amd64.exe"
    Write-Host "==> Python $PythonVersion 다운로드 및 설치"
    Download-File -Url $PythonUrl -Destination $installer

    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).
        IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    $scope = if ($isAdmin) { "InstallAllUsers=1" } else { "InstallAllUsers=0" }
    $args = "/quiet $scope PrependPath=1 Include_pip=1 Include_tcltk=1 Include_test=0"
    $proc = Start-Process -FilePath $installer -ArgumentList $args -Wait -PassThru
    Refresh-SessionPath
    if (-not (Find-Python)) {
        throw "Python 설치 실패 (exit code $($proc.ExitCode)). 관리자 권한으로 다시 시도하세요."
    }
}

function Ensure-Python {
    $python = Find-Python
    if ($python) {
        Write-Host "==> Python 이미 설치됨: $(& $python.Cmd @($python.Args + @('--version')))"
        return $python
    }

    Install-PythonDirect
    $python = Find-Python
    if (-not $python) {
        throw "Python 설치 후에도 실행 파일을 찾을 수 없습니다. 터미널을 다시 열고 재시도하세요."
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

function Install-VlcDirect {
    Ensure-DownloadDir
    $installer = Join-Path $DownloadDir "vlc-$VlcVersion-win64.exe"
    Write-Host "==> VLC $VlcVersion 다운로드 및 설치"
    Download-File -Url $VlcUrl -Destination $installer

    $size = (Get-Item $installer).Length
    if ($size -lt 1000000) {
        throw "VLC 설치 파일 크기가 비정상입니다. 네트워크 연결을 확인하세요."
    }

    Start-Process -FilePath $installer -ArgumentList "/S" -Wait | Out-Null
    Start-Sleep -Seconds 2
    if (-not (Is-VlcInstalled)) {
        throw "VLC 설치 실패. 설치 파일을 직접 실행하거나 https://www.videolan.org/vlc/ 에서 설치하세요."
    }
}

function Ensure-Vlc {
    if (Is-VlcInstalled) {
        Write-Host "==> VLC 이미 설치됨"
        return
    }
    Install-VlcDirect
    if (-not (Is-VlcInstalled)) {
        throw "VLC 설치 후 libvlc.dll 을 찾을 수 없습니다."
    }
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

function Is-FfmpegInstalled {
    if (-not (Has-Command "ffmpeg")) { return $false }
    try {
        & ffmpeg -version | Out-Null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Install-FfmpegDirect {
    Ensure-DownloadDir
    $zipPath = Join-Path $DownloadDir "ffmpeg-release-essentials.zip"
    $extractDir = Join-Path $DownloadDir "ffmpeg-extract"

    Write-Host "==> ffmpeg 다운로드 및 설치 ($FfmpegBin)"
    Download-File -Url $FfmpegUrl -Destination $zipPath

    if (Test-Path $extractDir) {
        Remove-Item -Recurse -Force $extractDir
    }
    Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

    $ffmpegExe = Get-ChildItem -Path $extractDir -Filter "ffmpeg.exe" -Recurse |
        Select-Object -First 1 -ExpandProperty FullName
    if (-not $ffmpegExe) {
        throw "ffmpeg.exe 를 압축 파일에서 찾을 수 없습니다."
    }

    New-Item -ItemType Directory -Force -Path $FfmpegBin | Out-Null
    Copy-Item $ffmpegExe (Join-Path $FfmpegBin "ffmpeg.exe") -Force

    $ffprobeExe = Join-Path (Split-Path $ffmpegExe) "ffprobe.exe"
    if (Test-Path $ffprobeExe) {
        Copy-Item $ffprobeExe (Join-Path $FfmpegBin "ffprobe.exe") -Force
    }

    Add-UserPathEntry -Directory $FfmpegBin
}

function Ensure-Ffmpeg {
    if (Is-FfmpegInstalled) {
        Write-Host "==> ffmpeg 이미 설치됨"
        return
    }
    Install-FfmpegDirect
    if (-not (Is-FfmpegInstalled)) {
        Write-Host "   ffmpeg 없음 - MP3 저장만 비활성화될 수 있습니다." -ForegroundColor Yellow
    }
}

function Get-VenvPython {
    $venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        throw "가상환경 Python을 찾을 수 없습니다: $venvPython"
    }
    return $venvPython
}

function Remove-VenvSafe {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path $Path)) { return $true }

    try {
        Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
        return -not (Test-Path $Path)
    } catch {
        Write-Host "   .venv 파일이 사용 중입니다. rmdir로 재시도합니다..." -ForegroundColor Yellow
    }

    cmd /c "if exist `"$Path`" rmdir /s /q `"$Path`" 2>nul" | Out-Null
    if (-not (Test-Path $Path)) { return $true }

    $backupName = ".venv.old." + [Guid]::NewGuid().ToString("N").Substring(0, 8)
    try {
        Rename-Item -LiteralPath $Path -NewName $backupName -ErrorAction Stop
        Write-Host "   기존 .venv 를 $backupName 으로 이름 변경했습니다" -ForegroundColor Yellow
        return $true
    } catch {
        return $false
    }
}

# --- 본체 ---

$pythonInfo = Ensure-Python
$pythonCmd = $pythonInfo.Cmd
$pythonArgs = $pythonInfo.Args

Ensure-Vlc
Ensure-Ffmpeg

Write-Host "==> Python 가상환경 (.venv)"
$venvPath = Join-Path $PSScriptRoot ".venv"
$reuseVenv = $false
if (Test-Path $venvPath) {
    if (-not (Remove-VenvSafe -Path $venvPath)) {
        Write-Host "   기존 .venv 삭제 불가 - 패키지만 재설치합니다" -ForegroundColor Yellow
        $reuseVenv = $true
    }
}

if (-not $reuseVenv) {
    & $pythonCmd @($pythonArgs + @("-m", "venv", ".venv"))
    if ($LASTEXITCODE -ne 0) {
        throw "가상환경 생성 실패"
    }
}

$venvPython = Get-VenvPython
& $venvPython -m pip install -U pip
if ($LASTEXITCODE -ne 0) { throw "pip 업그레이드 실패" }

& $venvPython -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "패키지 설치 실패" }

Write-Host ""
Write-Host "Windows 수동 설치 완료" -ForegroundColor Green
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
