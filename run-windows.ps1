# getYoutubeUrl Windows 실행 (run-windows.bat 에서 호출)
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
