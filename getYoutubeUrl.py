#!/usr/bin/env python3
"""
getYoutubeUrl — 유튜브 노래 검색 + 재생리스트 + 재생 GUI

1. 노래 제목을 입력해 유튜브 상위 10개를 검색한다. (yt-dlp)
2. 검색 결과에서 "추가" 로 원하는 곡을 재생리스트에 담는다.
3. 재생리스트에서 곡을 고르고 "재생" 을 누르면 VLC 로 오디오를 재생한다.
   (yt-dlp 로 오디오 스트림 URL 을 추출해 libVLC 로 재생)
"""

from __future__ import annotations

import os

# tkinter(XIM) 한글 입력 — Tcl/Tk 초기화 전에 설정해야 함
os.environ.setdefault("XMODIFIERS", "@im=fcitx")
os.environ.setdefault("GTK_IM_MODULE", "fcitx")
os.environ.setdefault("QT_IM_MODULE", "fcitx")
os.environ.setdefault("SDL_IM_MODULE", "fcitx")

import queue
import random
import re
import shutil
import sys
import tempfile
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, ttk

import vlc
import yt_dlp

from i18n import DEFAULT_LANG, LANG_MAP, LANG_OPTIONS, tr

# macOS: tkinter winfo_id() 는 NSView 포인터가 아니므로 VLC 영상 임베딩이 실패한다.
_mac_get_nsview = None
if sys.platform == "darwin":
    try:
        from ctypes import cdll, c_void_p
        from ctypes.util import find_library

        def _find_libtk() -> str | None:
            libname = f"libtk{tk.TkVersion}.dylib"
            for prefix in (getattr(sys, "base_prefix", ""), sys.prefix):
                if prefix:
                    candidate = os.path.join(prefix, "lib", libname)
                    if os.path.isfile(candidate):
                        return candidate
            return find_library("tk")

        _libtk_path = _find_libtk()
        if _libtk_path:
            _libtk = cdll.LoadLibrary(_libtk_path)
            _mac_get_nsview = _libtk.TkMacOSXGetRootControl
            _mac_get_nsview.restype = c_void_p
            _mac_get_nsview.argtypes = (c_void_p,)
    except (AttributeError, OSError):
        pass

# VLC 가 직접 재생할 수 있는 단일 스트림 포맷 (video+audio merge 제외)
AUDIO_FORMAT = "bestaudio[ext=m4a]/bestaudio/best[acodec!=none]/best"

# MV 재생 해상도 (라벨 → 최대 세로 픽셀)
MV_RESOLUTIONS: dict[str, int] = {
    "HD": 720,
    "FHD": 1080,
    "QHD": 1440,
    "2K": 1440,
    "4K": 2160,
}
DEFAULT_MV_RESOLUTION = "FHD"


def mv_format(max_height: int) -> str:
    """VLC 단일 URL 재생 불가 → ffmpeg 병합용 video+audio 포맷."""
    h = max_height
    return (
        f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo[height<={h}]+bestaudio/"
        f"best[height<={h}]/best"
    )

try:
    import syncedlyrics
    _HAS_LYRICS = True
except ImportError:
    _HAS_LYRICS = False

try:
    from kar_maker import create_kar_from_mp3
    _HAS_KAR = True
except ImportError:
    _HAS_KAR = False

DEFAULT_RESULTS = 20   # 검색 시 기본으로 가져올 결과 수
MAX_RESULTS = 200      # 검색 개수 입력 상한 (재생 리스트 추가 자체는 무제한)
MP3_AUDIO_EXTS = {".mp3", ".m4a", ".flac", ".ogg", ".wav"}

# 뮤직비디오 제목 판별 (MV, Official Video, 뮤직비디오 등)
MV_TITLE_RE = re.compile(
    r"(?i)(official\s*)?(m/?v|music\s*video|뮤직비디오|뮤비|ミュージック.?ビデオ)"
)


def is_mv_title(title: str) -> bool:
    return bool(MV_TITLE_RE.search(title or ""))


def fmt_duration(sec) -> str:
    if not sec:
        return "--:--"
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _ytdlp_opts(**extra) -> dict:
    opts = {"quiet": True, "no_warnings": True, "noplaylist": True}
    opts.update(extra)
    return opts


def _resolve_stream(info: dict) -> tuple[str | None, dict]:
    """yt-dlp info 에서 VLC 재생 가능한 URL·헤더를 추출."""
    headers = info.get("http_headers") or {}
    url = info.get("url")
    if url:
        return url, headers
    for fmt in reversed(info.get("requested_formats") or []):
        if fmt.get("url") and fmt.get("acodec") not in (None, "none"):
            return fmt["url"], fmt.get("http_headers") or headers
    for fmt in reversed(info.get("requested_formats") or []):
        if fmt.get("url"):
            return fmt["url"], fmt.get("http_headers") or headers
    return None, headers


def _vlc_media(vlc_instance, stream_url: str, http_headers: dict | None = None):
    media = vlc_instance.media_new(stream_url)
    if http_headers:
        for key, value in http_headers.items():
            lk = key.lower().replace("_", "-")
            if lk == "user-agent":
                media.add_option(f":http-user-agent={value}")
            elif lk in ("referer", "referrer"):
                media.add_option(f":http-referrer={value}")
            elif lk == "cookie":
                media.add_option(f":http-cookies={value}")
    return media


def _vlc_embed_handle(widget) -> int:
    """플랫폼별 VLC 출력 대상 핸들."""
    wid = widget.winfo_id()
    if sys.platform == "darwin" and _mac_get_nsview:
        ns = _mac_get_nsview(wid)
        if ns:
            return ns
    return wid


