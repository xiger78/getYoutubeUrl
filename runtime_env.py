"""VLC·ffmpeg 경로 설정 — 개발 실행 및 PyInstaller 빌드 공통."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path


def _frozen_exe_dir() -> Path | None:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return None


def _prepend_path(directory: Path) -> None:
    text = str(directory)
    current = os.environ.get("PATH", "")
    if text not in current.split(os.pathsep):
        os.environ["PATH"] = text + os.pathsep + current


def _mac_vlc_usable(app: Path) -> bool:
    exe = app / "Contents/MacOS/VLC"
    lib = app / "Contents/MacOS/lib/libvlccore.dylib"
    if not exe.is_file() or not lib.is_file():
        return False
    arch = platform.machine()
    try:
        proc = subprocess.run(
            ["lipo", "-info", str(lib)],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0 and arch in proc.stdout:
            return True
    except OSError:
        pass
    try:
        proc = subprocess.run(
            ["file", str(lib)],
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode == 0 and arch in proc.stdout
    except OSError:
        return True


def _configure_mac() -> None:
    exe_dir = _frozen_exe_dir()
    candidates: list[Path] = []
    if exe_dir:
        contents = exe_dir.parent
        candidates.extend(
            [
                contents / "Resources" / "VLC.app",
                contents / "Frameworks" / "VLC.app",
                exe_dir / "VLC.app",
            ]
        )
    vlc_app = os.environ.get("VLC_APP")
    if vlc_app:
        candidates.insert(0, Path(vlc_app))
    candidates.extend(
        [
            Path.home() / "Applications" / "VLC.app",
            Path("/Applications/VLC.app"),
        ]
    )
    for app in candidates:
        if _mac_vlc_usable(app):
            macos = app / "Contents/MacOS"
            lib_dir = macos / "lib"
            os.environ["DYLD_LIBRARY_PATH"] = (
                str(lib_dir)
                + (
                    os.pathsep + os.environ["DYLD_LIBRARY_PATH"]
                    if os.environ.get("DYLD_LIBRARY_PATH")
                    else ""
                )
            )
            os.environ["VLC_PLUGIN_PATH"] = str(macos / "plugins")
            break

    ff_candidates: list[Path] = []
    if exe_dir:
        ff_candidates.extend(
            [
                exe_dir / "bin" / "ffmpeg",
                exe_dir.parent / "Resources" / "bin" / "ffmpeg",
            ]
        )
    ff_candidates.append(Path.home() / ".local/bin/ffmpeg")
    for ff in ff_candidates:
        if ff.is_file():
            _prepend_path(ff.parent)
            break
    else:
        _prepend_path(Path.home() / ".local/bin")


def _configure_windows() -> None:
    exe_dir = _frozen_exe_dir()
    if exe_dir:
        bundled_vlc = exe_dir / "VLC"
        if (bundled_vlc / "libvlc.dll").is_file():
            _prepend_path(bundled_vlc)
        bundled_bin = exe_dir / "bin"
        if (bundled_bin / "ffmpeg.exe").is_file():
            _prepend_path(bundled_bin)

    for vlc_dir in (
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "VideoLAN" / "VLC",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
        / "VideoLAN"
        / "VLC",
    ):
        if (vlc_dir / "libvlc.dll").is_file():
            _prepend_path(vlc_dir)
            break

    local_bin = Path(os.environ.get("LOCALAPPDATA", "")) / "getYoutubeUrl" / "bin"
    if (local_bin / "ffmpeg.exe").is_file():
        _prepend_path(local_bin)


def _configure_linux() -> None:
    os.environ.setdefault("DISPLAY", ":0")
    os.environ.setdefault("XAUTHORITY", str(Path.home() / ".Xauthority"))
    os.environ.setdefault("XMODIFIERS", "@im=fcitx")
    os.environ.setdefault("GTK_IM_MODULE", "fcitx")
    os.environ.setdefault("QT_IM_MODULE", "fcitx")
    os.environ.setdefault("SDL_IM_MODULE", "fcitx")

    exe_dir = _frozen_exe_dir()
    if exe_dir:
        bundled_bin = exe_dir / "bin"
        if (bundled_bin / "ffmpeg").is_file():
            _prepend_path(bundled_bin)


def configure_runtime() -> None:
    if sys.platform == "darwin":
        _configure_mac()
    elif sys.platform == "win32":
        _configure_windows()
    else:
        _configure_linux()
