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
import sys
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, ttk

import vlc
import yt_dlp

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

# MV 저장 시 yt-dlp format (팝업 재생과 동일 — 1080p 이하)
MV_DOWNLOAD_FORMAT = (
    "best[height<=1080][ext=mp4]/best[height<=1080]/"
    "bestvideo[height<=1080]+bestaudio/best"
)

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


def media_kind_label(media_type: str) -> str:
    if media_type == "mv":
        return "🎬 MV"
    if media_type == "local":
        return "💾 로컬"
    return "🎵 노래"


class MvPlayerWindow(tk.Toplevel):
    """뮤직비디오 전용 팝업 재생 (초기 800×600, F11 전체화면)."""

    MV_WIDTH = 800
    MV_HEIGHT = 600

    def __init__(self, app: YoutubeFinder, item: dict) -> None:
        super().__init__(app)
        self.app = app
        self.item = item
        self._player = app._vlc.media_player_new()
        self.title(item.get("title", "뮤직비디오"))
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
        ttk.Button(bar, text="⛶ 전체화면 (F11)", command=self._toggle_fullscreen).pack(
            side="right", padx=4, pady=4,
        )
        ttk.Button(bar, text="닫기 (Esc)", command=self.close).pack(side="right", padx=8, pady=4)

        app._player.stop()
        threading.Thread(target=self._fetch_stream, daemon=True).start()

    def _fetch_stream(self) -> None:
        opts = {
            "quiet": True, "no_warnings": True, "noplaylist": True,
            # Full HD(1080p) 우선 (단일 스트림 → VLC 재생 호환)
            "format": (
                "best[height<=1080][ext=mp4]/best[height<=1080]/"
                "bestvideo[height<=1080]+bestaudio/best"
            ),
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.item["url"], download=False)
            stream = info.get("url")
            if not stream:
                self.app._queue.put(("mv_error", self, "스트림 URL을 찾지 못했습니다."))
                return
            self.app._queue.put(("mv_ready", self, stream))
        except Exception as exc:  # noqa: BLE001
            self.app._queue.put(("mv_error", self, str(exc)))

    def embed_and_play(self, stream_url: str) -> None:
        if not self.winfo_exists():
            return
        self.update_idletasks()
        wid = self.video_panel.winfo_id()
        if sys.platform.startswith("linux"):
            self._player.set_xwindow(wid)
        elif sys.platform == "win32":
            self._player.set_hwnd(wid)
        elif sys.platform == "darwin":
            self._player.set_nsobject(wid)
        self._player.set_media(self.app._vlc.media_new(stream_url))
        self._player.play()

    def _on_escape(self, _evt=None) -> None:
        if self.attributes("-fullscreen"):
            self.attributes("-fullscreen", False)
        else:
            self.close()

    def _toggle_fullscreen(self) -> None:
        cur = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not cur)

    def close(self) -> None:
        try:
            self._player.stop()
            self._player.release()
        except Exception:  # noqa: BLE001
            pass
        if self.winfo_exists():
            self.destroy()
        if self.app._mv_window is self:
            self.app._mv_window = None


