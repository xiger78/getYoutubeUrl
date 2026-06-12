# getYoutubeUrl — Windows 설치 파일(.exe) 빌드
# PyInstaller + VLC·ffmpeg 번들 + Inno Setup (선택)
#
# 사용법 (PowerShell):
#   .\scripts\build\build-windows.ps1
#
# 출력:
#   dist\getYoutubeUrl-<version>-win64-setup.exe  (Inno Setup 있을 때)
#   dist\getYoutubeUrl-<version>-win64.zip        (Inno Setup 없을 때)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Resolve-Path (Join-Path $ScriptDir "..\..")
Set-Location $Root

$Version = (Get-Content "VERSION" -Raw).Trim()
$VlcVersion = "3.0.21"
$VlcZipUrl = "https://get.videolan.org/vlc/$VlcVersion/win64/vlc-$VlcVersion-win64.zip"
$FfmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$CacheDir = Join-Path $Root "build\cache"
$OutDir = Join-Path $Root "dist\getYoutubeUrl-win"
$SetupExe = Join-Path $Root "dist\getYoutubeUrl-$Version-win64-setup.exe"
$SetupZip = Join-Path $Root "dist\getYoutubeUrl-$Version-win64.zip"
$IssFile = Join-Path $Root "installer\windows\getYoutubeUrl.iss"

function Write-Step([string]$Message) {
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Ensure-Venv {
    $python = Join-Path $Root ".venv\Scripts\python.exe"
    if (-not (Test-Path $python)) {
        Write-Step "가상환경 없음 — setup-windows.ps1 실행"
        & (Join-Path $Root "setup-windows.ps1")
    }
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv pip install -q -r requirements-build.txt
    } else {
        & $python -m ensurepip --upgrade
        & $python -m pip install -q -r requirements-build.txt
    }
    return $python
}

function Download-File([string]$Url, [string]$Dest) {
    if (Test-Path $Dest) { return }
    New-Item -ItemType Directory -Force -Path (Split-Path $Dest) | Out-Null
    Write-Step "다운로드: $Url"
    Invoke-WebRequest -Uri $Url -OutFile $Dest -UseBasicParsing
}

function Fetch-VlcPortable {
    $zipPath = Join-Path $CacheDir "vlc-$VlcVersion-win64.zip"
    $extractDir = Join-Path $CacheDir "vlc-portable"
    Download-File -Url $VlcZipUrl -Dest $zipPath
    if (-not (Test-Path (Join-Path $extractDir "libvlc.dll"))) {
        if (Test-Path $extractDir) { Remove-Item -Recurse -Force $extractDir }
        Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force
        $inner = Get-ChildItem $extractDir -Directory | Select-Object -First 1
        if ($inner -and (Test-Path (Join-Path $inner.FullName "libvlc.dll"))) {
            Get-ChildItem $inner.FullName | Move-Item -Destination $extractDir -Force
            Remove-Item $inner.FullName -Force -ErrorAction SilentlyContinue
        }
    }
    return $extractDir
}

function Fetch-FfmpegPortable {
    $zipPath = Join-Path $CacheDir "ffmpeg-release-essentials.zip"
    $binDir = Join-Path $CacheDir "bin"
    Download-File -Url $FfmpegUrl -Dest $zipPath
    if (-not (Test-Path (Join-Path $binDir "ffmpeg.exe"))) {
        $extractDir = Join-Path $CacheDir "ffmpeg-extract"
        if (Test-Path $extractDir) { Remove-Item -Recurse -Force $extractDir }
        Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force
        New-Item -ItemType Directory -Force -Path $binDir | Out-Null
        $ffmpegExe = Get-ChildItem -Path $extractDir -Filter "ffmpeg.exe" -Recurse |
            Select-Object -First 1
        if (-not $ffmpegExe) { throw "ffmpeg.exe not found in archive" }
        Copy-Item $ffmpegExe.FullName (Join-Path $binDir "ffmpeg.exe") -Force
        $ffprobe = Join-Path (Split-Path $ffmpegExe.FullName) "ffprobe.exe"
        if (Test-Path $ffprobe) {
            Copy-Item $ffprobe (Join-Path $binDir "ffprobe.exe") -Force
        }
    }
    return $binDir
}

function Run-PyInstaller([string]$Python) {
    Write-Step "PyInstaller 빌드"
    $work = Join-Path $Root "build\pyinstaller"
    if (Test-Path $OutDir) { Remove-Item -Recurse -Force $OutDir }
    $distPy = Join-Path $Root "dist\getYoutubeUrl"
    if (Test-Path $distPy) { Remove-Item -Recurse -Force $distPy }
    & $Python -m PyInstaller --noconfirm --distpath (Join-Path $Root "dist") --workpath $work (Join-Path $Root "getYoutubeUrl.spec")
    if (-not (Test-Path (Join-Path $distPy "getYoutubeUrl.exe"))) {
        throw "PyInstaller output not found: $distPy\getYoutubeUrl.exe"
    }
    Move-Item $distPy $OutDir
}

function Bundle-Dependencies {
    Write-Step "VLC·ffmpeg 번들 복사"
    $vlcSrc = Fetch-VlcPortable
    $vlcDest = Join-Path $OutDir "VLC"
    if (Test-Path $vlcDest) { Remove-Item -Recurse -Force $vlcDest }
    Copy-Item $vlcSrc $vlcDest -Recurse
    $ffSrc = Fetch-FfmpegPortable
    $ffDest = Join-Path $OutDir "bin"
    if (Test-Path $ffDest) { Remove-Item -Recurse -Force $ffDest }
    Copy-Item $ffSrc $ffDest -Recurse
}

function Build-InnoSetup {
    $isccCandidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    $iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $iscc) {
        Write-Host "   Inno Setup 6 미설치 — ZIP 설치 파일 생성" -ForegroundColor Yellow
        return $false
    }
    Write-Step "Inno Setup 컴파일"
    & $iscc "/DMyAppVersion=$Version" $IssFile
    if (-not (Test-Path $SetupExe)) {
        throw "Inno Setup failed: $SetupExe not created"
    }
    return $true
}

function Build-ZipFallback {
    Write-Step "ZIP 설치 파일 생성"
    if (Test-Path $SetupZip) { Remove-Item -Force $SetupZip }
    Compress-Archive -Path $OutDir -DestinationPath $SetupZip -Force
}

Write-Step "getYoutubeUrl Windows 설치 파일 빌드 (v$Version)"
$py = Ensure-Venv
Run-PyInstaller -Python $py
Bundle-Dependencies
if (-not (Build-InnoSetup)) {
    Build-ZipFallback
    Write-Host ""
    Write-Host "ZIP 설치 파일: $SetupZip" -ForegroundColor Green
    Write-Host "압축 해제 후 getYoutubeUrl.exe 실행"
} else {
    Write-Host ""
    Write-Host "Windows 설치 파일: $SetupExe" -ForegroundColor Green
}