class MvPlayerWindow(tk.Toplevel):
    """뮤직비디오 전용 팝업 재생 (초기 800×600, F11 전체화면)."""

    MV_WIDTH = 800
    MV_HEIGHT = 600

    def __init__(self, app: YoutubeFinder, item: dict, max_height: int, res_label: str) -> None:
        super().__init__(app)
        self.app = app
        self.item = item
        self.max_height = max_height
        self.res_label = res_label
        self.actual_height: int | None = None
        self._tmpdir: str | None = None
        self._player = app._vlc.media_player_new()
        self.title(item.get("title", self.app.t("mv_default_title")))
        self.configure(bg="#000000")
        self.geometry(f"{self.MV_WIDTH}x{self.MV_HEIGHT}")
        self.minsize(640, 480)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Escape>", self._on_escape)
        self.bind("<F11>", lambda e: self._toggle_fullscreen())

        self.video_panel = tk.Frame(self, bg="#000000")
        self.video_panel.pack(fill="both", expand=True)
        self.video_panel.bind("<Double-Button-1>", lambda e: self._toggle_fullscreen())

        bar = tk.Frame(self, bg="#0f172a", height=36)
        bar.pack(fill="x", side="bottom")
        tk.Label(
            bar, text=item.get("title", ""), bg="#0f172a", fg="#e2e8f0",
            font=("sans-serif", 10), anchor="w",
        ).pack(side="left", padx=12, pady=6)
        self._mv_fullscreen_btn = ttk.Button(
            bar, text=self.app.t("fullscreen"), command=self._toggle_fullscreen,
        )
        self._mv_fullscreen_btn.pack(side="right", padx=4, pady=4)
        self._mv_close_btn = ttk.Button(
            bar, text=self.app.t("close"), command=self.close,
        )
        self._mv_close_btn.pack(side="right", padx=8, pady=4)

        app._player.stop()
        threading.Thread(target=self._fetch_stream, daemon=True).start()

    def _fetch_stream(self) -> None:
        tmpdir = tempfile.mkdtemp(prefix="getYoutubeUrl_mv_")
        self._tmpdir = tmpdir
        outtmpl = os.path.join(tmpdir, "video.%(ext)s")
        title = self.item.get("title", "")

        def _hook(d: dict) -> None:
            status = d.get("status")
            if status == "downloading":
                pct = (d.get("_percent_str") or "").strip()
                self.app._queue.put((
                    "status",
                    self.app.t("status_mv_dl", res=self.res_label, pct=pct, title=title),
                ))
            elif status == "finished" and d.get("postprocessor"):
                self.app._queue.put((
                    "status",
                    self.app.t("status_mv_merge", res=self.res_label, title=title),
                ))

        try:
            opts = _ytdlp_opts(
                format=mv_format(self.max_height),
                merge_output_format="mp4",
                outtmpl=outtmpl,
                progress_hooks=[_hook],
            )
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.item["url"], download=True)
                path = ydl.prepare_filename(info)
            if not os.path.isfile(path):
                path = os.path.splitext(path)[0] + ".mp4"
            if not os.path.isfile(path):
                raise FileNotFoundError(self.app.t("err_merge_file"))
            self.actual_height = info.get("height")
            self.app._queue.put(("mv_ready", self, path, None))
        except Exception as exc:  # noqa: BLE001
            self._cleanup_tmpdir()
            self.app._queue.put(("mv_error", self, str(exc)))

    def embed_and_play(self, source: str, http_headers: dict | None = None) -> None:
        if not self.winfo_exists():
            return
        self.update_idletasks()
        handle = _vlc_embed_handle(self.video_panel)
        if sys.platform.startswith("linux"):
            self._player.set_xwindow(handle)
        elif sys.platform == "win32":
            self._player.set_hwnd(handle)
        elif sys.platform == "darwin":
            self._player.set_nsobject(handle)
        if os.path.isfile(source):
            media = self.app._vlc.media_new_path(source)
        else:
            media = _vlc_media(self.app._vlc, source, http_headers)
        self._player.set_media(media)
        self._player.play()
        if sys.platform == "darwin":
            self._wiggle_video_panel()

    def _wiggle_video_panel(self, delta: int = 4) -> None:
        """macOS 에서 VLC 영상이 패널에 맞게 그려지도록 크기를 살짝 조정."""
        if not self.winfo_exists() or self.attributes("-fullscreen"):
            return
        panel = self.video_panel
        w, h = panel.winfo_width(), panel.winfo_height()
        if w <= 1 or h <= 1:
            return
        panel.config(width=w + delta, height=h)
        self.after(100, lambda: panel.config(width=w, height=h) if self.winfo_exists() else None)
        if delta > 1:
            self.after(120, lambda: self._wiggle_video_panel(delta - 1))

    def _on_escape(self, _evt=None) -> None:
        if self.attributes("-fullscreen"):
            self.attributes("-fullscreen", False)
        else:
            self.close()

    def _toggle_fullscreen(self) -> None:
        cur = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not cur)

    def _cleanup_tmpdir(self) -> None:
        tmpdir = self._tmpdir
        self._tmpdir = None
        if tmpdir and os.path.isdir(tmpdir):
            try:
                shutil.rmtree(tmpdir)
            except OSError:
                pass

    def apply_language(self) -> None:
        if not self.winfo_exists():
            return
        self._mv_fullscreen_btn.config(text=self.app.t("fullscreen"))
        self._mv_close_btn.config(text=self.app.t("close"))

    def close(self) -> None:
        try:
            self._player.stop()
            self._player.release()
        except Exception:  # noqa: BLE001
            pass
        self._cleanup_tmpdir()
        if self.winfo_exists():
            self.destroy()
        if self.app._mv_window is self:
            self.app._mv_window = None