class YoutubeFinder(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("getYoutubeUrl — 유튜브 검색 & 재생")
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
        self.mp3_folder: str = ""
        self.mp3_files: list[dict] = []
        self.mp3_current: int = -1
        self._active_list: str = "playlist"  # "playlist" | "mp3"

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

        # 상태줄 (맨 아래)
        self.status = tk.Label(self, text="노래 제목을 입력하고 검색하세요.",
                               bg="#0f172a", fg="#94a3b8", anchor="w")
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
        tk.Label(right, text="가사", bg="#111827", fg="#fcd34d",
                 font=("sans-serif", 11, "bold")).pack(anchor="w", padx=12, pady=(12, 4))
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
        self._set_lyrics("", "재생을 시작하면 가사가 표시됩니다.")

        # 검색 모드 (노래 / 뮤직비디오)
        mode_row = tk.Frame(left, bg="#0f172a")
        mode_row.pack(fill="x", padx=16, pady=(14, 4))
        tk.Label(mode_row, text="검색 종류", bg="#0f172a", fg="#fcd34d",
                 font=("sans-serif", 10, "bold")).pack(side="left")
        ttk.Radiobutton(
            mode_row, text="🎵 노래 검색", variable=self._search_mode,
            value="song",
        ).pack(side="left", padx=(10, 4))
        ttk.Radiobutton(
            mode_row, text="🎬 뮤직비디오", variable=self._search_mode,
            value="mv",
        ).pack(side="left", padx=4)

        # 검색 입력줄
        top = tk.Frame(left, bg="#0f172a")
        top.pack(fill="x", padx=16, pady=(4, 6))
        tk.Label(top, text="검색어", bg="#0f172a", fg="#f8fafc",
                 font=("sans-serif", 11, "bold")).pack(side="left")
        self.entry = tk.Entry(top, bg="#1e293b", fg="#f8fafc", insertbackground="#f8fafc",
                              relief="flat", font=("sans-serif", 12))
        self.entry.pack(side="left", fill="x", expand=True, padx=10, ipady=5)
        self._enable_ime(self.entry)
        self.entry.focus_set()
        tk.Label(top, text="개수", bg="#0f172a", fg="#cbd5e1").pack(side="left", padx=(4, 2))
        self.count_var = tk.IntVar(value=DEFAULT_RESULTS)
        self.count_spin = ttk.Spinbox(top, from_=1, to=MAX_RESULTS, increment=5,
                                      width=5, textvariable=self.count_var)
        self.count_spin.pack(side="left", padx=(0, 6))
        self.search_btn = ttk.Button(top, text="검색", command=self.search)
        self.search_btn.pack(side="left")

        # 검색 결과
        tk.Label(left, text="검색 결과", bg="#0f172a", fg="#93c5fd",
                 font=("sans-serif", 10, "bold")).pack(anchor="w", padx=16)
        res = tk.Frame(left, bg="#0f172a")
        res.pack(fill="both", expand=True, padx=16, pady=(2, 4))
        rcols = ("no", "kind", "title", "channel", "dur")
        self.tree = ttk.Treeview(res, columns=rcols, show="headings", selectmode="browse", height=7)
        for c, t, w, anc, st in (
            ("no", "#", 36, "center", False), ("kind", "구분", 72, "center", False),
            ("title", "제목", 440, "w", True),
            ("channel", "채널", 150, "w", False), ("dur", "길이", 64, "center", False),
        ):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor=anc, stretch=st)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", self._on_search_result_double)
        rsb = ttk.Scrollbar(res, orient="vertical", command=self.tree.yview)
        rsb.pack(side="right", fill="y")
        self.tree.config(yscrollcommand=rsb.set)

        rbtn = tk.Frame(left, bg="#0f172a")
        rbtn.pack(fill="x", padx=16, pady=(0, 6))
        ttk.Button(rbtn, text="추가 ↓", command=self.add_to_playlist).pack(side="left", padx=3)
        ttk.Button(rbtn, text="🗑 삭제", command=self.remove_selected).pack(side="left", padx=3)
        ttk.Button(rbtn, text="🎬 MV 재생", command=self.play_selected_mv_from_results).pack(
            side="left", padx=3,
        )
        ttk.Button(rbtn, text="브라우저로 열기", command=self.open_selected_result).pack(side="left", padx=3)

        # 재생 리스트
        tk.Label(left, text="재생 리스트", bg="#0f172a", fg="#86efac",
                 font=("sans-serif", 10, "bold")).pack(anchor="w", padx=16)
        pl = tk.Frame(left, bg="#0f172a")
        pl.pack(fill="both", expand=True, padx=16, pady=(2, 4))
        pcols = ("no", "kind", "title", "channel", "dur")
        self.plist = ttk.Treeview(pl, columns=pcols, show="headings", selectmode="browse", height=6)
        for c, t, w, anc, st in (
            ("no", "#", 36, "center", False), ("kind", "구분", 72, "center", False),
            ("title", "제목", 440, "w", True),
            ("channel", "채널", 150, "w", False), ("dur", "길이", 64, "center", False),
        ):
            self.plist.heading(c, text=t)
            self.plist.column(c, width=w, anchor=anc, stretch=st)
        self.plist.pack(side="left", fill="both", expand=True)
        self.plist.bind("<Double-1>", self._on_playlist_double)
        psb = ttk.Scrollbar(pl, orient="vertical", command=self.plist.yview)
        psb.pack(side="right", fill="y")
        self.plist.config(yscrollcommand=psb.set)

        # 재생 리스트 — MP3 다운로드
        dlbtn = tk.Frame(left, bg="#0f172a")
        dlbtn.pack(fill="x", padx=16, pady=(0, 6))
        self.save_btn = ttk.Button(dlbtn, text="⬇ MP3 다운로드 (전체)",
                                   command=self.save_all_mp3)
        self.save_btn.pack(side="left", padx=3)
        self.save_one_btn = ttk.Button(dlbtn, text="⬇ 선택 곡 저장",
                                       command=self.save_selected_mp3)
        self.save_one_btn.pack(side="left", padx=3)
        self.save_mv_btn = ttk.Button(dlbtn, text="⬇ 선택 MV 저장",
                                      command=self.save_selected_mv)
        self.save_mv_btn.pack(side="left", padx=3)
        self.save_mv_all_btn = ttk.Button(dlbtn, text="⬇ MV 저장 (전체)",
                                         command=self.save_all_mv)
        self.save_mv_all_btn.pack(side="left", padx=3)
        self.kar_one_btn = ttk.Button(dlbtn, text="선택곡 MIDI파일 생성",
                                      command=self.create_kar_from_playlist)
        self.kar_one_btn.pack(side="left", padx=3)
        if not _HAS_KAR:
            self.kar_one_btn.config(state="disabled")

        # 로컬 MP3 폴더
        mp3_hdr = tk.Frame(left, bg="#0f172a")
        mp3_hdr.pack(fill="x", padx=16, pady=(4, 2))
        tk.Label(mp3_hdr, text="로컬 MP3", bg="#0f172a", fg="#f9a8d4",
                 font=("sans-serif", 10, "bold")).pack(side="left")
        self.mp3_folder_label = tk.Label(
            mp3_hdr, text="(폴더 미지정)", bg="#0f172a", fg="#94a3b8",
            font=("sans-serif", 9), anchor="w",
        )
        self.mp3_folder_label.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(mp3_hdr, text="📁 폴더 선택", command=self.pick_mp3_folder).pack(
            side="right", padx=3,
        )
        ttk.Button(mp3_hdr, text="🔄", width=3, command=self.refresh_mp3_folder).pack(
            side="right", padx=3,
        )

        mp3f = tk.Frame(left, bg="#0f172a")
        mp3f.pack(fill="both", expand=True, padx=16, pady=(2, 4))
        mcols = ("no", "title", "dur")
        self.mp3_tree = ttk.Treeview(mp3f, columns=mcols, show="headings", selectmode="browse", height=5)
        for c, t, w, anc, st in (
            ("no", "#", 36, "center", False),
            ("title", "파일명", 520, "w", True),
            ("dur", "길이", 64, "center", False),
        ):
            self.mp3_tree.heading(c, text=t)
            self.mp3_tree.column(c, width=w, anchor=anc, stretch=st)
        self.mp3_tree.pack(side="left", fill="both", expand=True)
        self.mp3_tree.bind("<Double-1>", self._on_mp3_double)
        msb = ttk.Scrollbar(mp3f, orient="vertical", command=self.mp3_tree.yview)
        msb.pack(side="right", fill="y")
        self.mp3_tree.config(yscrollcommand=msb.set)

        mp3btn = tk.Frame(left, bg="#0f172a")
        mp3btn.pack(fill="x", padx=16, pady=(0, 6))
        ttk.Button(mp3btn, text="▶ MP3 재생", command=self.play_selected_mp3).pack(side="left", padx=3)
        ttk.Button(mp3btn, text="전체 추가", command=self.add_all_mp3_to_playlist).pack(side="left", padx=3)
        ttk.Button(mp3btn, text="🗑 삭제", command=self.remove_mp3_from_list).pack(side="left", padx=3)

        # 재생 컨트롤
        pbtn = tk.Frame(left, bg="#0f172a")
        pbtn.pack(fill="x", padx=16, pady=(0, 4))
        ttk.Button(pbtn, text="▶ 재생", command=self.play_selected).pack(side="left", padx=3)
        ttk.Button(pbtn, text="⏸ 일시정지", command=self.toggle_pause).pack(side="left", padx=3)
        ttk.Button(pbtn, text="⏹ 정지", command=self.stop).pack(side="left", padx=3)
        ttk.Button(pbtn, text="⏭ 다음", command=self.play_next).pack(side="left", padx=3)
        ttk.Button(pbtn, text="🔀 랜덤재생", command=self.play_random).pack(side="left", padx=3)
        self.shuffle_btn = ttk.Button(pbtn, text="랜덤: 끔", width=9, command=self.toggle_shuffle)
        self.shuffle_btn.pack(side="left", padx=3)
        ttk.Button(pbtn, text="🗑 삭제", command=self.remove_selected).pack(side="left", padx=3)
        ttk.Button(pbtn, text="🗑 전체삭제", command=self.clear_playlist).pack(side="left", padx=3)
        ttk.Button(pbtn, text="전체 URL 복사", command=self.copy_all).pack(side="left", padx=3)

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
        mode_label = "뮤직비디오" if mode == "mv" else "노래"
        self.status.config(text=f"'{query}' {mode_label} 검색 중… (최대 {count}개)")
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
                kind = msg[0]
                if kind == "results":
                    self._show_results(msg[1], msg[2] if len(msg) > 2 else "song")
                elif kind == "mv_ready":
                    win, stream = msg[1], msg[2]
                    if win.winfo_exists():
                        win.embed_and_play(stream)
                        self.status.config(text=f"🎬 MV 재생: {win.item.get('title', '')}")
                elif kind == "mv_error":
                    win, err = msg[1], msg[2]
                    self.status.config(text=f"MV 재생 실패: {err}")
                    if win.winfo_exists():
                        win.close()
                elif kind == "error":
                    self._searching = False
                    self.search_btn.config(state="normal")
                    self.status.config(text=f"오류: {msg[1]}")
                elif kind == "status":
                    self.status.config(text=msg[1])
                elif kind == "play":
                    self._loading = False
                    stream, title = msg[1], msg[2]
                    self._player.set_media(self._vlc.media_new(stream))
                    self._player.play()
                    self.status.config(text=f"▶ 재생 중: {title}")
                elif kind == "mp3_scan_done":
                    self._show_mp3_files(msg[1], msg[2])
                elif kind == "mp3_durations":
                    self._update_mp3_durations(msg[1])
                elif kind == "play_error":
                    self._loading = False
                    self.status.config(text=f"재생 실패: {msg[1]}")
                elif kind == "lyrics":
                    seq, title, lrc = msg[1], msg[2], msg[3]
                    if seq == self._lyrics_seq:  # 최신 요청만 반영
                        self._set_lyrics(title, lrc or "가사를 찾지 못했습니다.")
                elif kind == "save_done":
                    ok, total, folder = msg[1], msg[2], msg[3]
                    save_kind = msg[4] if len(msg) > 4 else "mp3"
                    self._saving = False
                    self._set_save_buttons_state(True)
                    label = "MP3" if save_kind == "mp3" else "MV"
                    unit = "곡" if save_kind == "mp3" else "MV"
                    self.status.config(text=f"{label} 저장 완료: {ok}/{total}{unit} → {folder}")
                elif kind == "kar_done":
                    ok, total, folder = msg[1], msg[2], msg[3]
                    self._kar_creating = False
                    self.kar_one_btn.config(state="normal")
                    self.status.config(text=f"KAR MIDI 생성 완료: {ok}/{total}곡 → {folder}")
                elif kind == "kar_error":
                    self._kar_creating = False
                    self.kar_one_btn.config(state="normal")
                    self.status.config(text=f"KAR 생성 실패: {msg[1]}")
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _refresh_search_results(self, select_idx: int | None = None) -> None:
        self.tree.delete(*self.tree.get_children())
        for i, it in enumerate(self.results, 1):
            self.tree.insert("", "end", iid=str(i - 1), values=(
                i, media_kind_label(it.get("media_type", "song")),
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
            if mode == "mv":
                hint = "MV는 '🎬 MV 재생' 또는 더블클릭. 노래는 '추가 ↓'."
            else:
                hint = "'추가 ↓' 로 재생 리스트에 담기. MV는 '🎬 MV 재생'."
            self.status.config(text=f"{len(items)}개 결과. {hint}")
        else:
            self.status.config(text="검색 결과가 없습니다.")

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
            self.status.config(text="MV를 재생할 항목을 선택하세요.")
            return
        self._open_mv_player(item)

    def _open_mv_player(self, item: dict) -> None:
        if self._mv_window and self._mv_window.winfo_exists():
            self._mv_window.close()
        self._player.stop()
        self._loading = False
        self.status.config(text=f"MV 불러오는 중: {item['title']} …")
        self._mv_window = MvPlayerWindow(self, item)

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
        folder = filedialog.askdirectory(title="MP3 폴더 선택")
        if not folder:
            return
        self.mp3_folder = folder
        self._load_mp3_folder(folder)

    def refresh_mp3_folder(self) -> None:
        if not self.mp3_folder:
            self.status.config(text="먼저 MP3 폴더를 선택하세요.")
            return
        self._load_mp3_folder(self.mp3_folder)

    def _load_mp3_folder(self, folder: str) -> None:
        self.status.config(text=f"MP3 폴더 스캔 중: {folder} …")
        threading.Thread(target=self._scan_mp3_folder_worker, args=(folder,), daemon=True).start()

    @staticmethod
    def _scan_mp3_folder(folder: str) -> list[dict]:
        items: list[dict] = []
        try:
            names = sorted(os.listdir(folder), key=str.lower)
        except OSError:
            return items
        for name in names:
            ext = os.path.splitext(name)[1].lower()
            if ext not in MP3_AUDIO_EXTS:
                continue
            path = os.path.join(folder, name)
            if not os.path.isfile(path):
                continue
            items.append({
                "title": os.path.splitext(name)[0],
                "path": path,
                "channel": "로컬",
                "duration": None,
                "media_type": "local",
            })
        return items

    def _scan_mp3_folder_worker(self, folder: str) -> None:
        items = self._scan_mp3_folder(folder)
        self._queue.put(("mp3_scan_done", folder, items))
        if items:
            self._queue.put(("status", f"MP3 {len(items)}곡 길이 정보 불러오는 중…"))
            durations = self._probe_durations(items)
            self._queue.put(("mp3_durations", durations))

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
            self.status.config(text=f"MP3 {len(items)}곡 — 더블클릭 또는 '▶ MP3 재생'")
        else:
            self.status.config(text="MP3 파일이 없습니다.")

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

    def play_selected_mp3(self) -> None:
        idx = self._mp3_index()
        if idx is None:
            if self.mp3_files:
                idx = 0
            else:
                self.status.config(text="MP3 폴더를 선택하거나 재생할 곡을 고르세요.")
                return
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
        self.status.config(text=f"▶ 로컬 재생: {item['title']}")
        self._fetch_lyrics(item)

    def add_mp3_to_playlist(self) -> None:
        idx = self._mp3_index()
        if idx is None:
            self.status.config(text="재생 리스트에 추가할 MP3를 선택하세요.")
            return
        self._append_local_item(self.mp3_files[idx])

    def add_all_mp3_to_playlist(self) -> None:
        if not self.mp3_files:
            self.status.config(text="추가할 MP3가 없습니다.")
            return
        added = 0
        for it in self.mp3_files:
            if self._append_local_item(it, refresh=False):
                added += 1
        self._refresh_playlist()
        self.status.config(text=f"로컬 MP3 {added}곡을 재생 리스트에 추가했습니다.")

    def remove_mp3_from_list(self) -> None:
        idx = self._mp3_index()
        if idx is None:
            self.status.config(text="삭제할 MP3를 선택하세요.")
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
        self.status.config(text=f"MP3 목록에서 삭제됨: {title}")

    def _append_local_item(self, item: dict, refresh: bool = True) -> bool:
        path = item["path"]
        if any(p.get("path") == path for p in self.playlist):
            return False
        self.playlist.append(dict(item))
        if refresh:
            self._refresh_playlist()
            self.status.config(text=f"추가됨: {item['title']}")
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
            self.status.config(text="이미 재생 리스트에 있는 곡입니다.")
            return
        self.playlist.append(item)
        self._refresh_playlist()
        self.status.config(text=f"추가됨: {item['title']}")

    def remove_selected(self) -> None:
        idx = self._plist_index()
        if idx is None:
            self.status.config(text="재생 리스트에서 삭제할 곡을 선택하세요.")
            return
        title = self.playlist[idx]["title"]
        del self.playlist[idx]
        if self.current == idx:
            self._player.stop()
            self.current = -1
        elif self.current > idx:
            self.current -= 1
        self._refresh_playlist()
        self.status.config(text=f"삭제됨: {title}")

    def clear_playlist(self) -> None:
        if not self.playlist:
            self.status.config(text="재생 리스트가 비어 있습니다.")
            return
        n = len(self.playlist)
        self._player.stop()
        self.playlist.clear()
        self.current = -1
        self._refresh_playlist()
        self.status.config(text=f"재생 리스트 전체 삭제됨 ({n}곡).")

    def _refresh_playlist(self) -> None:
        self.plist.delete(*self.plist.get_children())
        for i, it in enumerate(self.playlist, 1):
            mark = "▶ " if (i - 1) == self.current else ""
            self.plist.insert("", "end", iid=str(i - 1), values=(
                i, media_kind_label(it.get("media_type", "song")),
                mark + it["title"], it["channel"], fmt_duration(it["duration"]),
            ))

    def _plist_index(self):
        sel = self.plist.selection()
        return int(sel[0]) if sel else None

    # ---------------- 재생 ----------------
    def play_selected(self) -> None:
        idx = self._plist_index()
        if idx is None:
            if self.playlist:
                idx = 0
            else:
                self.status.config(text="재생 리스트가 비어 있습니다.")
                return
        self.play_index(idx)

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
            self.status.config(text=f"▶ 로컬 재생: {item['title']}")
            self._fetch_lyrics(item)
            return
        self._loading = True
        self.status.config(text=f"불러오는 중: {item['title']} …")
        threading.Thread(target=self._play_worker, args=(item,), daemon=True).start()
        self._fetch_lyrics(item)

    def _play_worker(self, item: dict) -> None:
        opts = {
            "quiet": True, "no_warnings": True, "format": "bestaudio/best",
            "noplaylist": True,
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(item["url"], download=False)
            stream = info.get("url")
            if not stream:
                self._queue.put(("play_error", "스트림 URL을 찾지 못했습니다."))
                return
            self._queue.put(("play", stream, item["title"]))
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
            self._set_lyrics(item["title"], "(syncedlyrics 미설치: 가사 기능 불가)")
            return
        self._set_lyrics(item["title"], "가사 불러오는 중…")
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
            self.status.config(text="⏸ 일시정지")
        elif self._player.get_state() == vlc.State.Paused:
            self._player.play()
            self.status.config(text="▶ 재생 재개")

    def stop(self) -> None:
        self._player.stop()
        self.status.config(text="⏹ 정지")

    def toggle_shuffle(self) -> None:
        self.shuffle = not self.shuffle
        self.shuffle_btn.config(text="랜덤: 켬" if self.shuffle else "랜덤: 끔")
        self.status.config(text="랜덤 재생 켜짐" if self.shuffle else "랜덤 재생 꺼짐")

    def play_random(self) -> None:
        """랜덤 재생을 켜고 리스트에서 무작위 곡을 즉시 재생."""
        if self._active_list == "mp3" and self.mp3_files:
            if not self.shuffle:
                self.shuffle = True
                self.shuffle_btn.config(text="랜덤: 켬")
            self.play_mp3_index(self._random_mp3_index())
            return
        if not self.playlist:
            self.status.config(text="재생 리스트가 비어 있습니다.")
            return
        if not self.shuffle:
            self.shuffle = True
            self.shuffle_btn.config(text="랜덤: 켬")
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
                self.status.config(text="마지막 MP3입니다.")
            else:
                self.play_mp3_index(nxt)
            return
        nxt = self._next_index()
        if nxt is None:
            self.status.config(text="마지막 곡입니다.")
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
        self.status.config(text=f"재생 리스트 {len(self.playlist)}개 URL을 복사했습니다.")

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
            self.status.config(text="재생 리스트가 비어 있습니다.")
            return
        self._start_mp3_download(list(self.playlist))

    def save_selected_mp3(self) -> None:
        """재생 리스트에서 선택한 곡 한 곡만 MP3로 저장."""
        idx = self._plist_index()
        if idx is None:
            self.status.config(text="저장할 곡을 선택하세요.")
            return
        self._start_mp3_download([self.playlist[idx]])

    def save_selected_mv(self) -> None:
        """재생 리스트에서 선택한 MV 한 개를 영상 파일로 저장."""
        idx = self._plist_index()
        if idx is None:
            self.status.config(text="저장할 MV를 선택하세요.")
            return
        item = self.playlist[idx]
        if item.get("media_type") != "mv":
            self.status.config(text="선택한 항목은 MV가 아닙니다. 🎬 MV 항목을 선택하세요.")
            return
        self._start_mv_download([item])

    def save_all_mv(self) -> None:
        """재생 리스트에 있는 모든 MV를 영상 파일로 저장."""
        items = self._playlist_mv_items()
        if not items:
            self.status.config(text="재생 리스트에 MV가 없습니다.")
            return
        self._start_mv_download(items)

    def _start_mp3_download(self, items: list[dict]) -> None:
        if self._saving:
            return
        folder = filedialog.askdirectory(title="MP3를 저장할 폴더 선택")
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
        folder = filedialog.askdirectory(title="MV 영상을 저장할 폴더 선택")
        if not folder:
            return
        self._saving = True
        self._set_save_buttons_state(False)
        threading.Thread(
            target=self._save_worker, args=(folder, items, "mv"), daemon=True,
        ).start()

    def _save_worker(self, folder: str, items: list[dict], save_kind: str) -> None:
        total = len(items)
        ok = 0
        is_mv = save_kind == "mv"
        for i, item in enumerate(items, 1):
            label = "MV" if is_mv else "MP3"
            self._queue.put(("status", f"{label} 저장 중 ({i}/{total}): {item['title']} …"))
            opts: dict = {
                "quiet": True, "no_warnings": True, "noplaylist": True,
                "outtmpl": os.path.join(folder, "%(title)s.%(ext)s"),
            }
            if is_mv:
                opts["format"] = MV_DOWNLOAD_FORMAT
                opts["merge_output_format"] = "mp4"
            else:
                url = item.get("url")
                if not url:
                    continue
                opts["format"] = "bestaudio/best"
                opts["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }]
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([item["url"]])
                ok += 1
            except Exception:  # noqa: BLE001
                pass
        self._queue.put(("save_done", ok, total, folder, save_kind))

    # ---------------- KAR MIDI 생성 ----------------
    def create_kar_from_playlist(self) -> None:
        """재생 리스트 선택 곡: MP3를 받은 뒤 KAR MIDI 생성."""
        if not _HAS_KAR:
            self.status.config(text="KAR 생성 불가: mido·numpy 미설치")
            return
        idx = self._plist_index()
        if idx is None:
            self.status.config(text="KAR로 만들 곡을 재생 리스트에서 선택하세요.")
            return
        if self._kar_creating or self._saving:
            return
        folder = filedialog.askdirectory(title="KAR MIDI를 저장할 폴더 선택")
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
                self._queue.put(("status", f"MP3 다운로드 중: {item['title']} …"))
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
                        raise RuntimeError("MP3 다운로드 실패")
                    mp3_path = os.path.join(tmp, mp3s[0])
                safe = re.sub(r'[<>:"/\\|?*]', "_", title)[:120]
                out = os.path.join(folder, f"{safe}.kar")
                self._queue.put(("status", f"KAR MIDI 생성 중: {title} …"))
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
