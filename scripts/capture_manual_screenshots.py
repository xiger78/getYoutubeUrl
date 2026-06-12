#!/usr/bin/env python3
"""Capture getYoutubeUrl main window screenshots for each UI language."""

from __future__ import annotations

import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

if sys.platform == "darwin":
    for vlc_path in (
        os.path.expanduser("~/Applications/VLC.app"),
        "/Applications/VLC.app",
    ):
        if os.path.isdir(vlc_path):
            macos = os.path.join(vlc_path, "Contents", "MacOS")
            os.environ["DYLD_LIBRARY_PATH"] = os.path.join(macos, "lib")
            os.environ["VLC_PLUGIN_PATH"] = os.path.join(macos, "plugins")
            break

from i18n import LANG_MAP, LANG_OPTIONS  # noqa: E402

MAX_CAPTURE_BYTES = 500_000


def _cancel_pending_after(root) -> None:
    try:
        for aid in root.tk.call("after", "info"):
            try:
                root.after_cancel(aid)
            except Exception:
                pass
    except Exception:
        pass


def capture(lang_display: str, lang_code: str, out_dir: str) -> bool:
    import tkinter as tk

    import getYoutubeUrl  # noqa: WPS433

    app = getYoutubeUrl.YoutubeFinder()
    app._lang_display.set(lang_display)
    app._lang_code = LANG_MAP[lang_display]
    app._apply_ui_language()
    app.geometry("1240x900+50+50")
    app.deiconify()
    app.lift()
    app.focus_force()
    app.attributes("-topmost", True)
    app.update_idletasks()
    app.update()
    time.sleep(1.2)
    app.attributes("-topmost", False)
    app.update()

    out = os.path.join(out_dir, f"{lang_code}.png")
    wid = app.winfo_id()
    ok = subprocess.run(
        ["screencapture", "-x", "-l", str(wid), out],
        check=False,
    ).returncode == 0

    if not ok or not os.path.isfile(out) or os.path.getsize(out) < 10_000:
        x, y = app.winfo_rootx(), app.winfo_rooty()
        w, h = app.winfo_width(), app.winfo_height()
        subprocess.run(
            ["screencapture", "-x", "-R", f"{x},{y},{w},{h}", out],
            check=False,
        )

    _cancel_pending_after(app)
    app.destroy()
    tk._default_root = None  # noqa: SLF001

    if os.path.isfile(out) and os.path.getsize(out) <= MAX_CAPTURE_BYTES:
        print(out, os.path.getsize(out))
        return True
    return False


def main() -> None:
    out_dir = os.path.join(ROOT, "docs", "screenshots")
    os.makedirs(out_dir, exist_ok=True)
    ok_all = True
    for display in LANG_OPTIONS:
        if not capture(display, LANG_MAP[display], out_dir):
            ok_all = False
    if not ok_all:
        from render_manual_screenshots import main as render_main  # noqa: WPS433

        print("Live capture failed or too large; rendering UI mock…", file=sys.stderr)
        render_main()


if __name__ == "__main__":
    main()