class YoutubeFinder(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        # 하단 재생·다운로드 버튼이 한 줄에 다 보이도록 여유 있게 설정
        self.geometry("1240x900")
        self.minsize(1000, 780)
        self.configure(bg="#0f172a")

        # 데이터
        self.results: list[dict] = []
        self.playlist: list[dict] = []
        self._queue: queue.Queue = queue.Queue()
        self._searching = False
        self._loading = False
        self.current: int = -1
        self.shuffle: bool = False
        self._lyrics_seq: int = 0
        self._saving: bool = False
        self._kar_creating: bool = False
        self._mv_window: MvPlayerWindow | None = None
        self._search_mode = tk.StringVar(value="song")
        self._mv_resolution = tk.StringVar(value=DEFAULT_MV_RESOLUTION)
        self.mp3_folder: str = ""
        self.mp3_files: list[dict] = []
        self.mp3_current: int = -1
        self._active_list: str = "playlist"  # "playlist" | "mp3"
        self._lang_code = DEFAULT_LANG
        self._lang_display = tk.StringVar(value=LANG_OPTIONS[0])

        # VLC
        self._vlc = vlc.Instance("--no-xlib", "--quiet")
        self._player = self._vlc.media_player_new()

        self._setup_xim()
        self._build_ui()
        self.bind("<Return>", lambda e: self.search())
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._poll_queue)
        self.after(500, self._tick)

    # ---------------- UI ----------------
    def _setup_xim(self) -> None:
        """fcitx5 XIM 한글 입력 활성화 (tkinter Entry/Text)."""
        try:
            self.tk.call("tk", "useinputmethods", "1")
        except tk.TclError:
            pass

    @staticmethod
    def _enable_ime(widget: tk.Widget) -> None:
        def _on_focus_in(_evt=None) -> None:
            try:
                widget.tk.call("tk", "useinputmethods", "1")
            except tk.TclError:
                pass
        widget.bind("<FocusIn>", _on_focus_in, add="+")

    def t(self, key: str, **kwargs) -> str:
        return tr(self._lang_code, key, **kwargs)

    def _kind_label(self, media_type: str) -> str:
        if media_type == "mv":
            return self.t("kind_mv")
        if media_type == "local":
            return self.t("kind_local")
        return self.t("kind_song")

    def _on_language_change(self, _evt=None) -> None:
        self._lang_code = LANG_MAP.get(self._lang_display.get(), DEFAULT_LANG)
        self._apply_ui_language()

    def _apply_ui_language(self) -> None:
        self.title(self.t("window_title"))
        if not getattr(self, "status", None):
            return
        self.status.config(text=self.t("status_initial"))
        for key, widget in self._ui.items():
            if key.startswith("lbl_"):
                widget.config(text=self.t(key[4:]))
            elif key.startswith("btn_"):
                widget.config(text=self.t(key[4:]))
            elif key.startswith("radio_"):
                widget.config(text=self.t(key[6:]))
        self.shuffle_btn.config(text=self.t("shuffle_on" if self.shuffle else "shuffle_off"))
        if not self.mp3_folder:
            self.mp3_folder_label.config(text=self.t("folder_unset"))
        for tree, cols in ((self.tree, self._res_cols), (self.plist, self._res_cols)):
            for c, ck in cols:
                tree.heading(c, text=self.t(ck))
        for c, ck in self._mp3_cols:
            self.mp3_tree.heading(c, text=self.t(ck))
        self._set_lyrics("", self.t("lyrics_wait"))
        self._refresh_playlist()
        if self.results:
            self._rerender_search_results()
        if self.mp3_files:
            self._rerender_mp3_files()
        if self._mv_window and self._mv_window.winfo_exists():
            self._mv_window.apply_language()

    def _rerender_search_results(self) -> None:
        sel = self.tree.selection()
        idx = int(sel[0]) if sel else None
        self._refresh_search_results(idx)

    def _rerender_mp3_files(self) -> None:
        sel = self.mp3_tree.selection()
        self.mp3_tree.delete(*self.mp3_tree.get_children())
        for i, it in enumerate(self.mp3_files, 1):
            self.mp3_tree.insert("", "end", iid=str(i - 1), values=(
                i, it["title"], fmt_duration(it.get("duration")),
            ))
        if sel and sel[0] in self.mp3_tree.get_children():
            self.mp3_tree.selection_set(sel[0])

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TButton", padding=6)
        style.configure(
            "Treeview", background="#1e293b", fieldbackground="#1e293b",
            foreground="#e2e8f0", rowheight=26, borderwidth=0,
        )
        style.configure("Treeview.Heading", background="#334155", foreground="#f8fafc")
        style.map("Treeview", background=[("selected", "#38bdf8")],
                  foreground=[("selected", "#0f172a")])

        self._ui: dict = {}
        self._res_cols = (
            ("no", "col_no"), ("kind", "col_kind"), ("title", "col_title"),
            ("channel", "col_channel"), ("dur", "col_dur"),
        )
        self._mp3_cols = (("no", "col_no"), ("title", "col_filename"), ("dur", "col_dur"))

        # 상태줄 (맨 아래)
        self.status = tk.Label(self, text="", bg="#0f172a", fg="#94a3b8", anchor="w")
        self.status.pack(side="bottom", fill="x", padx=16, pady=(2, 10))

        # 본문: 왼쪽(검색/리스트/컨트롤) + 오른쪽(가사)
        body = tk.Frame(self, bg="#0f172a")
        body.pack(side="top", fill="both", expand=True)
        right = tk.Frame(body, bg="#111827", width=320)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        left = tk.Frame(body, bg="#0f172a")
        left.pack(side="left", fill="both", expand=True)

        # 오른쪽: 가사 패널
        self._ui["lbl_lyrics"] = tk.Label(
            right, text="", bg="#111827", fg="#fcd34d", font=("sans-serif", 11, "bold"),
        )
        self._ui["lbl_lyrics"].pack(anchor="w", padx=12, pady=(12, 4))
        self.lyrics_title = tk.Label(right, text="", bg="#111827", fg="#cbd5e1",
                                     font=("sans-serif", 9), wraplength=290, justify="left")
        self.lyrics_title.pack(anchor="w", padx=12)
        lyr = tk.Frame(right, bg="#111827")
        lyr.pack(fill="both", expand=True, padx=(12, 6), pady=8)
        self.lyrics_text = tk.Text(lyr, bg="#0b1220", fg="#e2e8f0", relief="flat",
                                   wrap="word", font=("sans-serif", 10), borderwidth=0,
                                   padx=8, pady=8, state="disabled", cursor="arrow")
        self.lyrics_text.pack(side="left", fill="both", expand=True)
        lsb = ttk.Scrollbar(lyr, orient="vertical", command=self.lyrics_text.yview)
        lsb.pack(side="right", fill="y")
        self.lyrics_text.config(yscrollcommand=lsb.set)

        # 검색 모드 (노래 / 뮤직비디오)
        mode_row = tk.Frame(left, bg="#0f172a")
        mode_row.pack(fill="x", padx=16, pady=(14, 4))
        self._ui["lbl_search_kind"] = tk.Label(
            mode_row, text="", bg="#0f172a", fg="#fcd34d", font=("sans-serif", 10, "bold"),
        )
        self._ui["lbl_search_kind"].pack(side="left")
        self._ui["radio_song_mode"] = ttk.Radiobutton(
            mode_row, text="", variable=self._search_mode, value="song",
        )
        self._ui["radio_song_mode"].pack(side="left", padx=(10, 4))
        self._ui["radio_mv_mode"] = ttk.Radiobutton(
            mode_row, text="", variable=self._search_mode, value="mv",
        )
        self._ui["radio_mv_mode"].pack(side="left", padx=4)

        # 검색 입력줄
        top = tk.Frame(left, bg="#0f172a")
        top.pack(fill="x", padx=16, pady=(4, 6))
        self._ui["lbl_query"] = tk.Label(
            top, text="", bg="#0f172a", fg="#f8fafc", font=("sans-serif", 11, "bold"),
        )
        self._ui["lbl_query"].pack(side="left")
        self.entry = tk.Entry(top, bg="#1e293b", fg="#f8fafc", insertbackground="#f8fafc",
                              relief="flat", font=("sans-serif", 12))
        self.entry.pack(side="left", fill="x", expand=True, padx=10, ipady=5)
        self._enable_ime(self.entry)
        self.entry.focus_set()
        self._ui["lbl_count"] = tk.Label(top, text="", bg="#0f172a", fg="#cbd5e1")
        self._ui["lbl_count"].pack(side="left", padx=(4, 2))
        self.count_var = tk.IntVar(value=DEFAULT_RESULTS)
        self.count_spin = ttk.Spinbox(top, from_=1, to=MAX_RESULTS, increment=5,
                                      width=5, textvariable=self.count_var)
        self.count_spin.pack(side="left", padx=(0, 6))
        self.search_btn = ttk.Button(top, text="", command=self.search)
        self._ui["btn_search"] = self.search_btn
        self.search_btn.pack(side="left")

        # 검색 결과
        self._ui["lbl_search_results"] = tk.Label(
            left, text="", bg="#0f172a", fg="#93c5fd", font=("sans-serif", 10, "bold"),
        )
        self._ui["lbl_search_results"].pack(anchor="w", padx=16)
        res = tk.Frame(left, bg="#0f172a")
        res.pack(fill="both", expand=True, padx=16, pady=(2, 4))
        rcols = ("no", "kind", "title", "channel", "dur")
        self.tree = ttk.Treeview(res, columns=rcols, show="headings", selectmode="browse", height=7)
        for c, w, anc, st in (
            ("no", 36, "center", False), ("kind", 72, "center", False),
            ("title", 440, "w", True), ("channel", 150, "w", False), ("dur", 64, "center", False),
        ):
            self.tree.column(c, width=w, anchor=anc, stretch=st)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", self._on_search_result_double)
        rsb = ttk.Scrollbar(res, orient="vertical", command=self.tree.yview)
        rsb.pack(side="right", fill="y")
        self.tree.config(yscrollcommand=rsb.set)

        rbtn = tk.Frame(left, bg="#0f172a")
        rbtn.pack(fill="x", padx=16, pady=(0, 6))
        self._ui["btn_add"] = ttk.Button(rbtn, text="", command=self.add_to_playlist)
        self._ui["btn_add"].pack(side="left", padx=3)
        self._ui["btn_mv_play"] = ttk.Button(rbtn, text="", command=self.play_selected_mv_from_results)
        self._ui["btn_mv_play"].pack(side="left", padx=3)
        self._ui["lbl_resolution"] = tk.Label(rbtn, text="", bg="#0f172a", fg="#cbd5e1")
        self._ui["lbl_resolution"].pack(side="left", padx=(8, 2))
        self.mv_res_combo = ttk.Combobox(
            rbtn, textvariable=self._mv_resolution,
            values=list(MV_RESOLUTIONS), state="readonly", width=5,
        )
        self.mv_res_combo.pack(side="left", padx=3)
        self._ui["btn_browser"] = ttk.Button(rbtn, text="", command=self.open_selected_result)
        self._ui["btn_browser"].pack(side="left", padx=3)
        self._ui["lbl_language"] = tk.Label(rbtn, text="", bg="#0f172a", fg="#cbd5e1")
        self._ui["lbl_language"].pack(side="left", padx=(8, 2))
        self.lang_combo = ttk.Combobox(
            rbtn, textvariable=self._lang_display,
            values=list(LANG_OPTIONS), state="readonly", width=8,
        )
        self.lang_combo.pack(side="left", padx=3)
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_language_change)

        # 재생 리스트
        self._ui["lbl_playlist"] = tk.Label(
            left, text="", bg="#0f172a", fg="#86efac", font=("sans-serif", 10, "bold"),
        )
        self._ui["lbl_playlist"].pack(anchor="w", padx=16)
        pl = tk.Frame(left, bg="#0f172a")
        pl.pack(fill="both", expand=True, padx=16, pady=(2, 4))
        pcols = ("no", "kind", "title", "channel", "dur")
        self.plist = ttk.Treeview(pl, columns=pcols, show="headings", selectmode="browse", height=6)
        for c, w, anc, st in (
            ("no", 36, "center", False), ("kind", 72, "center", False),
            ("title", 440, "w", True), ("channel", 150, "w", False), ("dur", 64, "center", False),
        ):
            self.plist.column(c, width=w, anchor=anc, stretch=st)
        self.plist.pack(side="left", fill="both", expand=True)
        self.plist.bind("<Double-1>", self._on_playlist_double)
        self.plist.bind("<FocusIn>", lambda _e: setattr(self, "_active_list", "playlist"))
        psb = ttk.Scrollbar(pl, orient="vertical", command=self.plist.yview)
        psb.pack(side="right", fill="y")
        self.plist.config(yscrollcommand=psb.set)

        # 재생 리스트 — MP3 / MV 다운로드
        dlbtn = tk.Frame(left, bg="#0f172a")
        dlbtn.pack(fill="x", padx=16, pady=(0, 6))
        self.save_btn = ttk.Button(dlbtn, text="", command=self.save_all_mp3)
        self._ui["btn_save_mp3_all"] = self.save_btn
        self.save_btn.pack(side="left", padx=3)
        self.save_one_btn = ttk.Button(dlbtn, text="", command=self.save_selected_mp3)
        self._ui["btn_save_mp3_sel"] = self.save_one_btn
        self.save_one_btn.pack(side="left", padx=3)
        self.save_mv_all_btn = ttk.Button(dlbtn, text="", command=self.save_all_mv)
        self._ui["btn_save_mv_all"] = self.save_mv_all_btn
        self.save_mv_all_btn.pack(side="left", padx=3)
        self.save_mv_btn = ttk.Button(dlbtn, text="", command=self.save_selected_mv)
        self._ui["btn_save_mv_sel"] = self.save_mv_btn
        self.save_mv_btn.pack(side="left", padx=3)
        self.kar_one_btn = ttk.Button(dlbtn, text="", command=self.create_kar_from_playlist)
        self._ui["btn_kar_create"] = self.kar_one_btn
        self.kar_one_btn.pack(side="left", padx=3)
        if not _HAS_KAR:
            self.kar_one_btn.config(state="disabled")
        self._ui["btn_clear_pl_list"] = ttk.Button(dlbtn, text="", command=self.clear_playlist)
        self._ui["btn_clear_pl_list"].pack(side="left", padx=3)

        # 로컬 MP3 폴더
        mp3_hdr = tk.Frame(left, bg="#0f172a")
        mp3_hdr.pack(fill="x", padx=16, pady=(4, 2))
        self._ui["lbl_local_mp3"] = tk.Label(
            mp3_hdr, text="", bg="#0f172a", fg="#f9a8d4", font=("sans-serif", 10, "bold"),
        )
        self._ui["lbl_local_mp3"].pack(side="left")
        self.mp3_folder_label = tk.Label(
            mp3_hdr, text="", bg="#0f172a", fg="#94a3b8", font=("sans-serif", 9), anchor="w",
        )
        self.mp3_folder_label.pack(side="left", fill="x", expand=True, padx=8)
        self._ui["btn_pick_folder"] = ttk.Button(mp3_hdr, text="", command=self.pick_mp3_folder)
        self._ui["btn_pick_folder"].pack(side="right", padx=3)
        ttk.Button(mp3_hdr, text="🔄", width=3, command=self.refresh_mp3_folder).pack(
            side="right", padx=3,
        )

        mp3f = tk.Frame(left, bg="#0f172a", height=130)
        mp3f.pack(fill="both", expand=True, padx=16, pady=(2, 4))
        mp3f.pack_propagate(False)
        mcols = ("no", "title", "dur")
        self.mp3_tree = ttk.Treeview(mp3f, columns=mcols, show="headings", selectmode="browse", height=5)
        for c, w, anc, st in (
            ("no", 36, "center", False), ("title", 520, "w", True), ("dur", 64, "center", False),
        ):
            self.mp3_tree.column(c, width=w, anchor=anc, stretch=st)
        self.mp3_tree.pack(side="left", fill="both", expand=True)
        self.mp3_tree.bind("<Double-1>", self._on_mp3_double)
        self.mp3_tree.bind("<FocusIn>", lambda _e: setattr(self, "_active_list", "mp3"))
        msb = ttk.Scrollbar(mp3f, orient="vertical", command=self.mp3_tree.yview)
        msb.pack(side="right", fill="y")
        self.mp3_tree.config(yscrollcommand=msb.set)

        ctrl = tk.Frame(left, bg="#0f172a")
        ctrl.pack(fill="x", padx=16, pady=(0, 6))
        self._ui["btn_play"] = ttk.Button(ctrl, text="", command=self.play_selected)
        self._ui["btn_play"].pack(side="left", padx=3)
        self._ui["btn_delete"] = ttk.Button(ctrl, text="", command=self.remove_playback_selection)
        self._ui["btn_delete"].pack(side="left", padx=3)
        self._ui["btn_clear_pl"] = ttk.Button(ctrl, text="", command=self.clear_playback_all)
        self._ui["btn_clear_pl"].pack(side="left", padx=3)
        self._ui["btn_shuffle"] = ttk.Button(ctrl, text="", command=self.play_random)
        self._ui["btn_shuffle"].pack(side="left", padx=3)
        self.shuffle_btn = ttk.Button(ctrl, text="", width=9, command=self.toggle_shuffle)
        self.shuffle_btn.pack(side="left", padx=3)
        self._ui["btn_copy_urls"] = ttk.Button(ctrl, text="", command=self.copy_all)
        self._ui["btn_copy_urls"].pack(side="left", padx=3)

        self._apply_ui_language()

    # ---------------- 검색 ----------------
    def search(self) -> None:
        query = self.entry.get().strip()
        if not query or self._searching:
            return
        try:
            count = int(self.count_var.get())
        except (tk.TclError, ValueError):
            count = DEFAULT_RESULTS
        count = max(1, min(MAX_RESULTS, count))
        self._searching = True
        self.search_btn.config(state="disabled")
        self.tree.delete(*self.tree.get_children())
        self.results = []
        mode = self._search_mode.get()
        mode_label = self.t("mode_mv") if mode == "mv" else self.t("mode_song")
        self.status.config(text=self.t("status_searching", query=query, mode=mode_label, count=count))
        threading.Thread(
            target=self._search_worker, args=(query, count, mode), daemon=True,
        ).start()

    def _search_worker(self, query: str, count: int, mode: str) -> None:
        opts = {
            "quiet": True, "no_warnings": True, "extract_flat": True,
            "skip_download": True, "noplaylist": True,
        }
        fetch_n = min(count * 3, MAX_RESULTS) if mode == "mv" else min(count * 2, MAX_RESULTS)
        search_q = f"{query} official mv" if mode == "mv" else query
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"ytsearch{fetch_n}:{search_q}", download=False)
            raw: list[dict] = []
            seen_urls: set[str] = set()
            for e in info.get("entries", []) or []:
                if not e:
                    continue
                url = e.get("url") or (
                    f"https://www.youtube.com/watch?v={e['id']}" if e.get("id") else None
                )
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                title = e.get("title") or "(제목 없음)"
                raw.append({
                    "title": title,
                    "channel": e.get("uploader") or e.get("channel") or "",
                    "duration": e.get("duration"),
                    "url": url,
                    "media_type": "mv" if is_mv_title(title) else "song",
                })

            def _urls(lst: list[dict]) -> set[str]:
                return {x["url"] for x in lst}

            items: list[dict] = []
            if mode == "mv":
                for it in raw:
                    if it["media_type"] == "mv":
                        items.append(it)
                for it in raw:
                    if len(items) >= count:
                        break
                    if it["url"] not in _urls(items):
                        items.append({**it, "media_type": "mv"})
            else:
                songs = [it for it in raw if it["media_type"] == "song"]
                items = songs[:count]
                for it in raw:
                    if len(items) >= count:
                        break
                    if it["url"] not in _urls(items):
                        items.append(it)
            self._queue.put(("results", items[:count], mode))
        except Exception as exc:  # noqa: BLE001
            self._queue.put(("error", str(exc)))

    # ---------------- 큐 폴링 ----------------
    def _poll_queue(self) -> None:
        try:
            while True:
                msg = self._queue.get_nowait()
                try:
                    self._handle_queue_message(msg)
                except Exception as exc:  # noqa: BLE001
                    self.status.config(text=self.t("status_error", err=str(exc)))
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _handle_queue_message(self, msg: tuple) -> None:
        kind = msg[0]
        if kind == "results":
            self._show_results(msg[1], msg[2] if len(msg) > 2 else "song")
        elif kind == "mv_ready":
            win, stream = msg[1], msg[2]
            headers = msg[3] if len(msg) > 3 else None
            if win.winfo_exists():
                win.embed_and_play(stream, headers)
                res = win.res_label
                if win.actual_height:
                    res = f"{win.res_label} {win.actual_height}p"
                self.status.config(text=self.t("status_mv_play", res=res, title=win.item.get("title", "")))
        elif kind == "mv_error":
            win, err = msg[1], msg[2]
            self.status.config(text=self.t("status_mv_fail", err=err))
            if win.winfo_exists():
                win.close()
        elif kind == "error":
            self._searching = False
            self.search_btn.config(state="normal")
            self.status.config(text=self.t("status_error", err=msg[1]))
        elif kind == "status":
            self.status.config(text=msg[1])
        elif kind == "play":
            self._loading = False
            stream, title = msg[1], msg[2]
            headers = msg[3] if len(msg) > 3 else None
            self._player.set_media(_vlc_media(self._vlc, stream, headers))
            self._player.play()
            self.status.config(text=self.t("status_playing", title=title))
        elif kind == "mp3_scan_done":
            self._show_mp3_files(msg[1], msg[2])
        elif kind == "mp3_durations":
            self._update_mp3_durations(msg[1])
        elif kind == "play_error":
            self._loading = False
            self.status.config(text=self.t("status_play_fail", err=msg[1]))
        elif kind == "lyrics":
            seq, title, lrc = msg[1], msg[2], msg[3]
            if seq == self._lyrics_seq:  # 최신 요청만 반영
                self._set_lyrics(title, lrc or self.t("lyrics_not_found"))
        elif kind == "save_done":
            ok, total, folder = msg[1], msg[2], msg[3]
            save_kind = msg[4] if len(msg) > 4 else "mp3"
            res_label = msg[5] if len(msg) > 5 else None
            self._saving = False
            self._set_save_buttons_state(True)
            if save_kind == "mp3":
                label = "MP3"
                unit = self.t("unit_song")
            else:
                label = f"MV ({res_label})" if res_label else "MV"
                unit = self.t("unit_mv")
            self.status.config(text=self.t("status_save_done", label=label, ok=ok, total=total, unit=unit, folder=folder))
        elif kind == "kar_done":
            ok, total, folder = msg[1], msg[2], msg[3]
            self._kar_creating = False
            self.kar_one_btn.config(state="normal")
            self.status.config(text=self.t("status_kar_done", ok=ok, total=total, folder=folder))
        elif kind == "kar_error":
            self._kar_creating = False
            self.kar_one_btn.config(state="normal")
            self.status.config(text=self.t("status_kar_fail", err=msg[1]))

    def _refresh_search_results(self, select_idx: int | None = None) -> None:
        self.tree.delete(*self.tree.get_children())
        for i, it in enumerate(self.results, 1):
            self.tree.insert("", "end", iid=str(i - 1), values=(
                i, self._kind_label(it.get("media_type", "song")),
                it["title"], it["channel"], fmt_duration(it["duration"]),
            ))
        if self.results:
            idx = 0 if select_idx is None else max(0, min(select_idx, len(self.results) - 1))
            self.tree.selection_set(str(idx))

    def _show_results(self, items: list[dict], mode: str) -> None:
        self._searching = False
        self.search_btn.config(state="normal")
        self.results = items
        self._refresh_search_results(0)
        if items:
            key = "status_results_mv" if mode == "mv" else "status_results_song"
            self.status.config(text=self.t(key, n=len(items)))
        else:
            self.status.config(text=self.t("status_no_results"))

    def _selected_result_item(self) -> dict | None:
        sel = self.tree.selection()
        if not sel:
            return None
        idx = int(sel[0])
        if 0 <= idx < len(self.results):
            return self.results[idx]
        return None

    def _on_search_result_double(self, _evt) -> None:
        item = self._selected_result_item()
        if not item:
            return
        if item.get("media_type") == "mv":
            self._open_mv_player(item)
        else:
            self.add_to_playlist()

    def play_selected_mv_from_results(self) -> None:
        item = self._selected_result_item()
        if not item:
            self.status.config(text=self.t("status_pick_mv"))
            return
        self._open_mv_player(item)

    def _mv_max_height(self) -> int:
        label = self._mv_resolution.get()
        if label not in MV_RESOLUTIONS:
            label = DEFAULT_MV_RESOLUTION
            self._mv_resolution.set(label)
        return MV_RESOLUTIONS[label]

    def _open_mv_player(self, item: dict) -> None:
        if self._mv_window and self._mv_window.winfo_exists():
            self._mv_window.close()
        self._player.stop()
        self._loading = False
        res_label = self._mv_resolution.get()
        max_height = self._mv_max_height()
        self.status.config(text=self.t("status_mv_prep", res=res_label, title=item["title"]))
        self._mv_window = MvPlayerWindow(self, item, max_height, res_label)

    def _on_playlist_double(self, _evt) -> None:
        idx = self._plist_index()
        if idx is None:
            return
        item = self.playlist[idx]
        if item.get("media_type") == "mv":
            self._open_mv_player(item)
        else:
            self.play_index(idx)

    # ---------------- 로컬 MP3 폴더 ----------------
    def pick_mp3_folder(self) -> None:
        folder = filedialog.askdirectory(title=self.t("dlg_mp3_folder"), parent=self)
        if not folder:
            return
        self.mp3_folder = folder
        self._load_mp3_folder(folder)

    def refresh_mp3_folder(self) -> None:
        if not self.mp3_folder:
            self.status.config(text=self.t("status_pick_mp3_first"))
            return
        self._load_mp3_folder(self.mp3_folder)

    def _load_mp3_folder(self, folder: str) -> None:
        self.status.config(text=self.t("status_mp3_scan", folder=folder))
        threading.Thread(target=self._scan_mp3_folder_worker, args=(folder,), daemon=True).start()

    def _scan_mp3_folder(self, folder: str) -> list[dict]:
        items: list[dict] = []
        channel = self.t("channel_local")
        try:
            for root, _dirs, files in os.walk(folder):
                for name in sorted(files, key=str.lower):
                    ext = os.path.splitext(name)[1].lower()
                    if ext not in MP3_AUDIO_EXTS:
                        continue
                    path = os.path.join(root, name)
                    if not os.path.isfile(path):
                        continue
                    rel = os.path.relpath(path, folder)
                    items.append({
                        "title": os.path.splitext(rel)[0],
                        "path": path,
                        "channel": channel,
                        "duration": None,
                        "media_type": "local",
                    })
        except OSError:
            return items
        items.sort(key=lambda it: it["title"].lower())
        return items

    def _scan_mp3_folder_worker(self, folder: str) -> None:
        try:
            items = self._scan_mp3_folder(folder)
            self._queue.put(("mp3_scan_done", folder, items))
            if items:
                self._queue.put(("status", self.t("status_mp3_probe", n=len(items))))
                durations = self._probe_durations(items)
                self._queue.put(("mp3_durations", durations))
        except Exception as exc:  # noqa: BLE001
            self._queue.put(("status", self.t("status_error", err=str(exc))))

    @staticmethod
    def _probe_durations(items: list[dict]) -> dict[str, int | None]:
        vlc_inst = vlc.Instance("--no-xlib", "--quiet")
        out: dict[str, int | None] = {}
        for it in items:
            path = it["path"]
            try:
                media = vlc_inst.media_new(path)
                media.parse()
                ms = media.get_duration()
                out[path] = int(ms / 1000) if ms and ms > 0 else None
            except Exception:  # noqa: BLE001
                out[path] = None
        return out

    def _show_mp3_files(self, folder: str, items: list[dict]) -> None:
        self.mp3_folder = folder
        self.mp3_files = items
        self.mp3_current = -1
        short = folder if len(folder) <= 48 else "…" + folder[-45:]
        self.mp3_folder_label.config(text=short)
        self._refresh_mp3_list()
        if items:
            self.mp3_tree.selection_set("0")
            self.status.config(text=self.t("status_mp3_found", n=len(items)))
        else:
            self.status.config(text=self.t("status_mp3_empty"))

    def _update_mp3_durations(self, durations: dict[str, int | None]) -> None:
        changed = False
        for it in self.mp3_files:
            dur = durations.get(it["path"])
            if dur is not None and it.get("duration") != dur:
                it["duration"] = dur
                changed = True
        if changed:
            self._refresh_mp3_list()

    def _refresh_mp3_list(self) -> None:
        self.mp3_tree.delete(*self.mp3_tree.get_children())
        for i, it in enumerate(self.mp3_files, 1):
            mark = "▶ " if (i - 1) == self.mp3_current else ""
            self.mp3_tree.insert("", "end", iid=str(i - 1), values=(
                i, mark + it["title"], fmt_duration(it.get("duration")),
            ))

    def _mp3_index(self) -> int | None:
        sel = self.mp3_tree.selection()
        return int(sel[0]) if sel else None

    def _on_mp3_double(self, _evt) -> None:
        idx = self._mp3_index()
        if idx is not None:
            self.play_mp3_index(idx)

    def play_mp3_index(self, idx: int) -> None:
        if not (0 <= idx < len(self.mp3_files)):
            return
        self._active_list = "mp3"
        self.mp3_current = idx
        self._refresh_mp3_list()
        self.mp3_tree.selection_set(str(idx))
        item = self.mp3_files[idx]
        if self._mv_window and self._mv_window.winfo_exists():
            self._mv_window.close()
        self._player.stop()
        self._loading = False
        self._player.set_media(self._vlc.media_new(item["path"]))
        self._player.play()
        self.status.config(text=self.t("status_local_play", title=item["title"]))
        self._fetch_lyrics(item)

    def add_mp3_to_playlist(self) -> None:
        idx = self._mp3_index()
        if idx is None:
            self.status.config(text=self.t("status_pick_mp3_add"))
            return
        self._append_local_item(self.mp3_files[idx])

    def remove_mp3_from_list(self) -> None:
        idx = self._mp3_index()
        if idx is None:
            self.status.config(text=self.t("status_pick_mp3_del"))
            return
        title = self.mp3_files[idx]["title"]
        del self.mp3_files[idx]
        if self._active_list == "mp3":
            if self.mp3_current == idx:
                self._player.stop()
                self.mp3_current = -1
            elif self.mp3_current > idx:
                self.mp3_current -= 1
        self._refresh_mp3_list()
        if self.mp3_files:
            self.mp3_tree.selection_set(str(min(idx, len(self.mp3_files) - 1)))
        self.status.config(text=self.t("status_mp3_removed", title=title))

    def _append_local_item(self, item: dict, refresh: bool = True) -> bool:
        path = item["path"]
        if any(p.get("path") == path for p in self.playlist):
            return False
        self.playlist.append(dict(item))
        if refresh:
            self._refresh_playlist()
            self.status.config(text=self.t("status_added", title=item["title"]))
        return True

    def _mp3_next_index(self) -> int | None:
        if not self.mp3_files:
            return None
        if self.shuffle:
            return self._random_mp3_index()
        nxt = self.mp3_current + 1
        return nxt if nxt < len(self.mp3_files) else None

    def _random_mp3_index(self) -> int:
        n = len(self.mp3_files)
        if n <= 1:
            return 0
        choices = [i for i in range(n) if i != self.mp3_current]
        return random.choice(choices)

    # ---------------- 재생 리스트 ----------------
    def add_to_playlist(self) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if not (0 <= idx < len(self.results)):
            return
        item = dict(self.results[idx])
        if "media_type" not in item:
            item["media_type"] = "mv" if is_mv_title(item["title"]) else "song"
        if any(p.get("url") == item["url"] for p in self.playlist):
            self.status.config(text=self.t("status_duplicate"))
            return
        self.playlist.append(item)
        self._refresh_playlist()
        self.status.config(text=self.t("status_added", title=item["title"]))

    def remove_playback_selection(self) -> None:
        if self._plist_index() is not None:
            self.remove_selected()
        elif self._mp3_index() is not None:
            self.remove_mp3_from_list()
        else:
            self.status.config(text=self.t("status_pick_delete_pl"))

    def remove_selected(self) -> None:
        idx = self._plist_index()
        if idx is None:
            self.status.config(text=self.t("status_pick_delete_pl"))
            return
        title = self.playlist[idx]["title"]
        del self.playlist[idx]
        if self.current == idx:
            self._player.stop()
            self.current = -1
        elif self.current > idx:
            self.current -= 1
        self._refresh_playlist()
        self.status.config(text=self.t("status_deleted", title=title))

    def clear_playback_all(self) -> None:
        if self._active_list == "mp3" and self.mp3_files:
            self.clear_mp3_list()
        elif self.playlist:
            self.clear_playlist()
        elif self.mp3_files:
            self.clear_mp3_list()
        else:
            self.status.config(text=self.t("status_pl_empty"))

    def clear_playlist(self) -> None:
        if not self.playlist:
            self.status.config(text=self.t("status_pl_empty"))
            return
        n = len(self.playlist)
        self._player.stop()
        self.playlist.clear()
        self.current = -1
        self._refresh_playlist()
        self.status.config(text=self.t("status_pl_cleared", n=n))

    def clear_mp3_list(self) -> None:
        if not self.mp3_files:
            self.status.config(text=self.t("status_mp3_empty"))
            return
        n = len(self.mp3_files)
        if self._active_list == "mp3":
            self._player.stop()
            self.mp3_current = -1
        self.mp3_files.clear()
        self._refresh_mp3_list()
        self.status.config(text=self.t("status_mp3_cleared", n=n))

    def _refresh_playlist(self) -> None:
        self.plist.delete(*self.plist.get_children())
        for i, it in enumerate(self.playlist, 1):
            mark = "▶ " if (i - 1) == self.current else ""
            self.plist.insert("", "end", iid=str(i - 1), values=(
                i, self._kind_label(it.get("media_type", "song")),
                mark + it["title"], it["channel"], fmt_duration(it["duration"]),
            ))

    def _plist_index(self):
        sel = self.plist.selection()
        return int(sel[0]) if sel else None

    # ---------------- 재생 ----------------
    def play_selected(self) -> None:
        pl_idx = self._plist_index()
        mp3_idx = self._mp3_index()
        if pl_idx is not None:
            self.play_index(pl_idx)
        elif mp3_idx is not None:
            self.play_mp3_index(mp3_idx)
        elif self.playlist:
            self.play_index(0)
        elif self.mp3_files:
            self.play_mp3_index(0)
        else:
            self.status.config(text=self.t("status_pl_empty"))

    def play_index(self, idx: int) -> None:
        if not (0 <= idx < len(self.playlist)) or self._loading:
            return
        self._active_list = "playlist"
        self.current = idx
        self._refresh_playlist()
        self.plist.selection_set(str(idx))
        item = self.playlist[idx]
        if item.get("media_type") == "mv":
            self._open_mv_player(item)
            self._fetch_lyrics(item)
            return  # current·plist 갱신은 _open_mv_player 전에 이미 수행됨
        if item.get("media_type") == "local" or item.get("path"):
            if self._mv_window and self._mv_window.winfo_exists():
                self._mv_window.close()
            self._player.stop()
            self._loading = False
            self._player.set_media(self._vlc.media_new(item["path"]))
            self._player.play()
            self.status.config(text=self.t("status_local_play", title=item["title"]))
            self._fetch_lyrics(item)
            return
        self._loading = True
        self.status.config(text=self.t("status_loading", title=item["title"]))
        threading.Thread(target=self._play_worker, args=(item,), daemon=True).start()
        self._fetch_lyrics(item)

    def _play_worker(self, item: dict) -> None:
        try:
            with yt_dlp.YoutubeDL(_ytdlp_opts(format=AUDIO_FORMAT)) as ydl:
                info = ydl.extract_info(item["url"], download=False)
            stream, headers = _resolve_stream(info)
            if not stream:
                self._queue.put(("play_error", "스트림 URL을 찾지 못했습니다."))
                return
            self._queue.put(("play", stream, item["title"], headers))
        except Exception as exc:  # noqa: BLE001
            self._queue.put(("play_error", str(exc)))

    # ---------------- 가사 ----------------
    @staticmethod
    def _clean_query(title: str, channel: str) -> str:
        """유튜브 제목에서 가사 검색에 방해되는 군더더기를 제거."""
        t = title
        t = re.sub(r"[\(\[\{].*?[\)\]\}]", " ", t)  # 괄호 안 내용 제거
        # 흔한 키워드 제거
        t = re.sub(r"(?i)\b(official|mv|m/v|video|audio|lyrics?|가사|뮤직비디오|"
                   r"feat\.?|ft\.?|live|performance|teaser|color\s*coded)\b", " ", t)
        t = re.sub(r"[|/_~\-]+", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t or title

    def _set_lyrics(self, title: str, body: str) -> None:
        self.lyrics_title.config(text=title)
        self.lyrics_text.config(state="normal")
        self.lyrics_text.delete("1.0", "end")
        self.lyrics_text.insert("1.0", body)
        self.lyrics_text.config(state="disabled")
        self.lyrics_text.yview_moveto(0.0)

    def _fetch_lyrics(self, item: dict) -> None:
        self._lyrics_seq += 1
        seq = self._lyrics_seq
        if not _HAS_LYRICS:
            self._set_lyrics(item["title"], self.t("lyrics_no_module"))
            return
        self._set_lyrics(item["title"], self.t("lyrics_loading"))
        query = self._clean_query(item["title"], item["channel"])
        threading.Thread(target=self._lyrics_worker, args=(seq, query, item["title"]),
                         daemon=True).start()

    def _lyrics_worker(self, seq: int, query: str, title: str) -> None:
        try:
            lrc = syncedlyrics.search(query, plain_only=True)
        except Exception:  # noqa: BLE001
            lrc = None
        if not lrc:
            # 괄호 등 제거 전 원제목으로 한 번 더 시도
            try:
                lrc = syncedlyrics.search(title, plain_only=True)
            except Exception:  # noqa: BLE001
                lrc = None
        if lrc:
            # 혹시 남아있는 LRC 타임스탬프 제거
            lrc = re.sub(r"\[\d{1,2}:\d{2}(?:\.\d{1,3})?\]", "", lrc).strip()
        self._queue.put(("lyrics", seq, title, lrc))

    def toggle_pause(self) -> None:
        if self._player.get_state() == vlc.State.Playing:
            self._player.pause()
            self.status.config(text=self.t("status_paused"))
        elif self._player.get_state() == vlc.State.Paused:
            self._player.play()
            self.status.config(text=self.t("status_resumed"))

    def stop(self) -> None:
        self._player.stop()
        self.status.config(text=self.t("status_stopped"))

    def toggle_shuffle(self) -> None:
        self.shuffle = not self.shuffle
        self.shuffle_btn.config(text=self.t("shuffle_on" if self.shuffle else "shuffle_off"))
        self.status.config(text=self.t("status_shuffle_on" if self.shuffle else "status_shuffle_off"))

    def play_random(self) -> None:
        """랜덤 재생을 켜고 리스트에서 무작위 곡을 즉시 재생."""
        if self._active_list == "mp3" and self.mp3_files:
            if not self.shuffle:
                self.shuffle = True
                self.shuffle_btn.config(text=self.t("shuffle_on"))
            self.play_mp3_index(self._random_mp3_index())
            return
        if not self.playlist:
            self.status.config(text=self.t("status_pl_empty"))
            return
        if not self.shuffle:
            self.shuffle = True
            self.shuffle_btn.config(text=self.t("shuffle_on"))
        self.play_index(self._random_index())

    def _random_index(self) -> int:
        """현재 곡을 가능한 한 피해서 무작위 인덱스 선택."""
        n = len(self.playlist)
        if n <= 1:
            return 0
        choices = [i for i in range(n) if i != self.current]
        return random.choice(choices)

    def _next_index(self):
        """셔플 여부에 따라 다음 곡 인덱스 (없으면 None)."""
        if not self.playlist:
            return None
        if self.shuffle:
            return self._random_index()
        nxt = self.current + 1
        return nxt if nxt < len(self.playlist) else None

    def play_next(self) -> None:
        if self._active_list == "mp3":
            nxt = self._mp3_next_index()
            if nxt is None:
                self.status.config(text=self.t("status_last_mp3"))
            else:
                self.play_mp3_index(nxt)
            return
        nxt = self._next_index()
        if nxt is None:
            self.status.config(text=self.t("status_last_song"))
        else:
            self.play_index(nxt)

    def _tick(self) -> None:
        # 곡이 끝나면 자동으로 다음 곡 재생 (셔플이면 무작위)
        if self._player.get_state() == vlc.State.Ended and not self._loading:
            if self._active_list == "mp3" and 0 <= self.mp3_current < len(self.mp3_files):
                nxt = self._mp3_next_index()
                if nxt is not None:
                    self.play_mp3_index(nxt)
            elif self._active_list == "playlist" and 0 <= self.current < len(self.playlist):
                nxt = self._next_index()
                if nxt is not None:
                    self.play_index(nxt)
        self.after(500, self._tick)

    # ---------------- 기타 ----------------
    def open_selected_result(self) -> None:
        sel = self.tree.selection()
        if sel:
            idx = int(sel[0])
            if 0 <= idx < len(self.results):
                webbrowser.open(self.results[idx]["url"])

    def copy_all(self) -> None:
        if not self.playlist:
            return
        self.clipboard_clear()
        self.clipboard_append("\n".join(
            p.get("url") or p.get("path", "") for p in self.playlist
        ))
        self.status.config(text=self.t("status_urls_copied", n=len(self.playlist)))

    def _set_save_buttons_state(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.save_btn.config(state=state)
        self.save_one_btn.config(state=state)
        self.save_mv_btn.config(state=state)
        self.save_mv_all_btn.config(state=state)

    def _playlist_mv_items(self) -> list[dict]:
        return [it for it in self.playlist if it.get("media_type") == "mv"]

    # ---------------- MP3 / MV 다운로드 ----------------
    def save_all_mp3(self) -> None:
        """재생 리스트의 모든 곡을 MP3로 저장."""
        if not self.playlist:
            self.status.config(text=self.t("status_pl_empty"))
            return
        self._start_mp3_download(list(self.playlist))

    def save_selected_mp3(self) -> None:
        """재생 리스트에서 선택한 곡 한 곡만 MP3로 저장."""
        idx = self._plist_index()
        if idx is None:
            self.status.config(text=self.t("status_pick_save_song"))
            return
        self._start_mp3_download([self.playlist[idx]])

    def save_selected_mv(self) -> None:
        """재생 리스트에서 선택한 MV 한 개를 영상 파일로 저장."""
        idx = self._plist_index()
        if idx is None:
            self.status.config(text=self.t("status_pick_save_mv"))
            return
        item = self.playlist[idx]
        if item.get("media_type") != "mv":
            self.status.config(text=self.t("status_not_mv"))
            return
        self._start_mv_download([item])

    def save_all_mv(self) -> None:
        """재생 리스트에 있는 모든 MV를 영상 파일로 저장."""
        items = self._playlist_mv_items()
        if not items:
            self.status.config(text=self.t("status_no_mv_in_pl"))
            return
        self._start_mv_download(items)

    def _start_mp3_download(self, items: list[dict]) -> None:
        if self._saving:
            return
        folder = filedialog.askdirectory(title=self.t("dlg_mp3_save"))
        if not folder:
            return
        self._saving = True
        self._set_save_buttons_state(False)
        threading.Thread(
            target=self._save_worker, args=(folder, items, "mp3"), daemon=True,
        ).start()

    def _start_mv_download(self, items: list[dict]) -> None:
        if self._saving:
            return
        res_label = self._mv_resolution.get()
        max_height = self._mv_max_height()
        folder = filedialog.askdirectory(
            title=self.t("dlg_mv_save", res=res_label),
        )
        if not folder:
            return
        self._saving = True
        self._set_save_buttons_state(False)
        threading.Thread(
            target=self._save_worker,
            args=(folder, items, "mv", max_height, res_label),
            daemon=True,
        ).start()

    def _save_worker(
        self,
        folder: str,
        items: list[dict],
        save_kind: str,
        max_height: int = 1080,
        res_label: str = "",
    ) -> None:
        total = len(items)
        ok = 0
        is_mv = save_kind == "mv"
        for i, item in enumerate(items, 1):
            if is_mv:
                label = f"MV ({res_label})"
            else:
                label = "MP3"
            self._queue.put(("status", self.t("status_saving", label=label, i=i, total=total, title=item["title"])))
            if is_mv:
                opts = _ytdlp_opts(
                    format=mv_format(max_height),
                    merge_output_format="mp4",
                    outtmpl=os.path.join(folder, "%(title)s.%(ext)s"),
                )
            else:
                url = item.get("url")
                if not url:
                    continue
                opts = _ytdlp_opts(
                    format="bestaudio/best",
                    outtmpl=os.path.join(folder, "%(title)s.%(ext)s"),
                    postprocessors=[{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }],
                )
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([item["url"]])
                ok += 1
            except Exception:  # noqa: BLE001
                pass
        self._queue.put(("save_done", ok, total, folder, save_kind, res_label if is_mv else None))

    # ---------------- KAR MIDI 생성 ----------------
    def create_kar_from_playlist(self) -> None:
        """재생 리스트 선택 곡: MP3를 받은 뒤 KAR MIDI 생성."""
        if not _HAS_KAR:
            self.status.config(text=self.t("status_kar_no_mod"))
            return
        idx = self._plist_index()
        if idx is None:
            self.status.config(text=self.t("status_kar_pick"))
            return
        if self._kar_creating or self._saving:
            return
        folder = filedialog.askdirectory(title=self.t("dlg_kar_save"))
        if not folder:
            return
        item = self.playlist[idx]
        self._kar_creating = True
        self.kar_one_btn.config(state="disabled")
        threading.Thread(
            target=self._kar_from_playlist_worker,
            args=(folder, item),
            daemon=True,
        ).start()

    def _kar_from_playlist_worker(self, folder: str, item: dict) -> None:
        """유튜브에서 MP3 다운로드 후 KAR 변환."""
        import tempfile

        title = self._clean_query(item["title"], item.get("channel", ""))
        artist = item.get("channel", "")
        total = 1
        ok = 0
        try:
            with tempfile.TemporaryDirectory() as tmp:
                mp3_path = os.path.join(tmp, "audio.mp3")
                self._queue.put(("status", self.t("status_kar_mp3_dl", title=item["title"])))
                opts = {
                    "quiet": True, "no_warnings": True, "noplaylist": True,
                    "format": "bestaudio/best",
                    "outtmpl": os.path.join(tmp, "audio.%(ext)s"),
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }],
                }
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([item["url"]])
                if not os.path.isfile(mp3_path):
                    mp3s = [f for f in os.listdir(tmp) if f.endswith(".mp3")]
                    if not mp3s:
                        raise RuntimeError(self.t("err_mp3_dl"))
                    mp3_path = os.path.join(tmp, mp3s[0])
                safe = re.sub(r'[<>:"/\\|?*]', "_", title)[:120]
                out = os.path.join(folder, f"{safe}.kar")
                self._queue.put(("status", self.t("status_kar_creating", title=title)))
                create_kar_from_mp3(mp3_path, out, title=title, artist=artist)
                ok = 1
        except Exception as exc:  # noqa: BLE001
            self._queue.put(("kar_error", str(exc)))
            return
        self._queue.put(("kar_done", ok, total, folder))

    def _on_close(self) -> None:
        try:
            if self._mv_window and self._mv_window.winfo_exists():
                self._mv_window.close()
            self._player.stop()
        finally:
            self.destroy()


def main() -> None:
    app = YoutubeFinder()
    app.mainloop()


if __name__ == "__main__":
    main()
